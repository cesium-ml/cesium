import numpy as np
import pandas as pd
import xray
import os
import tarfile
import tempfile
import zipfile
from mltsp import custom_exceptions
from mltsp import util
from mltsp import obs_feature_tools as oft
from mltsp import science_feature_tools as sft
from mltsp import custom_feature_tools as cft


def featurize_single_ts(t, m, e, features_to_use, meta_features={},
                        custom_script_path=None):
    """Compute feature values for a given single time-series. Data is
    manipulated as dictionaries/lists of lists (as opposed to a more
    convenient DataFrame/DataSet) since it will be serialized as part of
    `celery_tasks.featurize_ts_file`.

    Parameters
    ----------
    t : (n,) array
        Array of n time values for a single time series.
    m : (n,) or (n, p) array
        Array of n measurement values for a single time series, each containing
        p channels of measurements (if applicable).
    e : (n,) or (n, p) array
        Array of n measurement errors for a single time series, each containing
        p channels of errors (if applicable).
    features_to_use : list of str
        List of feature names to be generated.
    meta_features : dict
        Dictionary of metafeature information to potentially be consumed by
        custom feature scripts.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.

    Returns
    -------
    dict
        Dictionary with feature names as keys, lists of feature values (one per
        channel) as values.

    """
    if len(m.shape) == 1:
        m = np.reshape(m, (-1, 1))
        e = np.reshape(e, (-1, 1))

    all_feature_lists = {feature: m.shape[1] * [0.]
                         for feature in features_to_use}
    for i in range(m.shape[1]):  # featurize each channel
        obs_features = oft.generate_obs_features(t, m[:, i], e[:, i],
                                                 features_to_use)
        science_features = sft.generate_science_features(t, m[:, i], e[:, i],
                                                         features_to_use)
        if custom_script_path:
            custom_features = cft.generate_custom_features(
                custom_script_path, t, m[:, i], e[:, i],
                features_already_known=dict(list(obs_features.items()) +
                                            list(science_features.items()) +
                                            list(meta_features.items())))
            custom_features = {key: custom_features[key]
                               for key in custom_features.keys()
                               if key in features_to_use}
        else:
            custom_features = {}

        # We set values in this order so that custom features take priority
        # over MLTSP features in the case of name conflicts
        for feature, value in (list(obs_features.items()) +
                               list(science_features.items()) +
                               list(custom_features.items())):
            all_feature_lists[feature][i] = value

    return all_feature_lists


def assemble_featureset(feature_dicts, targets=None, metadata=None, names=None):
    """Transforms raw feature data (as returned by `featurize_single_ts`) into
    an xray.Dataset.

    Parameters
    ----------
    feature_dicts : list
        List of dicts (one per time series file) with feature names as keys and
        lists of feature values (one per channel) as values.

    targets : list or pandas.Series, optional
        If provided, the `target` coordinate of the featureset xray.Dataset
        will be set accordingly.

    metadata : pandas.DataFrame, optional
        If provided, the columns of `metadata` will be added as data variables
        to the featureset xray.Dataset.

    Returns
    -------
    xray.Dataset
        Featureset with `data_vars` containing feature values, and `coords`
        containing filenames and targets (if applicable).

    """

    feature_names = feature_dicts[0].keys() if len(feature_dicts) > 0 else []
    combined_feature_dict = {feature: (['name', 'channel'],
                                       [d[feature] for d in feature_dicts])
                             for feature in feature_names}
    if metadata is not None:
        combined_feature_dict.update({feature: (['name'], metadata[feature].values)
                                      for feature in metadata.columns})
    featureset = xray.Dataset(combined_feature_dict)
    if names is not None:
        featureset['name'].values = names
    if targets is not None:
        featureset['target'] = targets
    return featureset


def parse_ts_data(filepath, sep=","):
    """Parses time series data file and returns np.ndarray with 1-3 columns."""
    with open(filepath) as f:
        ts_data = np.loadtxt(f, delimiter=sep)
    ts_data = ts_data[:, :3]  # Only using T, M, E
    for row in ts_data:
        if len(row) < 2:
            raise custom_exceptions.DataFormatError(
                "Incomplete or improperly formatted time "
                "series data file provided.")
    return ts_data.T


def parse_headerfile(headerfile_path, files_to_include=None):
    """Parse header file.

    Parameters
    ----------
    headerfile_path : str
        Path to header file.

    files_to_include : list, optional
        If provided, only return the subset of rows from the header
        corresponding to the given filenames.

    Returns
    -------
    pandas.Series or None
        Target column from header file (if present)

    pandas.DataFrame
        Feature data from other columns besides filename, target (can be empty)
    """
    header = pd.read_csv(headerfile_path, comment='#')
    if 'filename' in header:
        header.index = [util.shorten_fname(str(f)) for f in header['filename']]
        header.drop('filename', axis=1, inplace=True)
    if files_to_include:
        short_fnames_to_include = [util.shorten_fname(str(f))
                                   for f in files_to_include]
        header = header.loc[short_fnames_to_include]
    if 'target' in header:
        targets = header['target']
    elif 'class' in header:
        targets = header['class']
    else:
        targets = None
    feature_data = header.drop(['target', 'class'], axis=1, errors='ignore')
    return targets, feature_data


def extract_data_archive(archive_path):
    """Extract zip- or tarfile of time series file and return file paths."""
    if tarfile.is_tarfile(archive_path):
        archive = tarfile.open(archive_path)
    elif zipfile.is_zipfile(archive_path):
        archive = zipfile.open(archive_path)
    else:
        raise ValueError('{} is not a valid zip- or '
                         'tarfile.'.format(archive_path))
    extract_dir = tempfile.mkdtemp()
    archive.extractall(path=extract_dir)
    all_paths = [os.path.join(extract_dir, f) for f in archive.getnames()]
    file_paths = [f for f in all_paths if not os.path.isdir(f)]
    return file_paths
