from celery import Celery
import os
import sys
import pickle
import numpy as np
import uuid
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mltsp import custom_feature_tools as cft
from mltsp import cfg
from mltsp import lc_tools
from mltsp import celery_task_tools as ctt
from copy import deepcopy
import uuid


#sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),
#                             "mltsp/ext"))
os.environ['CELERY_CONFIG_MODULE'] = 'mltsp.ext.celeryconfig'
celery_app = Celery('celery_fit', broker='amqp://guest@localhost//')


@celery_app.task(name='celery_tasks.fit_model')
def fit_and_store_model(featureset_name, featureset_key, model_type,
                        in_docker_container):
    """
    """
    data_dict = ctt.read_features_data_from_disk(featureset_key)

    created_file_name = ctt.create_and_pickle_model(
        data_dict, featureset_key, model_type, in_docker_container)
    return created_file_name


@celery_app.task(name="celery_tasks.pred_featurize_single")
def pred_featurize_single(ts_data_file_path, features_to_use,
                          custom_features_script, meta_features, short_fname,
                          sep):
    """
    """
    ts_data = ctt.parse_ts_data(ts_data_file_path)
    big_features_and_tsdata_dict = {}
    # Generate features:
    if len(list(set(features_to_use) & set(cfg.features_list))) > 0:
        timeseries_features = lc_tools.generate_timeseries_features(
            deepcopy(ts_data), sep=sep, ts_data_passed_directly=True)
    else:
        timeseries_features = {}
    if len(list(set(features_to_use) &
                set(cfg.features_list_science))) > 0:
        from mltsp.TCP.Software.ingest_tools import generate_science_features
        science_features = generate_science_features.generate(
            ts_data=deepcopy(ts_data))
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
def featurize_ts_data(ts_data_file_path, short_fname, custom_script_path,
                      object_class, features_to_use):
    """

    """
    ts_data = ctt.parse_ts_data(ts_data_file_path)
    # Generate general/cadence-related TS features, if to be used
    if len(set(features_to_use) & set(cfg.features_list)) > 0:
        timeseries_features = (
            lc_tools.generate_timeseries_features(
                deepcopy(ts_data),
                classname=object_class,
                sep=',', ts_data_passed_directly=True))
    else:
        timeseries_features = {}
    # Generate TCP TS features, if to be used
    if len(
            set(features_to_use) &
            set(cfg.features_list_science)) > 0:
        from mltsp.TCP.Software.ingest_tools import \
            generate_science_features
        science_features = generate_science_features.generate(
            ts_data=ts_data)
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
