from sklearn.grid_search import GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
import xarray as xr

from cesium import build_model
from cesium.tests.fixtures import sample_featureset


MODEL_TYPES = ['RandomForestClassifier', 'RandomForestRegressor',
               'LinearSGDClassifier', 'LinearRegressor', 'RidgeClassifierCV',
               'BayesianARDRegressor', 'BayesianRidgeRegressor']


def test_fit_existing_model():
    """Test model building helper function."""
    fset = sample_featureset(10, ['amplitude'], ['class1', 'class2'])
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.build_model_from_featureset(fset, model)
    assert isinstance(model, RandomForestClassifier)


def test_fit_existing_model_optimize():
    """Test model building helper function - with param. optimization"""
    fset = sample_featureset(10, ['amplitude', 'maximum', 'minimum', 'median'],
                             ['class1', 'class2'])
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model_options = {"criterion": "gini", "bootstrap": True}
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


def test_fit_optimize():
    """Test hypeparameter optimization"""
    fset = sample_featureset(10, ['amplitude', 'maximum', 'minimum', 'median'],
                             ['class1', 'class2'])
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
