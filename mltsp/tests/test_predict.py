from mltsp import predict_class as pred
from mltsp import featurize
from mltsp import cfg
from mltsp import build_model
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_parse_metadata_file():
    """Test parse metadata file."""
    meta_feats = pred.parse_metadata_file(
        pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"))
    assert("dotastro_215153.dat" in meta_feats)
    assert("meta1" in meta_feats["dotastro_215153.dat"])
    npt.assert_almost_equal(meta_feats["dotastro_215153.dat"]["meta1"],
                            0.23423)


def test_determine_feats_used():
    """Test determine_feats_used"""
    for suffix in ["features.csv", "classes.npy"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    feats_used = pred.determine_feats_used("TEST001")
    npt.assert_array_equal(feats_used, ["meta1", "meta2", "meta3", "std_err"])
    for fname in ["TEST001_features.csv", "TEST001_classes.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


def test_parse_ts_data():
    """Test parsing of TS data"""
    ts_data = pred.parse_ts_data(pjoin(DATA_PATH, "dotastro_215153.dat"),
                                 ",")
    npt.assert_array_almost_equal(ts_data[0], [2629.52836, 9.511, 0.042])
    npt.assert_array_almost_equal(ts_data[-1], [5145.57672, 9.755, 0.06])
    npt.assert_equal(len(ts_data), 170)


def test_featurize_multiple_serially():
    """Test serial featurization"""
    meta_feats = pred.parse_metadata_file(
        pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"))
    res_dict = pred.featurize_multiple_serially(
        pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
        "/tmp", ["std_err"], pjoin(DATA_PATH, "testfeature1.py"),
        meta_feats)
    npt.assert_equal(len(res_dict), 4)
    assert all("std_err" in d["features_dict"]
               for fname, d in res_dict.items())
    assert all("ts_data" in d for fname, d in res_dict.items())


def test_featurize_single():
    """Test featurization of single TS data file"""
    meta_feats = pred.parse_metadata_file(
        pjoin(DATA_PATH, "215153_metadata.dat"))
    res_dict = pred.featurize_single(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        ["std_err"],
        pjoin(DATA_PATH, "testfeature1.py"),
        meta_feats)
    assert all("std_err" in d["features_dict"]
               for fname, d in res_dict.items())
    assert all("ts_data" in d for fname, d in res_dict.items())


def test_featurize_tsdata():
    """Test featurize_tsdata"""
    res_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        "TEMP_TEST01",
        None, None, False,
        ['std_err'], False)
    assert all("std_err" in d["features_dict"]
               for fname, d in res_dict.items())
    assert all("ts_data" in d for fname, d in res_dict.items())


def test_create_feat_dict_and_list():
    """Test create feat dict and list"""
    feat_val_list, feat_dict = pred.create_feat_dict_and_list(
        {"f1": 21.1, "f2": 3.1, "f3": 101.0},
        ["f1", "f2", "f3"], ["f1", "f2", "f3"])
    npt.assert_array_almost_equal(feat_val_list, [21.1, 3.1, 101.0])
    npt.assert_almost_equal(feat_dict['f1'], 21.1)
    feat_val_list, feat_dict = pred.create_feat_dict_and_list(
        {"f1": 21.1, "f2": 3.1, "f3": 101.0},
        ["f1", "f3"], ["f1", "f2", "f3"])
    npt.assert_array_almost_equal(feat_val_list, [21.1, 101.0])
    npt.assert_almost_equal(feat_dict['f1'], 21.1)
    assert "f2" not in feat_dict


def test_add_to_predict_results_dict():
    """Test add data to predict results dict"""
    for suffix in ["classes.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    results_dict = {}
    pred.add_to_predict_results_dict(results_dict, [[0.2, 0.5, 0.3]], "TT.dat",
                                     [1, 2, 3], {'f1': 2},
                                     "TEST001", 5)
    npt.assert_array_equal(results_dict["TT.dat"]["ts_data"], [1, 2, 3])
    npt.assert_equal(len(results_dict["TT.dat"]["pred_results_list"]), 3)
    for fname in ["TEST001_features.csv", "TEST001_classes.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


def generate_model():
    shutil.copy(pjoin(DATA_PATH, "test_classes.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01_RF.pkl"))


def test_do_model_predictions():
    """Test model predictions"""
    generate_model()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001_RF.pkl"))
    for suffix in ["classes.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = "TEST001"
    model_type = "RF"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        "TEST001",
        None, None, False,
        cfg.features_list, False)
    pred_results_dict = pred.do_model_predictions(data_dict, featset_key,
                                                  model_type, features_to_use,
                                                  5)
    assert("dotastro_215153.dat" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153.dat"]["features_dict"])


def test_main_predict():
    """Test main predict function"""

    generate_model()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                      "TESTRUN_CF.py"))

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RF", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                     "TESTRUN_CF.py"))

    npt.assert_equal(
        len(pred_results_dict["TESTRUN_215153.dat"]["pred_results_list"]),
        3)

    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py"))
