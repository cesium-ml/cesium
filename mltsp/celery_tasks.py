from celery import Celery
import os
import sys
import pickle
import numpy as np
import uuid
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mltsp import observation_feature_tools as oft
from mltsp import science_feature_tools as sft
from mltsp import custom_feature_tools as cft
from mltsp import cfg
from mltsp import celery_task_tools as ctt
from copy import deepcopy


os.environ['CELERY_CONFIG_MODULE'] = cfg.CELERY_CONFIG
celery_app = Celery('celery_fit', broker=cfg.CELERY_BROKER)


@celery_app.task(name='celery_tasks.fit_model')
def fit_and_store_model(featureset_name, featureset_key, model_type,
                        in_docker_container):
    """Read features, fit classifier & save it to disk.

    This function is a Celery task.

    Parameters
    ----------
    featureset_name : str
        Name of the feature set on which to build the model.
    featureset_key : str
        Feature set ID/key.
    model_type : str
        Abbreviation of scikit-learn model type to build, e.g. "RF".
    in_docker_container : bool
        Boolean indicating whether currently running in Docker container.

    Returns
    -------
    str
        Path to serialized classifier object on disk.

    """
    data_dict = ctt.read_features_data_from_disk(featureset_key)

    created_file_name = ctt.create_and_pickle_model(
        data_dict, featureset_key, model_type, in_docker_container)
    return created_file_name


@celery_app.task(name="celery_tasks.pred_featurize_single")
def pred_featurize_single(ts_data_file_path, features_to_use,
                          custom_features_script, meta_features, short_fname,
                          sep):
    """Featurize unlabeled time-series data file for model prediciton.

    This function is a Celery task.

    Parameters
    ----------
    ts_data_file_path : str
        Time-series data file disk location path.
    features_to_use : list of str
        List of feature names to be generated.
    custom_features_script : str or None
        Path to custom features script .py file, or None.
    meta_features : dict
        Dictionary of associated meta features.
    short_fname : str
        File name without full path or type suffix.
    sep : str
        Delimiting character in data file, e.g. ",".

    Returns
    -------
    dict
        Dictionary with file name as key, and feature-containing
        dictionaries as value.

    """
    ts_data = ctt.parse_ts_data(ts_data_file_path)
    big_features_and_tsdata_dict = {}
    # Generate features:
    if len(list(set(features_to_use) & set(cfg.features_list))) > 0:
        timeseries_features = oft.generate_timeseries_features(
            deepcopy(ts_data), sep=sep, ts_data_passed_directly=True)
    else:
        timeseries_features = {}
    if len(list(set(features_to_use) &
                set(cfg.features_list_science))) > 0:
        science_features = sft.generate_science_features(ts_data)
    else:
        science_features = {}
    if custom_features_script:
        custom_features = cft.generate_custom_features(
            custom_script_path=custom_features_script, path_to_csv=None,
            features_already_known=dict(
                list(timeseries_features.items()) + list(science_features.items()) +
                (
                    list(meta_features[short_fname].items()) if short_fname in
                    meta_features else list({}.items()))), ts_data=ts_data)
        if (isinstance(custom_features, list) and
                len(custom_features) == 1):
            custom_features = custom_features[0]
        elif (isinstance(custom_features, list) and
              len(custom_features) == 0):
            custom_features = {}
        elif (isinstance(custom_features, list) and
              len(custom_features) > 1):
            raise("len(custom_features) > 1 for single TS data obj")
        elif not isinstance(custom_features, (list, dict)):
            raise("custom_features ret by cft module is of an invalid type")
    else:
        custom_features = {}
    features_dict = dict(
        list(timeseries_features.items()) + list(science_features.items()) +
        list(custom_features.items()) +
        (list(meta_features[short_fname].items()) if short_fname
         in meta_features else list({}.items())))
    big_features_and_tsdata_dict[short_fname] = {
        "features_dict": features_dict, "ts_data": ts_data}
    return big_features_and_tsdata_dict


@celery_app.task(name="celery_tasks.featurize_ts_data")
# TODO can't short_fname be generated instead of passed in?
def featurize_ts_data(ts_data_file_path, short_fname, custom_script_path,
                      object_class, features_to_use):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_data_file_path : str
        Time-series data file disk location path.
    short_fname : str
        File name without full path or type suffix.
    custom_script_path : str or None
        Path to custom features script .py file, or None.
    object_class : str
        Class name.
    features_to_use : list of str
        List of feature names to be generated.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the file name and
        second element is a dictionary of features.

    """
    ts_data = ctt.parse_ts_data(ts_data_file_path)
    # Generate general/cadence-related TS features, if to be used
    if len(set(features_to_use) & set(cfg.features_list)) > 0:
        timeseries_features = oft.generate_observation_features(ts_data)
    else:
        timeseries_features = {}
    # Generate TS science features, if to be used
    if len(
            set(features_to_use) &
            set(cfg.features_list_science)) > 0:
        science_features = sft.generate_science_features(ts_data)
    else:
        science_features = {}
    # Generate custom features, if any
    if custom_script_path:
        custom_features = cft.generate_custom_features(
            custom_script_path=custom_script_path,
            path_to_csv=None,
            features_already_known=dict(
                list(timeseries_features.items()) +
                list(science_features.items())),
            ts_data=deepcopy(ts_data))[0]
    else:
        custom_features = {}
    # Combine all features into single dict
    all_features = dict(
        list(timeseries_features.items()) +
        list(science_features.items()) +
        list(custom_features.items()))
    all_features['class'] = object_class
    return (short_fname, all_features)
