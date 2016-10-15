import numpy as np

from .cadence_features import (cad_prob, delta_t_hist, double_to_single_step,
                               normalize_hist, find_sorted_peaks, peak_bin,
                               peak_ratio, n_epochs, average_err, median_err,
                               std_err, total_time, average_time, cadences,
                               cads_std, cads_avg, cads_med,
                               avg_double_to_single_step,
                               med_double_to_single_step,
                               std_double_to_single_step,
                               all_times_hist_peak_val,
                               all_times_hist_peak_bin,
                               nhist_peaks_numpeaks,
                               nhist_peaks_peak_val)

from .common_functions import (maximum, median, max_slope,
                               median_absolute_deviation, minimum,
                               percent_beyond_1_std, percent_close_to_median,
                               skew, std, weighted_average, average)
from .amplitude import (amplitude, percent_amplitude, flux_percentile_ratio,
                        percent_difference_flux_percentile)
from .qso_model import (qso_fit, get_qso_log_chi2_qsonu,
                        get_qso_log_chi2nuNULL_chi2nu)
from .stetson import (stetson_j, stetson_k)

from .lomb_scargle import (lomb_scargle_model, get_lomb_frequency,
                           get_lomb_amplitude, get_lomb_rel_phase,
                           get_lomb_amplitude_ratio, get_lomb_frequency_ratio,
                           get_lomb_signif_ratio, get_lomb_lambda,
                           get_lomb_signif, get_lomb_varrat, get_lomb_trend,
                           get_lomb_y_offset)
from .lomb_scargle_fast import lomb_scargle_fast_period
from .num_alias import num_alias
from .periodic_model import (periodic_model, get_max_delta_mags,
    get_min_delta_mags, get_model_phi1_phi2)
from .period_folding import (period_folding, get_fold2P_slope_percentile,
                             get_medperc90_2p_p, p2p_model,
                             get_p2p_scatter_2praw, get_p2p_scatter_over_mad,
                             get_p2p_scatter_pfold_over_mad,
                             get_p2p_ssqr_diff_over_var)
from .scatter_res_raw import scatter_res_raw


__all__ = ['CADENCE_GRAPH', 'CADENCE_FEATS', 'GENERAL_GRAPH', 'GENERAL_FEATS',
           'LOMB_SCARGLE_GRAPH', 'LOMB_SCARGLE_FEATS', 'ALL_GRAPHS',
           'generate_dask_graph']


# Need to track features separately from graph keys since some of those are
# intermediate values used only for future computations
CADENCE_FEATS = [
    'n_epochs','avg_err','med_err','std_err',
    'total_time','avgt','cads_std','avg_mag',
    'cads_avg','cads_med','cad_probs_1',
    'cad_probs_10','cad_probs_20','cad_probs_30',
    'cad_probs_40','cad_probs_50','cad_probs_100',
    'cad_probs_500','cad_probs_1000','cad_probs_5000',
    'cad_probs_10000','cad_probs_50000','cad_probs_100000',
    'cad_probs_500000','cad_probs_1000000','cad_probs_5000000',
    'cad_probs_10000000','med_double_to_single_step',
    'avg_double_to_single_step','std_double_to_single_step',
    'all_times_hist_peak_val','all_times_hist_peak_bin',
    'all_times_nhist_numpeaks','all_times_nhist_peak_val',
    'all_times_nhist_peak_1_to_2','all_times_nhist_peak_1_to_3',
    'all_times_nhist_peak_2_to_3','all_times_nhist_peak_1_to_4',
    'all_times_nhist_peak_2_to_4','all_times_nhist_peak_3_to_4',
    'all_times_nhist_peak1_bin','all_times_nhist_peak2_bin',
    'all_times_nhist_peak3_bin','all_times_nhist_peak4_bin']

CADENCE_GRAPH = {
    'n_epochs': (n_epochs, 't'),
    'avg_err': (average_err, 'e'),
    'med_err': (median_err, 'e'),
    'std_err': (std_err, 'e'),
    'total_time': (total_time, 't'),
    'avgt': (average_time, 't'),
    'cads': (cadences, 't'),
    'cads_std': (cads_std, 'cads'),
    'avg_mag': (average, 'm'),
    'cads_avg': (cads_avg, 'cads'),
    'cads_med': (cads_med, 'cads'),
    'cad_probs_1': (cad_prob, 'cads', 1),
    'cad_probs_10': (cad_prob, 'cads', 10),
    'cad_probs_20': (cad_prob, 'cads', 20),
    'cad_probs_30': (cad_prob, 'cads', 30),
    'cad_probs_40': (cad_prob, 'cads', 40),
    'cad_probs_50': (cad_prob, 'cads', 50),
    'cad_probs_100': (cad_prob, 'cads', 100),
    'cad_probs_500': (cad_prob, 'cads', 500),
    'cad_probs_1000': (cad_prob, 'cads', 1000),
    'cad_probs_5000': (cad_prob, 'cads', 5000),
    'cad_probs_10000': (cad_prob, 'cads', 10000),
    'cad_probs_50000': (cad_prob, 'cads', 50000),
    'cad_probs_100000': (cad_prob, 'cads', 100000),
    'cad_probs_500000': (cad_prob, 'cads', 500000),
    'cad_probs_1000000': (cad_prob, 'cads', 1000000),
    'cad_probs_5000000': (cad_prob, 'cads', 5000000),
    'cad_probs_10000000': (cad_prob, 'cads', 10000000),
    'double_to_single_step': (double_to_single_step, 'cads'),
    'avg_double_to_single_step': (avg_double_to_single_step,
                                  'double_to_single_step'),
    'med_double_to_single_step': (med_double_to_single_step,
                                  'double_to_single_step'),
    'std_double_to_single_step': (std_double_to_single_step,
                                  'double_to_single_step'),
    'delta_t_hist': (delta_t_hist, 't'),
    'delta_t_nhist': (normalize_hist, 'delta_t_hist', 'total_time'),
    'nhist_peaks': (find_sorted_peaks, 'delta_t_nhist'),
    'all_times_hist_peak_val': (all_times_hist_peak_val, 'delta_t_hist'),
    # Can''t' JSON serialize np.int64 under Python3 (yet?), cast as int first
    'all_times_hist_peak_bin': (all_times_hist_peak_bin,
                                'delta_t_hist'),
    'all_times_nhist_numpeaks': (nhist_peaks_numpeaks, 'nhist_peaks'),
    'all_times_nhist_peak_val': (nhist_peaks_peak_val, 'delta_t_nhist'),
    'all_times_nhist_peak_1_to_2': (peak_ratio, 'nhist_peaks', 1, 2),
    'all_times_nhist_peak_1_to_3': (peak_ratio, 'nhist_peaks', 1, 3),
    'all_times_nhist_peak_2_to_3': (peak_ratio, 'nhist_peaks', 2, 3),
    'all_times_nhist_peak_1_to_4': (peak_ratio, 'nhist_peaks', 1, 4),
    'all_times_nhist_peak_2_to_4': (peak_ratio, 'nhist_peaks', 2, 4),
    'all_times_nhist_peak_3_to_4': (peak_ratio, 'nhist_peaks', 3, 4),
    'all_times_nhist_peak1_bin': (peak_bin, 'nhist_peaks', 1),
    'all_times_nhist_peak2_bin': (peak_bin, 'nhist_peaks', 2),
    'all_times_nhist_peak3_bin': (peak_bin, 'nhist_peaks', 3),
    'all_times_nhist_peak4_bin': (peak_bin, 'nhist_peaks', 4)
}


GENERAL_FEATS = [
    'amplitude', 'flux_percentile_ratio_mid20', 'flux_percentile_ratio_mid35',
    'flux_percentile_ratio_mid50', 'flux_percentile_ratio_mid65',
    'flux_percentile_ratio_mid80', 'max_slope', 'maximum', 'median',
    'median_absolute_deviation', 'minimum', 'percent_amplitude',
    'percent_beyond_1_std', 'percent_close_to_median',
    'percent_difference_flux_percentile', 'period_fast', 'qso_log_chi2_qsonu',
    'qso_log_chi2nuNULL_chi2nu', 'skew', 'std', 'stetson_j', 'stetson_k',
    'weighted_average']


GENERAL_GRAPH = {
    # Standalone features (disconnected nodes)
   'amplitude': (amplitude, 'm'),
   'flux_percentile_ratio_mid20': (flux_percentile_ratio, 'm', 20),
   'flux_percentile_ratio_mid35': (flux_percentile_ratio, 'm', 35),
   'flux_percentile_ratio_mid50': (flux_percentile_ratio, 'm', 50),
   'flux_percentile_ratio_mid65': (flux_percentile_ratio, 'm', 65),
   'flux_percentile_ratio_mid80': (flux_percentile_ratio, 'm', 80),
   'maximum': (maximum, 'm'),
   'max_slope': (max_slope, 't', 'm'),
   'median': (median, 'm'),
   'median_absolute_deviation': (median_absolute_deviation, 'm'),
   'minimum': (minimum, 'm'),
   'percent_amplitude': (percent_amplitude, 'm'),
   'percent_beyond_1_std': (percent_beyond_1_std, 'm', 'e'),
   'percent_close_to_median': (percent_close_to_median, 'm'),
   'percent_difference_flux_percentile': (
       percent_difference_flux_percentile, 'm'),
   'skew': (skew, 'm'),
   'std': (std, 'm'),
   'stetson_j': (stetson_j, 'm'),
   'stetson_k': (stetson_k, 'm'),
   'weighted_average': (weighted_average, 'm', 'e'),

    # QSO model features
   'qso_model': (qso_fit, 't', 'm', 'e'),
   'qso_log_chi2_qsonu': (get_qso_log_chi2_qsonu, 'qso_model'),
   'qso_log_chi2nuNULL_chi2nu': (get_qso_log_chi2nuNULL_chi2nu,
       'qso_model'),

    # Fast Lomb-Scargle from Gatspy
    'period_fast': (lomb_scargle_fast_period, 't', 'm', 'e'),
}


LOMB_SCARGLE_FEATS = [
    'fold2P_slope_10percentile', 'fold2P_slope_90percentile',
    'freq1_amplitude1', 'freq1_amplitude2', 'freq1_amplitude3',
    'freq1_amplitude4', 'freq1_freq', 'freq1_lambda', 'freq1_rel_phase2',
    'freq1_rel_phase3', 'freq1_rel_phase4', 'freq1_signif', 'freq2_amplitude1',
    'freq2_amplitude2', 'freq2_amplitude3', 'freq2_amplitude4', 'freq2_freq',
    'freq2_rel_phase2', 'freq2_rel_phase3', 'freq2_rel_phase4',
    'freq3_amplitude1', 'freq3_amplitude2', 'freq3_amplitude3',
    'freq3_amplitude4', 'freq3_freq', 'freq3_rel_phase2', 'freq3_rel_phase3',
    'freq3_rel_phase4', 'freq_amplitude_ratio_21', 'freq_amplitude_ratio_31',
    'freq_frequency_ratio_21', 'freq_frequency_ratio_31',
    'freq_model_max_delta_mags', 'freq_model_min_delta_mags',
    'freq_model_phi1_phi2', 'freq_n_alias', 'freq_signif_ratio_21',
    'freq_signif_ratio_31', 'freq_varrat', 'freq_y_offset', 'linear_trend',
    'medperc90_2p_p', 'p2p_scatter_2praw', 'p2p_scatter_over_mad',
    'p2p_scatter_pfold_over_mad', 'p2p_ssqr_diff_over_var', 'scatter_res_raw']

LOMB_SCARGLE_GRAPH = {
    'lomb_model': (lomb_scargle_model, 't', 'm', 'e'),
    # These could easily be programmatically generated, but this is more readable
    'freq1_freq': (get_lomb_frequency, 'lomb_model', 1),
    'freq2_freq': (get_lomb_frequency, 'lomb_model', 2),
    'freq3_freq': (get_lomb_frequency, 'lomb_model', 3),
    'freq1_amplitude1': (get_lomb_amplitude, 'lomb_model', 1, 1),
    'freq1_amplitude2': (get_lomb_amplitude, 'lomb_model', 1, 2),
    'freq1_amplitude3': (get_lomb_amplitude, 'lomb_model', 1, 3),
    'freq1_amplitude4': (get_lomb_amplitude, 'lomb_model', 1, 4),
    'freq2_amplitude1': (get_lomb_amplitude, 'lomb_model', 2, 1),
    'freq2_amplitude2': (get_lomb_amplitude, 'lomb_model', 2, 2),
    'freq2_amplitude3': (get_lomb_amplitude, 'lomb_model', 2, 3),
    'freq2_amplitude4': (get_lomb_amplitude, 'lomb_model', 2, 4),
    'freq3_amplitude1': (get_lomb_amplitude, 'lomb_model', 3, 1),
    'freq3_amplitude2': (get_lomb_amplitude, 'lomb_model', 3, 2),
    'freq3_amplitude3': (get_lomb_amplitude, 'lomb_model', 3, 3),
    'freq3_amplitude4': (get_lomb_amplitude, 'lomb_model', 3, 4),
#        'freq1_rel_phase1': (get_lomb_rel_phase, 'lomb_model', 1, 1),
    'freq1_rel_phase2': (get_lomb_rel_phase, 'lomb_model', 1, 2),
    'freq1_rel_phase3': (get_lomb_rel_phase, 'lomb_model', 1, 3),
    'freq1_rel_phase4': (get_lomb_rel_phase, 'lomb_model', 1, 4),
#        'freq2_rel_phase1': (get_lomb_rel_phase, 'lomb_model', 2, 1),
    'freq2_rel_phase2': (get_lomb_rel_phase, 'lomb_model', 2, 2),
    'freq2_rel_phase3': (get_lomb_rel_phase, 'lomb_model', 2, 3),
    'freq2_rel_phase4': (get_lomb_rel_phase, 'lomb_model', 2, 4),
#        'freq3_rel_phase1': (get_lomb_rel_phase, 'lomb_model', 3, 1),
    'freq3_rel_phase2': (get_lomb_rel_phase, 'lomb_model', 3, 2),
    'freq3_rel_phase3': (get_lomb_rel_phase, 'lomb_model', 3, 3),
    'freq3_rel_phase4': (get_lomb_rel_phase, 'lomb_model', 3, 4),
    'freq_amplitude_ratio_21': (get_lomb_amplitude_ratio, 'lomb_model', 2),
    'freq_amplitude_ratio_31': (get_lomb_amplitude_ratio, 'lomb_model', 3),
    'freq_frequency_ratio_21': (get_lomb_frequency_ratio, 'lomb_model', 2),
    'freq_frequency_ratio_31': (get_lomb_frequency_ratio, 'lomb_model', 3),
    'freq_signif_ratio_21': (get_lomb_signif_ratio, 'lomb_model', 2),
    'freq_signif_ratio_31': (get_lomb_signif_ratio, 'lomb_model', 3),
    'freq1_lambda': (get_lomb_lambda, 'lomb_model'),
    'freq1_signif': (get_lomb_signif, 'lomb_model'),
    'freq_varrat': (get_lomb_varrat, 'lomb_model'),
    'linear_trend': (get_lomb_trend, 'lomb_model'),
    'freq_y_offset': (get_lomb_y_offset, 'lomb_model'),

    # Other features that operate on Lomb-Scargle residuals
    'freq_n_alias': (num_alias, 'lomb_model'),
    'scatter_res_raw': (scatter_res_raw, 't', 'm', 'e', 'lomb_model'),
    'periodic_model': (periodic_model, 'lomb_model'),
    'freq_model_max_delta_mags': (get_max_delta_mags, 'periodic_model'),
    'freq_model_min_delta_mags': (get_min_delta_mags, 'periodic_model'),
    'freq_model_phi1_phi2': (get_model_phi1_phi2, 'periodic_model'),
    'period_folded_model': (period_folding, 't', 'm', 'e', 'lomb_model'),
    'fold2P_slope_10percentile': (get_fold2P_slope_percentile,
                                  'period_folded_model', 10),
    'fold2P_slope_90percentile': (get_fold2P_slope_percentile,
                                  'period_folded_model', 90),
    'medperc90_2p_p': (get_medperc90_2p_p, 'period_folded_model'),
    'p2p_model': (p2p_model, 't', 'm', 'freq1_freq'),
    'p2p_scatter_2praw': (get_p2p_scatter_2praw, 'p2p_model'),
    'p2p_scatter_over_mad': (get_p2p_scatter_over_mad, 'p2p_model'),
    'p2p_scatter_pfold_over_mad': (get_p2p_scatter_pfold_over_mad,
                                   'p2p_model'),
    'p2p_ssqr_diff_over_var': (get_p2p_ssqr_diff_over_var, 'p2p_model')
}


ALL_GRAPHS = [CADENCE_GRAPH, GENERAL_GRAPH, LOMB_SCARGLE_GRAPH]
def generate_dask_graph(t, m, e):
    full_graph = {'t': t, 'm': m, 'e': e}
    for graph in ALL_GRAPHS:
        full_graph.update(graph)
    return full_graph
