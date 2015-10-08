# cfg.py
#
# Config file for MLTSP app.
#
from __future__ import print_function
import os, sys
import multiprocessing
import yaml
from . import util

# Load configuration
config_files = [
    os.path.expanduser('~/.config/mltsp/mltsp.yaml'),
    os.path.join(os.path.dirname(__file__), '../mltsp.yaml')
    ]

config_files = [os.path.abspath(cf) for cf in config_files]

# Load example config file as default template
config = yaml.load(open(os.path.join(os.path.dirname(__file__),
                        'mltsp.yaml.example')))

for cf in config_files:
    try:
        config = yaml.load(open(cf))
        break
    except IOError:
        pass

if not config and not sys.argv[0].endswith('mltsp'):
    if not util.is_running_in_docker():
        print("Warning!  No 'mltsp.yaml' configuration found in one of:\n\n",
              '\n '.join(config_files),
              "\n\nPlease refer to the installation guide for further\n"
              "instructions.\n\n"
              "You probably want to execute:\n"
              "  mltsp --install")
        sys.exit(-1)

try:
    N_CORES = multiprocessing.cpu_count()
except Exception as e:
    print(e)
    print("Using N_CORES = 8")
    N_CORES = 8

CELERY_CONFIG = 'mltsp.ext.celeryconfig'
CELERY_BROKER = 'amqp://guest@localhost//'

# Specify path to project directory:
PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
MLTSP_PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.expanduser('~/.local/mltsp/')
SAMPLE_DATA_PATH = os.path.join(DATA_PATH, "sample_data")

# Specify path to uploads, models, and feature folders:
UPLOAD_FOLDER = os.path.join(DATA_PATH, "flask_uploads")
MODELS_FOLDER = os.path.join(DATA_PATH, "classifier_models")
FEATURES_FOLDER = os.path.join(DATA_PATH, "extracted_features")
CUSTOM_FEATURE_SCRIPT_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "custom_feature_scripts")
TMP_CUSTOM_FEATS_FOLDER = os.path.join(MLTSP_PACKAGE_PATH,
                                       "custom_feature_scripts")
ERR_LOG_PATH = os.path.join(
    DATA_PATH, "logs/errors_and_warnings.txt")

PROJECT_PATH_LINK = "/tmp/mltsp_link"

# Specify list of general time-series features to be used (must
# correspond to those in lc_tools.LightCurve object attributes):
features_list_obs = [
    "n_epochs","avg_err","med_err","std_err",
    "total_time","avgt","cads_std","avg_mag",
    "cads_avg","cads_med","cad_probs_1",
    "cad_probs_10","cad_probs_20","cad_probs_30",
    "cad_probs_40","cad_probs_50","cad_probs_100",
    "cad_probs_500","cad_probs_1000","cad_probs_5000",
    "cad_probs_10000","cad_probs_50000","cad_probs_100000",
    "cad_probs_500000","cad_probs_1000000","cad_probs_5000000",
    "cad_probs_10000000","med_double_to_single_step",
    "avg_double_to_single_step","std_double_to_single_step",
    "all_times_hist_peak_val","all_times_hist_peak_bin",
    "all_times_nhist_numpeaks","all_times_nhist_peak_val",
    "all_times_nhist_peak_1_to_2","all_times_nhist_peak_1_to_3",
    "all_times_nhist_peak_2_to_3","all_times_nhist_peak_1_to_4",
    "all_times_nhist_peak_2_to_4","all_times_nhist_peak_3_to_4",
    "all_times_nhist_peak1_bin","all_times_nhist_peak2_bin",
    "all_times_nhist_peak3_bin","all_times_nhist_peak4_bin"]

# List of science features to be extracted (former TCP module):
features_list_science = [
    "amplitude",
    "ar_is_sigma",
    "ar_is_theta",
    "percent_beyond_1_std",
    "color_bv_extinction",
    "color_diff_bj",
    "color_diff_hk",
    "color_diff_jh",
    "color_diff_rj",
    "color_diff_vj",
    "delta_phase_2minima",
    "flux_percentile_ratio_mid20",
    "flux_percentile_ratio_mid35",
    "flux_percentile_ratio_mid50",
    "flux_percentile_ratio_mid65",
    "flux_percentile_ratio_mid80",
    "fold2P_slope_10percentile",
    "fold2P_slope_90percentile",
    "freq1_amplitude1",
    "freq1_amplitude2",
    "freq1_amplitude3",
    "freq1_amplitude4",
    "freq1_freq",
#    "freq1_rel_phase1",
    "freq1_rel_phase2",
    "freq1_rel_phase3",
    "freq1_rel_phase4",
    "freq1_lambda",
    "freq2_amplitude1",
    "freq2_amplitude2",
    "freq2_amplitude3",
    "freq2_amplitude4",
    "freq2_freq",
#    "freq2_rel_phase1",
    "freq2_rel_phase2",
    "freq2_rel_phase3",
    "freq2_rel_phase4",
    "freq3_amplitude1",
    "freq3_amplitude2",
    "freq3_amplitude3",
    "freq3_amplitude4",
    "freq3_freq",
#    "freq3_rel_phase1",
    "freq3_rel_phase2",
    "freq3_rel_phase3",
    "freq3_rel_phase4",
    "freq_amplitude_ratio_21",
    "freq_amplitude_ratio_31",
    "freq_frequency_ratio_21",
    "freq_frequency_ratio_31",
    "freq_model_max_delta_mags",
    "freq_model_min_delta_mags",
    "freq_model_phi1_phi2",
    "freq_n_alias",
    "freq1_signif",
    "freq_signif_ratio_21",
    "freq_signif_ratio_31",
    "freq_varrat",
    "freq_y_offset",
    "gskew",
    "lcmodel_median_n_per_day",
    "lcmodel_neg_n_per_day",
    "lcmodel_pos_area_ratio",
    "lcmodel_pos_mag_ratio",
    "lcmodel_pos_n_per_day",
    "lcmodel_pos_n_ratio",
    "linear_trend",
    "maximum",
# TODO fix max_slope
#    "max_slope",
    "median",
    "median_absolute_deviation",
    "percent_close_to_median",
    "medperc90_2p_p",
    "minimum",
    "p2p_scatter_2praw",
    "p2p_scatter_over_mad",
    "p2p_scatter_pfold_over_mad",
    "p2p_ssqr_diff_over_var",
    "percent_amplitude",
    "percent_difference_flux_percentile",
    "phase_dispersion_freq0",
    "qso_log_chi2_qsonu",
    "qso_log_chi2nuNULL_chi2nu",
    "ratio_PDM_LS_freq0",
    "scatter_res_raw",
    "skew",
    "source_id",
    "std",
    "stetson_j",
    "stetson_k",
    "weighted_average"]

# TODO why ignore these?
ignore_feats_list_science = [
    "source_id",
    "color_bv_extinction",
    "color_diff_bj",
    "color_diff_hk",
    "color_diff_jh",
    "color_diff_rj",
    "color_diff_vj",
    "ar_is_theta",
    "ar_is_sigma",
    "delta_phase_2minima",
    "gskew",
    "lcmodel_median_n_per_day",
    "lcmodel_neg_n_per_day",
    "lcmodel_pos_area_ratio",
    "lcmodel_pos_mag_ratio",
    "lcmodel_pos_n_per_day",
    "lcmodel_pos_n_ratio",
    "phase_dispersion_freq0",
#    "freq1_rel_phase_0",
#    "freq2_rel_phase_0",
#    "freq3_rel_phase_0",
    "ratio_PDM_LS_freq0",
    "n_points"]
features_list_science = [f for f in features_list_science if f not in
        ignore_feats_list_science]


# Specify default features to plot in browser:
features_to_plot = [
    "freq1_freq",
    "freq1_amplitude1",
    "median",
    "fold2P_slope_90percentile",
    "maximum",
    "minimum",
    "percent_difference_flux_percentile",
    "freq1_rel_phase2"]


if not os.path.exists(PROJECT_PATH):
    print("cfg.py: Non-existing project path (%s) specified" % PROJECT_PATH)
    if util.is_running_in_docker() == False:
        sys.exit(-1)


for path in (DATA_PATH, UPLOAD_FOLDER, MODELS_FOLDER, FEATURES_FOLDER,
             ERR_LOG_PATH, CUSTOM_FEATURE_SCRIPT_FOLDER):
    if path == ERR_LOG_PATH:
        path = os.path.dirname(path)
    if not os.path.exists(path):
        print("Creating %s" % path)
        try:
            os.makedirs(path)
        except Exception as e:
            print(e)

del yaml, os, sys, print_function, config_files, multiprocessing

config['mltsp'] = locals()
