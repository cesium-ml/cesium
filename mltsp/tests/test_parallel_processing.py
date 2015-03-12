from mltsp import parallel_processing as prl_proc
from mltsp import cfg
import numpy.testing as npt
import os
import pandas as pd
import shutil

test_data_path = os.path.join(os.path.dirname(__file__), "Data")

def test_featurize_in_parallel():
    """Test main parallelized featurization function"""
    fname_features_dict = prl_proc.featurize_in_parallel(
        os.path.join(test_data_path,
                     "asas_training_subset_classes.dat"),
        os.path.join(test_data_path,
                     "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        is_test=True, custom_script_path=None)
    assert isinstance(fname_features_dict, dict)
    for k, v in fname_features_dict.items():
        assert "std_err" in v and "freq1_harmonics_freq_0" in v


def test_featurize_prediction_data_in_parallel():
    """Test parallel featurization of prediction TS data"""
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "Data/TESTRUN_features.csv"),
                cfg.FEATURES_FOLDER)
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "Data/TESTRUN_classes.pkl"),
                cfg.FEATURES_FOLDER)
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "Data/TESTRUN_RF.pkl"),
                cfg.MODELS_FOLDER)
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "Data/215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "Data/testfeature1.py"),
                os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                             "TESTRUN_CF.py"))

    features_and_tsdata_dict = prl_proc.featurize_prediction_data_in_parallel(
        os.path.join(test_data_path, "215153_215176_218272_218934.tar.gz"),
                     "TESTRUN")

    assert "std_err" in features_and_tsdata_dict\
        ["dotastro_218934.dat"]["features_dict"]
    os.remove(os.path.join(cfg.UPLOAD_FOLDER,
                           "215153_215176_218272_218934.tar.gz"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TESTRUN_features.csv"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER, "TESTRUN_classes.pkl"))
    os.remove(os.path.join(cfg.MODELS_FOLDER, "TESTRUN_RF.pkl"))
    os.remove(os.path.join(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py"))
