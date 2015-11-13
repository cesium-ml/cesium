import shutil
import tempfile
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
from random import shuffle
import os
import tarfile
import zipfile
import numpy as np
import pandas as pd

from . import cfg
from . import util
from . import custom_exceptions
from .celery_tasks import featurize_ts_file as featurize_celery_task
from . import featurize_tools as ft


def write_features_to_disk(featureset, featureset_id):
    """Store xray.Dataset of features as netCDF using given featureset key."""
    featureset_path = os.path.join(cfg.FEATURES_FOLDER,
                                   "{}_featureset.nc".format(featureset_id))
    featureset.to_netcdf(featureset_path)


def load_and_store_feature_data(features_path, featureset_id="unknown",
                                first_N=None):
    """Read features from CSV file and store as xray.Dataset."""
    targets, metadata = ft.parse_headerfile(features_path)
    if first_N:
        metadata = metadata[:first_N]
        if targets is not None:
            targets = targets[:first_N]
    featureset = ft.assemble_featureset([], targets, metadata)
    write_features_to_disk(featureset, featureset_id)
    return featureset


def featurize_task_params_list(ts_paths, features_to_use, metadata=None,
                               custom_script_path=None):
    """Create list of tuples containing params for `featurize_celery_task`."""
    params_list = []
    for ts_path in ts_paths:
        if metadata is not None:
            ts_metadata = metadata.loc[util.shorten_fname(ts_path)].to_dict()
        else:
            ts_metadata = {}
        params_list.append((ts_path, features_to_use, ts_metadata,
                            custom_script_path))
    return params_list


def featurize_data_file(data_path, header_path=None, features_to_use=[],
                        featureset_id=None, first_N=None,
                        custom_script_path=None):
    """Generate features for labeled time series data.

    If `featureset_id` is provided, Features are saved as an xray.Dataset in
    netCDF format to the file ``"%s_featureset.nc" % featureset_id`` in the
    directory `cfg.FEATURES_FOLDER`.

    Parameters
    ----------
    data_path : str
        Path to an invidiaul time series file or tarball of multiple time
        series files to be used for feature generation.
    header_path : str, optional
        Path to header file containing file names, target names, and
        metadata.
    features_to_use : list of str, optional
        List of feature names to be generated. Defaults to an empty
        list, which will result in only metadata features being stored.
    featureset_id : str, optional
        RethinkDB ID of the new feature set entry. If provided, the feature set
        will be saved to a file with prefix `featureset_id`.
    first_N : int, optional
        Integer indicating the maximum number of time series to featurize.
        Can be used to reduce the number of files for testing purposes. If
        `first_N` is None then all time series will be featurized.
    custom_script_path : str, optional
        Path to Python script containing function definitions for the
        generation of any custom features. Defaults to None.

    Returns
    -------
    xray.Dataset
        Featureset with `data_vars` containing feature values, and `coords` containing
        filenames and targets (if applicable).

    """
    if tarfile.is_tarfile(data_path) or zipfile.is_zipfile(data_path):
        ts_paths = ft.extract_data_archive(data_path)
        if first_N:
            ts_paths = ts_paths[:first_N]
    else:
        ts_paths = [data_path]

    if header_path:
        targets, metadata = ft.parse_headerfile(header_path, ts_paths)
    else:
        targets, metadata = None, None
    params_list = featurize_task_params_list(ts_paths, features_to_use,
                                             metadata, custom_script_path)

    # TODO: Determine number of cores in cluster:
    res = featurize_celery_task.chunks(params_list, cfg.N_CORES).delay()
    # Returns list of list of pairs [fname, {feature: [values]]
    res_list = res.get(timeout=100)
    res_flat = [res for chunk in res_list for res in chunk]
    fnames, feature_dicts = zip(*res_flat)

    if targets is not None:
        fname_targets = targets.loc[list(fnames)]
    else:
        fname_targets = None
    if metadata is not None:
        fname_metadata = metadata.loc[list(fnames)]
    else:
        fname_metadata = None, None
    featureset = ft.assemble_featureset(feature_dicts, fname_targets,
                                        fname_metadata, fnames)

    if featureset_id:
        write_features_to_disk(featureset, featureset_id)
#    if not in_docker_container:
#        os.remove(header_path)
#        os.remove(data_path)
    return featureset
