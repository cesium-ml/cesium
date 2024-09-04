import copy
from collections.abc import Iterable
import numpy as np
import pandas as pd
import dask
import dask.threaded
from dask import delayed
from dask.local import reraise
from dask.threaded import pack_exception
from dask.optimization import cull
from sklearn.impute import SimpleImputer as Imputer

from . import time_series
from .time_series import TimeSeries
from .features import generate_dask_graph

__all__ = [
    "featurize_time_series",
    "featurize_single_ts",
    "featurize_ts_files",
    "assemble_featureset",
]


def featurize_single_ts(
    ts,
    features_to_use,
    custom_script_path=None,
    custom_functions=None,
    raise_exceptions=True,
):
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
    raise_exceptions : bool, optional
        If True, exceptions during feature computation are raised immediately;
        if False, exceptions are supressed and `np.nan` is returned for the
        given feature and any dependent features. Defaults to True.

    Returns
    -------
    dict
        Dictionary with feature names as keys, lists of feature values (one per
        channel) as values.
    """
    # Initialize empty feature array for all channels
    feature_values = np.empty((len(features_to_use), ts.n_channels))
    for (t_i, m_i, e_i), i in zip(ts.channels(), range(ts.n_channels)):
        feature_graph = generate_dask_graph(t_i, m_i, e_i)
        feature_graph.update(ts.meta_features)

        if custom_functions:
            # If values in custom_functions are functions, add calls to graph
            if all(hasattr(v, "__call__") for v in custom_functions.values()):
                feature_graph.update(
                    {feat: f(t_i, m_i, e_i) for feat, f in custom_functions.items()}
                )
            # Otherwise, custom_functions is another dask graph
            else:
                feature_graph.update(custom_functions)

        def noop(e, tb):
            pass

        # Do not execute in parallel; parallelization has already taken place
        # at the level of time series, so we compute features for a single time
        # series in serial.
        if raise_exceptions:
            raise_callback = reraise
        else:
            raise_callback = noop
        culled_feature_graph, _ = cull(feature_graph, features_to_use)
        dask_values = dask.get(
            culled_feature_graph,
            features_to_use,
            raise_exception=raise_callback,
            pack_exception=pack_exception,
        )
        feature_values[:, i] = [
            x if not isinstance(x, Exception) else np.nan for x in dask_values
        ]
    index = pd.MultiIndex.from_product(
        (features_to_use, range(ts.n_channels)), names=("feature", "channel")
    )
    return pd.Series(feature_values.ravel(), index=index)


def assemble_featureset(
    features_list, time_series=None, meta_features_list=None, names=None
):
    """Transforms raw feature data (as returned by `featurize_single_ts`) into
    a pd.DataFrame.

    Parameters
    ----------
    features_list : list of pd.Series
        List of series (one per time series file) with (feature name, channel)
        multiindex.
    time_series : list of TimeSeries
        If provided, the name and metafeatures from the time series objects
        will be used, overriding the `meta_features_list` and `names` values.
    meta_features_list : list of dict
        If provided, the columns of `metadata` will be added to the featureset.
    names : list of str
        If provided, the (row) index of the featureset will be set accordingly.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns containing feature values, indexed by name.
    """
    if time_series is not None:
        meta_features_list, names = zip(
            *[(ts.meta_features, ts.name) for ts in time_series]
        )
    if len(features_list) > 0:
        feat_df = pd.concat(features_list, axis=1, ignore_index=True).T
        feat_df.index = names
    else:
        feat_df = pd.DataFrame(index=names)

    if meta_features_list and any(meta_features_list):  # not all empty dicts
        meta_df = pd.DataFrame(list(meta_features_list), index=names)
        meta_df.columns = pd.MultiIndex.from_tuples(
            [(c, "") for c in meta_df], names=["feature", "channel"]
        )
        feat_df = pd.concat((feat_df, meta_df), axis=1)

    return feat_df


# TODO should this be changed to use TimeSeries objects? or maybe an optional
# argument for TimeSeries? some redundancy here...
def featurize_time_series(
    times,
    values,
    errors=None,
    features_to_use=[],
    meta_features={},
    names=None,
    custom_script_path=None,
    custom_functions=None,
    scheduler=dask.threaded.get,
    raise_exceptions=True,
):
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
    featurized separately, and the index of the output featureset will contain
    a `channel` coordinate.

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
    meta_features : dict/Pandas.Series or list of dicts/Pandas.DataFrame
        dict/Series (for a single time series) or DataFrame (for multiple time
        series) of metafeature information; features are added to the output
        featureset, and their values are consumable by custom feature scripts.
    names : str or list of str, optional
        Name or list of names for each time series, if applicable; will be
        stored in the (row) index of the featureset.
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
        computation. Defaults to `dask.threaded.get`.
    raise_exceptions : bool, optional
        If True, exceptions during feature computation are raised immediately;
        if False, exceptions are supressed and `np.nan` is returned for the
        given feature and any dependent features. Defaults to True.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns containing feature values, indexed by name.
    """
    if times is None:
        times = copy.deepcopy(values)
        if isinstance(times, np.ndarray) and (times.ndim == 1 or 1 in times.shape):
            times[:] = np.linspace(0.0, time_series.DEFAULT_MAX_TIME, times.size)
        else:
            for t in times:
                if isinstance(t, np.ndarray) and (t.ndim == 1 or 1 in t.shape):
                    t[:] = np.linspace(0.0, time_series.DEFAULT_MAX_TIME, t.size)
                else:
                    for t_i in t:
                        t_i[:] = np.linspace(
                            0.0, time_series.DEFAULT_MAX_TIME, t_i.size
                        )

    if errors is None:
        errors = copy.deepcopy(values)
        if isinstance(errors, np.ndarray) and (errors.ndim == 1 or 1 in errors.shape):
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

    if names is None:
        names = np.arange(len(times))

    if isinstance(meta_features, pd.Series):
        meta_features = meta_features.to_dict()
    meta_features = pd.DataFrame(meta_features, index=names)

    all_time_series = [
        delayed(
            TimeSeries(t, m, e, meta_features=meta_features.loc[name], name=name),
            pure=True,
        )
        for t, m, e, name in zip(times, values, errors, names)
    ]

    all_features = [
        delayed(featurize_single_ts, pure=True)(
            ts, features_to_use, custom_script_path, custom_functions, raise_exceptions
        )
        for ts in all_time_series
    ]
    result = delayed(assemble_featureset, pure=True)(all_features, all_time_series)
    return result.compute(scheduler=scheduler)


def featurize_ts_files(
    ts_paths,
    features_to_use,
    custom_script_path=None,
    custom_functions=None,
    scheduler=dask.threaded.get,
    raise_exceptions=True,
):
    """Feature generation function for on-disk time series (.npz) files.

    By default, computes features concurrently using the
    `dask.threaded.get` scheduler. Other possible options include
    `dask.local.get` for synchronous computation (e.g., when debugging),
    or `dask.distributed.Executor.get` for distributed computation.

    In the case of multichannel measurements, each channel will be
    featurized separately, and the index of the output featureset will contain
    a `channel` coordinate.

    Parameters
    ----------
    ts_paths : list of str
        List of paths to time series data, stored in `numpy` .npz format.
        See `time_series.load` for details.
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
        computation. Defaults to `dask.threaded.get`.
    raise_exceptions : bool, optional
        If True, exceptions during feature computation are raised immediately;
        if False, exceptions are supressed and `np.nan` is returned for the
        given feature and any dependent features. Defaults to True.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns containing feature values, indexed by name.
    """
    all_time_series = [
        delayed(time_series.load, pure=True)(ts_path) for ts_path in ts_paths
    ]
    all_features = [
        delayed(featurize_single_ts, pure=True)(
            ts, features_to_use, custom_script_path, custom_functions, raise_exceptions
        )
        for ts in all_time_series
    ]
    names, meta_feats, all_labels = zip(
        *[(ts.name, ts.meta_features, ts.label) for ts in all_time_series]
    )
    result = delayed(assemble_featureset, pure=True)(
        all_features, meta_features_list=meta_feats, names=names
    )
    fset, labels = dask.compute(result, all_labels, scheduler=scheduler)

    return fset, labels


def impute_featureset(
    fset, strategy="constant", value=None, max_value=1e20, inplace=False
):
    """Replace NaN/Inf values with imputed values as defined by `strategy`.
    Output should satisfy `sklearn.validation.assert_all_finite` so that
    training a model will not produce an error.

    Parameters
    ----------
    strategy : str, optional
    The imputation strategy. Defaults to 'constant'.

        - 'constant': replace all missing with `value`
        - 'mean': replace all missing with mean along `axis`
        - 'median': replace all missing with median along `axis`
        - 'most_frequent': replace all missing with mode along `axis`

    value : float or None, optional
        Replacement value to use for `strategy='constant'`. Defaults to
        `None`, in which case a very large negative value is used (a
        good choice for e.g. random forests).

    max_value : float, optional
        Maximum (absolute) value above which values are treated as infinite.
        Used to prevent overflow when fitting `sklearn` models.

    inplace : bool, optional
        If True, fill in place. If False, return a copy.

    Returns
    -------
    pd.DataFrame
        Feature data frame wth no missing/infinite values.
    """
    if not inplace:
        fset = fset.copy()
    fset.values[np.isnan(fset.values)] = np.inf  # avoid NaN comparison warnings
    fset.values[np.abs(fset.values) > max_value] = np.nan
    if strategy == "constant":
        if value is None:
            # If no fill-in value is provided, use a large negative value
            value = -2.0 * np.nanmax(np.abs(fset.values))
        fset.fillna(value, inplace=True)
    elif strategy in ("mean", "median", "most_frequent"):
        imputer = Imputer(strategy=strategy)
        fset.values[:] = imputer.fit_transform(fset.values)
    else:
        raise NotImplementedError(
            "Imputation strategy '{}' not" "recognized.".format(strategy)
        )
    return fset


def save_featureset(fset, path, **kwargs):
    """Save feature DataFrame in .npz format.

    Can optionally store class labels/targets and other metadata. All other
    keyword arguments will be passed on to `np.savez`; data frames are saved as
    record arrays and converted back into data frames by `load_featureset`.

    Parameters
    ----------
    fset : pd.DataFrame
        Feature data frame to be saved.
    path : str
        Path to store feature data.
    kwargs : dict of array or data frame
        Additional keyword arguments, e.g.:
        labels -> class labels
        preds -> predicted class labels
        pred_probs -> (n_sample, n_class) data frame of class probabilities
    """
    # Transpose to properly handle MultiIndex columns
    kwargs["features"] = fset.T

    for k, v in kwargs.items():
        if isinstance(v, pd.DataFrame):
            arr = v.to_records()
            dt_list = arr.dtype.descr
            # Change type of indices from object to str
            for i, (name, dt) in enumerate(dt_list):
                if dt.endswith("O"):
                    size = max(len(str(x)) for x in arr[name])
                    dt_list[i] = (name, f"U{size}")
            kwargs[k] = arr.astype(dt_list)

        # Ignore null values, e.g. for unlabeled data
        if all(el is None for el in v):
            kwargs[k] = []

    # Bypass savez to allow for `allow_pickle` keyword
    # See also https://github.com/numpy/numpy/pull/27335
    np.lib._npyio_impl._savez(path, [], kwargs, compress=True, allow_pickle=False)


def load_featureset(path):
    """Load feature DataFrame from .npz file.

    Feature information is returned as a single DataFrame, while any other
    arrays that were saved (class labels/predictions, etc.) are returned in a
    single dictionary.

    Parameters
    ----------
    path : str
        Path where feature data is stored.

    Returns
    -------
    pd.DataFrame
        Feature data frame to be saved.
    dict
        Additional variables passed to `save_featureset`, including labels, etc.
    """
    with np.load(path, allow_pickle=False) as npz_file:
        data = dict(npz_file)

    # Transpose to properly handle MultiIndex columns
    fset = pd.DataFrame.from_records(data.pop("features"), index=["feature", "channel"])
    fset = fset.T

    # Channels loaded from disk are now either empty strings or
    # channel numbers (also strings), stored in an object array.
    #
    # We map non-empty channel numbers back to ints.
    channels = fset.columns.levels[1]
    int_channels = [int(c) if str(c).isdigit() else "" for c in channels]
    fset.columns = fset.columns.set_levels(levels=int_channels, level=1)

    for k, v in data.items():
        if len(v.dtype) > 0:
            data[k] = pd.DataFrame.from_records(v, index="index")

    return fset, data
