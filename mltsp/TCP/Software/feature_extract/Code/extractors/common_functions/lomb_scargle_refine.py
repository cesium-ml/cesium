from numpy import exp,empty,pi,sqrt,sin,cos,dot,where,arange,arctan2,array,diag,ix_,log10,outer,hstack,log,round,zeros
from scipy.stats import f as fdist, norm
from ._lomb_scargle import lomb_scargle


def lprob2sigma(lprob):
    """ translates a log_e(probability) to units of Gaussian sigmas
    """

    if (lprob>-36.):
        sigma = norm.ppf(1.-0.5*exp(1.*lprob))
    else:
        # this is good to 5.e-2; just to be crazy, get to 5.e-5
        sigma = sqrt( log(2./pi) - 2.*log(8.2) - 2.*lprob )
        f = 0.5*log(2./pi) - 0.5*sigma**2 - log(sigma) - lprob
        df = - sigma - 1./sigma
        sigma = sigma - f/df

    return float(sigma)


def lomb(time, signal, error, f1, df, numf, nharm=8, psdmin=6., detrend_order=0,
         freq_zoom=10., tone_control=1., return_model=True,
         lambda0=1., lambda0_range=[-8,6]):
    """
    C version of lomb_scargle:
    Simultaneous fit of a sum of sinusoids by weighted, linear least squares.
          model(t) = Sum_k Ck*t^k + Sum_i Sum_j Aij sin(2*pi*j*fi*(t-t0)+phij), i=[1,nfreq], j=[1,nharm]
           [t0 defined such that ph11=0]

    Inputs:
        time: time vector
        signal: data vector
        error: data uncertainty vector
        df: frequency step
        numf: number of frequencies to consider

        detrend_order: order of polynomial detrending (Ck orthogonol polynomial terms above;
            0 floating mean; <0 no detrending)

        psdmin: refine periodogram values with larger psd using multi-harmonic fit
        nharm: number of harmonics to use in refinement
        lambda0: typical value for regularization parameter (expert parameter)
        lambda0_range: allowable range for log10 of regularization parameter

    Output:
        psd: power spectrum on frequency grid: f1,f1+df,...,f1+numf*df
        out_dict: dictionary describing various parameters of the multiharmonic fit at
            the best-fit frequency
    """
    numt = len(time)

    freq_zoom = round(freq_zoom/2.)*2.

    dord = detrend_order
    if (detrend_order<0):
        dord=0

    if (tone_control<0):
        tone_control=0.

    # polynomial terms
    coef = empty(dord+1,dtype='float64')
    norm = empty(dord+1,dtype='float64')

    wth0 = (1./error).astype('float64')
    s0 = dot(wth0,wth0)
    wth0 /= sqrt(s0)

    cn = (signal*wth0).astype('float64')
    coef[0] = dot(cn,wth0); cn0 = coef[0]; norm[0] = 1.
    cn -= coef[0]*wth0
    vcn = 1.

    # sin's and cosin's for later
    tt = 2*pi*time.astype('float64')
    sinx,cosx = sin(tt*f1)*wth0,cos(tt*f1)*wth0
    sinx_step,cosx_step = sin(tt*df),cos(tt*df)
    sinx_back,cosx_back = -sin(tt*df/2.),cos(tt*df/2)
    sinx_smallstep,cosx_smallstep = sin(tt*df/freq_zoom),cos(tt*df/freq_zoom)

    npar=2*nharm
    hat_matr = empty((npar,numt),dtype='float64')
    hat0 = empty((npar,dord+1),dtype='float64')
    hat_hat = empty((npar,npar),dtype='float64')
    soln = empty(npar,dtype='float64')
    psd = zeros(numf,dtype='float64')

    # detrend the data and create the orthogonal detrending basis
    if (dord>0):
        wth = empty((dord+1,numt),dtype='float64')
        wth[0,:] = wth0
    else:
        wth = wth0

    for i in range(detrend_order):
        f = wth[i,:]*tt/(2*pi)
        for j in range(i+1):
            f -= dot(f,wth[j,:])*wth[j,:]
        norm[i+1] = sqrt(dot(f,f)); f /= norm[i+1]
        coef[i+1] = dot(cn,f)
        cn -= coef[i+1]*f
        wth[i+1,:] = f
        vcn += (f/wth0)**2


    chi0 = dot(cn,cn)
    varcn = chi0/(numt-1-dord)
    psdmin *= 2*varcn

    Tr = array(0.,dtype='float64')
    ifreq = array(0,dtype='int32')
    lambda0 = array(lambda0/s0,dtype='float64')
    lambda0_range = 10**array(lambda0_range,dtype='float64')/s0


    vars=['numt','numf','nharm','detrend_order','psd','cn','wth','sinx','cosx','sinx_step','cosx_step','sinx_back','cosx_back','sinx_smallstep','cosx_smallstep','hat_matr','hat_hat','hat0','soln','chi0','freq_zoom','psdmin','tone_control','lambda0','lambda0_range','Tr','ifreq']

    lomb_scargle(numt, numf, nharm, detrend_order, psd, cn, wth, sinx,
                 cosx, sinx_step, cosx_step, sinx_back, cosx_back,
                 sinx_smallstep, cosx_smallstep, hat_matr, hat_hat, hat0,
                 soln, chi0, freq_zoom, psdmin, tone_control, lambda0,
                 lambda0_range, Tr, ifreq)

    hat_hat /= s0
    ii = arange(nharm,dtype='int32')
    soln[0:nharm] /= (1.+ii)**2; soln[nharm:] /= (1.+ii)**2
    if (detrend_order>=0):
        hat_matr0 = outer(hat0[:,0],wth0)
    for i in range(detrend_order):
        hat_matr0 += outer(hat0[:,i+1],wth[i+1,:])


    modl = dot(hat_matr.T,soln); modl0 = dot(hat_matr0.T,soln)
    coef0 = dot(soln,hat0)
    coef -= coef0
    if (detrend_order>=0):
        hat_matr -= hat_matr0

    out_dict={}
    out_dict['chi0'] = chi0*s0
    if (return_model):
        if (dord>0):
            out_dict['trend'] = dot(coef,wth)/wth0
        else:
            out_dict['trend'] = coef[0] + 0*wth0
        out_dict['model'] = modl/wth0 + out_dict['trend']

    j = psd.argmax()
    freq = f1+df*j + (ifreq/freq_zoom - 1/2.)*df
    tt = (time*freq) % 1. ; s =tt.argsort()
    out_dict['freq'] = freq
    out_dict['s0'] = s0
    out_dict['chi2'] = (chi0 - psd[j])*s0
    out_dict['psd'] = psd[j]*0.5/varcn
    out_dict['lambda0'] = lambda0*s0
    out_dict['gcv_weight'] = (1-3./numt)/Tr
    out_dict['trace'] = Tr
    out_dict['nu0'] = numt - npar
    npars = (1-Tr)*numt/2
    out_dict['nu'] = numt-npars
    out_dict['npars'] = npars

    A0, B0 = soln[0:nharm],soln[nharm:]
    hat_hat /= outer( hstack(((1.+ii)**2,(1.+ii)**2)),hstack(((1.+ii)**2,(1.+ii)**2)) )
    err2 = diag(hat_hat)
    vA0, vB0 = err2[0:nharm], err2[nharm:]
    covA0B0 = hat_hat[(ii,nharm+ii)]

    if (return_model):
        vmodl = vcn/s0 + dot( (hat_matr/wth0).T, dot(hat_hat, hat_matr/wth0) )
        vmodl0 = vcn/s0 + dot( (hat_matr0/wth0).T, dot(hat_hat, hat_matr0/wth0) )
        out_dict['model_error'] = sqrt(diag(vmodl))
        out_dict['trend_error'] = sqrt(diag(vmodl0))

    amp = sqrt(A0**2+B0**2)
    damp = sqrt( A0**2*vA0 + B0**2*vB0 + 2.*A0*B0*covA0B0 )/amp
    phase = arctan2( B0,A0 )
    rel_phase = phase - phase[0]*(1.+ii)
    rel_phase = arctan2( sin(rel_phase),cos(rel_phase) )
    dphase = 0.*rel_phase
    for i in range(nharm-1):
        j=i+1
        v = array([-A0[0]*(1.+j)/amp[0]**2,B0[0]*(1.+j)/amp[0]**2,A0[j]/amp[j]**2,-B0[j]/amp[j]**2])
        jj=array([0,nharm,j,j+nharm])
        m = hat_hat[ix_(jj,jj)]
        dphase[j] = sqrt( dot(dot(v,m),v) )

    out_dict['amplitude'] = amp
    out_dict['amplitude_error'] = damp
    out_dict['rel_phase'] = rel_phase
    out_dict['rel_phase_error'] = dphase
    out_dict['time0'] = -phase[0]/(2*pi*freq)

    ncp = norm.cumprod()
    out_dict['trend_coef'] = coef/ncp
    out_dict['cn0'] = out_dict['trend_coef'][0] - cn0
    out_dict['trend_coef_error'] = sqrt( ( 1./s0 + diag(dot(hat0.T,dot(hat_hat,hat0))) )/ncp**2 )
    out_dict['cn0_error'] = out_dict['trend_coef_error'][0]

    prob = fdist.sf( 0.5*(numt-1.-dord)*(1.-out_dict['chi2']/out_dict['chi0']), 2,numt-1-dord )
    out_dict['signif'] = lprob2sigma(log(prob))

    return 0.5*psd/varcn,out_dict
