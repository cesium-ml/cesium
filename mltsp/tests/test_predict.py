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


def test_something():
    """ABC"""
