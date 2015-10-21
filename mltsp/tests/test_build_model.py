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
                 "targets": ['1', '2', '3']}
    ctt.clean_up_data_dict(data_dict)
    npt.assert_array_equal(data_dict["targets"], ['1', '2'])
    npt.assert_array_equal(data_dict["features"], [[1, 2, 3], [1, 2, 3]])


def test_create_and_pickle_model():
    """Test creation and storage of model"""
    data_dict = {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
                 "targets": ['1', '2']}
    ctt.create_and_pickle_model(
        {"features": [[1.1, 2.2, 3.1], [1.2, 2.1, 3.2]],
         "targets": ['1', '2']},
        "NEW_MODEL_KEY", "RFC", {})
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "NEW_MODEL_KEY.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "NEW_MODEL_KEY.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(pjoin(cfg.MODELS_FOLDER, "NEW_MODEL_KEY.pkl"))
    assert not os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                    "NEW_MODEL_KEY.pkl"))


def test_read_features_data_from_disk():
    """Test read features data from disk"""
    for suffix in ["features.csv", "targets.npy"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    data_dict = ctt.read_features_data_from_disk("TEST001")
    npt.assert_array_equal(data_dict["targets"], ['Mira', 'Herbig_AEBE',
                                                  'Beta_Lyrae', 'Mira',
                                                  'RR_Lyrae', 'Mira'])
    for fname in ["TEST001_features.csv", "TEST001_targets.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


def test_build_model_rfc():
    """Test main model building method - RFC"""
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict_proba")
    assert "sklearn.ensemble.forest.RandomForestClassifier" in str(type(model))


def test_build_model_rfr():
    """Test main model building method - RFR"""
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "sklearn.ensemble.forest.RandomForestRegressor" in str(type(model))


def test_build_model_lin_class():
    """Test main model building method - linear classifier"""
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")


def test_build_model_lin_reg():
    """Test main model building method - linear regressor"""
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "LinearRegression" in str(type(model))


def test_build_model_ridge_cv():
    """Test main model building method - Ridge Classifer CV"""
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")


def test_build_model_ard_reg():
    """Test main model building method - ARD Regression"""
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "ARDR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "ARDRegression" in str(type(model))
