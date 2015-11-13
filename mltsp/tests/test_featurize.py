from mltsp import featurize
from mltsp import featurize_tools
from mltsp import cfg
from nose.tools import with_setup
import numpy.testing as npt
import os
from os.path import join as pjoin
import tarfile
import shutil
import numpy as np
import xray


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def copy_classification_test_data():
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py",
              "test_features_with_targets.csv", "test_features_with_targets.csv"]
    for fname in fnames:
        if fname.endswith('.py'):
            shutil.copy(pjoin(DATA_PATH, fname),
                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def copy_regression_test_data():
    fnames = ["asas_training_subset_targets.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        if fname.endswith('.py'):
            shutil.copy(pjoin(DATA_PATH, fname),
                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def remove_test_data():
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset_targets.dat","test_featureset.nc",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        for data_dir in [cfg.UPLOAD_FOLDER, cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                         cfg.FEATURES_FOLDER]:
            try:
                os.remove(pjoin(data_dir, fname))
            except OSError:
                pass


def test_headerfile_parser():
    """Test header file parsing."""
    targets, metadata = featurize_tools.parse_headerfile(
        pjoin(DATA_PATH, "sample_classes_with_metadata_headerfile.dat"))
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(targets.loc["237022"], "W_Ursae_Maj")
    npt.assert_almost_equal(metadata.loc["230395"].meta1, 0.270056761691)


def sample_dataset():
    ds = xray.Dataset({'f1': ('name', [21.0, 23.4]),
                       'f2': ('name', [0.15, 2.31])},
                      coords={'target': ['c1', 'c2']})
    return ds


def test_write_features_to_disk():
    """Test writing features to disk"""
    featurize.write_features_to_disk(sample_dataset(), "test")
    featureset = xray.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         "test_featureset.nc"))
    npt.assert_equal(list(featureset.data_vars), ['f1', 'f2'])
    npt.assert_equal(list(featureset.coords), ['target', 'name'])
    npt.assert_equal(featureset['f1'].values, [21.0, 23.4])
    npt.assert_equal(featureset['f2'].values, [0.15, 2.31])
    npt.assert_equal(featureset['target'].values, ['c1', 'c2'])


@with_setup(copy_classification_test_data, remove_test_data)
def test_main_featurize_function():
    """Test main featurize function"""
    featureset = featurize.featurize_data_file(header_path=pjoin(
        cfg.UPLOAD_FOLDER,"asas_training_subset_classes_with_metadata.dat"),
        data_path=pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "f"], featureset_id="test", first_N=5,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"))
    assert("std_err" in featureset.data_vars)
    assert("f" in featureset.data_vars)
    assert(all(class_name in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj',
                              'Delta_Scuti'] 
               for class_name in featureset['target'].values))

# TODO test for single ts file

@with_setup(copy_classification_test_data, remove_test_data)
def test_already_featurized_data():
    """Test featurize function for pre-featurized data"""
    featureset = featurize.load_and_store_feature_data(
        pjoin(cfg.UPLOAD_FOLDER, "test_features_with_targets.csv"),
        featureset_id="test", first_N=5)
    assert("std_err" in featureset)
    assert("amplitude" in featureset)
    assert(all(class_name in ['class1', 'class2','class3'] for class_name in
               featureset['target']))


@with_setup(copy_regression_test_data, remove_test_data)
def test_main_featurize_function_regression_data():
    """Test main featurize function - regression data"""
    featureset = featurize.featurize_data_file(
        header_path=pjoin(cfg.UPLOAD_FOLDER,
                          "asas_training_subset_targets.dat"),
        data_path=pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_freq", "amplitude"],
        featureset_id="test", first_N=5, custom_script_path=None)
    npt.assert_array_equal(sorted(featureset.data_vars), 
                           ["amplitude", "freq1_freq", "std_err"])
    assert(all(isinstance(target, (float, np.float))
               for target in featureset['target'].values))
