import copy
import os
import pickle
import tarfile
import zipfile
import numpy as np
import pandas as pd
from .cfg import config
from . import util
from .celery_tasks import celery_available
from .celery_tasks import featurize_ts_data as featurize_data_task
from .celery_tasks import featurize_ts_file as featurize_file_task
from . import featurize_tools as ft
from . import manage_data


def write_features_to_disk(featureset, featureset_id):
    """Store xarray.Dataset of features as netCDF using given featureset key."""
    featureset_path = os.path.join(config['paths']['features_folder'],
                                   "{}_featureset.nc".format(featureset_id))
    featureset.to_netcdf(featureset_path)


def load_and_store_feature_data(features_path, featureset_id="unknown",
                                first_N=None):
    """Read features from CSV file and store as xarray.Dataset."""
    targets, meta_features = manage_data.parse_headerfile(features_path)
    meta_features = meta_features[:first_N]
    if targets is not None:
        targets = targets[:first_N]
    meta_feature_dicts = meta_features.to_dict(orient='record')
    featureset = ft.assemble_featureset([], targets, meta_feature_dicts)
    write_features_to_disk(featureset, featureset_id)
    return featureset


def prepare_celery_data_task_params(times, values, errors, labels,
                                    features_to_use, meta_features=None,
                                    custom_script_path=None,
                                    custom_functions=None):
    """Create list of tuples containing params for `featurize_data_task`.

    See `featurize_time_series` for parameter descriptions.
    """
    params_list = []
    for t, m, e, label in zip(times, values, errors, labels):
        meta_feature_dict = meta_features.loc[label].to_dict()
        if isinstance(label, np.int64):  # Labels need to be JSON-serializable
            label = int(label)
        params_list.append((t, m, e, label, features_to_use, meta_feature_dict,
                            custom_script_path, custom_functions))
    return params_list


def featurize_file_task_params(ts_paths, features_to_use,
                               custom_script_path=None):
    """Create list of tuples containing params for `featurize_file_task`."""
    params_list = [(ts_path, features_to_use, custom_script_path)
                   for ts_path in ts_paths]
    return params_list


def featurize_data_files(ts_paths, features_to_use=[],
                         featureset_id=None, first_N=None,
                         custom_script_path=None):
    """Generate features for labeled time series data.

    Each file should consist of one comma-separated line of per data point,
    where each line contains either pairs (time, value) or triples (time,
    value, error).

    If `featureset_id` is provided, Features are saved as an xarray.Dataset in
    netCDF format to the file ``"%s_featureset.nc" % featureset_id`` in the
    directory `config['paths']['features_folder']`.

    Parameters
    ----------
    data_path : str
        Path to an individual time series file or tarball of multiple time
        series files to be used for feature generation.
    header_path : str, optional
        Path to header file containing file names, target names, and
        meta_features.
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty
        list, which will result in only meta_features features being stored.
    featureset_id : str, optional
        RethinkDB ID of the new feature set entry. If provided, the feature set
        will be saved to a file with prefix `featureset_id`.
    first_N : int, optional
        Integer indicating the maximum number of time series to featurize.
        Can be used to reduce the number of files for testing purposes. If
        `first_N` is None then all time series will be featurized.
    custom_script_path : str, optional
        Path to Python script containing function definitions for the
        generation of any custom features. Defaults to None.

    Returns
    -------
    xarray.Dataset
        Featureset with `data_vars` containing feature values, and `coords`
        containing filenames and targets (if applicable).

    """
    ts_paths = ts_paths[:first_N]
    params_list = featurize_file_task_params(ts_paths, features_to_use,
                                             custom_script_path)
    if not celery_available():
        raise RuntimeError("Celery not available")
    celery_res = featurize_file_task.chunks(params_list,
                                            config['mltsp']['N_CORES']).delay()
    # Returns list of list of pairs [fname, {feature: [values]]
    res_list = celery_res.get()
    res_flat = [elem for chunk in res_list for elem in chunk]
    fnames, feature_dicts, targets, meta_feature_dicts = zip(*res_flat)
    featureset = ft.assemble_featureset(feature_dicts, targets,
                                        meta_feature_dicts, fnames)

    if featureset_id:
        write_features_to_disk(featureset, featureset_id)

    return featureset


def featurize_time_series(times, values, errors=None, features_to_use=[],
                          targets=None, meta_features={}, labels=None,
                          custom_script_path=None, custom_functions=None,
                          use_celery=False):
    """Versatile feature generation function for one or more time series.

    For a single time series, inputs may have the form:
        - times:  (n,) array or (p, n) array (for p channels of measurement)
        - values: (n,) array or (p, n) array (for p channels of measurement)
        - errors: (n,) array or (p, n) array (for p channels of measurement)

    For multiple time series, inputs may have the form:
        - times: list of (n,) arrays, list of (p, n) arrays (for p channels of
          measurement), or list of lists of (n,) arrays (for
          multichannel data with different time values per channel)
        - values: list of (n,) arrays, list of (p, n) arrays (for p channels of
          measurement), or list of lists of (n,) arrays (for
          multichannel data with different time values per channel)
        - errors: list of (n,) arrays, list of (p, n) arrays (for p channels of
          measurement), or list of lists of (n,) arrays (for
          multichannel data with different time values per channel)

    In the case of multichannel measurements, each channel will be
    featurized separately, and the data variables of the output
    `xarray.Dataset` will be indexed by a `channel` coordinate.

    Parameters
    ----------
    times : array, list of array, or list of lists of array
        Array containing time values for a single time series, or a list of
        arrays each containing time values for a single time series, or a list
        of lists of arrays for multichannel data with different time values per
        channel
    values : array or list of array
        Array containing measurement values for a single time series, or a list
        of arrays each containing (possibly multivariate) measurement values
        for a single time series, or a list of lists of arrays for multichannel
        data with different time values per channel
    errors : array or list/tuple of array, optional
        Array containing measurement error values for a single time series, or
        a list of arrays each containing (possibly multivariate) measurement
        values for a single time series, or a list of lists of arrays for
        multichannel data with different time values per channel
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty list, which
        will result in only meta_features features being stored.
    targets : str/float or array-like, optional
        Target or sequence of targets, one per time series (if applicable);
        will be stored in the `target` coordinate of the resulting
        `xarray.Dataset`.
    meta_features : dict/Pandas.Series or list of dicts/Pandas.DataFrame
        dict/Series (for a single time series) or DataFrame (for multiple time
        series) of metafeature information; features are added to the output
        featureset, and their values are consumable by custom feature scripts.
    labels : str or list of str, optional
        Label or list of labels for each time series, if applicable; will be
        stored in the `name` coordinate of the resulting `xarray.Dataset`.
    custom_script_path : str, optional
        Path to Python script containing function definitions for the
        generation of any custom features. Defaults to None.
    custom_functions : dict, optional
        Dictionary of custom feature functions to be evaluated for the given
        time series, or a dictionary representing a dask graph of function
        evaluations.  Dictionaries of functions should have keys `feature_name`
        and values functions that take arguments (t, m, e); in the case of a
        dask graph, these arrays should be referenced as 't', 'm', 'e',
        respectively, and any values with keys present in `features_to_use`
        will be computed.
    use_celery : bool, optional
        Boolean to control whether to distribute tasks to Celery workers (if
        Celery is available). Defaults to True.

    Returns
    -------
    xarray.Dataset
        Featureset with `data_vars` containing feature values and `coords`
        containing labels (`name`) and targets (`target`), if applicable.
    """
    if times is None:
        times = copy.deepcopy(values)
        if isinstance(times, np.ndarray) and (times.ndim == 1
                                              or 1 in times.shape):
            times[:] = np.linspace(0., config['mltsp']['DEFAULT_MAX_TIME'],
                                   times.size)
        else:
            for t in times:
                if isinstance(t, np.ndarray) and (t.ndim == 1 or 1 in t.shape):
                    t[:] = np.linspace(0., config['mltsp']['DEFAULT_MAX_TIME'],
                                       t.size)
                else:
                    for t_i in t:
                        t_i[:] = np.linspace(
                            0., config['mltsp']['DEFAULT_MAX_TIME'], t_i.size
                            )

    if errors is None:
        errors = copy.deepcopy(values)
        if isinstance(errors, np.ndarray) and (errors.ndim == 1
                                               or 1 in errors.shape):
            errors[:] = config['mltsp']['DEFAULT_ERROR_VALUE']
        else:
            for e in errors:
                if isinstance(e, np.ndarray) and (e.ndim == 1 or 1 in e.shape):
                    e[:] = config['mltsp']['DEFAULT_ERROR_VALUE']
                else:
                    for e_i in e:
                        e_i[:] = config['mltsp']['DEFAULT_ERROR_VALUE']

    if labels is None:
        if isinstance(times, (list, tuple)):
            labels = np.arange(len(times))
        else:
            labels = np.array([0])

    if all([isinstance(x, np.ndarray) for x in (times, values, errors)]):
        times, values, errors = ([times], [values], [errors])
    if isinstance(meta_features, pd.Series):
        meta_features = meta_features.to_dict()
    if targets is not None:
        targets = pd.Series(targets, index=labels)

    if not all([isinstance(x, (list, tuple)) for x in (times, values, errors)]):
        raise TypeError("times, values, and errors have incompatible types")

    meta_features = pd.DataFrame(meta_features, index=labels)

    if use_celery:
        if not celery_available():
            raise RuntimeError("Celery unavailable; please check your Celery "
                               "configuration or set `use_celery=False`.")
        try:
            pickle.loads(pickle.dumps(custom_functions))
            # If a function was defined outside a module, it will fail to load
            # properly on a Celery worker (even if it's pickleable)
            if custom_functions:
                assert(not any(f.__module__ == '__main__'
                               for f in custom_functions.values()))
        except:
            raise ValueError("Using Celery requires pickleable custom functions; "
                             "please import your functions from a module or set "
                             "`use_celery=False`.")

        params_list = prepare_celery_data_task_params(times, values, errors,
                                                      labels, features_to_use,
                                                      meta_features,
                                                      custom_script_path,
                                                      custom_functions)
        celery_res = featurize_data_task.chunks(
            params_list, config['mltsp']['N_CORES']).delay()
        # Returns list of list of pairs [label, {feature: [values]]
        res_list = celery_res.get()
        res_flat = [elem for chunk in res_list for elem in chunk]
        labels, feature_dicts = zip(*res_flat)
        if targets is not None:
            targets = targets.loc[list(labels)]
        meta_features = meta_features.loc[list(labels)]
        meta_feature_dicts = meta_features.to_dict(orient='record')
    else:
        feature_dicts = []
        meta_feature_dicts = []
        for t, m, e, label in zip(times, values, errors, labels):
            meta_feature_dict = meta_features.loc[label].to_dict()
            feature_dict = ft.featurize_single_ts(t, m, e, features_to_use,
                                                  meta_features=meta_feature_dict,
                                                  custom_script_path=custom_script_path,
                                                  custom_functions=custom_functions)
            feature_dicts.append(feature_dict)
            meta_feature_dicts.append(meta_feature_dict)
    return ft.assemble_featureset(feature_dicts, targets, meta_feature_dicts,
                                  labels)
