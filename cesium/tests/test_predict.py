from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
import tempfile
import joblib
import numpy as np
import sklearn.base
import xarray as xr

from cesium import predict
from cesium import build_model
from cesium import util
from cesium.celery_tasks import prediction_task, predict_prefeaturized_task


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
TS_CLASS_PATHS = [pjoin(DATA_PATH, f) for f in
                  ["dotastro_215153_with_class.nc",
                   "dotastro_215176_with_class.nc"]]
TS_TARGET_PATHS = [pjoin(DATA_PATH, f) for f in
                   ["dotastro_215153_with_target.nc",
                    "dotastro_215176_with_target.nc"]]


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


def test_model_predictions():
    """Test inner model prediction function"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_featureset.nc"))
    model = build_model.build_model_from_featureset(
        fset, model_type='RandomForestClassifier')
    preds = predict.model_predictions(fset, model)
    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.shape == (len(fset.name),
                                             len(np.unique(fset.target))))
    assert(preds.prediction.values.dtype == np.dtype('float'))


@with_setup(teardown=remove_output)
def test_predict_classification():
    """Test main predict function on multiple files (classification)"""
    classifier_types = [model_type for model_type, model_class
                        in build_model.MODELS_TYPE_DICT.items()
                        if issubclass(model_class,
                                      sklearn.base.ClassifierMixin)]
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_featureset.nc"))
    for model_type in classifier_types:
        model = build_model.build_model_from_featureset(fset,
                                                        model_type=model_type)
        model_path = pjoin(TEMP_DIR, "test.pkl")
        joblib.dump(model, model_path, compress=3)
        preds = prediction_task(TS_CLASS_PATHS, list(fset.data_vars),
                                model_path,
                                custom_features_script=None)().get()
        if preds.prediction.values.ravel()[0].dtype == np.dtype('float'):
            assert(all(preds.prediction.class_label == [b'class1', b'class2',
                                                        b'class3']))
            assert(preds.prediction.values.shape ==
                   (len(TS_CLASS_PATHS), len(np.unique(fset.target))))
        else:
            assert(all(p in [b'class1', b'class2', b'class3'] for p in
                       preds.prediction))


@with_setup(teardown=remove_output)
def test_predict_regression():
    """Test main predict function on multiple files (regression)"""
    regressor_types = [model_type for model_type, model_class
                       in build_model.MODELS_TYPE_DICT.items()
                       if issubclass(model_class, sklearn.base.RegressorMixin)]
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_reg_featureset.nc"))
    for model_type in regressor_types:
        model = build_model.build_model_from_featureset(fset,
                                                        model_type=model_type)
        model_path = pjoin(TEMP_DIR, "test.pkl")
        joblib.dump(model, model_path, compress=3)
        preds = prediction_task(TS_TARGET_PATHS, list(fset.data_vars),
                                model_path,
                                custom_features_script=None)().get()
        assert(preds.prediction.values.shape == (len(TS_CLASS_PATHS),))
        assert(p.dtype == np.dtype('float') for p in preds.prediction)


@with_setup(teardown=remove_output)
def test_predict_optimized_model():
    """Test main predict function (classification) w/ optimized model"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "asas_training_subset_featureset.nc"))
    model = build_model.build_model_from_featureset(fset,
                model_type="RandomForestClassifier",
                params_to_optimize={"n_estimators": [10, 50, 100]}, cv=2)
    model_path = pjoin(TEMP_DIR, "test.pkl")
    joblib.dump(model, model_path, compress=3)
    preds = prediction_task(TS_TARGET_PATHS, list(fset.data_vars), model_path,
                            custom_features_script=None)().get()
    assert(all(preds.prediction.class_label == ['Classical_Cepheid', 'Mira',
                                                'W_Ursae_Maj']))
    assert(preds.prediction.values.shape == (len(TS_CLASS_PATHS),
                                             len(np.unique(fset.target))))


@with_setup(teardown=remove_output)
def test_predict_prefeaturized():
    featureset_path = pjoin(DATA_PATH, "test_featureset.nc")
    fset = xr.open_dataset(featureset_path).load()
    model = build_model.build_model_from_featureset(
        fset, model_type='RandomForestClassifier')
    model_path = pjoin(TEMP_DIR, "test.pkl")
    joblib.dump(model, model_path, compress=3)
    preds = predict_prefeaturized_task(featureset_path, model_path)()

    assert(all(preds.name == fset.name))
    assert(preds.prediction.values.shape == (len(fset.name),
                                             len(np.unique(fset.target))))
    assert(preds.prediction.values.dtype == np.dtype('float'))
