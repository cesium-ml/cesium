import numpy as np
import scipy.stats as stats


__all__ = [
    "double_to_single_step",
    "cad_prob",
    "delta_t_hist",
    "normalize_hist",
    "find_sorted_peaks",
    "peak_ratio",
    "peak_bin",
]


def double_to_single_step(cads):
    """Ratios ``(t[i+2] - t[i]) / (t[i+1] - t[i]``)."""
    cads = np.asarray(cads)
    return (cads[2:] + cads[:-2]) / (cads[1:-1] - cads[:-2])


def cad_prob(cads, time):
    """Given the observed distribution of time lags `cads`, compute the probability
    that the next observation occurs within `time` minutes of an arbitrary epoch.
    """
    return stats.percentileofscore(cads, float(time) / (24.0 * 60.0)) / 100.0


def delta_t_hist(t, nbins=50, conv_oversample=50):
    """Build histogram of all possible ``|t_i - t_j|``'s.

    For efficiency, we construct the histogram via a convolution of the PDF
    rather than by actually computing all the differences. For better accuracy
    we use a factor `conv_oversample` more bins when performing the convolution
    and then aggregate the result to have `nbins` total values.
    """
    f, x = np.histogram(t, bins=conv_oversample * nbins)
    g = np.convolve(f, f[::-1])[len(f) - 1 :]  # Discard negative domain
    g[0] -= len(t)  # First bin is double-counted because of i=j terms
    hist = g.reshape((-1, conv_oversample)).sum(axis=1)  # Combine bins
    return hist


def normalize_hist(hist, total_time):
    """Normalize histogram such that integral from ``t_min`` to ``t_max`` equals 1.
    cf. ``np.histogram(..., density=True)``.
    """
    return hist / (total_time * np.mean(hist))


def find_sorted_peaks(x):
    """Find peaks, i.e. local maxima, of an array. Interior points are peaks if
    they are greater than both their neighbors, and edge points are peaks if
    they are greater than their only neighbor. In the case of ties, we
    (arbitrarily) choose the first index in the sequence of equal values as the
    peak.
    Returns a list of tuples ``(i, x[i])`` of peak indices ``i`` and values
    ``x[i]``, sorted in decreasing order by peak value.
    """
    peak_inds = []
    nbins = len(x)
    for i in range(nbins):
        if i == 0 or x[i] > x[i - 1]:  # Increasing from left
            if i == nbins - 1 or x[i] > x[i + 1]:  # Increasing from right
                peak_inds.append(i)
            elif x[i] == x[i + 1]:  # Tied; check the next non-equal value
                for j in range(i + 1, nbins):
                    if x[j] != x[i]:
                        if x[j] < x[i]:
                            peak_inds.append(i)
                        break
                if j == nbins - 1 and x[i] == x[j]:  # Reached the end
                    peak_inds.append(i)
    sorted_peak_inds = sorted(peak_inds, key=lambda i: x[i], reverse=True)
    return list(zip(sorted_peak_inds, x[sorted_peak_inds]))


def peak_ratio(peaks, i, j):
    """Compute the ratio of the values of the ith and jth largest peaks. Peaks is a list
    of tuples ``(i, x[i])`` of peak indices ``i`` and values ``x[i]``, sorted in decreasing order
    by peak value.
    """
    if len(peaks) > i and len(peaks) > j:
        return peaks[i][1] / peaks[j][1]
    else:
        return np.nan


def peak_bin(peaks, i):
    """Return the (bin) index of the ith largest peak. Peaks is a list of tuples
    ``(i, x[i])`` of peak indices ``i`` and values ``x[i]``, sorted in
    decreasing order by peak value.
    """
    if len(peaks) > i:
        return peaks[i][0]
    else:
        return np.nan
