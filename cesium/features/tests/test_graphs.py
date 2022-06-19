import os
import numpy as np
import numpy.testing as npt

from cesium import data_management
from cesium.features import graphs
from cesium.features.tests.util import generate_features


# Fixed set of features w/ known values
SCIENCE_FEATS = graphs.GENERAL_FEATS + graphs.LOMB_SCARGLE_FEATS


def test_feature_generation():
    """Compare generated features to reference values."""
    this_dir = os.path.join(os.path.dirname(__file__))
    test_files = [
        os.path.join(this_dir, "data/257141.dat"),
        os.path.join(this_dir, "data/245486.dat"),
        os.path.join(this_dir, "data/247327.dat"),
    ]
    features_extracted = None
    values_computed = None
    for i, ts_data_file_path in enumerate(test_files):
        t, m, e = data_management.parse_ts_data(ts_data_file_path)
        features = generate_features(t, m, e, SCIENCE_FEATS)
        sorted_features = sorted(features.items())
        if features_extracted is None:
            features_extracted = [f[0] for f in sorted_features]
            values_computed = np.zeros((len(test_files), len(features_extracted)))
        values_computed[i, :] = [f[1] for f in sorted_features]

    def features_from_csv(filename):
        with open(filename) as f:
            feature_names = f.readline().strip().split(",")
            feature_values = np.loadtxt(f, delimiter=",")

        return feature_names, feature_values

    this_dir = os.path.join(os.path.dirname(__file__))
    features_expected, values_expected = features_from_csv(
        os.path.join(this_dir, "data/expected_features.csv")
    )

    npt.assert_equal(features_extracted, features_expected)
    npt.assert_array_almost_equal(values_computed, values_expected)
