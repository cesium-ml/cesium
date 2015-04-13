from mltsp import featurize
from mltsp import cfg
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import ntpath
import tarfile
try:
    import cPickle as pickle
except:
    import pickle
from sklearn.externals import joblib
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
    npt.assert_array_equal(features_to_use, ["dummy_featname", "meta1", "meta2",
                                             "meta3"])
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


def test_determine_feats_to_plot():
    """Test determine feats to plot"""
    ftp = featurize.determine_feats_to_plot(["abc", "221a", "22d"])
    assert("221a" in ftp)
    assert("median" not in ftp)
    ftp = featurize.determine_feats_to_plot(cfg.features_list_science)
    assert("freq1_harmonics_amplitude_0" in ftp)
    assert("median" in ftp)


def test_count_classes():
    """Test count_classes"""
    objs = [{"class": "class1"}, {"class": "class1"}, {"class": "class2"}]
    class_count, num_used, num_held_back = featurize.count_classes(objs)
    npt.assert_equal(class_count["class1"], 2)
    npt.assert_equal(class_count["class2"], 1)


def test_generate_features_serial():
    """Test generate_features - serial extraction"""
    objs = featurize.generate_features(
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset_classes_with_metadata.dat"),
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset.tar.gz"),
        ["std_err"],
        pjoin(cfg.UPLOAD_FOLDER, "testfeature1.py"),
        True, False, False, False)
    npt.assert_equal(len(objs), 3)
    assert(all("std_err" in d for d in objs))
    assert(all("class" in d for d in objs))


def test_generate_features_parallel():
    """Test generate_features - parallelized extraction"""
    objs = featurize.generate_features(
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset_classes_with_metadata.dat"),
        pjoin(cfg.UPLOAD_FOLDER,
              "asas_training_subset.tar.gz"),
        ["std_err"],
        None, # Custom feats not working with Disco yet
        True, True, False, False)
    npt.assert_equal(len(objs), 3)
    assert(all("std_err" in d for d in objs))
    assert(all("class" in d for d in objs))


def test_featurize_tsdata_object():
    """Test featurize TS data object function"""
    path_to_csv = pjoin(DATA_PATH, "dotastro_215153.dat")
    short_fname = featurize.shorten_fname(path_to_csv)
    custom_script_path = pjoin(cfg.UPLOAD_FOLDER, "testfeature1.py")
    fname_class_dict = {"dotastro_215153": "Mira"}
    features_to_use = ["std_err", "freq1_harmonics_freq_0"]
    all_feats = featurize.featurize_tsdata_object(
        path_to_csv, short_fname, custom_script_path, fname_class_dict,
        features_to_use)
    assert(isinstance(all_feats, dict))
    assert("std_err" in all_feats)
    assert("freq1_harmonics_freq_0" in all_feats)


def test_remove_unzipped_files():
    """Test removal of unzipped files"""
    tarball_path = pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz")
    unzip_path = pjoin(cfg.UPLOAD_FOLDER, "unzipped")
    tarball_obj = tarfile.open(tarball_path)
    tarball_obj.extractall(path=unzip_path)
    all_fnames = tarball_obj.getnames()
    for fname in all_fnames:
        assert(os.path.exists(pjoin(unzip_path, fname)))

    featurize.remove_unzipped_files(all_fnames)

    for fname in all_fnames:
        assert(not os.path.exists(pjoin(cfg.UPLOAD_FOLDER, fname)))


def test_extract_serial():
    """Test serial featurization of multiple TS data sources"""
    objs = featurize.extract_serial(
        pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset_with_metadata.dat"),
        pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        ["std_err"],
        pjoin(cfg.UPLOAD_FOLDER, "testfeature1.py"),
        True, False, False, False,
        {"217801": "Mira", "219538": "Herbig_AEBE",
         "223592": "Beta_Lyrae"},
        {"217801": {"class": "Mira"},
         "219538": {"class": "Herbig_AEBE"},
         "223592": {"class": "Beta_Lyrae"}},
        {"217801": {}, "219538": {},
         "223592": {}})
    npt.assert_equal(len(objs), 3)
    assert(all("std_err" in obj for obj in objs))
    assert(all("avg_mag" in obj for obj in objs))


def test_determine_feats_to_plot():
    """Test determine features to plot"""
    ftpl = featurize.determine_feats_to_plot(cfg.features_to_plot)
    npt.assert_array_equal(ftpl, cfg.features_to_plot)
    ftpl = featurize.determine_feats_to_plot(cfg.features_list_science)
    npt.assert_array_equal(ftpl, cfg.features_to_plot)
    ftpl = featurize.determine_feats_to_plot(cfg.features_list)
    npt.assert_equal(len(ftpl), 5)
    assert(all(f in cfg.features_list for f in ftpl))
    ftpl = featurize.determine_feats_to_plot(["f1"])
    npt.assert_array_equal(ftpl, ["f1"])


def test_write_column_titles():
    """Test write column titles to files"""
    with open("test_file1.txt", "w") as f1, open("test_file2.txt", "w") as f2:
        featurize.write_column_titles(f1, f2, ["feat1", "feat2", "feat3", "feat4"],
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
    classes_list = joblib.load(pjoin(cfg.FEATURES_FOLDER,
                                     "test_featset_classes.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_features_with_classes.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER,
                    "test_featset01_classes.npy"))
    os.remove(pjoin(cfg.MLTSP_PACKAGE_PATH, "Flask/static/data",
                    "test_featset01_features_with_classes.csv"))
    npt.assert_equal(feat_cont, "f1,f2\n21.0,0.15\n23.4,2.31\n")
    npt.assert_equal(feat_class_cont, "class,f1,f2\nc1,21.0,0.15\nc2,23.4,2.31\n")


def test_main_featurize_function():
    """Test main featurize function - serial extraction"""
    shutil.copy(
        pjoin(DATA_PATH, "testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    results_msg = featurize.featurize(
        headerfile_path=pjoin(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=pjoin(cfg.UPLOAD_FOLDER,
                           "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        featureset_id="test", is_test=True,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"),
        USE_DISCO=False)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_classes.npy")))
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
    assert("freq1_harmonics_freq_0" in cols)


def test_main_featurize_function_disco():
    """Test main featurize function - using Disco"""
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
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        featureset_id="test", is_test=True,
        custom_script_path=None,# TODO: Doesn't work when using Disco!!!
        USE_DISCO=True)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "test_classes.npy")))
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
    assert("freq1_harmonics_freq_0" in cols)


def test_teardown():
    fpaths = []
    for fname in ["asas_training_subset_classes_with_metadata.dat",
                  "asas_training_subset.tar.gz", "testfeature1.py"]:
        fpaths.append(pjoin(cfg.UPLOAD_FOLDER, fname))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)
