#!/usr/bin/env python
""" data_cleaning.py

Tools which are used to clean timeseris data.

Initially intended to be applied to gen.generate()'s gen.sig.x_sdict object.

For Example:

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))

from data_cleaning import sigmaclip_sdict_ts

gen.generate(xml_handle="../../Data/vosource_9026.xml")
sigmaclip_sdict_ts(gen.sig.x_sdict['ts'], sigma_low=4., sigma_high=4.)


This is used in:
    arff_generation_master.py

"""
import os, sys
from numpy import array

def sigmaclip_sdict_ts(sdict_ts={}, sigma_low=4., sigma_high=4.): 
    """Iterative sigma-clipping of array elements. 
 
    Parameters:

    sdict_ts # A dictionary such as:
               gen.sig.x_sdict['ts']
       	       When previously called:
               gen.generate(xml_handle="../../Data/vosource_9026.xml")

    low : lower bound of sigma clipping 
    high : upper bound of sigma clipping 
 
    NOTE: sdict_ts is mpodified to use the new sigma-clipped timeseries data

    Example:

    gen.generate(xml_handle="../../Data/vosource_9026.xml")
    sigmaclip(gen.sig.x_sdict['ts'], low=4., high=4.)

    
    Note: satisfy the conditions:
           c > mean(c)-std(c)*low and c < mean(c) + std(c)*high 

    """ 
    for band_name, band_dict in sdict_ts.iteritems():

        if ":NOMAD" in band_name:
            continue  # skip from sigmaclipping the 1 pseudo epoch NOMAD epoch
        elif "extinct" in band_name:
            continue  # skip from sigmaclipping the 1 pseudo epoch NOMAD epoch

	m = array(band_dict['m'])

        m_std = m.std() 
        m_mean = m.mean() 
        keep_inds = ((m > m_mean - (m_std * sigma_low )) &
		     (m < m_mean + (m_std * sigma_high)))

	### This limit-mag section is not applicable since limiting mags can
	###    potentially have different time sampling/array:
	#if ((len(band_dict.get('limitmags', {}).get('lmt_mg',[])) > 0) and
	#    (len(band_dict.get('limitmags', {}).get('lmt_mg',[])) ==  len(m))):
	#    lmt_mg = array(band_dict['limitmags']['lmt_mg'])
	#    band_dict['limitmags']['lmt_mg'] = list(lmt_mg[keep_inds])
	#    
	#    lmt_t = array(band_dict['limitmags']['t'])
	#    band_dict['limitmags']['t'] = list(lmt_t[keep_inds])

	band_dict['m'] = list(m[keep_inds])

        t = array(band_dict['t'])
	band_dict['t'] = list(t[keep_inds])

	m_err = array(band_dict['m_err'])
	band_dict['m_err'] = list(m_err[keep_inds])

