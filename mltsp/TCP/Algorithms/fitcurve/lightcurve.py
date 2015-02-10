#!/usr/bin/env python

## Filename: lightcurve.py
## Version:  0.1  (realistically this is nearly the hundredth version)
## Notes:
##     -This code uses the pre_whiten from the NOISIFICATION directory. (the dictionary this prewhiten outputs has a 'y_offset' key and uses a shorter nharm_min-max range).
##     -Main change for v0.1:  lomb_scargle and pre_whiten take input signal errors. Before they were assigning uniform errors to each datapoint.
##                             pre_whiten has an lower and upper limit in scanning harmonics (4-20).  This is significant for phase offset issues
##     -TO STORE IN DATABASE:
##         In GetPeriodFoldForWeb.generate_lomb_period_fold there is a dictionary called db_dictionary.  The values stored in here will be what you want to put online.  Need
##         to have a method that returns this dictionary though.  Also, it may be best to store more harmonics, if we find that the cut I am using is too strict.  Currently it
##         is that the amplitude/amp_error >=1  (reasonable, although probably too liberal)
##     -FOR TCP_EXPLORER PLOT:
##         The values stored in db_dictionary are essentially used to create the plot on tcp_explorer.  db_dictionary does have extra values not needed in the plot, but useful
##         perhaps in feature generation.

######
from __future__ import print_function
import sys
import os

try:
    import MySQLdb
except:
    pass
import pprint
try:
    import matplotlib
    import matplotlib.pyplot as pyplot
    import matplotlib.mlab as mlab
except:
    pass # dstarr doesn't want any extra printed output
    #print "matplotlib dependencies could not load"
import scipy
import numpy
try:
    import pylab 
    from pylab import *
except:
    pass
from numpy import * # from numpy import loadtxt,long,linspace,pi,arctan2,sin,cos,hstack,array,log10,abs,logical_or,logical_and,var
from scipy.optimize import fmin, brute
from scipy import random
from numpy.random import rand
import lomb_scargle # obsolete?
from lomb_scargle import peak2sigma,lprob2sigma, lomb, get_peak_width # obsolete?
import pre_whiten # obsolete?
from lomb_scargle_refine import lomb as lombr

import pickle
import copy
from multi_harmonic_fit import multi_harmonic_fit as mh
from scipy.special import gammaincc,gammaln
from scipy.stats import scoreatpercentile

        
class lomb_model(object):
    def create_model(self, available, m, m_err, out_dict):
        def model(times):
            data = zeros(times.size)
            for freq in out_dict:
                freq_dict = out_dict[freq]
                # the if/else is a bit of a hack, 
                # but I don't want to catch "freq_searched_min" or "freq_searched_max"
                if len(freq) > 8:
                    continue
                else:
                    time_offset = freq_dict["harmonics_time_offset"]
                    for harmonic in range(freq_dict["harmonics_freq"].size):
                        f = freq_dict["harmonics_freq"][harmonic]
                        omega = f * 2 * pi
                        amp = freq_dict["harmonics_amplitude"][harmonic]
                        phase = freq_dict["harmonics_rel_phase"][harmonic]
                        new = amp * sin(omega * (times - time_offset) + phase)
                        data += new
            print("length of data is:", len(data))
            print("data:", data)
            return data
        return model
        
class period_folding_model(lomb_model):
    """ contains methods that use period-folding to model data """
    def period_folding(self, needed, available, m , m_err, out_dict, doplot=True):
        """ period folds both the needed and available times. Times are not ordered anymore! """
        
        # find the first frequency in the lomb scargle dictionary:
        f = (out_dict["freq1"]["harmonics_freq"][0])
        if out_dict["freq2"]["signif"] > out_dict["freq1"]["signif"]:
            f = out_dict["freq2"]["frequency"]
        
        # find the phase:
        p = out_dict["freq1"]["harmonics_rel_phase"][0]
        
        #period-fold the available times
        t_fold = mod( available + p/(2*pi*f) , (1./f) )
        
        #period-fold the needed times
        t_fold_model = mod( needed + p/(2*pi*f) , (1./f) )
        ###### DEBUG ######
        early_bool = available < (2.4526e6 + 40)
        ###### DEBUG #####
        
        period_folded_progenitor_file = file("period_folded_progenitor.txt", "w")
        progenitor_file = file("progenitor.txt", "w")

        for n in range(len(t_fold)):
            period_folded_progenitor_file.write("%f\t%f\t%f\n" % (t_fold[n], m[n], m_err[n]))
            progenitor_file.write("%f\t%f\t%f\n" % (available[n], m[n], m_err[n]))
        progenitor_file.close()

        print("RETURNING t_fold:")
        print(t_fold)
        print("RETURNING t_fold_model:")
        print(t_fold_model)
        return t_fold, t_fold_model

        
    def create_model(self,available, m , m_err, out_dict):
        f = out_dict["freq1"]["frequency"]
        def model(times):
            t_fold, t_fold_model = self.period_folding(times, available, m, m_err, out_dict)
            data = empty(0)
            rms = empty(0)
            for time in t_fold_model:
                # we're going to create a window around the desired time and sample a gaussian distribution around that time
                period = 1./f
                assert period < available.ptp()*1.5, "period is greater than ####SEE VARIABLE CONTSTRAINT#### of the duration of available data"   #alterring this.  originally 1/3
                # window is 2% of the period
                passed = False
                for x in arange(0.01, 0.1, 0.01):
                    t_min = time - x * period
                    t_max = time + x * period
                    window = logical_and((t_fold < t_max), (t_fold > t_min)) # picks the available times that are within that window
                    try:
                        # there must be more than # points in the window for this to work:
                        assert (window.sum() >= 2), str(time) # jhiggins changed sum from 5 to 2
                    except AssertionError:
                        continue
                    else:
                        passed = True
                        break
                assert passed, "No adequate window found"
                m_window = m[window]
                mean_window = mean(m_window)
                std_window = std(m_window)
                
                # now we're ready to sample that distribution and create our point
                new = (random.normal(loc=mean_window, scale = std_window, size = 1))[0]
                data = append(data,new)
                rms = append(rms, std_window)
            period_folded_model_file = file("period_folded_model.txt", "w")
#             model_file = file("model.txt", "w")
            for n in range(len(t_fold_model)):
                period_folded_model_file.write("%f\t%f\t%f\n" % (t_fold_model[n], data[n], rms[n]))
#                 model_file.write("%f\t%f\t%f\n" % (available[n], data[n], rms[n]))
#             model_file.close()
            period_folded_model_file.close()
            return {'flux':data, 'rms': rms}
        return model

#############################
# Use this code to generate out_dict as referenced above
#############################

class observatory_source_interface(object):
    def __init__(self):
        pass


    def get_peak_width(self, psd,imax):
        pmax = psd[imax]
        i = 0
        while ( (psd[imax-i:imax+1+i]>(pmax/2.)).sum()/(1.+2*i)==1 ):
            w = 1.+2*i
            i+=1
        return w


    def make_psd_plot(self, psd=None, srcid=None, freqin=None):
        """ Make PSD .png plots used in ALLStars webpages.
        """
        import time
        trys_left = 120
        while trys_left > 0:
            try:
                from matplotlib import pyplot as plt
                ### Plot the PSD(freq)
                psd_array = numpy.array(psd)
                #import matplotlib
                #matplotlib.use('PNG')
                #import matplotlib.pyplot as plt
                #from matplotlib import pyplot as plt
                #from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
                
                fig = plt.figure(figsize=(5,3), dpi=100)
                ax2 = fig.add_subplot(211)
                ax2.plot(freqin, numpy.log10(psd_array))
                ax2.set_ylim(0,3)
                ax2.set_yticks([3,2,1,0])
                ax2.set_ylabel("Log10(psd)")
                ax2.annotate("freq", xy=(.5, -0.05), xycoords='axes fraction',
                            horizontalalignment='center',
                            verticalalignment='top',
                            fontsize=10)
                ax2.set_title(str(srcid) + " Non-prewhitened, Power Spectral Density", fontsize=9)
                ax3 = fig.add_subplot(212)
                ax3.plot(numpy.log10(freqin), numpy.log10(psd_array))
                ax3.set_ylim(-3,3)
                ax3.set_xlim(-3,1)
                ax3.set_yticks([3,2,1,0,-1,-2,-3])
                ax3.set_yticklabels(['3','','','0','','','-3'])
                ax3.set_xticks([1,0,-1,-2,-3])
                ax3.set_ylabel("Log10(psd)")
                ax3.annotate("Log10(freq)", xy=(.5, -0.15), xycoords='axes fraction',
                            horizontalalignment='center',
                            verticalalignment='top',
                            fontsize=10)
                #plt.show()
                fpath = "/home/pteluser/scratch/tutor_psd_png/psd_%d.png" % (srcid)
                plt.savefig(fpath)
                fig.clf()
                trys_left = 0
                break
                #os.system('eog ' + fpath)
                #import pdb; pdb.set_trace()
                #print
            except:
                trys_left -= 1
                time.sleep(1)

        
    def get_2P_modeled_features(self, x=None, y=None, freq1_freq=None, srcid=None, ls_dict={}):
        """
        """
        out_dict = {}
        out_dict['model_phi1_phi2'] = 0.0 # NaN / divide by zero default value
        out_dict['model_min_delta_mags'] = 0.0
        out_dict['model_max_delta_mags'] = 0.0

        from scipy.optimize import fmin#, fmin_powell
        t_folded_phase = (x / (1./freq1_freq)) % 1.

        A = ls_dict['freq1']['harmonics_amplitude']
        y0 = ls_dict['freq1']['harmonics_y_offset']
        ph = ls_dict['freq1']['harmonics_rel_phase']

        def model_f(t):
            return A[0]*sin(2*pi   *t+ph[0]) + \
                   A[1]*sin(2*pi*2.*t+ph[1]) + \
                   A[2]*sin(2*pi*3.*t+ph[2]) + \
                   A[3]*sin(2*pi*4.*t+ph[3]) + \
                   A[4]*sin(2*pi*5.*t+ph[4]) + \
                   A[5]*sin(2*pi*6.*t+ph[5]) + \
                   A[6]*sin(2*pi*7.*t+ph[6]) + \
                   A[7]*sin(2*pi*8.*t+ph[7])

        def model_neg(t):
            return -1. * model_f(t)
        

        min_1_a = fmin(model_neg, 0.05)[0] # start finding 1st minima, at 5% of phase (fudge/magic number) > 0.018
        max_2_a = fmin(model_f, min_1_a + 0.01)[0]
        min_3_a = fmin(model_neg, max_2_a + 0.01)[0]
        max_4_a = fmin(model_f, min_3_a + 0.01)[0]

        try:
            out_dict['model_phi1_phi2'] = (min_3_a - max_2_a) / (max_4_a / min_3_a)
            out_dict['model_min_delta_mags'] = abs(model_f(min_1_a) - model_f(min_3_a))
            out_dict['model_max_delta_mags'] = abs(model_f(max_2_a) - model_f(max_4_a))
        except:
            pass # out_dict will just contains defauld 0.0 values

        if 0:
            from matplotlib import pyplot as plt
            fig = plt.figure()
            ax2 = fig.add_subplot(111)
            ax2.plot(t_folded_phase, y, 'bo')
            
            y_median = (max(y) - min(y))/2. + min(y)
            t_plot = arange(0.01, 1.0, 0.01)
            modl = model_f(t_plot) + y_median

            ax2.plot(t_plot, modl, 'go')

            ax2.plot([max_2_a, max_4_a], numpy.array([model_f(max_2_a), model_f(max_4_a)]) + y_median + 0.5, 'yo')
            ax2.plot([min_1_a, min_3_a], numpy.array([model_f(min_1_a), model_f(min_3_a)]) + y_median + 0.5, 'ko')
            
            ax2.set_title("srcid=%d   P=%f min_1=%f   max_2=%f   min_3=%f   max_4=%f" % (srcid, 1. / freq1_freq, min_1_a, max_2_a, min_3_a, max_4_a), fontsize=9)
            plt.savefig("/tmp/ggg.png")
            #os.system("eog /tmp/ggg.png &")
            plt.show()
            print()
            import pdb; pdb.set_trace()
            print()
        return out_dict


    def lomb_code(self, y, dy, x, sys_err=0.05, srcid=0):
        """ This function is used for final psd and final L-S freqs which are used as features.
        NOTE: lomb_extractor.py..lomb_extractor..extract() also generates psd, but its psd and objects  not used for the final L.S. freqs.

        NOTE: currently (20101120) This is adapted from Nat's run_lomb14.py
        
        """
        ### These are defaults found in run_lomb14.py::run_lomb() definition:
        nharm = 8 # nharm = 4
        num_freq_comps = 3
        do_models = True # 20120720: dstarr changes from False -> True
        tone_control = 5.0 #1.
        ##############

        dy0 = sqrt(dy**2 + sys_err**2)

        wt = 1./dy0**2
        x-=x.min()#needed for lomb() code to run in a fast amount of time

        chi0 = dot(y**2,wt)

        #alias_std = std( x-x.round() )

        Xmax = x.max()
        f0 = 1./Xmax
        df = 0.8/Xmax    # 20120202 :    0.1/Xmax
        fe = 33. #pre 20120126: 10. # 25
        numf = int((fe-f0)/df)
        freqin = f0 + df*arange(numf,dtype='float64') # OK

        ytest=1.*y # makes a copy of the array
        dof = n0 = len(x)
        hh = 1.+arange(nharm)

        out_dict = {}
        #prob = gammaincc(0.5*(n0-1.),0.5*chi0)
        #if (prob>0):
        #    lprob=log(prob)
        #else:
        #    lprob= -gammaln(0.5*(n0-1)) - 0.5*chi0 + 0.5*(n0-3)*log(0.5*chi0)
        #out_dict['sigma_vary'] = lprob2sigma(lprob)

        lambda0_range=[-log10(n0),8] # these numbers "fix" the strange-amplitude effect

        for i in range(num_freq_comps):
            if (i==0):
                psd,res = lombr(x,ytest,dy0,f0,df,numf, tone_control=tone_control,
                                lambda0_range=lambda0_range, nharm=nharm, detrend_order=1)                    
                ### I think it still makes sense to set these here, even though freq1 may be replaced by another non-alias freq.  This is because these are parameters that are derived from the first prewhitening application:
                out_dict['lambda'] = res['lambda0'] # 20120206 added
                out_dict['chi0'] = res['chi0']
                out_dict['time0'] = res['time0']
                out_dict['trend'] = res['trend_coef'][1] #temp_b
                out_dict['trend_error'] = res['trend_coef_error'][1] # temp_covar[1][1] # this is the stdev(b)**2
            else:
                psd,res = lombr(x,ytest,dy0,f0,df,numf, tone_control=tone_control,
                                lambda0_range=lambda0_range, nharm=nharm, detrend_order=0)
            ytest -= res['model']
            if (i==0):
                out_dict['varrat'] = dot(ytest**2,wt) / chi0
                #pre20110426: out_dict['cn0'] -= res['trend']*res['time0']
            dof -= n0 - res['nu']
            dstr = "freq%i" % (i + 1)

            if (do_models==True):
                #20120720Commentout#raise  # this needs to be moved below after alias stuff
                out_dict[dstr+'_model'] = res['model']
            out_dict[dstr] = {}
            freq_dict = out_dict[dstr]
            freq_dict["frequency"] = res['freq']
            freq_dict["signif"] = res['signif']
            freq_dict["psd"] = psd # 20110804 added just for self.make_psd_plot() use.
            freq_dict["f0"] = f0
            freq_dict["df"] = df
            freq_dict["numf"] = numf

            freq_dict['harmonics_amplitude'] = res['amplitude']
            freq_dict['harmonics_amplitude_error'] = res['amplitude_error']
            freq_dict['harmonics_rel_phase'] = res['rel_phase']
            freq_dict['harmonics_rel_phase_error'] = res['rel_phase_error']
            freq_dict['harmonics_nharm'] = nharm
            freq_dict['harmonics_time_offset'] = res['time0']
            freq_dict['harmonics_y_offset'] = res['cn0'] # 20110429: disable since it was previously mean subtracted and not useful, and not mean subtracted is avg-mag and essentially survey biased # out_dict['cn0']

        ### Here we check for "1-day" aliases in ASAS / Deboss sources
        dstr_alias = []
        dstr_all = ["freq%i" % (i + 1) for i in range(num_freq_comps)]
        ### 20120223 co:
        #for dstr in dstr_all:
        #    period = 1./out_dict[dstr]['frequency']
        #    if (((period >= 0.93) and (period <= 1.07) and 
        #         (out_dict[dstr]['signif'] < (3.771221/numpy.power(numpy.abs(period - 1.), 0.25) + 3.293027))) or
        #        ((period >= 0.485) and (period <= 0.515) and (out_dict[dstr]['signif'] < 10.0)) or
        #        ((period >= 0.325833333) and (period <= 0.340833333) and (out_dict[dstr]['signif'] < 8.0))):
        #        dstr_alias.append(dstr) # this frequency has a "1 day" alias (or 0.5 or 0.33
        #
        ### 20120212 Joey alias re-analysis:
        alias = [{'per':1., 
                  'p_low':0.92,
                  'p_high':1.08,
                  'alpha_1':8.191855,
                  'alpha_2':-7.976243},
                 {'per':0.5, 
                  'p_low':0.48,
                  'p_high':0.52,
                  'alpha_1':2.438913,
                  'alpha_2':0.9837243},
                 {'per':0.3333333333, 
                  'p_low':0.325,
                  'p_high':0.342,
                  'alpha_1':2.95749,
                  'alpha_2':-4.285432},
                 {'per':0.25, 
                  'p_low':0.245,
                  'p_high':0.255,
                  'alpha_1':1.347657,
                  'alpha_2':2.326338}]

        for dstr in dstr_all:
            period = 1./out_dict[dstr]['frequency']
            for a in alias:
                if ((period >= a['p_low']) and 
                    (period <= a['p_high']) and 
                    (out_dict[dstr]['signif'] < (a['alpha_1']/numpy.power(numpy.abs(period - a['per']), 0.25) + a['alpha_2']))):
                    dstr_alias.append(dstr) # this frequency has a "1 day" alias (or 0.5 or 0.33
                    break # only need to do this once per period, if an alias is found.
        
        out_dict['n_alias'] = len(dstr_alias)
        if 0:
            # 20120624 comment out the code which replaces the aliased freq1 with the next non-aliased one:
            if len(dstr_alias) > 0:
                ### Here we set the next non-alias frequency to freq1, etc:
                dstr_diff = list(set(dstr_all) - set(dstr_alias))
                dstr_diff.sort() # want to ensure that the lowest freq is first
                reorder = []
                for dstr in dstr_all:
                    if len(dstr_diff) > 0:
                        reorder.append(out_dict[dstr_diff.pop(0)])
                    else:
                        reorder.append(out_dict[dstr_alias.pop(0)])

                for i, dstr in enumerate(dstr_all):
                    out_dict[dstr] = reorder[i]
        
        if 0:
            ### Write PSD vs freq .png plots for AllStars web visualization:
            self.make_psd_plot(psd=out_dict['freq1']['psd'], srcid=srcid, freqin=freqin)

        var0 = var(ytest) - median(dy0)**2
        out_dict['sigma0'] = 0.
        if (var0 > 0.):
            out_dict['sigma0'] = sqrt(var0)
        out_dict['nu'] = dof
        out_dict['chi2'] = res['chi2'] #dot(ytest**2,wt)  # 20110512: res['chi2'] is the last freq (freq3)'s chi2, which is pretty similar to the old dot(ytest**2,wt) calculation which uses the signal removed ytest
        #out_dict['alias_std'] = alias_std
        out_dict['freq_binwidth'] = df
        out_dict['freq_searched_min']=min(freqin)
        out_dict['freq_searched_max']=max(freqin)
        out_dict['mad_of_model_residuals'] = median(abs(ytest - median(ytest)))

        ##### This is used for p2p_scatter_2praw feature:
        t_2per_fold = x % (2/out_dict['freq1']['frequency'])
        tups = zip(t_2per_fold, y)#, range(len(t_2per_fold)))
        tups.sort()
        t_2fold, m_2fold = zip(*tups) #So:  m_2fold[30] == y[i_fold[30]]
        m_2fold_array = numpy.array(m_2fold)
        sumsqr_diff_folded = numpy.sum((m_2fold_array[1:] - m_2fold_array[:-1])**2)
        sumsqr_diff_unfold = numpy.sum((y[1:] - y[:-1])**2)
        p2p_scatter_2praw = sumsqr_diff_folded / sumsqr_diff_unfold
        out_dict['p2p_scatter_2praw'] = p2p_scatter_2praw

        mad = numpy.median(numpy.abs(y - median(y)))
        out_dict['p2p_scatter_over_mad'] = numpy.median(numpy.abs(y[1:] - y[:-1])) / mad

        ### eta feature from arXiv 1101.3316 Kim QSO paper:
        out_dict['p2p_ssqr_diff_over_var'] = sumsqr_diff_unfold / ((len(y) - 1) * numpy.var(y))

        t_1per_fold = x % (1./out_dict['freq1']['frequency'])
        tups = zip(t_1per_fold, y)#, range(len(t_2per_fold)))
        tups.sort()
        t_1fold, m_1fold = zip(*tups) #So:  m_1fold[30] == y[i_fold[30]]
        m_1fold_array = numpy.array(m_1fold)
        out_dict['p2p_scatter_pfold_over_mad'] = \
                           numpy.median(numpy.abs(m_1fold_array[1:] - m_1fold_array[:-1])) / mad

        ######################## # # #
        ### This section is used to calculate Dubath (10. Percentile90:2P/P)
        ###     Which requires regenerating a model using 2P where P is the original found period
        ### NOTE: this essentially runs everything a second time, so makes feature
        ###     generation take roughly twice as long.

        model_vals = numpy.zeros(len(y))
        #all_model_vals = numpy.zeros(len(y))
        freq_2p = out_dict['freq1']['frequency'] * 0.5
        ytest_2p=1.*y # makes a copy of the array

        ### So here we force the freq to just 2*freq1_Period
        # - we also do not use linear detrending since we are not searching for freqs, and
        #   we want the resulting model to be smooth when in phase-space.  Detrending would result
        #   in non-smooth model when period folded
        psd,res = lombr(x,ytest_2p,dy0,freq_2p,df,1, tone_control=tone_control,
                            lambda0_range=lambda0_range, nharm=nharm, detrend_order=0)#1)
        model_vals += res['model']
        #all_model_vals += res['model']

        ytest_2p -= res['model']
        for i in range(1,num_freq_comps):
            psd,res = lombr(x,ytest_2p,dy0,f0,df,numf, tone_control=tone_control,
                            lambda0_range=lambda0_range, nharm=nharm, detrend_order=0)

            #all_model_vals += res['model']
            ytest_2p -= res['model']

        out_dict['medperc90_2p_p'] = scoreatpercentile(numpy.abs(ytest_2p), 90) / \
                                             scoreatpercentile(numpy.abs(ytest), 90)

        some_feats = self.get_2P_modeled_features(x=x, y=y, freq1_freq=out_dict['freq1']['frequency'], srcid=srcid, ls_dict=out_dict)
        out_dict.update(some_feats)

        ### So the following uses the 2*Period model, and gets a time-sorted, folded t and m:
        ### - NOTE: if this is succesful, I think a lot of other features could characterize the
        ###   shapes of the 2P folded data (not P or 2P dependent).
        ### - the reason we choose 2P is that occasionally for eclipsing
        ###   sources the LS code chooses 0.5 of true period (but never 2x
        ###   the true period).  slopes are not dependent upon the actual
        ###   period so 2P is fine if it gives a high chance of correct fitting.
        ### - NOTE: we only use the model from freq1 because this with its harmonics seems to
        ###   adequately model shapes such as RRLyr skewed sawtooth, multi minima of rvtau
        ###   without getting the scatter from using additional LS found frequencies.


        t_2per_fold = x % (1/freq_2p)
        tups = zip(t_2per_fold, model_vals)
        tups.sort()
        t_2fold, m_2fold = zip(*tups)
        t_2fold_array = numpy.array(t_2fold)
        m_2fold_array = numpy.array(m_2fold)
        slopes = (m_2fold_array[1:] - m_2fold_array[:-1]) / (t_2fold_array[1:] - t_2fold_array[:-1])
        out_dict['fold2P_slope_10percentile'] = scoreatpercentile(slopes,10) # this gets the steepest negative slope?
        out_dict['fold2P_slope_90percentile'] = scoreatpercentile(slopes,90) # this gets the steepest positive slope?

        return out_dict, ytest


class GetPeriodFoldForWeb:
    """
    To be called by tcp_html_show_recent_ptf_sources.py,
    which is called by a PHP script on lyra.

    Eventually this only prints a JSON javascript structure which
       contains period folded data for plottingL like: (mag vs time.)
    """
    def __init__(self):
        self.pars = { \
            'mysql_user':"pteluser",
            'mysql_hostname':"192.168.1.25",
            'mysql_database':'source_test_db',
            'mysql_port':3306,
            'featid_lookup_pkl_fpath':os.path.expandvars("$TCP_DATA_DIR/featname_featid_lookup.pkl"),
            'color_chris_folded':"#cc0033",
            'color_chris_model':"#ff3399",
            'color_feature_resampled':"#3399cc",
            'color_folded_data':"#000066",
            'tcptutor_hostname':'lyra.berkeley.edu',
            'tcptutor_username':'pteluser',
            'tcptutor_password':'Edwin_Hubble71',
            'tcptutor_port':     3306, 
            'tcptutor_database':'tutor',
            }


    def make_db_connection(self):
        """
        """
        self.db = MySQLdb.connect(host=self.pars['mysql_hostname'],
                             user=self.pars['mysql_user'],
                             db=self.pars['mysql_database'],
                             port=self.pars['mysql_port'])
        self.cursor = self.db.cursor()

        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()



    def generate_featname_featid_lookup(self, filter_id=8):
        """ Generate a RDB feature table lookup dictionary for: 
        feat_id : feat_value
        """
        import cPickle
        # TODO: if not .pkl file exists...
        if os.path.exists(self.pars['featid_lookup_pkl_fpath']):
            fp = open(self.pars['featid_lookup_pkl_fpath'])
            self.featname_lookup = cPickle.load(fp)
            fp.close()
            return
        else:
            select_str = "SELECT feat_name, feat_id FROM source_test_db.feat_lookup WHERE filter_id = %d" % (filter_id)
            self.cursor.execute(select_str)

            results = self.cursor.fetchall()
            self.cursor.close()
            self.featname_lookup = {}
            for (feat_name, feat_id) in results:
                self.featname_lookup[feat_name] = feat_id
            
            fp = open(self.pars['featid_lookup_pkl_fpath'], 'w')
            cPickle.dump(self.featname_lookup, fp)
            fp.close()
            return


    def get_source_arrays(self, source_id):
        """ Retrieve source m, t from rdb.
        """

        #select_str = """SELECT object_test_db.obj_srcid_lookup.src_id, 
        #                       object_test_db.ptf_events.ujd, 
        #                       object_test_db.ptf_events.mag, 
        #                       object_test_db.ptf_events.mag_err 
        #                 FROM object_test_db.obj_srcid_lookup 
        #                 JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id = object_test_db.obj_srcid_lookup.obj_id) 
        #                 WHERE survey_id = 3 AND src_id = %d """ % (source_id)

        # 20091030: dstarr comments out:
        #select_str = """SELECT object_test_db.obj_srcid_lookup.src_id, 
        #                       object_test_db.ptf_events.ujd,
        #                       (-2.5 * LOG10(object_test_db.ptf_events.flux_aper + object_test_db.ptf_events.f_aper) + object_test_db.ptf_events.ub1_zp_ref) AS m_total,
        #                       object_test_db.ptf_events.mag_err 
        #                 FROM object_test_db.obj_srcid_lookup 
        #                 JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id = object_test_db.obj_srcid_lookup.obj_id) 
        #                 WHERE survey_id = 3 AND src_id = %d
        #                 ORDER BY object_test_db.ptf_events.ujd""" % (source_id)

        # 20091030: dstarr instead uses:
        select_str = """SELECT object_test_db.obj_srcid_lookup.src_id, 
                               object_test_db.ptf_events.ujd,
                               object_test_db.ptf_events.mag AS m_total,
                               object_test_db.ptf_events.mag_err 
                         FROM object_test_db.obj_srcid_lookup 
                         JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id = object_test_db.obj_srcid_lookup.obj_id) 
                         WHERE survey_id = 3 AND src_id = %d
                         ORDER BY object_test_db.ptf_events.ujd""" % (source_id)


        #Testing fluxes
##         select_str = """SELECT object_test_db.obj_srcid_lookup.src_id, 
##                                object_test_db.ptf_events.ujd,
##                                object_test_db.ptf_events.flux,
##                                object_test_db.ptf_events.flux_err 
##                          FROM object_test_db.obj_srcid_lookup 
##                          JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id = object_test_db.obj_srcid_lookup.obj_id) 
##                          WHERE survey_id = 3 AND src_id = %d
##                          ORDER BY object_test_db.ptf_events.ujd""" % (source_id)

        self.cursor.execute(select_str)

        t_list = [] 
        m_list = []
        merr_list = []

        results = self.cursor.fetchall()

        # TODO: maybe close DB connection too.
        for row in results:
            t_list.append(row[1])
            m_list.append(row[2])
            merr_list.append(row[3])

        src_dict = {}
        src_dict['src_id'] = results[0][0]
        src_dict['t'] = numpy.array(t_list)
        src_dict['m'] = numpy.array(m_list)
        src_dict['m_err'] = numpy.array(merr_list)
        #src_dict['m_err'] = []   #/@/ Justin changed 20090804
        return src_dict


    def get_source_arrays__dotastro(self, source_id):
        """ Retrieve source m, t from rdb.

        This version of the method queries the DotAstro.org / TUTOR database on lyra
        """

        # TODO: need to determine shich filter has the most number of epochs
        # TODO: need to retrieve the magnitudes(time) from dotastro database for this fitler
        #                                 m_err(time)
        srcid_dotastro = source_id - 100000000

        # first need to use observations.source_id == <src_id> to get the
        #    observations.observation_id
        #    then select count(*) from obs_data.observation_id==<observation_id> and see which observation_id (eg filter) has the most epochs.
        # then retrieve all mag, m_err, time for this observation_id and return it.

        ##### First Retrieve the filter for the srcid from the tranx RDB

        select_str = "SELECT feats_used_filt FROM source_test_db.srcid_lookup WHERE src_id = %d" % (source_id)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        if len(results) == 0:
            return {}
        feat_filter = results[0][0]

        ##### Determine the filter / observation_id which has the most number of epochs,
        #     since this currently corresponds to the timeseries which the feature algorithms
        #     were generated using (eg not using the combo_band).
        #select_str = """SELECT filters.*, count(obs_data.obsdata_val) AS epoch_count, observations.observation_id
        #                FROM observations
        #                JOIN obs_data USING (observation_id)
        #                JOIN filters USING (filter_id) 
        #                WHERE observations.source_id=%d AND filters.filter_name like "%s%"
        #                GROUP BY observations.observation_id
        #                ORDER BY epoch_count DESC""" % (srcid_dotastro, feat_filter[0])

        select_str = """SELECT obs_data.obsdata_time, obs_data.obsdata_val, obs_data.obsdata_err
                        FROM observations
                        JOIN obs_data USING (observation_id)
                        JOIN filters USING (filter_id) 
                        WHERE observations.source_id=%d AND filters.filter_name like "%s""" % (srcid_dotastro, feat_filter[0]) + '%"'
        #'" """
        self.tutor_cursor.execute(select_str)

        t_list = [] 
        m_list = []
        merr_list = []

        results = self.tutor_cursor.fetchall()
        # TODO: maybe close DB connection too.
        for row in results:
            t_list.append(row[0])
            m_list.append(row[1])
            merr_list.append(row[2])

        src_dict = {}
        src_dict['src_id'] = source_id
        src_dict['t'] = numpy.array(t_list)
        src_dict['m'] = numpy.array(m_list)
        src_dict['m_err'] = numpy.array(merr_list)
        #src_dict['m_err'] = []   #/@/ Justin changed 20090804
        return src_dict


    ### This function is no longer used by lomb_scargle_extractor.  ONly Noisification/Chris related lightcurve.py functions use it.
    def generate_lomb_period_fold(self, src_dict, return_option='top4lombfreqs_withharmonics'):
        """ Re-generate lomb scargle using Chris code.  

        Return period folded m(t) and evenly resampled m(t) in a dictionary.
        """

        obs = observatory_source_interface()
        out_dict, cn_output = obs.lomb_code(src_dict['m'],
                                           src_dict['m_err'],
                                           src_dict['t'])
        

        return out_dict



    def using_features_generate_resampled(self, src_dict):
        """ Using features retrieved from RDB and stored in src_dict,
        form a re-sampled m(t) and return in a dictionary.
        """
        ##### TODO: Get the frequency components from feature tables if
        #           available.  
        #       - Construct y_axis for some generated time-axis.

        # TODO: using:
        #              self.featname_lookup
        #       form a SELECT string which retrieves all features of interest
        #   then gemerate an out_dict{} so that this works:
            
        select_str = """SELECT
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s,
        (SELECT feat_val FROM source_test_db.feat_values WHERE src_id=%d AND feat_id=%d) AS %s
        """%(src_dict['src_id'], self.featname_lookup['freq1_harmonics_freq_0'], 'freq1_harmonics_freq_0',
             src_dict['src_id'], self.featname_lookup['freq2_harmonics_freq_0'], 'freq2_harmonics_freq_0',
             src_dict['src_id'], self.featname_lookup['freq3_harmonics_freq_0'], 'freq3_harmonics_freq_0',
             src_dict['src_id'], self.featname_lookup['freq1_harmonics_amplitude_0'], 'freq1_harmonics_amplitude_0',
             src_dict['src_id'], self.featname_lookup['freq2_harmonics_amplitude_0'], 'freq2_harmonics_amplitude_0',
             src_dict['src_id'], self.featname_lookup['freq3_harmonics_amplitude_0'], 'freq3_harmonics_amplitude_0',
             src_dict['src_id'], self.featname_lookup['freq1_harmonics_rel_phase_0'], 'freq1_harmonics_rel_phase_0',
             src_dict['src_id'], self.featname_lookup['freq2_harmonics_rel_phase_0'], 'freq2_harmonics_rel_phase_0',
             src_dict['src_id'], self.featname_lookup['freq3_harmonics_rel_phase_0'], 'freq3_harmonics_rel_phase_0',
             src_dict['src_id'], self.featname_lookup['freq1_signif'], 'freq1_signif',
             src_dict['src_id'], self.featname_lookup['freq2_signif'], 'freq2_signif',
            )

        self.cursor.execute(select_str)

        result = self.cursor.fetchall()

        #############

        freq_list = []
        amp_list = []
        rel_phase = []

        freq_list.append(result[0][0])
        freq_list.append(result[0][1])
        freq_list.append(result[0][2])
        amp_list.append(result[0][3])
        amp_list.append(result[0][4])
        amp_list.append(result[0][5])
        rel_phase.append(result[0][6])
        rel_phase.append(result[0][7])
        rel_phase.append(result[0][8])

        freq1_harmonics_freq_0 = result[0][0]
        freq2_harmonics_freq_0 = result[0][1]
        freq1_signif = result[0][9]
        freq2_signif = result[0][10]
        freq1_harmonics_rel_phase_0 = result[0][6]
        
        #try:
        #    plot_period = 1.0 / freq_list[0]
        #    x_axis = arange(0,plot_period, .01)
        #
        #    y_axis= amp_list[0]*sin(2*numpy.pi*freq_list[0]*(x_axis-rel_phase[0]))+\
        #        amp_list[1]*sin(2*numpy.pi*freq_list[1]*(x_axis-rel_phase[1]))+\
        #        amp_list[2]*sin(2*numpy.pi*freq_list[2]*(x_axis-rel_phase[2]))
        #
        #    feature_resampled_dict = {'feature_resampled':{'t':x_axis, 'm':y_axis, 
        #                                               'color':self.pars['color_feature_resampled']}}
        #except:
        #    feature_resampled_dict = {'feature_resampled':{'t':[], 'm':[], 
        #                                               'color':self.pars['color_feature_resampled']}}

            
        ##### Here we period fold the existing data.
        f = (freq1_harmonics_freq_0)
        if freq2_signif > freq1_signif:
            f = freq2_harmonics_freq_0
        
        # find the phase:
        p = freq1_harmonics_rel_phase_0
        
        #period-fold the available times
        t_fold = mod( src_dict['t'] + p/(2*pi*f) , (1./f) )
        ##### This is the earlier data:
        try:
            plot_period = 1.0 / freq_list[0]
            x_axis = arange(0,plot_period, .001)

            #KLUDGE: I fake the generated LC mag amplitude & offset using real data:
            amp_kludge = max(src_dict['m']) - min(src_dict['m'])
            m_offset_kludge = amp_kludge/2. + min(src_dict['m'])

            # 20090720: dstarr replaces the following with something 4-6 lines below
            #y_axis= (amp_list[0]*sin(2*numpy.pi*freq_list[0]*(x_axis-rel_phase[0]))+\
            #    amp_list[1]*sin(2*numpy.pi*freq_list[1]*(x_axis-rel_phase[1]))+\
            #    amp_list[2]*sin(2*numpy.pi*freq_list[2]*(x_axis-rel_phase[2]))) 
            y_axis= (amp_list[0]*sin(2*numpy.pi*freq_list[0]*(x_axis)))+\
                amp_list[1]*sin(2*numpy.pi*freq_list[1]*(x_axis) + rel_phase[1])+\
                amp_list[2]*sin(2*numpy.pi*freq_list[2]*(x_axis) + rel_phase[2]) 

            y_axis= (amp_list[0]*sin(2*numpy.pi*freq_list[0]*(x_axis) + rel_phase[0]))+\
                amp_list[1]*sin(2*numpy.pi*freq_list[1]*(x_axis) + rel_phase[1])+\
                amp_list[2]*sin(2*numpy.pi*freq_list[2]*(x_axis) + rel_phase[2]) 

            amp_sampled_m = max(y_axis) - min(y_axis)
            amp_sampled_offset = amp_sampled_m / 2. + min(y_axis)

            y_axis = ((y_axis -amp_sampled_offset) / amp_sampled_m) * amp_kludge + m_offset_kludge

            feature_resampled_dict = {'DB features Generated':{'t':x_axis, 'm':y_axis, 
                                                       'color':self.pars['color_feature_resampled']}}
        except:
            feature_resampled_dict = {'DB features Generated':{'t':[], 'm':[], 'points': {'radius': 0.1},
                                                       'color':self.pars['color_feature_resampled']}}
        #####

        feature_resampled_dict.update({"DB features Period Folded":{'t':t_fold, 'm':src_dict['m'], 
                                                       'color':self.pars['color_folded_data']}})

        html_str = ""
        for i in range(len(amp_list)):
            html_str += "<tr><td style='font-size:11'>"+str(i)+"</td><td style='font-size:11'>"+str(amp_list[i])+"</td><td style='font-size:11'>"+str(freq_list[i])+"</td><td style='font-size:11'>"+str(rel_phase[i])+"</td><td style='font-size:11'>"+str(1/freq_list[i])+"</td></tr> \n"

        if len(sys.argv) >= 2:
            if sys.argv[1] == 'get_table_data':
                return html_str
        
        return feature_resampled_dict

    def form_json(self, combo_dict):
        """ Given period folded structures, form a JSON-like string, return.
            Justin changing order in list since dictionary model blocks folded data
        """
        json_list = []
        data_list1 = []
        for i in range(len(combo_dict['Actual Mags folded']['t'])):
            data_list1.append([combo_dict['Actual Mags folded']['t'][i],combo_dict['Actual Mags folded']['m'][i]])
        data_list2 = []
        for i in range(len(combo_dict['Folded Model']['t'])):
            data_list2.append([combo_dict['Folded Model']['t'][i],combo_dict['Folded Model']['m'][i]])
        data_list3 = []
        for i in range(len(combo_dict['Model with dictionary values']['t'])):
            data_list3.append([combo_dict['Model with dictionary values']['t'][i],combo_dict['Model with dictionary values']['m'][i]])
        json_list.append({'label':'Model with dictionary values', 
                          'color':'#F2BABB',
                          'data':data_list3})
        json_list.append({'label':'Folded Model', 
                          'color':'#BB8800',
                          'data':data_list2})
        json_list.append({'label':'Actual Mags folded', 
                          'color':'#194E84',
                          'data':data_list1})
            
        json_string_single_quotes = pprint.pformat(json_list)
        json_string = json_string_single_quotes.replace("'",'"')
        return json_string



    def main(self, source_id):
        """
        Eventually this function will calculate the period fold
        plotting x,y array and return a string with this JSON-like
        output, such as:

           [{"label":"Period Fold", "color":#36477b, 
                                    "data":[[1,1],[2,4],[3,9],[4,16]]}]
        """
        print("make db connect")
        self.make_db_connection()
        print("before mysql query")
        self.generate_featname_featid_lookup()
        print("after mysql query")
        if source_id >= 100000000:
            src_dict = self.get_source_arrays__dotastro(source_id)
        else:
            src_dict = self.get_source_arrays(source_id)
        print("finished generating src_dict")
        lc_dict = {}
        lomb_folded_dict = self.generate_lomb_period_fold(src_dict)
        lc_dict.update(lomb_folded_dict)

        json_string = self.form_json(lc_dict)
        return json_string
    ####### Justin adding to view fluxes folded #######
    def online_dictionary(self, source_id, return_option="database"):
        self.make_db_connection()
        self.generate_featname_featid_lookup()
        src_dict = self.get_source_arrays(source_id)

        db_dict = self.generate_lomb_period_fold(src_dict,return_option="db_dictionary")
        return db_dict

        

    def html_table(self, source_id, return_option="html"):
        self.make_db_connection()
        self.generate_featname_featid_lookup()
        
        src_dict = self.get_source_arrays(source_id)
        lomb_str = self.generate_lomb_period_fold(src_dict)
        db_str = self.using_features_generate_resampled(src_dict)
        final_str = "<table border=1 cellspacing=2 cellpadding=2> \n"
        final_str += "<th style='font-size:15'>Chris Values</th><th style='font-size:15'>DB values</th> \n"
        final_str += "<tr><table border=1 cellspacing=2 cellpadding=2> \n"
        final_str += "<th style='font-size:13'>Harmonic Num</th><th style='font-size:13'>Amplitude</th><th style='font-size:13'>Freq</th><th style='font-size:13'>Offset</th><th style='font-size:13'> 1 / freq</th> \n"
        final_str += lomb_str+"</table></tr> \n"
        final_str += "<tr><table border=1 cellspacing=2 cellpadding=2> \n"
        final_str += "<th style='font-size:13'>Harmonic Num</th><th style='font-size:13'>Amplitude</th><th style='font-size:13'>Freq</th><th style='font-size:13'>Offset</th><th style='font-size:13'> 1 / freq</th> \n"
        final_str += db_str+"</table></tr></table>"

        return final_str

    def for_testing(self, source_id):
        pass


# 20090806: dstarr does this since sys.argv doesnt work for module imports:
sys_argv_1 = None
sys_argv_2 = None
if len(sys.argv) >= 3:
    sys_argv_1 = sys.argv[1]
    sys_argv_2 = sys.argv[2]

if sys_argv_1 == 'get_period_fold2':
    source_id = int(sys_argv_2)
    GetPeriodFoldForWeb = GetPeriodFoldForWeb()
    json_out_string = GetPeriodFoldForWeb.main(source_id)
    print(json_out_string)

if sys_argv_1 == 'get_period_fold4':
    from lomb_scargle import *
    from pre_whiten import *
    from numpy import random
    time = arange(0,7.5,0.3)
    mags = sin(time)
    mags += 15. + 0.1*random.normal(size=len(time))
    psd,freq,signi,simsigni,psdpeak = lomb(time,mags)
    i0=psd.argmax(); freq0=freq[i0]
    cn, out_dict =  pre_whiten(time,mags, freq0)
    plot (time,mags,'o')
    plot (time,mags-cn)
    A = out_dict['amplitude']
    dA = out_dict['amplitude_error']
    ph = out_dict['rel_phase']
    t0 = out_dict['time_offset']
    y0 = out_dict['y_offset']
    f = out_dict['freq']
    tt = min(time) + (max(time)-min(time))*arange(1000)/999.
    modl = y0 + A[0]*sin(2*pi*f[0]*(tt-t0)+ph[0])
    for i in range(len(f)-1):
        j=i+1
        modl += A[j]*sin(2*pi*f[j]*(tt-t0)+ph[j])
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    ax.plot(tt,modl, 'ro')
    ax.plot(time, mags, 'bo')
    pyplot.show()
    
if sys_argv_1 == 'get_period_fold3':
    x = arange(0,7.5, 0.3)
    y = numpy.sin(x)
    y_err = []
    y += 15. + 0.1*random.normal(size=len(x))
    #now add magnitude offest
    src_dict = {'t': x,
                'm': y,
                'm_err':y_err}
    get = GetPeriodFoldForWeb()
    lomb_folded_dict = get.generate_lomb_period_fold(src_dict)
    fig = pyplot.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(lomb_folded_dict['Actual Mags folded']['t'],lomb_folded_dict['Actual Mags folded']['m'], 'bo')
    ax1.plot(lomb_folded_dict['Chris Period Folded:  JUSTIN MODIFIED']['t'],lomb_folded_dict['Chris Period Folded:  JUSTIN MODIFIED']['m'], 'ro')
    ax1.plot(lomb_folded_dict['Chris model generated (w/ new_offset)']['t'],lomb_folded_dict['Chris model generated (w/ new_offset)']['m'], 'yo')
    ax1.invert_yaxis()
    pyplot.show()

if sys_argv_1 == 'get_period_fold5':
    source_id = int(sys_argv_2)
    GetPeriodFoldForWeb = GetPeriodFoldForWeb()
    db_dict = GetPeriodFoldForWeb.online_dictionary(source_id)
    print(db_dict)

if __name__ == '__main__':
    ### 20101012: Added __main__ for testing use only, to see tracebacks from LombScargle code.


    source_id = 100149386
    gpffw =GetPeriodFoldForWeb()
    #db_dict = gpffw.main(source_id=source_id)
    ### The following is done in gpffw.main(), but is hardcoded
    #   here to keep from doing DB connections
    src_dict = {'m': array([ \
        18.172,  18.556]),
 'm_err': array([ 0.045,  0.046]),
 'src_id': 100149386,
 't': array([ 2451214.70375,  2451215.60842])}

    
    lomb_folded_dict = gpffw.generate_lomb_period_fold(src_dict, return_option='top4lombfreqs_withharmonics')
    import pprint
    pprint.pprint(lomb_folded_dict)

