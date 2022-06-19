import numpy as np
from scipy.stats import norm
from scipy.linalg import solveh_banded, cholesky_banded
from scipy.special import gammaln, betainc, gammaincc


# TODO duplicate
def lprob2sigma(lprob):
    """Translates a log_e(probability) to units of Gaussian sigmas."""
    if lprob > -36.0:
        sigma = norm.ppf(1.0 - 0.5 * np.exp(1.0 * lprob))
    else:
        sigma = np.sqrt(np.log(2.0 / np.pi) - 2.0 * np.log(8.2) - 2.0 * lprob)
    return float(sigma)


def chol_inverse_diag(t):
    """Computes inverse of matrix given its Cholesky upper Triangular decomposition t.
    matrix form: ab[u + i - j, j] == a[i,j] (here u=1)
    (quick version: only calculates diagonal and neighboring elements)
    """
    (uu, nrows) = t.shape
    B = np.zeros((uu, nrows), dtype="float64")
    B[1, nrows - 1] = 1.0 / t[1, nrows - 1] ** 2
    B[0, nrows - 1] = -t[0, nrows - 1] * B[1, nrows - 1] / t[1, nrows - 2]
    for j in reversed(range(nrows - 1)):
        tjj = t[1, j]
        B[1, j] = (1.0 / tjj - t[0, j + 1] * B[0, j + 1]) / tjj
        B[0, j] = -t[0, j] * B[1, j] / t[1, j - 1]
    return B


def qso_engine(time, data, error, ltau=3.0, lvar=-1.7, sys_err=0.0, return_model=False):
    """Calculates the fit quality of a damped random walk to a qso lightcurve.
    The formalism is from Rybicki & Press (1994; arXiv:comp-gas/9405004)

    Data are modelled with a covariance function
        Lij = 0.5*var*tau*exp(-|time_i-time_j|/tau) .

    Input:
        time - measurement times, typically days
        data - measured magnitudes
        error - uncertainty in measured magnitudes

    Output (dictionary):

        chi2/nu - classical variability measure
        chi2_qso/nu - for goodness of fit given fixed parameters
        chi2_qso/nu_extra - for parameter fitting, add to chi2/nu
        chi^2/nu_NULL - expected chi2/nu for non-qso variable

        signif_qso - significance chi^2/nu<chi^2/nu_NULL (rule out false alarm)
        signif_not_qso - significance chi^2/nu>1 (rule out qso)
        signif_vary - significance that source is variable
        class - resulting source type (ambiguous, not_qso, qso)

        model - time series prediction for each datum given all others (iff return_model==True)
        dmodel - model uncertainty, including uncertainty in data

    Notes:
        T = L^(-1)
        Data variance is D
        Full covariance C^(-1) = (L+D)^(-1) = T [T+D^(-1)]^(-1) D^(-1)
        Code takes advantage of the tridiagonality of T and T+D^(-1).
    """

    out_dict = {}
    out_dict["chi2_qso/nu"] = 999
    out_dict["chi2_qso/nu_extra"] = 0.0
    out_dict["signif_qso"] = 0.0
    out_dict["signif_not_qso"] = 0.0
    out_dict["signif_vary"] = 0.0
    out_dict["chi2_qso/nu_NULL"] = 0.0
    out_dict["chi2/nu"] = 0.0
    out_dict["nu"] = 0
    out_dict["model"] = []
    out_dict["dmodel"] = []
    out_dict["class"] = "ambiguous"

    lvar0 = np.log10(0.5) + lvar + ltau

    ln = len(data)
    dt = abs(time[1:] - time[:-1])

    # first make sure all dt>0
    g = np.where(dt > 0.0)[0]
    lg = len(g)
    # must have at least 2 data points
    if lg <= 0:
        return out_dict

    if return_model:
        model = 1.0 * data
        dmodel = -1.0 * error

    if lg < ln:
        dt = dt[g]
        gg = np.zeros(lg + 1, dtype="int64")
        gg[1:] = g + 1
        dat = data[gg]
        wt = 1.0 / (sys_err**2 + error[gg] ** 2)
        ln = lg + 1
    else:
        dat = 1.0 * data
        wt = 1.0 / (sys_err**2 + error**2)

    out_dict["nu"] = ln - 1.0
    varx = np.var(dat)
    dat0 = (dat * wt).sum() / wt.sum()
    out_dict["chi2/nu"] = ((dat - dat0) ** 2 * wt).sum() / out_dict["nu"]

    # define tridiagonal matrix T = L^(-1)
    # sparse matrix form: ab[u + i - j, j] == a[i,j]   i<=j, (here u=1)
    T = np.zeros((2, ln), dtype="float64")
    arg = dt * np.exp(-np.log(10) * ltau)
    ri = np.exp(-arg)
    ei = 1.0 / (1.0 / ri - ri)
    T[0, 1:] = -ei
    T[1, :-1] = 1.0 + ri * ei
    T[1, 1:] += ri * ei
    T[1, ln - 1] += 1.0
    T0 = np.median(T[1, :])
    T /= T0

    # equation for chi2_qso is [ (dat-x0) T Tp^(-1) D^(-1) (dat-x0) ]  , where Tp=T+D^(-1) and D^(-1)=wt
    fac = np.exp(np.log(10) * lvar0) / T0
    Tp = 1.0 * T
    Tp[1, :] += wt * fac
    # solve Tp*z=y for z (y=wt*dat)
    # This works for scipy __version__>='0.9.0' on anathem (20120809)
    b1 = (wt * dat).reshape((1, ln))
    b2 = b1.T
    # (Tpc,z) = solveh_banded(Tp,b2)
    z = solveh_banded(Tp, b2)
    Tpc = cholesky_banded(
        Tp
    )  # the solveh_banded() function used to return the cholesky matrix, now we get seperately
    z = z.T
    z = z[0, :]
    c1 = wt.reshape((1, ln))
    c2 = c1.T
    # (Tpc,z0) = solveh_banded(Tp,c2)
    z0 = solveh_banded(Tp, c2)
    # HAS NOT CHANGED#Tpc2 = cholesky_banded(Tp)
    z0 = z0.T
    z0 = z0[0, :]

    # finally, get u=T*z
    u = T[1, :] * z
    u[1:] += T[0, 1:] * z[:-1]
    u[:-1] += T[0, 1:] * z[1:]
    u0 = T[1, :] * z0
    u0[1:] += T[0, 1:] * z0[:-1]
    u0[:-1] += T[0, 1:] * z0[1:]

    # magnitude offset x0, error = 1./sqrt(u0sum)
    u0sum = u0.sum()
    x0 = u.sum() / u0sum

    # fit statistic
    out_dict["chi2_qso/nu"] = np.dot(dat - x0, u - u0 * x0) / out_dict["nu"]

    # -2*log(likelihood) = chi2_qso + ldet_C + log(u0sum)
    #   first term: use chi2_qso/nu for goodness of fit with fixed parameters;
    #   all terms: use chi2_qso/nu + chi2_qso/nu_extra for fitting with variable parameters
    # get log of determinant for use later
    Tc = cholesky_banded(T)
    ldet_Tp = 2 * np.log(Tpc[1, :]).sum()
    ldet_T = 2 * np.log(Tc[1, :]).sum()
    ldet_C = ldet_Tp - ldet_T - np.log(wt).sum()
    out_dict["chi2_qso/nu_extra"] = (ldet_C + np.log(u0sum)) / out_dict["nu"]

    # get trace of C^(-1) for significance calculation
    Tpm = chol_inverse_diag(Tpc)
    diagC = T[1, :] * wt * Tpm[1, :]
    diagC[:-1] += T[0, 1:] * wt[0:-1] * Tpm[0, 1:]
    diagC[1:] += T[0, 1:] * wt[1:] * Tpm[0, 1:]
    TrC = diagC.sum()

    # significance in sigma units (large means false alarm unlikely)
    # (expected value of chi2_qso under the NULL hypothesis is TrC*varx)
    out_dict["chi2_qso/nu_NULL"] = TrC * varx / out_dict["nu"]
    a = ln / 2.0
    x = (out_dict["chi2_qso/nu"] + 1.0e-8) / (
        out_dict["chi2_qso/nu_NULL"] + out_dict["chi2_qso/nu"] + 1.0e-8
    )
    prob = betainc(a, a, x)
    if prob <= 0:
        lprob = a * np.log(x) - np.log(a) + gammaln(2 * a) - 2 * gammaln(a)
    else:
        lprob = np.log(prob)
    out_dict["signif_qso"] = lprob2sigma(lprob)

    a = ln / 2.0
    x = 1.0 / (1.0 + out_dict["chi2_qso/nu"])
    prob = betainc(a, a, x)
    if prob <= 0:
        lprob = a * np.log(x) - np.log(a) + gammaln(2 * a) - 2 * gammaln(a)
    else:
        lprob = np.log(prob)
    out_dict["signif_not_qso"] = lprob2sigma(lprob)

    x = out_dict["chi2/nu"] * out_dict["nu"]
    prob = gammaincc(0.5 * out_dict["nu"], 0.5 * x)
    if prob <= 0:
        lprob = (
            (0.5 * out_dict["nu"] - 1) * np.log(x)
            - 0.5 * x
            - 0.5 * out_dict["nu"] * np.log(2)
            - gammaln(0.5 * out_dict["nu"])
        )
    else:
        lprob = np.log(prob)
    out_dict["signif_vary"] = lprob2sigma(lprob)

    if out_dict["signif_vary"] > 3:
        if out_dict["signif_qso"] > 3:
            out_dict["class"] = "qso"
        elif out_dict["signif_not_qso"] > 3:
            out_dict["class"] = "not_qso"

    # best-fit model for the lightcurve
    if return_model:
        model[gg] = dat - (u - u0 * x0) / diagC
        dmodel[gg] = 1.0 / np.sqrt(diagC)
        out_dict["model"] = model
        out_dict["dmodel"] = dmodel

    return out_dict


def qso_fit(time, data, error, filter="g", mag0=19.0, sys_err=0.0, return_model=False):
    """Best-fit qso model determined for Sesar Strip82, ugriz-bands (default r).
    See additional notes for underlying code qso_engine.

    Input:
        time - measurement times [days]
        data - measured magnitudes in single filter (also specified)
        error - uncertainty in measured magnitudes

    Output:
        chi^2/nu - classical variability measure
        chi^2_qso/nu - fit statistic
        chi^2_qso/nu_NULL - expected fit statistic for non-qso variable

        signif_qso - significance chi^2/nu<chi^2/nu_NULL (rule out false alarm)
        signif_not_qso - significance chi^2/nu>1 (rule out qso)
        signif_vary - significance that source is variable at all
        class - source type (ambiguous, not_qso, qso)

        model - time series prediction for each datum given all others (iff return_model==True)
        dmodel - model uncertainty, including uncertainty in data

    Note on use (i.e., how class is defined):

          (0) signif_vary < 3: ambiguous, else
          (1) signif_qso > 3: qso, else
          (2) signif_not_qso > 3: not_qso
    """

    data = data.copy() - np.median(data) + mag0
    pars = {}
    pars["u"] = [-3.90, 0.12, 2.73, -0.02]
    pars["g"] = [-4.10, 0.14, 2.92, -0.07]
    pars["r"] = [-4.34, 0.20, 3.12, -0.15]
    pars["i"] = [-4.23, 0.05, 2.83, 0.07]
    pars["z"] = [-4.44, 0.13, 3.06, -0.07]

    par = pars[filter.lower()]
    lvar = par[0] + par[1] * (mag0 - 19.0)
    ltau = par[2] + par[3] * (mag0 - 19.0)

    adict = qso_engine(
        time,
        data,
        error,
        ltau=ltau,
        lvar=lvar,
        return_model=return_model,
        sys_err=sys_err,
    )

    out_dict = {}
    out_dict["lvar"] = lvar
    out_dict["ltau"] = ltau
    out_dict["chi2/nu"] = adict["chi2/nu"]
    out_dict["nu"] = adict["nu"]
    out_dict["chi2_qso/nu"] = adict["chi2_qso/nu"]
    out_dict["chi2_qso/nu_NULL"] = adict["chi2_qso/nu_NULL"]
    out_dict["signif_qso"] = adict["signif_qso"]
    out_dict["signif_not_qso"] = adict["signif_not_qso"]
    out_dict["signif_vary"] = adict["signif_vary"]
    out_dict["class"] = adict["class"]
    out_dict["chi2qso_nu_nuNULL_ratio"] = (
        out_dict["chi2_qso/nu"] / out_dict["chi2_qso/nu_NULL"]
    )

    # ---
    # Nat has converged upon the following being the most significant features,
    # Joey believes it is best to just use these features only (so now the others are disabled in
    # __init__.py and qso_extractor.py
    out_dict["log_chi2_qsonu"] = np.log(out_dict["chi2_qso/nu"])
    out_dict["log_chi2nuNULL_chi2nu"] = np.log(
        out_dict["chi2_qso/nu_NULL"] / out_dict["chi2_qso/nu"]
    )
    # ---

    if return_model:
        out_dict["model"] = adict["model"]
        out_dict["dmodel"] = adict["dmodel"]

    return out_dict


def get_qso_log_chi2_qsonu(qso_model):
    """Natural log of goodness of fit of qso-model given fixed parameters."""
    return qso_model["log_chi2_qsonu"]


def get_qso_log_chi2nuNULL_chi2nu(qso_model):
    """Natural log of expected chi2/nu for non-qso variable."""
    return qso_model["log_chi2nuNULL_chi2nu"]
