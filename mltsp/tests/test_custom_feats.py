from mltsp import custom_feature_tools as cft
from mltsp import cfg
import numpy.testing as npt
import numpy as np
import os
import pandas as pd
from subprocess import call, PIPE
import shutil

def setup():
    call(["cp",
          os.path.join(os.path.dirname(__file__),
                       "Data/testfeature1.py"),
          os.path.join(cfg.MLTSP_PACKAGE_PATH,
                       "custom_feature_scripts/custom_feature_defs.py")])


def test_parse_for_req_prov_params():
    """Test parse custom script path for required & provided params"""
    fnames_req_prov_dict, all_required_params, all_provided_params = \
        cft.parse_for_req_prov_params(os.path.join(os.path.dirname(__file__),
                                                   "Data/testfeature1.py"))
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
        cft.parse_for_req_prov_params(os.path.join(os.path.dirname(__file__),
                                                   "Data/testfeature1.py"))
    extracted_feats_list = cft.call_custom_functions([{"t": [1.0, 1.2, 1.4],
                                                       "m": [12.2, 14.1, 15.2],
                                                       "e": [0.2, 0.3, 0.1]}],
                                                     all_required_params,
                                                     all_provided_params,
                                                     fnames_req_prov_dict)
    assert(isinstance(extracted_feats_list, list))
    npt.assert_equal(extracted_feats_list[0]["avg_mag"], np.average([12.2, 14.1,
                                                                     15.2]))
    assert(all(x in extracted_feats_list[0] for x in ["a", "l", "o"]))


def test_execute_functions_in_order():
    """Test execute_functions_in_order"""
    feats_list = cft.execute_functions_in_order(
        os.path.join(os.path.dirname(__file__), "Data/testfeature1.py"),
        {"t": [1.0, 1.2, 1.4], "m": [12.2, 14.1, 15.2], "e": [0.2, 0.3, 0.1]})
    assert(isinstance(feats_list, list))
    npt.assert_equal(feats_list[0]["avg_mag"], np.average([12.2, 14.1, 15.2]))
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
    npt.assert_array_equal(parsed_tsdata, [["1.2", "2.1", "3.0"],
                                           ["12.2", "21.3", "2.4"],
                                           [".3", "0.1", "1.4"]])
    tsdata = "1.2, 2.1, 3.0 \n12.2,21.3, 2.4\n.3 , 0.1 , 1.4 "
    parsed_tsdata = cft.parse_tsdata_to_lists(tsdata)
    npt.assert_array_equal(parsed_tsdata, [["1.2", "2.1", "3.0"],
                                           ["12.2", "21.3", "2.4"],
                                           [".3", "0.1", "1.4"]])
    new_parsed_tsdata = cft.parse_tsdata_to_lists(parsed_tsdata)
    npt.assert_array_equal(parsed_tsdata, new_parsed_tsdata)


def test_parse_tsdata_from_file():
    """Test parse TS data from file"""
    tsdata = cft.parse_tsdata_from_file(
        os.path.join(os.path.dirname(__file__), "Data/dotastro_215153.dat"))
    npt.assert_equal(len(tsdata), 170)
    npt.assert_equal(len(tsdata[-1]), 3)


def test_add_tsdata_to_feats_known_dict():
    """Test add TS data to features already known dict"""
    feats_known_dict_list = [{}]
    ts_datafile_paths = [os.path.join(os.path.dirname(__file__),
                                      "Data/dotastro_215153.dat")]
    cft.add_tsdata_to_feats_known_dict(feats_known_dict_list,
                                       ts_datafile_paths, None)
    npt.assert_equal(len(feats_known_dict_list[0]["t"]), 170)
    npt.assert_equal(len(feats_known_dict_list[0]["m"]), 170)
    npt.assert_equal(len(feats_known_dict_list[0]["e"]), 170)
    assert(isinstance(feats_known_dict_list[0]["e"][0], float))


def test_make_tmp_dir():
    """Test creation of temp directory"""
    container_name, tmp_dir_path = cft.make_tmp_dir()
    assert(isinstance(container_name, str))
    assert(isinstance(tmp_dir_path, str))
    assert(os.path.exists(tmp_dir_path))
    npt.assert_equal(len(container_name), 10)


def test_copy_data_to_tmp_dir():
    """Test copy data to temp dir"""
    cft.copy_data_to_tmp_dir(os.path.join(os.path.dirname(__file__),
                                          "Data/testfeature1.py"),
                             [{"feat1": 0.215, "feat2": 0.311},
                              {"feat1": 1, "feat2": 2}])
    #assert(os.path.exists(


def teardown():
    """Tear-down - remove tmp files"""
    if os.path.exists(tmp_dir_path):
        shutil.rmtree(tmp_dir_path, ignore_errors=True)
    assert(not os.path.exists(tmp_dir_path))

    for f in [os.path.join(cfg.MLTSP_PACKAGE_PATH,
                           "custom_feature_scripts/custom_feature_defs.py")]:
        if os.path.isfile(f):
            os.remove(f)
