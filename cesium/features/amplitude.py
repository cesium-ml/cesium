import numpy as np


def amplitude(x):
    """Half the difference between the maximum and minimum magnitude."""
    return (np.max(x) - np.min(x)) / 2.0


# TODO old comment did not match code; is this the quantity we want to compute?
def percent_amplitude(x, base=10.0, exponent=-0.4):
    """Returns the largest distance from the median value, measured
    as a percentage of the median.

    Assumes data is log-scaled; by default we assume inputs are scaled as
    x=10^(-0.4*y), corresponding to units of magnitudes. Computations are
    performed on the corresponding linear-scale values.
    """
    linear_scale_data = base ** (exponent * x)
    y_max = np.max(linear_scale_data)
    y_min = np.min(linear_scale_data)
    y_med = np.median(linear_scale_data)
    return max(abs((y_max - y_med) / y_med), abs((y_med - y_min) / y_med))


def percent_difference_flux_percentile(x, base=10.0, exponent=-0.4):
    """Difference between the 95th and 5th percentiles of the data, expressed
    as a percentage of the median value.
    See Eyer (2005) arXiv:astro-ph/0511458v1, Evans & Belokurov (2005) (there
    the 98th and 2nd percentiles are used).

    Assumes data is log-scaled; by default we assume inputs are scaled as
    x=10^(-0.4*y), corresponding to units of magnitudes. Computations are
    performed on the corresponding linear-scale values.
    """
    linear_scale_data = base ** (exponent * x)
    y_95, y_50, y_5 = np.percentile(linear_scale_data, [95, 50, 5])
    return (y_95 - y_5) / y_50


def flux_percentile_ratio(x, percentile_range, base=10.0, exponent=-0.4):
    """A ratio of ((50+x) flux percentile - (50-x) flux percentile) /
    (95 flux percentile - 5 flux percentile), where x = percentile_range/2.

    Assumes data is log-scaled; by default we assume inputs are scaled as
    x=10^(-0.4*y), corresponding to units of magnitudes. Computations are
    performed on the corresponding linear-scale values.
    """
    linear_scale_data = base ** (exponent * x)
    y_high, y_low, y_95, y_5 = np.percentile(
        linear_scale_data,
        [50 + percentile_range / 2.0, 50 - percentile_range / 2.0, 95, 5],
    )
    return (y_high - y_low) / (y_95 - y_5)
