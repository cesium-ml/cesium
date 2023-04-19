import itertools
import numpy as np
import numpy.testing as npt
from scipy import stats

from cesium.features import cadence_features as cf
from cesium.features.tests.util import (
    generate_features,
    irregular_random,
)


def test_delta_t_hist():
    """Test histogram of all time lags."""
    times, values, errors = irregular_random(500)
    delta_ts = [pair[1] - pair[0] for pair in itertools.combinations(times, 2)]
    nbins = 50
    bins = np.linspace(0, max(times) - min(times), nbins + 1)
    npt.assert_allclose(
        cf.delta_t_hist(times, nbins), np.histogram(delta_ts, bins=bins)[0], atol=2
    )


def test_normalize_hist():
    """Test normalization of histogram."""
    times, values, errors = irregular_random(500)
    delta_ts = [pair[1] - pair[0] for pair in itertools.combinations(times, 2)]
    nbins = 50
    bins = np.linspace(0, max(times) - min(times), nbins + 1)
    nhist = cf.normalize_hist(cf.delta_t_hist(times, nbins), max(times) - min(times))
    npt.assert_allclose(
        nhist, np.histogram(delta_ts, bins=bins, density=True)[0], atol=0.01
    )


def test_find_sorted_peaks():
    """Test peak-finding algorithm."""
    x = np.array([0, 5, 3, 1])  # Single peak
    npt.assert_allclose(cf.find_sorted_peaks(x), np.array([[1, 5]]))

    x = np.array([0, 5, 3, 6, 1])  # Multiple peaks
    npt.assert_allclose(cf.find_sorted_peaks(x), np.array([[3, 6], [1, 5]]))

    x = np.array([3, 1, 3])  # End-points can be peaks
    npt.assert_allclose(cf.find_sorted_peaks(x), np.array([[0, 3], [2, 3]]))

    x = np.array([0, 3, 3, 3, 0])  # In case of ties, peak is left-most point
    npt.assert_allclose(cf.find_sorted_peaks(x), np.array([[1, 3]]))

    # Tie is a peak only if greater than next value
    x = np.array([0, 3, 3, 5, 0])
    npt.assert_allclose(cf.find_sorted_peaks(x), np.array([[3, 5]]))


def test_peak_ratio():
    """Test peak ratio method."""
    x = np.array([0, 5, 2, 3, 1])
    peaks1 = cf.find_sorted_peaks(x)
    npt.assert_almost_equal(cf.peak_ratio(peaks1, 0, 1), 5 / 3)
    assert cf.peak_ratio(peaks1, 1, 6) is np.nan
    peaks2 = []
    assert cf.peak_ratio(peaks2, 1, 2) is np.nan


def test_peak_bins():
    """Test peak bins method"""
    x = np.array([0, 5, 2, 3, 1])
    peaks1 = cf.find_sorted_peaks(x)
    npt.assert_almost_equal(cf.peak_bin(peaks1, 0), 1)
    npt.assert_almost_equal(cf.peak_bin(peaks1, 1), 3)
    assert cf.peak_bin(peaks1, 6) is np.nan


def test_compute_time_lag_stats():
    """Test compute_time_lag_stats function."""
    times, values, errors = irregular_random(500)
    cads = np.diff(times)

    f = generate_features(
        times, values, errors, ["cads_avg", "cads_std", "cads_skew", "cads_kurtosis"]
    )
    npt.assert_almost_equal(f["cads_avg"], np.mean(cads))
    npt.assert_almost_equal(f["cads_std"], np.std(cads))
    npt.assert_almost_equal(f["cads_skew"], stats.skew(cads))
    npt.assert_almost_equal(f["cads_kurtosis"], stats.kurtosis(cads))
