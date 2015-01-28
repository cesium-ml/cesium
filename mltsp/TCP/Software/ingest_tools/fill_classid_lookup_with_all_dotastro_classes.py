#!/usr/bin/env python

import sys, os
import MySQLdb


class Fill_Classid_Lookup_With_All_Dotastro_Classes:
    """ This selects all class_names, class_ids from Dotastro.org database and inserts into
    tranx RDB:source_test_db.classid_lookup TABLE using schema_id=10000
    """
    def __init__(self, pars):
        self.pars = pars
        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()

        self.class_db = MySQLdb.connect(host=self.pars['classdb_hostname'], \
                                  user=self.pars['classdb_username'], \
                                  db=self.pars['classdb_database'],\
                                  port=self.pars['classdb_port'])
        self.class_cursor = self.class_db.cursor()


    def main(self):
        """ main() for Fill_Classid_Lookup_With_All_Dotastro_Classes
        """

        dotastro_select_str = "SELECT DISTINCT sources.project_id, sources.class_id, sources.pclass_id, project_classes.pclass_name, project_classes.pclass_short_name FROM sources JOIN project_classes USING (pclass_id)"
        self.tutor_cursor.execute(dotastro_select_str)
        results = self.tutor_cursor.fetchall()

        delete_str = "DELETE FROM classid_lookup WHERE (schema_id=10000)"
        self.class_cursor.execute(delete_str)

        insert_list = ["INSERT INTO classid_lookup (schema_id, class_id, class_name, schema_n_feats, schema_n_classes, schema_comment, schema_dtime) VALUES "]
        for result in results:
            if len(result) == 0:
                continue
            (project_id, class_id, pclass_id, pclass_name, pclass_short_name) = result
            #print (project_id, class_id, pclass_id, pclass_name, pclass_short_name)
            insert_list.append('(10000, %d, "%s", 111, %d, "DotAstro", NOW()), ' % \
                                (pclass_id, pclass_name, len(results)))
        # now insert these into tranx rdb using schema_id=1000000

        self.class_cursor.execute(''.join(insert_list)[:-2])

        print


if __name__ == '__main__':

    pars = { \
        'tcptutor_hostname':'lyra.berkeley.edu',
        'tcptutor_username':'pteluser', # guest
        'tcptutor_password':'Edwin_Hubble71', #'iamaguest',
        'tcptutor_database':'tutor',
        'tcptutor_port':3306,
        'classdb_hostname':'192.168.1.25', # This is my LOCAL replicated DB
        'classdb_username':'pteluser', #'pteluser',
        'classdb_port':     3306, 
        'classdb_database':'source_test_db', #'source_db',
        'classid_lookup_tablename':'classid_lookup'}


    fcl = Fill_Classid_Lookup_With_All_Dotastro_Classes(pars)
    fcl.main()
