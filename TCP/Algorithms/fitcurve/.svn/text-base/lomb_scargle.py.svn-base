#! /usr/bin/env python

from __future__ import division
from numpy import *
from numpy.random import normal
from scipy.stats import norm,betai
from scipy.special import betaln
from pylab import where
from scipy import weave

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


def peak2sigma(psdpeak,n0):
    """ translates a psd peak height into a multi-trial NULL-hypothesis probability
    NOTE: dstarr replaces '0' with 0.000001 to catch float-point accuracy bugs
          Which I otherwise stumble into.
    """

    # Student's-T
    prob0 = betai( 0.5*n0-2.,0.5,(n0-1.)/(n0-1.+2.*psdpeak) )
    if (0.5*n0-2.<=0.000001):
      lprob0=0.
    elif ( (n0-1.)/(n0-1.+2.*psdpeak) <=0.000001 ):
      lprob0=-999.
    elif (prob0==0):
        lprob0=(0.5*n0-2.)*log( (n0-1.)/(n0-1.+2.*psdpeak)
) - log(0.5*n0-2.) - betaln(0.5*n0-2.,0.5)
    else: lprob0=log(prob0)

    # ballpark number of independent frequencies
    #  (Horne and Baliunas, eq. 13)
    horne = long(-6.362+1.193*n0+0.00098*n0**2.)
    if (horne <= 0): horne=5

    if (lprob0>log(1.e-4) and prob0>0):
	# trials correction, monitoring numerical precision
        lprob = log( 1. - exp( horne*log(1-prob0) ) )
    elif (lprob0+log(horne)>log(1.e-4) and prob0>0):
        lprob = log( 1. - exp( -horne*prob0 ) )
    else:
        lprob = log(horne) + lprob0

    sigma = lprob2sigma(lprob)

    return sigma


def get_peak_width(psd,imax):
    pmax = psd[imax]
    i = 0
    while ( (psd[imax-i:imax+1+i]>(pmax/2.)).sum()/(1.+2*i)==1 ):
        w = 1.+2*i
        i+=1
    return w


# New as of 20101120: (with run_lomb14.py changes):
def lomb(time, signal, error, f1, df, numf, fit_mean=True, fit_slope=False, subtract_mean=True):
    """
    C version of lomb_scargle

    Inputs:
        time: time vector
        signal: data vector
        error: uncertainty on signal
        df: frequency step
        numf: number of frequencies to consider

    Output:
        psd: power spectrum on frequency grid: f1,f1+df,...,f1+numf*df
    """
    numt = len(time)

    wth = (1./error).astype('float64')
    s0 = dot(wth,wth)
    wth /= sqrt(s0)

    if (fit_mean==True):
        subtract_mean=True

    if (fit_slope==True):
        fit_mean=True
        subtract_mean=True

    cn = (signal*wth).astype('float64')
    if (subtract_mean==True):
        cn -= dot(cn,wth)*wth

    tt = 2*pi*time.astype('float64')
    sinx0, cosx0 = sin(df*tt), cos(df*tt)
    sinx, cosx = sin(f1*tt)*wth, cos(f1*tt)*wth

    if (fit_slope==True):
        tt *= wth
        tt -= dot(tt,wth)*wth
        tt /= tt.max()
        s1 = dot(tt,tt)
        cn -= dot(tt,cn)*tt/s1

    numf = int(numf)
    psd = empty(numf,dtype='float64')

    if (subtract_mean==False):
        vcn = 1./s0
    else:
        vcn = var(cn)

    fit_mean = int(fit_mean)
    lomb_scargle_support = """
      inline double SQR(double a) {
        return (a == 0.0 ? 0.0 : a*a);
      }

      inline void update_sincos (long int numt, double *sinx0_ptr, double *cosx0_ptr, double *sinx_ptr, double *cosx_ptr) {
          double tmp,*sinx0 = sinx0_ptr, *cosx0 = cosx0_ptr, *sinx = sinx_ptr, *cosx = cosx_ptr;
          for (unsigned long i=0;i<numt;i++,sinx0++,cosx0++,sinx++,cosx++) {
              tmp = *sinx;
              *sinx = *cosx0*tmp + *sinx0**cosx;
              *cosx = -*sinx0*tmp + *cosx0**cosx;
          }
      }
    """

    lomb_scargle_codeB = """

      inline double lomb_scargle(double *cn_ptr, double *wt_ptr, double *sinx_ptr, double *cosx_ptr, long int numt, int fit_mean) {

        double ts1=0.,tc1=0.,s2=0.,c2=0.,sh=0.,ch=0.,tc2,ts2;
        double omtau;
        double tmp,px,cosomtau,sinomtau,cos2omtau,sin2omtau;

        double *wt = wt_ptr, *cn = cn_ptr;
        double *sinx = sinx_ptr, *cosx = cosx_ptr;
        double norm_sin,norm_cos,cn0=0.;

        for (unsigned long i=0;i<numt;i++, wt++, cn++, sinx++, cosx++) {
          ts1 += *sinx**wt;
          s2 += *cosx*(*sinx);
          tc1 += *cosx**wt;
          c2 += SQR(*cosx);
          sh += *sinx*(*cn);
          ch += *cosx*(*cn);
        }
        s2 *= 2.; c2 = 2*c2 - 1.;

        omtau = atan2(s2,c2)/2;
        sinomtau = sin(omtau);
        cosomtau = cos(omtau);

        sin2omtau = 2.*sinomtau*cosomtau;
        cos2omtau = 2.*SQR(cosomtau) - 1.;

        tmp = c2*cos2omtau + s2*sin2omtau;
        tc2 = 0.5*(1.+tmp);
        ts2 = 0.5*(1.-tmp);

        tmp = ts1;
        ts1 = cosomtau*tmp - sinomtau*tc1;
        tc1 = sinomtau*tmp + cosomtau*tc1;

        tmp = sh;
        sh = cosomtau*tmp - sinomtau*ch;
        ch = sinomtau*tmp + cosomtau*ch;

        norm_sin = sh/ts2;
        norm_cos = ch/tc2;

        if (fit_mean) {
          cn0 = ( norm_sin*ts1 + norm_cos*tc1 ) / ( SQR(ts1)/ts2 + SQR(tc1)/tc2 - 1. );
          norm_sin -= cn0*ts1/ts2;
          norm_cos -= cn0*tc1/tc2;
        }

        px = SQR(norm_sin)*ts2 + SQR(norm_cos)*tc2 - SQR(cn0);
        if (tc2<=0 || ts2<=0) px = 0.;

        return px;
      }
    """

    lomb_scargle_codeA = """

      inline double lomb_scargle_linear(double *tt_ptr, double *cn_ptr, double *wt_ptr, double *sinx_ptr, double *cosx_ptr, double s1, long int numt) {

        double ts1=0.,tc1=0.,s2=0.,c2=0.,sh=0.,ch=0.,ts=0.,tc=0.,tc2,ts2;
        double omtau;
        double tmp,px,cosomtau,sinomtau,cos2omtau,sin2omtau;

        double *wt = wt_ptr, *cn = cn_ptr, *tt = tt_ptr;
        double *sinx = sinx_ptr, *cosx = cosx_ptr;
        double cn0,cn1;

        for (unsigned long i=0;i<numt;i++, wt++, tt++, cn++, sinx++, cosx++) {
          ts1 += *sinx**wt;
          s2 += *cosx*(*sinx);
          tc1 += *cosx**wt;
          c2 += SQR(*cosx);
          sh += *sinx*(*cn);
          ch += *cosx*(*cn);
          ts += *sinx*(*tt);
          tc += *cosx*(*tt);
        }
        s2 *= 2.; c2 = 2*c2 - 1.;

        omtau = atan2(s2,c2)/2;
        sinomtau = sin(omtau);
        cosomtau = cos(omtau);

        sin2omtau = 2.*sinomtau*cosomtau;
        cos2omtau = 2.*SQR(cosomtau) - 1.;

        tmp = c2*cos2omtau + s2*sin2omtau;
        tc2 = 0.5*(1.+tmp);
        ts2 = 0.5*(1.-tmp);

        tmp = ts1;
        ts1 = cosomtau*tmp - sinomtau*tc1;
        tc1 = sinomtau*tmp + cosomtau*tc1;

        tmp = ts;
        ts = cosomtau*tmp - sinomtau*tc;
        tc = sinomtau*tmp + cosomtau*tc;

        tmp = sh;
        sh = cosomtau*tmp - sinomtau*ch;
        ch = sinomtau*tmp + cosomtau*ch;

        tmp = 2*tc*tc1*ts*ts1 + (s1*ts2 - SQR(ts))*SQR(tc1) + (s1*tc2 - SQR(tc))*SQR(ts1) - ((s1*tc2 - SQR(tc))*ts2 - tc2*SQR(ts));
        cn0 = ch*(tc*ts*ts1 + (s1*ts2 - SQR(ts))*tc1) + sh*(tc*ts*tc1 + (s1*tc2 - SQR(tc))*ts1);
        cn0 /= tmp;
        cn1 = ch*(ts*tc1*ts1 - tc*SQR(ts1) + tc*ts2) + sh*(tc*tc1*ts1 - ts*SQR(tc1) + ts*tc2);
        cn1 /= tmp;

        px = SQR(sh-cn0*ts1-cn1*ts)/ts2 + SQR(ch-cn0*tc1-cn1*tc)/tc2 - SQR(cn0) - s1*SQR(cn1);
        if (tc2<=0 || ts2<=0) px = 0.;

        return px;
      }
    """

    lomb_code_A = """
      for (unsigned long j=0;j<numf;j++,psd++) {
          *psd = lomb_scargle_linear(tt,cn,wth,sinx,cosx,s1,numt);
          update_sincos (numt, sinx0, cosx0, sinx, cosx);
      }
    """

    lomb_code_B = """
      for (unsigned long j=0;j<numf;j++,psd++) {
          *psd = lomb_scargle(cn,wth,sinx,cosx,numt,fit_mean);
          update_sincos (numt, sinx0, cosx0, sinx, cosx);
      }
    """

    if (fit_slope==True):
        weave.inline(lomb_code_A,\
          ['cn','wth','tt','numt','numf','psd','s1','sinx0','cosx0','sinx','cosx'],\
          support_code = lomb_scargle_support+lomb_scargle_codeA,force=0)
    else:
        weave.inline(lomb_code_B,\
          ['cn','wth','numt','numf','psd','sinx0','cosx0','sinx','cosx','fit_mean'],\
          support_code = lomb_scargle_support+lomb_scargle_codeB,force=0)

    return 0.5*psd/vcn;


def lomb__pre20101120(time, signal, wt, df, numf ):
    """
    C version of lomb_scargle
    Constructs a periodogram from frequency df to frequency numf * df

    Inputs:
        time: time vector
        signal: data vector
        wt: weights vector = 1/uncertainty^2
        df: frequency step
        numf: number of frequencies to consider

    Output:
        psd: power spectrum on frequency grid
    """
    numt = len(time)

    wt = wt.astype('float64')

    s0 = wt.sum()
    cn = signal.astype('float64') - ( signal*wt ).sum() / s0
    var = ( cn**2*wt ).sum()/(numt-1.)
    s0 = array([s0]).astype('float64')

    # make times manageable (Scargle periodogram is time-shift invariant)
    tt = 2*pi*( time.astype('float64')-time.min() )

    #df = array([df],dtype='float64')
    df = float64(df)
    numf = int(numf)
    psd = empty(numf,dtype='float64')
    #numf = array([numf],dtype='float64')

    # work space
    sinx0,cosx0,sinx,cosx = empty((4,numt),dtype='float64')

    lomb_scargle = """
      inline double SQR(double a) {
        return (a == 0.0 ? 0.0 : a*a);
      }

      inline void initialize_sincos (long int numt, double *tt_ptr, double *sinx0_ptr, double *cosx0_ptr, double *sinx_ptr, double *cosx_ptr, double df) {
          double *sinx0 = sinx0_ptr, *cosx0 = cosx0_ptr, *tt = tt_ptr;
          double *sinx = sinx_ptr, *cosx = cosx_ptr;
          for (unsigned long i=0;i<numt;i++,tt++,sinx0++,cosx0++,sinx++,cosx++) {
              *sinx0 = sin(*tt*df);
              *cosx0 = cos(*tt*df);
              *sinx = *sinx0; *cosx = *cosx0;
          }
      }

      inline void update_sincos (long int numt, double *sinx0_ptr, double *cosx0_ptr, double *sinx_ptr, double *cosx_ptr) {
          double tmp;
          double *sinx0 = sinx0_ptr, *cosx0 = cosx0_ptr, *sinx = sinx_ptr, *cosx = cosx_ptr;
          for (unsigned long i=0;i<numt;i++,sinx0++,cosx0++,sinx++,cosx++) {
              tmp = *sinx;
              *sinx = *cosx0*tmp + *sinx0**cosx;
              *cosx = -*sinx0*tmp + *cosx0**cosx;
          }
      }

      inline double lomb_scargle(double *cn_ptr, double *wt_ptr, double *sinx_ptr, double *cosx_ptr, double s0, long int numt) {

        double ts1=0.,tc1=0.,s2=0.,c2=0.,sh=0.,ch=0.,tc2,ts2;
        double omtau;
        double tmp,px,cosomtau,sinomtau,cos2omtau,sin2omtau;

        double *wt = wt_ptr, *cn = cn_ptr;
        double *sinx = sinx_ptr, *cosx = cosx_ptr;
        double norm,norm_sin,norm_cos,cn0;

        for (unsigned long i=0;i<numt;i++, wt++, cn++, sinx++, cosx++) {
          ts1 += tmp = *sinx**wt;
          s2 += *cosx*tmp;
          tc1 += tmp = *cosx**wt;
          c2 += *cosx*tmp;
          tmp = *cn**wt;
          sh += *sinx*tmp;
          ch += *cosx*tmp;
        }
        s2 *= 2.; c2 = 2*c2 - s0;

        omtau = atan2(s2,c2)/2;
        sinomtau = sin(omtau);
        cosomtau = cos(omtau);

        sin2omtau = 2.*sinomtau*cosomtau;
        cos2omtau = 2.*SQR(cosomtau) - 1.;

        tmp = c2*cos2omtau + s2*sin2omtau;
        tc2 = 0.5*(s0+tmp);
        ts2 = 0.5*(s0-tmp);

        tmp = ts1;
        ts1 = cosomtau*tmp - sinomtau*tc1;
        tc1 = sinomtau*tmp + cosomtau*tc1;

        tmp = sh;
        sh = cosomtau*tmp - sinomtau*ch;
        ch = sinomtau*tmp + cosomtau*ch;

        norm_sin = sh/ts2;
        norm_cos = ch/tc2;

        cn0 = ( norm_sin*ts1 + norm_cos*tc1 ) / ( SQR(ts1)/ts2 + SQR(tc1)/tc2 - s0 );
        norm_sin -= cn0*ts1/ts2;
        norm_cos -= cn0*tc1/tc2;

        px = SQR(norm_sin)*ts2 + SQR(norm_cos)*tc2 - s0*SQR(cn0);
        if (tc2<=0 || ts2<=0) px = 0.;

        return px;
      }
    """

    lomb_code = """
      initialize_sincos (numt,tt,sinx0,cosx0,sinx,cosx,df);
      *psd = lomb_scargle(cn,wt,sinx,cosx,*s0,numt);
      psd++;

      for (unsigned long j=1;j<numf;j++,psd++) {
          update_sincos (numt, sinx0, cosx0, sinx, cosx);
          *psd = lomb_scargle(cn,wt,sinx,cosx,*s0,numt);
      }
    """

    weave.inline(lomb_code,\
      ['cn','wt','tt','numt','numf','psd','s0','df','sinx0','cosx0','sinx','cosx'],\
      support_code = lomb_scargle)
    #import pdb; pdb.set_trace()
    #print

    return 0.5*psd/var;



def lomb__numpy20100913efficent(time,signal,wt=[],freqin=[]):
    """ run lomb_scargle on the graphics card
      requires frequency grid as input, returns psd

    Nat made this numpy-optimal version on 20100911.
    """
    numt = len(time)

    wt = wt.astype('float64')
    freqin = freqin.astype('float64')

    s0 = wt.sum()
    cn = signal.astype('float64') - (signal*wt).sum()/s0
    var = ( cn**2*wt ).sum()/(numt-1.)

    tt = 2*pi*( time.astype('float64')-time.min() )

    numf = len(freqin)
    ts1 = zeros(numf,'float64'); tc1 = zeros(numf,'float64')
    s2 = zeros(numf,'float64'); c2 = zeros(numf,'float64')
    sh = zeros(numf,'float64'); ch = zeros(numf,'float64')

    for i in xrange(numt):
      x = freqin * tt[i]
      sinx, cosx = sin(x), cos(x)
      tmp = wt[i]*sinx;
      ts1 += tmp;
      s2 += tmp*cosx;
      tmp = wt[i]*cosx
      tc1 += tmp
      c2 += tmp*cosx;
      tmp = cn[i]*wt[i]
      sh += tmp*sinx; ch += tmp*cosx

    s2 *= 2.
    c2 = 2.*c2 - s0

    omtau = 0.5*arctan2(s2,c2)
    sinomtau = sin(omtau); cosomtau = cos(omtau)

    tmp = ts1;
    ts1 = cosomtau*tmp - sinomtau*tc1;
    tc1 = sinomtau*tmp + cosomtau*tc1;

    tmp = sh;
    sh = cosomtau*tmp - sinomtau*ch;
    ch = sinomtau*tmp + cosomtau*ch;

    tmp = c2*cos(2.*omtau) + s2*sin(2.*omtau)
    tc2 = 0.5*(s0+tmp)
    ts2 = 0.5*(s0-tmp)

    norm_sin = sh/ts2;
    norm_cos = ch/tc2;

    cn0 = ( norm_sin*ts1 + norm_cos*tc1 ) / ( ts1**2/ts2 + tc1**2/tc2 - s0 );

    norm_sin -= cn0*ts1/ts2;
    norm_cos -= cn0*tc1/tc2;

    return 0.5/var *(norm_sin**2*ts2 + norm_cos**2*tc2 - s0*cn0**2)


### OBSOLETE: 20100912: Nat replaced this with a more optimal numpy version and an even more optimal C/weave version.
def lomb__old_pre20100912(time, signal, delta_time=[], signal_err=[], freqin=[], fap=0.01, multiple=0, noise=0, verbosity=2, use_bayes=False, num_freq_max=10000):
#
# NAME:
#         lomb
#
# PURPOSE:
#         Compute the lomb-scargle periodogram of an unevenly sampled
#         lightcurve 
#
# CATEGORY:
#         time series analysis
#
# CALLING SEQUENCE:
#   psd, freq =  scargle(time,signal)
#
# INPUTS:
#         time: The times at which the time series was measured
#         signal: the corresponding count rates
#
# OPTIONAL INPUTS:
#         delta_time: exposure times (bin widths) centered around time 
#         signal_err: 1-sigma uncertainty on signal vector
#         freqin: frequencies for which the PSD values are desired
#         fap : false alarm probability desired
#               (see Scargle et al., p. 840, and signi
#               keyword). Default equal to 0.01 (99% significance)       
#         noise: PSD normalization, default assumes (chi^2/nu)^0.5 for a linear fit
#         multiple: number of Gaussian noise simulations for the FAP
#            power level. Default equal to 0 (i.e., no simulations).
#
# OUTPUTS:
#            psd: the psd-values corresponding to omega
#            freq: frequency of PSD
#
# OPTIONAL OUTPUTS:
#            signi : peak of the PSD
#            simsigni : PSD peak corresponding to the given 
#                    false alarm probabilities fap according to Gaussian
#                    noise simulations
#            psdpeak: array with the maximum peak for each simulation    
#
#
# KEYWORD PARAMETERS:
#         verbosity: print out debugging information if set
#
# MODIFICATION HISTORY:
#          Version 1.0, 1997, Joern Wilms IAAT
#          Version 1.1, 1998.09.23, JW: Do not normalize if variance is 0
#             (for computation of LSP of window function...)
#          Version 1.2, 1999.01.07, JW: force numf to be int
#          Version 1.3, 1999.08.05, JW: added omega keyword   
#          Version 1.4, 1999.08
#              KP: significance levels   
#              JW: pmin,pmax keywords
#          Version 1.5, 1999.08.27, JW: compute the significance levels
#               from the horne number of independent frequencies, and not from
#               numf
#          Version 1.6, 2000.07.27, SS and SB: added fast algorithm and FAP
#               according to white noise lc simulations.    
#          Version 1.7, 2000.07.28 JW: added debug keyword, sped up 
#               simulations by factor of four (use /slow to get old
#               behavior of the simulations)
#           Version 2.0 2004.09.01, Thomas Kornack rewritten in Python
#           Version 2.1 2008.04.11, Nat Butler added error propagation and allowed
#               for non-zero and variable time bins, altered output signi to be trials
#               significance of periodogram peak
#           Version 2.2 2009.11.17, Nat Butler added Bayesian term for width of periodogram
#               (Laplace approximation to posterior).  This now searches over a linear
#               frequency grid, with a present maximum number of bins.
#

    if verbosity>1: print('Starting Lomb (standard)...')

    signal = atleast_1d(signal).astype(double)
    time = atleast_1d(time).astype(double)

    n0 = len(time)

    # if data error not given, assume all are unity
    if (signal_err==[]):
      wt = ones(n0,dtype=float)
    else:
      wt = 1./atleast_1d(signal_err).astype(double)**2;
      wt[signal_err<=0] = 1.

    # if delta_time not given, assume 0
    do_sync=True
    if (delta_time==[]): 
      do_sync=False
      delta_time = zeros(n0, dtype=float)
    else:
      delta_time = atleast_1d(delta_time).astype(double)

    # make times manageable (Scargle periodogram is time-shift invariant)
    tt = time-min(time)
    ii = tt.argsort()
    tt = tt[ii]; cn = signal[ii]; wt=wt[ii];

    s0 = sum(wt)
    msignal = sum( cn*wt ) / s0
    cn -= msignal

    # defaults
    renorm=1
    if noise == 0: 
      renorm=0
      noise = sqrt( sum( cn**2*wt )/(n0-1) )

    # make times manageable (Scargle periodogram is time-shift invariant)
    tt = time-min(time)
    tt.sort()
    max_tt = tt[-1]

    # min.freq is 1/T, go a bit past that
    # initial max. freq guess: approx. to Nyquist frequency
    df = 0.1/max_tt
    fmin = 0.5/max_tt
    fmax = n0*fmin
    # refine the maximum frequency to be a bit higher
    dt = tt[1:] - tt[:-1]
    g=where(dt>0)
    if (len(g[0])>0):
      dt_min = dt[g].min()
      fmax = 0.5/dt_min

    # if omega is not given, compute it
    if (freqin==[]):
        numf = long( ceil( (fmax-fmin)/df ) )
        if (numf>num_freq_max):
            if (verbosity>1): print ("Warning: shrinking num_freq %d -> %d (num_freq_max)") % (numf,num_freq_max)
            numf = long(num_freq_max)
            #fmax = fmin + numf*df
            df = (fmax - fmin)/numf
        freqin = fmax - df*arange(numf,dtype=float)
        om = 2.*pi*freqin
    else:
        om = freqin*2*pi
        numf = len(om)

    # Bayes term in periodogram gets messy at frequencies lower than this
    om0 = pi/max_tt

    if (numf==0): multiple = 0

    if verbosity>1: print('Setting up periodogram...')

    # Periodogram   
    # Ref.: W.H. Press and G.B. Rybicki, 1989, ApJ 338, 277

    # finite bins leads to sinc function; sinc factors drop out if delta_time = const.
    # sinc(x) = sin(x*pi)/(x*pi)

    if (multiple > 0):
        if verbosity>1: print('Looping...')
        sisi=zeros([n0,numf], dtype=float)
        coco=zeros([n0,numf], dtype=float)

    # Eq. (6); s2, c2
    ts1 = zeros(numf, dtype=float)
    tc1 = zeros(numf, dtype=float)
    s1 = zeros(numf, dtype=float)
    s2 = zeros(numf, dtype=float)
    c2 = zeros(numf, dtype=float)
    # Eq. (5); sh and ch
    sh = zeros(numf, dtype=float)
    ch = zeros(numf, dtype=float)
    bayes_term = zeros(numf, dtype=float)

    sync_func = lambda x: 1.
    if (do_sync): 
      sync_func = lambda x: (1.e-99 + sin(pi*x))/(1.e-99 + pi*x)


    for i in range(numf):

       x = ( om[i]*tt ) % (2*pi)
       synct = sync_func(freqin[i]*delta_time)
       sinom = sin(x)*synct
       cosom = cos(x)*synct

       ts1[i] = sum( sinom*wt )
       tc1[i] = sum (cosom*wt )
       s1[i] = sum( synct**2*wt )
       s2[i] = 2.*sum( sinom*cosom*wt )
       c2[i] = sum( (cosom**2-sinom**2)*wt )
       sh[i] = sum( cn*sinom*wt )
       ch[i] = sum( cn*cosom*wt )

       if (multiple > 0):
            sisi[:,i]=sinom*wt
            coco[:,i]=cosom*wt

    # cleanup
    sinom = 0.
    cosom = 0.
    synct = 0.

    # Eq. (2): Definition -> tan(2omtau)
    # --- tan(2omtau)  =  s2 / c2
    omtau = arctan2(s2,c2)/2

    # cos(tau), sin(tau)
    cosomtau = cos(omtau)
    sinomtau = sin(omtau)

    tmp = 1.*ts1;
    ts1 = cosomtau*tmp - sinomtau*tc1;
    tc1 = sinomtau*tmp + cosomtau*tc1;

    tmp = 1.*sh;
    sh = cosomtau*tmp - sinomtau*ch;
    ch = sinomtau*tmp + cosomtau*ch;

    # Eq. (7); sum(cos(t-tau)**2)  and sum(sin(t-tau)**2)
    tmp = c2*cos(2.*omtau) + s2*sin(2.*omtau)
    tc2 = 0.5*(s1+tmp) # sum(cos(t-tau)**2)
    ts2 = 0.5*(s1-tmp) # sum(sin(t-tau)**2)

    norm_sin = sh/ts2;
    norm_cos = ch/tc2;
    cn0 = ( norm_sin*ts1 + norm_cos*tc1 ) / ( ts1**2/ts2 + tc1**2/tc2 - s0 );
    norm_sin -= cn0*ts1/ts2;
    norm_cos -= cn0*tc1/tc2;

    #amplitude = sqrt(norm_sin**2+norm_cos**2)
    #damplitude = sqrt(norm_sin**2/ts2+norm_cos**2/tc2)/amplitude*noise

    bayes_term = -0.5*log( s0*ts2*tc2 - tc1**2*ts2 - ts1**2*tc2 ) + 1.5*log(s0) - 0.5*log(4.) - log(freqin) + (log(freqin)).mean()

    # Eq. (3), modified
    px = norm_sin**2*ts2 + norm_cos**2*tc2 - cn0**2*s0

    # be careful here
    wh = (tc2<=0) | (ts2<=0)
    px[wh] = 0.

    # clean up
    tmp = 0.
    omtau = 0.
    s2 = 0.
    c2 = 0.
    if multiple <=0 :
      ts1 = 0.
      tc1 = 0.
      tc2 = 0.
      ts2 = 0.

    # correct normalization 
    psd = atleast_1d( 0.5*px/(noise**2) )

    if (use_bayes):
        g=where(om<om0)
        #bayes_term[g]=0.
        psd += bayes_term


    signi = 0.
    if (numf>0):
        if (use_bayes):
            j0 = psd.argmax()
            signi = peak2sigma( (psd-bayes_term)[j0],n0)
        else:
            signi = peak2sigma(psd.max(),n0)

    # --- RUN SIMULATIONS for multiple > 0
    simsigni=[]
    psdpeak=[]
    if multiple > 0:
        if verbosity>1: print('Running Simulations...')
        if (multiple*fap < 10): 
            print('WARNING: Number of iterations (multiple keyword) not large enough for false alarm probability requested (need multiple*FAP > 10 )')

        psdpeak = zeros(multiple, dtype=float)
        for m in range(multiple):
            if ((m+1)%100 == 0) and (verbosity>0):
                print "...working on %ith simulation. (%.2f Done)" % (m,m/multiple)

            # Gaussian noise simulation
            cn = normal(loc=0.0,scale=1.,size=n0)/sqrt(wt)
            msignal = sum( cn*wt ) / s0
            cn = cn-msignal # force OBSERVED count rate to zero
            if (renorm==0): noise = sqrt( sum( cn**2*wt )/(n0-1) )

            # Eq. (5); sh and ch
            for i in range(numf):
                sh[i]=sum(cn*sisi[:,i])
                ch[i]=sum(cn*coco[:,i])

            # Eq. (3) ; computing the periodogram for each simulation
            tmp = sh;
            sh = cosomtau*tmp - sinomtau*ch;
            ch = sinomtau*tmp + cosomtau*ch;

            norm_sin = sh/ts2;
            norm_cos = ch/tc2;
            cn0 = ( norm_sin*ts1 + norm_cos*tc1 ) / ( ts1*ts1/ts2 + tc1*tc1/tc2 - s0 );
            norm_sin -= cn0*ts1/ts2;
            norm_cos -= cn0*tc1/tc2;

            # Eq. (3), modified
            px = norm_sin**2*ts2 + norm_cos**2*tc2 - s0*cn0**2

            # be careful here
            px[wh] = 0.

            psdpeak[m] = 0.5*px.max()/(noise**2)

        # False Alarm Probability according to simulations
        if len(psdpeak) != 0:
            psdpeak.sort()
            psd0 = psdpeak[ long((1-fap)*(multiple-1)) ]
            simsigni = peak2sigma(psd0,n0)


    freq = om/(2.*pi)

    if verbosity>1: print('Done...')

    return (psd,freq,signi,simsigni,psdpeak)


if __name__ == '__main__':
    from numpy.random import normal
    from scipy.stats import betai

    #print('Testing Lomb-Scargle Periodogram with Gaussian noise...')
    #freq = 10. # Hz - Sample frequency
    #time = 10. #seconds
    #noisetime = arange(0,time,1./freq, dtype=float)
    #N = len(noisetime)
    #dnoisetime=0*noisetime + 1./freq
    #noisedata = sin(noisetime*2*pi)*1. + normal(loc=0,scale=1,size=N)
    #dnoisedata = noisedata*0.+1.

    file='vosource_9026.dat'
    #file='00331_3.dat'
    #file='07914_9.dat'
    mfile=open(file,'r')
    fileList = mfile.readlines()
    N = fileList.__len__()
    noisedata = zeros(N,dtype=float)
    dnoisedata = zeros(N,dtype=float)
    noisetime = zeros(N,dtype=float)
    dnoisetime = zeros(N,dtype=float)

    i=0
    for line in fileList:
        (a,b,c) = line.split()
        noisetime[i]=float(a)
        noisedata[i]=float(b)
        dnoisedata[i]=float(c)
        i = i+1

    noisetime = noisetime - noisetime[0]

    mfile.close()

    # get a careful estimate of the typical time between observations
    time = noisetime
    time.sort
    dt = median( time[1:]-time[:-1] )

    maxlogx = log(0.5/dt) # max frequency is ~ the sampling rate
    minlogx = log(0.5/(time[-1]-time[0])) #min frequency is 0.5/T

    # sample the PSD with 1% fractional precision
    M=long(ceil( (maxlogx-minlogx)*100. ))
    frequencies = exp(maxlogx-arange(M, dtype=float) / (M-1.) * (maxlogx-minlogx))
    fap = 0.01  # we want to see what psd peak this false alarm probability would correspond to

    # set multiple >0 to get Monte Carlo significane estimate for peak (warning: this is slow)
    multiple = 0  # should be >~10/fap
    psd, freqs, signi, sim_signi, peak_sort = lomb(noisetime,noisedata,delta_time=dnoisedata,
signal_err=dnoisedata,freqin=frequencies,fap=fap,multiple=multiple)

    #peak location
    imax = psd.argmax()
    freq_max = freqs[imax]

    mpsd=max(psd)
    print ("Peak=%.2f @ %.2f Hz, significance estimate: %.1f-sigma (T-test)") % (mpsd,freq_max,signi)

    if (len(peak_sort)>0):

      psd0 = peak_sort[ long((1-fap)*(multiple-1)) ]
      print ("Expected peak %.2f for False Alarm of %.2e") % (psd0,fap)

      Prob0 = betai( 0.5*N-2.,0.5,(N-1.)/(N-1.+2.*psd0) )
      Nindep = log(1-fap)/log(1-Prob0)
      horne = long(-6.362+1.193*N+0.00098*N**2.)
      if (horne <= 0): horne=5
      print ("Estimated number of independent trials: %.2f (horne=%d)") % (Nindep,horne)

      nover = sum( peak_sort>=mpsd )
      print ("Fraction of simulations with peak greater than observed value: %d/%d") % (nover,multiple)

"""
import Gnuplot
import time
plotobj = Gnuplot.Gnuplot()
plotobj.xlabel('Period (s)')
plotobj.ylabel('LS Periodogram')
plotobj('set logscale x')
plotobj('set logscale y')
plotobj.plot(Gnuplot.Data(1./freqs,psd, with = 'l 4 0'))
time.sleep(30)
"""
