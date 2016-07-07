import copy
import os
import numpy as np
import pandas as pd
from celery import group
from .celery_tasks import celery_available
from .celery_tasks import featurize_ts_data as featurize_data_task
from .celery_tasks import featurize_ts_file as featurize_file_task
from . import data_management
from . import featurize_tools as ft
from . import time_series
from .time_series import TimeSeries


__all__ = ['load_and_store_feature_data', 'featurize_time_series']


def load_and_store_feature_data(features_path, output_path):
    """Read features from CSV file and save as an xarray.Dataset."""
    targets, meta_features = data_management.parse_headerfile(features_path)
    meta_feature_dicts = meta_features.to_dict(orient='record')
    featureset = ft.assemble_featureset([], targets, meta_feature_dicts)
    featureset.to_netcdf(output_path)
    return featureset


# TODO should this be changed to use TimeSeries objects? or maybe an optional
# argument for TimeSeries? some redundancy here...
def featurize_time_series(times, values, errors=None, features_to_use=[],
                          targets=None, meta_features={}, labels=None,
                          custom_script_path=None, custom_functions=None,
                          use_celery=False):
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

    if not all([isinstance(x, (list, tuple))
                for x in (times, values, errors)]):
        raise TypeError("times, values, and errors have incompatible types")

    meta_features = pd.DataFrame(meta_features, index=labels)

    if use_celery:
        if not celery_available():
            raise RuntimeError("Celery unavailable; please check your Celery "
                               "configuration or set `use_celery=False`.")

        all_time_series = [TimeSeries(t, m, e, meta_features.loc[label],
                                      name=label)
                           for t, m, e, label in zip(times, values, errors,
                                                     labels)]
        celery_res = group(featurize_data_task.s(ts, features_to_use,
                                                 custom_script_path,
                                                 custom_functions)
                           for ts in all_time_series)()
        res_list = celery_res.get()
        labels, feature_dicts = zip(*res_list)
        if targets is not None:
            targets = targets.loc[list(labels)]
        meta_features = meta_features.loc[list(labels)]
        meta_feature_dicts = meta_features.to_dict(orient='record')
    else:
        feature_dicts = []
        meta_feature_dicts = []
        for t, m, e, label in zip(times, values, errors, labels):
            ts = TimeSeries(t, m, e, meta_features=meta_features.loc[label])
            feature_dict = ft.featurize_single_ts(ts, features_to_use,
                                                  custom_script_path=custom_script_path,
                                                  custom_functions=custom_functions)
            feature_dicts.append(feature_dict)
            meta_feature_dicts.append(ts.meta_features)
    return ft.assemble_featureset(feature_dicts, targets, meta_feature_dicts,
                                  labels)
