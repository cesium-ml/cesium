from mltsp import featurize
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
import ntpath
import tarfile
try:
    import cPickle as pickle
except:
    import pickle
from sklearn.externals import joblib
import shutil

def setup():
    fpaths = []
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(os.path.join(os.path.dirname(__file__),
                                   os.path.join("Data", fname)))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def test_features_file_parser():
    """Test features file parsing."""
    objects = featurize.parse_prefeaturized_csv_data(
        os.path.join(os.path.dirname(__file__), "Data/csv_test_data.csv"))
    npt.assert_array_equal(sorted(list(objects[0].keys())), ["col1", "col2",
                                                             "col3", "col4"])
    npt.assert_equal(objects[1]['col1'], ".1")
    npt.assert_equal(objects[-1]['col4'], "221")


def test_headerfile_parser():
    """Test header file parsing."""
    (features_to_use, fname_class_dict, fname_class_science_features_dict,
     fname_metadata_dict) = featurize.parse_headerfile(
         os.path.join(os.path.dirname(__file__),
                      "Data/sample_classes_with_metadata_headerfile.dat"),
         features_to_use=["dummy_featname"])
    npt.assert_array_equal(features_to_use, ["dummy_featname", "meta1", "meta2",
                                             "meta3"])
    npt.assert_equal(fname_class_dict["237022"], "W_Ursae_Maj")
    npt.assert_equal(fname_class_science_features_dict["215153"]["class"],
                     "Mira")
    npt.assert_equal(fname_metadata_dict["230395"]["meta1"], 0.270056761691)


def test_shorten_fname():
    """Test shorten_fname."""
    npt.assert_equal(featurize.shorten_fname("path/to/filename.sfx"),
                     "filename")
    npt.assert_equal(featurize.shorten_fname("/home/path/abc.dat"), "abc")


def test_featurize_tsdata_object():
    """Test featurize TS data object."""
    feats = featurize.featurize_tsdata_object(
        os.path.join(os.path.dirname(__file__), "Data/dotastro_215153.dat"),
        "dotastro_215153", None, {"dotastro_215153": "Mira"}, {}, ["std_err"])
    assert("std_err" in feats)
    assert(isinstance(feats["std_err"], float))


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


def test_generate_features():
    """Test generate_features"""
    objs = featurize.generate_features(
        os.path.join(cfg.UPLOAD_FOLDER,
                     "asas_training_subset_classes_with_metadata.dat"),
        os.path.join(cfg.UPLOAD_FOLDER,
                     "asas_training_subset.tar.gz"),
        ["std_err"],
        os.path.join(cfg.UPLOAD_FOLDER,
                     "testfeature1.py"),
        True, False, False, False, cfg.UPLOAD_FOLDER)
    npt.assert_equal(len(objs), 3)
    assert(all("std_err" in d for d in objs))
    assert(all("class" in d for d in objs))


def test_featurize_tsdata_object():
    """Test featurize TS data object function"""
    path_to_csv = os.path.join(os.path.dirname(__file__),
                               os.path.join("Data", "dotastro_215153.dat"))
    short_fname = featurize.shorten_fname(path_to_csv)
    custom_script_path = os.path.join(cfg.UPLOAD_FOLDER, "testfeature1.py")
    fname_class_dict = {"dotastro_215153": "Mira"}
    features_to_use = ["std_err"]
    all_feats = featurize.featurize_tsdata_object(
        path_to_csv, short_fname, custom_script_path, fname_class_dict,
        features_to_use)
    assert(isinstance(all_feats, dict))
    assert("std_err" in all_feats)


def test_remove_unzipped_files():
    """Test removal of unzipped files"""
    tarball_path = os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz")
    unzip_path = os.path.join(cfg.UPLOAD_FOLDER, "unzipped")
    tarball_obj = tarfile.open(tarball_path)
    tarball_obj.extractall(path=unzip_path)
    all_fnames = tarball_obj.getnames()
    for fname in all_fnames:
        assert(os.path.exists(os.path.join(unzip_path, fname)))

    featurize.remove_unzipped_files(all_fnames, unzip_path)

    for fname in all_fnames:
        assert(not os.path.exists(os.path.join(cfg.UPLOAD_FOLDER, fname)))


def test_extract_serial():
    """Test serial featurization of multiple TS data sources"""
    objs = featurize.extract_serial(
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset_with_metadata.dat"),
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        ["std_err"],
        os.path.join(cfg.UPLOAD_FOLDER, "testfeature1.py"),
        True, False, False, False, cfg.UPLOAD_FOLDER,
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
        "test_featset",
        "", ["f1", "f2"], False)
    with open("test_featset_features.csv") as f:
        feat_cont = f.read()
    with open("test_featset_features_with_classes.csv") as f:
        feat_class_cont = f.read()
    classes_list = joblib.load("test_featset_classes.pkl")
    os.remove("test_featset_features.csv")
    os.remove("test_featset_features_with_classes.csv")
    os.remove("test_featset_classes.pkl")
    os.remove(os.path.join(
        os.path.join(cfg.MLTSP_PACKAGE_PATH, "Flask/static/data"),
        "test_featset_features_with_classes.csv"))
    npt.assert_equal(feat_cont, "f1,f2\n21.0,0.15\n23.4,2.31\n")
    npt.assert_equal(feat_class_cont, "class,f1,f2\nc1,21.0,0.15\nc2,23.4,2.31\n")


def test_main_featurize_function():
    """Test main featurize function"""
    shutil.copy(
        os.path.join(os.path.dirname(__file__),
                     "Data/testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    results_msg = featurize.featurize(
        headerfile_path=os.path.join(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=os.path.join(cfg.UPLOAD_FOLDER,
                                  "asas_training_subset.tar.gz"),
        features_to_use=["std_err"],# #TEMP# TCP still broken under py3
        featureset_id="test", is_test=True,
        custom_script_path=os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                        "testfeature1.py"),
        USE_DISCO=True)
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv")))
    assert(os.path.exists(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_classes.pkl")))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "test_classes.pkl"))
    df = pd.io.parsers.read_csv(os.path.join(cfg.FEATURES_FOLDER,
                                       "test_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "test_features.csv"))
    os.remove(os.path.join(os.path.join(cfg.MLTSP_PACKAGE_PATH,
                                        "Flask/static/data"),
                           "test_features_with_classes.csv"))
    assert("std_err" in cols)


def teardown():
    fpaths = []
    for fname in ["asas_training_subset_classes_with_metadata.dat",
                  "asas_training_subset.tar.gz", "testfeature1.py"]:
        fpaths.append(os.path.join(cfg.UPLOAD_FOLDER, fname))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)
