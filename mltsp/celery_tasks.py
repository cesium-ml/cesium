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


@celery_app.task(name="celery_tasks.check_celery")
def check_celery():
    """Test task."""
    return "OK"

def celery_available():
    """Test Celery task; this is much faster than running `celery status`."""
    try:
        res = check_celery.apply_async()
        return "OK" == res.get(timeout=5)
    except:
        return False


@celery_app.task(name="celery_tasks.featurize_ts_file")
def featurize_ts_file(ts_file_path, features_to_use, metadata={},
                      custom_script_path=None):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_file_path : str
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
    short_fname = util.shorten_fname(ts_file_path)
    t, m, e = ft.parse_ts_data(ts_file_path)
    all_features = ft.featurize_single_ts(t, m, e, features_to_use, metadata,
                                          custom_script_path)
    return (short_fname, all_features)


@celery_app.task(name="celery_tasks.featurize_ts_data")
def featurize_ts_data(t, m, e, label, features_to_use, metadata={},
                      custom_script_path=None):
    """Featurize time-series data file.

    Parameters
    ----------
    t : (n,) or (p, n) array or list of (n_i,) arrays
        Array of time values for a single time series, or a list of arrays (of
        potentially different lengths) of time values for each channel of
        measurement.
    m : (n,) or (p, n) array or list of (n_i,) arrays
        Array or list of measurement values for a single time series, each
        containing p channels of measurements (if applicable).
    e : (n,) or (p, n) array or list of (n_i,) arrays
        Array or list of measurement error values for a single time series,
        each containing p channels of measurements (if applicable).
    label : str or int
        Label identifying which time series is being featurized. Can be a
        string (such as a filename) or an integer index.
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
    all_features = ft.featurize_single_ts(t, m, e, features_to_use, metadata,
                                          custom_script_path)
    return (label, all_features)
