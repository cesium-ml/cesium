#!/usr/bin/env python
""" retrieve xmls for a particular tutor/dotastro class_id
"""
from __future__ import print_function
import os, sys
import pprint
import MySQLdb
import datetime

class tutor_db:
    """
    """
    def __init__(self):
        self.pars ={'tcptutor_hostname':'192.168.1.103',
                    'tcptutor_username':'tutor', # guest
                    'tcptutor_password':'ilove2mass', #'iamaguest',
                    'tcptutor_database':'tutor',
                    'tcptutor_port':3306}


        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()



class Retrieve_XMLs:
    """
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.db = tutor_db()

    def retrieve_xmls_for_proj_list(self, base_dirpath="", proj_id_list=[]):
        """ Given a list of proj_id, retrieve xmls from TUTOR.
        """

        for proj_id in proj_id_list:

            select_str = "SELECT source_id FROM sources WHERE project_id=%d" % (proj_id)
            self.db.tutor_cursor.execute(select_str)
            results = self.db.tutor_cursor.fetchall()

            if len(results)== 0:
                print(datetime.datetime.now(), "No sources for project_id=%d" % (proj_id))
            else:
                print(datetime.datetime.now(), "Project_id=", proj_id, "N sources=", len(results))

            srcid_list = []
            for row in results:
                srcid_list.append(row[0])

            retrieve_dirpath = "%s/tutor_%d" % (base_dirpath, proj_id)
            if not os.path.exists(retrieve_dirpath):
                os.system("mkdir -p %s" % (retrieve_dirpath))

                for src_id in srcid_list:
                    #get_str = "wget -O %s/%d.xml http://dotastro.org/lightcurves/vosource.php?Source_ID=%d" % (pars['retrieve_dirpath'], src_id, src_id)
                    get_str = "curl --compressed -o %s/%d.xml http://dotastro.org/lightcurves/vosource.php?Source_ID=%d" % (retrieve_dirpath, src_id, src_id)
                    #os.system(get_str)
                    #print get_str
                    (a,b,c) = os.popen3(get_str)
                    a.close()
                    c.close()
                    lines = b.read()
                    b.close()

                    #print "  Retrieved: %d" % (src_id)
    


if __name__ == '__main__':

    pars = { \
        }
    #    'project_id':121, # 120 : ASAS    (122 : debosscher)
    #    'retrieve_dirpath':'/media/raid_0/tutor_121_xmls', #'/tmp/tutor_120_xmls',
    #RetrieveXMLs.retrieve_xmls_for_proj_list(base_dirpath="/media/raid_0/all_tutor_xmls",
    #                                         proj_id_list=[16, 55])

    RetrieveXMLs = Retrieve_XMLs(pars=pars)

    proj_id_list = range(1,126 + 1) # 126 is currently the largest tutor project_id

    skip_projids = [121, 123, 126,
                    120, 122] # already done, obsolete/old

    for projid in skip_projids:
        proj_id_list.remove(projid)

    print()
    RetrieveXMLs.retrieve_xmls_for_proj_list(base_dirpath="/media/raid_0/all_tutor_xmls",
                                             proj_id_list=proj_id_list)


