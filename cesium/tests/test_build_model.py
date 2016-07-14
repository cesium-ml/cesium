from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
import tempfile
from sklearn.externals import joblib
from sklearn.grid_search import GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
import xarray as xr

from cesium import build_model
from cesium.celery_tasks import build_model_task


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
MODEL_TYPES = ['RandomForestClassifier', 'RandomForestRegressor',
               'LinearSGDClassifier', 'LinearRegressor', 'RidgeClassifierCV',
               'BayesianARDRegressor', 'BayesianRidgeRegressor']


def setup(module):
    module.TEMP_DIR = tempfile.mkdtemp()


def teardown(module):
    shutil.rmtree(module.TEMP_DIR)


def remove_output():
    fnames = ["test.pkl"]
    for fname in fnames:
        try:
            os.remove(pjoin(TEMP_DIR, fname))
        except OSError:
            pass


@with_setup(teardown=remove_output)
def test_build_model_task():
    """Test main model building method - various types"""
    for model_type in MODEL_TYPES:
        if 'Classifier' in model_type:
            fset_path = pjoin(DATA_PATH, "test_featureset.nc")
        elif 'Regressor' in model_type:
            fset_path = pjoin(DATA_PATH, "test_reg_featureset.nc")
        else:
            raise ValueError("Unrecognized scikit-learn model type.")
        output_path = pjoin(TEMP_DIR, "test.pkl")
        model = build_model_task.delay(model_type, {}, fset_path,
                                       output_path).get()
        assert isinstance(model, build_model.MODELS_TYPE_DICT[model_type])


@with_setup(teardown=remove_output)
def test_fit_existing_model():
    """Test model building helper function."""
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_featureset.nc"))
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.build_model_from_featureset(fset, model)
    assert isinstance(model, RandomForestClassifier)


@with_setup(teardown=remove_output)
def test_fit_existing_model_optimize():
    """Test model building helper function - with param. optimization"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "asas_training_subset_featureset.nc"))
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model_options = {"criterion": "gini",
                     "bootstrap": True}
    params_to_optimize = {"n_estimators": [10, 50, 100],
                          "min_samples_split": [2, 5],
                          "max_features": ["auto", 3]}
    model = build_model.build_model_from_featureset(fset, model, None,
                                                    model_options,
                                                    params_to_optimize)
    assert hasattr(model, "best_params_")
    assert hasattr(model, "predict_proba")
    assert isinstance(model, GridSearchCV)
    assert isinstance(model.best_estimator_, RandomForestClassifier)


@with_setup(teardown=remove_output)
def test_fit_optimize():
    """Test hypeparameter optimization"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "asas_training_subset_featureset.nc"))
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model_options = {"criterion": "gini", "bootstrap": True}
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']\
            (**model_options)
    feature_df = build_model.rectangularize_featureset(fset)
    params_to_optimize = {"n_estimators": [10, 50, 100],
                          "min_samples_split": [2, 5],
                          "max_features": ["auto", 3]}
    model = build_model.fit_model_optimize_hyperparams(feature_df,
                                                       fset['target'], model,
                                                       params_to_optimize)
    assert hasattr(model, "best_params_")
    assert hasattr(model, "predict_proba")
    assert isinstance(model, GridSearchCV)
    assert isinstance(model.best_estimator_, RandomForestClassifier)
