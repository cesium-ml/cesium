#!/usr/bin/env python
"""

Simple sanity check test

Find the sources in 50k ASAS dataset which have duplicate ra,dec

"""
import sys, os
import time


class Database_Utils:
    """ Establish database connections, contains methods related to database tables.
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def connect_to_db(self):
        import MySQLdb
        self.tcp_db = MySQLdb.connect(host=pars['tcp_hostname'], \
                                  user=pars['tcp_username'], \
                                  db=pars['tcp_database'],\
                                  port=pars['tcp_port'])
        self.tcp_cursor = self.tcp_db.cursor()

        self.tutor_db = MySQLdb.connect(host=pars['tutor_hostname'], \
                                  user=pars['tutor_username'], \
                                  db=pars['tutor_database'], \
                                  passwd=pars['tutor_password'], \
                                  port=pars['tutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()



class Test_Asas(Database_Utils):
    """

    Retrieve colors from simbad and possiby ASAS GCVS dataset


    """

    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()



    def main(self):
        """
        """


        select_str = "select source_id, source_ra, source_dec from sources where project_id=126"
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        for (src_id, ra, dec) in results:
            select_str = "select source_id, source_ra, source_dec from sources where project_id=126 and source_ra >= %lf and source_ra <= %lf and source_dec >= %lf and source_dec <= %lf and source_id != %d" % ( \
                float(ra) - 0.000555555555556,
                float(ra) + 0.000555555555556,
                float(dec) - 0.000555555555556,
                float(dec) + 0.000555555555556,
                int(src_id))
            self.tutor_cursor.execute(select_str)
            sub_results = self.tutor_cursor.fetchall()
            if len(sub_results) > 0:
                print (src_id, ra, dec)
                print sub_results
                print '--------------------------'
            
        import pdb; pdb.set_trace()
        print



if __name__ == '__main__':

    pars = { \
    'tutor_hostname':'192.168.1.103', #'lyra.berkeley.edu',
    'tutor_username':'dstarr', #'tutor', # guest
    'tutor_password':'ilove2mass', #'iamaguest',
    'tutor_database':'tutor',
    'tutor_port':3306,
    'tcp_hostname':'192.168.1.25',
    'tcp_username':'pteluser',
    'tcp_port':     3306, 
    'tcp_database':'source_test_db',
    }

    TestAsas = Test_Asas(pars=pars)
    TestAsas.main()
