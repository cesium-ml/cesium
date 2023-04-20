import logging
import os

import joblib

from .. import util
from .. import data_management
from . import util as dsutil


# TODO replace with real host
BASE_URL = "https://github.com/cesium-ml/cesium-data/raw/main/asas_training/"
MD5SUMS = {"asas_training_set.tar.gz": "02c65e90d23999ec1c59ad56a78de477"}
ARCHIVE_NAME = "asas_training_set.tar.gz"
HEADER_FILE = "asas_training_set_classes_with_metadata.dat"
CACHE_NAME = "asas_training_set.pkl"

logger = logging.getLogger(__name__)


def download_asas_training(data_dir):
    """Download sample light curve data.

    Three files are created within `data_dir`:
        - asas_training.tar.gz (containing .dat files for each time series)
        - asas_training.csv (header file containing class labels)
        - asas_training.pkl (cached data for faster loading from disk)

     Meta-features `meta1`, `meta2`, and `meta3` are randomly generated for
     testing purposes only.

    Parameters
    ----------
    data_dir: str
        Path where downloaded data should be stored.

    Returns
    -------
    dict
        Dictionary with attributes:
            - times: list of arrays of time values
            - measurements: list of arrays of measurement values
            - errors: list of arrays of error values
            - classes: array of class labels for each time series
            - metadata: DataFrame of metafeature values indexed by file
            - archive: path to data archive
            - header: path to header file
    """
    logger.warning(f"Downloading data from {BASE_URL}")

    header_path = dsutil.download_file(data_dir, BASE_URL, HEADER_FILE)
    ts_paths = dsutil.download_and_extract_archives(
        data_dir, BASE_URL, [ARCHIVE_NAME], MD5SUMS, remove_archive=False
    )
    archive_path = os.path.join(data_dir, ARCHIVE_NAME)

    times = []
    measurements = []
    errors = []
    for fname in ts_paths:
        t, m, e = data_management.parse_ts_data(fname)
        times.append(t)
        measurements.append(m)
        errors.append(e)
    util.remove_files(ts_paths)

    classes, metadata = data_management.parse_headerfile(header_path, ts_paths)

    cache_path = os.path.join(data_dir, CACHE_NAME)
    data = dict(
        times=times,
        measurements=measurements,
        errors=errors,
        classes=classes,
        metadata=metadata,
        archive=archive_path,
        header=header_path,
    )
    joblib.dump(data, cache_path, compress=3)
    return data


def fetch_asas_training(data_dir=None):
    """Download (if not already downloaded) and load example light curve data.

    Parameters
    ----------
    data_dir: str, optional
        Path where downloaded data should be stored. Defaults to
        a subdirectory `datasets/asas_training` within `dsutil.DATA_PATH`.

    Returns
    -------
    dict
        Dictionary attributes:
            - times: list of arrays of time values
            - measurements: list of arrays of measurement values
            - errors: list of arrays of error values
            - classes: Series of classes for each time series indexed by file
            - metadata: DataFrame of metafeature values indexed by file
            - archive: path to data archive
            - header: path to header file

    References
    ----------
    Richards, J. W., Starr, D. L., Miller, A. a., Bloom, J. S., Butler, N. R.,
    Brink, H., & Crellin-Quick, A. (2012). Construction of a Calibrated
    Probabilistic Classification Catalog: Application to 50k Variable Sources
    in the All-Sky Automated Survey. The Astrophysical Journal Supplement
    Series, 203(2), 32. http://doi.org/10.1088/0067-0049/203/2/32
    """

    if data_dir is None:
        data_dir = os.path.join(dsutil.DATA_PATH, "datasets/asas_training")
    cache_path = os.path.join(data_dir, CACHE_NAME)

    try:
        data = joblib.load(cache_path)
        logger.warning("Loaded data from cached archive.")
    except (OSError, ValueError):  # missing or incompatible cache
        data = download_asas_training(data_dir)
    return data
