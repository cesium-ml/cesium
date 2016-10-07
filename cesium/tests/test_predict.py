from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
import tempfile
import numpy as np
import sklearn.base
import xarray as xr

from cesium import predict
from cesium import build_model
from cesium import util
from cesium.tests.fixtures import sample_featureset


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
    """Test model prediction function: classification"""
    fset = sample_featureset(10, 1, ['amplitude'], ['class1', 'class2'])
    fset.target.values = np.random.random(len(fset.target.values))
    model = build_model.build_model_from_featureset(fset,
                                                    model_type='RandomForestRegressor')
    preds = predict.model_predictions(fset, model)
    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.dtype == np.dtype('float'))


@with_setup(teardown=remove_output)
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
