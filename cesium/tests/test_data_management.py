from io import StringIO
import os
from os.path import join as pjoin
import numpy as np
from cesium import data_management

import numpy.testing as npt
import pytest


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_parse_ts_data(tmpdir):
    """Test time series data file parsing."""

    def to_str(X):
        return StringIO("\n".join([",".join(row) for row in X.astype(str).tolist()]))

    values = np.random.random((10, 3))

    t, m, e = data_management.parse_ts_data(to_str(values))
    npt.assert_allclose(t, values[:, 0])
    npt.assert_allclose(m, values[:, 1])
    npt.assert_allclose(e, values[:, 2])

    t, m, e = data_management.parse_ts_data(to_str(values[:, :2]))
    npt.assert_allclose(t, values[:, 0])
    npt.assert_allclose(m, values[:, 1])
    npt.assert_allclose(e[1:], e[:-1])  # constant

    t, m, e = data_management.parse_ts_data(to_str(values[:, :1]))
    npt.assert_allclose(np.diff(t), 1.0 / (len(values) - 1))
    npt.assert_allclose(m, values[:, 0])
    npt.assert_allclose(e[1:], e[:-1])  # constant

    with pytest.raises(ValueError):
        data_management.parse_ts_data(to_str(values[:, []]))


def test_parse_headerfile():
    """Test header file parsing."""
    headerfile_path = pjoin(DATA_PATH, "asas_training_subset_classes_with_metadata.dat")

    labels, metadata = data_management.parse_headerfile(headerfile_path)
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(labels.loc["217801"], "Mira")
    npt.assert_almost_equal(metadata.loc["224635"].meta1, 0.330610932539)

    with pytest.raises(ValueError):
        labels, metadata = data_management.parse_headerfile(
            StringIO("test\n1,2\n3,4,5")
        )

    labels, metadata = data_management.parse_headerfile(
        headerfile_path, files_to_include=["217801"]
    )
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(labels.loc["217801"], "Mira")

    with pytest.raises(ValueError):
        labels, metadata = data_management.parse_headerfile(
            headerfile_path, files_to_include=["111111111"]
        )

    labels, metadata = data_management.parse_headerfile(
        headerfile_path, files_to_include=["217801"]
    )
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(labels.loc["217801"], "Mira")


def test_parsing_and_saving(tmpdir):
    data_file_path = pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz")
    header_path = pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat")
    time_series = data_management.parse_and_store_ts_data(
        data_file_path,
        str(tmpdir),
        header_path,
        cleanup_archive=False,
        cleanup_header=False,
    )
    for ts in time_series:
        assert isinstance(ts, str)
        assert os.path.exists(ts)

    time_series = data_management.parse_and_store_ts_data(
        data_file_path, str(tmpdir), None, cleanup_archive=False, cleanup_header=False
    )
    for ts in time_series:
        assert isinstance(ts, str)
        assert os.path.exists(ts)
