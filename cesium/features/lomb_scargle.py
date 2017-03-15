import numpy as np
import scipy.stats as stats
from ._lomb_scargle import lomb_scargle


def lomb_scargle_model(time, signal, error, sys_err=0.05, nharm=8, nfreq=3, tone_control=5.0):
    """Simultaneous fit of a sum of sinusoids by weighted least squares:
           y(t) = Sum_k Ck*t^k + Sum_i Sum_j A_ij sin(2*pi*j*fi*(t-t0)+phi_j),
           i=[1,nfreq], j=[1,nharm]

    Parameters
    ----------
    time : array_like
        Array containing time values.

    signal : array_like
        Array containing data values.

    error : array_like
        Array containing measurement error values.

    nharm : int
        Number of harmonics to fit for each frequency.

    nfreq : int
        Number of frequencies to fit.

    Returns
    -------
    dict
        Dictionary containing fitted parameter values. Parameters specific to
        a specific fitted frequency are stored in a list of dicts at
        model_dict['freq_fits'], each of which contains the output of
        fit_lomb_scargle(...)

    """

    dy0 = np.sqrt(error**2 + sys_err**2)

    wt = 1. / dy0**2
    time = time.copy() - min(time) # speeds up lomb_scargle code to have min(time)==0
    signal = signal.copy()

    chi0 = np.dot(signal**2, wt)

# TODO parametrize?
    f0 = 1. / max(time)
    df = 0.8 / max(time) # 20120202 :    0.1/Xmax
    fmax = 33. #pre 20120126: 10. # 25
    numf = int((fmax - f0) / df) # TODO !!! this is off by 1 point, fix?

    model_dict = {'freq_fits' : []}
    lambda0_range = [-np.log10(len(time)), 8] # these numbers "fix" the strange-amplitude effect
    for i in range(nfreq):
        if i == 0:
            fit = fit_lomb_scargle(time, signal, dy0, f0, df, numf,
                    tone_control=tone_control, lambda0_range=lambda0_range,
                    nharm=nharm, detrend_order=1)
            model_dict['trend'] = fit['trend_coef'][1]
        else:
            fit = fit_lomb_scargle(time, signal, dy0, f0, df, numf,
                    tone_control=tone_control, lambda0_range=lambda0_range,
                    nharm=nharm, detrend_order=0)
        model_dict['freq_fits'].append(fit)
        signal -= fit['model']
        model_dict['freq_fits'][-1]['resid'] = signal.copy()
        if i == 0:
            model_dict['varrat'] = np.dot(signal**2, wt) / chi0

    model_dict['nfreq'] = nfreq
    model_dict['nharm'] = nharm
    model_dict['chi2'] = fit['chi2']
    model_dict['f0'] = f0
    model_dict['df'] = df
    model_dict['numf'] = numf

    return model_dict


def lprob2sigma(lprob):
    """Translate a log_e(probability) to units of Gaussian sigmas."""
    if lprob > -36.:
        sigma = stats.norm.ppf(1. - 0.5 * np.exp(lprob))
    else:
        sigma = np.sqrt(np.log(2. / np.pi) - 2. * np.log(8.2) - 2. * lprob)
        f = 0.5 * np.log(2. / np.pi) - 0.5 * sigma**2 - np.log(sigma) - lprob
        sigma += f / (sigma + 1. / sigma)
    return sigma


def fit_lomb_scargle(time, signal, error, f0, df, numf, nharm=8, psdmin=6., detrend_order=0,
         freq_zoom=10., tone_control=5., lambda0=1., lambda0_range=[-8,6]):
    """Calls C implementation of Lomb Scargle sinusoid fitting, which fits a
    single frequency with nharm harmonics to the data. Called repeatedly by
    lomb_scargle_model in order to produce a fit with multiple distinct
    frequencies.

    Inputs:
    time : array_like
        Array containing time values.

    signal : array_like
        Array containing data values.

    error : array_like
        Array containing measurement error values.

    f0 : float
        Smallest frequency value to consider.

    df : float
        Step size for frequency grid search.

    numf : int
        Number of frequencies for frequency grid search.

    nharm : int
        Number of harmonics to fit.

    detrend_order : int
        Order of polynomial detrending.

    psdmin : int
        Refine periodogram values with larger psd using multi-harmonic fit

    nharm : int
        Number of harmonics to use in refinement

    lambda0 : float
        Typical value for regularization parameter

    lambda0_range : [float, float]
        Allowable range for log10 of regularization parameter

    Returns
    -------
    dict
        Dictionary describing various parameters of the multiharmonic fit at
        the best-fit frequency
    """
    ntime = len(time)

# For some reason we round this to the nearest even integer
    freq_zoom = round(freq_zoom/2.)*2.

# Polynomial terms
    coef = np.zeros(detrend_order + 1, dtype='float64')
    norm = np.zeros(detrend_order + 1, dtype='float64')

    wth0 = 1. / error
    s0 = np.dot(wth0, wth0)
    wth0 /= np.sqrt(s0)

    cn = signal * wth0
    coef[0] = np.dot(cn,wth0)
    cn0 = coef[0]
    norm[0] = 1.
    cn -= coef[0] * wth0
    vcn = 1.

    # np.sin's and cosin's for later
    tt = 2. * np.pi * time
    sinx,cosx = np.sin(tt*f0)*wth0,np.cos(tt*f0)*wth0
    sinx_step,cosx_step = np.sin(tt*df),np.cos(tt*df)
    sinx_back,cosx_back = -np.sin(tt*df/2.),np.cos(tt*df/2)
    sinx_smallstep,cosx_smallstep = np.sin(tt*df/freq_zoom),np.cos(tt*df/freq_zoom)

    npar = 2*nharm
    hat_matr = np.zeros((npar,ntime),dtype='float64')
    hat0 = np.zeros((npar,detrend_order+1),dtype='float64')
    hat_hat = np.zeros((npar,npar),dtype='float64')
    soln = np.zeros(npar,dtype='float64')
    psd = np.zeros(numf,dtype='float64')

    # Detrend the data and create the orthogonal detrending basis
    if detrend_order > 0:
        wth = np.zeros((detrend_order + 1, ntime),dtype='float64')
        wth[0,:] = wth0
    else:
        wth = wth0

    for i in range(detrend_order):
        f = wth[i,:] * tt / (2 * np.pi)
        for j in range(i+1):
            f -= np.dot(f, wth[j,:]) * wth[j,:]
        norm[i+1] = np.sqrt(np.dot(f,f))
        f /= norm[i+1]
        coef[i+1] = np.dot(cn,f)
        cn -= coef[i+1]*f
        wth[i+1,:] = f
        vcn += (f/wth0)**2

    chi0 = np.dot(cn,cn)
    varcn = chi0/(ntime-1-detrend_order)
    psdmin *= 2*varcn

    Tr = np.array(0., dtype='float64')
    ifreq = np.array(0, dtype='int32')
    lambda0 = np.array(lambda0 / s0, dtype='float64')
    lambda0_range = 10**np.array(lambda0_range, dtype='float64') / s0

    lomb_scargle(ntime, numf, nharm, detrend_order, psd, cn, wth, sinx, cosx,
            sinx_step, cosx_step, sinx_back, cosx_back, sinx_smallstep,
            cosx_smallstep, hat_matr, hat_hat, hat0, soln, chi0, freq_zoom,
            psdmin, tone_control, lambda0, lambda0_range, Tr, ifreq)

    hat_hat /= s0
    ii = np.arange(nharm, dtype='int32')
    soln[0:nharm] /= (1. + ii)**2
    soln[nharm:] /= (1. + ii)**2
    hat_matr0 = np.outer(hat0[:,0], wth0)
    for i in range(detrend_order):
        hat_matr0 += np.outer(hat0[:,i+1], wth[i+1,:])

    modl = np.dot(hat_matr.T, soln)
    coef0 = np.dot(soln, hat0)
    coef -= coef0
    hat_matr -= hat_matr0

    out_dict = {}
    out_dict['psd'] = psd
    out_dict['chi0'] = chi0 * s0
    if detrend_order > 0:
        out_dict['trend'] = np.dot(coef,wth)/wth0
    else:
        out_dict['trend'] = coef[0] + 0*wth0
    out_dict['model'] = modl/wth0 + out_dict['trend']

    j = psd.argmax()
    freq = f0 + df * j + (ifreq / freq_zoom - 1/2.) * df
    tt = (time * freq) % 1.
    out_dict['freq'] = freq
    out_dict['s0'] = s0
    out_dict['chi2'] = (chi0 - psd[j]) * s0
    out_dict['psd'] = psd[j] * 0.5 / varcn
    out_dict['lambda'] = lambda0 * s0
#    out_dict['gcv_weight'] = (1 - 3. / ntime) / Tr
    out_dict['trace'] = Tr
    out_dict['nu0'] = ntime - npar
    npars = (1 - Tr) * ntime / 2.
    out_dict['nu'] = ntime - npars
    out_dict['npars'] = npars

    A0, B0 = soln[0:nharm], soln[nharm:]
    hat_hat /= np.outer(np.hstack(((1.+ii)**2, (1.+ii)**2)), np.hstack(((1.+ii)**2, (1.+ii)**2)))
    err2 = np.diag(hat_hat)
    vA0, vB0 = err2[0:nharm], err2[nharm:]
    covA0B0 = hat_hat[(ii,nharm+ii)]

    vmodl = vcn/s0 + np.dot((hat_matr/wth0).T, np.dot(hat_hat, hat_matr/wth0))
    vmodl0 = vcn/s0 + np.dot((hat_matr0/wth0).T, np.dot(hat_hat, hat_matr0/wth0))
    out_dict['model_error'] = np.sqrt(np.diag(vmodl))
    out_dict['trend_error'] = np.sqrt(np.diag(vmodl0))

    amp = np.sqrt(A0**2 + B0**2)
    damp = np.sqrt(A0**2 * vA0 + B0**2 * vB0 + 2. * A0 * B0 * covA0B0) / amp
    phase = np.arctan2(B0, A0)
    rel_phase = phase - phase[0]*(1.+ii)
    rel_phase = np.arctan2(np.sin(rel_phase), np.cos(rel_phase))
    dphase = 0.*rel_phase
    for i in range(nharm - 1):
        j = i + 1
        v = np.array([-A0[0] * (1. + j) / amp[0]**2, B0[0] * (1. + j) / amp[0]**2, A0[j] / amp[j]**2, -B0[j] / amp[j]**2])
        jj = np.array([0, nharm, j, j+nharm])
        m = hat_hat[np.ix_(jj, jj)]
        dphase[j] = np.sqrt(np.dot(np.dot(v, m), v))

    out_dict['amplitude'] = amp
    out_dict['amplitude_error'] = damp
    out_dict['rel_phase'] = rel_phase
    out_dict['rel_phase_error'] = dphase
    out_dict['time0'] = -phase[0] / (2 * np.pi * freq)

    ncp = norm.cumprod()
    out_dict['trend_coef'] = coef / ncp
    out_dict['y_offset'] = out_dict['trend_coef'][0] - cn0

    prob = stats.f.sf(0.5 * (ntime - 1. - detrend_order) * (1. -out_dict['chi2'] / out_dict['chi0']), 2, ntime - 1 - detrend_order)
    out_dict['signif'] = lprob2sigma(np.log(prob))

    return out_dict


def get_lomb_frequency(lomb_model, i):
    """Get the ith frequency from a fitted Lomb-Scargle model."""
    return lomb_model['freq_fits'][i-1]['freq']


def get_lomb_amplitude(lomb_model, i, j):
    """
    Get the amplitude of the jth harmonic of the ith frequency from a fitted
    Lomb-Scargle model.
    """
    return lomb_model['freq_fits'][i-1]['amplitude'][j-1]


def get_lomb_rel_phase(lomb_model, i, j):
    """
    Get the relative phase of the jth harmonic of the ith frequency from a
    fitted Lomb-Scargle model.
    """
    return lomb_model['freq_fits'][i-1]['rel_phase'][j-1]


def get_lomb_amplitude_ratio(lomb_model, i):
    """
    Get the ratio of the amplitudes of the first harmonic for the ith and first
    frequencies from a fitted Lomb-Scargle model.
    """
    return (lomb_model['freq_fits'][i-1]['amplitude'][0] /
            lomb_model['freq_fits'][0]['amplitude'][0])


def get_lomb_frequency_ratio(lomb_model, i):
    """
    Get the ratio of the ith and first frequencies from a fitted Lomb-Scargle
    model.
    """
    return (lomb_model['freq_fits'][i-1]['freq'] /
            lomb_model['freq_fits'][0]['freq'])


def get_lomb_signif_ratio(lomb_model, i):
    """
    Get the ratio of the significances (in sigmas) of the ith and first
    frequencies from a fitted Lomb-Scargle model.
    """
    return (lomb_model['freq_fits'][i-1]['signif'] /
            lomb_model['freq_fits'][0]['signif'])


def get_lomb_lambda(lomb_model):
    """Get the regularization parameter of a fitted Lomb-Scargle model."""
    return lomb_model['freq_fits'][0]['lambda']


def get_lomb_signif(lomb_model):
    """
    Get the significance (in sigmas) of the first frequency from a fitted
    Lomb-Scargle model.
    """
    return lomb_model['freq_fits'][0]['signif']


def get_lomb_varrat(lomb_model):
    """
    Get the fraction of the variance explained by the first frequency of a
    fitted Lomb-Scargle model.
    """
    return lomb_model['varrat']


def get_lomb_trend(lomb_model):
    """Get the linear trend of a fitted Lomb-Scargle model."""
    return lomb_model['trend']


def get_lomb_y_offset(lomb_model):
    """Get the y-intercept of a fitted Lomb-Scargle model."""
    return lomb_model['freq_fits'][0]['y_offset']
