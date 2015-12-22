import numpy as np
import pandas as pd
import xarray as xr
import os
import dask.async
from mltsp import custom_exceptions
from mltsp import util
from mltsp import obs_feature_tools as oft
from mltsp import science_feature_tools as sft
from mltsp import custom_feature_tools as cft


def featurize_single_ts(t, m, e, features_to_use, meta_features={},
                        custom_script_path=None, custom_functions=None):
    """Compute feature values for a given single time-series. Data is
    manipulated as dictionaries/lists of lists (as opposed to a more
    convenient DataFrame/DataSet) since it will be serialized as part of
    `celery_tasks.featurize_ts_file`.

    Parameters
    ----------
    t : (n,) or (p, n) array or list of (n_i,) arrays
        Array of time values for a single time series, or a list of arrays (of
        potentially different lengths) of time values for each channel of
        measurement.
    m : (n,) or (p, n) array or list of (n_i,) arrays
        Array or list of measurement values for a single time series, each
        containing p channels of measurements (if applicable).
    e : (n,) or (p, n) array or list of (n_i,) arrays
        Array or list of measurement error values for a single time series,
        each containing p channels of measurements (if applicable).
    features_to_use : list of str
        List of feature names to be generated.
    meta_features : dict
        Dictionary of metafeature information to potentially be consumed by
        custom feature scripts.
    custom_script_path : str, optional
        Path to custom features script .py file to be run in Docker container.
    custom_functions : dict, optional
        Dictionary of custom feature functions to be evaluated for the given
        time series, or a dictionary representing a dask graph of function
        evaluations. Dictionaries of functions should have keys `feature_name`
        and values functions that take arguments (t, m, e); in the case of a
        dask graph, these arrays should be referenced as 't', 'm', 'e',
        respectively, and any values with keys present in `features_to_use`
        will be computed.

    Returns
    -------
    dict
        Dictionary with feature names as keys, lists of feature values (one per
        channel) as values.

    """
    # Reformat single-channel data as multichannel with n_channels=1
    if isinstance(m, np.ndarray) and (m.ndim == 1 or 1 in m.shape):
        n_channels = 1
        m = [m]
    else:
        n_channels = len(m)
    if isinstance(t, np.ndarray) and (t.ndim == 1 or 1 in t.shape):
        t = [t] * n_channels
    if isinstance(e, np.ndarray) and (e.ndim == 1 or 1 in e.shape):
        e = [e] * n_channels

    all_feature_lists = {feature: [0.] * n_channels
                         for feature in features_to_use}
    for i in range(n_channels):
        obs_features = oft.generate_obs_features(t[i], m[i], e[i],
                                                 features_to_use)
        science_features = sft.generate_science_features(t[i], m[i], e[i],
                                                         features_to_use)
        if custom_script_path:
            custom_features = cft.generate_custom_features(
                custom_script_path, t[i], m[i], e[i],
                features_already_known=dict(list(obs_features.items()) +
                                            list(science_features.items()) +
                                            list(meta_features.items())))
            custom_features = {key: custom_features[key]
                               for key in custom_features.keys()
                               if key in features_to_use}
        elif custom_functions:
            # If all values in custom_functions are functions, evaluate each
            if all(hasattr(v, '__call__') for v in custom_functions.values()):
                custom_features = {feature: f(t[i], m[i], e[i])
                                   for feature, f in custom_functions.items()
                                   if feature in features_to_use}
            # Otherwise, custom_functions is a dask graph
            else:
                dask_graph = {key: value
                              for key, value in custom_functions.items()
                              if key in features_to_use}
                dask_keys = list(dask_graph.keys())
                dask_graph['t'] = t[i]
                dask_graph['m'] = m[i]
                dask_graph['e'] = e[i]
                dask_graph.update(dict(list(obs_features.items()) +
                                       list(science_features.items()) +
                                       list(meta_features.items())))
                custom_features = dict(zip(dask_keys,
                                           dask.async.get_sync(dask_graph,
                                                               dask_keys)))
        else:
            custom_features = {}

        # We set values in this order so that custom features take priority
        # over MLTSP features in the case of name conflicts
        for feature, value in (list(obs_features.items()) +
                               list(science_features.items()) +
                               list(custom_features.items())):
            all_feature_lists[feature][i] = value

    return all_feature_lists


def assemble_featureset(feature_dicts, targets=None, metadata=None, names=None):
    """Transforms raw feature data (as returned by `featurize_single_ts`) into
    an xarray.Dataset.

    Parameters
    ----------
    feature_dicts : list
        List of dicts (one per time series file) with feature names as keys and
        lists of feature values (one per channel) as values.

    targets : list or pandas.Series, optional
        If provided, the `target` coordinate of the featureset xarray.Dataset
        will be set accordingly.

    metadata : pandas.DataFrame, optional
        If provided, the columns of `metadata` will be added as data variables
        to the featureset xarray.Dataset.

    Returns
    -------
    xarray.Dataset
        Featureset with `data_vars` containing feature values, and `coords`
        containing filenames and targets (if applicable).

    """

    feature_names = feature_dicts[0].keys() if len(feature_dicts) > 0 else []
    combined_feature_dict = {feature: (['name', 'channel'],
                                       [d[feature] for d in feature_dicts])
                             for feature in feature_names}
    if metadata is not None and metadata != (None, None):
        combined_feature_dict.update({feature: (['name'],
                                                metadata[feature].values)
                                      for feature in metadata.columns})
    featureset = xr.Dataset(combined_feature_dict)
    if names is not None:
        featureset.coords['name'] = ('name', np.array(names))
    if targets is not None:
        featureset.coords['target'] = ('name', np.array(targets))
    return featureset


def parse_ts_data(filepath, sep=","):
    """Parses time series data file and returns np.ndarray with 1-3 columns."""
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep)
    ts_data = ts_data[:, :3]  # Only using T, M, E
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
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
