import os
from os.path import join as pjoin
from nose.tools import with_setup
import numpy as np
import numpy.testing as npt
from cesium import time_series as tslib
from cesium import transformation

DATA_PATH = pjoin(os.path.dirname(__file__), "data")
TS_PATHS = [pjoin(DATA_PATH, f) for f in
            ["dotastro_215153_with_class.nc",
             "dotastro_215176_with_class.nc"]]


def test_train_test_split():
    # Mock out unevenly-labeled test data: 4 class1, 8 class2
    n_class1 = 4
    n_class2 = 8
    TS_MOCK_PATHS = [TS_PATHS[0]] * n_class1 + [TS_PATHS[1]] * n_class2
    transform_type = "Train/Test Split"
    time_series = [tslib.from_netcdf(path) for path in TS_MOCK_PATHS]
    np.random.seed(0)
    train, test = transformation.transform_ts_files(time_series,
                                                    transform_type)
    npt.assert_equal(sum(ts.target == 'class1' for ts in train), 1 * n_class1 / 2)
    npt.assert_equal(sum(ts.target == 'class1' for ts in test), n_class1 / 2)
    npt.assert_equal(sum(ts.target == 'class2' for ts in train), 1 * n_class2 / 2)
    npt.assert_equal(sum(ts.target == 'class2' for ts in test), n_class2 / 2)
