from mltsp import build_rf_model as bm
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
from subprocess import call


def setup():
    print("Copying data files")
    # copy data files to proper directory:
    call(["cp",
          os.path.join(os.path.dirname(__file__),
                       "Data/asas_training_subset_classes_with_metadata.dat"),
          os.path.join(cfg.UPLOAD_FOLDER,
                       "asas_training_subset_classes_with_metadata.dat")])

    call(["cp",
          os.path.join(os.path.dirname(__file__),
                       "Data/asas_training_subset.tar.gz"),
          os.path.join(cfg.UPLOAD_FOLDER,
                       "asas_training_subset.tar.gz")])

    call(["cp",
          os.path.join(os.path.dirname(__file__),
                       "Data/testfeature1.py"),
          os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "testfeature1.py")])


def test_csv_parser():
    """Test CSV file parsing."""
    colnames, data_rows = bm.read_data_from_csv_file(
        os.path.join(os.path.dirname(__file__), "Data/csv_test_data.csv"))
    npt.assert_equal(colnames[0], "col1")
    npt.assert_equal(colnames[-1], "col4")
    npt.assert_equal(len(data_rows[0]), 4)
    npt.assert_equal(len(data_rows[-1]), 4)
    npt.assert_equal(data_rows[0][-1], "4")


def test_features_file_parser():
    """Test features file parsing."""
    objects = bm.parse_prefeaturized_csv_data(
        os.path.join(os.path.dirname(__file__), "Data/csv_test_data.csv"))
    npt.assert_array_equal(sorted(list(objects[0].keys())), ["col1", "col2",
                                                             "col3", "col4"])
    npt.assert_equal(objects[1]['col1'], ".1")
    npt.assert_equal(objects[-1]['col4'], "221")


def test_headerfile_parser():
    """Test header file parsing."""
    (features_to_use, fname_class_dict, fname_class_science_features_dict,
     fname_metadata_dict) = bm.parse_headerfile(
         os.path.join(os.path.dirname(__file__),
                      "Data/sample_classes_with_metadata_headerfile.dat"),
         features_to_use=["dummy_featname"])
    npt.assert_array_equal(features_to_use, ["dummy_featname", "meta1", "meta2",
                                             "meta3"])
    npt.assert_equal(fname_class_dict["237022"], "W_Ursae_Maj")
    npt.assert_equal(fname_class_science_features_dict["215153"]["class"],
                     "Mira")
    npt.assert_equal(fname_metadata_dict["230395"]["meta1"], 0.270056761691)


def test_featurize():
    """Test main featurize function."""
    results_msg = bm.featurize(
        headerfile_path=os.path.join(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=os.path.join(cfg.UPLOAD_FOLDER,
                                  "asas_training_subset.tar.gz"),
        features_to_use=["std_err"],# #TEMP# TCP still broken under py3
        featureset_id="test", is_test=True,
        custom_script_path=os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                        "testfeature1.py"),
        USE_DISCO=False)
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv")))
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_classes.pkl")))
    df = pd.io.parsers.read_csv(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv"))
    cols = df.columns
    values = df.values
    assert("std_err" in cols)


def test_build_model():
    """Test model build function."""
    results_msg = bm.build_model(featureset_name="test", featureset_key="test")
    assert(os.path.exists(os.path.join(cfg.MODELS_FOLDER, "test_RF.pkl")))


def test_generate_features():
    """Test generate features function."""


def test_predict():
    """Test prediction."""


def remove_created_files():
    """Remove files created by test suite."""

    for fname in [os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"),
                  os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"),
                  os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                               "testfeature1.py"),
                  os.path.join(cfg.MODELS_FOLDER, "test_RF.pkl")]:
        os.remove(fname)
