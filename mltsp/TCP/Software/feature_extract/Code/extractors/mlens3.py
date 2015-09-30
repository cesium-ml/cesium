#!/usr/bin/env python
"""Mlens
 a plugin to the classification engine that makes statements about probabilities of a microlens in a light curve

 v1.0 -- JSB

 Usage:
 import mlens3
 ## make a data model instance from a VOSource
 d = mlens3.EventData("124.22024.4124.xml")

 ## run the fitter (turn off doplot for running without pylab)
 m = mlens3.Mlens(datamodel=d,doplot=True)

 ## print the results
 print m

 ## grab the results (prob_mlens should be between 0 and 1...anything above 0.8 is pretty sure bet)
 prob_mlens =  m.final_results["final"]["probabilities"]["single-lens"]

 TODO:
    - combine multiple filters to make stronger statements
    - search for anamolies in the data
    - make statements about multiple lens

"""
from __future__ import print_function
from __future__ import absolute_import
from numpy import *
from math import degrees, pi
from scipy.optimize import leastsq, fmin, fmin_powell
from scipy import random as r
from scipy.odr import *

from scipy.stats import trim_mean, normaltest, moment, chisqprob
try:
    from scipy.stats import median
except:
    from scipy import median
try:
    from scipy.stats import samplestd
except:
    from scipy import std as samplestd

from scipy.stats.kde import gaussian_kde as kde

from scipy.stats import norm as statnorm
c  = 2.998e10
g  = 6.674e-8
import copy, sys, os
try:
    from matplotlib.pylab import *
except:
    print("unable to import matplotlib")
from . import vosource_parse, xmldict
#from pprint import pprint, pformat# dstarr disables pprint function since I'd rather not have this module constantly in memory if just for debugging use.

__version__ = "1.0.2"


from .. import db_importer

class Mlens:

    ## basic lens equations
    theta_e          = lambda s,ml, dl: sqrt(2.0*g*ml*1.99e33/(dl*3.085e18))/c
    theta_e_arcsec   = lambda s,ml, dl: 3600.0*degrees(theta_e(ml,dl))
    re               = lambda s,ml, dl: dl*3.085e18*theta_e(ml,dl)
    te               = lambda s,ml, dl, vl: re(ml,dl)/(vl*1e5)
    te_in_days       = lambda s,ml, dl, vl: te(ml, dl, vl)/(24.0*3600.0)
    u                = lambda s,ml, dl, vl, umin, t0, t: sqrt(umin**2 + ((t - t0)/te_in_days(ml,dl,vl))**2)
    u_te             = lambda s,the_te, umin, t0, t: sqrt(umin**2 + ((t - t0)/the_te)**2)

    final_results = {}

    def __init__(self,datamodel=None,doplot=True,verbose=False):
        self.doplot = doplot
        self.verbose = verbose
        if self.doplot:
            cla()
        if datamodel is None:
            self.test()
        else:
            self.data = datamodel
            self.run()

    def __str__(self):
        a = "Results of microlens fitting\n"
        # dstarr disables pprint function since I'd rather not have this module constantly in memory if just for debugging use.
        #a += pformat(self.final_results)
        a += str(self.final_results)
        return a

    def out_print(self,rez):

        if not isinstance(rez,dict):
            return ""

        a =  "********* Filter = %s ************\n" % rez.keys()[0]
        a += "_"*50 + "\n"
        tmp =  rez.values()[0]
        for k,v in rez.values()[0].iteritems():
            a += " --> sub-set name: %s <-- \n" % k
            a += "  +  metadata  ---\n"
            ndata = -1 if "ndata" not in v else v['ndata']
            normalcy_prob = -1 if "normalcy_prob" not in v else v['normalcy_prob']
            p_chi         = -1 if "p_chi" not in v else v['p_chi']
            res_var       = -1 if "resid_var" not in v else v['resid_var']
            chisq         = -1 if "chisq" not in v else v['chisq']
            dof           = -1 if "dof" not in v else v['dof']
            frac_data_remaining = 1 if "frac_data_remaining" not in v else v['frac_data_remaining']
            beta          = [-1,-1,-1,-1,-1,-1] if "beta" not in v else v['beta']
            if len(beta) == 6:
                eq = "f(t) = %8.3e + (%7.3f + %8.3e x t) * g(u[t])" % (beta[5],beta[3],beta[4])
            elif len(beta) == 5:
                eq = "f(t) = (%7.3f + %8.3e x t) * g(u[t])" % (beta[3],beta[4])
            else:
                eq = ""
            a += "\tndata = %i chisq = %f  dof = %f\n" % (ndata,chisq,dof)
            a += "\tp_chi = %f p_normalcy= %f resid_variance = %f\n" % (p_chi,normalcy_prob,res_var)
            a += "\tfrac data = %7.2f\n" % frac_data_remaining
            a += "\tequation: %s\n" % eq
            a += "   + derived parameters ---\n"
            a += "\tt_0 = %6.3f +/- %6.3f d     t_e = %6.3f +/- %6.3f d\n" % \
                   (v["t0"]["val"],v["t0"]["err"],v["te"]["val"],v["te"]["err"])
            a += "\tAmax = %6.3f +/- %6.3f     u_min = %6.3f +/- %6.3f\n" % \
                  (v["Amax"]["val"],v["Amax"]["err"],v["umin"]["val"],v["umin"]["err"])
        return a
    def renorm_data(self,dat,rez,dset="sig5"):

        if dset not in rez.values()[0]:
            dset = "all"
        if dset not in rez.values()[0]:
            durga
            return (dat[0],dat[1],dat[2])
        v=rez.values()[0][dset]
        if "beta" not in v:
            durga
            return  (dat[0],dat[1],dat[2])

        beta          =  v['beta']
        if len(beta) == 6:
            zp = beta[5]
        else:
            zp = 0.0

        f    = (dat[1] - zp)/(beta[3] + beta[4]*dat[0]/dat[0][0])
        ferr = (f/dat[1])*dat[2]

        return (dat[0],f,ferr)


    def run(self,multifilt=False):

        if not multifilt:
            print("Warning: we're only going to use the filter with the most data for now")
            print("         in the future we'll combine the results")
            self.all_fits = []
            self.all_out = []
            if self.doplot:
                cla()
            minx, maxx = 1e9,-99
            miny, maxy = 1e9,-99
            maxdata = 0
            thef = ""
            for f in self.data.filts:
                if len(self.data.t(f)) > maxdata:
                    maxdata = len(self.data.t(f))
                    thef = f

            f = thef
            tt, ff, fferr = [], [], []
            print("using %i epochs from filter %s" % (maxdata,f))
            dat = [self.data.t(f),self.data.flux(f),self.data.flux_err(f)]
            minx = min([min(self.data.t(f)),minx])
            miny = min([min(self.data.flux(f)),miny])
            maxx = max([max(self.data.t(f)),maxx])
            maxy = max([max(self.data.flux(f)),maxy])
            # 20090212: dstarr re-enables try/except to see if we handle it fine (when n_epochs==1)
            try:
                self.all_fits.append({f: self._filt_run(dat,f)})
                self.all_out.append({f: self.inspect_output_by_filter(self.all_fits[-1],dat,doplot=self.doplot)})
                if self.verbose:
                    print(self.out_print(self.all_out[-1]))
            except:
                print("EXCEPT: mlens3.py:168 self.inspect_output_by_filter(..).  Probably not enough datapoints.")
                return
            tnorm, fluxnorm, flux_errnorm = self.renorm_data(dat,self.all_out[-1],dset="sig5")
            tt.extend(list(tnorm))
            ff.extend(list(fluxnorm))
            fferr.extend(list(flux_errnorm))
            self.single_lens_statements(self.all_out[-1])
            a = self.out_print(self.all_out[-1])
            self.final_results.update({"description": a})
            if self.doplot:
                xlim([minx,maxx])
                ylim([0.9*miny,maxy*1.1])
            return
        else:
            if not isinstance(self.data,EventData):
                print("bad data model")

            self.all_fits = []
            self.all_out = []
            if self.doplot:
                cla()
            ## loop over the filters and collect the results
            minx, maxx = 1e9,-99
            miny, maxy = 1e9,-99
            tt, ff, fferr = [], [], []
            for f in self.data.filts:
                print("filter %s" % f)
                dat = [self.data.t(f),self.data.flux(f),self.data.flux_err(f)]
                minx = min([min(self.data.t(f)),minx])
                miny = min([min(self.data.flux(f)),miny])
                maxx = max([max(self.data.t(f)),maxx])
                maxy = max([max(self.data.flux(f)),maxy])
                try:
                    self.all_fits.append({f: self._filt_run(dat,f)})
                    self.all_out.append({f: self.inspect_output_by_filter(self.all_fits[-1],dat,doplot=self.doplot)})
                    if self.verbose:
                        print(self.out_print(self.all_out[-1]))
                except:
                    continue
                tnorm, fluxnorm, flux_errnorm = self.renorm_data(dat,self.all_out[-1],dset="sig5")
                tt.extend(list(tnorm))
                ff.extend(list(fluxnorm))
                fferr.extend(list(flux_errnorm))
                self.single_lens_statements(self.all_out[-1])

            if self.doplot:
                xlim([minx,maxx])
                ylim([0.9*miny,maxy*1.1])

            print(self.data.filts)
            if len(self.data.filts) > 1:
                print("combined fit")
                print(dat)
                #dat = [array(tt),array(ff),array(fferr)]
                #self.all_fits.append({"all": self._filt_run(dat,"all")})
                #self.all_out.append({"all": self.inspect_output_by_filter(self.all_fits[-1],dat)})
                #self.out_print(self.all_out[-1])

    def single_lens_statements(self,rez):

        f = rez.keys()[0]
        rez = rez.values()[0]
        rel_import = array([1/1.0,1/0.8,1/2.0]) ## importance of knowing umin, te, t0
        rel_pimport = array([1.0,2.0,3.0]) ## inverse of importance
        bestp = besta = 0.0
        ret = []
        for k,v in rez.iteritems():
            effective_prob = sqrt(max([v['p_chi'], exp(-1.0*v['resid_var'])]))
            expected_te    = 40.0
            best_te_dif    = min( [abs(expected_te - v['te']['val'] + v['te']['err']),\
                                  abs(expected_te - v['te']['val'] - v['te']['err']),\
                                  abs(expected_te - v['te']['val'])] )
            var = log10(12.0)
            te_prob_1        = exp(  -( log10(expected_te) - log10(v['te']['val'] + v['te']['err']) )**2/var**2)
            te_prob_2        = exp(  -(log10(expected_te) - log10(v['te']['val'] - v['te']['err']) )**2/var**2)
            te_prob_3        = exp(  -(log10(expected_te) - log10(v['te']['val']) )**2/var**2)

            #print (te_prob_1,te_prob_2,te_prob_3)
            te_prob = max([te_prob_1,te_prob_2,te_prob_3])
            #effective_prob *= te_prob

            ## how well is umin and te measured?
            umin_sig = v['umin']['val']/v['umin']['err']
            te_sig   = v['te']['val']/v['te']['err']

            ## how well is t0 measured (relative to t_e)?
            t0_sig   = v['te']['val']/v['t0']['err']

            ## what's the chance that the peak was before the first data?
            p_peak_before = statnorm.cdf((self.data.t(f)[0] - v['t0']['val'])/v['t0']['err'])

            ## what's the chance that the peak was the after the last data?
            p_peak_after = 1 - statnorm.cdf((self.data.t(f)[-1] - v['t0']['val'])/v['t0']['err'])

            pvals = array([1.0 - math.exp(-1.0*umin_sig/2), 1.0 - math.exp(-1.0*te_sig/2),1.0 - math.exp(-1.0*t0_sig/2)])
            avgpval = sqrt(  ( (pvals/rel_import)**2 ).sum() / ( (1.0/rel_import)**2 ).sum() )
            final_p =  sqrt(  ((avgpval/rel_pimport[0])**2 + (te_prob/rel_pimport[1])**2 + (effective_prob/rel_pimport[2])**2 ) / ((1.0/rel_pimport)**2).sum())
            bestp = bestp if bestp > final_p or isnan(final_p) else final_p
            besta = besta if besta > avgpval or isnan(avgpval) else avgpval

            tmp = {k: {"probabilities": \
                       {"peak_before_first_obs": p_peak_before, \
                        "peak_after_last_obs": p_peak_after, \
                        "well measured parameters": avgpval, \
                        "combined_is_microlens": final_p, \
                        "reasonable effetive time (te)": te_prob,\
                        "statistical normalcy of fit": effective_prob}, \
                       "parameters": \
                        {"te": {"val": v['te']['val'], "err": v['te']['err'], "sig": te_sig},\
                         "t0": {"val": v['t0']['val'], "err": v['t0']['err'], "sig": t0_sig},\
                         "umin": {"val": v['umin']['val'], "err": v['umin']['err'], "sig": umin_sig}}}}
            ret.append(tmp)
            if self.verbose:
                print((k, final_p, avgpval, te_prob, effective_prob, umin_sig,te_sig,t0_sig,p_peak_before,p_peak_after))
        ## what's the robustness of the result (how much do the parameters change on clipping)?
        ## how well observed are all the data (how much do the parameters change on clipping)?
        if self.verbose:
                print("Best probability of a being a single microlens = %f" % bestp)
                print("Robustness of the 3 parameter fit = %f " % besta)
        ret = {"value_added_properties": ret}
        #tmp = {"probabilities": {"single-lens": bestp, "single-lens-parameter-robustness": besta}}
        #dstarr prefers a more generic form:   ("weight" is just a 0..1 quantifier)
        tmp = {"probabilities": {"single-lens": {'prob':bestp, "prob_weight": besta}}}
        ret.update(tmp)
        self.final_results = ret

    def _extract_info(self,b,berr,extra):

        umin_found, umin_found_sigma = b[1], berr[1]
        dadu = -(umin_found**2 + 2)/(umin_found**2*sqrt(umin_found + 4)) - \
                            (umin_found**2 + 2)/(2*umin_found*(umin_found + 4)**(1.5)) + \
                            2/sqrt(umin_found + 4)

        Amax = (umin_found**2 + 2)/(umin_found*sqrt(umin_found**2 + 4))
        Amax_sigma = sqrt(dadu**2)*umin_found_sigma

        ret = {"beta": b,
               "t0":   {"val": b[2], "err": berr[2]},
               "te":   {"val": abs(b[0]), "err": berr[0]},
               "umin": {"val": abs(b[1]), "err": berr[1]},
               "Amax": {"val": abs(Amax), "err": Amax_sigma},
               "resid_var":  extra.res_var}

        return ret

    def inspect_output_by_filter(self,rez,dat,doplot=False,test=False,
                                 sig_clips=[5, 3, 2], sig_test=[False,False,True]):
        p = rez.values()[0][1]
        myoutput = rez.values()[0][0]
        new  = rez.values()[0][2]
        filt = rez.keys()[0]

        ret = {}
        ret.update({"all": self._extract_info(p,myoutput.sd_beta,myoutput)})
        err = dat[2]
        tmp = (dat[1] - self.modelfunc_small_te(p,dat[0]))/err
        dof = tmp.shape[0] -  myoutput.beta.shape[0]
        chisq = (tmp**2).sum()
        ret['all'].update({"ndata": dat[0].shape[0], \
                            "chisq": chisq, "dof": dof, "p_chi": chisqprob(chisq,dof),
                            "normalcy_prob": normaltest(tmp)[1]})

        for s in enumerate(sig_clips):
            if sig_test[s[0]] and not test:
                continue
            sig = s[1]
            # get the indices of those inside and out of the clip area
            tmpisig = (abs(tmp) < sig).nonzero()[0]
            tmpisige = (abs(tmp) > sig).nonzero()[0]
            frac_less_than_sig =  float(tmpisig.shape[0])/dat[0].shape[0]
            # print frac_less_than_sig
            if frac_less_than_sig < 1.0:
                out = self._filt_run([dat[0][tmpisig],dat[1][tmpisig],err[tmpisig]],\
                                      filt,do_sim=False,vplot=False)
                p        = out[1]
                myoutput = out[0]
                t = "-test" if sig_test[s[0]] else ""

                ret.update({"sig" + str(sig) + t: self._extract_info(p,myoutput.sd_beta,myoutput)})
                tmp = (dat[1][tmpisig] - self.modelfunc_small_te(p,dat[0][tmpisig]))/err[tmpisig]
                dof = tmp.shape[0] - myoutput.beta.shape[0]
                chisq = (tmp**2).sum()
                try:
                    ntest =  normaltest(tmp)[1]
                except:
                    ntest = 0.0
                ret["sig" + str(sig) + t].update({"ndata": dat[0][tmpisig].shape[0], \
                                    "chisq": chisq, "dof": dof, "p_chi": chisqprob(chisq,dof),
                                    "normalcy_prob": ntest, "frac_data_remaining": frac_less_than_sig })
                if doplot:
                    plot(dat[0][tmpisige],dat[1][tmpisige],".")

        return ret

    def _filt_run(self,dat,filt,do_sim=False,vplot=True,nrange=1):

        if self.doplot and vplot:
            errorbar(dat[0],dat[1],dat[2],fmt="o")

        new = True
        if new:
            mymodel = Model(self.fitfunc_small_te,extra_args=[dat[1],dat[2],False])
        else:
            mymodel = Model(self.fitfunc_te) #,extra_args=[dat[1],dat[2],False])

        # get some good guesses
        try:
            scale = trim_mean(dat[1],0.3)
        except:
            scale = mean(dat[1])
        offset = 1.0 #trim_mean(dat[1],0.3)
        t0    = median(dat[0])
        umin  = 1.0
        b     = 0.0  ## trending slope
        mydata  = RealData(dat[0],dat[1],sx=1.0/(60*24),sy=dat[2])

        trange = list(linspace(min(dat[0]),max(dat[0]),nrange))
        maxi = (dat[1] == max(dat[1])).nonzero()[0]
        trange.extend(list(dat[0][maxi]))
        trange.extend([t0, max(dat[0]) + 10, max(dat[0]) + 100])

        final_output = None
        for t0i in trange:
            for te in 10**linspace(log10(2),log10(200),nrange):
                if new:
                    pinit = [te,umin,t0i] # ,scale,offset,b]
                else:
                    pinit = [te,umin,t0i ,scale,offset,b]

                myodr = ODR(mydata,mymodel,beta0=pinit)
                myoutput = myodr.run()
                if final_output is None:
                    final_output = myoutput
                    old_sd_beta = final_output.sd_beta
                    continue

                if trim_mean(log10(myoutput.sd_beta / final_output.sd_beta),0.0) < 0.0 and \
                    myoutput.res_var <= final_output.res_var and (myoutput.sd_beta == 0.0).sum() <= (final_output.sd_beta == 0.0).sum():
                    final_output = myoutput

        if 1:
            t = linspace(min(dat[0]),max([max(dat[0]),final_output.beta[2] + 6*final_output.beta[0]]),1500)
            if new:
                tmp = self.fitfunc_small_te(final_output.beta,dat[0],dat[1],dat[2],True)
                #print tmp, "***"
                p = list(final_output.beta)
                p.extend([tmp[0],tmp[1],tmp[2]])
                y = array(self.modelfunc_small_te(p,t))
            else:
                p = final_output.beta
                y = self.fitfunc_te(final_output.beta,t)
                #print final_output.beta
            if self.doplot:
                plot(t,y)
                xlabel('Time [days]')
                ylabel('Relative Flux Density')

            if do_sim:
                for i in range(10):
                    tmp = r.multivariate_normal(myoutput.beta, myoutput.cov_beta)
                    if self.doplot:
                        plot(t, self.a_te(tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5],t),"-")

        return (final_output, p, new)

    def exp_model(self,scale):
        pass

    def a_te(self,the_te, umin, t0, scale, offset, b, t):
        uu = self.u_te(the_te,umin,t0,t)
        return scale*(offset + b*(t/t[0]))*(uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))

        #return scale*((uu**2 + 2)/(uu*sqrt(uu**2 + 4.0)) + offset + b*(t/t[0]))

    def a(self,ml, dl, vl, umin, t0, t):
        uu = self.u(ml, dl, vl, umin, t0, t)
        return (uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))

    def fitfunc_te(self,p, t):
        return self.a_te(p[0],p[1],p[2],p[3],p[4],p[5],t)

    def errfunc_small_te(self,p, t, y, err):
        the_te, umin, t0 = p[0],p[1],p[2]
        uu = self.u_te(the_te,umin,t0,t)
        tp = t/t[0]
        c1, c2, c3, c4, c5 = (uu**2/err**2).sum(), (uu*tp/err**2).sum(), \
                             (uu*y/err**2).sum(), (tp**2*uu**2/err**2).sum(), (tp*y*uu/err**2).sum()
        a = (c5*c2 - c3*c4)/(c4*c1 - c2**2)
        b = (-1.0*c3 - a*c1)/c2

        f = (a + b*tp)*(uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))
        return (y - f) / err

    def modelfunc_small_te(self,p,t):
        the_te, umin, t0, a, b = abs(p[0]),p[1],p[2],p[3],p[4]
        if len(p) > 5:
            c = p[5]
        else:
            c = 0
        #the_te, umin, t0 = 6.55809283e+01 ,  1.01096831e+00 , 1.85432274e+03
        #a = 1.22903731e+00* 1.00337302e+00
        #b = -2.41483071e-04 * 1.22903731e+00

        uu = self.u_te(the_te,umin,t0,t)
        tp = t/t[0]
        return c + (a + b*tp)*(uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))

    def fitfunc_small_te(self,p, t, y,err,retab):
        #the_te, umin, t0 = 6.55809283e+01 ,  1.01096831e+00 , 1.85432274e+03

        the_te, umin, t0 = abs(p[0]),p[1],p[2]
        uu = self.u_te(the_te,umin,t0,t)
        uu = (uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))
        tp = t/t[0]
        #err[:] = 1
        old = False
        if old:
            c1, c2, c3, c4, c5 = (uu**2/err**2).sum(), (tp*uu**2/err**2).sum(), \
                             (uu*y/err**2).sum(), (tp**2*uu**2/err**2).sum(), (tp*y*uu/err**2).sum()
        # print c1, c2, c3, c4, c5
            a = (-1.0*c5*c2 + c3*c4)/(c4*c1 - c2**2)
            b = (c3 - a*c1)/c2
            c = 0
            ##
            #a = 1.0*c3/c1
            #b = 0.0
             # (uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))
        else:
            c1 = (y/err**2).sum()
            c2 = (1/err**2).sum()
            c3 = (uu/err**2).sum()
            c4 = (tp*uu/err**2).sum()
            c5 = (y*uu/err**2).sum()
            c6 = c4
            c7 = (uu**2/err**2).sum()
            c8 = (tp*uu**2/err**2).sum()
            c9 = (tp*y*uu/err**2).sum()
            c10 = c4
            c11 = c8
            c12 = (tp**2*uu**2/err**2).sum()
            c= (c3*(c12*c5-c8*c9)+c4*(c7*c9-c11*c5)+c1*(c11*c8-c12*c7))/(c2*(c11*c8-c12*c7)+c3*(c12*c6-c10*c8)+c4*(c10*c7-c11*c6))
            a=-(c2*(c12*c5-c8*c9)+c4*(c6*c9-c10*c5)+c1*(c10*c8-c12*c6))/(c2*(c11*c8-c12*c7)+c3*(c12*c6-c10*c8)+c4*(c10*c7-c11*c6))
            b= (c2*(c11*c5-c7*c9)+c3*(c6*c9-c10*c5)+c1*(c10*c7-c11*c6))/(c2*(c11*c8-c12*c7)+c3*(c12*c6-c10*c8)+c4*(c10*c7-c11*c6))

        f = (a + b*tp)*uu + c
        #cc = (((f - y)/err)**2).sum()
        #print (a,b,the_te,umin,t0)
        #a = 1.22903731e+00* 1.00337302e+00
        #b = -2.41483071e-04 * 1.22903731e+00
        #f = (a + b*tp)*uu # (uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))
        #cc1 = (((f - y)/err)**2).sum()
        #print cc, cc1, cc/cc1
        #f = (a + b*tp)*uu # (uu**2 + 2)/(uu*sqrt(uu**2 + 4.0))
        if not retab:
            return f # (y - f) / err
        else:
            return (a,b,c)
    def plot_rez(self):
        cla()

class EventData:

    def __init__(self,data):
        ## should be
        if isinstance(data,xmldict.XmlDictObject) or isinstance(data,dict):
            self.data = data
        if isinstance(data,str):
            ## maybe it's a file?
            if data.endswith(".xml"):
                v = vosource_parse.vosource_parser(data)
                self.fname = data
                #self.elemtree = v.elemtree # 20090225 dstarr added
                self.data = v.d
            else:
                # The we assume it is a large string of XML
                v = vosource_parse.vosource_parser(data, is_xmlstring=True)
                self.fname = data
                #self.elemtree = v.elemtree # 20090225 dstarr added
                self.data = v.d
                # self.fiter_data/dict = .... ?etree?

        self.filts = self.data['ts'].keys()

        # We get feature data (not for mlens use, but for other classifier's use)
        self.get_features_from_data()


    def get_features_from_data(self):
        """ Retrieve features from self.data (vosource_parser)
        inserts into self.feat_dict{}
        WHERE:
        self.feat_dict[<feature_name>] = {\
 'description': 'freq1_harmonics_peak2peak_flux',
 'err': {'_text': 'unknown', 'datatype': 'string'},
 'filter': {'_text': 'H', 'datatype': 'string'},
 'name': {'_text': 'freq1_harmonics_peak2peak_flux', 'class': 'timeseries'},
 'origin': {'code_output': {'_text': '"0.307688969542"',
                            'datatype': 'string'},
            'code_ver': 'db_importer.py 885 2008-10-24 19:47:03Z pteluser',
            'description': '',
            't_gen': {'_text': '2008-10-28T04:50:35.258144',
                      'ucd': 'time.epoch'}},
 'val': {'_text': '0.307688969542',
         'datatype': 'float',
         'is_reliable': 'True'}}
        """
        self.feat_dict = {'multiband':{}}
        # TODO: there are different filters. Use these.

        for feat_obj in self.data.get('VOSOURCE',{}).get('Features',{}).get('Feature',[]):
            a_feat_dict = dict(feat_obj)
            feat_name = a_feat_dict.get('name',{}).get('_text','NOT_A_FEATURE')
            filt_name = a_feat_dict.get('filter',{}).get('_text','NOT_A_FILTER')
            if filt_name not in self.feat_dict:
                self.feat_dict[filt_name] = {}
            self.feat_dict[filt_name][feat_name] = a_feat_dict # ??? need to copy.deepcopy() this?


    def t(self,filt):
        """assumes unit = day for now"""

        if isinstance(filt,str):
            if filt not in self.filts:
                return array([])
            else:
                ret = array([])
                for c in self.data['ts'][filt]:
                    if "name" in c:
                        if c['name'] == "t":
                            ret = c['val']
                            break
                    if "system" in c:
                        if c['system'] == "TIMESYS":
                            ret = c["val"]
                            break
            return ret
        return array([])

    def flux(self,filt,zp=None):
            """assumes unit = day for now"""
            if not zp:
                zp = 3000e3  ## just choose something to get us close to mJy

            if isinstance(filt,str):
                if filt not in self.filts:
                    return array([])
                else:
                    ret = array([])
                    for c in self.data['ts'][filt]:
                        if "name" in c:
                            if c['name'].find("err") != -1:
                                continue
                            #if c['name'] == "f" or c['name'].find("flux") != -1:
                            #   ret = c['val']
                            #   break
                            #if c['name'] == "m" or c['name'].find("mag") != -1:
                            #   ret = zp*10**(-0.4*c["val"])
                            #   break
                        if "ucd" in c:
                            if c['ucd'].find("err") != -1:
                                continue
                            if c['ucd'].find("rel flux") != -1:
                                ret = c["val"] + 1.0 ## for OGLE data
                                break
                            if c['ucd'].find("flux") != -1:
                                ret = c["val"]
                                break
                            if c['ucd'].find("phot.mag") != -1:
                                ret = zp*10**(-0.4*c["val"])
                                break
                        if "unit" in c:
                            if c['unit'].find("Jy") != -1 or c['unit'].find("erg") != -1:
                                ret = c["val"]
                                break
                            if c["unit"].find("rel flux") != -1:
                                ret = c["val"] + 1.0 ## for OGLE
                                break
                            if c['unit'].find("mag") != -1:
                                ret = zp*10**(-0.4*c["val"])
                                break

                return ret
            return array([])

    def flux_err(self,filt,zp=None):
            """assumes unit = day for now
            not a correct calculation for large errors
            """

            if not zp:
                zp = 3000e3  ## just choose something to get us close to mJy

            if isinstance(filt,str):
                if filt not in self.filts:
                    return array([])
                else:
                    ret = array([])
                    for c in self.data['ts'][filt]:
                        #if c.has_key("name"):
                        #   if c['name'] == "f_err":
                        #       ret = c['val']
                        #       break
                        #   if c['name'] == "m_err":
                        #           ret = c["val"]*self.flux(filt,zp)
                        #           break
                        if "ucd" in c:
                            if c['ucd'].find("flux") != -1 and c['ucd'].find("err") != -1:
                                ret = c["val"]
                                break
                            if c['ucd'].find("phot.mag") and c['ucd'].find("err") != -1:
                                ret = c["val"]*self.flux(filt,zp)
                                break

                if (ret == 0).sum() == ret.shape[0]:
                    ## all zeros! figure out the scatter
                    tmp = self.flux(filt,zp)
                    for i in range(5):
                        med = median(tmp)
                        sigma = sqrt(((tmp - med)**2).sum()/ret.shape[0])
                        tmpi = (abs(tmp - med) < 2.5*sigma).nonzero()[0]
                        tmp = tmp[tmpi]
                        #print med, sigma
                    ret = sigma*ones(ret.shape[0])

                return ret
            return array([])

def test():

    #d = EventData("test_feature_algorithms.VOSource.xml")
    #m = Mlens(datamodel=d)
    #d = EventData("MM1-1190.xml")
    #d = EventData("sc33-290665.xml")
    #d = EventData("124.22024.4124.xml")
    #d = EventData("142.27776.3952.xml")
    #d = EventData("167.24169.3673.xml")
    #d = EventData("168.25079.1100.xml")
    #d = EventData("307.36884.258.xml")
    #d = EventData("sc39-468687.xml")
    d  = EventData("sc39-697584.xml")
    #d = EventData("sc34-451887.xml")
    #d = EventData("MM1-1192.xml")  # 2 filters
    #d = EventData("BLG157.7-132318.xml") # multi
    #d = EventData("MM1-0307.xml")  #not a lens
    #d = EventData("ON231.xml")  #not a lens
    #d = EventData("SN1998dk.xml") #not a lens
    #pprint(d.data)
    #pprint(d.data['ts'])
    #pprint(d.t("B"))
    #pprint(d.flux("B"))
    #pprint(d.flux_err("B"))
    #durga
    m = Mlens(datamodel=d,doplot=True)
    print(m)
    #errorbar(d.t("I"),d.flux("I"),d.flux_err("I"))
    #print d.t("I").median()

if __name__ == '__main__':

    ##### dstarr added these testing statements:

    d = EventData(os.path.abspath(os.environ.get("TCP_DIR") + "/Data/124.22024.4124.xml"))

    ## run the fitter (turn off doplot for running without pylab)
    m = Mlens(datamodel=d,doplot=True)

    ###m.run()
    ## print the results
    import pprint
    pprint.pprint(m.final_results)

    ## grab the results (prob_mlens should be between 0 and 1...anything above 0.8 is pretty sure bet)
    prob_mlens =  m.final_results["probabilities"]["single-lens"]

    pass # for pdb breakpoint
