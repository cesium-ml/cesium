from mltsp import run_in_docker_container as ridc
from mltsp import cfg
from mltsp import build_model
import numpy.testing as npt
import os
from os.path import join as pjoin
import pandas as pd
import shutil
import numpy as np
from sklearn.externals import joblib
try:
    import cPickle as pickle
except ImportError:
    import pickle
import tempfile


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def featurize_setup():
    fpaths = []
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(pjoin(DATA_PATH, fname))
    for fpath in fpaths:
        shutil.copy(fpath, cfg.UPLOAD_FOLDER)


def featurize_teardown():
    fpaths = [pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                    "testfeature1.py")]
    fnames = ["asas_training_subset_classes_with_metadata.dat",
              "asas_training_subset.tar.gz", "testfeature1.py"]
    for fname in fnames:
        fpaths.append(pjoin(cfg.UPLOAD_FOLDER, fname))
    fpaths.append(pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                        "testfeature1.py"))
    for fpath in fpaths:
        if os.path.exists(fpath):
            os.remove(fpath)


def test_copy_data_files_featurize_prep():
    """Test copy data files - featurization prep"""
    tmp_dir = tempfile.mkdtemp()
    test_data_dir = DATA_PATH
    args_dict = {
        'copied_data_dir': tmp_dir,
        'headerfile_path': pjoin(test_data_dir,
                                 "asas_training_subset_classes.dat"),
        'zipfile_path': "None",
        'custom_script_path': pjoin(test_data_dir,
                                    "testfeature1.py")}
    tmp_files_list = ridc.copy_data_files_featurize_prep(args_dict)
    assert os.path.exists(pjoin(tmp_dir, "function_args.pkl"))
    assert os.path.exists(pjoin(tmp_dir,
                                "asas_training_subset_classes.dat"))
    copied_custom_script_path = pjoin(tmp_dir, "custom_feature_defs.py")
    assert os.path.exists(copied_custom_script_path)
    os.remove(copied_custom_script_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    assert isinstance(tmp_files_list, list) and len(tmp_files_list) > 0


def test_spin_up_and_run_container():
    """Test spin up and run container"""
    client, cont_id = ridc.spin_up_and_run_container("mltsp/featurize", "/tmp")
    conts = client.containers(all=True)
    found_match = False
    for cont in conts:
        if cont["Id"] == cont_id:
            found_match = True
            break
    client.remove_container(container=cont_id, force=True)
    assert found_match


def test_copy_results_files_featurize():
    """Test copy results files - featurize"""
    copied_data_dir = tempfile.mkdtemp()
    featurize_setup()
    shutil.copy(
        pjoin(DATA_PATH, "testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    headerfile_path = pjoin(
        cfg.UPLOAD_FOLDER, "asas_training_subset_classes_with_metadata.dat")
    zipfile_path = pjoin(cfg.UPLOAD_FOLDER,
                         "asas_training_subset.tar.gz")
    features_to_use = ["std_err", "freq1_harmonics_freq_0"]
    featureset_key = "TEST01"
    is_test = True
    already_featurized = False
    custom_script_path = pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                               "testfeature1.py")
    args_dict = locals()
    tmp_files = ridc.copy_data_files_featurize_prep(args_dict)
    client, cont_id = ridc.spin_up_and_run_container("mltsp/featurize",
                                                     copied_data_dir)
    ridc.copy_results_files_featurize(featureset_key, client, cont_id)
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "TEST01_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "TEST01_classes.npy")))
    assert(os.path.exists(pjoin(pjoin(cfg.MLTSP_PACKAGE_PATH,
                                      "Flask/static/data"),
                                "TEST01_features_with_classes.csv")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEST01_classes.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEST01_features.csv"))
    os.remove(pjoin(pjoin(cfg.MLTSP_PACKAGE_PATH,
                          "Flask/static/data"),
                    "TEST01_features_with_classes.csv"))
    featurize_teardown()


def test_featurize_in_docker_container():
    """Test main featurize in docker container function"""
    featurize_setup()
    shutil.copy(
        pjoin(DATA_PATH, "testfeature1.py"),
        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
    ridc.featurize_in_docker_container(
        headerfile_path=pjoin(
            cfg.UPLOAD_FOLDER,
            "asas_training_subset_classes_with_metadata.dat"),
        zipfile_path=pjoin(cfg.UPLOAD_FOLDER,
                           "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        featureset_key="TEST01", is_test=True, already_featurized=False,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "TEST01_features.csv")))
    assert(os.path.exists(pjoin(cfg.FEATURES_FOLDER,
                                "TEST01_classes.npy")))
    assert(os.path.exists(pjoin(pjoin(cfg.MLTSP_PACKAGE_PATH,
                                      "Flask/static/data"),
                                "TEST01_features_with_classes.csv")))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEST01_classes.npy"))
    df = pd.io.parsers.read_csv(pjoin(cfg.FEATURES_FOLDER,
                                      "TEST01_features.csv"))
    cols = df.columns
    values = df.values
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEST01_features.csv"))
    os.remove(pjoin(pjoin(cfg.MLTSP_PACKAGE_PATH,
                          "Flask/static/data"),
                    "TEST01_features_with_classes.csv"))
    assert("std_err" in cols)
    assert("freq1_harmonics_freq_0" in cols)
    featurize_teardown()


def test_build_model_in_docker_container():
    """Test build model in docker container"""
    shutil.copy(pjoin(DATA_PATH, "test_classes.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))

    ridc.build_model_in_docker_container("TEMP_TEST01", "TEMP_TEST01", "RF")

    assert os.path.exists(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    model = joblib.load(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    assert hasattr(model, "predict_proba")
    os.remove(pjoin(cfg.MODELS_FOLDER, "TEMP_TEST01_RF.pkl"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    os.remove(pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))


def generate_model():
    shutil.copy(pjoin(DATA_PATH, "test_classes.npy"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(pjoin(DATA_PATH, "test_features.csv"),
                pjoin(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(pjoin(cfg.MODELS_FOLDER,
                                "TEMP_TEST01_RF.pkl"))


def test_copy_data_files_predict_prep():
    """Test copy data files - prediction prep"""
    tmp_dir = tempfile.mkdtemp()
    test_data_dir = DATA_PATH
    args_dict = {
        'copied_data_dir': tmp_dir,
        'newpred_file_path': pjoin(test_data_dir,
                                   "dotastro_215153.dat"),
        'metadata_file': "None",
        'custom_features_script': pjoin(test_data_dir,
                                        "testfeature1.py")}
    tmp_files_list = ridc.copy_data_files_predict_prep(args_dict)
    assert os.path.exists(pjoin(tmp_dir, "function_args.pkl"))
    assert os.path.exists(pjoin(tmp_dir,
                                "dotastro_215153.dat"))
    copied_custom_script_path = pjoin(tmp_dir, "custom_feature_defs.py")
    assert os.path.exists(copied_custom_script_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    assert isinstance(tmp_files_list, list) and len(tmp_files_list) > 0


def test_predict_in_docker_container():
    """Test predict in docker container"""
    generate_model()

    shutil.copy(pjoin(DATA_PATH, "dotastro_215153.dat"),
                pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"))
    shutil.copy(pjoin(DATA_PATH, "TESTRUN_215153_metadata.dat"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                      "TESTRUN_CF.py"))

    pred_results_dict = ridc.predict_in_docker_container(
        pjoin(cfg.UPLOAD_FOLDER, "TESTRUN_215153.dat"),
        "TEMP_TEST01", "RF", "TEMP_TEST01", "TEMP_TEST01",
        metadata_file=pjoin(cfg.UPLOAD_FOLDER,
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
