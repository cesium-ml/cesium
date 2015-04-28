from mltsp import parallel_processing as prl_proc
from mltsp import cfg
from mltsp import build_model
import os
from os.path import join as pjoin
import shutil


DATA_PATH = pjoin(os.path.dirname(__file__), "data")


def test_featurize_in_parallel():
    """Test main parallelized featurization function"""
    fname_features_dict = prl_proc.featurize_in_parallel(
        pjoin(DATA_PATH,
              "asas_training_subset_classes.dat"),
        pjoin(DATA_PATH,
              "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_harmonics_freq_0"],
        is_test=True, custom_script_path=None)
    assert isinstance(fname_features_dict, dict)
    for k, v in fname_features_dict.items():
        assert "std_err" in v and "freq1_harmonics_freq_0" in v


def generate_model():
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_classes.npy"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_classes.npy"))
    shutil.copy(os.path.join(os.path.join(os.path.dirname(__file__), "data"),
                             "test_features.csv"),
                os.path.join(cfg.FEATURES_FOLDER, "TEMP_TEST01_features.csv"))
    build_model.build_model("TEMP_TEST01", "TEMP_TEST01")
    assert os.path.exists(os.path.join(cfg.MODELS_FOLDER,
                                       "TEMP_TEST01_RF.pkl"))


def test_featurize_prediction_data_in_parallel():
    """Test parallel featurization of prediction TS data"""
    generate_model()
    shutil.copy(pjoin(DATA_PATH, "215153_215176_218272_218934.tar.gz"),
                cfg.UPLOAD_FOLDER)
    shutil.copy(pjoin(DATA_PATH, "testfeature1.py"),
                pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                      "TESTRUN_CF.py"))

    features_and_tsdata_dict = prl_proc.featurize_prediction_data_in_parallel(
        os.path.join(test_data_path, "215153_215176_218272_218934.tar.gz"),
                     "TEMP_TEST01")

    assert "std_err" in \
        features_and_tsdata_dict["dotastro_218934.dat"]["features_dict"]
    for fname in (
            pjoin(cfg.UPLOAD_FOLDER,
                  "215153_215176_218272_218934.tar.gz"),
            pjoin(cfg.FEATURES_FOLDER, "TESTRUN_features.csv"),
            pjoin(cfg.FEATURES_FOLDER, "TESTRUN_classes.npy"),
            pjoin(cfg.MODELS_FOLDER, "TESTRUN_RF.pkl"),
            pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER, "TESTRUN_CF.py")):
        if os.path.exists(fname):
            os.remove(fname)
