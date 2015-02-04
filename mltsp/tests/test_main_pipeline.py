from mltsp import build_model
from mltsp import featurize
from mltsp import predict_class
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


def test_featurize():
    """Test main featurize function."""
    results_msg = featurize.featurize(
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
    results_msg = build_model.build_model(featureset_name="test",
                                          featureset_key="test")
    assert(os.path.exists(os.path.join(cfg.MODELS_FOLDER, "test_RF.pkl")))


def test_predict():
    """Test class prediction."""
    results_dict = predict_class.predict(
        os.path.join(os.path.dirname(__file__), "Data/dotastro_215153.dat"),
        "test", "RF", "test",
        custom_features_script=os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                              "testfeature1.py"),
        metadata_file_path=os.path.join(os.path.dirname(__file__),
                                        "Data/215153_metadata.dat"))
    assert(isinstance(results_dict, dict))
    assert("dotastro_215153.dat" in results_dict)
    assert(isinstance(
        results_dict["dotastro_215153.dat"]["features_dict"]["std_err"], float))


def remove_created_files():
    """Remove files created by test suite."""

    for fname in [os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"),
                  os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"),
                  os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                               "testfeature1.py"),
                  os.path.join(cfg.MODELS_FOLDER, "test_RF.pkl")]:
        os.remove(fname)
