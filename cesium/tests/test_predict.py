import os
from os.path import join as pjoin
import shutil
import numpy as np
import sklearn.base
import xarray as xr

from cesium import predict
from cesium import build_model
from cesium import util
from cesium.tests.fixtures import sample_featureset


def test_model_classification():
    """Test model prediction function: classification"""
    fset = sample_featureset(10, 1, ['amplitude'], ['class1', 'class2'])
    model = build_model.build_model_from_featureset(
        fset, model_type='RandomForestClassifier')
    preds = predict.model_predictions(fset, model)
    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.shape == (len(fset.name),
                                             len(np.unique(fset.target))))
    assert(preds.prediction.values.dtype == np.dtype('float'))

    classes = predict.model_predictions(fset, model, return_probs=False)
    assert(all(classes.name == fset.name))
    assert(classes.prediction.values.shape == (len(fset.name),))
    assert(isinstance(classes.prediction.values[0], (str, bytes)))


def test_model_regression():
    """Test model prediction function: regression"""
    fset = sample_featureset(10, 1, ['amplitude'], [0.1, 0.5])
    model = build_model.build_model_from_featureset(fset,
                                                    model_type='RandomForestRegressor')
    preds = predict.model_predictions(fset, model)
    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.dtype == np.dtype('float'))


def test_predict_optimized_model():
    """Test main predict function (classification) w/ optimized model"""
    fset = sample_featureset(10, 1, ['amplitude'], ['class1', 'class2'])
    model = build_model.build_model_from_featureset(fset,
        model_type='RandomForestClassifier',
        params_to_optimize={"n_estimators": [10, 50, 100]}, cv=2)
    preds = predict.model_predictions(fset, model)
    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.shape == (len(fset.name),
                                             len(np.unique(fset.target))))
    assert(preds.prediction.values.dtype == np.dtype('float'))
