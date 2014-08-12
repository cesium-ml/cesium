#!/usr/bin/env python
""" Summarizes certain science class sources found in AL*.dat files

"""

import sys, os
import MySQLdb
import glob
from numpy import loadtxt

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/ingest_tools'))
import activelearn_utils

if __name__ == '__main__':

    pars = {'tutor_hostname':'192.168.1.103',
        'tutor_username':'dstarr', #'tutor', # guest
        'tutor_password':'ilove2mass', #'iamaguest',
        'tutor_database':'tutor',
        'tutor_port':3306, #33306,
        'tcp_hostname':'192.168.1.25',
        'tcp_username':'pteluser',
        'tcp_port':     3306, #23306, 
        'tcp_database':'source_test_db',
        'al_dirpath':'/home/pteluser/src/TCP/Data/allstars',
        'al_glob_str':'AL_*_*.dat',
        'classids_of_interest':[202, # wtts
                                201, # ctts
                                200, # tt (obsolete)
                                267, # Herbig AE
                                197], # Herbig AE/BE],
        }


    DatabaseUtils = activelearn_utils.Database_Utils(pars=pars)
    rclass_tutorid_lookup = DatabaseUtils.retrieve_tutor_class_ids()
    class_id_name = dict([[v,k] for k,v in rclass_tutorid_lookup.items()])

    fpaths = glob.glob("%s/%s" % (pars['al_dirpath'], pars['al_glob_str']))

    print """<html><body><table>
    """
    for fpath in fpaths:
        tup_list = loadtxt(fpath,
                           dtype={'names': ('src_id', 'class_id'),
                                  'formats': ('i4', 'i4')},
                           usecols=(0,1),
                           unpack=False)
        srcid_list = tup_list['src_id']
        classid_list = tup_list['class_id']
        for i, classid in enumerate(classid_list):
            if classid in pars['classids_of_interest']:
                print '<tr><td>%d (%s) %s     <A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td></tr>' % (srcid_list[i], fpath[fpath.rfind('/')+1:], class_id_name[classid].replace(' ','_'), srcid_list[i], srcid_list[i])

    select_str = "select source_id, class_id from sources where project_id = 123"
    DatabaseUtils.tutor_cursor.execute(select_str)
    results = DatabaseUtils.tutor_cursor.fetchall()
    if len(results) == 0:
        raise "Error"
    for row in results:
        (source_id, classid) = row
        if classid in pars['classids_of_interest']:
            print '<tr><td>%d (%s) %s     <A href="http://lyra.berkeley.edu/allstars/?mode=inspect&srcid=%d">%d</A></td></tr>' % (source_id, "Debosscher", class_id_name[classid].replace(' ','_'), source_id, source_id)

    print """</table></body></html>
    """
    import pdb; pdb.set_trace()
    print
    
