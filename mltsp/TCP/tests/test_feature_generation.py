from mltsp import featurize
from mltsp import cfg

import numpy as np
import numpy.testing as npt

import time
import os
import shutil
import glob


def setup():
    print("Copying data files")
    # copy data files to proper directory:
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/asas_training_subset_classes.dat"),
                cfg.UPLOAD_FOLDER)

    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/asas_training_subset.tar.gz"),
                cfg.UPLOAD_FOLDER)


def test_feature_generation():
    for f in glob.glob(os.path.join(cfg.FEATURES_FOLDER, '/*.csv')):
        os.remove(f)

    tic = time.time()
    this_dir = os.path.join(os.path.dirname(__file__))

    featurize.featurize(
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset_classes.dat"),
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        featureset_id="testfeatset", is_test=True, USE_DISCO=False,
        features_to_use=cfg.features_list_science
    )

    delta = time.time() - tic

    def features_from_csv(filename):
        with open(filename) as f:
            feature_names = f.readline().strip().split(",")
            feature_values = np.loadtxt(f, delimiter=',')

        return feature_names, feature_values

    features_extracted, values_computed = features_from_csv(
        os.path.join(cfg.FEATURES_FOLDER, "testfeatset_features.csv"))

    features_expected, values_expected = features_from_csv(
        os.path.join(this_dir, "data/expected_features.csv"))

    npt.assert_equal(len(features_extracted), 81)
    npt.assert_equal(features_extracted, features_expected)
    npt.assert_array_almost_equal(values_computed, values_expected)

    # Ensure this test takes less than a minute to run
    assert delta < 60


if __name__ == "__main__":
    setup()
    test_feature_generation()
