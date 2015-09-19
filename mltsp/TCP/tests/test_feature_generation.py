from mltsp import featurize
from mltsp import cfg
from mltsp.TCP.Software.feature_extract.Code import extractors

import numpy as np
import numpy.testing as npt

import time
import os
import shutil
import glob


# TODO just a list for reference, will eventually remove
untested_extractors = [
                       'freq_model_phi1_phi2_extractor', # TODO wrong?
                       'freq_n_alias_extractor', # TODO what is this?
                       ]


# These values are chosen because they lie exactly on the grid of frequencies
# searched by the Lomb Scargle optimization procedure
WAVE_FREQS = np.array([5.3, 3.3, 2.1])
# This value is hard-coded in Lomb Scargle algorithm algorithm
NUM_HARMONICS = 4


def setup():
    print("Copying data files")
    # copy data files to proper directory:
    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/asas_training_subset_classes.dat"),
                os.path.join(cfg.UPLOAD_FOLDER))

    shutil.copy(os.path.join(os.path.dirname(__file__),
                             "data/asas_training_subset.tar.gz"),
                os.path.join(cfg.UPLOAD_FOLDER))


# Random noise generated at irregularly-sampled times
def irregular_random(seed=0, size=50):
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 10, size))
    values = state.normal(1, 1, size)
    errors = state.exponential(0.1, size)
    return times, values, errors


# Periodic test data sampled at regular intervals: superposition
# of multiple sine waves, each with multiple harmonics
def regular_periodic(freqs, amplitudes, phase, size=501):
    times = np.linspace(0, 2, size)
    values = np.zeros(size)
    for (i,j), amplitude in np.ndenumerate(amplitudes):
        values += amplitude * np.sin(2*np.pi*times*freqs[i]*(j+1)+phase)
    errors = 1e-4*np.ones(size)
    return times, values, errors


# Periodic test data sampled at randomly spaced intervals: superposition
# of multiple sine waves, each with multiple harmonics
def irregular_periodic(freqs, amplitudes, phase, seed=0, size=501):
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 2, size))
    values = np.zeros(size)
    for i in range(len(freqs)):
        for j in range(NUM_HARMONICS):
            values += amplitudes[i,j] * np.sin(2*np.pi*times*freqs[i]*(j+1)+phase)
    errors = state.exponential(1e-2, size)
    return times, values, errors


def initialize_extractor_from_data(extractor, times, values, errors, **kwargs):
    data_dict = {'time_data': times, 'flux_data': values, 'rms_data': errors,
                 'time_data_unit': None, 'flux_data_unit': 'mag',
                }
    extractor.extr({'data': {'v': {'features': [], 'inter': [],
                                   'input': data_dict}}}, band='v')


# TODO test for few data points
def test_amplitude_extractor():
    times, values, errors = irregular_random()
    e = extractors.amplitude_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            (max(e.flux_data)-min(e.flux_data))/2.)

    e = extractors.percent_amplitude_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    max_scaled = 10**(-0.4*max(e.flux_data))
    min_scaled = 10**(-0.4*min(e.flux_data))
    med_scaled = 10**(-0.4*np.median(e.flux_data))
    peak_from_median = max(abs((max_scaled - med_scaled)/med_scaled),
                           abs((min_scaled - med_scaled))/med_scaled)
    npt.assert_allclose(e.extract(), peak_from_median)

    e = extractors.percent_difference_flux_percentile_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    band_offset = 13.72
    w_m2 = 10**(-0.4*(e.flux_data+band_offset)-3)  # 1 erg/s/cm^2 = 10^-3 w/m^2
    npt.assert_allclose(e.extract(), np.diff(
        np.percentile(w_m2, [5, 95])) / np.median(w_m2))

    e = extractors.flux_percentile_ratio_mid20_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            np.diff(np.percentile(w_m2, [40, 60])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    e = extractors.flux_percentile_ratio_mid35_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            np.diff(np.percentile(w_m2, [32.5, 67.5])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    e = extractors.flux_percentile_ratio_mid50_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            np.diff(np.percentile(w_m2, [25, 75])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    e = extractors.flux_percentile_ratio_mid65_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            np.diff(np.percentile(w_m2, [17.5, 82.5])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    e = extractors.flux_percentile_ratio_mid80_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(),
                            np.diff(np.percentile(w_m2, [10, 90])) /
                            np.diff(np.percentile(w_m2, [5, 95])))


def test_ar_is_extractor():
# Uses a long, slow exponential decay
# Even after removing LS fit, an AR model still fits well
    times = np.linspace(0, 500, 201)
    theta = 0.95
    sigma = 0.0
    values = theta ** (times/250.) + sigma*np.random.randn(len(times))
    errors = 1e-4*np.ones(len(times))

    e = extractors.ar_is_theta_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), theta, atol=3e-2)

    e = extractors.ar_is_sigma_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), sigma, atol=1e-5)

# Hard-coded values from reference data set
    times, values, errors = irregular_random()
    e = extractors.ar_is_theta_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), 5.9608609865491405e-06, rtol=1e-3)
    e = extractors.ar_is_sigma_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), 1.6427095072108497, rtol=1e-3)


# TODO is there a way to make this test more precise?
def test_delta_phase_2minima_extractor():
    times1, values1, errors1 = regular_periodic(np.array([1.0]), np.array(1.0,ndmin=2), 0.0)
    times2, values2, errors2 = regular_periodic(np.array([3.0]), np.array(0.5,ndmin=2), np.pi/8)
    e = extractors.delta_phase_2minima_extractor()
    initialize_extractor_from_data(e, times1, values1+values2, errors1+errors2)
# Closed-form distance between local minima
    npt.assert_allclose(e.extract(), 1 - 0.163143 - 0.351671, atol=5e-2)


def test_gskew_extractor():
    times, values, errors = irregular_random()
    e = extractors.gskew_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    i_3percent = int(round(0.03*len(e.flux_data)))
# TODO use percentile
    npt.assert_allclose(e.extract(), 2*np.median(e.flux_data) -
                            np.median(sorted(e.flux_data)[-i_3percent:]) -
                            np.median(sorted(e.flux_data)[0:i_3percent]))


def test_linear_extractor():
    from numpy.polynomial.polynomial import polyfit as pfit
    times, values, errors = irregular_random()
    e = extractors.linear_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    error_weights = 1. / (e.rms_data)**2 / ((1./e.rms_data)**2).sum()
    wls_coefs = pfit(e.time_data, e.flux_data, 1, w=error_weights**0.5)
    npt.assert_allclose(e.extract(), np.flipud(wls_coefs), rtol=1e-4)


# TODO the smoothed model here seems insanely oversmoothed
# In general all these extractors are a complete mess, punting for now
#"""
def test_lcmodel_extractor():
    frequencies = np.hstack((1., np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [2,0,0,0]
    phase = 0.0
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)

    e = extractors.lcmodel_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    lc_feats = e.extract()

# Median is zero for this data, so crossing median = changing sign
    incr_median_crosses = sum((np.abs(np.diff(np.sign(values))) > 1) &
                             (np.diff(values) > 0))
    npt.assert_allclose(lc_feats['median_n_per_day'], (incr_median_crosses+1) /
                        (max(times)-min(times)))
#"""


# TODO what about very short time scale? could cause problems
def test_lomb_scargle_regular_single_freq():
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)

# Only test the first (true) frequency; the rest correspond to noise
    e_name = 'freq1_harmonics_freq_0_extractor'
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(frequencies[0], e.extract())

# Hard-coded value from previous solution
    e_name = 'freq1_lambda_extractor'
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0.001996007984, e.extract(), rtol=1e-7)

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        e_name = 'freq{}_harmonics_amplitude_{}_extractor'.format(i+1,j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitude, e.extract(), rtol=1e-2, atol=1e-2)

# Only test the first (true) frequency; the rest correspond to noise
    for j in range(NUM_HARMONICS):
        e_name = 'freq1_harmonics_rel_phase_{}_extractor'.format(j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
# TODO why is this what 'relative phase' means?
        npt.assert_allclose(phase*j*(-1**j), e.extract(), rtol=1e-2, atol=1e-2)

# Frequency ratio not relevant since there is only; only test amplitude/signif
    for i in [1,2]:
        e_name = 'freq_amplitude_ratio_{}1_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(0., e.extract(), atol=1e-3)

# TODO make significance test more precise
    e = extractors.freq_signif_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_array_less(10., e.extract())
    """
     e_name = 'freq_signif_ratio_{}1_extractor'.format(i)
     e = getattr(extractors, e_name)()
     initialize_extractor_from_data(e, times, values, errors)
     npt.assert_allclose(0., e.extract(), atol=1e-3)
    """
# Only one frequency, so this should explain basically all the variance
    e = extractors.freq_varrat_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=5e-3)

# Exactly periodic, so the same minima/maxima should reoccur
    e = extractors.freq_model_max_delta_mags_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-6)
    e = extractors.freq_model_min_delta_mags_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-6)

# Linear trend should be zero since the signal is exactly sinusoidal
    e = extractors.linear_trend_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-4)

    folded_times = times % 1./(frequencies[0]/2.)
    sort_indices = np.argsort(folded_times)
    folded_times = folded_times[sort_indices]
    folded_values = values[sort_indices]

# Residuals from doubling period should be much higher
    e = extractors.medperc90_2p_p_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_array_less(10., e.extract())

# Slopes should be the same for {un,}folded data; use unfolded for stability
    slopes = np.diff(e.flux_data) / np.diff(e.time_data)
    e = extractors.fold2P_slope_10percentile_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.percentile(slopes,10), e.extract(), rtol=1e-2)
    e = extractors.fold2P_slope_90percentile_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.percentile(slopes,90), e.extract(), rtol=1e-2)


def test_lomb_scargle_irregular_single_freq():
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(WAVE_FREQS),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)

# Only test the first (true) frequency; the rest correspond to noise
    e_name = 'freq1_harmonics_freq_0_extractor'
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(frequencies[0], e.extract(), rtol=1e-2)

# Only test first frequency here; noise gives non-zero amplitudes for residuals
    for j in range(NUM_HARMONICS):
        e_name = 'freq1_harmonics_amplitude_{}_extractor'.format(j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitudes[0,j], e.extract(), rtol=5e-2, atol=5e-2)

        e_name = 'freq1_harmonics_rel_phase_{}_extractor'.format(j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
# TODO why is this what 'relative phase' means?
        npt.assert_allclose(phase*j*(-1**j), e.extract(), rtol=1e-1, atol=1e-1)

# TODO make significance test more precise
    e = extractors.freq_signif_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_array_less(10., e.extract())
    """
    e_name = 'freq_signif_ratio_{}1_extractor'.format(i)
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-3)
    """
# Only one frequency, so this should explain basically all the variance
    e = extractors.freq_varrat_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=5e-3)

    e = extractors.freq_y_offset_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(-np.mean(values), e.extract(), rtol=5e-2)
# TODO this extractor seems wrong to me; fix then test?
    """
    e = extractors.freq_model_phi1_phi2_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(-np.mean(values), e.extract(), rtol=5e-2)
    """


# Tests for features derived from period-folded data
def test_lomb_scargle_period_folding():
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(WAVE_FREQS),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)

# Folding is numerically unstable so we need to use the exact fitted frequency
    e = extractors.freq1_harmonics_freq_0_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    freq_est = e.extract()
# Fold by 1*period
    fold1ed_times = (times-times[0]) % (1./freq_est)
    sort_indices = np.argsort(fold1ed_times)
    fold1ed_times = fold1ed_times[sort_indices]
    fold1ed_values = values[sort_indices]
# Fold by 2*period
    fold2ed_times = (times-times[0]) % (2./freq_est)
    sort_indices = np.argsort(fold2ed_times)
    fold2ed_times = fold2ed_times[sort_indices]
    fold2ed_values = values[sort_indices]

    e = extractors.p2p_scatter_2praw_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.sum(np.diff(fold2ed_values)**2) /
                        np.sum(np.diff(values)**2), e.extract())

    e = extractors.p2p_ssqr_diff_over_var_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.sum(np.diff(values)**2) /
                        ((len(values) - 1) * np.var(values)), e.extract())

    e = extractors.p2p_scatter_over_mad_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.median(np.abs(np.diff(values))) /
                        np.median(np.abs(values-np.median(values))),
                        e.extract())

    e = extractors.p2p_scatter_pfold_over_mad_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(np.median(np.abs(np.diff(fold1ed_values))) /
                        np.median(np.abs(values-np.median(values))),
                        e.extract())


def test_lomb_scargle_regular_multi_freq():
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[:,0] = [4,2,1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)

    for i, frequency in enumerate(frequencies):
        e_name = 'freq{}_harmonics_freq_0_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(frequency, e.extract())

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        e_name = 'freq{}_harmonics_amplitude_{}_extractor'.format(i+1,j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitude, e.extract(), rtol=5e-2, atol=5e-2)

# Relative phase is zero for first harmonic
    for i in range(len(frequencies)):
        e_name = 'freq{}_harmonics_rel_phase_0_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(0., e.extract(), rtol=1e-2, atol=1e-2)

    for i in [1,2]:
        e_name = 'freq_amplitude_ratio_{}1_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitudes[i,0]/amplitudes[0,0], e.extract(), atol=2e-2)

        e_name = 'freq_frequency_ratio_{}1_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(frequencies[i]/frequencies[0], e.extract(), atol=1e-3)

# TODO make significance test more precise
    e = extractors.freq_signif_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_array_less(10., e.extract())
    """
    e_name = 'freq_signif_ratio_{}1_extractor'.format(i)
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-3)
    """


def test_lomb_scargle_irregular_multi_freq():
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[:,0] = [4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)

    for i, frequency in enumerate(frequencies):
        e_name = 'freq{}_harmonics_freq_0_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(frequency, e.extract(), rtol=1e-2)

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        e_name = 'freq{}_harmonics_amplitude_{}_extractor'.format(i+1,j)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitude, e.extract(), rtol=1e-1, atol=1e-1)

# Relative phase is zero for first harmonic
    for i in range(len(frequencies)):
        e_name = 'freq{}_harmonics_rel_phase_0_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(0., e.extract(), rtol=1e-2, atol=1e-2)

    for i in [1,2]:
        e_name = 'freq_amplitude_ratio_{}1_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(amplitudes[i,0]/amplitudes[0,0], e.extract(), atol=2e-2)

        e_name = 'freq_frequency_ratio_{}1_extractor'.format(i+1)
        e = getattr(extractors, e_name)()
        initialize_extractor_from_data(e, times, values, errors)
        npt.assert_allclose(frequencies[i]/frequencies[0], e.extract(), atol=5e-2)

# TODO make significance test more precise
    e = extractors.freq_signif_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_array_less(10., e.extract())
"""
    e_name = 'freq_signif_ratio_{}1_extractor'.format(i)
    e = getattr(extractors, e_name)()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(0., e.extract(), atol=1e-3)
"""

def test_max_extractor():
    times, values, errors = irregular_random()
    e = extractors.max_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_equal(e.extract(), max(e.flux_data))


# TODO this returns the index of the biggest slope...might be wrong
def test_max_slope_extractor():
    times, values, errors = irregular_random()
    e = extractors.max_slope_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    slopes = np.diff(e.flux_data) / np.diff(e.time_data)
    npt.assert_allclose(e.extract(), np.argmax(np.abs(slopes)))


def test_median_absolute_deviation_extractor():
    times, values, errors = irregular_random()
    e = extractors.median_absolute_deviation_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), np.median(
        np.abs(e.flux_data - np.median(e.flux_data))))


def test_median_buffer_range_percentage_extractor():
    times, values, errors = irregular_random()
    e = extractors.median_buffer_range_percentage_extractor()
    initialize_extractor_from_data(e, times, values, errors)
# TODO feature is currently broken; this test is for the broken version,
# should replace with commented version once fixed
    amplitude = (np.abs(max(e.flux_data)) - np.abs(min(e.flux_data))) / 2.
#    amplitude = (max(e.flux_data) - min(e.flux_data)) / 2.
    within_buffer = np.abs(e.flux_data - np.median(e.flux_data)) < 0.2*amplitude
    npt.assert_allclose(e.extract(), np.mean(within_buffer))


def test_median_extractor():
    times, values, errors = irregular_random()
    e = extractors.median_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), np.median(e.flux_data))


def test_min_extractor():
    times, values, errors = irregular_random()
    e = extractors.min_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_equal(e.extract(), min(e.flux_data))


def test_n_points_extractor():
    times, values, errors = irregular_random()
    e = extractors.n_points_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_equal(e.extract(), len(e.flux_data))


# TODO deprecated?
def test_old_dc_extractor():
    times, values, errors = irregular_random()
    e = extractors.old_dc_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), np.mean(e.flux_data))


def test_phase_dispersion_extractor():
# Frequency chosen to lie on the relevant search grid
    frequencies = np.hstack((5.36, np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [1,0,0,0]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    e = extractors.phase_dispersion_freq0_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), frequencies[0])

    e = extractors.freq1_harmonics_freq_0_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    lomb_freq = e.extract()
    e = extractors.ratio_PDM_LS_freq0_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), frequencies[0]/lomb_freq)


# Hard-coded values from previous implementation; not sure of examples with a
# closed-form solution
def test_qso_extractor():
    times, values, errors = irregular_random()
    e = extractors.qso_log_chi2_qsonu_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), 6.9844064754)

    times, values, errors = irregular_random()
    e = extractors.qso_log_chi2nuNULL_chi2nu_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), -0.456526327522)


def test_s_extractor():
    times, values, errors = irregular_random()
    e = extractors.s_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    x_bar_wt = (e.flux_data / (e.rms_data)**2).sum()/((1/e.rms_data)**2).sum()
    resids = e.flux_data-x_bar_wt
    npt.assert_allclose(e.extract(),
                            np.sqrt(sum(resids**2)/(len(e.flux_data)-1)))


# TODO these seem broken/deprecated, remove?
"""
def test_sine_fit_extractor():
    e = extractors.sine_fit_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), ...)


def test_sine_leastsq_extractor():
    e = extractors.sine_leastsq_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), ...)
"""

def test_scatter_res_raw_extractor():
    times, values, errors = irregular_random()
    e = extractors.lomb_scargle_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    lomb_dict = e.extract()
    residuals = values - lomb_dict['freq1_model']
    resid_mad = np.median(np.abs(residuals-np.median(residuals)))
    value_mad = np.median(np.abs(values-np.median(values)))
    e = extractors.scatter_res_raw_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), resid_mad/value_mad, atol=3e-2)


def test_skew_extractor():
    from scipy import stats
    times, values, errors = irregular_random()
    e = extractors.skew_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), stats.skew(e.flux_data))


def test_std_extractor():
    times, values, errors = irregular_random()
    e = extractors.std_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), np.std(e.flux_data))


# These steps are basically just copied from the Stetson code
def test_stetson_extractor():
    times, values, errors = irregular_random(size=201)
    e = extractors.stetson_j_extractor()
    initialize_extractor_from_data(e, times, values, errors)
# Stetson mean approximately equal to standard mean for large inputs
    dists = np.sqrt(float(len(values)) / (len(values) - 1.)) * (values - np.mean(values)) / 0.1
    npt.assert_allclose(e.extract(),
                        np.mean(np.sign(dists**2-1)*np.sqrt(np.abs(dists**2-1))),
                        rtol=1e-2)
# Stetson_j should be somewhat close to (scaled) variance for normal data
    npt.assert_allclose(e.extract()*0.1, np.var(values), rtol=2e-1)
# Hard-coded original value
    npt.assert_allclose(e.extract(), 7.591347175195703)

    e = extractors.stetson_k_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), 1./0.798 * np.mean(np.abs(dists)) / np.sqrt(np.mean(dists**2)), rtol=5e-4)
# Hard-coded original value
    npt.assert_allclose(e.extract(), 1.0087218792719013)


# TODO this should be a function not an extractor
def test_watt_per_m2_flux_extractor():
    times, values, errors = irregular_random()
    e = extractors.watt_per_m2_flux_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    band_const = 13.72  # from constants dict in watt_per_m2_flux_extractor
# 1 erg/s/cm^2 = 10^-3 w/m^2
    npt.assert_allclose(e.extract(), 10**(-0.4*(e.flux_data+band_const)-3))


# TODO more general name?
def test_weighted_average_extractor():
    times, values, errors = irregular_random()
    e = extractors.weighted_average_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    weighted_std_err = 1./sum(e.rms_data**2)
    error_weights = 1./(e.rms_data)**2 / weighted_std_err
    weighted_avg = np.average(e.flux_data, weights=error_weights)
    npt.assert_allclose(e.extract(), weighted_avg)

    e = extractors.wei_av_uncertainty_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_allclose(e.extract(), weighted_std_err)

    e = extractors.dist_from_u_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    dists_from_weighted_avg = e.flux_data - weighted_avg
    npt.assert_allclose(e.extract(), dists_from_weighted_avg)

    e = extractors.stdvs_from_u_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    stds_from_weighted_avg = dists_from_weighted_avg / np.sqrt(weighted_std_err)
    npt.assert_allclose(e.extract(), stds_from_weighted_avg)

    e = extractors.beyond1std_extractor()
    initialize_extractor_from_data(e, times, values, errors)
    npt.assert_equal(e.extract(), np.mean(stds_from_weighted_avg > 1.))


# TODO compare numbers of features, check for completeness
def test_feature_generation():
    for f in glob.glob(os.path.join(cfg.FEATURES_FOLDER, '/*.csv')):
        os.remove(f)

    tic = time.time()
    this_dir = os.path.join(os.path.dirname(__file__))

    featurize.featurize(
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset_classes.dat"),
        os.path.join(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        featureset_id="testfeatset", is_test=True,
        features_to_use=cfg.features_list_science
    )

    delta = time.time() - tic

    def features_from_csv(filename):
        with open(filename) as f:
            feature_names = f.readline().strip().split(",")
            feature_values = np.loadtxt(f, delimiter=',')

        return feature_names, feature_values

    features_extracted, values_computed = features_from_csv(
        os.path.join(cfg.FEATURES_FOLDER, "testfeatset_features.csv"))

    features_expected, values_expected = features_from_csv(
        os.path.join(this_dir, "data/expected_features.csv"))

    os.remove(os.path.join(cfg.FEATURES_FOLDER, "testfeatset_features.csv"))
    os.remove(os.path.join(cfg.FEATURES_FOLDER,
                           "testfeatset_classes.npy"))
    npt.assert_equal(len(features_extracted), 81)
    npt.assert_equal(features_extracted, features_expected)
    npt.assert_array_almost_equal(values_computed, values_expected)

    # Ensure this test takes less than a minute to run
    assert delta < 60


if __name__ == "__main__":
    setup()
    test_feature_generation()
