from mltsp import build_model
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
from sklearn.externals import joblib
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_build_model_rfc():
    """Test main model building method - RFC"""
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.create_and_pickle_model("TEMP_TEST01", "RFC", "TEMP_TEST01")
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
    build_model.create_and_pickle_model("TEMP_TEST01", "RFR", "TEMP_TEST01")
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
    build_model.create_and_pickle_model("TEMP_TEST01", "LC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "SGDClassifier" in str(type(model))


def test_build_model_lin_reg():
    """Test main model building method - linear regressor"""
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.create_and_pickle_model("TEMP_TEST01", "LR", "TEMP_TEST01")
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
    build_model.create_and_pickle_model("TEMP_TEST01", "RC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "RidgeClassifierCV" in str(type(model))


def test_build_model_ard_reg():
    """Test main model building method - ARD Regression"""
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.create_and_pickle_model("TEMP_TEST01", "ARDR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER,
                              "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    assert hasattr(model, "predict")
    assert "ARDRegression" in str(type(model))
