#!/usr/bin/env python 
"""
   v0.1 An example / demo file on how to connect to TCP MySQL server
"""
from __future__ import print_function


import sys, os
import MySQLdb

if __name__ == '__main__':

    pars = { \
    'mysql_user':"pteluser",
    'mysql_hostname':"192.168.1.25",
    'mysql_database':'source_test_db',
    'mysql_port':3306,
        }

    db = MySQLdb.connect(host=pars['mysql_hostname'],
                         user=pars['mysql_user'],
                         db=pars['mysql_database'],
                         port=pars['mysql_port'])
    cursor = db.cursor()

    # NOTE: The table existing in the tranx MySQLdb contains columns:
    #      ptf_candidate_footprint (id, ujd, lmt_mg, filter, radec_region)
    # It is populated with data taken from LBL's sgn02 database:
    #     SELECT id, ujd, lmt_mg, filter, ra_ul, ra_ur, ra_lr, ra_ll, dec_ul, dec_ur, dec_lr, dec_ll FROM proc_image WHERE id > %d AND id <= %d"
    # NOTE: this table was filled using the TCP/Software/ingest_tools/sync_with_lbl_footprint_table.py script.

    #(ra, dec)  = (336.00127488, 36.490527063)
    (ra, dec)  = (320.87275, -0.84803)
    ##### This gets the PTF limiting magnitude for an (ra,dec):
    #select_str = "SELECT filter, ujd, lmt_mg from object_test_db.ptf_candidate_footprint WHERE (MBRContains(radec_region, GeomFromText('POINT(%lf %lf)'))) ORDER BY filter, ujd" % (ra, dec)
    select_str = """
SELECT source_test_db.srcid_lookup_htm.src_id, 
       object_test_db.sdss_events_a.t,
       object_test_db.sdss_events_a.jsb_mag,
       object_test_db.sdss_events_a.jsb_mag_err,
       object_test_db.sdss_events_a.filt,
       object_test_db.sdss_events_a.ra,
       object_test_db.sdss_events_a.decl
FROM source_test_db.srcid_lookup_htm
JOIN object_test_db.obj_srcid_lookup USING (src_id)
JOIN object_test_db.sdss_events_a USING (obj_id)
WHERE (DIF_HTMCircle(%lf, %lf, 0.01))
ORDER BY src_id, t
    """ % (ra, dec)
    print("SDSS filter numbers translate using {0:'u',1:'g',2:'r',3:'i',4:'z'}")
    cursor.execute(select_str)
    results = cursor.fetchall()
    for row in results:
        print(row)
