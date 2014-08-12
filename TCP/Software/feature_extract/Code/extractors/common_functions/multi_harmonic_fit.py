from numpy import sin,cos,sqrt,empty,pi,dot,arctan2,atleast_1d,diag,arange,abs,ones,array,zeros,log,trace
from scipy.linalg import cho_solve,cho_factor

from pre_whiten import chi2sigma

def CholeskyInverse(t,B):
    """
    Computes inverse of matrix given its Cholesky upper Triangular decomposition t.
    """
    nrows = len(t)
    # Backward step for inverse.
    for j in reversed(range(nrows)):
      tjj = t[j,j]
      S = sum([t[j,k]*B[j,k] for k in range(j+1, nrows)])
      B[j,j] = 1.0/ tjj**2 - S/ tjj
      for i in reversed(range(j)):
        B[j,i] = B[i,j] = -sum([t[i,k]*B[k,j] for k in range(i+1,nrows)])/t[i,i]

def multi_harmonic_fit(time,data,error,freq,nharm=4,return_model=False,freq_sep=0.01,fit_mean=True,fit_slope=False):
    """
    Simultaneous fit of a sum of sinusoids by weighted, linear least squares.
       model(t) = C0 + C1*(t-t0) + Sum_i Sum_j Aij sin(2*pi*j*fi*(t-t0)+phij), i=[1,nfreq], j=[1,nharm]
         [t0 defined such that ph11=0]

    Input:
        time: x vector
        data: y vector
        error: uncertainty on data
        freq: one or more frequencies freq_i to fit
        nharm: number of harmonics of each frequency to fit (nharm=1 is just fundamental)
              fij = fi, 2*fi, ... nharm*fi
        freq_sep: freq_ij seperated by less than this are ignored (should be the search grid spacing)
        fit_slope=False, then C1=0
        fit_mean=False, then C0=0

    Output:
        A dictionary containing the model evaluated on the time grid (if return_model==True) and 
        the model amplitudes Aij, phases phij, and their uncertainties.
    """
    t = time.astype('float64')
    r = data.astype('float64')
    dr = error.astype('float64')

    numt = len(t)

    wt = 1./dr**2
    s0 = wt.sum()
    t0 = (t*wt).sum()/s0
    t -= t0

    dr *= sqrt(s0)
    r0 = (r*wt).sum()/s0
    r -= r0

    nfit=0
    if (fit_mean==True):
        nfit=1

    if (fit_slope==True):
        fit_mean=True
        nfit=2
        tm = t.max()
        s1 = ((t/tm)**2*wt).sum()
        sb = ((t/tm)*r*wt).sum()
        slope = sb/s1; s1 /= s0
        r -= slope*t/tm
        tt = t/tm/dr

    rr = r/dr
    chi0 = dot(rr,rr)*s0

    matr = empty((nfit+2*nharm,nfit+2*nharm),dtype='float64')
    vec = empty(nfit+2*nharm,dtype='float64')

    sx = empty((nharm,numt),dtype='float64')
    cx = empty((nharm,numt),dtype='float64')

    #
    # We will solve matr*res = vec, for res.  Define matr and vec.
    #
    sx0,cx0 = sin(2*pi*t*freq), cos(2*pi*t*freq)
    sx[0,:] = sx0/dr; cx[0,:] = cx0/dr
    for i in xrange(nharm-1):
        sx[i+1,:] = cx0*sx[i,:] + sx0*cx[i,:]
        cx[i+1,:] = -sx0*sx[i,:] + cx0*cx[i,:]

    if (nfit>0):
        vec[0] = 0.; matr[0,0] = 1.; 
    if (nfit>1):
        vec[1] = matr[0,1] = matr[1,0] = 0.; matr[1,1] = s1

    for i in xrange(nharm):
        vec[i+nfit] = dot(sx[i,:],rr)
        vec[nharm+i+nfit] = dot(cx[i,:],rr)
        if (nfit>0):
            matr[0,i+nfit] = matr[i+nfit,0] = dot(sx[i,:],1./dr)
            matr[0,nharm+i+nfit] = matr[nharm+i+nfit,0] = dot(cx[i,:],1./dr)
        if (nfit>1):
            matr[1,i+nfit] = matr[i+nfit,1] = dot(sx[i,:],tt)
            matr[1,nharm+i+nfit] = matr[nharm+i+nfit,1] = dot(cx[i,:],tt)
        for j in xrange(i+1):
            matr[j+nfit,i+nfit] = matr[i+nfit,j+nfit] = dot(sx[i,:],sx[j,:])
            matr[j+nfit,nharm+i+nfit] = matr[nharm+i+nfit,j+nfit] = dot(cx[i,:],sx[j,:])
            matr[nharm+j+nfit,i+nfit] = matr[i+nfit,nharm+j+nfit] = dot(sx[i,:],cx[j,:])
            matr[nharm+j+nfit,nharm+i+nfit] = matr[nharm+i+nfit,nharm+j+nfit] = dot(cx[i,:],cx[j,:])


    out_dict={}

    #
    # Convert to amplitudes and phases and propagate errors
    #
    out_dict['cn0'] = r0
    out_dict['cn0_error'] = 1./sqrt(s0)
    out_dict['trend'] = 0.
    out_dict['trend_error']=0.

    A0,B0,vA0,vB0,covA0B0 = zeros((5,nharm),dtype='float64')
    amp,phase,rel_phase = zeros((3,nharm),dtype='float64')
    damp,dphase = zeros((2,nharm),dtype='float64')
    covA0B0 = zeros(nharm,dtype='float64')
    res = zeros(nfit+2*nharm,dtype='float64')
    err2 = zeros(nfit+2*nharm,dtype='float64')

    out_dict['bayes_factor'] = 0.

    try:
        #
        # solve the equation and replace matr with its inverse
        #
        m0 = cho_factor(matr,lower=False)
        out_dict['bayes_factor'] = -log(trace(m0[0]))
        res = cho_solve(m0,vec)
        CholeskyInverse(m0[0],matr)

        A0, B0 = res[nfit:nharm+nfit],res[nharm+nfit:]
        amp = sqrt(A0**2+B0**2)
        phase = arctan2( B0,A0 )

        err2 = diag(matr)/s0
        vA0, vB0 = err2[nfit:nharm+nfit], err2[nharm+nfit:]
        for i in xrange(nharm):
            covA0B0[i] = matr[nfit+i,nharm+nfit+i]/s0

        damp = sqrt( A0**2*vA0 + B0**2*vB0 + 2.*A0*B0*covA0B0 )/amp
        dphase = sqrt( A0**2*vB0 + B0**2*vA0 - 2.*A0*B0*covA0B0 )/amp**2
        rel_phase = phase - phase[0]*(1.+arange(nharm))
        rel_phase = arctan2( sin(rel_phase),cos(rel_phase) )

    except:
        print ("Failed: singular matrix! (Are your frequencies unique/non-harmonic?)")

    out_dict['time0'] = t0-phase[0]/(2*pi*freq)
    out_dict["amplitude"] = amp
    out_dict["amplitude_error"] = damp
    out_dict["rel_phase"] = rel_phase
    out_dict["rel_phase_error"] = dphase

    modl = r0 + dot(A0,sx*dr) + dot(B0,cx*dr)
    if (nfit>0):
        out_dict['cn0'] += res[0]
        out_dict['cn0_error'] = sqrt(err2[0])
        modl += res[0]
    if (nfit>1):
        out_dict['trend'] = (res[1]+slope)/tm
        out_dict['trend_error'] = sqrt(err2[1])/tm
        modl += out_dict['trend']*t
        ###
        #import os
        #import matplotlib.pyplot as pyplot
        #t_folded = t % (1./freq)
        #pyplot.title("nfit=%d After modl += res[0] and modl += out_dict['trend']*t" % (nfit))

        #pyplot.plot(t_folded, data, 'bo', ms=3)
        #pyplot.plot(t_folded, modl, 'ro', ms=3)
        #pyplot.plot(t_folded, modl - out_dict['trend']*t, 'mo', ms=3)
        #pyplot.plot(t_folded, out_dict['trend']*t, 'go', ms=3)
        ##pyplot.plot(t, data, 'bo', ms=3)
        ##pyplot.plot(t, modl, 'ro', ms=3)
        ##pyplot.plot(t, modl - out_dict['trend']*t, 'mo', ms=3)
        ##pyplot.plot(t, out_dict['trend']*t, 'go', ms=3)
        ###pyplot.show()
        ##fpath = '/tmp/multiharmonic.ps'
        ##pyplot.savefig(fpath)
        ##os.system('gv %s &' % (fpath))
        #import pdb; pdb.set_trace()
        ###
        resid = (modl-r-r0-slope*tt*dr)/dr
        out_dict['chi2'] = dot(resid,resid)*s0
        out_dict['cn0'] += out_dict['trend']*(out_dict['time0']-t0)
    else:
        resid = (modl-r-r0)/dr
        out_dict['chi2'] = dot(resid,resid)*s0

    ###
    #import os
    #import matplotlib.pyplot as pyplot
    #t_folded = t % (1./freq)
    #pyplot.title("nfit=%d freq=%f End" % (nfit, freq))

    #pyplot.plot(t_folded, data, 'bo', ms=3)
    #pyplot.plot(t_folded, modl, 'ro', ms=3)
    #pyplot.plot(t_folded, modl - out_dict['trend']*t, 'mo', ms=3)
    #pyplot.plot(t_folded, out_dict['trend']*t, 'go', ms=3)
    ##pyplot.plot(t, data, 'bo', ms=3)
    ##pyplot.plot(t, modl, 'ro', ms=3)
    ##pyplot.plot(t, modl - out_dict['trend']*t, 'mo', ms=3)
    ##pyplot.plot(t, out_dict['trend']*t, 'go', ms=3)
    ###pyplot.show()
    #fpath = '/tmp/multiharmonic.ps'
    #pyplot.savefig(fpath)
    #os.system('gv %s &' % (fpath))
    #import pdb; pdb.set_trace()
    #pyplot.clf()
    ###


    out_dict['nu'] = numt - 2*nharm - nfit
    out_dict['signif'] = chi2sigma(chi0,out_dict['chi2'],numt-nfit,nharm)
    if (return_model):
        out_dict['model'] = modl

    return out_dict
