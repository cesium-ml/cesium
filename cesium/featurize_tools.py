import numpy as np
import xarray as xr
import dask.async
from . import obs_feature_tools as oft
from . import science_feature_tools as sft


# TODO now that we use pickle as Celery serializer, this could return something
# more convenient
def featurize_single_ts(ts, features_to_use, custom_script_path=None,
                        custom_functions=None):
    """Compute feature values for a given single time-series. Data is
    returned as dictionaries/lists of lists (as opposed to a more
    convenient DataFrame/DataSet) since it will be serialized as part of
    `celery_tasks.featurize_ts_file`.

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


def assemble_featureset(feature_dicts, targets=None, meta_feature_dicts=None,
                        names=None):
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
    meta_feature_dicts : list
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
    if meta_feature_dicts is not None:
        meta_feature_names = meta_feature_dicts[0].keys()
        combined_feature_dict.update({feature: (['name'], [d[feature] for d in
                                                           meta_feature_dicts])
                                      for feature in meta_feature_names})
    featureset = xr.Dataset(combined_feature_dict)
    if names is not None:
        featureset.coords['name'] = ('name', np.array(names))
    if targets is not None:
        featureset.coords['target'] = ('name', np.array(targets))
    return featureset
