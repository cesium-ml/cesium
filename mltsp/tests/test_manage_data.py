from nose.tools import with_setup
import numpy.testing as npt
import os
from os.path import join as pjoin
import shutil
import tarfile
import numpy as np
import xarray as xr
from mltsp import cfg
from mltsp import manage_data
from mltsp import util


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
INPUT_TEST_FILES = ["215153_215176_218272_218934_metadata.dat",
                    "215153_215176_218272_218934.tar.gz", "247327.dat"]
EXTRACTED_TEST_FILES = ["dotastro_218934.dat", "dotastro_218272.dat",
                        "dotastro_215176.dat", "dotastro_215153.dat"]


def copy_test_data():
    for fname in INPUT_TEST_FILES:
        shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def remove_test_data():
    ts_data_paths = [pjoin(DATA_PATH, util.shorten_fname(fname) + '.nc')
                     for fname in EXTRACTED_TEST_FILES]
    for fname in INPUT_TEST_FILES + ts_data_paths:
        try:
            os.remove(fname)
        except OSError:
            pass


def sample_time_series(size=51, channels=1):
    times = np.sort(np.random.random(size))
    values = np.array([np.random.normal(size=size) for i in range(channels)])
    errors = np.array([np.random.exponential(size=size)
                       for i in range(channels)])
    if channels == 1:
        values = values[0]
        errors = errors[0]
    return times, values, errors


def test_parse_ts_data():
    """Test time series data file parsing."""
    t, m, e = manage_data.parse_ts_data(pjoin(DATA_PATH, "dotastro_215153.dat"))
    assert t.ndim == 1
    assert len(t) == len(m) and len(m) == len(e)


def test_parse_headerfile():
    """Test header file parsing."""
    targets, metadata = manage_data.parse_headerfile(
        pjoin(DATA_PATH, "sample_classes_with_metadata_headerfile.dat"))
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(targets.loc["237022"], "W_Ursae_Maj")
    npt.assert_almost_equal(metadata.loc["230395"].meta1, 0.270056761691)


def test_assemble_ts_dataset():
    t, m, e = sample_time_series()
    target = 'class1'
    meta_features = {'f1': 1.0}
    fname = 'testf'
    dataset = manage_data.assemble_ts_dataset(t, m, e, target, meta_features,
                                              fname)
    assert(all(t == dataset.time) and all(m == dataset.measurement)
           and all(e == dataset.error))
    assert dataset.target == target
    assert dataset.meta_features.to_series().to_dict() == meta_features
    assert dataset.name == fname


@with_setup(copy_test_data, remove_test_data)
def test_parse_and_store_ts_data():
    data_file_path = pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz")
    header_path = pjoin(cfg.UPLOAD_FOLDER,
                        "215153_215176_218272_218934_metadata.dat")
    datasets, fnames = manage_data.parse_and_store_ts_data(data_file_path,
                                                           header_path,
                                                           cleanup_archive=False)
    for ds, fname in zip(datasets, fnames):
        assert all(ds.feature == ['meta1', 'meta2', 'meta3'])
        assert ds.name + '.nc' == fname
        assert(len(ds.time) == len(ds.measurement)
               and len(ds.time) == len(ds.error))
