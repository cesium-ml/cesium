import numpy as np
import numpy.testing as npt


from cesium.features.tests.util import (
    generate_features,
    irregular_random,
    regular_periodic,
    irregular_periodic,
)


def test_anderson_darling():
    """Test Anderson-Darling feature."""
    from scipy.stats import anderson

    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["anderson_darling"])
    npt.assert_allclose(f["anderson_darling"], anderson(values / errors)[0])


def test_amplitude():
    """Test features related to amplitude/magnitude percentiles."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["amplitude"])
    npt.assert_allclose(f["amplitude"], (max(values) - min(values)) / 2.0)

    f = generate_features(times, values, errors, ["percent_amplitude"])
    max_scaled = 10 ** (-0.4 * max(values))
    min_scaled = 10 ** (-0.4 * min(values))
    med_scaled = 10 ** (-0.4 * np.median(values))
    peak_from_median = max(
        abs((max_scaled - med_scaled) / med_scaled),
        abs(min_scaled - med_scaled) / med_scaled,
    )
    npt.assert_allclose(f["percent_amplitude"], peak_from_median, rtol=5e-4)

    f = generate_features(times, values, errors, ["percent_difference_flux_percentile"])
    band_offset = 13.72
    w_m2 = 10 ** (-0.4 * (values + band_offset) - 3)  # 1 erg/s/cm^2 = 10^-3 w/m^2
    npt.assert_allclose(
        f["percent_difference_flux_percentile"],
        np.diff(np.percentile(w_m2, [5, 95])) / np.median(w_m2),
    )

    f = generate_features(times, values, errors, ["flux_percentile_ratio_mid20"])
    npt.assert_allclose(
        f["flux_percentile_ratio_mid20"],
        np.diff(np.percentile(w_m2, [40, 60])) / np.diff(np.percentile(w_m2, [5, 95])),
    )

    f = generate_features(times, values, errors, ["flux_percentile_ratio_mid35"])
    npt.assert_allclose(
        f["flux_percentile_ratio_mid35"],
        np.diff(np.percentile(w_m2, [32.5, 67.5]))
        / np.diff(np.percentile(w_m2, [5, 95])),
    )

    f = generate_features(times, values, errors, ["flux_percentile_ratio_mid50"])
    npt.assert_allclose(
        f["flux_percentile_ratio_mid50"],
        np.diff(np.percentile(w_m2, [25, 75])) / np.diff(np.percentile(w_m2, [5, 95])),
    )

    f = generate_features(times, values, errors, ["flux_percentile_ratio_mid65"])
    npt.assert_allclose(
        f["flux_percentile_ratio_mid65"],
        np.diff(np.percentile(w_m2, [17.5, 82.5]))
        / np.diff(np.percentile(w_m2, [5, 95])),
    )

    f = generate_features(times, values, errors, ["flux_percentile_ratio_mid80"])
    npt.assert_allclose(
        f["flux_percentile_ratio_mid80"],
        np.diff(np.percentile(w_m2, [10, 90])) / np.diff(np.percentile(w_m2, [5, 95])),
    )


# AR-IS features are currently ignored
"""
def test_ar_is():
    times = np.linspace(0, 500, 201)
    theta = 0.95
    sigma = 0.0
    values = theta ** (times/250.) + sigma*np.random.randn(len(times))
    errors = 1e-4*np.ones(len(times))

    f = generate_features(times, values, errors, ['ar_is_theta'])
    npt.assert_allclose(f['ar_is_theta'], theta, atol=3e-2)

    f = generate_features(times, values, errors, ['ar_is_sigma'])
    npt.assert_allclose(f['ar_is_sigma'], sigma, atol=1e-5)

# Hard-coded values from reference data set
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ['ar_is_theta'])
    npt.assert_allclose(f['ar_is_theta'], 5.9608609865491405e-06, rtol=1e-3)
    f = generate_features(times, values, errors, ['ar_is_sigma'])
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

    f = generate_features(times, values, errors, ['lcmodel'])
    lc_feats = f['lcmodel']

    # Median is zero for this data, so crossing median = changing sign
    incr_median_crosses = sum((np.abs(np.diff(np.sign(values))) > 1) &
                             (np.diff(values) > 0))
    npt.assert_allclose(lc_feats['median_n_per_day'], (incr_median_crosses+1) /
                        (max(times)-min(times)))
"""


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
    f = generate_features(times, values, errors, ["period_fast"])

    npt.assert_allclose(f["period_fast"], 1.0 / frequencies[0], rtol=5e-4)


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
    f = generate_features(times, values, errors, ["period_fast"])

    npt.assert_allclose(f["period_fast"], 1.0 / frequencies[0], rtol=3e-2)


def test_max():
    """Test maximum value feature."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["maximum"])
    npt.assert_equal(f["maximum"], max(values))


def test_max_slope():
    """Test maximum slope feature, which finds the INDEX of the largest slope."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["max_slope"])
    slopes = np.diff(values) / np.diff(times)
    npt.assert_allclose(f["max_slope"], np.max(np.abs(slopes)))


def test_median_absolute_deviation():
    """Test median absolute deviation (from the median) feature."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["median_absolute_deviation"])
    npt.assert_allclose(
        f["median_absolute_deviation"], np.median(np.abs(values - np.median(values)))
    )


def test_percent_close_to_median():
    """Test feature which finds the percentage of points near the median value."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["percent_close_to_median"])
    amplitude = (max(values) - min(values)) / 2.0
    within_buffer = np.abs(values - np.median(values)) < 0.2 * amplitude
    npt.assert_allclose(f["percent_close_to_median"], np.mean(within_buffer))


def test_median():
    """Test median value feature."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["median"])
    npt.assert_allclose(f["median"], np.median(values))


def test_min():
    """Test minimum value feature."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["minimum"])
    npt.assert_equal(f["minimum"], min(values))


# These features are currently ignored
"""
def test_phase_dispersion():
# Frequency chosen to lie on the relevant search grid
    frequencies = np.hstack((5.36, np.zeros(len(WAVE_FREQS)-1)))
    amplitudes = np.zeros((len(frequencies),4))
    amplitudes[0,:] = [1,0,0,0]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    f = generate_features(times, values, errors, ['phase_dispersion_freq0'])
    npt.assert_allclose(f['phase_dispersion_freq0'], frequencies[0])

    f = generate_features(times, values, errors, ['freq1_freq'])
    lomb_freq = f['freq1_freq']
    f = generate_features(times, values, errors, ['ratio_PDM_LS_freq0'])
    npt.assert_allclose(f['ratio_PDM_LS_freq0'], frequencies[0]/lomb_freq)
"""


def test_qso_features():
    """Test features which measure fit of QSO model.

    Reference values are hard-coded values from previous implementation; not sure
    of examples with a closed-form solution.
    """
    times, values, errors = irregular_random()
    f = generate_features(
        times, values, errors, ["qso_log_chi2_qsonu", "qso_log_chi2nuNULL_chi2nu"]
    )
    npt.assert_allclose(f["qso_log_chi2_qsonu"], 6.9844064754)
    npt.assert_allclose(f["qso_log_chi2nuNULL_chi2nu"], -0.456526327522)


def test_skew():
    """Test statistical skew feature."""
    from scipy import stats

    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["skew"])
    npt.assert_allclose(f["skew"], stats.skew(values))


def test_std():
    """Test standard deviation feature."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["std"])
    npt.assert_allclose(f["std"], np.std(values))


def test_shapiro_wilk():
    """Test Shapiro-Wilk feature."""
    from scipy.stats import shapiro

    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["shapiro_wilk"])
    npt.assert_allclose(f["shapiro_wilk"], shapiro(values / errors)[0])


def test_stetson():
    """Test Stetson variability features."""
    times, values, errors = irregular_random(size=201)
    f = generate_features(times, values, errors, ["stetson_j"])
    # Stetson mean approximately equal to standard mean for large inputs
    dists = (
        np.sqrt(float(len(values)) / (len(values) - 1.0))
        * (values - np.mean(values))
        / 0.1
    )
    npt.assert_allclose(
        f["stetson_j"],
        np.mean(np.sign(dists**2 - 1) * np.sqrt(np.abs(dists**2 - 1))),
        rtol=1e-2,
    )
    # Stetson_j should be somewhat close to (scaled) variance for normal data
    npt.assert_allclose(f["stetson_j"] * 0.1, np.var(values), rtol=2e-1)
    # Hard-coded original value
    npt.assert_allclose(f["stetson_j"], 7.591347175195703)

    f = generate_features(times, values, errors, ["stetson_k"])
    npt.assert_allclose(
        f["stetson_k"],
        1.0 / 0.798 * np.mean(np.abs(dists)) / np.sqrt(np.mean(dists**2)),
        rtol=5e-4,
    )
    # Hard-coded original value
    npt.assert_allclose(f["stetson_k"], 1.0087218792719013)


def test_weighted_average():
    """Test weighted average and distance from weighted average features."""
    times, values, errors = irregular_random()
    f = generate_features(times, values, errors, ["weighted_average"])
    weighted_avg = np.average(values, weights=1.0 / (errors**2))
    weighted_var = np.average((values - weighted_avg) ** 2, weights=1.0 / (errors**2))
    npt.assert_allclose(f["weighted_average"], weighted_avg)

    dists_from_weighted_avg = values - weighted_avg
    stds_from_weighted_avg = dists_from_weighted_avg / np.sqrt(weighted_var)

    f = generate_features(times, values, errors, ["percent_beyond_1_std"])
    npt.assert_equal(
        f["percent_beyond_1_std"], np.mean(np.abs(stds_from_weighted_avg) > 1.0)
    )


def test_weighted_std_dev():
    """Test weighted std dev."""
    times, values, errors = irregular_random()
    f = generate_features(
        times, values, errors, ["weighted_average", "weighted_std_dev"]
    )
    weighted_std_dev = np.sqrt(
        np.average((values - f["weighted_average"]) ** 2, weights=1.0 / (errors**2))
    )
    npt.assert_allclose(f["weighted_std_dev"], weighted_std_dev)
