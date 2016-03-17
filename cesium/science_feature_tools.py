import numpy as np
import dask.async
from . import science_features as sf


__all__ = ['FEATURES_LIST', 'generate_science_features']


FEATURES_LIST = [
    'amplitude',
    'percent_beyond_1_std',
    'flux_percentile_ratio_mid20',
    'flux_percentile_ratio_mid35',
    'flux_percentile_ratio_mid50',
    'flux_percentile_ratio_mid65',
    'flux_percentile_ratio_mid80',
    'fold2P_slope_10percentile',
    'fold2P_slope_90percentile',
    'freq1_amplitude1',
    'freq1_amplitude2',
    'freq1_amplitude3',
    'freq1_amplitude4',
    'freq1_freq',
    'freq1_rel_phase2',
    'freq1_rel_phase3',
    'freq1_rel_phase4',
    'freq1_lambda',
    'freq2_amplitude1',
    'freq2_amplitude2',
    'freq2_amplitude3',
    'freq2_amplitude4',
    'freq2_freq',
    'freq2_rel_phase2',
    'freq2_rel_phase3',
    'freq2_rel_phase4',
    'freq3_amplitude1',
    'freq3_amplitude2',
    'freq3_amplitude3',
    'freq3_amplitude4',
    'freq3_freq',
    'freq3_rel_phase2',
    'freq3_rel_phase3',
    'freq3_rel_phase4',
    'freq_amplitude_ratio_21',
    'freq_amplitude_ratio_31',
    'freq_frequency_ratio_21',
    'freq_frequency_ratio_31',
    'freq_model_max_delta_mags',
    'freq_model_min_delta_mags',
    'freq_model_phi1_phi2',
    'freq_n_alias',
    'freq1_signif',
    'freq_signif_ratio_21',
    'freq_signif_ratio_31',
    'freq_varrat',
    'freq_y_offset',
    'linear_trend',
    'maximum',
    'max_slope',
    'median',
    'median_absolute_deviation',
    'percent_close_to_median',
    'medperc90_2p_p',
    'minimum',
    'p2p_scatter_2praw',
    'p2p_scatter_over_mad',
    'p2p_scatter_pfold_over_mad',
    'p2p_ssqr_diff_over_var',
    'percent_amplitude',
    'percent_difference_flux_percentile',
    'period_fast',
    'qso_log_chi2_qsonu',
    'qso_log_chi2nuNULL_chi2nu',
    'scatter_res_raw',
    'skew',
    'std',
    'stetson_j',
    'stetson_k',
    'weighted_average']


def generate_science_features(t, m, e, features_to_compute=FEATURES_LIST):
    """Generate science features for provided time series data.

    Parameters
    ----------
    t : array_like
        Array containing time values.

    m : array_like
        Array containing data values.

    e : array_like
        Array containing measurement error values.

    features_to_compute : list
        Optional list containing names of desired features.

    Returns
    -------
    dict
        Dictionary containing newly-generated features. Keys are
        feature names, values are feature values (floats).
    """
    features_to_compute = [f for f in features_to_compute
                           if f in FEATURES_LIST]
    feature_graph = {
        # Standalone features (disconnected nodes)
       'amplitude': (sf.amplitude, m),
       'flux_percentile_ratio_mid20': (sf.flux_percentile_ratio, m, 20),
       'flux_percentile_ratio_mid35': (sf.flux_percentile_ratio, m, 35),
       'flux_percentile_ratio_mid50': (sf.flux_percentile_ratio, m, 50),
       'flux_percentile_ratio_mid65': (sf.flux_percentile_ratio, m, 65),
       'flux_percentile_ratio_mid80': (sf.flux_percentile_ratio, m, 80),
       'maximum': (sf.maximum, m),
       'max_slope': (sf.max_slope, t, m),
       'median': (sf.median, m),
       'median_absolute_deviation': (sf.median_absolute_deviation, m),
       'minimum': (sf.minimum, m),
       'percent_amplitude': (sf.percent_amplitude, m),
       'percent_beyond_1_std': (sf.percent_beyond_1_std, m, e),
       'percent_close_to_median': (sf.percent_close_to_median, m),
       'percent_difference_flux_percentile': (
           sf.percent_difference_flux_percentile, m),
       'skew': (sf.skew, m),
       'std': (sf.std, m),
       'stetson_j': (sf.stetson_j, m),
       'stetson_k': (sf.stetson_k, m),
       'weighted_average': (sf.weighted_average, m, e),

        # QSO model features
       'qso_model': (sf.qso_fit, t, m, e),
       'qso_log_chi2_qsonu': (sf.get_qso_log_chi2_qsonu, 'qso_model'),
       'qso_log_chi2nuNULL_chi2nu': (sf.get_qso_log_chi2nuNULL_chi2nu,
           'qso_model'),

        # Lomb-Scargle features
        'lomb_model': (sf.lomb_scargle_model, t, m, e),
        # These could easily be programmatically generated, but this is more readable
        'freq1_freq': (sf.get_lomb_frequency, 'lomb_model', 1),
        'freq2_freq': (sf.get_lomb_frequency, 'lomb_model', 2),
        'freq3_freq': (sf.get_lomb_frequency, 'lomb_model', 3),
        'freq1_amplitude1': (sf.get_lomb_amplitude, 'lomb_model', 1, 1),
        'freq1_amplitude2': (sf.get_lomb_amplitude, 'lomb_model', 1, 2),
        'freq1_amplitude3': (sf.get_lomb_amplitude, 'lomb_model', 1, 3),
        'freq1_amplitude4': (sf.get_lomb_amplitude, 'lomb_model', 1, 4),
        'freq2_amplitude1': (sf.get_lomb_amplitude, 'lomb_model', 2, 1),
        'freq2_amplitude2': (sf.get_lomb_amplitude, 'lomb_model', 2, 2),
        'freq2_amplitude3': (sf.get_lomb_amplitude, 'lomb_model', 2, 3),
        'freq2_amplitude4': (sf.get_lomb_amplitude, 'lomb_model', 2, 4),
        'freq3_amplitude1': (sf.get_lomb_amplitude, 'lomb_model', 3, 1),
        'freq3_amplitude2': (sf.get_lomb_amplitude, 'lomb_model', 3, 2),
        'freq3_amplitude3': (sf.get_lomb_amplitude, 'lomb_model', 3, 3),
        'freq3_amplitude4': (sf.get_lomb_amplitude, 'lomb_model', 3, 4),
        'freq1_rel_phase1': (sf.get_lomb_rel_phase, 'lomb_model', 1, 1),
        'freq1_rel_phase2': (sf.get_lomb_rel_phase, 'lomb_model', 1, 2),
        'freq1_rel_phase3': (sf.get_lomb_rel_phase, 'lomb_model', 1, 3),
        'freq1_rel_phase4': (sf.get_lomb_rel_phase, 'lomb_model', 1, 4),
        'freq2_rel_phase1': (sf.get_lomb_rel_phase, 'lomb_model', 2, 1),
        'freq2_rel_phase2': (sf.get_lomb_rel_phase, 'lomb_model', 2, 2),
        'freq2_rel_phase3': (sf.get_lomb_rel_phase, 'lomb_model', 2, 3),
        'freq2_rel_phase4': (sf.get_lomb_rel_phase, 'lomb_model', 2, 4),
        'freq3_rel_phase1': (sf.get_lomb_rel_phase, 'lomb_model', 3, 1),
        'freq3_rel_phase2': (sf.get_lomb_rel_phase, 'lomb_model', 3, 2),
        'freq3_rel_phase3': (sf.get_lomb_rel_phase, 'lomb_model', 3, 3),
        'freq3_rel_phase4': (sf.get_lomb_rel_phase, 'lomb_model', 3, 4),
        'freq_amplitude_ratio_21': (sf.get_lomb_amplitude_ratio, 'lomb_model', 2),
        'freq_amplitude_ratio_31': (sf.get_lomb_amplitude_ratio, 'lomb_model', 3),
        'freq_frequency_ratio_21': (sf.get_lomb_frequency_ratio, 'lomb_model', 2),
        'freq_frequency_ratio_31': (sf.get_lomb_frequency_ratio, 'lomb_model', 3),
        'freq_signif_ratio_21': (sf.get_lomb_signif_ratio, 'lomb_model', 2),
        'freq_signif_ratio_31': (sf.get_lomb_signif_ratio, 'lomb_model', 3),
        'freq1_lambda': (sf.get_lomb_lambda, 'lomb_model'),
        'freq1_signif': (sf.get_lomb_signif, 'lomb_model'),
        'freq_varrat': (sf.get_lomb_varrat, 'lomb_model'),
        'linear_trend': (sf.get_lomb_trend, 'lomb_model'),
        'freq_y_offset': (sf.get_lomb_y_offset, 'lomb_model'),

        # Other features that operate on Lomb-Scargle residuals
        'freq_n_alias': (sf.num_alias, 'lomb_model'),
        'scatter_res_raw': (sf.scatter_res_raw, t, m, e, 'lomb_model'),
        'periodic_model': (sf.periodic_model, 'lomb_model'),
        'freq_model_max_delta_mags': (sf.get_max_delta_mags, 'periodic_model'),
        'freq_model_min_delta_mags': (sf.get_min_delta_mags, 'periodic_model'),
        'freq_model_phi1_phi2': (sf.get_model_phi1_phi2, 'periodic_model'),
        'period_folded_model': (sf.period_folding, t, m, e, 'lomb_model'),
        'fold2P_slope_10percentile': (sf.get_fold2P_slope_percentile,
            'period_folded_model', 10),
        'fold2P_slope_90percentile': (sf.get_fold2P_slope_percentile,
            'period_folded_model', 90),
        'medperc90_2p_p': (sf.get_medperc90_2p_p, 'period_folded_model'),
        'p2p_model': (sf.p2p_model, t, m, 'freq1_freq'),
        'p2p_scatter_2praw': (sf.get_p2p_scatter_2praw, 'p2p_model'),
        'p2p_scatter_over_mad': (sf.get_p2p_scatter_over_mad, 'p2p_model'),
        'p2p_scatter_pfold_over_mad': (sf.get_p2p_scatter_pfold_over_mad,
                                       'p2p_model'),
        'p2p_ssqr_diff_over_var': (sf.get_p2p_ssqr_diff_over_var, 'p2p_model'),

        # Fast Lomb-Scargle from Gatspy
        'period_fast': (sf.lomb_scargle_fast_period, t, m, e),
   }

    # Do not execute in parallel; parallelization has already taken place at
    # the level of time series, so we compute features for a single time series
    # in serial.
    values = dask.async.get_sync(feature_graph, features_to_compute)
    return dict(zip(features_to_compute, values))
