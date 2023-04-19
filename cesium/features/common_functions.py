import numpy as np
from scipy import stats


def max_slope(t, x):
    """Compute the largest rate of change in the observed data."""
    slopes = np.diff(x) / np.diff(t)
    return np.max(np.abs(slopes))


def maximum(x):
    """Maximum observed value."""
    return np.max(x)


def median(x):
    """Median of observed values."""
    return np.median(x)


def median_absolute_deviation(x):
    """Median absolute deviation (from the median) of the observed values."""
    return np.median(np.abs(x - np.median(x)))


def minimum(x):
    """Minimum observed value."""
    return np.min(x)


def percent_beyond_1_std(x, e):
    """Percentage of values more than 1 std. dev. from the weighted average."""
    dists_from_mu = x - weighted_average(x, e)
    return np.mean(np.abs(dists_from_mu) > weighted_std_dev(x, e))


def percent_close_to_median(x, window_frac=0.1):
    """Percentage of values within window_frac*(max(x)-min(x)) of median."""
    window = (x.max() - x.min()) * window_frac
    return np.mean(np.abs(x - np.median(x)) < window)


def skew(x):
    """Skewness of a dataset. Approximately 0 for Gaussian data."""
    return stats.skew(x)


def kurtosis(x):
    """Kurtosis of a dataset. Approximately 0 for Gaussian data."""
    return stats.kurtosis(x)


def std(x):
    """Standard deviation of observed values."""
    return np.std(x)


def weighted_average(x, e):
    """Arithmetic mean of observed values, weighted by measurement errors."""
    return np.average(x, weights=1.0 / (e**2))


def weighted_average_std_err(x, e):
    """
    Standard deviation of the sample weighted average of values x with
    measurement errors e.

    Note: this is not the same as the weighted sample standard deviation;
    this value only quantifies the measurement errors, not the dispersion of
    the data.
    """
    return np.sqrt(1.0 / np.sum(e**2))


def weighted_std_dev(x, e):
    """Standard deviation of observed values, weighted by measurement errors."""
    return np.sqrt(
        np.average((x - weighted_average(x, e)) ** 2, weights=1.0 / (e**2))
    )


def anderson_darling(x, e):
    "Anderson-Darling test statistic."
    return stats.anderson(x / e)[0]


def shapiro_wilk(x, e):
    "Shapiro-Wilk test statistic."
    return stats.shapiro(x / e)[0]
