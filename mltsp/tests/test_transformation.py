import os
from os.path import join as pjoin
from nose.tools import with_setup
import numpy as np
from mltsp import cfg
from mltsp import transformation

DATA_PATH = pjoin(os.path.dirname(__file__), "data")
TS_PATHS = [pjoin(DATA_PATH, f) for f in
            ["dotastro_215153_with_class.nc",
             "dotastro_215176_with_class.nc"]]
TEST_OUTPUT_PATHS = [pjoin(cfg.TS_DATA_FOLDER, "train_dotastro_215153.nc"),
                     pjoin(cfg.TS_DATA_FOLDER, "test_dotastro_215153.nc"),
                     pjoin(cfg.TS_DATA_FOLDER, "train_dotastro_215176.nc"),
                     pjoin(cfg.TS_DATA_FOLDER, "test_dotastro_215176.nc")]


def remove_test_data():
    for f in TEST_OUTPUT_PATHS:
        try:
            os.remove(f)
        except OSError:
            pass


@with_setup(teardown=remove_test_data)
def test_train_test_split():
    # Mock out unevenly-labeled test data: 4 class1, 8 class2
    n_class1 = 4
    n_class2 = 8
    TS_MOCK_PATHS = [TS_PATHS[0]] * n_class1 + [TS_PATHS[1]] * n_class2
    train, test= transformation.transform_ts_files(TS_MOCK_PATHS, ['train', 'test'],
                                                   transformation.train_test_split)
    assert sum(ts.target == 'class1' for ts in train) == 3 * n_class1 / 4
    assert sum(ts.target == 'class1' for ts in test) == n_class1 / 4
    assert sum(ts.target == 'class2' for ts in train) == 3 * n_class2 / 4
    assert sum(ts.target == 'class2' for ts in test) == n_class2 / 4
