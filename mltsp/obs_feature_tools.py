import numpy as np
import dask.async
import scipy.stats as stats


__all__ = ['FEATURES_LIST', 'double_to_single_step', 'cad_prob',
           'delta_t_hist', 'normalize_hist', 'find_sorted_peaks', 'peak_ratio',
           'peak_bin', 'generate_obs_features']


FEATURES_LIST = [
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


def double_to_single_step(cads):
    """Ratios t[i+2] - t[i] / (t[i+2] - t[i+1])."""
    return (cads[1:] + cads[:-1]) / cads[1:]


def cad_prob(cads, time):
    """Given the observed distribution of time lags `cads`, compute the probability
    that the next observation occurs within `time` minutes of an arbitrary epoch.
    """
    return stats.percentileofscore(cads, float(time) / (24.0 * 60.0)) / 100.0

 
def delta_t_hist(t, nbins=50):
    """Build histogram of all possible delta_t's without storing every value"""
    hist = np.zeros(nbins, dtype='int')
    bins = np.linspace(0, max(t) - min(t), nbins+1)
    for i in range(len(t)):
        hist += np.histogram(t[i] - t[:i], bins=bins)[0]
        hist += np.histogram(t[i+1:] - t[i], bins=bins)[0]
    return hist / 2 # Double-counts since we loop over every pair twice


def normalize_hist(hist, total_time):
    """Normalize histogram such that integral from t_min to t_max equals 1.
    cf. np.histogram(..., density=True).
    """
    return hist / (total_time * np.mean(hist))


def find_sorted_peaks(x):
    """Find peaks, i.e. local maxima, of an array. Interior points are peaks if
    they are greater than both their neighbors, and edge points are peaks if
    they are greater than their only neighbor. In the case of ties, we
    (arbitrarily) choose the first index in the sequence of equal values as the
    peak.

    Returns a list of tuples (i, x[i]) of peak indices i and values x[i],
    sorted in decreasing order by peak value.
     """
    peak_inds = []
    nbins = len(x)
    for i in range(nbins):
        if i == 0 or x[i] > x[i-1]: # Increasing from left
            if i == nbins-1 or x[i] > x[i+1]: # Increasing from right
                peak_inds.append(i)
            elif x[i] == x[i+1]: # Tied; check the next non-equal value
                for j in range(i+1, nbins):
                    if x[j] != x[i]:
                        if x[j] < x[i]:
                            peak_inds.append(i)
                        break
                if j == nbins-1 and x[i] == x[j]: # Reached the end
                    peak_inds.append(i)
    sorted_peak_inds = sorted(peak_inds, key=lambda i: x[i], reverse=True)
    return list(zip(sorted_peak_inds, x[sorted_peak_inds]))


def peak_ratio(peaks, i, j):
    """Compute the ratio of the values of the ith and jth largest peaks."""
    if len(peaks) > i and len(peaks) > j:
        return peaks[i][1] / peaks[j][1]
    else:
        return None


def peak_bin(peaks, i):
    """Return the (bin) index of the ith largest peak."""
    if len(peaks) > i:
        return peaks[i][0]
    else:
        return None


def generate_obs_features(t, m, e, features_to_compute=FEATURES_LIST):
    """Generate features dict from given time-series data.

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
        Dictionary containing generated time series features.
    """
    features_to_compute = [f for f in features_to_compute
                           if f in FEATURES_LIST]
    feature_graph = {
        'n_epochs': (len, t),
        'avg_err': (np.mean, e),
        'med_err': (np.median, e),
        'std_err': (np.std, e),
        'total_time': (lambda x: np.max(x) - np.min(x), t),
        'avgt': (np.mean, t),
        'cads': (np.diff, t),
        'cads_std': (np.std, 'cads'),
        'avg_mag': (np.mean, m),
        'cads_avg': (np.mean, 'cads'),
        'cads_med': (np.median, 'cads'),
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
        'avg_double_to_single_step': (np.mean, 'double_to_single_step'),
        'med_double_to_single_step': (np.median, 'double_to_single_step'),
        'std_double_to_single_step': (np.std, 'double_to_single_step'),
        'delta_t_hist': (delta_t_hist, t),
        'delta_t_nhist': (normalize_hist, 'delta_t_hist', 'total_time'),
        'nhist_peaks': (find_sorted_peaks, 'delta_t_nhist'),
        'all_times_hist_peak_val': (np.max, 'delta_t_hist'),
        # Can't JSON serialize np.int64 under Python3 (yet?), cast as int first
        'all_times_hist_peak_bin': (lambda x: int(np.argmax(x)),
                                    'delta_t_hist'),
        'all_times_nhist_numpeaks': (len, 'nhist_peaks'),
        'all_times_nhist_peak_val': (np.max, 'delta_t_nhist'),
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

    # Do not execute in parallel; parallelization has already taken place at
    # the level of time series, so we compute features for a single time series
    # in serial.
    values = dask.async.get_sync(feature_graph, features_to_compute)
    return dict(zip(features_to_compute, values))
