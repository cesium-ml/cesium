#!/usr/bin/env python
"""
populate_feat_db_using_TCPTUTOR_sources.py

   v0.1 Initial version just queries all VOSource-available XML TCPTutor
        sources and adds to RDB using:
          ingest_tools...get_sources_using_xml_file_with_feature_extraction()

### PDB Command:
/usr/lib/python2.5/pdb.py populate_feat_db_using_TCPTUTOR_sources.py


### NOTE: Table defs in testsuite.par.py:
CREATE TABLE classid_lookup (schema_id SMALLINT UNSIGNED, 
                             class_id SMALLINT UNSIGNED, 
                             class_short_name VARCHAR(12) DEFAULT '', 
                             class_name VARCHAR(100) DEFAULT '', 
                             schema_n_feats SMALLINT UNSIGNED DEFAULT 0, 
                             schema_n_classes SMALLINT UNSIGNED DEFAULT 0, 
                             schema_comment VARCHAR(160) DEFAULT '', 
                             schema_dtime DATETIME,
                             PRIMARY KEY(schema_id, class_id));

CREATE TABLE src_class_probs (schema_id SMALLINT UNSIGNED,
			      class_id SMALLINT UNSIGNED, 
			      prob FLOAT,
		              src_id INT UNSIGNED,
			      is_primary_class BOOLEAN,
			      gen_dtime DATETIME,
			      PRIMARY KEY(schema_id, class_id, prob),
			      INDEX(schema_id, src_id));

"""
import sys, os
import MySQLdb
import threading
import time
import glob

#        'tcptutor_hostname':'lyra.berkeley.edu',
#        'tcptutor_username':'pteluser',
#        'tcptutor_password':'Edwin_Hubble71',
#        'tcptutor_port':     3306, 
#        'tcptutor_database':'tutor',
#        'classdb_hostname':'127.0.0.1',
#        'classdb_username':'dstarr', #'pteluser',
#        'classdb_port':     3306, 
#        'classdb_database':'source_test_db', #'sourcet_db',
 
local_pars = {'t_sleep':0.2,
        'number_threads':10, # on transx : 10
        'tcp_tutor_srcid_offset':100000000,
        'exclude_existing_xml_sources':False, # 20100527 dstarr changes from True to False
        }

import ingest_tools # This is done to get tcptutor and classdb server configs
pars = ingest_tools.pars
pars.update(local_pars)

class Populate_Feat_DB_Using_Tcptutor_sources:
    def __init__(self, pars):
        self.pars = pars
        self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \
                                  user=self.pars['tcptutor_username'], \
                                  passwd=self.pars['tcptutor_password'],\
                                  db=self.pars['tcptutor_database'],\
                                  port=self.pars['tcptutor_port'])
        self.tutor_cursor = self.tutor_db.cursor()

 
        self.classdb_db = MySQLdb.connect(host=self.pars['classdb_hostname'], \
                                  user=self.pars['classdb_username'],\
                                  db=self.pars['classdb_database'],\
                                  port=self.pars['classdb_port'])
        self.classdb_cursor = self.classdb_db.cursor()



    def get_srcid_list(self, project_id=123,
                       exclude_existing_xml_sources=False):
        ### This gets everything:
        #select_str = "SELECT DISTINCT sources.source_id FROM    sources WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID)"
        ### 20100714 This gets (new) Debosscher dataset
        #pre20110106#select_str = "SELECT DISTINCT sources.source_id FROM    sources WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND project_id=123"
        #pre20110123#select_str ='SELECT DISTINCT sources.source_id, classes.class_short_name FROM    sources JOIN classes USING (class_id) WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND project_id=123 AND class_short_name != "xrbin" AND class_short_name != "sx" AND sources.source_id!=163477 AND sources.source_id!=163974 AND sources.source_id!=164010 AND sources.source_id!=163338 '
        ####### pre 20120222
        #if project_id == 123:
        #    select_str ='''SELECT DISTINCT sources.source_id, classes.class_short_name FROM    sources JOIN classes USING (class_id) WHERE
        #    EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND
        #    project_id=123 AND
        #    sources.source_id!=163849 AND
        #    sources.source_id!=163974 AND
        #    sources.source_id!=164010 AND
        #    sources.source_id!=163477 AND
        #    sources.source_id!=163853 AND
        #    sources.source_id!=163614 AND
        #    sources.source_id!=163765 AND
        #    sources.source_id!=164203 AND
        #    sources.source_id!=163534 AND
        #    sources.source_id!=163500 AND
        #    sources.source_id!=163338 AND
        #    sources.source_id!=163354 AND
        #    sources.source_id!=164149 AND
        #    sources.source_id!=163559 AND
        #    sources.source_id!=163948 AND
        #    sources.source_id!=164146 AND
        #    sources.source_id!=163495
        #    '''
        if project_id == 123:
            select_str ='''SELECT DISTINCT sources.source_id, classes.class_short_name FROM    sources JOIN classes USING (class_id) WHERE
            EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND
            project_id=123 AND
            sources.source_id!=163849 AND
            sources.source_id!=163853 AND
            sources.source_id!=163534 AND
            sources.source_id!=163500 AND
            sources.source_id!=163559 AND
            sources.source_id!=163948 AND
            sources.source_id!=164146
            '''
        else:
            #select_str ='SELECT DISTINCT sources.source_id, classes.class_short_name FROM    sources JOIN classes USING (class_id) WHERE   EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND project_id=%d' % (project_id)
            select_str ='SELECT DISTINCT sources.source_id FROM sources WHERE EXISTS(SELECT Observations.Observation_ID FROM Observations WHERE Observations.Source_ID = sources.Source_ID) AND project_id=%d' % (project_id)
            
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        srcid_list = []
        if (self.pars.get('exclude_existing_xml_sources',False) or
            exclude_existing_xml_sources):
            glob_str = "%s/1*xml" % (self.pars['local_vosource_xml_write_dir'])
            existing_dirs = glob.glob(glob_str)
            existing_srcid_lists = []
            for dirpath in existing_dirs:
                exisiting_srcid = int(dirpath[dirpath.rfind('/')+2:dirpath.rfind('.')])
                existing_srcid_lists.append(exisiting_srcid)
            for result in results:
                if int(result[0]) in existing_srcid_lists:
                        continue # skip it
                srcid_list.append(result[0])
        else:
            for result in results:
                srcid_list.append(result[0])
        return srcid_list


    def _thread_getadd_feat_class_for_tutor_source(self, command_str):
        #print command_str
        os.system(command_str)
        #time.sleep(10000000)
        #raw_input("press key")

    def threaded_get_features_populate_rdb(self, schema_id, srcid_list, xml_write_dirpath=''):
        """ Given a list of TCPTutor srcids, spawn several ingest_tools.py
        threads which will generate features for each source and insert them
        into the freature DB.
        """
        running_threads = []
        for source_id in srcid_list:
            #if source_id <= 17329:
            #    continue
            #print '@@@@@@@@@@@@', source_id
            offset_source_id = source_id + self.pars['tcp_tutor_srcid_offset']
            #source_url = "http://lyra.berkeley.edu/tutor/pub/vosource.php?Source_ID=%d" % (source_id)
            source_url = "http://192.168.1.103/tutor/pub/vosource.php?Source_ID=%d" % (source_id)

            if len(xml_write_dirpath) == 0:
                xml_write_dirpath = self.pars['local_vosource_xml_write_dir']

            # For dstarr@wintermute tests:
            #exec_str = "/home/dstarr/src/TCP/Software/ingest_tools/ingest_tools.py do_get_sources_using_xml_file_with_feature_extraction=1 vosource_srcid=%d vosource_url=%s xmlrpc_server_name=127.0.0.1 xmlrpc_server_port=8000 rdb_name_2=object_test_db rdb_name_3=object_test_db rdb_user_4=dstarr rdb_name_4=source_test_db rdb_features_host_ip=127.0.0.1 rdb_features_user=dstarr rdb_features_db_name=source_test_db source_region_lock_host_ip=127.0.0.1 source_region_lock_user=dstarr source_region_lock_dbname=source_test_db footprint_host_ip=127.0.0.1 footprint_user=dstarr footprint_dbname=object_test_db sdss_astrom_repo_host_ip=192.168.1.55 sdss_astrom_repo_dirpath=/media/disk-4/sdss_astrom_repository rdb_host_ip_2=127.0.0.1 rdb_user=dstarr rdb_host_ip_3=127.0.0.1 rdb_host_ip_4=127.0.0.1 sci_class_schema_id=%d" % (offset_source_id, source_url, schema_id)
            # For transx Testing-DB run:
            exec_str = "/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py do_get_sources_using_xml_file_with_feature_extraction=1 vosource_srcid=%d vosource_url=%s xmlrpc_server_name=192.168.1.25 xmlrpc_server_port=8000 rdb_name_2=object_test_db rdb_name_3=object_test_db rdb_user_4=pteluser rdb_name_4=source_test_db rdb_features_host_ip=192.168.1.25 rdb_features_user=pteluser rdb_features_db_name=source_test_db source_region_lock_host_ip=192.168.1.25 source_region_lock_user=pteluser source_region_lock_dbname=source_test_db footprint_host_ip=192.168.1.25 footprint_user=pteluser footprint_dbname=object_test_db sdss_astrom_repo_host_ip=192.168.1.55 sdss_astrom_repo_dirpath=/media/disk-4/sdss_astrom_repository rdb_host_ip_2=192.168.1.25 rdb_user=pteluser rdb_host_ip_3=192.168.1.25 rdb_host_ip_4=192.168.1.25 sci_class_schema_id=%d do_delete_existing_featvals=1 local_vosource_xml_write_dir=%s" % (offset_source_id, source_url, schema_id, xml_write_dirpath)
            print exec_str
            # For transx/192.168.1.25 production run:
            #exec_str = "/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py do_get_sources_using_xml_file_with_feature_extraction=1 vosource_srcid=%d vosource_url=%s xmlrpc_server_name=192.168.1.45 xmlrpc_server_port=8000 rdb_name_2=object_db rdb_name_3=object_db rdb_user_4=pteluser rdb_name_4=source_db rdb_features_host_ip=192.168.1.25 rdb_features_user=pteluser rdb_features_db_name=source_db source_region_lock_host_ip=192.168.1.25 source_region_lock_user=pteluser source_region_lock_dbname=source_db footprint_host_ip=192.168.1.25 footprint_user=pteluser footprint_dbname=object_db sdss_astrom_repo_host_ip=192.168.1.55 sdss_astrom_repo_dirpath=/media/disk-4/sdss_astrom_repository rdb_host_ip_2=192.168.1.25 rdb_user=pteluser rdb_host_ip_3=192.168.1.25 rdb_host_ip_4=192.168.1.25" % (offset_source_id, source_url)
            # For testing on 192.168.1.65 test database:
            #exec_str = "/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py do_get_sources_using_xml_file_with_feature_extraction=1 vosource_srcid=%d vosource_url=%s xmlrpc_server_name=192.168.1.65 xmlrpc_server_port=8000 rdb_name_2=object_test_db rdb_name_3=object_test_db rdb_user_4=pteluser rdb_name_4=source_test_db rdb_features_host_ip=192.168.1.65 rdb_features_user=pteluser rdb_features_db_name=source_test_db source_region_lock_host_ip=192.168.1.65 source_region_lock_user=pteluser source_region_lock_dbname=source_test_db footprint_host_ip=192.168.1.65 footprint_user=pteluser footprint_dbname=object_test_db sdss_astrom_repo_host_ip=192.168.1.55 sdss_astrom_repo_dirpath=/media/disk-4/sdss_astrom_repository rdb_host_ip_2=192.168.1.65 rdb_user=pteluser rdb_host_ip_3=192.168.1.65 rdb_host_ip_4=192.168.1.65 sci_class_schema_id=%d" % (offset_source_id, source_url, schema_id)

            for thr in running_threads:
                if not thr.isAlive():
                    running_threads.remove(thr)
            n_tasks_to_spawn = self.pars['number_threads'] - \
                                                       len(running_threads)
            #self._thread_getadd_feat_class_for_tutor_source(exec_str)
            while n_tasks_to_spawn < 1:
                time.sleep(self.pars['t_sleep'])
                for thr in running_threads:
                    if not thr.isAlive():
                        running_threads.remove(thr)
                n_tasks_to_spawn = self.pars['number_threads'] - \
                                                       len(running_threads)
            t = threading.Thread(target=\
                               self._thread_getadd_feat_class_for_tutor_source,\
                                 args=[exec_str])
            #os.system(exec_str)
            t.start()
            running_threads.append(t)
            #import pdb; pdb.set_trace()

        ### Now wait for all threads to complete.
        while len(running_threads) > 0:
            for thr in running_threads:
                if not thr.isAlive():
                    running_threads.remove(thr)
            time.sleep(self.pars['t_sleep'])


    def insert_classes_to_classid_lookup_table(self):
        """ Retrieve TCPTUTOR science classes from TUTOR DB, and import
        into Local RDB classid_lookup table.
        """
        #self.tutor_cursor = self.tutor_db.cursor()
        #self.tutor_db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], \

        select_str ="SELECT max(schema_id) FROM classid_lookup"
        self.classdb_cursor.execute(select_str)
        results = self.classdb_cursor.fetchall()
        if results[0][0] == None:
            i_schema = 0
        else:
            print results
            i_schema = int(results[0][0]) + 1
        
        select_str ="SELECT class_id, class_short_name, class_name FROM classes"
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()

        class_id_list = []
        for result in results:
            class_id_list.append(result[0])
        max_class_id = max(class_id_list)
            
        result_list = list(results)
        # We add extra Plugin Classifiers:
        for class_schema_name,schema_dict in self.pars['class_schema_definition_dicts'].iteritems():
            if 'weka' in class_schema_name.lower():
                continue # go to the next class_schema since WEKA is done.
            for short_class_name in schema_dict['class_list']:
                max_class_id += 1
                insert_tup = (max_class_id, short_class_name, \
                              class_schema_name + '_'+ short_class_name)
                result_list.append(insert_tup)
        n_classes = len(result_list)
        insert_list = ["INSERT INTO classid_lookup (schema_id, class_id, class_short_name, class_name, schema_n_classes, schema_dtime) VALUES "]
        for result in result_list:
            insert_list.append("(%d, %s, '%s', '%s', %d, NOW()), " % (i_schema, result[0], result[1], result[2], n_classes))
        self.classdb_cursor.execute(''.join(insert_list)[:-2])
        return i_schema


    def main(self):
        # TODO: retrieve TUTOR classes from lyra and copy locally?
        # # # # # 20100527 dstarr disables schema_id generation since we are not interested in generating classifications or even the dotastro existing classifications for dotastro sources. just interested in getting feature values into RDB.
        # # # # #schema_id = self.insert_classes_to_classid_lookup_table()
        schema_id = 10000
        srcid_list = self.get_srcid_list()
        #print len(srcid_list), srcid_list[-5:]
        self.threaded_get_features_populate_rdb(schema_id, srcid_list)


if __name__ == '__main__':

    pfduts = Populate_Feat_DB_Using_Tcptutor_sources(pars)
    pfduts.main()
