from sklearn.ensemble import RandomForestClassifier as RFC
from celery import Celery
import os
import sys
import pickle
import numpy as np
import uuid
from mltsp import custom_feature_tools as cft
from mltsp import cfg
from mltsp import lc_tools
from mltsp import custom_exceptions
from copy import deepcopy
import uuid


sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "ext"))
os.environ['CELERY_CONFIG_MODULE'] = 'celeryconfig'
celery_app = Celery('celery_fit', broker='amqp://guest@localhost//')


def parse_ts_data(filepath, sep=","):
    """
    """
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep)
    ts_data = ts_data[:, :3].tolist()  # Only using T, M, E; convert to list
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
    return ts_data


@celery_app.task(name='celery_tools.fit_model')
def fit_model(data_dict):
    """
    """
    # Initialize
    ntrees = 1000
    njobs = -1
    rf_fit = RFC(n_estimators=ntrees, max_features='auto', n_jobs=njobs)
    print("Model initialized.")

    # Fit the model to training data:
    print("Fitting the model...")
    rf_fit.fit(data_dict['features'], data_dict['classes'])
    print("Done.")
    del data_dict
    return pickle.dumps(rf_fit)


@celery_app.task(name="celery_tools.pred_featurize_single")
def pred_featurize_single(ts_data, features_to_use, custom_features_script,
                          meta_features, short_fname, sep):
    """
    """
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
    if custom_features_script is not None:
        fname = os.path.join("/tmp", str(uuid.uuid4())[:10] + ".py")
        with open(fname, "w") as f:
            f.writelines(custom_features_script)
        custom_features_script = fname
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


@celery_app.task(name="celery_tools.featurize_ts_data")
def featurize_ts_data(ts_data, short_fname, custom_script_path,
                      object_class, features_to_use):
    """

    """
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
