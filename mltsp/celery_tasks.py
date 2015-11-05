from celery import Celery
import os
import sys
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mltsp import cfg
from mltsp import util
from mltsp import featurize_tools as ft
from mltsp import obs_feature_tools as oft
from mltsp import science_feature_tools as sft
from mltsp import custom_feature_tools as cft


os.environ['CELERY_CONFIG_MODULE'] = cfg.CELERY_CONFIG
celery_app = Celery('celery_fit', broker=cfg.CELERY_BROKER)


@celery_app.task(name="celery_tasks.featurize_ts_data")
def featurize_ts_file(ts_data_file_path, custom_script_path, target,
                      features_to_use):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_data_file_path : str
        Time-series data file disk location path.
    custom_script_path : str or None
        Path to custom features script .py file, or None.
    target : str or float
        Target value/class name.
    features_to_use : list of str
        List of feature names to be generated.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the file name and
        second element is a dictionary of features.

    """
    short_fname = util.shorten_fname(ts_data_file_path)
    t, m, e = ft.parse_ts_data(ts_data_file_path)
    all_features = ft.featurize_single_ts(t, m, e, custom_script_path,
                                           features_to_use)
    all_features['target'] = target
    return (short_fname, all_features)
