import numpy as np
import pandas as pd
import os
import tarfile
import tempfile
from mltsp import cfg
from mltsp import custom_exceptions
from mltsp import util
from mltsp import obs_feature_tools as oft
from mltsp import science_feature_tools as sft
from mltsp import custom_feature_tools as cft


def featurize_single_ts(t, m, e, custom_script_path, features_to_use):
    """Compute feature values for a given single time-series.

    Parameters
    ----------
    t : array-like
        Array of time values for a single time series.
    m : array-like
        Array of measurement values for a single time series.
    e : array-like
        Array of measurement errors for a single time series.
    custom_script_path : str or None
        Path to custom features script .py file, or None.
    features_to_use : list of str
        List of feature names to be generated.

    Returns
    -------
    dict
        Dictionary with feature names as keys.

    """
    obs_features = oft.generate_obs_features(t, m, e, features_to_use)
    science_features = sft.generate_science_features(t, m, e, features_to_use)
    if custom_script_path:
        custom_features = cft.generate_custom_features(custom_script_path, t,
            m, e, features_already_known=dict(list(obs_features.items()) +
            list(science_features.items())))
        custom_features = {key: custom_features[key] for key in
            custom_features.keys() if key in features_to_use}
    else:
        custom_features = {}
    all_features = dict(list(obs_features.items()) +
            list(science_features.items()) + list(custom_features.items()))
    return all_features


def parse_ts_data(filepath, sep=","):
    """
    """
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep)
    ts_data = ts_data[:,:3] # Only using T, M, E
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
    return ts_data.T


def parse_headerfile(headerfile_path):
    """Parse header file.

    Parameters
    ----------
    headerfile_path : str
        Path to header file.
    
    Returns
    -------
    tuple

    """
# TODO throw exception for missing values; can Pandas do this?
    header = pd.read_csv(headerfile_path, comment='#')
    header.filename = header.filename.astype(str)
    header.filename = [util.shorten_fname(f) for f in header.filename]
    if 'class' in header:
        header.rename(columns={'class': 'target'}, inplace=True)
    if 'target' not in header:
        header['target'] = None
    targets = header[['filename', 'target']]
    metadata = header.drop(['target', 'class'], axis=1, errors='ignore')
    return targets, metadata


def extract_data_archive(zipfile_path):
    zipfile = tarfile.open(zipfile_path)
    unzip_dir = tempfile.mkdtemp()
    zipfile.extractall(path=unzip_dir)
    all_paths = [os.path.join(unzip_dir, f) for f in zipfile.getnames()]
    file_paths = [f for f in all_paths if not os.path.isdir(f)]
    return file_paths
