#!/usr/bin/env python
""" 20110116: Looking at alsit of Joey debosscher source ids,
I determine the dotastro.org source ids.
"""
import os, sys
import MySQLdb
sys.path.append(os.path.abspath(os.path.expandvars('$TCP_DIR/' + 
                                'Algorithms')))
import simbad_id_lookup


class Find_DotAstro_Deboss_Sources():
    def __init__(self, pars={}):
        self.pars = pars
        self.db = MySQLdb.connect(host=self.pars['tcptutor_hostname'],
                                  user=self.pars['tcptutor_username'],
                                  db=self.pars['tcptutor_database'],
                                  port=self.pars['tcptutor_port'],
                                  passwd=self.pars['tcptutor_password'])
        self.cursor = self.db.cursor()




    def main(self):
        """
        """
        list_fpath = os.path.abspath(os.path.expandvars('$TCP_DIR/' + 
                                                        'Data/tutor_new_deboss.list'))
        #list_fpath = os.path.expandvars('$HOME/scratch/tutor_new_deboss.list')

        lines = open(list_fpath).readlines()
        joey_id_list = []
        class_name_list = []
        joey_source_name_list = []
        tutor_source_id_list = []
        for line in lines:
            tups = line.split()
            (joey_id, class_name, source_name) = tups

            joey_id_list.append(joey_id)
            class_name_list.append(class_name)
            joey_source_name_list.append(source_name)
            


            
            #select_str = 'SELECT source_id, source_name FROM sources WHERE project_id=123 and source_name like "%' + source_name + '%"'
            select_str = 'SELECT source_id, source_name FROM sources WHERE project_id=123 and source_name = "' + source_name + '"'
            
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            tutor_source_id = results[0][0]
            if len(results) == 0:
                print "NO MATCH: ", joey_id, class_name, source_name
            elif len(results) > 1:
                print "TOO MANY: ", joey_id, class_name, source_name
                print results
            else:
                pass #print joey_id, tutor_source_id, results[0][1]

            if tutor_source_id in tutor_source_id_list:
                print "ALREADY matched this tutor source_id: %d(%s) joey_id=%d class_name=%s joey_source_name=%s" % (tutor_source_id, results[0][1], joey_id, class_name, source_name)
            else:
                tutor_source_id_list.append(tutor_source_id)

        # TODO: now query tutor rdb for all sources and match with the tutor_source_id to see what extra srcids


        select_str = 'SELECT source_id, source_name FROM sources WHERE project_id=123'
            
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()

        for row in results:
            if row[0] not in tutor_source_id_list:
                print "In TUTOR, but not in Joey 1542 list: source_id=%d source_name=%s" % (row[0], row[1])

        import pdb; pdb.set_trace()
        print


if __name__ == '__main__':

    pars = { \
        'user_id':3, # 3 = dstarr in tutor.users
        'tcptutor_hostname':'192.168.1.103',
        'tcptutor_username':'dstarr', # guest
        'tcptutor_password':'ilove2mass', #'iamaguest',
        'tcptutor_database':'tutor',
        'tcptutor_port':3306,
        }


    FindDotAstroDebossSources = Find_DotAstro_Deboss_Sources(pars=pars)
    FindDotAstroDebossSources.main()
