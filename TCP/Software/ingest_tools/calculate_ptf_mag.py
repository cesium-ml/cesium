#!/usr/bin/env python 
"""
Contains a function which calculates the total mag for a ptf source.

Intended to be called by ptf_master.py and maintenance_ptf_events_add_column.py

"""
import os, sys
import numpy

def calculate_total_mag(candid_dict):
    """ Assumes candid_dict contains keys like:

    {'f_aper': 411.60500000000002,
     'filter': 'R',
     'flux_aper': 219.90899999999999,
     'lmt_mg_new': 21.305,
     'mag': 20.993200000000002,
     'mag_ref': 0.0,
     'pos_sub': True,
     'sub_zp': 27.899999999999999,
     'ub1_zp_ref': 25.699999999999999,
     'ujd': 2454938.7807800001}
    """
    total_mag = 0

    if candid_dict['pos_sub']:
        #total_mag = -2.5 * numpy.log10(numpy.abs(candid_dict['f_aper'] * numpy.power(10.,(-0.4*(candid_dict['sub_zp'] - candid_dict['ub1_zp_ref']))) + candid_dict['flux_aper'] )) + candid_dict['ub1_zp_ref']
        total_mag = -2.5 * numpy.log10((candid_dict['f_aper'] * numpy.power(10.,(-0.4*(candid_dict['sub_zp'] - candid_dict['ub1_zp_ref']))) + candid_dict['flux_aper'] )) + candid_dict['ub1_zp_ref']
    else:
        ### The problem with this following case is that we are setting the total_mag to a limit, which doesn't work with the current lightcurve fitting / features code (since they do not incorporate limits in their feature calculations):
        #if candid_dict['lmt_mg_new'] <= candid_dict['mag_ref']:
        #    # limiting_mag is (not) fainter than reference_mag
        #    #     then total_mag = limit_mag = (upper limmit)
        #    total_mag = candid_dict['lmt_mg_new']
        #else:
        if True:
            # limiting_mag is fainter than reference_mag

            ### TODO: want some condition where detection in negative_sub == No and in pos_sub==No
            ###     -> this is when the reference source completely matches the mag for an epoch
            ###     -> then total_mag = ref_mag

            # Assuming detection in negative sub:
            #total_mag = -2.5 * numpy.log10(numpy.abs(-1. * candid_dict['f_aper'] * numpy.power(10.,(-0.4*(candid_dict['sub_zp'] - candid_dict['ub1_zp_ref']))) + candid_dict['flux_aper'] )) + candid_dict['ub1_zp_ref']
            total_mag = -2.5 * numpy.log10((-1. * candid_dict['f_aper'] * numpy.power(10.,(-0.4*(candid_dict['sub_zp'] - candid_dict['ub1_zp_ref']))) + candid_dict['flux_aper'] )) + candid_dict['ub1_zp_ref']

            ### TODO: Josh says that if "mag in negative sub" < limit_mag - ref_mag  is NOT True:
            ###      -> then total_mag - limit_mag,
            ###    - but to me this seems like a non-detecion, were we just revert to only using
            ###          knowledge of the upper limits.
    return total_mag
