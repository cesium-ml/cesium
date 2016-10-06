import numpy as np
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
    fset = sample_featureset(10, 1, ['amplitude', 'maximum', 'minimum', 'median'],
                             ['class1', 'class2'])
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.build_model_from_featureset(fset, model)
    assert isinstance(model, RandomForestClassifier)


def test_fit_existing_model_optimize():
    """Test model building helper function - with param. optimization"""
    fset = sample_featureset(10, 1, ['amplitude', 'maximum', 'minimum', 'median'],
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
    fset = sample_featureset(10, 1, ['amplitude', 'maximum', 'minimum', 'median'],
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


def test_fit_multichannel():
    """Test model building helper function for multi-channel feature data."""
    fset = sample_featureset(10, 3, ['amplitude', 'maximum', 'minimum', 'median'],
                             ['class1', 'class2'])
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    model = build_model.build_model_from_featureset(fset, model)
    assert isinstance(model, RandomForestClassifier)


def test_invalid_feature_values():
    """Test proper exception handling for invalid feature values"""
    fset = sample_featureset(10, 1, ['x_valid', 'x_inf', 'x_nan'], ['class1', 'class2'])
    fset.x_inf.values[0, 0] = np.inf
    fset.x_nan.values[0, 0] = np.nan
    model = build_model.MODELS_TYPE_DICT['RandomForestClassifier']()
    try:
        model = build_model.build_model_from_featureset(fset, model)
    except ValueError as e:
        assert 'x_valid' not in str(e)
        assert 'x_inf' in str(e)
        assert 'x_nan' in str(e)
    else:
        raise AssertionError("Exception should have been raised for invalid data.")

    model = build_model.build_model_from_featureset(fset.drop(['x_inf', 'x_nan']), model)
    assert isinstance(model, RandomForestClassifier)
