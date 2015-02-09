from mltsp import predict_class as pred
from mltsp import featurize
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
from subprocess import call

def test_parse_metadata_file():
    """Test parse metadata file."""
    meta_feats = pred.parse_metadata_file(
        os.path.join(os.path.dirname(__file__),
                     "Data/215153_215176_218272_218934_metadata.dat"))
    assert("dotastro_215153.dat" in meta_feats)
    assert("meta1" in meta_feats["dotastro_215153.dat"])
    npt.assert_equal(meta_feats["dotastro_215153.dat"]["meta1"], 0.23423)


def test_determine_feats_used():
    """Test determine_feats_used"""
    feats_used = pred.determine_feats_used(
        "test", os.path.join(os.path.dirname(__file__), "Data"))
    npt.assert_array_equal(feats_used, ["meta1", "meta2", "meta3", "std_err"])


def test_parse_ts_data():
    """Test parsing of TS data"""
    ts_data = pred.parse_ts_data(os.path.join(os.path.dirname(__file__),
                                              "Data/dotastro_215153.dat"), ",")
    npt.assert_array_equal(ts_data[0], [2629.52836, 9.511, 0.042])
    npt.assert_array_equal(ts_data[-1], [5145.57672, 9.755, 0.06])
    npt.assert_equal(len(ts_data), 170)


def test_featurize_multiple_serially():
    """Test serial featurization"""
    meta_feats = pred.parse_metadata_file(
        os.path.join(os.path.dirname(__file__),
                     "Data/215153_215176_218272_218934_metadata.dat"))
    res_dict = pred.featurize_multiple_serially(
        os.path.join(os.path.dirname(__file__),
                     "Data/215153_215176_218272_218934.tar.gz"),
        "/tmp", ["std_err"], os.path.join(os.path.dirname(__file__),
                                          "Data/testfeature1.py"),
        meta_feats, cfg.UPLOAD_FOLDER)
    npt.assert_equal(len(res_dict), 4)
    assert all("std_err" in d["features_dict"] for fname, d in res_dict.items())
    assert all("ts_data" in d for fname, d in res_dict.items())


def test_featurize_single():
    """Test featurization of single TS data file"""
    meta_feats = pred.parse_metadata_file(
        os.path.join(os.path.dirname(__file__), "Data/215153_metadata.dat"))
    res_dict = pred.featurize_single(os.path.join(os.path.dirname(__file__),
                                                  "Data/dotastro_215153.dat"),
                                     ["std_err"], cfg.UPLOAD_FOLDER,
                                     os.path.join(os.path.dirname(__file__),
                                                  "Data/testfeature1.py"),
                                     meta_feats)
    assert all("std_err" in d["features_dict"] for fname, d in res_dict.items())
    assert all("ts_data" in d for fname, d in res_dict.items())
