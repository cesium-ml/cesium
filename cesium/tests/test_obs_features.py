from cesium import obs_feature_tools as oft
import itertools

import numpy as np
import numpy.testing as npt


def irregular_random(seed=0, size=50):
    """Generate random test data at irregularly-sampled times."""
    state = np.random.RandomState(seed)
    times = np.sort(state.uniform(0, 10, size))
    values = state.normal(1, 1, size)
    errors = state.exponential(0.1, size)
    return times, values, errors


def test_delta_t_hist():
    """Test histogram of all time lags."""
    times, values, errors = irregular_random()
    delta_ts = [pair[1] - pair[0] for pair in itertools.combinations(times, 2)]
    nbins = 50
    bins = np.linspace(0, max(times) - min(times), nbins+1)
    npt.assert_allclose(oft.delta_t_hist(times, nbins), np.histogram(delta_ts,
        bins=bins)[0])


def test_normalize_hist():
    """Test normalization of histogram."""
    times, values, errors = irregular_random()
    delta_ts = [pair[1] - pair[0] for pair in itertools.combinations(times, 2)]
    nbins = 50
    bins = np.linspace(0, max(times) - min(times), nbins+1)
    nhist = oft.normalize_hist(oft.delta_t_hist(times, nbins), max(times) -
                               min(times))
    npt.assert_allclose(nhist, np.histogram(delta_ts,
        bins=bins, density=True)[0])


def test_find_sorted_peaks():
    """Test peak-finding algorithm."""
    x = np.array([0,5,3,1]) # Single peak
    npt.assert_allclose(oft.find_sorted_peaks(x), np.array([[1,5]]))

    x = np.array([0,5,3,6,1]) # Multiple peaks
    npt.assert_allclose(oft.find_sorted_peaks(x), np.array([[3,6],[1,5]]))

    x = np.array([3,1,3]) # End-points can be peaks
    npt.assert_allclose(oft.find_sorted_peaks(x), np.array([[0,3],[2,3]]))

    x = np.array([0,3,3,3,0]) # In case of ties, peak is left-most point
    npt.assert_allclose(oft.find_sorted_peaks(x), np.array([[1,3]]))

    x = np.array([0,3,3,5,0]) # Tie is a peak only if greater than next value
    npt.assert_allclose(oft.find_sorted_peaks(x), np.array([[3,5]]))
