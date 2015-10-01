from mltsp import featurize
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import tarfile
import numpy as np
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_setup():
    fpaths = []
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(pjoin(DATA_PATH, fname))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def test_features_file_parser():
    """Test features file parsing."""
    objects = featurize.parse_prefeaturized_csv_data(
        pjoin(DATA_PATH, "csv_test_data.csv"))
    npt.assert_array_equal(sorted(list(objects[0].keys())), ["col1", "col2",
                                                             "col3", "col4"])
    npt.assert_equal(objects[1]['col1'], ".1")
    npt.assert_equal(objects[-1]['col4'], "221")


def test_headerfile_parser():
    """Test header file parsing."""
    (features_to_use, fname_class_dict, fname_class_science_features_dict,
     fname_metadata_dict) = featurize.parse_headerfile(
         pjoin(DATA_PATH, "sample_classes_with_metadata_headerfile.dat"),
         features_to_use=["dummy_featname"])
    npt.assert_array_equal(features_to_use, ["dummy_featname", "meta1",
                                             "meta2", "meta3"])
    npt.assert_equal(fname_class_dict["237022"], "W_Ursae_Maj")
    npt.assert_equal(fname_class_science_features_dict["215153"]["class"],
                     "Mira")
    npt.assert_almost_equal(fname_metadata_dict["230395"]["meta1"],
                            0.270056761691)


def test_shorten_fname():
    """Test shorten_fname."""
    npt.assert_equal(featurize.shorten_fname("path/to/filename.sfx"),
                     "filename")
    npt.assert_equal(featurize.shorten_fname("/home/path/abc.dat"), "abc")


def test_determine_feats_to_plot1():
    """Test determine feats to plot - 1"""
    ftp = featurize.determine_feats_to_plot(["abc", "221a", "22d"])
    assert("221a" in ftp)
    assert("median" not in ftp)
    ftp = featurize.determine_feats_to_plot(cfg.features_list_science)
    assert("freq1_amplitude1" in ftp)
    assert("median" in ftp)


def test_count_classes():
    """Test count_classes"""
    objs = [{"class": "class1"}, {"class": "class1"}, {"class": "class2"}]
    class_count, num_used, num_held_back = featurize.count_classes(objs)
    npt.assert_equal(class_count["class1"], 2)
    npt.assert_equal(class_count["class2"], 1)


def test_generate_features():
    """Test generate_features"""
    objs = featurize.generate_features(
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset_classes_with_metadata.dat"),
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset.tar.gz"),
        ["std_err"],
        pjoin(cfg.UPLOAD_FOLDER, "testfeature1.py"),
        True, False, False)
    npt.assert_equal(len(objs), 3)
    assert(all("std_err" in d for d in objs))
    assert(all("class" in d for d in objs))
    assert(all(d["class"] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti']
               for d in objs))


def test_determine_feats_to_plot2():
    """Test determine features to plot - 2"""
    ftpl = featurize.determine_feats_to_plot(cfg.features_to_plot)
    npt.assert_array_equal(ftpl, cfg.features_to_plot)
    ftpl = featurize.determine_feats_to_plot(cfg.features_list_science)
    npt.assert_array_equal(ftpl, cfg.features_to_plot)
    ftpl = featurize.determine_feats_to_plot(cfg.features_list_obs)
    npt.assert_equal(len(ftpl), 5)
    assert(all(f in cfg.features_list_obs for f in ftpl))
    ftpl = featurize.determine_feats_to_plot(["f1"])
    npt.assert_array_equal(ftpl, ["f1"])


def test_write_column_titles():
    """Test write column titles to files"""
    with open("test_file1.txt", "w") as f1, open("test_file2.txt", "w") as f2:
        featurize.write_column_titles(f1, f2, ["feat1", "feat2", "feat3",
                                               "feat4"],
                                      ["feat1", "feat2", "feat3"],
                                      ["feat1", "feat2"])
    with open("test_file1.txt", "r") as f1, open("test_file2.txt", "r") as f2:
        f1_cont = f1.read()
        f2_cont = f2.read()
    os.remove(f1.name)
    os.remove(f2.name)
    npt.assert_equal(f1_cont, "feat1,feat2,feat3\n")
    npt.assert_equal(f2_cont, "class,feat1,feat2\n")


def test_write_features_to_disk():
    """Test writing features to disk"""
    featurize.write_features_to_disk(
        [{"f1": 21.0, "f2": 0.15, "class": "c1"},
         {"f1": 23.4, "f2": 2.31, "class": "c2"}],
        "test_featset01", ["f1", "f2"], False)
    with open(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features.csv")) as f:
        feat_cont = f.read()
    with open(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features_with_classes.csv")) as f:
        feat_class_cont = f.read()
    classes_list = list(np.load(pjoin(cfg.FEATURES_FOLDER,
                                      "test_featset01_classes.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features_with_classes.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_classes.npy"))
    os.remove(pjoin(cfg.MLTSP_PACKAGE_PATH, "Flask/static/data",
                    "test_featset01_features_with_classes.csv"))
    npt.assert_equal(feat_cont, "f1,f2\n21.0,0.15\n23.4,2.31\n")
    npt.assert_equal(feat_class_cont,
                     "class,f1,f2\nc1,21.0,0.15\nc2,23.4,2.31\n")


def test_main_featurize_function():
    """Test main featurize function"""
    test_setup()

    shutil.copy(
        pjoin(DATA_PATH, "testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    results_msg = featurize.featurize(
        headerfile_path=pjoin(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=pjoin(cfg.UPLOAD_FOLDER,
                           "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "f"],
        featureset_id="test", is_test=True,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"),)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_classes.npy")))
    class_list = list(np.load(pjoin(cfg.FEATURES_FOLDER, "test_classes.npy")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_classes.npy"))
    df = pd.io.parsers.read_csv(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(pjoin(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(pjoin(pjoin(cfg.MLTSP_PACKAGE_PATH,
                          "Flask/static/data"),
                    "test_features_with_classes.csv"))
    assert("std_err" in cols)
    assert("f" in cols)
    assert(all(class_name in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti']
               for class_name in class_list))


def test_teardown():
    fpaths = []
    for fname in ["asas_training_subset_classes_with_metadata.dat",
                  "asas_training_subset.tar.gz", "testfeature1.py"]:
        fpaths.append(pjoin(cfg.UPLOAD_FOLDER, fname))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)
