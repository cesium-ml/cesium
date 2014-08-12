#! /usr/bin/env python
# this is Nat's code copied over from the feature_extract project on August 3rd 2008, but I copied over nat's original svn upload, not Dan's modification (the modifications did not apply to this project)

from __future__ import division
from numpy import *

from lomb_scargle import lprob2sigma

def chi2sigma(chi0,chi1,nu0,nharm):
    from scipy.stats import betai
    from scipy.special import betaln

    nu1 = nu0 - 2.*nharm
    dfn = nu0-nu1
    dfd = nu1
    sigma = 0.
    if (dfn>0 and dfd>0 and chi0>chi1):
        fstat = (chi0/chi1-1.)*dfd/dfn
        prob = betai( dfd/2., dfn/2., dfd/(dfd+dfn*fstat) )
        if (dfd<=0 or dfn<=0): lprob=0.
        elif (chi1==0): lprob=-999.
        elif (prob==0): lprob = 0.5*dfd*log( dfd/(dfd+dfn*fstat) )-log(dfd/2.)-betaln(dfd/2.,dfn/2.)
        else: lprob = log(prob)
        sigma = lprob2sigma(lprob)

    return sigma


def pre_whiten(time, signal, freq, delta_time=[], signal_err=[], dof=-999, 
nharm_min=4, nharm_max=20):
    """Generates a harmonic fit to data (time,signal) with at most 
       nharm_max harmonics relative to the fundamental frequency freq.  
       Report statistics for nharm_min of them.
    """
    n0 = len(time)
    if (dof==-999 or dof>n0): dof=n0

    A0 = zeros(nharm_max,dtype=float)
    dA0 = zeros(nharm_max,dtype=float)
    B0 = zeros(nharm_max,dtype=float)
    dB0 = zeros(nharm_max,dtype=float)
    pha = zeros(nharm_max,dtype=float)

    # if data error not given, assume all are unity
    if (signal_err==[]):
      wt = ones(n0,dtype=float)
    else:
      wt = 1./signal_err**2;
      wt[signal_err<=0]=1.

    # if delta_time not given, assume 0
    do_sync=True
    if (delta_time==[]): 
      do_sync=False
      delta_time = zeros(n0, dtype=float)

    sync_func = lambda x: 1.
    if (do_sync): 
      sync_func = lambda x: (1.e-99 + sin(pi*x))/(1.e-99 + pi*x)

    x = 2*pi*freq*time
    cn = 1.*signal

    # just in case it wasn't already subtracted away
    s0 = sum(wt)
    mn = sum(cn*wt) / s0
    cn_offset = mn
    cn -= cn_offset
    dof = dof - 1.

    # initial chi^2 value for constant fit
    nu0 = dof
    chi0 = sum( cn**2*wt )

    #
    n_grid = (1+nharm_max)*20
    x_grid = 2*pi*arange(n_grid,dtype=float)/(1.*n_grid)
    modls = zeros([nharm_max,n_grid],dtype=float)
    modlc = zeros([nharm_max,n_grid],dtype=float)
    modl0 = zeros(n_grid,dtype=float)
    vmodl0 = zeros(n_grid,dtype=float)

    #
    # do the dirty work, fit for the sinusoid amplitudes and phases
    # modulus   cn = A*sin(x+pha) , of A0*sin(x)+B0*cos(x)
    # 
    chi1_last = chi0
    stop = 0
    for i in range(nharm_max):

        j = i+1

        synct = sync_func(freq*j*delta_time)
        sinx = sin(j*x)*synct
        cosx = cos(j*x)*synct

        ts2 = 2.*sum( sinx*cosx*wt )
        tc2 = sum( (cosx**2-sinx**2)*wt )

        x0 = 0.5*arctan2(ts2, tc2)/j
        sinomtau = sin(j*x0)
        cosomtau = cos(j*x0)
        sin2omtau = 2.*sinomtau*cosomtau;
        cos2omtau = cosomtau**2 - sinomtau**2

        tmp = tc2*cos2omtau + ts2*sin2omtau;
        tc2 = 0.5*(s0+tmp);
        ts2 = 0.5*(s0-tmp);

        tmp = sinx
        sinx = tmp*cosomtau-cosx*sinomtau
        cosx = cosx*cosomtau + tmp*sinomtau

        sh = sum( cn*sinx*wt )
        ts1 = sum( sinx*wt )

        ch = sum( cn*cosx*wt ) 
        tc1 = sum( cosx*wt )

        A0[i] = sh / ts2; dA0[i] = 1./sqrt(ts2);
        B0[i] = ch / tc2; dB0[i] = 1./sqrt(tc2);
        cn0 = ( A0[i]*ts1 + B0[i]*tc1 ) / ( ts1**2/ts2 + tc1**2/tc2 - s0 );
        A0[i] -= cn0*ts1/ts2;
        B0[i] -= cn0*tc1/tc2;

        pha[i] = arctan2(B0[i],A0[i]) - j*x0

        cn_test = cn - cn0 - ( A0[i]*sinx + B0[i]*cosx ) * synct

        chi1 = sum( cn_test**2*wt ) # chi^2 for harmonic component removed
        if (chi1 > chi1_last*(nu0-2*j)/(nu0-2*(j-1)) or j==nharm_max): 
            stop=1
            nharm = i
            sigma = chi2sigma(chi0,chi1,nu0,nharm)

        if (stop==1 and j>nharm_min):	# calculate >= nharm_min harmonics

            A0 = A0[:i]
            dA0 = dA0[:i]
            B0 = B0[:i]
            dB0 = dB0[:i]
            pha = pha[:i]
            modls = modls[:i,:]
            modlc = modlc[:i,:]
            break

        chi1_last = chi1
        cn = cn_test
        cn_offset += cn0

        modls[i,:] = sin(j*(x_grid-x0))
        modlc[i,:] = cos(j*(x_grid-x0))
        modl0 += A0[i]*modls[i,:] + B0[i]*modlc[i,:]
        vmodl0 += (dA0[i]*modls[i,:])**2 + (dB0[i]*modlc[i,:])**2


    # find light curve extremum for bookkeeping
    pk = argmax(modl0*modl0)
    # report phases relative to extremum, time' = time - time_offset
    time_offset = - x_grid[pk] / (2*pi*freq)
    for i in range(nharm):
        pha[i] = pha[i] - (1+i)*x_grid[pk]
        pha[i] = arctan2( sin(pha[i]),cos(pha[i]) )

    x_grid = x_grid-x_grid[pk]
    x_grid = arctan2(sin(x_grid),cos(x_grid))
    i0 = argmin(x_grid)
    i1 = argmax(x_grid)

    #
    # error propagation
    #
    A = sqrt( A0**2 + B0**2 )
    dA = sqrt( (A0*dA0)**2 + (B0*dB0)**2 ) / A
    dpha = 1./(1+(A0/B0)**2) * sqrt( (dA0/B0)**2+(A0*dB0/B0**2)**2 )

    # use the chi^2 values to get a better (more conservative) error estimate
    fac=1.
    sigma0 = A[0]/dA[0]
    if (sigma0>sigma and sigma>0): fac = sigma0/sigma
    # now apply it
    dA = fac*dA
    vmodl0 = fac**2*vmodl0
    dpha = fac*dpha

    #
    # get flux extrema
    #
    mn = argmin(modl0)
    fmin = modl0[mn]
    vfmin = vmodl0[mn]
    mx = argmax(modl0)
    fmax = modl0[mx]
    vfmax = vmodl0[mx]
    peak2peak_flux = fmax - fmin
    peak2peak_flux_error = sqrt( vfmin+vfmax )

    #
    # set flux offset and sign for moment calculation below
    #
    s0 = 0.5*(modl0[i0]+modl0[i1])
    vs0 = 0.25*(vmodl0[i0]+vmodl0[i1])

    #import Gnuplot
    #import time
    #plotobj = Gnuplot.Gnuplot()
    #plotobj.xlabel('Time (s)')
    #plotobj.ylabel('Folded Light Curve')
    #plotobj('unset logscale x')
    #plotobj.plot(Gnuplot.Data(x_grid/(2*pi*freq),modl0-s0))
    #time.sleep(3)

    niter=10
    for k in range(niter):
        if (k==0): window = 1.

        nmom = 4	# number of moments requested (don't change)
        mu = zeros(1+nmom,dtype=float)
        vmu = zeros(1+nmom,dtype=float)
        x0=0.
        norm=1.
        for j in range(1+nmom):
            xfac = pow(x_grid-x0,j)*window
            mu[j] = -s0*mean(xfac)/norm
            vmu[j] = vs0*(mean(xfac)/norm)**2
            for k in range(nharm):
                mas = mean( xfac*modls[k,:] )
                mac = mean( xfac*modlc[k,:] )
                mu[j] = mu[j] + (A0[k]*mas + B0[k]*mac)/norm
                vmu[j] = vmu[j] + (dA0[k]*mas/norm)**2 + (dB0[k]*mac/norm)**2
            if (j==0 and abs(mu[0])>0): norm = mu[0]
            if (j==1): x0 = mu[1]
            if (j==2): window = 1*( abs(x_grid-x0) < 3.*sqrt(mu[2]) )
        if (sum(window)==n_grid): break

    # defaults
    moments = array([0.,0.5/freq,0.,0.])
    dmoments = array([1.,0.5/freq,1.,1.])
    if (abs(mu[0])>0 and mu[2]>0):
        av = x0
        var = mu[2]
        stdev = sqrt(var)
        skewness = mu[3] / mu[2]**1.5
        kurtosis = mu[4] / mu[2]**2 - 3.
        # error propagation is approximate
        dav = sqrt(vmu[1])
        dstdev = 0.5*sqrt(vmu[2]/mu[2])
        dskewness = sqrt( vmu[3] ) / var**1.5
        dkurtosis = sqrt( vmu[4] ) / var**2.

        moments = array([av,stdev/(2*pi*freq),skewness,kurtosis])
        dmoments = array([dav,dstdev/(2*pi*freq),dskewness,dkurtosis])

    #
    # put it all in a dictionary
    #
    freqs = freq*(1+arange(nharm_min))
    #out_dict = { 'signif': sigma, 'peak2peak_flux': peak2peak_flux, 
    #             'peak2peak_flux_error': peak2peak_flux_error, 'amplitude': A[:nharm_min], 
    #             'freq': freqs, 'amplitude_error': dA[:nharm_min], 'rel_phase': pha[:nharm_min],
    #             'rel_phase_error': dpha[:nharm_min], 'moments': moments, 
    #             'moments_err': dmoments, 'nharm': nharm}

    # 20080508: dstarr wants verbosely labeled dict:
    out_dict = { 'signif': sigma, 'peak2peak_flux': peak2peak_flux, 
                 'peak2peak_flux_error': peak2peak_flux_error, 'nharm': nharm}

    for i in xrange(len(moments)):
        out_dict['moments_' + str(i)] = moments[i]
    for i in xrange(len(dA[:nharm_min])):
        out_dict['amplitude_error_' + str(i)] = dA[:nharm_min][i]
    for i in xrange(len(dmoments)):
        out_dict['moments_err_' + str(i)] = dmoments[i]
    for i in xrange(len(dpha[:nharm_min])):
        out_dict['rel_phase_error_' + str(i)] = dpha[:nharm_min][i]
    for i in xrange(len(A[:nharm_min])):
        out_dict['amplitude_' + str(i)] = A[:nharm_min][i]
    for i in xrange(len(pha[:nharm_min])):
        out_dict['rel_phase_' + str(i)] = pha[:nharm_min][i]
    for i in xrange(len(freqs)):
        out_dict['freq_' + str(i)] = freqs[i]

    out_dict = { 'signif': sigma, 'peak2peak_flux': peak2peak_flux, 
'peak2peak_flux_error': peak2peak_flux_error, 'amplitude': A[:nharm_min], 
'freq': freqs, 'amplitude_error': dA[:nharm_min], 'rel_phase': pha[:nharm_min],
'rel_phase_error': dpha[:nharm_min], 'moments': moments, 
'moments_err': dmoments, 'nharm': nharm, 'time_offset': time_offset,'y_offset':cn_offset}

    return cn, out_dict
