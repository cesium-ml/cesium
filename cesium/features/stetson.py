import numpy as np


def stetson_mean(x, weight=100.0, alpha=2.0, beta=2.0, tol=1.0e-6, nmax=20):
    """An iteratively weighted mean used in the Stetson variability index"""
    mu = np.median(x)
    for i in range(nmax):
        resid = x - mu
        resid_err = np.abs(resid) * np.sqrt(weight)
        weight1 = weight / (1.0 + (resid_err / alpha) ** beta)
        weight1 /= weight1.mean()
        diff = np.mean(x * weight1) - mu
        mu += diff
        if np.abs(diff) < tol * np.abs(mu) or np.abs(diff) < tol:
            break

    return mu


def stetson_j(x, y=[], dx=0.1, dy=0.1):
    """
    Robust covariance statistic between pairs of observations x,y
    whose uncertainties are dx,dy. If y is not given, calculates a robust
    variance for x.
    """
    n = len(x)
    x0 = stetson_mean(x, 1.0 / dx**2)
    delta_x = np.sqrt(n / (n - 1.0)) * (x - x0) / dx

    if len(y) > 0:
        y0 = stetson_mean(y, 1.0 / dy**2)
        delta_y = np.sqrt(n / (n - 1.0)) * (y - y0) / dy
        p_k = delta_x * delta_y
    else:
        p_k = delta_x**2 - 1.0

    return np.mean(np.sign(p_k) * np.sqrt(np.abs(p_k)))


def stetson_k(x, dx=0.1):
    """A robust kurtosis statistic."""
    n = len(x)
    x0 = stetson_mean(x, 1.0 / dx**2)
    delta_x = np.sqrt(n / (n - 1.0)) * (x - x0) / dx
    return 1.0 / 0.798 * np.mean(np.abs(delta_x)) / np.sqrt(np.mean(delta_x**2))
