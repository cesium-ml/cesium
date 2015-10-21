from mltsp import predict as pred
from mltsp import cfg
from mltsp import build_model
import numpy.testing as npt
import os
from os.path import join as pjoin
import shutil
import numpy as np


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
    for suffix in ["features.csv", "targets.npy"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    feats_used = pred.determine_feats_used("TEST001")
    npt.assert_array_equal(feats_used, ["meta1", "meta2", "meta3",
                                        "std_err","amplitude"])

    for fname in ["TEST001_features.csv", "TEST001_targets.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


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
        None, None, False, ['amplitude', 'std_err'])
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
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    results_dict = {}
    pred.add_to_predict_results_dict_classification_proba(
		results_dict, [[0.2, 0.5, 0.3]], "TT.dat",
        [1, 2, 3], {'f1': 2}, "TEST001", 5)
    npt.assert_array_equal(results_dict["TT"]["ts_data"], [1, 2, 3])
    npt.assert_equal(len(results_dict["TT"]["pred_results"]), 3)
    for fname in ["TEST001_features.csv", "TEST001_targets.npy"]:
        os.remove(pjoin(cfg.FEATURES_FOLDER, fname))


def generate_model_rfc():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_rfr():
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_lc():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_lr():
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_rc():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_ardr():
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "ARDR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_brr():
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "BRR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_cust_feats_rfc():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features_wcust.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_cust_feats_rfr():
    shutil.copy(pjoin(DATA_PATH, "test_reg_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features_wcust.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "RFR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_cust_feats_lc():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features_wcust.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LC", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def generate_model_cust_feats_lr():
    shutil.copy(pjoin(DATA_PATH, "test_targets.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features_wcust.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "LR", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01.pkl"))


def test_do_model_predictions_rfc():
    """Test model predictions - RFC"""
    generate_model_rfc()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "RFC"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs", "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_rfc():
    """Test main predict function - RFC"""

    generate_model_rfc()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RFC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_cust_feats_rfc():
    """Test main predict function w/ custom feats - RFC"""

    generate_model_cust_feats_rfc()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                      "TESTRUN_CF.py"))

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RFC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                     "TESTRUN_CF.py"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py"))
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_tarball_rfc():
    """Test main predict function - tarball - RFC"""

    generate_model_rfc()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "RFC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_tarball_cust_feats_rfc():
    """Test main predict function - tarball w/ custom feats - RFC"""

    generate_model_cust_feats_rfc()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                      "TESTRUN_CF.py"))

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "RFC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                     "TESTRUN_CF.py"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    os.remove(pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py"))
    npt.assert_equal(
        len(pred_results_dict["dotastro_215153"]["pred_results"]),
        4)
    npt.assert_equal(len(pred_results_dict), 4)
    for res_dict in pred_results_dict.values():
        assert(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict)


def test_do_model_predictions_rfr():
    """Test model predictions - RFR"""
    generate_model_rfr()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "RFR"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_rfr():
    """Test main predict function - RFR"""

    generate_model_rfr()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RFR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_tarball_rfr():
    """Test main predict function - tarball - RFR"""

    generate_model_rfr()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "RFR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_do_model_predictions_lc():
    """Test model predictions - LC"""
    generate_model_lc()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "LC"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_lc():
    """Test main predict function - LC"""

    generate_model_lc()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "LC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_main_predict_tarball_lc():
    """Test main predict function - tarball - LC"""

    generate_model_lc()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "LC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(all(el[0] in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                             'Classical_Cepheid', 'W_Ursae_Maj', 'Delta_Scuti',
                             'RR_Lyrae']
                   for el in pred_results_dict[fname]\
                   ["pred_results"]) for fname in pred_results_dict))


def test_do_model_predictions_lr():
    """Test model predictions - LR"""
    generate_model_lr()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "LR"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_lr():
    """Test main predict function - LR"""

    generate_model_lr()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "LR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_tarball_lr():
    """Test main predict function - tarball - LR"""

    generate_model_lr()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "LR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_do_model_predictions_rc():
    """Test model predictions - RC"""
    generate_model_rc()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "RC"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(pred_results_dict[fname]["pred_results"] in
               ['Mira', 'Herbig_AEBE', 'Beta_Lyrae', 'Classical_Cepheid',
                'W_Ursae_Maj', 'Delta_Scuti', 'RR_Lyrae'] for fname in
               pred_results_dict))


def test_main_predict_rc():
    """Test main predict function - RC"""

    generate_model_rc()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(pred_results_dict[fname]["pred_results"] in
               ['Mira', 'Herbig_AEBE', 'Beta_Lyrae', 'Classical_Cepheid',
                'W_Ursae_Maj', 'Delta_Scuti', 'RR_Lyrae'] for fname in
               pred_results_dict))


def test_main_predict_tarball_rc():
    """Test main predict function - tarball - RC"""

    generate_model_rc()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "RC", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(pred_results_dict[fname]["pred_results"] in
               ['Mira', 'Herbig_AEBE', 'Beta_Lyrae', 'Classical_Cepheid',
                'W_Ursae_Maj', 'Delta_Scuti', 'RR_Lyrae'] for fname in
               pred_results_dict))


def test_do_model_predictions_ardr():
    """Test model predictions - ARD Regression"""
    generate_model_ardr()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "ARDR"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_ardr():
    """Test main predict function - ARD Regression"""

    generate_model_ardr()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "ARDR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_tarball_ardr():
    """Test main predict function - tarball - ARD Regression"""

    generate_model_ardr()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "ARDR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_do_model_predictions_brr():
    """Test model predictions - BR Regression"""
    generate_model_brr()
    os.rename(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"),
              pjoin(cfg.MODELS_FOLDER, "TEST001.pkl"))
    for suffix in ["targets.npy", "features.csv"]:
        shutil.copy(
            pjoin(DATA_PATH, "test_%s" % suffix),
            pjoin(cfg.FEATURES_FOLDER, "TEST001_%s" % suffix))
    featset_key = model_key = "TEST001"
    model_type = "BRR"
    features_to_use = ["std_err", "avg_err", "med_err", "n_epochs",
                       "amplitude"]
    data_dict = pred.featurize_tsdata(
        pjoin(DATA_PATH, "dotastro_215153.dat"),
        None, None, False, features_to_use)
    pred_results_dict = pred.do_model_predictions(data_dict, model_key,
                                                  model_type, featset_key,
                                                  features_to_use, 5)
    assert("dotastro_215153" in pred_results_dict)
    assert("std_err" in
           pred_results_dict["dotastro_215153"]["features_dict"])
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_brr():
    """Test main predict function - BR Regression"""

    generate_model_brr()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "BRR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "TESTRUN_215153_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))


def test_main_predict_tarball_brr():
    """Test main predict function - tarball - BR Regression"""

    generate_model_brr()

    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934_metadata.dat"),
                cfg.UPLOAD_FOLDER)

    pred_results_dict = pred.predict(
        pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"),
        "TEMP_TEST01", "BRR", "TEMP_TEST01",
        metadata_file_path=pjoin(cfg.UPLOAD_FOLDER,
                                 "215153_215176_218272_218934_metadata.dat"),
        custom_features_script=None)
    os.remove(pjoin(cfg.UPLOAD_FOLDER, "215153_215176_218272_218934.tar.gz"))
    os.remove(pjoin(cfg.UPLOAD_FOLDER,
                    "215153_215176_218272_218934_metadata.dat"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_targets.npy"))
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01.pkl"))
    npt.assert_equal(len(pred_results_dict), 4)
    assert(all(isinstance(pred_results_dict[fname]["pred_results"],
                          (float, np.float)) for fname in pred_results_dict))
