from celery import Celery
import os
import sys
import numpy as np
import pandas as pd
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
def featurize_ts_file(ts_data_file_path, features_to_use, metadata={},
                      custom_script_path=None):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_data_file_path : str
        Time-series data file disk location path.
    features_to_use : list of str
        List of names of features to be generated.
    metadata : dict, optional
        Dictionary containing metafeature names and values for the given time
        series, if applicable.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the file name and
        second element is a dictionary of features.

    """
    short_fname = util.shorten_fname(ts_data_file_path)
    t, m, e = ft.parse_ts_data(ts_data_file_path)
    all_features = ft.featurize_single_ts(t, m, e, features_to_use, metadata,
                                          custom_script_path)
    return (short_fname, all_features)
