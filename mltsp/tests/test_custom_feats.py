from mltsp import custom_feature_tools as cft
from mltsp import celery_task_tools as ctt
from mltsp import cfg
from mltsp import util
import numpy.testing as npt
import numpy as np
import os
from os.path import join as pjoin
from subprocess import call, PIPE
import shutil
import uuid
try:
    import cPickle as pickle
except:
    import pickle
import tempfile
from numpy.testing import decorators as dec


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
no_docker = (os.getenv("MLTSP_NO_DOCKER") == "1")


def setup():
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.MLTSP_PACKAGE_PATH,
                      "custom_feature_scripts/custom_feature_defs.py"))


def test_parse_for_req_prov_params():
    """Test parse custom script path for required & provided params"""
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(pjoin(DATA_PATH, "testfeature1.py"))
    assert(all(param in all_provided_params for param in ["period", "avg_mag",
                                                          "a", "g", "l", "o"]))
    assert(all(param in all_required_params for param in ["t", "m", "c",
                                                          "period"]))
    assert(fnames_req_prov_dict["test_feature6"]["requires"] == ["e"])
    assert(all(x in fnames_req_prov_dict["test_feature6"]["provides"] for x in
               ['q', 'n', 'o']))


def test_call_custom_functions():
    """Test executing of custom feature definition functions"""
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(pjoin(DATA_PATH, "testfeature1.py"))
    if not os.path.exists(pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                                "custom_feature_defs.py")):
        shutil.copyfile(pjoin(DATA_PATH, "testfeature1.py"),
                        pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                              "custom_feature_defs.py"))
    extracted_feats = cft.call_custom_functions(
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2],
          "e": [0.2, 0.3, 0.1]},
        all_required_params, all_provided_params, fnames_req_prov_dict)
    assert(isinstance(extracted_feats, dict))
    npt.assert_almost_equal(extracted_feats["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in extracted_feats for x in ["a", "l", "o"]))
    os.remove(pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER, "custom_feature_defs.py"))


def test_execute_functions_in_order():
    """Test execute_functions_in_order"""
    feats = cft.execute_functions_in_order(
        pjoin(DATA_PATH, "testfeature1.py"),
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2], "e": [0.2, 0.3, 0.1]})
    assert(isinstance(feats, dict))
    npt.assert_almost_equal(feats["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in feats for x in ["a", "l", "o"]))


@dec.skipif(no_docker, "Docker testing turned off")
def test_docker_installed():
    """Test check to see if Docker is installed on local machine"""
    assert(util.docker_images_available())


def test_generate_random_str():
    """Test generate random string"""
    rs = cft.generate_random_str()
    assert(isinstance(rs, (str, unicode)))
    npt.assert_equal(len(rs), 10)


def test_make_tmp_dir():
    """Test creation of temp directory"""
    tmp_dir_path = cft.make_tmp_dir()
    assert(os.path.exists(tmp_dir_path))
    shutil.rmtree(tmp_dir_path, ignore_errors=True)
    assert(not os.path.exists(tmp_dir_path))


def test_copy_data_to_tmp_dir():
    """Test copy data to temp dir"""
    tmp_dir_path = cft.make_tmp_dir()
    copied_file_path1 = pjoin(tmp_dir_path,
                              "custom_feature_defs.py")
    copied_file_path2 = pjoin(tmp_dir_path,
                              "features_already_known.pkl")

    feats_known_dict = {"feat1": 0.215, "feat2": 0.311}
    ts_datafile = pjoin(DATA_PATH, "dotastro_215153.dat")
    t, m, e = ctt.parse_ts_data(ts_datafile)
    feats_known_dict['t'] = t
    feats_known_dict['m'] = m
    feats_known_dict['e'] = e

    for fpath in [copied_file_path1, copied_file_path2]:
        if os.path.exists(fpath):
            os.remove(fpath)
    assert(not os.path.exists(copied_file_path1))
    cft.copy_data_to_tmp_dir(tmp_dir_path, pjoin(DATA_PATH, "testfeature1.py"),
                             feats_known_dict)
    assert(os.path.exists(copied_file_path1))
    assert(os.path.exists(copied_file_path2))
    with open(copied_file_path2, "rb") as f:
        unpickled_dict = pickle.load(f)
    npt.assert_equal(unpickled_dict, feats_known_dict)
    shutil.rmtree(tmp_dir_path, ignore_errors=True)


@dec.skipif(no_docker, "Docker testing turned off")
def test_extract_feats_in_docker_container():
    """Test custom feature extraction in Docker container"""
    tmp_dir_path = cft.make_tmp_dir()
    feats_known_dict = {"feat1": 0.215, "feat2": 0.311}
    ts_datafile = pjoin(DATA_PATH, "dotastro_215153.dat")
    t, m, e = ctt.parse_ts_data(ts_datafile)
    feats_known_dict['t'] = t
    feats_known_dict['m'] = m
    feats_known_dict['e'] = e
    cft.copy_data_to_tmp_dir(tmp_dir_path,
                             pjoin(DATA_PATH, "testfeature1.py"),
                             feats_known_dict)
    results = cft.extract_feats_in_docker_container("test", tmp_dir_path)
    shutil.rmtree(tmp_dir_path, ignore_errors=True)
    cft.remove_tmp_files(tmp_dir_path)
    assert(isinstance(results, dict))
    npt.assert_almost_equal(results["avg_mag"], 10.347417647058824)


def test_remove_tmp_files_and_container():
    """Test remove temp files and container"""
    cft.remove_tmp_files("/tmp/mltsp_test")
    assert(not os.path.exists("/tmp/mltsp_test"))
    for tmp_file in [pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "custom_feature_defs.py"),
                     pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "custom_feature_defs.pyc"),
                     pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "__init__.pyc")]:
        assert(not os.path.exists(tmp_file))


@dec.skipif(no_docker, "Docker testing turned off")
def test_docker_extract_features():
    """Test main Docker extract features method"""
    script_fpath = pjoin(DATA_PATH, "testfeature1.py")
    ts_datafile = pjoin(DATA_PATH, "dotastro_215153.dat")
    t, m, e = ctt.parse_ts_data(ts_datafile)
    feats_known_dict = {'t': t, 'm': m, 'e': e}
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
    feats = cft.verify_new_script(pjoin(DATA_PATH, "testfeature1.py"))
    npt.assert_almost_equal(feats["avg_mag"], 10.347417647058824)


def test_list_features_provided():
    """Test list_features_provided"""
    feats_prov = cft.list_features_provided(
        pjoin(DATA_PATH, "testfeature1.py"))
    assert(all(feat in feats_prov for feat in ["j", "k", "f", "c", "avg_mag"]))
    npt.assert_equal(len(feats_prov), 17)


def test_generate_custom_features():
    """Test main generate custom features function"""
    t, m, e = ctt.parse_ts_data(pjoin(DATA_PATH, "dotastro_215153.dat"))
    feats = cft.generate_custom_features(pjoin(DATA_PATH, "testfeature1.py"),
                                         t, m, e)
    npt.assert_almost_equal(feats["avg_mag"], 10.347417647058824)


def teardown():
    """Tear-down - remove tmp files"""
    for f in [pjoin(cfg.MLTSP_PACKAGE_PATH,
                    "custom_feature_scripts/custom_feature_defs.py")]:
        if os.path.isfile(f):
            os.remove(f)
