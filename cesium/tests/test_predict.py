from cesium import predict
from cesium import build_model
from cesium import util
from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
import tempfile
import numpy as np
import xarray as xr
import sklearn.base


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
TS_CLASS_PATHS = [pjoin(DATA_PATH, f) for f in
                  ["dotastro_215153_with_class.nc",
                   "dotastro_215176_with_class.nc"]]
TS_TARGET_PATHS = [pjoin(DATA_PATH, f) for f in
                   ["dotastro_215153_with_target.nc",
                    "dotastro_215176_with_target.nc"]]


def test_model_predictions():
    """Test inner model prediction function"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_featureset.nc"))
    model = build_model.build_model_from_featureset(
        fset, model_type='RandomForestClassifier')
    preds = predict.model_predictions(fset, model)
    assert(preds.shape[0] == len(fset.name))
    assert(preds.shape[1] == len(np.unique(fset.target.values)))
    assert(preds.values.dtype == np.dtype('float'))


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
        pred_results_dict = predict.predict_data_files(TS_CLASS_PATHS,
                                                       list(fset.data_vars),
                                                       model,
                                                       custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(el[0] in [b'class1', b'class2', b'class3']
                       or el in [b'class1', b'class2', b'class3'])


def test_predict_regression():
    """Test main predict function on multiple files (regression)"""
    regressor_types = [model_type for model_type, model_class
                       in build_model.MODELS_TYPE_DICT.items()
                       if issubclass(model_class, sklearn.base.RegressorMixin)]
    fset = xr.open_dataset(pjoin(DATA_PATH, "test_reg_featureset.nc"))
    for model_type in regressor_types:
        model = build_model.build_model_from_featureset(fset,
                                                        model_type=model_type)
        pred_results_dict = predict.predict_data_files(TS_TARGET_PATHS,
                                                       list(fset.data_vars),
                                                       model,
                                                       custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(isinstance(el, float))


def test_predict_optimized_model():
    """Test main predict function (classification) w/ optimized model"""
    fset = xr.open_dataset(pjoin(DATA_PATH, "asas_training_subset_featureset.nc"))
    model = build_model.build_model_from_featureset(fset,
                model_type="RandomForestClassifier",
                params_to_optimize={"n_estimators": [10, 50, 100]}, cv=2)
    pred_results_dict = predict.predict_data_files(TS_TARGET_PATHS,
                                                   list(fset.data_vars), model,
                                                   custom_features_script=None)
    for fname, results in pred_results_dict.items():
        for el in results['pred_results']:
            print(el)
            assert(el[0] in ['Mira', 'W_Ursae_Maj', 'Classical_Cepheid']
                   or el in ['Mira', 'W_Ursae_Maj', 'Classical_Cepheid'])
