import os
import numpy as np
import pandas as pd
import rethinkdb as rdb
import xarray as xr
from . import cfg
from . import util


__all__ = []


def parse_ts_data(filepath, sep=","):
    """Parses time series data file and returns np.ndarray with 3 columns:
       - For data containing three columns (time, measurement, error), all three are
         returned
       - For data containing two columns, a dummy error column is added with
         value `config['mltsp']['DEFAULT_ERROR_VALUE']`
       - For data containing one column, a time column is also added with
         values evenly spaced from 0 to `config['mltsp']['DEFAULT_MAX_TIME']`
         """
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep, ndmin=2)
    ts_data = ts_data[:, :3]  # Only using T, M, E
    if ts_data.shape[1] == 0:
        raise custom_exceptions.DataFormatError("""Incomplete or improperly
                                                formatted time series data file
                                                provided.""")
    elif ts_data.shape[1] == 1:
        ts_data = np.c_[np.linspace(0, config['mltsp']['DEFAULT_MAX_TIME'],
                                    len(ts_data)),
                        ts_data,
                        np.repeat(config['mltsp']['DEFAULT_ERROR_VALUE'],
                                  len(ts_data))]
    elif ts_data.shape[1] == 2:
        ts_data = np.c_[ts_data,
                        np.repeat(config['mltsp']['DEFAULT_ERROR_VALUE'],
                                  len(ts_data))]
    return ts_data.T


def parse_headerfile(headerfile_path, files_to_include=None):
    """Parse header file.

    Parameters
    ----------
    headerfile_path : str
        Path to header file.

    files_to_include : list, optional
        If provided, only return the subset of rows from the header
        corresponding to the given filenames.

    Returns
    -------
    pandas.Series or None
        Target column from header file (if present)

    pandas.DataFrame
        Feature data from other columns besides filename, target (can be empty)
    """
    header = pd.read_csv(headerfile_path, comment='#')
    if 'filename' in header:
        header.index = [util.shorten_fname(str(f)) for f in header['filename']]
        header.drop('filename', axis=1, inplace=True)
    if files_to_include:
        short_fnames_to_include = [util.shorten_fname(str(f))
                                   for f in files_to_include]
        header = header.loc[short_fnames_to_include]
    if 'target' in header:
        targets = header['target']
    elif 'class' in header:
        targets = header['class']
    else:
        targets = None
    feature_data = header.drop(['target', 'class'], axis=1, errors='ignore')
    return targets, feature_data


# TODO more general API, expand to match `featurize_single_ts`? lists of arrays, etc.
def assemble_ts_dataset(t, m, e, target, meta_features, fname):
    meta_features = xr.DataArray(pd.Series(meta_features), dims=['feature'])
    dataset = xr.Dataset({'time': (['i'], t), 'measurement': (['i'], m),
                          'error': (['i'], e),
                          'meta_features': meta_features},
#                         coords={'feature': meta_features.keys()},
                         attrs={'name': fname})
    if target:
        dataset.attrs['target'] = target
    return dataset


def parse_and_store_ts_data(data_path, header_path=None, dataset_id=None,
                            cleanup_archive=True):
    """

    

    Parameters
    ----------
    data_path : str
        Path to an individual time series file or tarball of multiple time
        series files to be used for feature generation.
    header_path : str, optional
        Path to header file containing file names, target names, and
        meta_features.

    Returns
    -------
    List of xarray.Dataset
        

    """
    with util.extract_time_series(data_path, cleanup_archive=cleanup_archive,
                                  cleanup_files=True) as ts_paths:
        short_fnames = [util.shorten_fname(f) for f in ts_paths]
        if header_path:
            targets, meta_features = parse_headerfile(header_path, ts_paths)
        else:
            targets = pd.Series([None], index=short_fnames)
            meta_features = pd.DataFrame(index=short_fnames)

        datasets, ds_fnames = [], []
        for ts_path in ts_paths:
            fname = util.shorten_fname(ts_path)
            t, m, e = parse_ts_data(ts_path)
            ts_target = targets.loc[fname]
            ts_meta_features = meta_features.loc[fname]
            ds = assemble_ts_dataset(t, m, e, ts_target, ts_meta_features,
                                     fname)
            ds_fname = '{}.nc'.format(fname)
            if dataset_id:
                ds_fname = '_'.join(dataset_id, ds_fname)
            ds.to_netcdf(os.path.join(cfg.TS_DATA_FOLDER, ds_fname))
            datasets.append(ds)
            ds_fnames.append(ds_fname)
    return datasets, ds_fnames


# TODO move into separate database module
def add_dataset_to_db(name, project_id):
    """Add a new entry to the rethinkDB 'datasets' table.

    Parameters
    ----------
    name : str
        New dataset name.
    project_id : str
        RethinkDB key/ID of parent project.

    Returns
    -------
    str
        RethinkDB key/ID of newly created dataset entry.

    """
    new_dataset_id = rdb.table('datasets').insert({
        'projkey': project_key,
        'name': name,
        'created': str(rdb.now().in_timezone('-08:00').run(g.rdb_conn)),
    }).run(g.rdb_conn)['generated_keys'][0]
    print("Dataset %s entry added to mltsp_app db." % name)
    return new_dataset_id


def set_dataset_filenames_in_db(dataset_id, ts_filenames):
    rdb.table('datasets').get(dataset_id).update({'ts_filenames':
                                                  ts_filenames})


def process_uploaded_ts_data(dataset_name, project_id, data_path,
                             header_path=None):
    dataset_id = add_dataset_to_db(dataset_name, project_id)
    datasets, fnames = parse_and_store_ts_data(data_path, header_path,
                                               dataset_id)
    set_dataset_filenames_in_db(dataset_id, fnames)
    return dataset_id
