from celery import Celery
import os
import sys
import pickle
import numpy as np
import uuid
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mltsp import obs_feature_tools as oft
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
                          custom_features_script, meta_features={}):
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

    Returns
    -------
    dict
        Dictionary with file name as key, and feature-containing
        dictionaries as value.

    """
    short_fname = os.path.splitext(os.path.basename(ts_data_file_path))[0]
    t, m, e = ctt.parse_ts_data(ts_data_file_path)
    big_features_and_tsdata_dict = {}
    obs_features = oft.generate_obs_features(t, m, e, features_to_use)
    science_features = sft.generate_science_features(t, m, e, features_to_use)
    if custom_features_script:
        custom_features = cft.generate_custom_features(
            custom_features_script, t, m, e,
            features_already_known=dict(obs_features.items() +
                                        science_features.items() +
                                        meta_features.items()))
    else:
        custom_features = {}
    features_dict = dict(obs_features.items() + science_features.items() +
                         custom_features.items() + meta_features.items())
    big_features_and_tsdata_dict[short_fname] = {
        "features_dict": features_dict, "ts_data": zip(t, m, e)}
    return big_features_and_tsdata_dict


# TODO de-dupe this code; remove above function?
@celery_app.task(name="celery_tasks.featurize_ts_data")
def featurize_ts_data(ts_data_file_path, custom_script_path, object_class,
                      features_to_use):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_data_file_path : str
        Time-series data file disk location path.
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
    short_fname = os.path.splitext(os.path.basename(ts_data_file_path))[0]
    t, m, e = ctt.parse_ts_data(ts_data_file_path)
    obs_features = oft.generate_obs_features(t, m, e, features_to_use)
    science_features = sft.generate_science_features(t, m, e, features_to_use)
    if custom_script_path:
        custom_features = cft.generate_custom_features(custom_script_path, t,
            m, e, features_already_known=dict(obs_features.items() +
            science_features.items()))
    else:
        custom_features = {}
    all_features = dict(obs_features.items() + science_features.items() +
                        custom_features.items())
    all_features['class'] = object_class
    return (short_fname, all_features)
