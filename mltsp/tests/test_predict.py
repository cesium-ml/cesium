from mltsp import predict
from mltsp import cfg
from mltsp import build_model
from nose.tools import with_setup
import os
from os.path import join as pjoin
import shutil
import numpy as np
import xarray as xr
import sklearn.base


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def copy_classification_test_data():
    fnames = ["test_featureset.nc", "test_cust_featureset.nc",
              "dotastro_215153.dat", "215153_metadata.dat",
              "215153_215176_218272_218934_metadata.dat",
              "215153_215176_218272_218934.tar.gz", "testfeature1.py"]
    for fname in fnames:
        if fname.endswith('.nc'):
            shutil.copy(pjoin(DATA_PATH, fname), cfg.FEATURES_FOLDER)
        elif fname.endswith('.py'):
            shutil.copy(pjoin(DATA_PATH, fname),
                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def copy_regression_test_data():
    fnames = ["test_reg_featureset.nc", "dotastro_215153.dat",
              "215153_metadata.dat"]
    for fname in fnames:
        if fname.endswith('.nc'):
            shutil.copy(pjoin(DATA_PATH, fname), cfg.FEATURES_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def remove_test_data():
    fnames = ["test_featureset.nc", "test_reg_featureset.nc",
              "test_cust_featureset.nc", "testfeature1.py",
              "dotastro_215153.dat", "215153_metadata.dat",
              "215153_215176_218272_218934_metadata.dat",
              "215153_215176_218272_218934.tar.gz"]
    for fname in fnames:
        for data_dir in [cfg.FEATURES_FOLDER, cfg.MODELS_FOLDER,
                         cfg.CUSTOM_FEATURE_SCRIPT_FOLDER]:
            try:
                os.remove(pjoin(data_dir, fname))
            except OSError:
                pass


@with_setup(copy_classification_test_data, remove_test_data)
def test_model_predictions():
    """Test inner model prediction function"""
    featureset = xr.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         'test_featureset.nc'))
    model = build_model.build_model_from_featureset(
        featureset, model_type='RandomForestClassifier')
    preds = predict.model_predictions(featureset, model)
    assert(preds.shape[0] == len(featureset.name))
    assert(preds.shape[1] == len(np.unique(featureset.target.values)))
    assert(preds.values.dtype == np.dtype('float'))


@with_setup(copy_classification_test_data, remove_test_data)
def test_single_predict_classification():
    """Test main predict function on single file (classification)"""
    classifier_types = [model_type for model_type, model_class
                        in build_model.MODELS_TYPE_DICT.items()
                        if issubclass(model_class,
                                      sklearn.base.ClassifierMixin)]
    for model_type in classifier_types:
        build_model.create_and_pickle_model('test', model_type, 'test')
        pred_results_dict = predict.predict_data_file(
                                pjoin(cfg.UPLOAD_FOLDER, "dotastro_215153.dat"),
                                'test', model_type, 'test',
                                metadata_path=pjoin(cfg.UPLOAD_FOLDER,
                                "215153_metadata.dat"), custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(el[0] in [b'class1', b'class2', b'class3']
                       or el in [b'class1', b'class2', b'class3'])


@with_setup(copy_classification_test_data, remove_test_data)
def test_single_predict_classification_with_custom():
    """Test predict function w/ custom feat. on single file (classification)"""
    classifier_types = [model_type for model_type, model_class
                        in build_model.MODELS_TYPE_DICT.items()
                        if issubclass(model_class,
                                      sklearn.base.ClassifierMixin)]
    for model_type in classifier_types:
        build_model.create_and_pickle_model('test', model_type, 'test_cust')
        pred_results_dict = predict.predict_data_file(
                                pjoin(cfg.UPLOAD_FOLDER, "dotastro_215153.dat"),
                                'test', model_type, "test_cust",
                                metadata_path=pjoin(cfg.UPLOAD_FOLDER,
                                "215153_metadata.dat"), custom_features_script=pjoin(
                                cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "testfeature1.py"))
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(el[0] in [b'class1', b'class2', b'class3']
                       or el in [b'class1', b'class2', b'class3'])


@with_setup(copy_classification_test_data, remove_test_data)
def test_multiple_predict_classification():
    """Test main predict function on multiple files (classification)"""
    classifier_types = [model_type for model_type, model_class
                        in build_model.MODELS_TYPE_DICT.items()
                        if issubclass(model_class, sklearn.base.ClassifierMixin)]
    for model_type in classifier_types:
        build_model.create_and_pickle_model('test', model_type, 'test')
        pred_results_dict = predict.predict_data_file(
                                pjoin(cfg.UPLOAD_FOLDER,
                                      "215153_215176_218272_218934.tar.gz"),
                                'test', model_type, 'test',
                                metadata_path=pjoin(cfg.UPLOAD_FOLDER,
                                "215153_215176_218272_218934_metadata.dat"),
                                custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(el[0] in [b'class1', b'class2', b'class3']
                       or el in [b'class1', b'class2', b'class3'])


@with_setup(copy_regression_test_data, remove_test_data)
def test_single_predict_regression():
    """Test main predict function on single file (regression)"""
    regressor_types = [model_type for model_type, model_class
                       in build_model.MODELS_TYPE_DICT.items()
                       if issubclass(model_class, sklearn.base.RegressorMixin)]
    for model_type in regressor_types:
        build_model.create_and_pickle_model('test', model_type, 'test_reg')
        pred_results_dict = predict.predict_data_file(
                                pjoin(cfg.UPLOAD_FOLDER, "dotastro_215153.dat"),
                                'test', model_type, 'test_reg',
                                metadata_path=pjoin(cfg.UPLOAD_FOLDER,
                                "215153_metadata.dat"), custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(isinstance(el, float))


@with_setup(copy_regression_test_data, remove_test_data)
def test_multiple_predict_regression():
    """Test main predict function on multiple files (regression)"""
    regressor_types = [model_type for model_type, model_class
                       in build_model.MODELS_TYPE_DICT.items()
                       if issubclass(model_class, sklearn.base.RegressorMixin)]
    for model_type in regressor_types:
        build_model.create_and_pickle_model('test', model_type, 'test_reg')
        pred_results_dict = predict.predict_data_file(pjoin(cfg.UPLOAD_FOLDER,
                                "215153_215176_218272_218934.tar.gz"),
                                'test', model_type, 'test_reg',
                                metadata_path=pjoin(cfg.UPLOAD_FOLDER,
                                "215153_215176_218272_218934_metadata.dat"),
                                custom_features_script=None)
        for fname, results in pred_results_dict.items():
            for el in results['pred_results']:
                assert(isinstance(el, float))
