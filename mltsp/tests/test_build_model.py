from mltsp import build_model
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
from sklearn.externals import joblib
import shutil

def test_csv_parser():
    """Test CSV file parsing."""
    colnames, data_rows = build_model.read_data_from_csv_file(
        os.path.join(os.path.dirname(__file__), "Data/csv_test_data.csv"))
    npt.assert_equal(colnames[0], "col1")
    npt.assert_equal(colnames[-1], "col4")
    npt.assert_equal(len(data_rows[0]), 4)
    npt.assert_equal(len(data_rows[-1]), 4)
    npt.assert_equal(data_rows[0][-1], "4")


def test_count_classes():
    """Test counting of class instances"""
    class_list = ["c5", "c1", "c1", "c2", "c2", "c2", "c3"]
    class_count, sorted_class_list = build_model.count_classes(class_list)
    npt.assert_array_equal(sorted_class_list, ["c1", "c2", "c3", "c5"])
    npt.assert_equal(class_count["c1"], 2)
    npt.assert_equal(class_count["c2"], 3)
    npt.assert_equal(class_count["c5"], 1)


def test_clean_up_data_dict():
    """Test removal of empty lines from data"""
    data_dict = {"features": [[1, 2, 3], [1, 2, 3], [1]],
                 "classes": ['1', '2', '3']}
    build_model.clean_up_data_dict(data_dict)
    npt.assert_array_equal(data_dict["classes"], ['1', '2'])
    npt.assert_array_equal(data_dict["features"], [[1, 2, 3], [1, 2, 3]])


def test_create_and_pickle_model():
    """Test creation and storage of model"""
    data_dict = {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
                 "classes": ['1', '2']}
    featset_key = "test"
    model_type = "RF"
    build_model.create_and_pickle_model(
        {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
         "classes": ['1', '2']},
        "test_build_model", "RF", False)
    assert os.path.exists(os.path.join(cfg.MODELS_FOLDER,
                                       "test_build_model_RF.pkl"))
    model = joblib.load(os.path.join(cfg.MODELS_FOLDER,
                                     "test_build_model_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(os.path.join(cfg.MODELS_FOLDER, "test_build_model_RF.pkl"))
    assert not os.path.exists(os.path.join(cfg.MODELS_FOLDER,
                                           "test_build_model_RF.pkl"))


def test_read_features_data_from_disk():
    for suffix in ["features.csv", "classes.pkl"]:
        shutil.copy(
            os.path.join(os.path.join(os.path.dirname(__file__), "Data"),
                         "test_%s" % suffix),
            os.path.join(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    data_dict = build_model.read_features_data_from_disk("TEST001")
    npt.assert_array_equal(data_dict["classes"], ["Mira", "Herbig_AEBE",
                                                  "Beta_Lyrae"])
    for fname in ["TEST001_features.csv", "TEST001_classes.pkl"]:
        os.remove(os.path.join(cfg.FEATURES_FOLDER, fname))

def test_build_model():
    """Test main model building method"""
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "Data"),
                             "test_classes.pkl"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.pkl"))
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "Data"),
                             "test_features.csv"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(os.path.join(cfg.MODELS_FOLDER,
                                       "TEMP_TEST01_RF.pkl"))
    model = joblib.load(os.path.join(cfg.MODELS_FOLDER,
                                     "TEMP_TEST01_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(os.path.join(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.pkl"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
