#!/usr/bin/env python 
""" This code mirror's the LBL PTF proc_image footprint table
which has time, limitng magnitude for candidate images.

The purpose of this is to have this information accessible to all
TCP task cleints, without needing seperate RDB connections with
the LBL PGSQL gootprint server.

This code is intended to be ruin continously on tranx, under a seperate "screen".

"""
import sys, os
import ingest_tools
import MySQLdb
import psycopg2
import time
import datetime

class Poll_LBL_PTF_Footprint_Server:
    """ Main singleton which does the polling

    NOTE: local mysql footprint table of form (in object_test_db database):

          CREATE TABLE ptf_candidate_footprint (id INT UNSIGNED NOT NULL, ujd DOUBLE, lmt_mg FLOAT, filter VARCHAR(1), radec_region GEOMETRY NOT NULL, PRIMARY KEY (id), SPATIAL INDEX(radec_region));

    """

    def __init__(self, pars):
        self.pars = pars

        self.mysql_db = MySQLdb.connect(host=self.pars['rdb_host_ip_2'], 
                                  user=self.pars['rdb_user'],
                                  db=self.pars['rdb_name_2'],
                                  port=self.pars['rdb_port_2'])
        self.mysql_cursor = self.mysql_db.cursor()

        self.pg_conn = psycopg2.connect(\
             "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                            (self.pars['ptf_postgre_dbname'],\
                             self.pars['ptf_postgre_user'],\
                             self.pars['ptf_postgre_host'],\
                             self.pars['ptf_postgre_password'],\
                             self.pars['ptf_postgre_port']))
        self.pg_conn.set_isolation_level(2)
        #self.pg_cursor = self.pg_conn.cursor()

        # get the max() ingested LBL/PTF footprint id from local mysql table:

        select_str = "SELECT max(id) FROM ptf_candidate_footprint"

        self.mysql_cursor.execute(select_str)
        results = self.mysql_cursor.fetchall()

        self.max_id_ingested = 0
        if len(results) > 0:
            if results[0][0] != None:
                self.max_id_ingested = results[0][0]



    def query_add_new_footprint_row(self):
        """ Attempt to retrieve a new footprint row from the LBL PTF
        table/server.  Add to local footprint table.
        """
        id_increment = 1000

        ### we do this loop until we dont select any new rows:
        while True:
            try:
                select_str = "SELECT id, ujd, lmt_mg, filter, ra_ul, ra_ur, ra_lr, ra_ll, dec_ul, dec_ur, dec_lr, dec_ll FROM proc_image WHERE id > %d AND id <= %d" % ( \
                                self.max_id_ingested,
                                self.max_id_ingested + id_increment)
                self.pg_cursor = self.pg_conn.cursor()
                self.pg_cursor.execute(select_str)
                rdb_rows = self.pg_cursor.fetchall()
                self.pg_cursor.close()
                self.pg_conn.rollback()
            except:
                return

            insert_list = ["INSERT INTO ptf_candidate_footprint (id, ujd, lmt_mg, filter, radec_region) VALUES "]

            current_max_id = self.max_id_ingested
            for row in rdb_rows:
                (cand_id, ujd, lmt_mg, cand_filter, \
                 ra_ul,  ra_ur,  ra_lr,  ra_ll, \
                 dec_ul, dec_ur, dec_lr, dec_ll) = tuple(row)
                # KLUDGE: not efficient:
                if cand_id > current_max_id:
                    current_max_id = cand_id
                insert_list.append("(%d, %lf, %lf, '%s', GeomFromText('POLYGON((%lf %lf, %lf %lf, %lf %lf, %lf %lf, %lf %lf))')), " % (cand_id, ujd, lmt_mg, cand_filter, ra_ul, dec_ul, ra_ur, dec_ur, ra_lr, dec_lr, ra_ll, dec_ll, ra_ul, dec_ul))

            if len(insert_list) == 1:
                return # we get out of here... sleep a bit in the higher loop
            else:
                self.max_id_ingested = current_max_id
                insert_str = ''.join(insert_list)[:-2] + ' ON DUPLICATE KEY UPDATE ujd=VALUES(ujd), lmt_mg=VALUES(lmt_mg)'
                self.mysql_cursor.execute(insert_str)
                print "self.max_id_ingested:", self.max_id_ingested


    def main(self):
        """ Main continous polling loop
        """
        while True:
            self.query_add_new_footprint_row()
            print datetime.datetime.utcnow(), "sleep(60)..."
            time.sleep(60) # give LBL PTF server a break

if __name__ == '__main__':


    PollLblPtfFootprintServer = Poll_LBL_PTF_Footprint_Server(ingest_tools.pars)
    PollLblPtfFootprintServer.main()
