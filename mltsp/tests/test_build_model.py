from mltsp import build_model
from mltsp import celery_task_tools as ctt
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
from sklearn.externals import joblib
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_csv_parser():
    """Test CSV file parsing."""
    colnames, data_rows = ctt.read_data_from_csv_file(
        pjoin(DATA_PATH, "csv_test_data.csv"))
    npt.assert_equal(colnames[0], "col1")
    npt.assert_equal(colnames[-1], "col4")
    npt.assert_equal(len(data_rows[0]), 4)
    npt.assert_equal(len(data_rows[-1]), 4)
    npt.assert_equal(data_rows[0][-1], "4")


def test_clean_up_data_dict():
    """Test removal of empty lines from data"""
    data_dict = {"features": [[1, 2, 3], [1, 2, 3], [1]],
                 "classes": ['1', '2', '3']}
    ctt.clean_up_data_dict(data_dict)
    npt.assert_array_equal(data_dict["classes"], ['1', '2'])
    npt.assert_array_equal(data_dict["features"], [[1, 2, 3], [1, 2, 3]])


def test_create_and_pickle_model():
    """Test creation and storage of model"""
    data_dict = {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
                 "classes": ['1', '2']}
    featset_key = "test"
    model_type = "RF"
    ctt.create_and_pickle_model(
        {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
         "classes": ['1', '2']},
        "test_build_model", "RF", False)
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "test_build_model_RF.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "test_build_model_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(pjoin(cfg.MODELS_FOLDER, "test_build_model_RF.pkl"))
    assert not os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                    "test_build_model_RF.pkl"))


def test_read_features_data_from_disk():
    """Test read features data from disk"""
    for suffix in ["features.csv", "classes.npy"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    data_dict = ctt.read_features_data_from_disk("TEST001")
    npt.assert_array_equal(data_dict["classes"], ["Mira", "Herbig_AEBE",
                                                  "Beta_Lyrae"])
    for fname in ["TEST001_features.csv", "TEST001_classes.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


def test_build_model():
    """Test main model building method"""
    shutil.copy(pjoin(DATA_PATH, "test_classes.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01_RF.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
