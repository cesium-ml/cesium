from cesium import data_management
from cesium import science_feature_tools as sft

import numpy as np
import numpy.testing as npt

import time
import os
import shutil
import glob


# These values are chosen because they lie exactly on the grid of frequencies
# searched by the Lomb Scargle optimization procedure
WAVE_FREQS = np.array([5.3, 3.3, 2.1])

# List of features that involve the Lomb-Scargle periodogram; we repeatedly
# compute these for each Lomb-Scargle test
lomb_features = [
        "fold2P_slope_10percentile",
        "fold2P_slope_90percentile",
        "freq1_amplitude1",
        "freq1_amplitude2",
        "freq1_amplitude3",
        "freq1_amplitude4",
        "freq1_freq",
#        "freq1_rel_phase1",
        "freq1_rel_phase2",
        "freq1_rel_phase3",
        "freq1_rel_phase4",
        "freq1_lambda",
        "freq2_amplitude1",
        "freq2_amplitude2",
        "freq2_amplitude3",
        "freq2_amplitude4",
        "freq2_freq",
#        "freq2_rel_phase1",
        "freq2_rel_phase2",
        "freq2_rel_phase3",
        "freq2_rel_phase4",
        "freq3_amplitude1",
        "freq3_amplitude2",
        "freq3_amplitude3",
        "freq3_amplitude4",
        "freq3_freq",
#        "freq3_rel_phase1",
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
        "linear_trend",
        "medperc90_2p_p",
        "p2p_scatter_2praw",
        "p2p_scatter_over_mad",
        "p2p_scatter_pfold_over_mad",
        "p2p_ssqr_diff_over_var",
        "scatter_res_raw"
]


def test_feature_generation():
    """Compare generated features to reference values."""
    this_dir = os.path.join(os.path.dirname(__file__))
    test_files = [
            os.path.join(this_dir, 'data/257141.dat'),
            os.path.join(this_dir, 'data/245486.dat'),
            os.path.join(this_dir, 'data/247327.dat'),
            ]
    features_extracted = None
    values_computed = None
    for i, ts_data_file_path in enumerate(test_files):
        t, m, e = data_management.parse_ts_data(ts_data_file_path)
        features = sft.generate_science_features(t, m, e)
        sorted_features = sorted(features.items())
        if features_extracted is None:
            features_extracted = [f[0] for f in sorted_features]
            values_computed = np.zeros((len(test_files),
                len(features_extracted)))
        values_computed[i,:] = [f[1] for f in sorted_features]

    def features_from_csv(filename):
        with open(filename) as f:
            feature_names = f.readline().strip().split(",")
            feature_values = np.loadtxt(f, delimiter=',')

        return feature_names, feature_values

    this_dir = os.path.join(os.path.dirname(__file__))
    features_expected, values_expected = features_from_csv(
        os.path.join(this_dir, "data/expected_features.csv"))

    npt.assert_equal(features_extracted, features_expected)
    npt.assert_array_almost_equal(values_computed, values_expected)


def irregular_random(seed=0, size=50):
    """Generate random test data at irregularly-sampled times."""
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 10, size))
    values = state.normal(1, 1, size)
    errors = state.exponential(0.1, size)
    return times, values, errors


def regular_periodic(freqs, amplitudes, phase, size=501):
    """
    Generate periodic test data sampled at regular intervals: superposition of
    multiple sine waves, each with multiple harmonics.
    """
    times = np.linspace(0, 2, size)
    values = np.zeros(size)
    for (i,j), amplitude in np.ndenumerate(amplitudes):
        values += amplitude * np.sin(2*np.pi*times*freqs[i]*(j+1) + phase)
    errors = 1e-4*np.ones(size)
    return times, values, errors


def irregular_periodic(freqs, amplitudes, phase, seed=0, size=501):
    """
    Generate periodic test data sampled at randomly-spaced intervals:
    superposition of multiple sine waves, each with multiple harmonics.
    """
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 2, size))
    values = np.zeros(size)
    for i in range(freqs.shape[0]):
        for j in range(amplitudes.shape[1]):
            values += amplitudes[i,j] * np.sin(2*np.pi*times*freqs[i]*(j+1)+phase)
    errors = state.exponential(1e-2, size)
    return times, values, errors


def test_amplitude():
    """Test features related to amplitude/magnitude percentiles."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['amplitude'])
    npt.assert_allclose(f['amplitude'], (max(values) - min(values)) /2.)

    f = sft.generate_science_features(times, values, errors, ['percent_amplitude'])
    max_scaled = 10**(-0.4 * max(values))
    min_scaled = 10**(-0.4 * min(values))
    med_scaled = 10**(-0.4 * np.median(values))
    peak_from_median = max(abs((max_scaled - med_scaled) / med_scaled),
            abs((min_scaled - med_scaled)) / med_scaled)
    npt.assert_allclose(f['percent_amplitude'], peak_from_median, rtol=5e-4)

    f = sft.generate_science_features(times, values, errors, ['percent_difference_flux_percentile'])
    band_offset = 13.72
    w_m2 = 10**(-0.4*(values+band_offset)-3)  # 1 erg/s/cm^2 = 10^-3 w/m^2
    npt.assert_allclose(f['percent_difference_flux_percentile'], np.diff(
        np.percentile(w_m2, [5, 95])) / np.median(w_m2))

    f = sft.generate_science_features(times, values, errors, ['flux_percentile_ratio_mid20'])
    npt.assert_allclose(f['flux_percentile_ratio_mid20'],
                            np.diff(np.percentile(w_m2, [40, 60])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    f = sft.generate_science_features(times, values, errors, ['flux_percentile_ratio_mid35'])
    npt.assert_allclose(f['flux_percentile_ratio_mid35'],
                            np.diff(np.percentile(w_m2, [32.5, 67.5])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    f = sft.generate_science_features(times, values, errors, ['flux_percentile_ratio_mid50'])
    npt.assert_allclose(f['flux_percentile_ratio_mid50'],
                            np.diff(np.percentile(w_m2, [25, 75])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    f = sft.generate_science_features(times, values, errors, ['flux_percentile_ratio_mid65'])
    npt.assert_allclose(f['flux_percentile_ratio_mid65'],
                            np.diff(np.percentile(w_m2, [17.5, 82.5])) /
                            np.diff(np.percentile(w_m2, [5, 95])))

    f = sft.generate_science_features(times, values, errors, ['flux_percentile_ratio_mid80'])
    npt.assert_allclose(f['flux_percentile_ratio_mid80'],
                            np.diff(np.percentile(w_m2, [10, 90])) /
                            np.diff(np.percentile(w_m2, [5, 95])))


# AR-IS features are currently ignored
"""
def test_ar_is():
    times = np.linspace(0, 500, 201)
    theta = 0.95
    sigma = 0.0
    values = theta ** (times/250.) + sigma*np.random.randn(len(times))
    errors = 1e-4*np.ones(len(times))

    f = sft.generate_science_features(times, values, errors, ['ar_is_theta'])
    npt.assert_allclose(f['ar_is_theta'], theta, atol=3e-2)

    f = sft.generate_science_features(times, values, errors, ['ar_is_sigma'])
    npt.assert_allclose(f['ar_is_sigma'], sigma, atol=1e-5)

# Hard-coded values from reference data set
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['ar_is_theta'])
    npt.assert_allclose(f['ar_is_theta'], 5.9608609865491405e-06, rtol=1e-3)
    f = sft.generate_science_features(times, values, errors, ['ar_is_sigma'])
    npt.assert_allclose(f['ar_is_sigma'], 1.6427095072108497, rtol=1e-3)
"""


# The smoothed model fit in lcmodel seems insanely oversmoothed; in general
# all these extractors are a complete mess, and are currently ignored
"""
def test_lcmodel():
    frequencies = np.hstack((1., np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [2,0,0,0]
    phase = 0.0
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)

    f = sft.generate_science_features(times, values, errors, ['lcmodel'])
    lc_feats = f['lcmodel']

    # Median is zero for this data, so crossing median = changing sign
    incr_median_crosses = sum((np.abs(np.diff(np.sign(values))) > 1) &
                             (np.diff(values) > 0))
    npt.assert_allclose(lc_feats['median_n_per_day'], (incr_median_crosses+1) /
                        (max(times)-min(times)))
"""


def test_lomb_scargle_regular_single_freq():
    """
    Test Lomb-Scargle model features on regularly-sampled periodic data with one
    frequency/multiple harmonics. Estimated parameters should be very accurate in
    this case.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)

    # Only test the first (true) frequency; the rest correspond to noise
    npt.assert_allclose(all_lomb['freq1_freq'], frequencies[0])

    # Hard-coded value from previous solution
    npt.assert_allclose(0.001996007984, all_lomb['freq1_lambda'], rtol=1e-7)

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(amplitude,
                all_lomb['freq{}_amplitude{}'.format(i+1,j+1)], rtol=1e-2,
                    atol=1e-2)

    # Only test the first (true) frequency; the rest correspond to noise
    for j in range(1, amplitudes.shape[1]):
        npt.assert_allclose(phase*j*(-1**j),
            all_lomb['freq1_rel_phase{}'.format(j+1)], rtol=1e-2, atol=1e-2)

    # Frequency ratio not relevant since there is only; only test amplitude/signif
    for i in [2,3]:
        npt.assert_allclose(0., all_lomb['freq_amplitude_ratio_{}1'.format(i)], atol=1e-3)

    npt.assert_array_less(10., all_lomb['freq1_signif'])

    # Only one frequency, so this should explain basically all the variance
    npt.assert_allclose(0., all_lomb['freq_varrat'], atol=5e-3)

    # Exactly periodic, so the same minima/maxima should reoccur
    npt.assert_allclose(0., all_lomb['freq_model_max_delta_mags'], atol=1e-6)
    npt.assert_allclose(0., all_lomb['freq_model_min_delta_mags'], atol=1e-6)

    # Linear trend should be zero since the signal is exactly sinusoidal
    npt.assert_allclose(0., all_lomb['linear_trend'], atol=1e-4)

    folded_times = times % 1./(frequencies[0]/2.)
    sort_indices = np.argsort(folded_times)
    folded_times = folded_times[sort_indices]
    folded_values = values[sort_indices]

    # Residuals from doubling period should be much higher
    npt.assert_array_less(10., all_lomb['medperc90_2p_p'])

    # Slopes should be the same for {un,}folded data; use unfolded for stability
    slopes = np.diff(values) / np.diff(times)
    npt.assert_allclose(np.percentile(slopes,10),
        all_lomb['fold2P_slope_10percentile'], rtol=1e-2)
    npt.assert_allclose(np.percentile(slopes,90),
        all_lomb['fold2P_slope_90percentile'], rtol=1e-2)


def test_lomb_scargle_irregular_single_freq():
    """
    Test Lomb-Scargle model features on irregularly-sampled periodic data with one
    frequency/multiple harmonics. More difficult than regularly-sampled case, so
    we allow parameter estimates to be slightly noisy.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(WAVE_FREQS),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)

    # Only test the first (true) frequency; the rest correspond to noise
    npt.assert_allclose(all_lomb['freq1_freq'], frequencies[0], rtol=1e-2)

    # Only test first frequency here; noise gives non-zero amplitudes for residuals
    for j in range(amplitudes.shape[1]):
        npt.assert_allclose(amplitudes[0,j],
                all_lomb['freq1_amplitude{}'.format(j+1)], rtol=5e-2, atol=5e-2)
        if j >= 1:
            npt.assert_allclose(phase*j*(-1**j),
                all_lomb['freq1_rel_phase{}'.format(j+1)], rtol=1e-1, atol=1e-1)

    npt.assert_array_less(10., all_lomb['freq1_signif'])

    # Only one frequency, so this should explain basically all the variance
    npt.assert_allclose(0., all_lomb['freq_varrat'], atol=5e-3)

    npt.assert_allclose(-np.mean(values), all_lomb['freq_y_offset'], rtol=5e-2)


def test_lomb_scargle_period_folding():
    """
    Tests for features derived from fitting a Lomb-Scargle periodic model and
    period-folding the data by the estimated period.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(WAVE_FREQS),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)

    # Folding is numerically unstable so we need to use the exact fitted frequency
    freq_est = all_lomb['freq1_freq']
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

    npt.assert_allclose(np.sum(np.diff(fold2ed_values)**2) /
            np.sum(np.diff(values)**2), all_lomb['p2p_scatter_2praw'])
    npt.assert_allclose(np.sum(np.diff(values)**2) / ((len(values) - 1) *
        np.var(values)), all_lomb['p2p_ssqr_diff_over_var'])
    npt.assert_allclose(np.median(np.abs(np.diff(values))) /
            np.median(np.abs(values-np.median(values))),
            all_lomb['p2p_scatter_over_mad'])
    npt.assert_allclose(np.median(np.abs(np.diff(fold1ed_values))) /
                        np.median(np.abs(values-np.median(values))),
                        all_lomb['p2p_scatter_pfold_over_mad'])


def test_lomb_scargle_regular_multi_freq():
    """
    Test Lomb-Scargle model features on regularly-sampled periodic data with
    multiple frequencies, each with a single harmonic. Estimated parameters should
    be very accurate in this case.
    """
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[:,0] = [4,2,1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)

    for i, frequency in enumerate(frequencies):
        npt.assert_allclose(frequency,
                all_lomb['freq{}_freq'.format(i+1)])

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(amplitude,
                all_lomb['freq{}_amplitude{}'.format(i+1,j+1)],
                rtol=5e-2, atol=5e-2)

    for i in [2,3]:
        npt.assert_allclose(amplitudes[i-1,0] / amplitudes[0,0],
                all_lomb['freq_amplitude_ratio_{}1'.format(i)], atol=2e-2)

    npt.assert_array_less(10., all_lomb['freq1_signif'])


def test_lomb_scargle_irregular_multi_freq():
    """
    Test Lomb-Scargle model features on irregularly-sampled periodic data with
    multiple frequencies, each with a single harmonic. More difficult than
    regularly-sampled case, so we allow parameter estimates to be slightly noisy.
    """
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[:,0] = [4,2,1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)

    for i, frequency in enumerate(frequencies):
        npt.assert_allclose(frequency,
                all_lomb['freq{}_freq'.format(i+1)], rtol=1e-2)

    for (i,j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(amplitude,
                all_lomb['freq{}_amplitude{}'.format(i+1,j+1)],
                rtol=1e-1, atol=1e-1)

    for i in [2,3]:
        npt.assert_allclose(amplitudes[i-1,0] / amplitudes[0,0],
                all_lomb['freq_amplitude_ratio_{}1'.format(i)], atol=2e-2)
        npt.assert_allclose(frequencies[i-1] / frequencies[0],
                all_lomb['freq_frequency_ratio_{}1'.format(i)], atol=5e-2)

    npt.assert_array_less(10., all_lomb['freq1_signif'])


def test_lomb_scargle_linear_trend():
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(WAVE_FREQS),4))
    amplitudes[0,:] = [8,4,2,1]
    phase = 0.1
    slope = 0.5

    # Estimated trend should be almost exact for noiseless data
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    values += slope * times
    all_lomb = sft.generate_science_features(times, values, errors,
            lomb_features)
    npt.assert_allclose(slope, all_lomb['linear_trend'], rtol=1e-3)

    # Should still be close to true trend when noise is present
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    values += slope * times
    values += np.random.normal(scale=1e-3, size=len(times))
    all_lomb = sft.generate_science_features(times, values, errors,
                                             lomb_features)
    npt.assert_allclose(slope, all_lomb['linear_trend'], rtol=1e-1)


def test_lomb_scargle_fast_regular():
    """Test gatspy's fast Lomb-Scargle period estimate on regularly-sampled
    periodic data.

    Note: this model fits only a single sinusoid with no additional harmonics,
    so we use only 1 frequency and 1 amplitude to generate test data.
    """
    frequencies = np.array([4])
    amplitudes = np.array([[1]])
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    f = sft.generate_science_features(times, values, errors, ['period_fast'])

    npt.assert_allclose(f['period_fast'], 1. / frequencies[0], rtol=5e-4)


def test_lomb_scargle_fast_irregular():
    """Test gatspy's fast Lomb-Scargle period estimate on irregularly-sampled
    periodic data.

    Note: this model fits only a single sinusoid with no additional harmonics,
    so we use only 1 frequency and 1 amplitude to generate test data.
    """
    frequencies = np.array([4])
    amplitudes = np.array([[1]])
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    f = sft.generate_science_features(times, values, errors, ['period_fast'])

    npt.assert_allclose(f['period_fast'], 1. / frequencies[0], rtol=3e-2)


def test_max():
    """Test maximum value feature."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['maximum'])
    npt.assert_equal(f['maximum'], max(values))


def test_max_slope():
    """Test maximum slope feature, which finds the INDEX of the largest slope."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['max_slope'])
    slopes = np.diff(values) / np.diff(times)
    npt.assert_allclose(f['max_slope'], np.max(np.abs(slopes)))


def test_median_absolute_deviation():
    """Test median absolute deviation (from the median) feature."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['median_absolute_deviation'])
    npt.assert_allclose(f['median_absolute_deviation'], np.median(np.abs(values -
        np.median(values))))


def test_percent_close_to_median():
    """Test feature which finds the percentage of points near the median value."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors,
            ['percent_close_to_median'])
    amplitude = (max(values) - min(values)) / 2.
    within_buffer = np.abs(values - np.median(values)) < 0.2*amplitude
    npt.assert_allclose(f['percent_close_to_median'], np.mean(within_buffer))


def test_median():
    """Test median value feature."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['median'])
    npt.assert_allclose(f['median'], np.median(values))


def test_min():
    """Test minimum value feature."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['minimum'])
    npt.assert_equal(f['minimum'], min(values))


# These features are currently ignored
"""
def test_phase_dispersion():
# Frequency chosen to lie on the relevant search grid
    frequencies = np.hstack((5.36, np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [1,0,0,0]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    f = sft.generate_science_features(times, values, errors, ['phase_dispersion_freq0'])
    npt.assert_allclose(f['phase_dispersion_freq0'], frequencies[0])

    f = sft.generate_science_features(times, values, errors, ['freq1_freq'])
    lomb_freq = f['freq1_freq']
    f = sft.generate_science_features(times, values, errors, ['ratio_PDM_LS_freq0'])
    npt.assert_allclose(f['ratio_PDM_LS_freq0'], frequencies[0]/lomb_freq)
"""


def test_qso_features():
    """
    Test features which measure fit of QSO model.

    Reference values are hard-coded values from previous implementation; not sure
    of examples with a closed-form solution.
    """
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors,
            ['qso_log_chi2_qsonu', 'qso_log_chi2nuNULL_chi2nu'])
    npt.assert_allclose(f['qso_log_chi2_qsonu'], 6.9844064754)
    npt.assert_allclose(f['qso_log_chi2nuNULL_chi2nu'], -0.456526327522)


def test_scatter_res_raw():
    """Test feature that measures scatter of Lomb-Scargle residuals."""
    times, values, errors = irregular_random()
    lomb_model = sft.sf.lomb_scargle_model(times, values, errors)
    residuals = values - lomb_model['freq_fits'][0]['model']
    resid_mad = np.median(np.abs(residuals - np.median(residuals)))
    value_mad = np.median(np.abs(values - np.median(values)))
    f = sft.generate_science_features(times, values, errors, ['scatter_res_raw'])
    npt.assert_allclose(f['scatter_res_raw'], resid_mad / value_mad, atol=3e-2)


def test_skew():
    """Test statistical skew feature."""
    from scipy import stats
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['skew'])
    npt.assert_allclose(f['skew'], stats.skew(values))


def test_std():
    """Test standard deviation feature."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['std'])
    npt.assert_allclose(f['std'], np.std(values))


def test_stetson():
    """Test Stetson variability features."""
    times, values, errors = irregular_random(size=201)
    f = sft.generate_science_features(times, values, errors, ['stetson_j'])
    # Stetson mean approximately equal to standard mean for large inputs
    dists = np.sqrt(float(len(values)) / (len(values) - 1.)) * (values - np.mean(values)) / 0.1
    npt.assert_allclose(f['stetson_j'],
                        np.mean(np.sign(dists**2-1)*np.sqrt(np.abs(dists**2-1))),
                        rtol=1e-2)
    # Stetson_j should be somewhat close to (scaled) variance for normal data
    npt.assert_allclose(f['stetson_j']*0.1, np.var(values), rtol=2e-1)
    # Hard-coded original value
    npt.assert_allclose(f['stetson_j'], 7.591347175195703)

    f = sft.generate_science_features(times, values, errors, ['stetson_k'])
    npt.assert_allclose(f['stetson_k'], 1./0.798 * np.mean(np.abs(dists)) / np.sqrt(np.mean(dists**2)), rtol=5e-4)
    # Hard-coded original value
    npt.assert_allclose(f['stetson_k'], 1.0087218792719013)


def test_weighted_average():
    """Test weighted average and distance from weighted average features."""
    times, values, errors = irregular_random()
    f = sft.generate_science_features(times, values, errors, ['weighted_average'])
    weighted_avg = np.average(values, weights=1. / (errors**2))
    weighted_var = np.average((values - weighted_avg)**2,
                              weights=1. / (errors**2))
    npt.assert_allclose(f['weighted_average'], weighted_avg)

    dists_from_weighted_avg = values - weighted_avg
    stds_from_weighted_avg = (dists_from_weighted_avg /
            np.sqrt(weighted_var))

    f = sft.generate_science_features(times, values, errors,
                                      ['percent_beyond_1_std'])
    npt.assert_equal(f['percent_beyond_1_std'], np.mean(stds_from_weighted_avg > 1.))
