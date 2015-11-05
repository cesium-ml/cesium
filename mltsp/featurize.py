#!/usr/bin/python
# featurize.py

from __future__ import print_function
import shutil
import tempfile
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
from random import shuffle
import os
import tarfile
import numpy as np
import pandas as pd

from . import cfg
from . import util
from . import custom_exceptions
from .celery_tasks import featurize_ts_file as featurize_celery_task
from . import featurize_tools as ft


def generate_featurize_params_list(features_to_use, targets, ts_paths,
        custom_script_path, first_N=None):
    """
    """
    params_list = []
    for ts_path in ts_paths:
        short_fname = util.shorten_fname(ts_path)
        target = targets[targets.filename == short_fname].target.values[0]
        params_list.append((ts_path, custom_script_path, target,
            features_to_use))
    if first_N:
        params_list = params_list[:first_N]
    return params_list


def write_features_to_disk(features_df, featureset_id, in_docker_container):
    """

    """
    features_path = os.path.join(cfg.FEATURES_FOLDER,
            "%s_features.csv" % featureset_id)
    features_cols = [f for f in sorted(features_df.columns) if f != 'target']
    features_df.to_csv(features_path, index=False, columns=features_cols)

    features_targets_path = os.path.join(cfg.FEATURES_FOLDER,
            "%s_features_with_targets.csv" % featureset_id)
    features_targets_cols = ['target'] + [f for f in sorted(features_df.columns)
            if f in cfg.features_to_plot]
    if len(features_targets_cols) < 5: # add more features until we get to 5
        additional_features = [f for f in features_cols if f not in
                cfg.features_to_plot]
        features_targets_cols += additional_features[:(5-len(features_targets_cols))]
    features_df.to_csv(features_targets_path, index=False,
            columns=features_targets_cols)

    np.save(os.path.join(("/tmp" if in_docker_container else
        cfg.FEATURES_FOLDER), "%s_targets.npy" % featureset_id), features_df.target)


def load_and_store_feature_data(features_path, featureset_id="unknown",
        in_docker_container=False, first_N=None):
    features = pd.read_csv(features_path, comment='#', skipinitialspace=True)
    if first_N:
        features = features[:first_N]
    write_features_to_disk(features, featureset_id, in_docker_container)
    if not in_docker_container:
        os.remove(features_path)
    return "Featurization of timeseries data complete."


def featurize_data_archive(headerfile_path, zipfile_path, features_to_use=[],
        featureset_id="unknown", first_N=None, custom_script_path=None,
        in_docker_container=False):
    """Generate features for labeled time series data.

    Features are saved to the file given by
    ``"%s_features.csv" % featureset_id``
    and a list of corresponding targets is saved to the file given by
    ``"%s_targets.npy" % featureset_id``
    in the directory `cfg.FEATURES_FOLDER` (or is later copied there if
    generated inside a Docker container).

    Parameters
    ----------
    headerfile_path : str
        Path to header file containing file names, target names, and
        metadata.
    zipfile_path : str
        Path to the tarball of individual time series files to be used
        for feature generation.
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty
        list, which results in all available features being used.
    featureset_id : str, optional
        RethinkDB ID of the new feature set entry. Defaults to
        "unknown".
    first_N : int, optional
        Integer indicating the maximum number of time series to featurize.
        Can be used to reduce the number of files for testing purposes. If
        `first_N` is None then all time series will be featurized.
    custom_script_path : str, optional
        Path to Python script containing function definitions for the
        generation of any custom features. Defaults to None.
    in_docker_container : bool, optional
        Boolean indicating whether function is being called from inside
        a Docker container. Defaults to False.

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """
    # Parse header file
    targets, metadata = ft.parse_headerfile(headerfile_path)
#    if len(metadata_dict) > 0:
#        features_to_use += list(metadata_dict.values()[0].keys())
    ts_paths = ft.extract_data_archive(zipfile_path)
    params_list = generate_featurize_params_list(features_to_use, targets,
            ts_paths, custom_script_path, first_N)
    # TO-DO: Determine number of cores in cluster:
    res = featurize_celery_task.chunks(params_list, cfg.N_CORES).delay()
    res_list = res.get(timeout=100) # list of list of [fname, features]
    res_list_flat = [res for chunk in res_list for res in chunk]
    for fname, feature_dict in res_list_flat:
        feature_dict['filename'] = fname
    features = pd.DataFrame([feat_dict for fname, feat_dict in res_list_flat])
    features = pd.merge(features, metadata, on='filename')
    features = features.drop('filename', axis=1)
    write_features_to_disk(features, featureset_id, in_docker_container)
    if not in_docker_container:
        os.remove(headerfile_path)
        os.remove(zipfile_path)
    return "Featurization of timeseries data complete."
