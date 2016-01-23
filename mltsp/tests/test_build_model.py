from mltsp import build_model
from mltsp import cfg
from nose.tools import with_setup
import os
from os.path import join as pjoin
from sklearn.externals import joblib
from sklearn.grid_search import GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
import shutil
import xarray as xr


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def copy_classification_test_data():
    fnames = ["test_featureset.nc", "test_10_featureset.nc"]
    for fname in fnames:
        shutil.copy(pjoin(DATA_PATH, fname), cfg.FEATURES_FOLDER)


def copy_regression_test_data():
    fnames = ["test_reg_featureset.nc"]
    for fname in fnames:
        shutil.copy(pjoin(DATA_PATH, fname), cfg.FEATURES_FOLDER)


def remove_test_data():
    fnames = ["test_featureset.nc", "test_10_featureset.nc",
              "test_reg_featureset.nc", "test.pkl"]
    for fname in fnames:
        for data_dir in [cfg.FEATURES_FOLDER, cfg.MODELS_FOLDER]:
            try:
                os.remove(pjoin(data_dir, fname))
            except OSError:
                pass


@with_setup(copy_classification_test_data, remove_test_data)
def test_build_model_rfc():
    """Test main model building method - RandomForestClassifier"""
    build_model.create_and_pickle_model("test", "RandomForestClassifier",
                                        "test")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict_proba")
    assert isinstance(model, RandomForestClassifier)


@with_setup(copy_regression_test_data, remove_test_data)
def test_build_model_rfr():
    """Test main model building method - RandomForestRegressor"""
    build_model.create_and_pickle_model("test", "RandomForestRegressor",
                                        "test_reg")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, RandomForestRegressor)


@with_setup(copy_classification_test_data, remove_test_data)
def test_build_model_lin_class():
    """Test main model building method - linear classifier"""
    build_model.create_and_pickle_model("test", "LinearSGDClassifier", "test")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, SGDClassifier)


@with_setup(copy_regression_test_data, remove_test_data)
def test_build_model_lin_reg():
    """Test main model building method - linear regressor"""
    build_model.create_and_pickle_model("test", "LinearRegressor", "test_reg")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, LinearRegression)


@with_setup(copy_classification_test_data, remove_test_data)
def test_build_model_ridge_cv():
    """Test main model building method - Ridge Classifer CV"""
    build_model.create_and_pickle_model("test", "RidgeClassifierCV", "test")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, RidgeClassifierCV)


@with_setup(copy_regression_test_data, remove_test_data)
def test_build_model_ard_reg():
    """Test main model building method - ARD Regression"""
    build_model.create_and_pickle_model("test", "BayesianARDRegressor",
                                        "test_reg")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, ARDRegression)


@with_setup(copy_regression_test_data, remove_test_data)
def test_build_model_ard_reg():
    """Test main model building method - Bayesian Ridge Regression"""
    build_model.create_and_pickle_model("test", "BayesianRidgeRegressor",
                                        "test_reg")
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test.pkl"))
    assert hasattr(model, "predict")
    assert isinstance(model, BayesianRidge)


@with_setup(copy_classification_test_data, remove_test_data)
def test_fit_existing_model():
    """Test model building helper function."""
    featureset = xr.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         "test_featureset.nc"))
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.build_model_from_featureset(featureset, model)
    assert hasattr(model, "n_features_")
    assert hasattr(model, "predict_proba")
    assert isinstance(model, RandomForestClassifier)


@with_setup(copy_classification_test_data, remove_test_data)
def test_fit_existing_model_optimize():
    """Test model building helper function - with param. optimization"""
    featureset = xray.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         "test_10_featureset.nc"))
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model_options = {"criterion": "gini",
                     "bootstrap": True}
    params_to_optimize = {"n_estimators": [10, 50, 100],
                          "min_samples_split": [2, 5],
                          "max_features": ["auto", 3]}
    model = build_model.build_model_from_featureset(
        featureset, model=model, model_options=model_options,
        params_to_optimize=params_to_optimize)
    assert hasattr(model, "best_params_")
    assert hasattr(model, "predict_proba")
    assert isinstance(model, GridSearchCV)
    assert isinstance(model.best_estimator_, RandomForestClassifier)


@with_setup(copy_classification_test_data, remove_test_data)
def test_fit_optimize():
    """Test hypeparameter optimization"""
    featureset = xray.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         "test_10_featureset.nc"))
    model_options = {"criterion": "gini",
                     "bootstrap": True}
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']\
            (**model_options)
    feature_df = build_model.rectangularize_featureset(featureset)
    params_to_optimize = {"n_estimators": [10, 50, 100],
                          "min_samples_split": [2, 5],
                          "max_features": ["auto", 3]}
    model = build_model.fit_model_optimize_hyperparams(
        feature_df, featureset['target'], model, params_to_optimize)
    assert hasattr(model, "best_params_")
    assert hasattr(model, "predict_proba")
    assert isinstance(model, GridSearchCV)
    assert isinstance(model.best_estimator_, RandomForestClassifier)


@with_setup(copy_classification_test_data, remove_test_data)
def test_build_model_lin_class_optimize():
    """Test main model building method - linear classifier - w/ optimization"""
    model_options = {"learning_rate": "optimal"}
    params_to_optimize = {"alpha": [0.1, 0.001, 0.0001, 0.0000001],
                          "epsilon": [0.001, 0.01, 0.1, 0.5]}
    build_model.create_and_pickle_model("test_10", "LinearSGDClassifier",
                                        "test_10", model_options,
                                        params_to_optimize)
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "test_10.pkl"))
    assert hasattr(model, "best_params_")
    assert hasattr(model, "predict")
    assert isinstance(model, GridSearchCV)
    assert isinstance(model.best_estimator_, SGDClassifier)
