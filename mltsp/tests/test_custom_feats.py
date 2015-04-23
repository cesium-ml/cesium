from mltsp import custom_feature_tools as cft
from mltsp import cfg
import numpy.testing as npt
import numpy as np
import os
from os.path import join as pjoin
import pandas as pd
from subprocess import call, PIPE
import shutil
try:
    import cPickle as pickle
except:
    import pickle


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def setup():
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.MLTSP_PACKAGE_PATH,
                             "custom_feature_scripts/custom_feature_defs.py"))


def test_parse_csv_file():
    """Test parse CSV file"""
    t, m, e = cft.parse_csv_file(pjoin(DATA_PATH, "dotastro_215153.dat"))
    npt.assert_equal(len(t), 170)
    npt.assert_equal(len(e), 170)
    npt.assert_almost_equal(t[0], 2629.52836)

    t, m, e = cft.parse_csv_file(pjoin(DATA_PATH, "samp_ts_noerrs.dat"))
    npt.assert_equal(len(t), 4)
    npt.assert_equal(len(e), 0)
    npt.assert_almost_equal(t[0], 1.22)


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


def test_listify_feats_known_dict():
    """Test listifiy_feats_known_dict"""
    npt.assert_equal(cft.listify_feats_known_dict({"a": 2}), [{"a": 2}])
    npt.assert_equal(cft.listify_feats_known_dict([2, 3]), [2, 3])


def test_call_custom_functions():
    """Test executing of custom feature definition functions"""
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(pjoin(DATA_PATH, "testfeature1.py"))
    extracted_feats_list = cft.call_custom_functions(
        [{"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2], "e": [0.2, 0.3, 0.1]}],
        all_required_params, all_provided_params, fnames_req_prov_dict)
    assert(isinstance(extracted_feats_list, list))
    npt.assert_almost_equal(extracted_feats_list[0]["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in extracted_feats_list[0] for x in ["a", "l", "o"]))


def test_execute_functions_in_order():
    """Test execute_functions_in_order"""
    feats_list = cft.execute_functions_in_order(
        pjoin(DATA_PATH, "testfeature1.py"),
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2], "e": [0.2, 0.3, 0.1]})
    assert(isinstance(feats_list, list))
    npt.assert_almost_equal(feats_list[0]["avg_mag"],
                            np.average([12.2, 14.1, 15.2]))
    assert(all(x in feats_list[0] for x in ["a", "l", "o"]))


def test_docker_installed():
    """Test check to see if Docker is installed on local machine"""
    docker_installed = cft.docker_installed()
    assert(isinstance(docker_installed, bool))
    try:
        x = call(["docker"], stdout=PIPE, stderr=PIPE)
        docker_really_installed = True
    except OSError:
        docker_really_installed = False
    npt.assert_equal(docker_installed, docker_really_installed)


def test_parse_tsdata_to_lists():
    """Test parsing of TS data str to lists"""
    tsdata = "1.2,2.1,3.0\n12.2,21.3,2.4\n.3,0.1,1.4"
    parsed_tsdata = cft.parse_tsdata_to_lists(tsdata)
    npt.assert_array_equal(parsed_tsdata,
                           [["1.2", "2.1", "3.0"],
                            ["12.2", "21.3", "2.4"],
                            [".3", "0.1", "1.4"]])
    tsdata = "1.2, 2.1, 3.0 \n12.2,21.3, 2.4\n.3 , 0.1 , 1.4 "
    parsed_tsdata = cft.parse_tsdata_to_lists(tsdata)
    npt.assert_array_equal(parsed_tsdata,
                           [["1.2", "2.1", "3.0"],
                            ["12.2", "21.3", "2.4"],
                            [".3", "0.1", "1.4"]])
    new_parsed_tsdata = cft.parse_tsdata_to_lists(parsed_tsdata)
    npt.assert_array_equal(parsed_tsdata, new_parsed_tsdata)


def test_parse_tsdata_from_file():
    """Test parse TS data from file"""
    tsdata = cft.parse_tsdata_from_file(
        pjoin(DATA_PATH, "dotastro_215153.dat"))
    npt.assert_equal(len(tsdata), 170)
    npt.assert_equal(len(tsdata[-1]), 3)


def test_add_tsdata_to_feats_known_dict():
    """Test add TS data to features already known dict"""
    feats_known_dict_list = [{}]
    ts_datafile_paths = [pjoin(DATA_PATH, "dotastro_215153.dat")]
    cft.add_tsdata_to_feats_known_dict(feats_known_dict_list,
                                       ts_datafile_paths, None)
    npt.assert_equal(len(feats_known_dict_list[0]["t"]), 170)
    npt.assert_equal(len(feats_known_dict_list[0]["m"]), 170)
    npt.assert_equal(len(feats_known_dict_list[0]["e"]), 170)
    assert(isinstance(feats_known_dict_list[0]["e"][0], float))


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
    copied_file_path1 = pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                                    "custom_feature_defs.py")
    copied_file_path2 = pjoin(cfg.PROJECT_PATH,
                              "copied_data_files",
                              "features_already_known_list.pkl")

    feats_known_dict_list = [{"feat1": 0.215, "feat2": 0.311},
                             {"feat1": 1, "feat2": 2}]
    ts_datafile_paths = [pjoin(DATA_PATH, "dotastro_215153.dat")] * 2
    cft.add_tsdata_to_feats_known_dict(feats_known_dict_list,
                                       ts_datafile_paths, None)

    for fpath in [copied_file_path1, copied_file_path2]:
        if os.path.exists(fpath):
            os.remove(fpath)
    assert(not os.path.exists(copied_file_path1))
    cft.copy_data_to_tmp_dir(tmp_dir_path,
                             pjoin(DATA_PATH, "testfeature1.py"),
                             feats_known_dict_list)
    assert(os.path.exists(copied_file_path1))
    assert(os.path.exists(copied_file_path2))
    with open(copied_file_path2, "rb") as f:
        list_of_dict = pickle.load(f)
    npt.assert_equal(list_of_dict, feats_known_dict_list)
    shutil.rmtree(tmp_dir_path, ignore_errors=True)


def test_extract_feats_in_docker_container():
    """Test custom feature extraction in Docker container"""
    tmp_dir = "/tmp/mltsp_test"
    os.mkdir(tmp_dir)
    results = cft.extract_feats_in_docker_container("test", tmp_dir)
    npt.assert_equal(len(results), 2)
    assert(isinstance(results[0], dict))
    npt.assert_almost_equal(results[0]["avg_mag"], 10.347417647058824)


def test_remove_tmp_files_and_container():
    cft.remove_tmp_files("/tmp/mltsp_test")
    assert(not os.path.exists("/tmp/mltsp_test"))
    for tmp_file in [pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "custom_feature_defs.py"),
                     pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "custom_feature_defs.pyc"),
                     pjoin(cfg.TMP_CUSTOM_FEATS_FOLDER,
                           "__init__.pyc"),
                     pjoin(cfg.PROJECT_PATH,
                           "copied_data_files",
                           "features_already_known_list.pkl")]:
        assert(not os.path.exists(tmp_file))


def test_docker_extract_features():
    """Test main Docker extract features method"""
    script_fpath = pjoin(DATA_PATH, "testfeature1.py")
    ts_datafile_paths = ts_datafile_paths = [
        pjoin(DATA_PATH, "dotastro_215153.dat")]
    results = cft.docker_extract_features(script_fpath,
                                          ts_datafile_paths=ts_datafile_paths)
    npt.assert_equal(len(results), 1)
    assert(isinstance(results[0], dict))
    npt.assert_almost_equal(results[0]["avg_mag"], 10.347417647058824)


def test_assemble_test_data():
    """Test assemble test data"""
    td = cft.assemble_test_data()
    assert(isinstance(td, list))
    npt.assert_equal(len(td), 3)
    assert("t" in td[0])
    npt.assert_array_equal(td[-1]["t"], [1])
    npt.assert_almost_equal(td[0]["t"][0], 2629.52836)


def test_verify_new_script():
    """Test verify_new_script"""
    feats_list = cft.verify_new_script(pjoin(DATA_PATH, "testfeature1.py"))
    npt.assert_almost_equal(feats_list[0]["avg_mag"], 10.347417647058824)


def test_list_features_provided():
    """Test list_features_provided"""
    feats_prov = cft.list_features_provided(
        pjoin(DATA_PATH, "testfeature1.py"))
    assert(all(feat in feats_prov for feat in ["j", "k", "f", "c", "avg_mag"]))
    npt.assert_equal(len(feats_prov), 17)


def test_generate_custom_features():
    """Test main generate custom features function"""
    feats = cft.generate_custom_features(pjoin(DATA_PATH, "testfeature1.py"),
                                         pjoin(DATA_PATH, "dotastro_215153.dat"))
    npt.assert_almost_equal(feats[0]["avg_mag"], 10.347417647058824)


def test_running_in_docker_cont():
    """Test running in Docker cont check"""
    output = cft.is_running_in_docker_container()
    assert(isinstance(output, bool))
    npt.assert_equal(output, False)


def teardown():
    """Tear-down - remove tmp files"""
    for f in [pjoin(cfg.MLTSP_PACKAGE_PATH,
                    "custom_feature_scripts/custom_feature_defs.py")]:
        if os.path.isfile(f):
            os.remove(f)
