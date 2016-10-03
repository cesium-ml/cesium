import copy
import os
from collections import Iterable
import numpy as np
import pandas as pd
import xarray as xr
import dask.async
import dask.multiprocessing
from dask import delayed

from . import data_management
from . import time_series
from . import util
from .time_series import TimeSeries
from . import obs_feature_tools as oft
from . import science_feature_tools as sft

__all__ = ['load_and_store_feature_data', 'featurize_time_series',
           'featurize_single_ts', 'assemble_featureset']


def featurize_single_ts(ts, features_to_use, custom_script_path=None,
                        custom_functions=None):
    """Compute feature values for a given single time-series. Data is
    returned as dictionaries/lists of lists.

    Parameters
    ----------
    ts : TimeSeries object
        Single time series to be featurized.
    features_to_use : list of str
        List of feature names to be generated.
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
    all_feature_lists = {feature: [0.] * ts.n_channels
                         for feature in features_to_use}
    for (t_i, m_i, e_i), i in zip(ts.channels(), range(ts.n_channels)):
        obs_features = oft.generate_obs_features(t_i, m_i, e_i,
                                                 features_to_use)
        science_features = sft.generate_science_features(t_i, m_i, e_i,
                                                         features_to_use)
        if custom_functions:
            # If all values in custom_functions are functions, evaluate each
            if all(hasattr(v, '__call__') for v in custom_functions.values()):
                custom_features = {feature: f(t_i, m_i, e_i)
                                   for feature, f in custom_functions.items()
                                   if feature in features_to_use}
            # Otherwise, custom_functions is a dask graph
            else:
                dask_graph = {key: value
                              for key, value in custom_functions.items()
                              if key in features_to_use}
                dask_keys = list(dask_graph.keys())
                dask_graph['t'] = t_i
                dask_graph['m'] = m_i
                dask_graph['e'] = e_i
                dask_graph.update(dict(list(obs_features.items()) +
                                       list(science_features.items()) +
                                       list(ts.meta_features.items())))
                custom_features = dict(zip(dask_keys,
                                           dask.async.get_sync(dask_graph,
                                                               dask_keys)))
        else:
            custom_features = {}

        # We set values in this order so that custom features take priority
        # over cesium features in the case of name conflicts
        for feature, value in (list(obs_features.items()) +
                               list(science_features.items()) +
                               list(custom_features.items())):
            all_feature_lists[feature][i] = value

    return all_feature_lists


def assemble_featureset(feature_dicts, time_series=None, targets=None,
                        meta_feature_dicts=None, names=None):
    """Transforms raw feature data (as returned by `featurize_single_ts`) into
    an xarray.Dataset.

    Parameters
    ----------
    feature_dicts : list of dict
        List of dicts (one per time series file) with feature names as keys and
        lists of feature values (one per channel) as values.
    time_series : list of TimeSeries
        If provided, the target, name, and metafeatures from the time series
        objects will be used, overriding the `targets`, `meta_feature_dicts`,
        and `names` values.
    targets : list or pandas.Series, optional
        If provided, the `target` coordinate of the featureset xarray.Dataset
        will be set accordingly.
    meta_feature_dicts : list of dict
        If provided, the columns of `metadata` will be added as data variables
        to the featureset xarray.Dataset.
    names : list of str
        If provided, the `name` coordinate of the featureset xarray.Dataset
        will be set accordingly.

    Returns
    -------
    xarray.Dataset
        Featureset with `data_vars` containing feature values, and `coords`
        containing names and targets (if applicable).
    """
    feature_names = feature_dicts[0].keys() if len(feature_dicts) > 0 else []
    combined_feature_dict = {feature: (['name', 'channel'],
                                       [d[feature] for d in feature_dicts])
                             for feature in feature_names}

    if time_series is not None:
        targets, meta_feature_dicts, names = zip(*[(ts.target,
                                                    ts.meta_features, ts.name)
                                                   for ts in time_series])


    if meta_feature_dicts is not None:
        meta_feature_names = meta_feature_dicts[0].keys()
        combined_feature_dict.update({feature: (['name'], [d[feature] for d in
                                                           meta_feature_dicts])
                                      for feature in meta_feature_names})
    featureset = xr.Dataset(combined_feature_dict)
    if names is not None:
        featureset.coords['name'] = ('name', np.array(names))
    if targets is not None and any(targets):
        featureset.coords['target'] = ('name', np.array(targets))
    return featureset


def load_and_store_feature_data(features_path, output_path):
    """Read features from CSV file and save as an xarray.Dataset."""
    targets, meta_features = data_management.parse_headerfile(features_path)
    meta_feature_dicts = meta_features.to_dict(orient='record')
    featureset = assemble_featureset([], targets=targets,
                                     meta_feature_dicts=meta_feature_dicts)
    featureset.to_netcdf(output_path)
    return featureset


# TODO should this be changed to use TimeSeries objects? or maybe an optional
# argument for TimeSeries? some redundancy here...
def featurize_time_series(times, values, errors=None, features_to_use=[],
                          targets=None, meta_features={}, labels=None,
                          custom_script_path=None, custom_functions=None,
                          scheduler=dask.multiprocessing.get):
    """Versatile feature generation function for one or more time series.

    For a single time series, inputs may have the form:

    - `times`:  (n,) array or (p, n) array (for p channels of measurement)
    - `values`: (n,) array or (p, n) array (for p channels of measurement)
    - `errors`: (n,) array or (p, n) array (for p channels of measurement)

    For multiple time series, inputs may have the form:

    - `times`: list of (n,) arrays, list of (p, n) arrays (for p channels of
      measurement), or list of lists of (n,) arrays (for
      multichannel data with different time values per channel)
    - `values`: list of (n,) arrays, list of (p, n) arrays (for p channels of
      measurement), or list of lists of (n,) arrays (for
      multichannel data with different time values per channel)
    - `errors`: list of (n,) arrays, list of (p, n) arrays (for p channels of
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
    scheduler : function, optional
        `dask` scheduler function used to perform feature extraction
        computation. Defaults to `dask.multiprocessing.get`.

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
            times[:] = np.linspace(0., time_series.DEFAULT_MAX_TIME,
                                   times.size)
        else:
            for t in times:
                if isinstance(t, np.ndarray) and (t.ndim == 1 or 1 in t.shape):
                    t[:] = np.linspace(0., time_series.DEFAULT_MAX_TIME,
                                       t.size)
                else:
                    for t_i in t:
                        t_i[:] = np.linspace(0., time_series.DEFAULT_MAX_TIME,
                                             t_i.size)

    if errors is None:
        errors = copy.deepcopy(values)
        if isinstance(errors, np.ndarray) and (errors.ndim == 1
                                               or 1 in errors.shape):
            errors[:] = time_series.DEFAULT_ERROR_VALUE
        else:
            for e in errors:
                if isinstance(e, np.ndarray) and (e.ndim == 1 or 1 in e.shape):
                    e[:] = time_series.DEFAULT_ERROR_VALUE
                else:
                    for e_i in e:
                        e_i[:] = time_series.DEFAULT_ERROR_VALUE

    # One single-channel time series:
    if not isinstance(values[0], Iterable):
        times, values, errors = [times], [values], [errors]
    # One multi-channel time series:
    elif isinstance(values, np.ndarray) and values.ndim == 2:
        times, values, errors = [times], [values], [errors]

    if labels is None:
        labels = np.arange(len(times))

    if targets is None:
        targets = [None] * len(times)
    targets = pd.Series(targets, index=labels)

    if isinstance(meta_features, pd.Series):
        meta_features = meta_features.to_dict()
    meta_features = pd.DataFrame(meta_features, index=labels)

    all_time_series = [delayed(TimeSeries(t, m, e, target=targets.loc[label],
                                          meta_features=meta_features.loc[label],
                                          name=label), pure=True)
                       for t, m, e, label in zip(times, values, errors,
                                                 labels)]

    all_features = [delayed(featurize_single_ts, pure=True)(ts, features_to_use,
                                                            custom_script_path,
                                                            custom_functions)
                    for ts in all_time_series]
    result = delayed(assemble_featureset, pure=True)(all_features, all_time_series)
    return result.compute(get=scheduler)


def featurize_ts_files(ts_paths, features_to_use, output_path=None,
                       custom_script_path=None, custom_functions=None,
                       scheduler=dask.multiprocessing.get):
    """Feature generation function for on-disk time series (NetCDF) files.

    By default, computes features concurrently using the
    `dask.multiprocessing.get` scheduler. Other possible options include
    `dask.async.get_sync` for synchronous computation (e.g., when debugging),
    or `dask.distributed.Executor.get` for distributed computation.

    In the case of multichannel measurements, each channel will be
    featurized separately, and the data variables of the output
    `xarray.Dataset` will be indexed by a `channel` coordinate.

    Parameters
    ----------
    ts_paths : list of str
        List of paths to time series data, stored in NetCDF format. See
        `time_series.from_netcdf` for details.
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty list, which
        will result in only meta_features features being stored.
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
    scheduler : function, optional
        `dask` scheduler function used to perform feature extraction
        computation. Defaults to `dask.multiprocessing.get`.

    Returns
    -------
    xarray.Dataset
        Featureset with `data_vars` containing feature values and `coords`
        containing labels (`name`) and targets (`target`), if applicable.
    """
    all_time_series = [delayed(time_series.from_netcdf, pure=True)(ts_path)
                       for ts_path in ts_paths]
    all_features = [delayed(featurize_single_ts, pure=True)(ts, features_to_use,
                                                            custom_script_path,
                                                            custom_functions)
                    for ts in all_time_series]
    result = delayed(assemble_featureset, pure=True)(all_features, all_time_series)
    fset = result.compute(get=scheduler)
    if output_path:
        fset.to_netcdf(output_path)

    return fset
