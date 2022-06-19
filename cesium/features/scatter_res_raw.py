from . import common_functions as cf


def scatter_res_raw(t, m, e, lomb_model):
    """From arXiv 1101_2406v1 Dubath 20110112 paper.

    Scatter: res/raw
    Median absolute deviation (MAD) of the residuals (obtained by subtracting
    model values from the raw light curve) divided by the MAD of the raw
    light-curve values around the median.
    """
    lomb_resid = lomb_model["freq_fits"][-1]["resid"]
    return cf.median_absolute_deviation(lomb_resid) / cf.median_absolute_deviation(m)
