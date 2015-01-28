#!/usr/bin/env python
# utils.py
#   v0.1 : initial version
#
# Various utilities for Python.
#

import os, sys
import datetime


def calc_last_day_of_month(year, month):
    """ Given numerical year & month, figure out the last day of the month
    """
    lday = 0
    if (month == 1):
        lday = 31
    elif (month == 3):
        lday = 31
    elif (month == 4):
        lday = 30
    elif (month == 5):
        lday = 31
    elif (month == 6):
        lday = 30
    elif (month == 7):
        lday = 31
    elif (month == 8):
        lday = 31
    elif (month == 9):
        lday = 30
    elif (month == 10):
        lday = 31
    elif (month == 11):
        lday = 30
    elif (month == 12):
        lday = 31
    elif (month == 2):
        if (year == 2000):
            lday = 29
        elif (year == 2004):
            lday = 29
        elif (year == 2008):
            lday = 29
        elif (year == 2012):
            lday = 29
        elif (year == 2016):
            lday = 29
        elif (year == 2020):
            lday = 29
        elif (year == 1996):
            lday = 29
        else:
            lday = 28
    return lday


#   '2006-07-09 05:39:35.498801'
# datetime(year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
# 
def convert_str_to_datetime(raw_str_date):
    """ converts a string datetime into a datetime
    """
    str_date = raw_str_date.strip()
    year = int(str_date[0:4])
    month = int(str_date[5:7])
    day = int(str_date[8:10])
    hour = int(str_date[11:13])
    minute = int(str_date[14:16])
    sec = int(str_date[17:19])
    usec = int(str_date[20:])
    
    return datetime.datetime(year,month,day,hour,minute,sec,usec)


def nmon_to_smon(nmon):
    """ Converts numerical month to string month xxx
    PAIRITEL-centric, in that the first letter is capitalized.
    """
    if (nmon == 1):
        smon = 'Jan'
    elif (nmon == 2):
        smon = 'Feb'
    elif (nmon == 3):
        smon = 'Mar'
    elif (nmon == 4):
        smon = 'Apr'
    elif (nmon == 5):
        smon = 'May'
    elif (nmon == 6):
        smon = 'Jun'
    elif (nmon == 7):
        smon = 'Jul'
    elif (nmon == 8):
        smon = 'Aug'
    elif (nmon == 9):
        smon = 'Sep'
    elif (nmon == 10):
        smon = 'Oct'
    elif (nmon == 11):
        smon = 'Nov'
    elif (nmon == 12):
        smon = 'Dec'
    return smon


def smon_to_nmon(s_mon):
    """ Converts string month xxx to numerical month
    PAIRITEL-centric, in that the first letter is capitalized.
    """
    if (s_mon == 'Jan'):
        nmon = 1
    elif (s_mon == 'Feb'):
        nmon = 2
    elif (s_mon == 'Mar'):
        nmon = 3
    elif (s_mon == 'Apr'):
        nmon = 4
    elif (s_mon == 'May'):
        nmon = 5
    elif (s_mon == 'Jun'):
        nmon = 6
    elif (s_mon == 'Jul'):
        nmon = 7
    elif (s_mon == 'Aug'):
        nmon = 8
    elif (s_mon == 'Sep'):
        nmon = 9
    elif (s_mon == 'Oct'):
        nmon = 10
    elif (s_mon == 'Nov'):
        nmon = 11
    elif (s_mon == 'Dec'):
        nmon = 12
    return nmon



def convert_ptel_fitspath_to_datetime(fits_path):
    """ Given a fitsfile path eg: krr2006-Jul-09-09h57m03s-CALIB.85.4-p0-0.fits
    parses and returns a datetime.
    """
    if '/' in fits_path:
        filename = fits_path[fits_path.rfind('/')+1:]
        date_str = filename[filename.find('-')-4:24]
    else:
        date_str = fits_path[fits_path.find('-')-4:24]
    return datetime.datetime(int(date_str[:4]),
                             smon_to_nmon(date_str[5:8]),
                             int(date_str[9:11]),
                             int(date_str[12:14]),
                             int(date_str[15:17]),
                             int(date_str[18:20]))


def convert_datetime_to_float(dtime):
    """ Convert datetime to float-date, similar to matplotlib.dates.date2num()
    """
    cur_year = dtime.year
    month = dtime.month
    day = dtime.day
    hour = dtime.hour
    minute = dtime.minute
    second = dtime.second + (dtime.microsecond * 0.000001)

    days_upto_2003 = 731216.0 # float days for 20030101

    total_days = days_upto_2003

    # iterate over all year past 2003
    year_list = range(2003,cur_year+1)
    for i_year in year_list:
        if not i_year == cur_year:
            last_mon = 12
        else:
            last_mon = month - 1 # don't include the current month
        for i_mon in range(1,last_mon+1):
            month_days = calc_last_day_of_month(i_year,i_mon)
            total_days += month_days

    total_days += day -1 # Don't add the extra day which hasn't been completed
    total_days += ((second/60.0 + minute)/60.0 + hour)/24.0

    return total_days


def get_cvs_entries_dict_from_fpath(cvs_entries_fpath):
    """ return a summarizing dictionary of the CVS Entries file.
    """
    entries_dict = {}
    try:
        lines = open(cvs_entries_fpath).readlines()
    except:
        lines = []
    for line in lines:
        split_list = line.split('/')
        if len(split_list) >= 4:
            entries_dict.update({split_list[1]:{'ver':split_list[2], \
                                                'date':split_list[3]}})
    return entries_dict


def form_version_tuple_from_version_string(cvs_ver_str):
    """ Form and return a float tuple of the CVS versions, found in FITS header
    """
    if 'megar' in cvs_ver_str:
        end_str = ',megar'
    else:
        end_str = ',night_mos'
    end_ind = cvs_ver_str.find(end_str)

    changelog_ver = float(cvs_ver_str[cvs_ver_str.find('ChLg')+4:cvs_ver_str.find(',sk_cl')])
    skark_client_ver = float(cvs_ver_str[cvs_ver_str.find(',sk_cl')+6:end_ind])
    night_mos_ver = float(cvs_ver_str[end_ind+len(end_str):])
    return (changelog_ver, skark_client_ver, night_mos_ver)


def form_version_id_from_cvs_entries(redux_entries_fpath='', task_type='', \
                                    pipe2_entries_fpath='', return_tuple='no'):
    """ This forms a string which represents current CVS versions of critical
    software and the ChangeLog.  This string is later intended to written
    into reduced/mosaic FITS headers.
    """
    cvs_string = ''
    cvs_tuple = ()
    redux_entries_dict = get_cvs_entries_dict_from_fpath(redux_entries_fpath)
    pipe2_entries_dict = get_cvs_entries_dict_from_fpath(pipe2_entries_fpath)

    if task_type == 'mosaic':
        cvs_string = "ChLg%s,sk_cl%s,night_mos%s" % (\
            pipe2_entries_dict.get('ChangeLog',{}).get('ver',0),
            pipe2_entries_dict.get('skark_client.py',{}).get('ver',0),
            redux_entries_dict.get('night_mos.py',{}).get('ver',0))
        cvs_tuple=(float(pipe2_entries_dict.get('ChangeLog',{}).get('ver',0)),
            float(pipe2_entries_dict.get('skark_client.py',{}).get('ver',0)),
            float(redux_entries_dict.get('night_mos.py',{}).get('ver',0)))
    elif task_type == 'megar':
        cvs_string = "ChLg%s,sk_cl%s,megar%s" % (\
            pipe2_entries_dict.get('ChangeLog',{}).get('ver',0),
            pipe2_entries_dict.get('skark_client.py',{}).get('ver',0),
            redux_entries_dict.get('megar.py',{}).get('ver',0))
        cvs_tuple=(float(pipe2_entries_dict.get('ChangeLog',{}).get('ver',0)),
            float(pipe2_entries_dict.get('skark_client.py',{}).get('ver',0)),
            float(redux_entries_dict.get('megar.py',{}).get('ver',0)))
    elif task_type == 'reduction':
        cvs_string = "ChLg%s,sk_cl%s,sk_compute%s" % (\
            pipe2_entries_dict.get('ChangeLog',{}).get('ver',0),
            pipe2_entries_dict.get('skark_client.py',{}).get('ver',0),
            pipe2_entries_dict.get('skark_compute.py',{}).get('ver',0))
        cvs_tuple=(float(pipe2_entries_dict.get('ChangeLog',{}).get('ver',0)),
            float(pipe2_entries_dict.get('skark_client.py',{}).get('ver',0)),
            float(pipe2_entries_dict.get('skark_compute.py',{}).get('ver',0)))
    if return_tuple == 'yes':
        return cvs_tuple
    else:
        return cvs_string
