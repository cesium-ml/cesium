import numpy.testing as npt
import os
from os.path import join as pjoin
import shutil
import numpy as np
from cesium import data_management
from cesium import util


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_parse_ts_data():
    """Test time series data file parsing."""
    t, m, e = data_management.parse_ts_data(pjoin(DATA_PATH,
                                                  "dotastro_215153.dat"))
    assert t.ndim == 1
    assert len(t) == len(m) and len(m) == len(e)


def test_parse_headerfile():
    """Test header file parsing."""
    labels, metadata = data_management.parse_headerfile(
        pjoin(DATA_PATH, "asas_training_subset_classes_with_metadata.dat"))
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(labels.loc["217801"], "Mira")
    npt.assert_almost_equal(metadata.loc["224635"].meta1, 0.330610932539)


def test_parsing_and_saving(tmpdir):
    data_file_path = pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz")
    header_path = pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat")
    time_series = data_management.parse_and_store_ts_data(
        data_file_path, str(tmpdir), header_path, cleanup_archive=False,
        cleanup_header=False)
    for ts in time_series:
        assert isinstance(ts, str)
        assert os.path.exists(ts)
