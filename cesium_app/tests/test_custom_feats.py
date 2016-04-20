from cesium_app import custom_feature_tools as cft
from cesium_app import docker_util
import cesium
from cesium import featurize_tools as ft
from cesium import data_management
import numpy.testing as npt
import numpy as np
import os
from os.path import join as pjoin
from subprocess import call, PIPE
import json
import shutil
import uuid
import tempfile
from numpy.testing import decorators as dec


DATA_DIR = pjoin(os.path.dirname(cesium.__file__), "tests/data")
APP_DATA_DIR = pjoin(os.path.dirname(__file__), "data")
if docker_util.docker_images_available():
    USE_DOCKER = True
else:
    USE_DOCKER = False
    print("WARNING: computing custom features outside Docker container...")


def test_parse_for_req_prov_params():
    """Test parse custom script path for required & provided params"""
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(pjoin(APP_DATA_DIR, "testfeature1.py"))
    assert(all(param in all_provided_params for param in ["period", "avg_mag",
                                                          "a", "g", "l", "o"]))
    assert(all(param in all_required_params for param in ["t", "m", "c",
                                                          "period"]))
    assert(fnames_req_prov_dict["test_feature6"]["requires"] == ["e"])
    assert(all(x in fnames_req_prov_dict["test_feature6"]["provides"] for x in
               ['q', 'n', 'o']))


def test_call_custom_functions():
    """Test executing of custom feature definition functions"""
    script_fpath = pjoin(APP_DATA_DIR, "testfeature1.py")
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(script_fpath)
    extracted_feats = cft.call_custom_functions(
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2],
         "e": [0.2, 0.3, 0.1]},
        all_required_params, all_provided_params, fnames_req_prov_dict,
        script_fpath)
    assert(isinstance(extracted_feats, dict))
    npt.assert_almost_equal(extracted_feats["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in extracted_feats for x in ["a", "l", "o"]))


def test_execute_functions_in_order():
    """Test execute_functions_in_order"""
    feats = cft.execute_functions_in_order(
        pjoin(APP_DATA_DIR, "testfeature1.py"),
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2], "e": [0.2, 0.3, 0.1]})
    assert(isinstance(feats, dict))
    npt.assert_almost_equal(feats["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in feats for x in ["a", "l", "o"]))


@dec.skipif(not USE_DOCKER, "Docker testing turned off")
def test_docker_installed():
    """Test check to see if Docker is installed on local machine"""
    assert(docker_util.docker_images_available())


@dec.skipif(not USE_DOCKER, "Docker testing turned off")
def test_docker_extract_features():
    """Test main Docker extract features method"""
    script_fpath = pjoin(APP_DATA_DIR, "testfeature1.py")
    ts_datafile = pjoin(DATA_DIR, "dotastro_215153.dat")
    t, m, e = data_management.parse_ts_data(ts_datafile)
    feats_known_dict = {'t': list(t), 'm': list(m), 'e': list(e)}
    results = cft.docker_extract_features(script_fpath, feats_known_dict)
    assert(isinstance(results, dict))
    npt.assert_almost_equal(results["avg_mag"], 10.347417647058824)


def test_assemble_test_data():
    """Test assemble test data"""
    td = cft.assemble_test_data()
    assert(isinstance(td, dict))
    assert("t" in td)
    npt.assert_almost_equal(td["t"][0], 2629.52836)


def test_verify_new_script():
    """Test verify_new_script"""
    feats = cft.verify_new_script(pjoin(APP_DATA_DIR, "testfeature1.py"), use_docker=False)
    npt.assert_almost_equal(feats["avg_mag"], 10.347417647058824)


def test_list_features_provided():
    """Test list_features_provided"""
    feats_prov = cft.list_features_provided(
        pjoin(APP_DATA_DIR, "testfeature1.py"))
    assert(all(feat in feats_prov for feat in ["j", "k", "f", "c", "avg_mag"]))
    npt.assert_equal(len(feats_prov), 17)


def test_generate_custom_features():
    """Test main generate custom features function"""
    t, m, e = data_management.parse_ts_data(pjoin(DATA_DIR,
                                                  "dotastro_215153.dat"))
    feats = cft.generate_custom_features(pjoin(APP_DATA_DIR, "testfeature1.py"),
                                         t, m, e, use_docker=USE_DOCKER)
    npt.assert_almost_equal(feats["avg_mag"], 10.347417647058824)
