from mltsp import predict
from mltsp.cfg import config
from mltsp import build_model
from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
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
CUSTOM_SCRIPT = pjoin(DATA_PATH, "testfeature1.py")


def copy_test_data():
    fnames = ["test_featureset.nc", "test_reg_featureset.nc",
              "test_10_featureset.nc"]
    for fname in fnames:
        shutil.copy(pjoin(DATA_PATH, fname),
                    config['paths']['features_folder'])
    

def remove_test_data():
    fnames = ["test_featureset.nc", "test_reg_featureset.nc",
              "test_10_featureset.nc"]
    for fname in fnames:
        try:
            os.remove(pjoin(config['paths']['features_folder'], fname))
        except OSError:
            pass


@with_setup(copy_test_data, remove_test_data)
def test_model_predictions():
    """Test inner model prediction function"""
    featureset = xr.open_dataset(pjoin(config['paths']['features_folder'],
                                 "test_featureset.nc"))
    model = build_model.build_model_from_featureset(
        featureset, model_type='RandomForestClassifier')
    preds = predict.model_predictions(featureset, model)
    assert(preds.shape[0] == len(featureset.name))
    assert(preds.shape[1] == len(np.unique(featureset.target.values)))
    assert(preds.values.dtype == np.dtype('float'))


@with_setup(copy_test_data, remove_test_data)
def test_predict_classification():
    """Test main predict function on multiple files (classification)"""
    classifier_types = [model_type for model_type, model_class
                        in build_model.MODELS_TYPE_DICT.items()
                        if issubclass(model_class, sklearn.base.ClassifierMixin)]
    for model_type in classifier_types:
        build_model.create_and_pickle_model('test', model_type, 'test')
        pred_results_dict = predict.predict_data_files(TS_CLASS_PATHS, 'test',
                                                       'test')
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(el[0] in [b'class1', b'class2', b'class3']
                       or el in [b'class1', b'class2', b'class3'])


@with_setup(copy_test_data, remove_test_data)
def test_predict_regression():
    """Test main predict function on multiple files (regression)"""
    regressor_types = [model_type for model_type, model_class
                       in build_model.MODELS_TYPE_DICT.items()
                       if issubclass(model_class, sklearn.base.RegressorMixin)]
    for model_type in regressor_types:
        build_model.create_and_pickle_model('test', model_type, 'test_reg')
        pred_results_dict = predict.predict_data_files(TS_TARGET_PATHS, 'test',
                                                      'test')
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(isinstance(el, float))


@with_setup(copy_test_data, remove_test_data)
def test_predict_optimized_model():
    """Test main predict function (classification) w/ optimized model"""
    build_model.create_and_pickle_model('test_10', "RandomForestClassifier",
                                        'test_10',
                                        {},
                                        {"n_estimators": [10, 50, 100]})
    pred_results_dict = predict.predict_data_files(TS_CLASS_PATHS, 'test_10',
                                                   'test_10')
    for fname, results in pred_results_dict.items():
        for el in results['pred_results']:
            assert(el[0] in [b'Mira', b'W_Ursae_Maj', b'Delta_Scuti',
                             b'Beta_Lyrae', b'Herbig_AEBE', b'Classical_Cepheid']
                   or el in [b'Mira', b'W_Ursae_Maj', b'Delta_Scuti',
                             b'Beta_Lyrae', b'Herbig_AEBE', b'Classical_Cepheid'])
