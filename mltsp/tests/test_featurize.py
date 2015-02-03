from mltsp import featurize
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
from subprocess import call


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
