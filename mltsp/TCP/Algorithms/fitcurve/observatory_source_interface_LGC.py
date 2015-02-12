#!/usr/bin/env python
# encoding: utf-8
"""
the observatory emits certain demands, fulfilled by this interface
"""
from __future__ import print_function
import sys
import os

from pylab import *

from numpy import *
from scipy.optimize import fmin, brute
from scipy import random
from numpy.random import rand

from xml_reading import xml_reading
from janskies_converter import janskies_converter

import lomb_scargle
from gcd_utilities import gcd_array
from scipy.fftpack import fftfreq, ifft
import pre_whiten

import pickle

import copy

import ephem

from spline_fit import spline_fitted_magnitudes, window_creator , window_tttimes, spline_fitted_magnitudes_brute

from numpy.random import permutation

        
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
                assert period < available.ptp()/3, "period is greater than one third of the duration of available data"
                # window is 2% of the period
                passed = False
                for x in arange(0.01, 0.1, 0.01):
                    t_min = time - x * period
                    t_max = time + x * period
                    window = logical_and((t_fold < t_max), (t_fold > t_min)) # picks the available times that are within that window
                    try:
                        # there must be more than 3 points in the window for this to work:
                        assert (window.sum() > 5), str(time)
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
        
class spline_model(lomb_model):
    """ Uses a spline fit as model """
    def create_model(self,available, m , m_err, out_dict):
        def model(times):
            assert available.ptp() > times.ptp(), "not enough range in available time data to perform spline fit"
            delta = available[0] - times[0]
            shifted_times = times + delta
            mindiff = min(abs(diff(shifted_times)))
            possible_range = max(available) - max(shifted_times)
            dt = arange(0,possible_range, mindiff/5.*sign(possible_range))
            rand_dt = dt[permutation(dt.size)]
            ispassed = False
            for t in rand_dt:
                try:
                    trial_times = shifted_times+t # try to advance shifted_times by amount t and see if that works
                    for i in arange(trial_times.size):
                        difftimes = available - trial_times[i]
                        absdiff = abs(difftimes)
                        nearest = absdiff.argmin() # the distance to the two nearest points
                        other_side = nearest - 1 * sign(difftimes[nearest])
                        distance_to_nearest = absdiff[nearest]
                        distance_to_other_side = absdiff[other_side]
                        
                        # check that the distance to the nearest points is smaller than the minimum separation between desired times
                        assert distance_to_nearest < mindiff, "distance to the nearest points must be smaller than the minimum separation between desired times"
                        assert distance_to_other_side < mindiff, "distance to the other side must also be smaller than the minimum separation between desired times"
                        shift_worked = t
                        desired_times = shifted_times + t
                        window = logical_and(available > (desired_times.min()-10.), available < (desired_times.max()+10))

                        data, rms = spline_fitted_magnitudes(available, m, m_err, desired_times, mindiff = mindiff)
                except AssertionError as description:
                    latest_description = description
                    continue
                else:
                    print("passed")
                    ispassed = True
                    break
            assert ispassed, "Didn't find a time shift that works, latest reason:" + str(latest_description)
            time_fold, time_model_fold = period_folding_model().period_folding(desired_times, available, m , m_err, out_dict, doplot = False)
            model_file = file("model.txt", "w")
            for n in range(len(desired_times)):
                model_file.write("%f\t%f\t%f\n" % (desired_times[n], data[n], rms[n]))
            model_file.close()
            return {'flux':data, 'rms':rms, 'new_times':desired_times}
        return model
        
class brutespline(lomb_model):
    def create_model(self,available, m , m_err, out_dict):
        def model(times):
            assert available.ptp() > times.ptp(), "not enough range in available time data to perform spline fit"
            delta = available[0] - times[0]
            shifted_times = times + delta
            possible_range = available[-2] - max(shifted_times)
            mindiff = min(abs(diff(shifted_times)))
            dt = arange(available[1],possible_range, mindiff/5.*sign(possible_range))
            rand_dt = dt[permutation(dt.size)]
            t= rand_dt[0]
            ispassed = False
            desired_times = shifted_times+t # try to advance shifted_times by amount t and see if that works
            data, rms = spline_fitted_magnitudes_brute(available, m, m_err, desired_times)
            time_fold, time_model_fold = period_folding_model().period_folding(desired_times, available, m , m_err, out_dict, doplot = False)
            model_file = file("model.txt", "w")
            for n in range(len(desired_times)):
                model_file.write("%f\t%f\t%f\n" % (desired_times[n], data[n], rms[n]))
            model_file.close()
            return {'flux':data, 'rms':rms, 'new_times':desired_times}
        return model
        
            

class observatory_source_interface(object):
    # # # # # #: dstarr changes this to initially exclude spline models.  Only want period_folded.
    if len(sys.argv) > 4:
        # xxx
        if sys.argv[4] == 'tutor':
            list_of_models = [period_folding_model()]
        else:
            list_of_models = [period_folding_model(), spline_model()]
    else:
        list_of_models = [period_folding_model(), spline_model()]

    def __init__(self):
        pass
    def get_out_dict(self, available, m, m_err, xml_file):
        # time = x
        # time.sort()
        # 20080520: dstarr finds that SDSS-II data can have "duplicate" data points, which a noisy result of the photometric pipeline(s?).  The median() can often be 0.0, which fouls things.  So I use a mean here:
        #dt = median( time[1:]-time[:-1] )
        dt = median( available[1:]-available[:-1] )
        maxlogx = log(0.5/dt) # max frequency is ~ the sampling rate
        minlogx = log(0.5/(available[-1]-available[0])) #min frequency is 0.5/T
        # sample the PSD with 1% fractional precision
        M=long(ceil( (maxlogx-minlogx)*1000. )) # could change 100 to 1000 for higher resolution
        frequencies = exp(maxlogx-arange(M, dtype=float) / (M-1.) * (maxlogx-minlogx))
        out_dict = self.lomb_code(frequencies, m, m_err, available)
        f = (out_dict["freq1"]["harmonics_freq"][0])
        if out_dict["freq2"]["signif"] > out_dict["freq1"]["signif"]:
            f = out_dict["freq2"]["frequency"]
        narrow_frequencies = arange(0.99*f,1.01*f, 0.00001)
        out_dict = self.lomb_code(narrow_frequencies, m, m_err, available)
        return out_dict
    def lomb_code(self,frequencies, m, m_err, available):
        len_av = len(available)
        dx = zeros(len_av,dtype=float)
        num_freq_comps = 4
        out_dict={}
        ytest=m
        dof = len_av # don't know why we need to have two separate variables for this
        if (dof>=5):
            out_dict['frequencies'] = frequencies
            out_dict['freq_searched_min']=min(frequencies)
            out_dict['freq_searched_max']=max(frequencies)
            for i in range(num_freq_comps):
                psd, freqs, signi, sim_signi, peak_sort = lomb_scargle.lomb(available,ytest,delta_time=dx, signal_err=m_err,freqin=frequencies,verbosity=2)
                imax = psd.argmax()
                freq_max = freqs[imax]
                void_ytest, harm_dict = pre_whiten.pre_whiten(available, ytest, freq_max, delta_time=dx, signal_err=m_err, dof=dof, nharm_min=1, nharm_max=99)
                dstr = "freq%i" % (i+1)
                # check for nharm and rerun
                nharm = harm_dict["nharm"]
                if nharm == 0:
                    break
                print("frequency", i+1, "nharm", nharm) 
                ytest, harm_dict = pre_whiten.pre_whiten(available, ytest, freq_max, delta_time=dx, signal_err=m_err, dof=dof, nharm_min=nharm, nharm_max=nharm)
                out_dict[dstr] = {}
                freq_dict = out_dict[dstr]
                freq_dict["signif"] = signi
                freq_dict["frequency"] = freq_max
                for elem_k, elem_v in harm_dict.items():
                    freq_dict["harmonics_" + elem_k] = elem_v
                    dof = dof - harm_dict['nharm']*2.
        return out_dict

    def form_vsrc_xml_ts(self, old_ts_dict, times, mags, merrs):
        """ form a s_dict['ts'] style dict and return it.
        """
        new_ts = copy.deepcopy(old_ts_dict)
        assert len(new_ts.keys()) == 1 # DEBUG KLUDGE TEST
        band_dict = new_ts.values()[0]
        band_dict['m'] = mags
        band_dict['m_err'] = merrs
        band_dict['t'] = times
        return new_ts


    def obs_request(self, target, needed, band="u"):
        # first, have xml_reading parse the xml:
        xml_file, picked_band = self.pick_object(target,band)
        self.xml_file = xml_file
        s_dict, source = xml_reading().read_xml(xml_file = xml_file)
        #  we're going to dig through the dictionary and define a few useful variables
        # this is the sub-dictionary that contains the actually time series data, it is defined by db_importer:
        ts = s_dict["ts"]
        # ts's sub-entries are the different bands available for this source
        # we choose the band we want:
        picked_band_key = picked_band
        for item in ts.keys():
            if picked_band == item.split(":")[0]:
                try:
                    picked_band_key = picked_band + ":" + item.split(":")[1]
                except IndexError:
                    break
        print(picked_band_key)
        try:
            if len(sys.argv) > 4:
                if sys.argv[4] != 'tutor':
                    band_dic = ts[picked_band]
                else:
                    if picked_band == 'any':
                        band_dic = ts.values()[0]
                    else:
                        bands = ts.keys()
                        band_dic = {}
                        for vsrc_band in bands:
                            if picked_band in vsrc_band:
                                band_dic = ts[vsrc_band]
                                break
                        if len(band_dic) == 0:
                            raise KeyError
            else:
                band_dic = ts[picked_band]
        except KeyError:
            print("print ts.keys()", ts.keys())
            raise KeyError
        # we then make a copy of this dictionary for us to work with:
        my_dic = band_dic.copy()
        # we now prepare for the lomb scargle periodogram
        available = array(my_dic["t"]) # available times
        available = available - min(available)
        m = array(my_dic["m"])
        m_err = array(my_dic["m_err"])
        self.out_dict = self.get_out_dict(available, m, m_err, xml_file)
        passed = False
        for model in self.list_of_models:
            print("trying", model)
            try:
                model_function = model.create_model(available,m,m_err, self.out_dict)
                model_output = model_function(needed)
            except AssertionError as description:
                print("we caught an assertion error %s" % description)
                continue
            else:
                passed = True
                break
        print(passed, "passed?")
        assert passed, "None of the models supplied worked :-/"
        # reduce my_dic to these picked times
        model_flux = model_output["flux"]
        model_rms = model_output["rms"]
        m_new = model_flux
        model_lightcurve = []
        avg_model_mag = model_flux.mean()
        vosource_fpath = sys.argv[1]

        # TODO: replace modeled_lightcurves/ with some explicit, command-line stated  dirpath
        if vosource_fpath.count('/') == 0:
            sourceid = vosource_fpath[:-4]
        else:
            sourceid = vosource_fpath[vosource_fpath.rfind('/')+1:\
                                      vosource_fpath.rfind('.')]
        ##### The following will automatically contain the TUTOR Classification info:
        temp_ts = {}
        temp_ts['default_band'] = my_dic
        ### OLD (gets full, original t,m,merr):
        #s_dict['ts'] = temp_ts
        s_dict['ts'] = self.form_vsrc_xml_ts(temp_ts, needed, model_output["flux"], model_output["rms"])
        source.source_dict_to_xml(s_dict)
        out_xml_fpath = "OutputVOSources/%s_%s.xml" % (sourceid, str(avg_model_mag))
        # DEBUG/KLUDGE:  (the first generated model seems to have an average mag of 0, while subsequent are >>0)  I skip the ~0 source:
        if avg_model_mag > 3:
            source.write_xml(out_xml_fpath=out_xml_fpath)

        first_time = needed[0]
        model_lightcurve_file2 = file("model.txt", "w")
        model_lightcurve_file = file("modeled_lightcurves/" + sourceid + "_" + str(avg_model_mag), "w")
        for n in range(len(needed)):
            model_lightcurve_file.write(str(needed[n]) + "\t" + str(model_flux[n]) + "\t" + str(model_rms[n]) + "\n")
            model_lightcurve_file2.write(str(needed[n]-first_time) + "\t" + str(model_flux[n]) + "\t" + str(model_rms[n]) + "\n")
            model_lightcurve.append([needed[n], model_flux[n], model_rms[n]])
        model_lightcurve_file.close()
        model_lightcurve_file2.close()
        my_dic["t"] = needed
        my_dic["m"] = m_new + m.mean()
        my_dic["m_err"] = model_rms
        return {"old data": m, "new data": my_dic["m"], "difference": None, "needed": needed, "available":available, "m_err": m_err, "out_dict": self.out_dict, "my_dic": my_dic, "s_dict":s_dict, "source": source, "old_xmlfile":xml_file}
    def pick_object(self,target, band = "u"):
        if len(sys.argv) > 1:
            xml_filename = sys.argv[1]
            band = sys.argv[2]
            assert xml_filename.split('.')[1] == 'xml'
            if xml_filename.count('/') == 0:
                xml_fpath = "VOsources/" + xml_filename
            else:
                xml_fpath = xml_filename # I expect this to be a full, expanded filepath to .xml
            return xml_fpath, band
    def read_mags_and_convert(self,my_dic,band):
        """ reads the magnitudes from the source dictionary and converts them to janskies 
        this function assumes the vo_source structure
        """
        # each band has an entry for the actual data, the magnitudes, which we convert to a numpy array:
        magnitudes = array(my_dic['m'])
        # and the uncertainties:
        errors = array(my_dic["m_err"])
        # send this off to a separate function in janskies_converter for conversion
        janskies_dic = janskies_converter().m_to_janskies(magnitudes,errors,band)
        my_dic["janskies"] = janskies_dic["janskies"]
        my_dic["j_err"] = janskies_dic["errors"]
        return my_dic
    
        
class use_pickle(observatory_source_interface):
    """ This class stores the lomb scargle model in a pickle file to speed up simulation of the same source multiple times """
    def get_out_dict(self, available, m, m_err, xml_file):
        if '/' in xml_file:
            sourcename = xml_file[xml_file.rfind('/')+1:xml_file.rfind('.')]
        else:
            sourcename = xml_file.split('.')[0]
            sourcename = sourcename.split('/')[1]
        band = sys.argv[2]
        pklfile = 'pickled_models/' + sourcename + "_" + band + '.pkl'
        try:
            outdict_file = open(pklfile, 'r')
            out_dict = pickle.load(outdict_file)
            return out_dict
        except IOError:
            out_dict = super(use_pickle, self).get_out_dict(available, m, m_err, xml_file)
            outdict_file = open(pklfile, 'w')
            pickle.dump(out_dict, outdict_file)
            return out_dict

def main():

    def request_noisified():
        my_obs = observatory_PTF.PTF
        # make up an object:
        vega = my_obs.create_target(ephem.hours('18:36:56.20'), ephem.degrees('38:46:59.0'), "cepheid") # coordinates of vega
        for i in range(10):
            mindiff_multiplier = i - 5
            if mindiff_multiplier < 1: 
                mindiff_multiplier = 1
            t = generic_observatory.time_series_generator()
            time_series = t.generate_time_series(vega, my_obs)
            print("mindiff_multiplier should be: ", mindiff_multiplier)
            try:
                output = my_obs.observe(target=vega, times = time_series, band = "V")
            except AssertionError as description:
                print("Failed %s times so far, because of %s" % ((i+1), description))
            else:
                return output
    return request_noisified()

if __name__ == '__main__':
    output = main()
