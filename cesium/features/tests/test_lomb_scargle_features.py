import numpy as np
import numpy.testing as npt

from cesium.features import lomb_scargle
from cesium.features.graphs import LOMB_SCARGLE_FEATS
from cesium.features.tests.util import (
    generate_features,
    irregular_random,
    regular_periodic,
    irregular_periodic,
)


# These values are chosen because they lie exactly on the grid of frequencies
# searched by the Lomb Scargle optimization procedure
WAVE_FREQS = np.array([5.3, 3.3, 2.1])


def test_lomb_scargle_freq_grid():
    """Test Lomb-Scargle model frequency grid calculation"""
    f0 = 0.5
    fmax = 10
    numf = 100
    df = 0.8
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS) - 1)))
    amplitudes = np.zeros((len(frequencies), 4))
    amplitudes[0, :] = [8, 4, 2, 1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    model = lomb_scargle.lomb_scargle_model(
        times,
        values,
        errors,
        nharm=8,
        nfreq=1,
        freq_grid={"f0": f0, "fmax": fmax, "numf": numf},
    )

    assert model["numf"] == numf
    # check that the spacing is correct
    npt.assert_allclose(
        model["freq_fits"][0]["freqs_vector"][1]
        - model["freq_fits"][0]["freqs_vector"][0],
        model["df"],
    )
    freqs = np.linspace(f0, fmax, numf)
    npt.assert_allclose(freqs[1] - freqs[0], model["df"])

    model = lomb_scargle.lomb_scargle_model(
        times,
        values,
        errors,
        nharm=8,
        nfreq=1,
        freq_grid={"f0": f0, "fmax": fmax, "df": df},
    )
    assert model["numf"] == int((fmax - f0) / df) + 1

    # check the autogeneration of the frequency grid
    model = lomb_scargle.lomb_scargle_model(
        times, values, errors, nharm=8, nfreq=1, freq_grid=None
    )
    npt.assert_allclose(model["f0"], 1.0 / (max(times) - min(times)))


def test_lomb_scargle_regular_single_freq():
    """Test Lomb-Scargle model features on regularly-sampled periodic data with
    one frequency/multiple harmonics. Estimated parameters should be very
    accurate in this case.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS) - 1)))
    amplitudes = np.zeros((len(frequencies), 4))
    amplitudes[0, :] = [8, 4, 2, 1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)

    # Only test the first (true) frequency; the rest correspond to noise
    npt.assert_allclose(all_lomb["freq1_freq"], frequencies[0])

    # Hard-coded value from previous solution
    npt.assert_allclose(0.001996007984, all_lomb["freq1_lambda"], rtol=1e-7)

    for (i, j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(
            amplitude,
            all_lomb[f"freq{i + 1}_amplitude{j + 1}"],
            rtol=1e-2,
            atol=1e-2,
        )

    # Only test the first (true) frequency; the rest correspond to noise
    for j in range(1, amplitudes.shape[1]):
        npt.assert_allclose(
            phase * j * (-(1**j)),
            all_lomb[f"freq1_rel_phase{j + 1}"],
            rtol=1e-2,
            atol=1e-2,
        )

    # Frequency ratio not relevant since there is only; only test amplitude/signif
    for i in [2, 3]:
        npt.assert_allclose(0.0, all_lomb[f"freq_amplitude_ratio_{i}1"], atol=1e-3)

    npt.assert_array_less(10.0, all_lomb["freq1_signif"])

    # Only one frequency, so this should explain basically all the variance
    npt.assert_allclose(0.0, all_lomb["freq_varrat"], atol=5e-3)

    # Exactly periodic, so the same minima/maxima should reoccur
    npt.assert_allclose(0.0, all_lomb["freq_model_max_delta_mags"], atol=1e-6)
    npt.assert_allclose(0.0, all_lomb["freq_model_min_delta_mags"], atol=1e-6)

    # Linear trend should be zero since the signal is exactly sinusoidal
    npt.assert_allclose(0.0, all_lomb["linear_trend"], atol=1e-4)

    folded_times = times % 1.0 / (frequencies[0] / 2.0)
    sort_indices = np.argsort(folded_times)
    folded_times = folded_times[sort_indices]

    # Residuals from doubling period should be much higher
    npt.assert_array_less(10.0, all_lomb["medperc90_2p_p"])

    # Slopes should be the same for {un,}folded data; use unfolded for stability
    slopes = np.diff(values) / np.diff(times)
    npt.assert_allclose(
        np.percentile(slopes, 10), all_lomb["fold2P_slope_10percentile"], rtol=1e-2
    )
    npt.assert_allclose(
        np.percentile(slopes, 90), all_lomb["fold2P_slope_90percentile"], rtol=1e-2
    )


def test_lomb_scargle_irregular_single_freq():
    """Test Lomb-Scargle model features on irregularly-sampled periodic data
    with one frequency/multiple harmonics. More difficult than
    regularly-sampled case, so we allow parameter estimates to be slightly
    noisy.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS) - 1)))
    amplitudes = np.zeros((len(WAVE_FREQS), 4))
    amplitudes[0, :] = [8, 4, 2, 1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)

    # Only test the first (true) frequency; the rest correspond to noise
    npt.assert_allclose(all_lomb["freq1_freq"], frequencies[0], rtol=1e-2)

    # Only test first frequency here; noise gives non-zero amplitudes for residuals
    for j in range(amplitudes.shape[1]):
        npt.assert_allclose(
            amplitudes[0, j],
            all_lomb[f"freq1_amplitude{j + 1}"],
            rtol=5e-2,
            atol=5e-2,
        )
        if j >= 1:
            npt.assert_allclose(
                phase * j * (-(1**j)),
                all_lomb[f"freq1_rel_phase{j + 1}"],
                rtol=1e-1,
                atol=1e-1,
            )

    npt.assert_array_less(10.0, all_lomb["freq1_signif"])

    # Only one frequency, so this should explain basically all the variance
    npt.assert_allclose(0.0, all_lomb["freq_varrat"], atol=5e-3)

    npt.assert_allclose(-np.mean(values), all_lomb["freq_y_offset"], rtol=5e-2)


def test_lomb_scargle_period_folding():
    """Tests for features derived from fitting a Lomb-Scargle periodic model
    and period-folding the data by the estimated period.
    """
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS) - 1)))
    amplitudes = np.zeros((len(WAVE_FREQS), 4))
    amplitudes[0, :] = [8, 4, 2, 1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)

    # Folding is numerically unstable so we need to use the exact fitted frequency
    freq_est = all_lomb["freq1_freq"]
    # Fold by 1*period
    fold1ed_times = (times - times[0]) % (1.0 / freq_est)
    sort_indices = np.argsort(fold1ed_times)
    fold1ed_times = fold1ed_times[sort_indices]
    fold1ed_values = values[sort_indices]
    # Fold by 2*period
    fold2ed_times = (times - times[0]) % (2.0 / freq_est)
    sort_indices = np.argsort(fold2ed_times)
    fold2ed_times = fold2ed_times[sort_indices]
    fold2ed_values = values[sort_indices]

    npt.assert_allclose(
        np.sum(np.diff(fold2ed_values) ** 2) / np.sum(np.diff(values) ** 2),
        all_lomb["p2p_scatter_2praw"],
    )
    npt.assert_allclose(
        np.sum(np.diff(values) ** 2) / ((len(values) - 1) * np.var(values)),
        all_lomb["p2p_ssqr_diff_over_var"],
    )
    npt.assert_allclose(
        np.median(np.abs(np.diff(values)))
        / np.median(np.abs(values - np.median(values))),
        all_lomb["p2p_scatter_over_mad"],
    )
    npt.assert_allclose(
        np.median(np.abs(np.diff(fold1ed_values)))
        / np.median(np.abs(values - np.median(values))),
        all_lomb["p2p_scatter_pfold_over_mad"],
    )


def test_lomb_scargle_regular_multi_freq():
    """Test Lomb-Scargle model features on regularly-sampled periodic data with
    multiple frequencies, each with a single harmonic. Estimated parameters
    should be very accurate in this case.
    """
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies), 4))
    amplitudes[:, 0] = [4, 2, 1]
    phase = 0.1
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)

    for i, frequency in enumerate(frequencies):
        npt.assert_allclose(frequency, all_lomb[f"freq{i + 1}_freq"])

    for (i, j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(
            amplitude,
            all_lomb[f"freq{i + 1}_amplitude{j + 1}"],
            rtol=5e-2,
            atol=5e-2,
        )

    for i in [2, 3]:
        npt.assert_allclose(
            amplitudes[i - 1, 0] / amplitudes[0, 0],
            all_lomb[f"freq_amplitude_ratio_{i}1"],
            atol=2e-2,
        )

    npt.assert_array_less(10.0, all_lomb["freq1_signif"])


def test_lomb_scargle_irregular_multi_freq_normalize():
    """Use the normalize parameter on irregularly sampled data
    and make sure that we still get back the frequencies that
    we expect.
    """
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies), 4))
    amplitudes[:, 0] = [4, 2, 1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)

    sys_err = 0.15
    nfreq = len(frequencies)
    tone_control = 20.0
    for nharm in range(1, 21):
        model_cesium = lomb_scargle.lomb_scargle_model(
            times - min(times),
            values,
            errors,
            sys_err=sys_err,
            nharm=nharm,
            nfreq=nfreq,
            tone_control=tone_control,
            normalize=True,
        )
        for i, frequency in enumerate(frequencies):
            npt.assert_allclose(
                frequency, model_cesium["freq_fits"][i]["freq"], rtol=1e-1
            )
            # check to see if the power spectrum is returned
            assert len(model_cesium["freq_fits"][i]["freqs_vector"]) == len(
                model_cesium["freq_fits"][i]["psd_vector"]
            )


def test_lomb_scargle_irregular_multi_freq():
    """Test Lomb-Scargle model features on irregularly-sampled periodic data
    with multiple frequencies, each with a single harmonic. More difficult than
    regularly-sampled case, so we allow parameter estimates to be slightly
    noisy.
    """
    frequencies = WAVE_FREQS
    amplitudes = np.zeros((len(frequencies), 4))
    amplitudes[:, 0] = [4, 2, 1]
    phase = 0.1
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)

    for i, frequency in enumerate(frequencies):
        npt.assert_allclose(frequency, all_lomb[f"freq{i + 1}_freq"], rtol=1e-2)

    for (i, j), amplitude in np.ndenumerate(amplitudes):
        npt.assert_allclose(
            amplitude,
            all_lomb[f"freq{i + 1}_amplitude{j + 1}"],
            rtol=1e-1,
            atol=1e-1,
        )

    for i in [2, 3]:
        npt.assert_allclose(
            amplitudes[i - 1, 0] / amplitudes[0, 0],
            all_lomb[f"freq_amplitude_ratio_{i}1"],
            atol=2e-2,
        )
        npt.assert_allclose(
            frequencies[i - 1] / frequencies[0],
            all_lomb[f"freq_frequency_ratio_{i}1"],
            atol=5e-2,
        )

    npt.assert_array_less(10.0, all_lomb["freq1_signif"])


def test_lomb_scargle_linear_trend():
    frequencies = np.hstack((WAVE_FREQS[0], np.zeros(len(WAVE_FREQS) - 1)))
    amplitudes = np.zeros((len(WAVE_FREQS), 4))
    amplitudes[0, :] = [8, 4, 2, 1]
    phase = 0.1
    slope = 0.5

    # Estimated trend should be almost exact for noiseless data
    times, values, errors = regular_periodic(frequencies, amplitudes, phase)
    values += slope * times
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)
    npt.assert_allclose(slope, all_lomb["linear_trend"], rtol=1e-3)

    # Should still be close to true trend when noise is present
    times, values, errors = irregular_periodic(frequencies, amplitudes, phase)
    values += slope * times
    values += np.random.normal(scale=1e-3, size=len(times))
    all_lomb = generate_features(times, values, errors, LOMB_SCARGLE_FEATS)
    npt.assert_allclose(slope, all_lomb["linear_trend"], rtol=1e-1)


def test_scatter_res_raw():
    """Test feature that measures scatter of Lomb-Scargle residuals."""
    times, values, errors = irregular_random()
    lomb_model = lomb_scargle.lomb_scargle_model(times, values, errors)
    residuals = values - lomb_model["freq_fits"][0]["model"]
    resid_mad = np.median(np.abs(residuals - np.median(residuals)))
    value_mad = np.median(np.abs(values - np.median(values)))
    f = generate_features(times, values, errors, ["scatter_res_raw"])
    npt.assert_allclose(f["scatter_res_raw"], resid_mad / value_mad, atol=3e-2)
