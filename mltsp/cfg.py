# cfg.py
#
# Config file for MLTSP app.
#
from __future__ import print_function
import os, sys

import yaml

# Load configuration
config_files = [
    os.path.expanduser('~/.config/mltsp/mltsp.yaml'),
    os.path.join(os.path.dirname(__file__), '../mltsp.yaml')
    ]

config_files = [os.path.abspath(cf) for cf in config_files]

config = {}
for cf in config_files:
    try:
        config = yaml.load(open(cf))
        break
    except IOError:
        pass

if not config:
    print("Warning!  No 'mltsp.yaml' configuration found in one of:\n\n",
          '\n '.join(config_files),
          "\n\nPlease refer to the installation guide for further\n"
          "instructions.\n\n"
          "If you don't want to read the manual, do the following:\n"
          "  import mltsp; mltsp.install()")
    sys.exit(-1)

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

# Specify path to generate_science_features script in TCP:
TCP_INGEST_TOOLS_PATH = os.path.join(MLTSP_PACKAGE_PATH,
                                     "TCP/Software/ingest_tools")

PROJECT_PATH_LINK = "/tmp/mltsp_link"

# Specify list of general time-series features to be used (must
# correspond to those in lc_tools.LightCurve object attributes):
features_list = [
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

# List of features to be extracted by TCP script:
features_list_science = [
    "source_id",
    "lcmodel_neg_n_per_day",
    "freq_signif_ratio_31",
    "max_slope",
    "lcmodel_pos_mag_ratio",
    "color_diff_vj",
    "gskew",
    "percent_difference_flux_percentile",
    "lcmodel_median_n_per_day",
    "flux_percentile_ratio_mid80",
    "lcmodel_pos_n_ratio",
    "freq_varrat",
    "freq_amplitude_ratio_31",
    "freq_model_phi1_phi2",
    "flux_percentile_ratio_mid65",
    "linear_trend",
    "fold2P_slope_10percentile",
    "median",
    "qso_log_chi2_qsonu",
    "p2p_ssqr_diff_over_var",
    "p2p_scatter_over_mad",
    "p2p_scatter_2praw",
    "beyond1std",
    "lcmodel_pos_area_ratio",
    "freq1_harmonics_amplitude_2",
    "freq1_harmonics_amplitude_3",
    "freq1_harmonics_amplitude_0",
    "freq1_harmonics_amplitude_1",
    "freq3_harmonics_rel_phase_3",
    "median_buffer_range_percentage",
    "freq_model_min_delta_mags",
    "median_absolute_deviation",
    "ar_is_theta",
    "freq3_harmonics_amplitude_1",
    "freq1_harmonics_freq_0",
    "weighted_average",
    "freq3_harmonics_amplitude_2",
    "freq_signif_ratio_21",
    "lcmodel_pos_n_per_day",
    "stetson_j",
    "stetson_k",
    "color_diff_rj",
    "freq_model_max_delta_mags",
    "ar_is_sigma",
    "fold2P_slope_90percentile",
    "skew",
    "delta_phase_2minima",
    "freq1_harmonics_rel_phase_0",
    "freq_frequency_ratio_21",
    "color_diff_hk",
    "freq_signif",
    "flux_percentile_ratio_mid20",
    "std",
    "flux_percentile_ratio_mid50",
    "percent_amplitude",
    "freq3_harmonics_amplitude_0",
    "medperc90_2p_p",
    "amplitude",
    "freq3_harmonics_amplitude_3",
    "freq_y_offset",
    "ratio_PDM_LS_freq0",
    "freq_frequency_ratio_31",
    "freq_n_alias",
    "freq1_harmonics_rel_phase_1",
    "freq1_harmonics_rel_phase_2",
    "freq1_harmonics_rel_phase_3",
    "color_bv_extinction",
    "qso_log_chi2nuNULL_chi2nu",
    "freq2_harmonics_freq_0",
    "flux_percentile_ratio_mid35",
    "freq3_harmonics_freq_0",
    "min",
    "freq_amplitude_ratio_21",
    "freq2_harmonics_amplitude_1",
    "freq2_harmonics_amplitude_0",
    "freq2_harmonics_amplitude_3",
    "freq2_harmonics_amplitude_2",
    "freq2_harmonics_rel_phase_3",
    "freq2_harmonics_rel_phase_2",
    "freq2_harmonics_rel_phase_1",
    "freq2_harmonics_rel_phase_0",
    "freq1_lambda",
    "max",
    "color_diff_jh",
    "scatter_res_raw",
    "freq3_harmonics_rel_phase_2",
    "color_diff_bj",
    "freq3_harmonics_rel_phase_0",
    "freq3_harmonics_rel_phase_1",
    "p2p_scatter_pfold_over_mad",
    "phase_dispersion_freq0"]

# TCP science features being ignored:
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
    "freq1_harmonics_rel_phase_0",
    "freq2_harmonics_rel_phase_0",
    "freq3_harmonics_rel_phase_0",
    "ratio_PDM_LS_freq0",
    "n_points"]


# Specify default features to plot in browser:
features_to_plot = [
    "freq1_harmonics_freq_0",
    "freq1_harmonics_amplitude_0",
    "median",
    "fold2P_slope_90percentile",
    "max",
    "min",
    "percent_difference_flux_percentile",
    "freq1_harmonics_rel_phase_1"]


if not os.path.exists(PROJECT_PATH):
    print("cfg.py: Non-existing project path (%s) specified" % PROJECT_PATH)
    from . import util
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

del yaml, os, sys, print_function, config_files

config['mltsp'] = locals()
