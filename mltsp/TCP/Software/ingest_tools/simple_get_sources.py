#!/usr/bin/env python
""" Script which retrieves SDSS-II DR5+DR6 survey sources and prints out
source attributes for parsing by other scripts.

NOTE: There may be occasional PAIRITEL data which is also included with sources.
    - PAIRITEL data is in j,h,k filters so easily distinguished from SDSS data.

NOTE: 'Query box size' shouldn't be larger than 5 arc minutes (0.08333 degrees)

QUERY TIMES:
 - repeated queries of a position and box-range should be < 10 seconds
 - new positions may take a couple minutes for data to be retrieved, reduced.
 - NOTE: When the SDSS object database is re-populated, queries take < 10s


HOW TO CALL:
./simple_get_sources.py <ra_in_degrees> <dec_in_degrees> <box_size_in_arcmins>

./simple_get_sources.py 49.599497 -1.0050998 0.0166666


OUTPUT FORMAT:
  Source1 Block
    Filter1 Block
      time1 mag1 mag_err1
      time2 mag2 mag_err2
      ...
    Filter2 Block
      time1 mag1 mag_err1
      time2 mag2 mag_err2
      ...
    ...
  Source2 Block
    ...
"""
import os, sys
import xmlrpclib
import random

import MySQLdb
class Mysql_Server_Query:
    def __init__(self, ra, dec, box_size):
        self.db = MySQLdb.connect(host="192.168.1.25", user="pteluser", db="object_test_db")
        self.cursor = self.db.cursor()

    def main(self):
        select_str = """SELECT src_id, 
       object_test_db.sdss_events_a.obj_id,
       object_test_db.sdss_events_a.filt,
       object_test_db.sdss_events_a.t,
       object_test_db.sdss_events_a.jsb_mag,
       object_test_db.sdss_events_a.jsb_mag_err,
       object_test_db.sdss_events_a.ra,
       object_test_db.sdss_events_a.decl,
       object_test_db.sdss_events_a.ra_rms,
       object_test_db.sdss_events_a.dec_rms
  FROM source_test_db.srcid_lookup_htm 
  JOIN object_test_db.obj_srcid_lookup USING (src_id) 
  JOIN object_test_db.sdss_events_a USING (obj_id) 
  WHERE DIF_HTMCircle(%lf,%lf,%lf)
  ORDER BY src_id,filt,t;
        """ % (ra, dec, box_size)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for result in results:
            for elem in result:
                print elem,
            print



    def main_random_srcid(self):
        select_str = "SELECT COUNT(*) FROM source_test_db.srcid_lookup"
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        n_sources = results[0][0]
        random_row = int(n_sources * random.random())

        select_str = "SELECT src_id FROM source_test_db.srcid_lookup limit %d,1" % \
                             (random_row)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        random_srcid = results[0][0]

        select_str = """SELECT src_id, 
       object_test_db.sdss_events_a.obj_id,
       object_test_db.sdss_events_a.filt,
       object_test_db.sdss_events_a.t,
       object_test_db.sdss_events_a.jsb_mag,
       object_test_db.sdss_events_a.jsb_mag_err,
       object_test_db.sdss_events_a.ra,
       object_test_db.sdss_events_a.decl,
       object_test_db.sdss_events_a.ra_rms,
       object_test_db.sdss_events_a.dec_rms
  FROM source_test_db.srcid_lookup
  JOIN object_test_db.obj_srcid_lookup USING (src_id) 
  JOIN object_test_db.sdss_events_a USING (obj_id) 
  WHERE src_id=%d
  ORDER BY src_id,filt,t;
        """ % (random_srcid)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        for result in results:
            for elem in result:
                print elem,
            print




out_filepath = "/tmp/simple_get_sources.outfile"
xmlrpc_server_url = "http://192.168.1.25:8000"
#xmlrpc_server_url = "http://127.0.0.1:8000"
ra = 49.599497
dec = -1.0050998
box_size = 0.0166666 # 1 arcmin

if len(sys.argv) == 4:
    ra = float(sys.argv[1])
    dec = float(sys.argv[2])
    box_size = float(sys.argv[3])
    print "#INPUT: ra=%lf dec=%lf box_size=%lf\n" % (ra, dec, box_size)

if ((ra < 0) or
    (ra > 360) or
    (dec < -90) or
    (dec > 90) or
    (box_size < 0.008888) or
    (box_size > 30.0)):
    print "Input values out of range!"
    sys.exit()


##########
### Do the MySQL database query instead. (does not populate database for unpopulated ra,dec).
#      NOTE: data format columns are:
# | src_id | obj_id | t | filt | jsb_mag | jsb_mag_err | ra | decl | ra_rms  | dec_rms  |
# # # msq = Mysql_Server_Query(ra, dec, box_size)
### (not sure what this was used for) :
#       msq.main_random_srcid()
# # # msq.main()
# # # sys.exit() # Exit!
##########

server = xmlrpclib.ServerProxy(xmlrpc_server_url, allow_none=True)

src_list = server.get_sources_for_radec(ra, dec, box_size, '')

os.system("rm " + out_filepath)

fp = open(out_filepath, 'w')
for s_i in xrange(len(src_list)):
    for filter_name in src_list[s_i].keys():
        print "\n##### source_id=%d filter=%s" % (\
                              src_list[s_i][filter_name]['src_id'], filter_name)
        print "# ra=%lf ra_rms=%lf" % (src_list[s_i][filter_name]['ra'],\
                                       src_list[s_i][filter_name]['ra_rms'])
        print "# dec=%lf dec_rms=%lf"%(src_list[s_i][filter_name]['dec'],\
                                       src_list[s_i][filter_name]['dec_rms'])
        for epoch_i in xrange(len(src_list[s_i][filter_name]['t'])):
            print "%lf %lf %lf" % (src_list[s_i][filter_name]['t'][epoch_i],\
                                   src_list[s_i][filter_name]['m'][epoch_i],\
                                   src_list[s_i][filter_name]['m_err'][epoch_i])
            fp.write(\
                  "%lf %lf %lf\n" % (src_list[s_i][filter_name]['t'][epoch_i],\
                                   src_list[s_i][filter_name]['m'][epoch_i],\
                                  src_list[s_i][filter_name]['m_err'][epoch_i]))
fp.close()
