import numpy as np
from . import lomb_scargle as ls
from . import common_functions as cf


# TODO is this worth it since it doubles running time?
def period_folding(x, y, dy, lomb_model, sys_err=0.05):
    """
    This section is used to calculate Dubath (10. Percentile90:2P/P),
    which requires regenerating a model using 2P where P is the original found period

    NOTE: this essentially runs everything a second time, so makes feature
    generation take roughly twice as long.
    """
    out_dict = {}
    model_vals = np.zeros(len(y))
    freq_2p = lomb_model["freq_fits"][0]["freq"] * 0.5
    ytest_2p = y.copy()
    dy0 = np.sqrt(dy**2 + sys_err**2)

    # Here we force the freq to just 2*freq1_Period; we also do not use linear
    # detrending since we are not searching for freqs, and we want the
    # resulting model to be smooth when in phase-space. Detrending would result
    # in non-smooth model when period folded
    lambda0_range = [-np.log10(len(x)), 8.0]
    fit = ls.fit_lomb_scargle(
        x,
        ytest_2p,
        dy0,
        freq_2p,
        lomb_model["df"],
        1,
        lambda0_range=lambda0_range,
        nharm=lomb_model["nharm"],
        detrend_order=0,
    )
    model_vals += fit["model"]

    ytest_2p -= fit["model"]
    for i in range(1, lomb_model["nfreq"]):
        fit = ls.fit_lomb_scargle(
            x,
            ytest_2p,
            dy0,
            lomb_model["f0"],
            lomb_model["df"],
            lomb_model["numf"],
            lambda0_range=lambda0_range,
            nharm=lomb_model["nharm"],
            detrend_order=0,
        )
        ytest_2p -= fit["model"]

    out_dict["1p_resid"] = lomb_model["freq_fits"][-1]["resid"]
    out_dict["2p_resid"] = ytest_2p

    # So the following uses the 2*Period model, and gets a time-sorted, folded t and m:
    # NOTE: if this is succesful, I think a lot of other features could characterize the
    # shapes of the 2P folded data (not P or 2P dependent).
    # the reason we choose 2P is that occasionally for eclipsing
    # sources the LS code chooses 0.5 of true period (but never 2x
    # the true period).  slopes are not dependent upon the actual
    # period so 2P is fine if it gives a high chance of correct fitting.
    # NOTE: we only use the model from freq1 because this with its harmonics seems to
    # adequately model shapes such as RRLyr skewed sawtooth, multi minima of rvtau
    # without getting the scatter from using additional LS found frequencies.
    t_2per_fold = np.array(x % (1.0 / freq_2p))
    t_2per_sort_inds = np.argsort(t_2per_fold)
    t_2per_fold = t_2per_fold[t_2per_sort_inds]
    y_2per_fold = np.array(model_vals)[t_2per_sort_inds]
    out_dict["folded_slopes"] = np.diff(y_2per_fold) / np.diff(t_2per_fold)

    return out_dict


def p2p_model(x, y, frequency):
    """
    Compute features that compare the residuals of data folded by estimated
    period from Lomb-Scargle model with residuals folded by twice the estimated
    period.
    """

    sumsqr_diff_unfold = np.sum(np.diff(y) ** 2)
    median_diff = np.median(np.abs(np.diff(y)))
    mad = cf.median_absolute_deviation(y)
    x = x.copy()
    x = x - min(x)

    t_2per_fold = np.array(x % (2.0 / frequency))
    t_2per_sort_inds = np.argsort(t_2per_fold)
    t_2per_fold = t_2per_fold[t_2per_sort_inds]
    y_2per_fold = np.array(y)[t_2per_sort_inds]
    sumsqr_diff_2per_fold = np.sum(np.diff(y_2per_fold) ** 2)

    # eta feature from arXiv 1101.3316 Kim QSO paper:
    t_1per_fold = np.array(x % (1.0 / frequency))
    t_1per_sort_inds = np.argsort(t_1per_fold)
    t_1per_fold = t_1per_fold[t_1per_sort_inds]
    y_1per_fold = np.array(y)[t_1per_sort_inds]
    median_1per_fold_diff = np.median(np.abs(np.diff(y_1per_fold)))

    out_dict = {}
    out_dict["scatter_2praw"] = sumsqr_diff_2per_fold / sumsqr_diff_unfold
    out_dict["scatter_over_mad"] = median_diff / mad
    out_dict["ssqr_diff_over_var"] = sumsqr_diff_unfold / ((len(y) - 1) * np.var(y))
    out_dict["scatter_pfold_over_mad"] = median_1per_fold_diff / mad
    return out_dict


# TODO why not just get the (almost) steepest positive/negative slopes directly?
# TODO wrong for strictly increasing/decreasing
def get_fold2P_slope_percentile(model, alpha):
    """Get alphath percentile of slopes of period-folded model."""
    return np.percentile(model["folded_slopes"], alpha)


def get_medperc90_2p_p(model):
    """
    Get ratio of 90th percentiles of residuals for data folded by twice the
    estimated period and the estimated period, respectively.
    """
    return np.percentile(np.abs(model["2p_resid"]), 90) / np.percentile(
        np.abs(model["1p_resid"]), 90
    )


def get_p2p_scatter_2praw(model):
    """
    Get ratio of variability (sum of squared differences of consecutive
    values) of folded and unfolded models.
    """
    return model["scatter_2praw"]


def get_p2p_scatter_over_mad(model):
    """Get ratio of variability of folded and unfolded models."""
    return model["scatter_over_mad"]


def get_p2p_scatter_pfold_over_mad(model):
    """
    Get ratio of median of period-folded data over median absolute
    deviation of observed values.
    """
    return model["scatter_pfold_over_mad"]


def get_p2p_ssqr_diff_over_var(model):
    """
    Get sum of squared differences of consecutive values as a fraction of the
    variance of the data.
    """
    return model["ssqr_diff_over_var"]
