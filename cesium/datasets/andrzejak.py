import logging
import os

import numpy as np
import joblib

from .. import util
from . import util as dsutil


BASE_URL = "https://github.com/cesium-ml/cesium-data/raw/main/andrzejak/"
ZIP_FILES = ["Z.zip", "O.zip", "N.zip", "F.zip", "S.zip"]
MD5SUMS = {
    "Z.zip": "ca5c761d62704c4d2465822e2131f868",
    "O.zip": "666ade7e9d519935103404d4a8d81d7d",
    "N.zip": "0bb8e39ae7530ba17f55b5b4f14e6a02",
    "F.zip": "10f78c004122c609e8eef74de8790af3",
    "S.zip": "1d560ac1e03a5c19bb7f336e270ff286",
}
CACHE_NAME = "andrzejak.pkl"
ARCHIVE_NAME = "andrzejak.tar.gz"
T_MAX = 23.6

logger = logging.getLogger(__name__)


def download_andrzejak(data_dir):
    """Download sample EEG data.

    Three files are created within `data_dir`:
        - andrzejak.tar.gz (containing .dat files for each time series)
        - andrzejak.csv (header file containing class labels)
        - andrzejak.pkl (cached data for faster loading from disk)

    Parameters
    ----------
    data_dir : str
        Path where downloaded data should be stored.

    Returns
    -------
    dict
        Dictionary with attributes:
            - times: list of (4096,) arrays of time values
            - measurements: list of (4096,) arrays of measurement values
            - classes: array of class labels for each time series
            - archive: path to data archive
            - header: path to header file
    """
    logger.warning(f"Downloading data from {BASE_URL}")

    ts_paths = dsutil.download_and_extract_archives(
        data_dir, BASE_URL, ZIP_FILES, MD5SUMS
    )

    # Reformat time series files and add to `andrzejak.tar.gz` archive
    times = []
    measurements = []
    new_ts_paths = []
    classes = []
    for fname in ts_paths:
        m = np.loadtxt(fname)
        t = np.linspace(start=0, stop=T_MAX, num=len(m))
        new_fname = fname[:-4] + ".dat"
        np.savetxt(new_fname, np.vstack((t, m)).T, delimiter=",")
        measurements.append(m)
        times.append(t)
        new_ts_paths.append(new_fname)
        classes.append(os.path.basename(new_fname)[0])  # 'Z001.txt' -> 'Z'
    archive_path = os.path.join(data_dir, ARCHIVE_NAME)
    dsutil.build_time_series_archive(archive_path, new_ts_paths)

    header_path = os.path.join(data_dir, "andrzejak.csv")
    dsutil.write_header(header_path, new_ts_paths, classes)
    util.remove_files(ts_paths + new_ts_paths)

    cache_path = os.path.join(data_dir, CACHE_NAME)
    data = dict(
        times=times,
        measurements=measurements,
        classes=np.array(classes),
        archive=archive_path,
        header=header_path,
    )
    joblib.dump(data, cache_path, compress=3)
    return data


def fetch_andrzejak(data_dir=None):
    """Download (if not already downloaded) and load an example EEG dataset.

    Parameters
    ----------
    data_dir : str, optional
        Path where downloaded data should be stored. Defaults to a subdirectory
        `datasets/andrzejak` within `dsutil.DATA_PATH`.

    Returns
    -------
    dict
        Dictionary with attributes:
            - times: list of (4096,) arrays of time values
            - measurements: list of (4096,) arrays of measurement values
            - classes: array of class labels for each time series
            - archive: path to data archive
            - header: path to header file

    References
    ----------
    Andrzejak, Ralph G., et al. "Indications of nonlinear deterministic and
    finite-dimensional structures in time series of brain electrical activity:
    Dependence on recording region and brain state." *Phys. Rev. E* 64.6
    (2001): 061907.
    """

    if data_dir is None:
        data_dir = os.path.join(dsutil.DATA_PATH, "datasets/andrzejak")
    cache_path = os.path.join(data_dir, CACHE_NAME)

    try:
        data = joblib.load(cache_path)
        logger.warning("Loaded data from cached archive.")
    except (OSError, ValueError):  # missing or incompatible cache
        data = download_andrzejak(data_dir)
    return data
