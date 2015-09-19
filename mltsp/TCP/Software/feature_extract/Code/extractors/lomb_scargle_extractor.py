"""This module is a low-tech implementation of lomb_scargle_extractor using
regular expressions
"""
from __future__ import print_function
from __future__ import absolute_import

from ..FeatureExtractor import FeatureExtractor
from ..FeatureExtractor import InterExtractor
from .common_functions.pre_whiten import pre_whiten

# TODO use namespace
try:
    from pylab import *
except:
    pass
from numpy import log, exp, arange, median, ceil
from .common_functions import lightcurve
import copy # 20100902 added

class lomb_scargle_extractor(InterExtractor):
    """ wrapper for common_functions lomb_scargle and pre_whiten
    """
    internal_use_only = False
    active = True
    extname = 'lomb_scargle'
    def __init__(self):
        pass

    def extract(self):
        src_dict = {}
        src_dict['t'] = copy.copy(self.time_data)  # 20100902 added the copy()
        src_dict['m'] = copy.copy(self.flux_data)  # 20100902 addde the copy()
        src_dict['m_err'] = copy.copy(self.rms_data) # 20100902 added the copy()

        if len(self.time_data) == 0:
            self.ex_error(text="self.time_data of len()==0")

        obs = lightcurve.observatory_source_interface()
        # 20110611 dstarr added just for lightcurve.py:lomb_code():<Plot the PSD(freq)> debug/allstars-plot use.
        db_dictionary, cn_output = obs.lomb_code(src_dict['m'],
                                                 src_dict['m_err'],
                                                 src_dict['t'],
                                                 srcid=self.dic['input'].get('srcid',0))# 20110611 dstarr added just for lightcurve.py:lomb_code():<Plot the PSD(freq)> debug/allstars-plot use.

        out_dict = {}
        dstr_list = ['freq1','freq2','freq3']#,'freq4']
        for dstr in dstr_list:
            lomb_dict = db_dictionary[dstr]
            if len(lomb_dict['harmonics_amplitude']) < 4:
                n_harm_iters = len(lomb_dict['harmonics_amplitude'])
            else:
                n_harm_iters = 1 + 3 # includes primary component

# TODO don't like this but is there a simpler way? where/how else could these be stored in general?
            out_dict["%s_harmonics_freq_0" % (dstr)] = lomb_dict['frequency']
            for i in range(n_harm_iters):
                out_dict["%s_harmonics_amplitude_%d" % (dstr, i)] = \
                  lomb_dict['harmonics_amplitude'][i]
                out_dict["%s_harmonics_amplitude_error_%d" % (dstr, i)] = \
                  lomb_dict['harmonics_amplitude_error'][i]
                out_dict["%s_harmonics_rel_phase_%d" % (dstr, i)] = \
                  lomb_dict['harmonics_rel_phase'][i]
                out_dict["%s_harmonics_rel_phase_error_%d" % (dstr, i)] = \
                  lomb_dict['harmonics_rel_phase_error'][i]
        out_dict['freq_harmonics_offset'] = db_dictionary['freq1']['harmonics_time_offset']
        out_dict['freq_nharm'] = db_dictionary['freq1']['harmonics_nharm']
        out_dict['freq_signif'] = db_dictionary['freq1']['signif']
        out_dict['freq_y_offset'] = db_dictionary['freq1']['harmonics_y_offset']

        out_dict['lambda'] = db_dictionary['lambda']
        out_dict['trend'] = db_dictionary['trend']
        out_dict['varrat'] = db_dictionary['varrat']
        out_dict['n_alias'] = db_dictionary['n_alias']
        out_dict['model_phi1_phi2'] = db_dictionary['model_phi1_phi2']
        out_dict['model_min_delta_mags'] = db_dictionary['model_min_delta_mags']
        out_dict['model_max_delta_mags'] = db_dictionary['model_max_delta_mags']

        out_dict['freq1_psd'] = db_dictionary['freq1']["psd"]
        out_dict['freq1_f0'] = db_dictionary['freq1']["f0"]
        out_dict['freq1_df'] = db_dictionary['freq1']["df"]
        out_dict['freq1_numf'] = db_dictionary['freq1']["numf"]
        out_dict['freq1_model'] = db_dictionary['freq1_model']

        # 20100916 dstarr adds a couple more features:
        try:
            out_dict['freq_signif_ratio_21'] = db_dictionary['freq2']['signif'] / db_dictionary['freq1']['signif']
        except:
            out_dict['freq_signif_ratio_21'] = 0.0

        try:
            out_dict['freq_signif_ratio_31'] = db_dictionary['freq3']['signif'] / db_dictionary['freq1']['signif']
        except:
            out_dict['freq_signif_ratio_31'] = 0.0

        try:
            out_dict['freq_frequency_ratio_21'] = db_dictionary['freq2']['frequency'] / db_dictionary['freq1']['frequency']
        except:
            out_dict['freq_frequency_ratio_21'] = 0.0

        try:
            out_dict['freq_frequency_ratio_31'] = db_dictionary['freq3']['frequency'] / db_dictionary['freq1']['frequency']
        except:
            out_dict['freq_frequency_ratio_31'] = 0.0


        try:
            out_dict['freq_amplitude_ratio_21'] = db_dictionary['freq2']['harmonics_amplitude'][0] / db_dictionary['freq1']['harmonics_amplitude'][0]
        except:
            out_dict['freq_amplitude_ratio_21'] = 0.0

        try:
            out_dict['freq_amplitude_ratio_31'] = db_dictionary['freq3']['harmonics_amplitude'][0] / db_dictionary['freq1']['harmonics_amplitude'][0]
        except:
            out_dict['freq_amplitude_ratio_31'] = 0.0

        try:
            out_dict['mad_of_model_residuals'] = db_dictionary['mad_of_model_residuals']
        except:
            out_dict['mad_of_model_residuals'] = 0.0


        try:
            out_dict['p2p_scatter_2praw'] = db_dictionary['p2p_scatter_2praw']
        except:
            out_dict['p2p_scatter_2praw'] = 0.0

        try:
            out_dict['p2p_scatter_over_mad'] = db_dictionary['p2p_scatter_over_mad']
        except:
            out_dict['p2p_scatter_over_mad'] = 0.0

        try:
            out_dict['p2p_scatter_pfold_over_mad'] = db_dictionary['p2p_scatter_pfold_over_mad']
        except:
            out_dict['p2p_scatter_pfold_over_mad'] = 0.0

        try:
            out_dict['medperc90_2p_p'] = db_dictionary['medperc90_2p_p']
        except:
            out_dict['medperc90_2p_p'] = 0.0



        try:
            out_dict['p2p_ssqr_diff_over_var'] = db_dictionary['p2p_ssqr_diff_over_var']
        except:
            out_dict['p2p_ssqr_diff_over_var'] = 0.0

        try:
            out_dict['fold2P_slope_10percentile'] = db_dictionary['fold2P_slope_10percentile']
        except:
            out_dict['fold2P_slope_10percentile'] = 0.0

        try:
            out_dict['fold2P_slope_90percentile'] = db_dictionary['fold2P_slope_90percentile']
        except:
            out_dict['fold2P_slope_90percentile'] = 0.0

        return out_dict


        
class lomb_generic(FeatureExtractor):
    """ Generic lomb extractor grabs value from dictionary  """
    internal_use_only = False
    active = True
    extname = 'to_be_overloaded' # identifier used in final extracted value dict.
    lomb_key = 'to_be_overloaded'
    def extract(self):
        lomb_dict = self.fetch_extr('lomb_scargle') # fetches the dictionary from lomb_scargle_extractor with the useful lomb scargle results in it
        # If lomb_dict is partially filled, most likely lomb couldn't compute completely due to FALSE condition: (dof>0 and harm_dict['nharm']>0 and harm_dict['signif']>0)
        if self.lomb_key in lomb_dict:
            return lomb_dict[self.lomb_key] # finds the correct keyword that this class is assigned to, this could be replaced by self.extname if it wasn't for the _alt
        else:
            self.ex_error('Lomb Scargle Dictionary does not have key %s' % (self.lomb_key))
        
#[!'freq_searched_min',
# !'freq1_harmonics_rel_phase_error_1',
# !'freq1_harmonics_peak2peak_flux',
# !'freq1_harmonics_rel_phase_error_3',
# !'freq1_harmonics_rel_phase_error_2',
# !'freq1_harmonics_rel_phase_0',
# !'freq1_harmonics_rel_phase_1',
# !'freq1_harmonics_rel_phase_2',
# !'freq1_harmonics_rel_phase_3',
# !'freq1_harmonics_amplitude_2',
# !'freq1_harmonics_amplitude_3',
# !'freq1_harmonics_amplitude_0',
# !'freq1_harmonics_amplitude_1',
# !'freq2_signif',
# !'freq1_harmonics_peak2peak_flux_error',
# !'freq1_harmonics_signif',
# !'freq3',
# !'freq2',
# !'freq1',
# !'freq1_harmonics_rel_phase_error_0',
# !'freq1_harmonics_freq_0',
# !'freq1_harmonics_freq_1',
# !'freq1_harmonics_freq_2',
# !'freq1_harmonics_freq_3',
# !'freq3_signif',
# !'freq1_harmonics_nharm',
# !'freq1_harmonics_moments_err_0',
# !'freq1_harmonics_moments_err_1',
# !'freq1_harmonics_moments_err_2',
# !'freq1_harmonics_moments_err_3',
# !'freq1_signif',
# !'freq1_harmonics_moments_0',
# !'freq1_harmonics_moments_1',
# !'freq1_harmonics_moments_2',
# !'freq1_harmonics_moments_3',
# !'freq1_harmonics_amplitude_error_3',
# !'freq1_harmonics_amplitude_error_2',
# !'freq1_harmonics_amplitude_error_1',
# !'freq1_harmonics_amplitude_error_0',
# !'freq_searched_max']

# regex from !'(\S+)',\n to 
#   class $1_extractor(lomb_generic):
#       """ $1 """
#       extname = "$1"
#       lomb_key = "$1"
#       
# (need a newline at the end)



#class freq1_extractor(lomb_generic):
#   """ freq1 """
#   extname = "freq1"
#   lomb_key = "freq1"

class freq1_harmonics_amplitude_0_extractor(lomb_generic):
    """ freq1_harmonics_amplitude_0 """
    extname = "freq1_harmonics_amplitude_0"
    lomb_key = "freq1_harmonics_amplitude_0"

class freq1_harmonics_amplitude_1_extractor(lomb_generic):
    """ freq1_harmonics_amplitude_1 """
    extname = "freq1_harmonics_amplitude_1"
    lomb_key = "freq1_harmonics_amplitude_1"

class freq1_harmonics_amplitude_2_extractor(lomb_generic):
    """ freq1_harmonics_amplitude_2 """
    extname = "freq1_harmonics_amplitude_2"
    lomb_key = "freq1_harmonics_amplitude_2"

class freq1_harmonics_amplitude_3_extractor(lomb_generic):
    """ freq1_harmonics_amplitude_3 """
    extname = "freq1_harmonics_amplitude_3"
    lomb_key = "freq1_harmonics_amplitude_3"

class freq1_harmonics_amplitude_error_0_extractor(lomb_generic):
    """ freq1_harmonics_amplitude_error_0 """
    extname = "freq1_harmonics_amplitude_error_0"
    lomb_key = "freq1_harmonics_amplitude_error_0"

#class freq1_harmonics_amplitude_error_1_extractor(lomb_generic):
#   """ freq1_harmonics_amplitude_error_1 """
#   extname = "freq1_harmonics_amplitude_error_1"
#   lomb_key = "freq1_harmonics_amplitude_error_1"
#
#class freq1_harmonics_amplitude_error_2_extractor(lomb_generic):
#   """ freq1_harmonics_amplitude_error_2 """
#   extname = "freq1_harmonics_amplitude_error_2"
#   lomb_key = "freq1_harmonics_amplitude_error_2"
#
#class freq1_harmonics_amplitude_error_3_extractor(lomb_generic):
#   """ freq1_harmonics_amplitude_error_3 """
#   extname = "freq1_harmonics_amplitude_error_3"
#   lomb_key = "freq1_harmonics_amplitude_error_3"

class freq1_harmonics_freq_0_extractor(lomb_generic):
    """ freq1_harmonics_freq_0 """
    extname = "freq1_harmonics_freq_0"
    lomb_key = "freq1_harmonics_freq_0"

#class freq1_harmonics_freq_1_extractor(lomb_generic):
#   """ freq1_harmonics_freq_1 """
#   extname = "freq1_harmonics_freq_1"
#   lomb_key = "freq1_harmonics_freq_1"
#
#class freq1_harmonics_freq_2_extractor(lomb_generic):
#   """ freq1_harmonics_freq_2 """
#   extname = "freq1_harmonics_freq_2"
#   lomb_key = "freq1_harmonics_freq_2"
#
#class freq1_harmonics_freq_3_extractor(lomb_generic):
#   """ freq1_harmonics_freq_3 """
#   extname = "freq1_harmonics_freq_3"
#   lomb_key = "freq1_harmonics_freq_3"

class freq1_harmonics_moments_0_extractor(lomb_generic):
    """ freq1_harmonics_moments_0 """
    extname = "freq1_harmonics_moments_0"
    lomb_key = "freq1_harmonics_moments_0"

class freq1_harmonics_moments_1_extractor(lomb_generic):
    """ freq1_harmonics_moments_1 """
    extname = "freq1_harmonics_moments_1"
    lomb_key = "freq1_harmonics_moments_1"

class freq1_harmonics_moments_2_extractor(lomb_generic):
    """ freq1_harmonics_moments_2 """
    extname = "freq1_harmonics_moments_2"
    lomb_key = "freq1_harmonics_moments_2"

class freq1_harmonics_moments_3_extractor(lomb_generic):
    """ freq1_harmonics_moments_3 """
    extname = "freq1_harmonics_moments_3"
    lomb_key = "freq1_harmonics_moments_3"

class freq1_harmonics_moments_err_0_extractor(lomb_generic):
    """ freq1_harmonics_moments_err_0 """
    extname = "freq1_harmonics_moments_err_0"
    lomb_key = "freq1_harmonics_moments_err_0"

#class freq1_harmonics_moments_err_1_extractor(lomb_generic):
#   """ freq1_harmonics_moments_err_1 """
#   extname = "freq1_harmonics_moments_err_1"
#   lomb_key = "freq1_harmonics_moments_err_1"
#
#class freq1_harmonics_moments_err_2_extractor(lomb_generic):
#   """ freq1_harmonics_moments_err_2 """
#   extname = "freq1_harmonics_moments_err_2"
#   lomb_key = "freq1_harmonics_moments_err_2"
#
#class freq1_harmonics_moments_err_3_extractor(lomb_generic):
#   """ freq1_harmonics_moments_err_3 """
#   extname = "freq1_harmonics_moments_err_3"
#   lomb_key = "freq1_harmonics_moments_err_3"

## class freq1_harmonics_nharm_extractor(lomb_generic):
##  """ freq1_harmonics_nharm """
##  extname = "freq1_harmonics_nharm"
##  lomb_key = "freq1_harmonics_nharm"

class freq1_harmonics_peak2peak_flux_extractor(lomb_generic):
    """ freq1_harmonics_peak2peak_flux """
    extname = "freq1_harmonics_peak2peak_flux"
    lomb_key = "freq1_harmonics_peak2peak_flux"

class freq1_harmonics_peak2peak_flux_error_extractor(lomb_generic):
    """ freq1_harmonics_peak2peak_flux_error """
    extname = "freq1_harmonics_peak2peak_flux_error"
    lomb_key = "freq1_harmonics_peak2peak_flux_error"

class freq1_harmonics_rel_phase_0_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_0 """
    extname = "freq1_harmonics_rel_phase_0"
    lomb_key = "freq1_harmonics_rel_phase_0"

class freq1_harmonics_rel_phase_1_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_1 """
    extname = "freq1_harmonics_rel_phase_1"
    lomb_key = "freq1_harmonics_rel_phase_1"

class freq1_harmonics_rel_phase_2_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_2 """
    extname = "freq1_harmonics_rel_phase_2"
    lomb_key = "freq1_harmonics_rel_phase_2"

class freq1_harmonics_rel_phase_3_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_3 """
    extname = "freq1_harmonics_rel_phase_3"
    lomb_key = "freq1_harmonics_rel_phase_3"

class freq1_harmonics_rel_phase_error_0_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_error_0 """
    extname = "freq1_harmonics_rel_phase_error_0"
    lomb_key = "freq1_harmonics_rel_phase_error_0"

class freq1_harmonics_rel_phase_error_0_extractor(lomb_generic):
    """ freq1_harmonics_rel_phase_error_0 """
    extname = "freq1_harmonics_rel_phase_error_0"
    lomb_key = "freq1_harmonics_rel_phase_error_0"

class freq1_lambda_extractor(lomb_generic):
    """ freq1_lambda """
    extname = "freq1_lambda"
    lomb_key = "lambda"



#class freq1_harmonics_rel_phase_error_1_extractor(lomb_generic):
#   """ freq1_harmonics_rel_phase_error_1 """
#   extname = "freq1_harmonics_rel_phase_error_1"
#   lomb_key = "freq1_harmonics_rel_phase_error_1"
#
#class freq1_harmonics_rel_phase_error_2_extractor(lomb_generic):
#   """ freq1_harmonics_rel_phase_error_2 """
#   extname = "freq1_harmonics_rel_phase_error_2"
#   lomb_key = "freq1_harmonics_rel_phase_error_2"
#
#class freq1_harmonics_rel_phase_error_3_extractor(lomb_generic):
#   """ freq1_harmonics_rel_phase_error_3 """
#   extname = "freq1_harmonics_rel_phase_error_3"
#   lomb_key = "freq1_harmonics_rel_phase_error_3"

## class freq1_harmonics_signif_extractor(lomb_generic):
##  """ freq1_harmonics_signif """
##  extname = "freq1_harmonics_signif"
##  lomb_key = "freq1_harmonics_signif"

## class freq1_signif_extractor(lomb_generic):
##  """ freq1_signif """
##  extname = "freq1_signif"
##  lomb_key = "freq1_signif"

## class freq2_extractor(lomb_generic):
##  """ freq2 """
##  extname = "freq2"
##  lomb_key = "freq2"

class freq2_harmonics_amplitude_0_extractor(lomb_generic):
    """ freq2_harmonics_amplitude_0 """
    extname = "freq2_harmonics_amplitude_0"
    lomb_key = "freq2_harmonics_amplitude_0"

class freq2_harmonics_amplitude_1_extractor(lomb_generic):
    """ freq2_harmonics_amplitude_1 """
    extname = "freq2_harmonics_amplitude_1"
    lomb_key = "freq2_harmonics_amplitude_1"

class freq2_harmonics_amplitude_2_extractor(lomb_generic):
    """ freq2_harmonics_amplitude_2 """
    extname = "freq2_harmonics_amplitude_2"
    lomb_key = "freq2_harmonics_amplitude_2"

class freq2_harmonics_amplitude_3_extractor(lomb_generic):
    """ freq2_harmonics_amplitude_3 """
    extname = "freq2_harmonics_amplitude_3"
    lomb_key = "freq2_harmonics_amplitude_3"

class freq2_harmonics_amplitude_error_0_extractor(lomb_generic):
    """ freq2_harmonics_amplitude_error_0 """
    extname = "freq2_harmonics_amplitude_error_0"
    lomb_key = "freq2_harmonics_amplitude_error_0"

#class freq2_harmonics_amplitude_error_1_extractor(lomb_generic):
#   """ freq2_harmonics_amplitude_error_1 """
#   extname = "freq2_harmonics_amplitude_error_1"
#   lomb_key = "freq2_harmonics_amplitude_error_1"
#
#class freq2_harmonics_amplitude_error_2_extractor(lomb_generic):
#   """ freq2_harmonics_amplitude_error_2 """
#   extname = "freq2_harmonics_amplitude_error_2"
#   lomb_key = "freq2_harmonics_amplitude_error_2"
#
#class freq2_harmonics_amplitude_error_3_extractor(lomb_generic):
#   """ freq2_harmonics_amplitude_error_3 """
#   extname = "freq2_harmonics_amplitude_error_3"
#   lomb_key = "freq2_harmonics_amplitude_error_3"

class freq2_harmonics_freq_0_extractor(lomb_generic):
    """ freq2_harmonics_freq_0 """
    extname = "freq2_harmonics_freq_0"
    lomb_key = "freq2_harmonics_freq_0"

#class freq2_harmonics_freq_1_extractor(lomb_generic):
#   """ freq2_harmonics_freq_1 """
#   extname = "freq2_harmonics_freq_1"
#   lomb_key = "freq2_harmonics_freq_1"
#
#class freq2_harmonics_freq_2_extractor(lomb_generic):
#   """ freq2_harmonics_freq_2 """
#   extname = "freq2_harmonics_freq_2"
#   lomb_key = "freq2_harmonics_freq_2"
#
#class freq2_harmonics_freq_3_extractor(lomb_generic):
#   """ freq2_harmonics_freq_3 """
#   extname = "freq2_harmonics_freq_3"
#   lomb_key = "freq2_harmonics_freq_3"

class freq2_harmonics_moments_0_extractor(lomb_generic):
    """ freq2_harmonics_moments_0 """
    extname = "freq2_harmonics_moments_0"
    lomb_key = "freq2_harmonics_moments_0"

class freq2_harmonics_moments_1_extractor(lomb_generic):
    """ freq2_harmonics_moments_1 """
    extname = "freq2_harmonics_moments_1"
    lomb_key = "freq2_harmonics_moments_1"

class freq2_harmonics_moments_2_extractor(lomb_generic):
    """ freq2_harmonics_moments_2 """
    extname = "freq2_harmonics_moments_2"
    lomb_key = "freq2_harmonics_moments_2"

class freq2_harmonics_moments_3_extractor(lomb_generic):
    """ freq2_harmonics_moments_3 """
    extname = "freq2_harmonics_moments_3"
    lomb_key = "freq2_harmonics_moments_3"

class freq2_harmonics_moments_err_0_extractor(lomb_generic):
    """ freq2_harmonics_moments_err_0 """
    extname = "freq2_harmonics_moments_err_0"
    lomb_key = "freq2_harmonics_moments_err_0"

#class freq2_harmonics_moments_err_1_extractor(lomb_generic):
#   """ freq2_harmonics_moments_err_1 """
#   extname = "freq2_harmonics_moments_err_1"
#   lomb_key = "freq2_harmonics_moments_err_1"
#
#class freq2_harmonics_moments_err_2_extractor(lomb_generic):
#   """ freq2_harmonics_moments_err_2 """
#   extname = "freq2_harmonics_moments_err_2"
#   lomb_key = "freq2_harmonics_moments_err_2"
#
#class freq2_harmonics_moments_err_3_extractor(lomb_generic):
#   """ freq2_harmonics_moments_err_3 """
#   extname = "freq2_harmonics_moments_err_3"
#   lomb_key = "freq2_harmonics_moments_err_3"

## class freq2_harmonics_nharm_extractor(lomb_generic):
##  """ freq2_harmonics_nharm """
##  extname = "freq2_harmonics_nharm"
##  lomb_key = "freq2_harmonics_nharm"

## class freq2_harmonics_peak2peak_flux_extractor(lomb_generic):
##  """ freq2_harmonics_peak2peak_flux """
##  extname = "freq2_harmonics_peak2peak_flux"
##  lomb_key = "freq2_harmonics_peak2peak_flux"

## class freq2_harmonics_peak2peak_flux_error_extractor(lomb_generic):
##  """ freq2_harmonics_peak2peak_flux_error """
##  extname = "freq2_harmonics_peak2peak_flux_error"
##  lomb_key = "freq2_harmonics_peak2peak_flux_error"

class freq2_harmonics_rel_phase_0_extractor(lomb_generic):
    """ freq2_harmonics_rel_phase_0 """
    extname = "freq2_harmonics_rel_phase_0"
    lomb_key = "freq2_harmonics_rel_phase_0"

class freq2_harmonics_rel_phase_1_extractor(lomb_generic):
    """ freq2_harmonics_rel_phase_1 """
    extname = "freq2_harmonics_rel_phase_1"
    lomb_key = "freq2_harmonics_rel_phase_1"

class freq2_harmonics_rel_phase_2_extractor(lomb_generic):
    """ freq2_harmonics_rel_phase_2 """
    extname = "freq2_harmonics_rel_phase_2"
    lomb_key = "freq2_harmonics_rel_phase_2"

class freq2_harmonics_rel_phase_3_extractor(lomb_generic):
    """ freq2_harmonics_rel_phase_3 """
    extname = "freq2_harmonics_rel_phase_3"
    lomb_key = "freq2_harmonics_rel_phase_3"

class freq2_harmonics_rel_phase_error_0_extractor(lomb_generic):
    """ freq2_harmonics_rel_phase_error_0 """
    extname = "freq2_harmonics_rel_phase_error_0"
    lomb_key = "freq2_harmonics_rel_phase_error_0"

#class freq2_harmonics_rel_phase_error_1_extractor(lomb_generic):
#   """ freq2_harmonics_rel_phase_error_1 """
#   extname = "freq2_harmonics_rel_phase_error_1"
#   lomb_key = "freq2_harmonics_rel_phase_error_1"
#
#class freq2_harmonics_rel_phase_error_2_extractor(lomb_generic):
#   """ freq2_harmonics_rel_phase_error_2 """
#   extname = "freq2_harmonics_rel_phase_error_2"
#   lomb_key = "freq2_harmonics_rel_phase_error_2"
#
#class freq2_harmonics_rel_phase_error_3_extractor(lomb_generic):
#   """ freq2_harmonics_rel_phase_error_3 """
#   extname = "freq2_harmonics_rel_phase_error_3"
#   lomb_key = "freq2_harmonics_rel_phase_error_3"

## class freq2_harmonics_signif_extractor(lomb_generic):
##  """ freq2_harmonics_signif """
##  extname = "freq2_harmonics_signif"
##  lomb_key = "freq2_harmonics_signif"

## class freq2_signif_extractor(lomb_generic):
##  """ freq2_signif """
##  extname = "freq2_signif"
##  lomb_key = "freq2_signif"

## class freq3_extractor(lomb_generic):
##  """ freq3 """
##  extname = "freq3"
##  lomb_key = "freq3"

class freq3_harmonics_amplitude_0_extractor(lomb_generic):
    """ freq3_harmonics_amplitude_0 """
    extname = "freq3_harmonics_amplitude_0"
    lomb_key = "freq3_harmonics_amplitude_0"

class freq3_harmonics_amplitude_1_extractor(lomb_generic):
    """ freq3_harmonics_amplitude_1 """
    extname = "freq3_harmonics_amplitude_1"
    lomb_key = "freq3_harmonics_amplitude_1"

class freq3_harmonics_amplitude_2_extractor(lomb_generic):
    """ freq3_harmonics_amplitude_2 """
    extname = "freq3_harmonics_amplitude_2"
    lomb_key = "freq3_harmonics_amplitude_2"

class freq3_harmonics_amplitude_3_extractor(lomb_generic):
    """ freq3_harmonics_amplitude_3 """
    extname = "freq3_harmonics_amplitude_3"
    lomb_key = "freq3_harmonics_amplitude_3"

class freq3_harmonics_amplitude_error_0_extractor(lomb_generic):
    """ freq3_harmonics_amplitude_error_0 """
    extname = "freq3_harmonics_amplitude_error_0"
    lomb_key = "freq3_harmonics_amplitude_error_0"

#class freq3_harmonics_amplitude_error_1_extractor(lomb_generic):
#   """ freq3_harmonics_amplitude_error_1 """
#   extname = "freq3_harmonics_amplitude_error_1"
#   lomb_key = "freq3_harmonics_amplitude_error_1"
#
#class freq3_harmonics_amplitude_error_2_extractor(lomb_generic):
#   """ freq3_harmonics_amplitude_error_2 """
#   extname = "freq3_harmonics_amplitude_error_2"
#   lomb_key = "freq3_harmonics_amplitude_error_2"
#
#class freq3_harmonics_amplitude_error_3_extractor(lomb_generic):
#   """ freq3_harmonics_amplitude_error_3 """
#   extname = "freq3_harmonics_amplitude_error_3"
#   lomb_key = "freq3_harmonics_amplitude_error_3"

class freq3_harmonics_freq_0_extractor(lomb_generic):
    """ freq3_harmonics_freq_0 """
    extname = "freq3_harmonics_freq_0"
    lomb_key = "freq3_harmonics_freq_0"

#class freq3_harmonics_freq_1_extractor(lomb_generic):
#   """ freq3_harmonics_freq_1 """
#   extname = "freq3_harmonics_freq_1"
#   lomb_key = "freq3_harmonics_freq_1"
#
#class freq3_harmonics_freq_2_extractor(lomb_generic):
#   """ freq3_harmonics_freq_2 """
#   extname = "freq3_harmonics_freq_2"
#   lomb_key = "freq3_harmonics_freq_2"
#
#class freq3_harmonics_freq_3_extractor(lomb_generic):
#   """ freq3_harmonics_freq_3 """
#   extname = "freq3_harmonics_freq_3"
#   lomb_key = "freq3_harmonics_freq_3"

class freq3_harmonics_moments_0_extractor(lomb_generic):
    """ freq3_harmonics_moments_0 """
    extname = "freq3_harmonics_moments_0"
    lomb_key = "freq3_harmonics_moments_0"

class freq3_harmonics_moments_1_extractor(lomb_generic):
    """ freq3_harmonics_moments_1 """
    extname = "freq3_harmonics_moments_1"
    lomb_key = "freq3_harmonics_moments_1"

class freq3_harmonics_moments_2_extractor(lomb_generic):
    """ freq3_harmonics_moments_2 """
    extname = "freq3_harmonics_moments_2"
    lomb_key = "freq3_harmonics_moments_2"

class freq3_harmonics_moments_3_extractor(lomb_generic):
    """ freq3_harmonics_moments_3 """
    extname = "freq3_harmonics_moments_3"
    lomb_key = "freq3_harmonics_moments_3"

class freq3_harmonics_moments_err_0_extractor(lomb_generic):
    """ freq3_harmonics_moments_err_0 """
    extname = "freq3_harmonics_moments_err_0"
    lomb_key = "freq3_harmonics_moments_err_0"

#class freq3_harmonics_moments_err_1_extractor(lomb_generic):
#   """ freq3_harmonics_moments_err_1 """
#   extname = "freq3_harmonics_moments_err_1"
#   lomb_key = "freq3_harmonics_moments_err_1"
#
#class freq3_harmonics_moments_err_2_extractor(lomb_generic):
#   """ freq3_harmonics_moments_err_2 """
#   extname = "freq3_harmonics_moments_err_2"
#   lomb_key = "freq3_harmonics_moments_err_2"
#
#class freq3_harmonics_moments_err_3_extractor(lomb_generic):
#   """ freq3_harmonics_moments_err_3 """
#   extname = "freq3_harmonics_moments_err_3"
#   lomb_key = "freq3_harmonics_moments_err_3"

## class freq3_harmonics_nharm_extractor(lomb_generic):
##  """ freq3_harmonics_nharm """
##  extname = "freq3_harmonics_nharm"
##  lomb_key = "freq3_harmonics_nharm"

## class freq3_harmonics_peak2peak_flux_extractor(lomb_generic):
##  """ freq3_harmonics_peak2peak_flux """
##  extname = "freq3_harmonics_peak2peak_flux"
##  lomb_key = "freq3_harmonics_peak2peak_flux"

## class freq3_harmonics_peak2peak_flux_error_extractor(lomb_generic):
##  """ freq3_harmonics_peak2peak_flux_error """
##  extname = "freq3_harmonics_peak2peak_flux_error"
##  lomb_key = "freq3_harmonics_peak2peak_flux_error"

class freq3_harmonics_rel_phase_0_extractor(lomb_generic):
    """ freq3_harmonics_rel_phase_0 """
    extname = "freq3_harmonics_rel_phase_0"
    lomb_key = "freq3_harmonics_rel_phase_0"

class freq3_harmonics_rel_phase_1_extractor(lomb_generic):
    """ freq3_harmonics_rel_phase_1 """
    extname = "freq3_harmonics_rel_phase_1"
    lomb_key = "freq3_harmonics_rel_phase_1"

class freq3_harmonics_rel_phase_2_extractor(lomb_generic):
    """ freq3_harmonics_rel_phase_2 """
    extname = "freq3_harmonics_rel_phase_2"
    lomb_key = "freq3_harmonics_rel_phase_2"

class freq3_harmonics_rel_phase_3_extractor(lomb_generic):
    """ freq3_harmonics_rel_phase_3 """
    extname = "freq3_harmonics_rel_phase_3"
    lomb_key = "freq3_harmonics_rel_phase_3"

class freq3_harmonics_rel_phase_error_0_extractor(lomb_generic):
    """ freq3_harmonics_rel_phase_error_0 """
    extname = "freq3_harmonics_rel_phase_error_0"
    lomb_key = "freq3_harmonics_rel_phase_error_0"

#class freq3_harmonics_rel_phase_error_1_extractor(lomb_generic):
#   """ freq3_harmonics_rel_phase_error_1 """
#   extname = "freq3_harmonics_rel_phase_error_1"
#   lomb_key = "freq3_harmonics_rel_phase_error_1"
#
#class freq3_harmonics_rel_phase_error_2_extractor(lomb_generic):
#   """ freq3_harmonics_rel_phase_error_2 """
#   extname = "freq3_harmonics_rel_phase_error_2"
#   lomb_key = "freq3_harmonics_rel_phase_error_2"
#
#class freq3_harmonics_rel_phase_error_3_extractor(lomb_generic):
#   """ freq3_harmonics_rel_phase_error_3 """
#   extname = "freq3_harmonics_rel_phase_error_3"
#   lomb_key = "freq3_harmonics_rel_phase_error_3"

## class freq3_harmonics_signif_extractor(lomb_generic):
##  """ freq3_harmonics_signif """
##  extname = "freq3_harmonics_signif"
##  lomb_key = "freq3_harmonics_signif"

## class freq3_signif_extractor(lomb_generic):
##  """ freq3_signif """
##  extname = "freq3_signif"
##  lomb_key = "freq3_signif"

## class freq_searched_max_extractor(lomb_generic):
##  """ freq_searched_max """
##  extname = "freq_searched_max"
##  lomb_key = "freq_searched_max"

## class freq_searched_min_extractor(lomb_generic):
##  """ freq_searched_min """
##  extname = "freq_searched_min"
##  lomb_key = "freq_searched_min"

######
    
class freq_harmonics_offset_extractor(lomb_generic):
    """ freq_harmonics_offset """
    extname = "freq_harmonics_offset"
    lomb_key = "freq_harmonics_offset"
    
class freq_y_offset_extractor(lomb_generic):
    """ freq_y_offset """
    extname = "freq_y_offset"
    lomb_key = "freq_y_offset"

class freq_signif_extractor(lomb_generic):
    """ freq_signif """
    extname = "freq_signif"
    lomb_key = "freq_signif"

class freq_nharm_extractor(lomb_generic):
    """ freq_nharm """
    extname = "freq_nharm"
    lomb_key = "freq_nharm"

class linear_trend_extractor(lomb_generic):
    """ slope (b)  of linear trend fitted to unfolded data using linfit.py: m = a+b*x; minimize chi^2 = Sum (y-m)^2/dy^2"""
    extname = "linear_trend"
    lomb_key = "trend"

class freq_varrat_extractor(lomb_generic):
    """ Ratio of variances: V_freq1_subtracted / V_linear_trend_subtracted """
    extname = "freq_varrat"
    lomb_key = "varrat"

########
    
class freq_signif_ratio_21_extractor(lomb_generic):
    """ freq_signif_ratio_21 """
    extname = "freq_signif_ratio_21"
    lomb_key = "freq_signif_ratio_21"

class freq_signif_ratio_31_extractor(lomb_generic):
    """ freq_signif_ratio_31 """
    extname = "freq_signif_ratio_31"
    lomb_key = "freq_signif_ratio_31"

class freq_frequency_ratio_21_extractor(lomb_generic):
    """ freq_frequency_ratio_21 """
    extname = "freq_frequency_ratio_21"
    lomb_key = "freq_frequency_ratio_21"

class freq_frequency_ratio_31_extractor(lomb_generic):
    """ freq_frequency_ratio_31 """
    extname = "freq_frequency_ratio_31"
    lomb_key = "freq_frequency_ratio_31"

class freq_amplitude_ratio_21_extractor(lomb_generic):
    """ freq_amplitude_ratio_21 """
    extname = "freq_amplitude_ratio_21"
    lomb_key = "freq_amplitude_ratio_21"

class freq_amplitude_ratio_31_extractor(lomb_generic):
    """ freq_amplitude_ratio_31 """
    extname = "freq_amplitude_ratio_31"
    lomb_key = "freq_amplitude_ratio_31"

class p2p_scatter_2praw_extractor(lomb_generic):
    """ From arXiv 1101_2406v1 Dubath 20110112  paper.
sum of the squares of the magnitude 
differences between pairs of successive data points in the light 
curve folded around twice the period divided by the same quantity
derived from the raw light curve.   """
    extname = "p2p_scatter_2praw"
    lomb_key = "p2p_scatter_2praw"

class p2p_scatter_over_mad_extractor(lomb_generic):
    """ From arXiv 1101_2406v1 Dubath 20110112  paper.
median of the absolute values of the differences 
between successive magnitudes in the raw light curve normalized
by the Median Absolute Deviation (MAD) around the median. 
"""
    extname = "p2p_scatter_over_mad"
    lomb_key = "p2p_scatter_over_mad"


class p2p_scatter_pfold_over_mad_extractor(lomb_generic):
    """ From arXiv 1101_2406v1 Dubath 20110112  paper.
median of the absolute values of the 
differences between successive magnitudes in the folded light 
curve normalized by the Median Absolute Deviation (MAD) 
around the median of the raw lightcurve. """
    extname = "p2p_scatter_pfold_over_mad"
    lomb_key = "p2p_scatter_pfold_over_mad"


class medperc90_2p_p_extractor(lomb_generic):
    """ From arXiv 1101_2406v1 Dubath 20110112  paper.
Percentile90:2P/P:
the 90-th percentile of the absolute residual values around the 2P model 
divided by the same quantity 
for the residuals around the P model. The 2P model is a model 
recomputed using twice the period value. 
"""
    extname = "medperc90_2p_p"
    lomb_key = "medperc90_2p_p"


class p2p_ssqr_diff_over_var_extractor(lomb_generic):
    """ eta feature from arXiv 1101.3316 Kim QSO paper.
    if there exists positive serial correlation, the eta is small, negative serial correlation then eta is large.  Note that the linear trend is not use in the model"""
    extname = "p2p_ssqr_diff_over_var"
    lomb_key = "p2p_ssqr_diff_over_var"


class fold2P_slope_10percentile_extractor(lomb_generic):
    """ Using point-to-point slopes calculated from LS freq1 model and 2 Period folded data, this is 10 percentile median of the slopes.  Note that the linear trend is not use in the model"""
    extname = "fold2P_slope_10percentile"
    lomb_key = "fold2P_slope_10percentile"


class fold2P_slope_90percentile_extractor(lomb_generic):
    """ Using point-to-point slopes calculated from LS freq1 model and 2 Period folded data, this is 90 percentile median of the slopes.  Note that the linear trend is not use in the model"""
    extname = "fold2P_slope_90percentile"
    lomb_key = "fold2P_slope_90percentile"

class freq_n_alias_extractor(lomb_generic):
    """ freq_n_alias """
    extname = "freq_n_alias"
    lomb_key = "n_alias"

class freq_model_phi1_phi2_extractor(lomb_generic):
    """ freq_model_phi1_phi2 : ratio of model phase between max1 and min2 over phase between min2 to max3 """
    extname = "freq_model_phi1_phi2"
    lomb_key = "model_phi1_phi2"


class freq_model_min_delta_mags_extractor(lomb_generic):
    """ freq_model_min_delta_mags : ratio of model phase between max1 and min2 over phase between min2 to max3 """
    extname = "freq_model_min_delta_mags"
    lomb_key = "model_min_delta_mags"

class freq_model_max_delta_mags_extractor(lomb_generic):
    """ freq_model_max_delta_mags : ratio of model phase between max1 and min2 over phase between min2 to max3 """
    extname = "freq_model_max_delta_mags"
    lomb_key = "model_max_delta_mags"

