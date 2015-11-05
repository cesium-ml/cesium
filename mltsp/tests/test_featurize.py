from mltsp import featurize
from mltsp import featurize_tools
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import tarfile
import numpy as np
import pandas as pd
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_setup():
    fpaths = []
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py",
              "test_features_with_targets.csv"]
    for fname in fnames:
        fpaths.append(pjoin(DATA_PATH, fname))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def test_setup_regression():
    fpaths = []
    fnames = ["asas_training_subset_targets.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(pjoin(DATA_PATH, fname))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def test_headerfile_parser():
    """Test header file parsing."""
    targets, metadata = featurize_tools.parse_headerfile(
             pjoin(DATA_PATH, "sample_classes_with_metadata_headerfile.dat"))
    npt.assert_array_equal(metadata.columns, ["filename", "meta1", "meta2",
        "meta3"])
    npt.assert_equal(targets[targets.filename=="237022"].target.values[0],
            "W_Ursae_Maj")
    npt.assert_almost_equal(metadata[metadata.filename=="230395"].meta1.values[0],
            0.270056761691)


def test_write_features_to_disk():
    """Test writing features to disk"""
    featurize.write_features_to_disk(
        pd.DataFrame([{"f1": 21.0, "f2": 0.15, "target": "c1"},
         {"f1": 23.4, "f2": 2.31, "target": "c2"}]),
        "test_featset01", False)
    with open(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features.csv")) as f:
        feat_cont = f.read()
    with open(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features_with_targets.csv")) as f:
        feat_class_cont = f.read()
    targets_list = list(np.load(pjoin(cfg.FEATURES_FOLDER,
                                      "test_featset01_targets.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features_with_targets.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_targets.npy"))
    npt.assert_equal(feat_cont, "f1,f2\n21.0,0.15\n23.4,2.31\n")
    npt.assert_equal(feat_class_cont,
                     "target,f1,f2\nc1,21.0,0.15\nc2,23.4,2.31\n")


def test_main_featurize_function():
    """Test main featurize function"""
    test_setup()

    shutil.copy(
        pjoin(DATA_PATH, "testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    results_msg = featurize.featurize_data_archive(
        headerfile_path=pjoin(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=pjoin(cfg.UPLOAD_FOLDER,
                           "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "f"],
        featureset_id="test", first_N=5,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_targets.npy")))
    target_list = list(np.load(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy"))
    df = pd.io.parsers.read_csv(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_features_with_targets.csv"))
    assert("std_err" in cols)
    assert("f" in cols)
    assert(all(class_name in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti']
               for class_name in target_list))


def test_already_featurized_data():
    """Test featurize function for pre-featurized data"""
    test_setup()

    results_msg = featurize.load_and_store_feature_data(
        pjoin(cfg.UPLOAD_FOLDER, "test_features_with_targets.csv"),
        featureset_id="test", first_N=5)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_targets.npy")))
    target_list = list(np.load(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy"))
    df = pd.io.parsers.read_csv(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_features_with_targets.csv"))
    assert("std_err" in cols)
    assert("amplitude" in cols)
    assert(all(class_name in ['class1', 'class2','class3'] for class_name in
        target_list))


def test_main_featurize_function_regression_data():
    """Test main featurize function - regression data"""
    test_setup_regression()

    results_msg = featurize.featurize_data_archive(
        headerfile_path=pjoin(cfg.UPLOAD_FOLDER,
            "asas_training_subset_targets.dat"),
        zipfile_path=pjoin(cfg.UPLOAD_FOLDER,
                           "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_freq", "amplitude"],
        featureset_id="test", first_N=5,
        custom_script_path=None)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_targets.npy")))
    target_list = list(np.load(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_targets.npy"))
    df = pd.io.parsers.read_csv(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_features_with_targets.csv"))
    npt.assert_array_equal(sorted(cols), ["amplitude", "freq1_freq", "std_err"])
    assert(all(isinstance(target, (float, np.float))
               for target in target_list))


def test_teardown():
    fpaths = []
    for fname in ["asas_training_subset_classes_with_metadata.dat",
                  "asas_training_subset_targets.dat",
                  "asas_training_subset.tar.gz", "testfeature1.py"]:
        fpaths.append(pjoin(cfg.UPLOAD_FOLDER, fname))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)
