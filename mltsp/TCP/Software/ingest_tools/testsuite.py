#!/usr/bin/env python 
""" testsuite.py

   v0.3 Implemented SDSS-II object, source, features tests.
   v0.2 Tests implemented: object, source, feature generation for Pairitel data
   v0.1 Initial version: (20080215 dstarr)
         - Test suite for important ingest_tools.py tasks.
         - Generates all MySQL TABLEs, DATABASEs, custom index servers, etc.
         - Tests based upon SVN commited Pairitel mos*.fits files.

SEE WIKI: http://lyra.berkeley.edu/dokuwiki/doku.php?id=tcp:test_suite

REQUIREMENTS:
   - User MUST create TestSuite workpath:
       - Edit testsuite.par.py parameter:  'ptel_mosfits_dirpath'
       - create local directory: (e.g.):
             mkdir /home/dstarr/scratch/TCP_tests
   - User MUST download test Pairitel mos*.fits tarball into workpath:
             wget http://lyra.berkeley.edu/~jbloom/dstarr/testsuite/testsuite_mosjSN.112.tar.gz
             tar -xzvf testsuite_mosjSN.112.tar.gz
   - User environment variables need to be set:
        TCP_DIR :: path where .../TCP svn-checked-out software exists.

DEPENDENCIES:
   - Tested with Python 2.5.1
   - Tested with MySQL 5.1.22-rc (--with-partition)
   - Requires *NIX shell command:   pkill
   - Dependent packages require/tested with:
      - wcstools-3.6.4
      - sextractor-2.5.0
      - mcs-0.3.2 (for HTM/DIF use)
          - pcre-6.5
      - IRAF 2.12.2
      - ??? PyRAF 1.3 (2006Nov25)
      - swarp-2.16.4
      - numpy, pylab...

DEBUG NOTES:
   - If debugging outside of Lyra LAN:
      - In testsuite.par.py, SET: 'test_suite__use_tunnel_mysql_server':True
      - Shutdown your local MySQL Server, if exists/installed:
                      sudo mysqladmin shutdown
      - Setup SSH 'tunneling' on your local, debugging machine:
                      ssh -L 37921:192.168.1.55:22 pteluser@lyra.berkeley.edu
                      ssh -L 3306:192.168.1.55:3306 pteluser@lyra.berkeley.edu
      - It'd be useful to copy your ~/.ssh/id_rsa.pub to
                                          pteluser@lyra:~/.ssh/authorized_keys
   - If restarting testsuite.py quickly ( < 1 min between runs), you may want
        to manually kill index-socket servers and XMLRPC server
        to avoid errors (from socket conflict)
                      pkill -9 -f python.*obj_id_sockets.py
                      pkill -9 -f python.*do_rpc_server.*
   - To use PDB:
      - In testsuite.par.py, SET: 'test_suite__enable_traceback':True
      - In emacs:     /usr/lib/python2.5/pdb.py testsuite.py
"""
import sys, os
import unittest
import MySQLdb
import time
# DO I need these 2 lines? :
import socket
#socket.setdefaulttimeout(10) # urllib.urlopen() needs a short timeout forced

ingest_tools_path = os.environ.get("TCP_DIR") +'/Software/ingest_tools'
astro_phot_path = os.environ.get("TCP_DIR") +'/Software/AstroPhot'
sys.path.append(ingest_tools_path)
sys.path.append(astro_phot_path)

import ingest_tools
import ptel_astrophot
import feature_extraction_interface

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
from Code import *

# Load parameters:
#f = open('testsuite.par.py')# Import the standard Parameter file
f = open('testsuite.par.py')# Import the standard Parameter file
####f = open('testsuite.transx_production_configs.par.py')# Import the standard Parameter file
exec f
f.close()
pars = parameters

class Test_Suite_Shared_Objects:
    """ This class can be passed in additional structures, objects.
    Here we should sort/extract parameters needed for various test cases.
    """
    def __init__(self, pars):
        self.pars = pars
        self.mysql_hostname = self.pars['mysql_hostname']
        self.mysql_username = self.pars['mysql_username']
        self.mysql_port = self.pars['mysql_port']
        self.ssh_port = self.pars['ssh_port']
        self.TCP_path = self.pars['TCP_path']



        cur_pid = str(os.getpid())
        self.tcp_runs = ingest_tools.TCP_Runtime_Methods(cur_pid=cur_pid)


    def ingest_tools__setup_pars(self):
        """ Set up parameters needed for ingest_tools.py methods/classes.
        NOTE: This method sets up tests for local use.
        """
        # Kill local index sockets, if exist from earlier testing:
        # KLUDGE: This is sort of out of place here, but needs some
        #     buffer time from kills before socket servers are started again.

        ### 20080320: I comment this out right now, since I execute
        #      pkill by hand, anyways. :
        #if not self.pars['test_suite__preserve_tables_databases_servers']:
        #    os.system("pkill -9 -f python.*obj_id_sockets.py")
        #    os.system("pkill -9 -f python.*do_rpc_server.*")
        time.sleep(2) # KLUDGE

        # NOTE: The following is obsolete now that testsuite.par.py does it.
        """
        if self.pars['test_suite__use_tunnel_mysql_server'] == True:
            self.mysql_hostname = self.pars['local_hostname']
            self.mysql_username = self.pars['local_username']
            self.mysql_port = self.pars['local_mysql_port']
            self.ssh_port = self.pars['local_ssh_port']
            self.TCP_path = os.path.expandvars(self.pars['local_TCP_path'])
        else:
            self.mysql_hostname = self.pars['remote_hostname']
            self.mysql_username = self.pars['remote_username']
            self.mysql_port = self.pars['remote_mysql_port']
            self.ssh_port = self.pars['remote_ssh_port']
            self.TCP_path = os.path.expandvars(self.pars['remote_TCP_path'])
        self.pars['ingest_tools_pars']['sdss_astrom_repo_user'] = \
                                                          self.mysql_username
        self.pars['ingest_tools_pars']['rdb_host_ip_2'] = self.mysql_hostname
        self.pars['ingest_tools_pars']['rdb_host_ip_3'] = self.mysql_hostname
        self.pars['ingest_tools_pars']['rdb_host_ip_4'] = self.mysql_hostname
        self.pars['ingest_tools_pars']['rdb_features_host_ip'] = \
                                                        self.mysql_hostname
        self.pars['ingest_tools_pars']['source_region_lock_host_ip'] = \
                                                        self.mysql_hostname
        self.pars['ingest_tools_pars']['footprint_host_ip'] = \
                                                        self.mysql_hostname
        ###
        self.pars['ingest_tools_pars']['rdb_user'] = self.mysql_username
        self.pars['ingest_tools_pars']['source_region_lock_user'] = self.mysql_username
        self.pars['ingest_tools_pars']['footprint_user'] = self.mysql_username

        self.pars['ingest_tools_pars']['sdss_astrom_repo_user'] = self.mysql_username
        """
        return True


    def generate_table_creation_script_strs(self):
        """ Since MySQL source and object tables require DIF MySQL functions,
        triggers to be created via shell; I've opt'd to do table creation with
        a shell script.
        """
        ptf_events_columns_str = ""
        ptf_events_colname_str = ""
        for col_name,col_type in self.pars['ingest_tools_pars']\
                                          ['ptf_candidate_table_columns_tups']:
            ptf_events_columns_str += "%s %s, " % (col_name,col_type)
            ptf_events_colname_str += "%s, " % (col_name)
        for col_name,col_type in self.pars['ingest_tools_pars']\
                                          ['ptf_sub_table_columns_tups']:
            ptf_events_columns_str += "%s %s, " % (col_name,col_type)
            ptf_events_colname_str += "%s, " % (col_name)

        script_str_list = []
        val_list = [self.pars['ingest_tools_pars']['rdb_name_2']]*1
        val_list.extend([ptf_events_columns_str])
        val_list.extend([self.pars['ingest_tools_pars']['rdb_name_2']]*16)
        val_list.extend([ptf_events_colname_str])
        val_list.extend([self.pars['ingest_tools_pars']['rdb_name_2']]*20)
        val_list.append(self.TCP_path)
        val_list.extend([self.pars['ingest_tools_pars']['rdb_name_2']]*25)
        create_object_tables_str = \
            self.pars['create_object_tables_str'] % (tuple(val_list))
        script_str_list.append(create_object_tables_str)

        create_source_tables_str = \
            self.pars['create_source_tables_str'] % ((\
            self.pars['ingest_tools_pars']['rdb_name_4'],) * 19)
        script_str_list.append(create_source_tables_str)
        return script_str_list


    def execute_table_create_scripts(self, script_str_list):
        """ Execute all table-creation scripts which were generated.
        This script may be run locally or remotely, depending on configuration.
        """
        for create_tables_str in script_str_list:
            open(self.pars['table_create_script_fpath'], 'w').write(create_tables_str)
            os.system("chmod u+x %s" % (self.pars['table_create_script_fpath']))
            if ((self.mysql_hostname != '127.0.0.1') and \
                (self.mysql_hostname != 'localhost')):
                scp_str = "scp -P %d %s %s@%s:%s" % (\
                                    self.ssh_port, \
                                    self.pars['table_create_script_fpath'], \
                                    self.mysql_username, self.mysql_hostname, \
                                    self.pars['table_create_script_fpath'])
                os.system(scp_str)
            ssh_exec_str = "ssh -p %d %s@%s %s" % (\
                                    self.ssh_port, \
                                    self.mysql_username, self.mysql_hostname, \
                                    self.pars['table_create_script_fpath'])
            os.system(ssh_exec_str)


    def drop_database(self):
        """ DROP (remote/local) Test MySQL database.
        """
        open(self.pars['table_create_script_fpath'], 'w').write(""" \
                                echo "DROP DATABASE %s;
                                      DROP DATABASE %s;" | mysql""" % \
                              (self.pars['ingest_tools_pars']['rdb_name_2'], \
                               self.pars['ingest_tools_pars']['rdb_name_4']))
        os.system("chmod u+x %s" % (self.pars['table_create_script_fpath']))
        if ((self.mysql_hostname != '127.0.0.1') and \
            (self.mysql_hostname != 'localhost')):
            scp_str = "scp -P %d %s %s@%s:%s" % (\
                                    self.ssh_port, \
                                    self.pars['table_create_script_fpath'], \
                                    self.mysql_username, self.mysql_hostname, \
                                    self.pars['table_create_script_fpath'])
            os.system(scp_str)
        ssh_exec_str = "ssh -p %d %s@%s %s" % (\
                                    self.ssh_port, \
                                    self.mysql_username, self.mysql_hostname, \
                                    self.pars['table_create_script_fpath'])
        os.system(ssh_exec_str)


    def init_featdb_object(self):
        """ Initialize feat_db singleton object.
        """
        self.feat_db = feature_extraction_interface.Feature_database()
        self.feat_db.initialize_mysql_connection(\
              rdb_host_ip=self.mysql_hostname, rdb_user=self.mysql_username,\
              rdb_name=self.pars['ingest_tools_pars']['rdb_features_db_name'],\
feat_lookup_tablename=self.pars['ingest_tools_pars']['feat_lookup_tablename'],\
feat_values_tablename=self.pars['ingest_tools_pars']['feat_values_tablename'])
        self.feat_db.create_feature_lookup_dict()


    def create_tables(self):
        """ Create all necessary MySQL Tables.
        """
        #script_str_list = []
        script_str_list = self.generate_drop_table_script_str_list()
        script_str_list_temp = self.generate_table_creation_script_strs()
        script_str_list.extend(script_str_list_temp)
        self.execute_table_create_scripts(script_str_list)


    def generate_drop_table_script_str_list(self):
        """ DROP all MySQL Tables.
        """
        temp_list = [\
            "DROP TABLE object_test_db.footprint_regions;",
            "DROP TABLE object_test_db.footprint_values;",
            "DROP TABLE object_test_db.obj_srcid_lookup;",
            "DROP TABLE object_test_db.pairitel_events_a;",
            "DROP TABLE object_test_db.pairitel_ingest_accounting;",
            "DROP TABLE object_test_db.ptf_events;",
            "DROP TABLE object_test_db.rfc_ingest_status;",
            "DROP TABLE object_test_db.sdss_events_a;",
            "DROP TABLE object_test_db.sdss_obj_fcr_lookup;",
            "DROP TABLE object_test_db.lbl_ingest_acct",
            "DROP TABLE source_test_db.classid_lookup;",
            "DROP TABLE source_test_db.feat_lookup;",
            "DROP TABLE source_test_db.feat_values;",
            "DROP TABLE source_test_db.source_region_locks;",
            "DROP TABLE source_test_db.src_class_probs;",
            "DROP TABLE source_test_db.srcid_lookup;",
            "CREATE DATABASE object_test_db;",
            "CREATE DATABASE source_test_db;"] # these last two have probably been done so they will fail but that is ok.

        drop_tables_shell_str_list = []
        for elem in temp_list:
            drop_tables_shell_str = """
#!/bin/sh
echo "
%s
" | mysql
        """ % (elem) 
            drop_tables_shell_str_list.append(drop_tables_shell_str)
        return drop_tables_shell_str_list


    def test_table_cols_dict(self, hostname='', username='', db_name='', \
                                                       port='', table_dict={}):
        """ Compare tables in given database with given number-of-cols.
        """
        db = MySQLdb.connect(host=hostname, user=username, db=db_name,port=port)
        cursor = db.cursor()

        for table_name,n_cols in table_dict.iteritems():
            select_str = "DESCRIBE %s" % (table_name)
            cursor.execute(select_str)
            results = cursor.fetchall()
            if len(results) != n_cols:
                return False
        return True


    def check_for_table_existance(self):
        """ Check for existance of various, recently created tables.
        """
        status_1 = self.test_table_cols_dict(hostname=self.mysql_hostname, \
                         username=self.mysql_username, port=self.mysql_port, \
                         db_name=self.pars['ingest_tools_pars']['rdb_name_2'], \
                table_dict=self.pars['testvals_object_database_table_columns'])
        status_2 = self.test_table_cols_dict(hostname=self.mysql_hostname, \
                         username=self.mysql_username, port=self.mysql_port, \
                         db_name=self.pars['ingest_tools_pars']['rdb_name_4'], \
                table_dict=self.pars['testvals_source_database_table_columns'])
        return status_1 and status_2


    def spawn_index_servers(self):
        """ Spawn off all needed index servers.
        NOTE: Testing of index server usablility occurs in later tests.
        """
        for index_type, index_dict in self.pars['index_server'].iteritems():
            exec_str = "$TCP_DIR/Software/ingest_tools/obj_id_sockets.py socket_server_host_ip=%s socket_server_port=%d rdb_server_host_ip=%s rdb_server_user=%s rdb_server_db=%s primary_table_colname=%s obj_id_reference_tablename=%s &" % \
                (self.mysql_hostname,\
                 index_dict['socket_server_port'], \
                 self.mysql_hostname, self.mysql_username, \
                 index_dict['rdb_server_db'], \
                 index_dict['primary_table_colname'], \
                 index_dict['obj_id_reference_tablename'])
            print exec_str
            os.system(exec_str)


    def spawn_XMLRPC_server(self):
        """ Spawn off the XMLRPC server.
        """
        pars = self.pars['ingest_tools_pars']
        exec_str = "$TCP_DIR/Software/ingest_tools/ingest_tools.py do_rpc_server=1 xmlrpc_server_name=%s xmlrpc_server_port=%d rdb_name_2=%s rdb_name_3=%s rdb_user_4=%s rdb_name_4=%s rdb_features_host_ip=%s rdb_features_user=%s rdb_features_db_name=%s source_region_lock_host_ip=%s source_region_lock_user=%s source_region_lock_dbname=%s footprint_host_ip=%s footprint_user=%s footprint_dbname=%s sdss_astrom_repo_host_ip=%s sdss_astrom_repo_dirpath=%s rdb_host_ip_2=%s rdb_user=%s rdb_host_ip_3=%s rdb_host_ip_4=%s sdss_astrom_repo_user=%s &" % (\
            self.pars['xmlrpc_server_name'], \
            pars['xmlrpc_server_port'], \
            pars['rdb_name_2'], \
            pars['rdb_name_3'], \
            pars['rdb_user_4'], \
            pars['rdb_name_4'], \
            self.mysql_hostname, \
            self.mysql_username, \
            pars['rdb_features_db_name'], \
            self.mysql_hostname, \
            self.mysql_username, \
            pars['source_region_lock_dbname'], \
            self.mysql_hostname, \
            self.mysql_username, \
            pars['footprint_dbname'], \
            pars['sdss_astrom_repo_host_ip'], \
            pars['sdss_astrom_repo_dirpath'], \
            self.mysql_hostname, \
            self.mysql_username, \
            self.mysql_hostname, \
            self.mysql_hostname, \
            self.mysql_username)
        print exec_str
        os.system(exec_str)


    def generate_index_server_pars(self, index_type):
        """ Construct a dict which can be (eventually) passed to obj_id_sockets.
        """
        index_server_pars = self.pars['index_server'][index_type]
        index_server_pars['socket_server_host_ip'] = "127.0.0.1"
        index_server_pars['rdb_server_host_ip'] = self.mysql_hostname
        index_server_pars['rdb_server_user'] = self.mysql_username
        return index_server_pars


    def populate_ptel_object_tables_using_list(self, mosfits_fpath_list):
        """ Using a list of Pairitel mos*fits files, extract astrometry,
        photometry and add to MySQL DB.
        """
        footprint_index_server_pars = self.generate_index_server_pars(\
                                                                 'footprint_id')
        ptel_obj_index_server_pars = self.generate_index_server_pars(\
                                                                 'ptel_obj_id')
        ptf_obj_index_server_pars = self.generate_index_server_pars(\
                                                                 'ptf_obj_id')
        sdss_obj_index_server_pars = self.generate_index_server_pars(\
                                                                 'obj_id')
        pars = ingest_tools.pars
        pars.update(self.pars['ingest_tools_pars']) # Use TestSuite params
        # These objects are also used in: populate_ptel_related_sources():
        self.htm_tools = ingest_tools.HTM_Tools(pars) #TODO: this needed?
        self.rcd = ingest_tools.RDB_Column_Defs(\
                    rdb_table_names=pars['rdb_table_names'], \
                    rdb_db_name=pars['rdb_name_2'], \
                    col_definitions=ingest_tools.new_rdb_col_defs)
        self.rcd.init_generate_mysql_strings(pars)
        self.rdbt = ingest_tools.Rdb_Tools(pars, self.rcd, self.htm_tools, \
                    rdb_host_ip=pars['rdb_host_ip_2'], \
                    rdb_user=pars['rdb_user'], \
                    rdb_name=pars['rdb_name_2'], \
                    footprint_index_server_pars=footprint_index_server_pars,\
                    ptel_obj_index_server_pars=ptel_obj_index_server_pars,\
                    sdss_obj_index_server_pars=sdss_obj_index_server_pars,\
                    ptf_obj_index_server_pars=ptf_obj_index_server_pars)

        for mos_globpath in mosfits_fpath_list:
            mos_fname = mos_globpath[mos_globpath.rfind('/')+1:]
            mos_fname_root_trunc = mos_fname[:30]
            try:
                has_been_ingested = self.rdbt.check_obsid_has_been_ingested(\
                                                          mos_fname_root_trunc)
            except:
                print "SKIP INSERT of existing ptel objects:", \
                                                          mos_fname_root_trunc
                continue
            if (has_been_ingested == 0):
                a = ptel_astrophot.PTEL_data_block(mos_globpath, \
                                                   req_filts=['j','h','k'])
                a.runit()
                astrophot_dict = a.out_results
                self.rdbt.insert_pairitel_astrometry_into_rdb(\
                                                     phot_dict=astrophot_dict, \
                                                     mosfits_fpath=mos_fname)
                 #self.rdbt.add_obsid_to_ingested_table(mos_fname_root_trunc)
                self.rdbt.add_obsid_to_ingested_table(mos_fname)


    def cleanup_ptel_mosfits_dirpath(self, ptel_mosfits_dirpath):
        """ Clean work files from Pairitel mos*.fits directory.
        This then makes astrometry and photometry algorithms run again.
        """
        for wildcard in self.pars['mosfits_cleanup_wildcards']:
            rm_str = "rm %s/%s" % (os.path.expandvars(ptel_mosfits_dirpath), \
                                   wildcard)
            os.system(rm_str)


    def populate_sdss_object_tables(self):
        """ Using (SDSS-II object-table www repo), photometrically calibrate
        objects and add to MySQL DB.
        """
        # # # # # # # #
        # TODO: put these in the parameter file:
        ra = 49.599497
        dec = -1.0050998

        pars = ingest_tools.pars
        pars.update(self.pars['ingest_tools_pars']) # Use TestSuite params

        self.slfits_repo = ingest_tools.SDSS_Local_Fits_Repository(pars)
        # TODO: the pars[] below may need to come from test_suite.pars.py
        self.sdss_fcr_iso = ingest_tools.SDSS_FCR_Ingest_Status_Object(\
                rdb_host_ip=pars['rdb_host_ip_3'], \
                rdb_user=self.mysql_username, \
                rdb_name=pars['rdb_name_3'], \
                table_name=pars['sdss_fields_table_name'], \
                sdss_fields_doc_fpath_list= \
                                    pars['sdss_fields_doc_fpath_list'],\
                hostname=self.mysql_hostname)

        # Populate the sdss_events table with all (f,c,r) data, for a (ra,dec):
        self.tcp_runs.sdss_rfc_ingest_using_ra_dec(pars, self.rdbt, \
                                        self.slfits_repo, self.sdss_fcr_iso, \
                                        ra=ra, dec=dec, do_delete_scratch_dir=0)


    def assert_table_values(self, db_cursor, table_name, testvals_list):
        """ Assert some values in a MySQL table.
        """
        for test_vals_dict in testvals_list:
            condition_list = []
            for name,val in test_vals_dict.iteritems():
                condition_list.append("(%s > %lf) and (%s < %lf)" % ( \
                    name, val - self.pars['mysql_float_condition_accuracy'], \
                    name, val + self.pars['mysql_float_condition_accuracy']))
            condition_str = ' AND '.join(condition_list)

            select_str = "SELECT True FROM %s where (%s)" % (table_name, \
                                                            condition_str)
            db_cursor.execute(select_str)
            result = db_cursor.fetchall()
            if result[0][0] != 1:
                return False
        return True


    def assert_table_len(self, db_cursor, table_name, table_row_count):
        """ Count the number rows in given table.  Return T/F depending on
        match with table_row_count.
        """
        select_str = "SELECT count(*) FROM %s" % (table_name)
        db_cursor.execute(select_str)
        result = db_cursor.fetchall()
        if result[0][0] != table_row_count:
            return False
        return True


    def assert_feature_table_values(self):
        """ Assert some values in the Feature tables.
        Query is of form:
SELECT x0.src_id from feat_lookup
INNER JOIN feat_values AS x0 ON feat_lookup.feat_id = x0.feat_id
       AND feat_lookup.filter_id = 5 AND feat_lookup.feat_name = 'std'
INNER JOIN feat_values AS x1 ON x1.src_id = x0.src_id
                            AND x1.feat_id =(SELECT feat_id from feat_lookup 
                                             WHERE feat_name ='first_frequency'
                                             AND filter_id = 5)
INNER JOIN ...
WHERE (x0.feat_val > 0.340430) and (x0.feat_val < 0.340432)
  AND (x1.feat_val > 0.083576) and (x1.feat_val < 0.083578) ...
        """
        db_cursor = self.feat_db.cursor
        for (filt_num, test_vals_dict) in self.pars[\
                                                'testvals_ptel_feature_values']:
            condition_list = []
            join_list = []
            name_val_tuplist = []
            for (name,val) in test_vals_dict.iteritems():
                name_val_tuplist.append((name,val))
            (feat_name,feat_val) = name_val_tuplist[0]
            join_list.append(\
           """inner join feat_values AS x0 ON feat_lookup.feat_id = x0.feat_id
                             AND feat_lookup.filter_id = %d
                             AND feat_lookup.feat_name = '%s'""" % \
                                      (filt_num, feat_name))
            condition_list.append(\
                         "(x0.feat_val > %lf) and (x0.feat_val < %lf)" % ( \
                    feat_val - self.pars['mysql_float_condition_accuracy'], \
                    feat_val + self.pars['mysql_float_condition_accuracy']))

            i = 1
            for feat_name,feat_val in name_val_tuplist[1:]:
                tt_name = "x%d" % (i)
                join_list.append(\
                """inner join feat_values AS %s ON %s.src_id = x0.src_id
                         AND %s.feat_id = (SELECT feat_id from feat_lookup 
                                              WHERE feat_name = '%s'
                                              AND filter_id = %d)""" % \
                               (tt_name, tt_name, tt_name, feat_name, filt_num))

                condition_list.append("(%s.feat_val > %lf) and (%s.feat_val < %lf)"%(\
                    tt_name, 
                    feat_val - self.pars['mysql_float_condition_accuracy'], \
                    tt_name, 
                    feat_val + self.pars['mysql_float_condition_accuracy']))
                i += 1
            condition_str = ' AND '.join(condition_list)
            join_str = "\n".join(join_list)
            select_str = """SELECT x0.src_id from feat_lookup
                            %s WHERE %s """ % (join_str, condition_str)
            #print select_str
            db_cursor.execute(select_str)
            result = db_cursor.fetchall()
            if len(result) != 1:
                return False
        return True


    def assert_feature_extraction_and_parse(self):
        """ Perform feature extraction for a vosource.xml, parse the
        results, and assert that expected features are found.
        """
        return_bool = True # to be filled

        test_feature_dict = { \
            "$TCP_DIR/Data/vosource_SNi_2008ib.xml": { \
                'multiband':{ \
                    'closest_in_light':2.5012624014,    # This is: distance_in_arcmin_to_nearest_galaxy
                    'closest_light_absolute_bmag':-21.21,
                    'closest_light_angle_from_major_axis':-94.8401695909,
                    'closest_light_angular_offset_in_arcmin':3.229580743,
                    'closest_light_physical_offset_in_kpc':54.8115727828,
                    'ecpb':-30.4425607882,
                    'gall':303.185828447,
                    },
                },
            "$TCP_DIR/Data/vosource_tutor12881.xml": { \
                'multiband':{ \
                    'sdss_best_dm':42.609555388,
                    'sdss_best_offset_in_kpc':76.6349855699,
                    'sdss_dered_r':21.012598,
                    'sdss_dist_arcmin':0.194756,
                    'sdss_petro_radius_g':2.969694,
                    'sdss_photo_rest_abs_r':-22.7974,
                    'sdss_photo_rest_iz':0.31285,
                    },
                'H:table1384':{ \
                    'freq1':0.0230410691315,
                    'freq3':0.0262471261565,
                    'median':11.9415,
                    'min':-0.592318489111,
                    'n_points':65,
                    'pair_slope_trend':0.4,
                    'skew':-0.328432633858,
                    'std':0.337081857868,
                    'weighted_average':11.8462184891,
                    },
                },
            }
        
        ##### For debugging & printing all available {feature : values}
        #test = signals_list[0].properties['data']['multiband']['features'].keys()
        #test.sort()
        #for a in test:  print "%40.40s   %s" % (a,str(signals_list[0].properties['data']['multiband']['features'][a]))
        #####
        #test = signals_list[0].properties['data']['H:table1384']['features'].keys()
        #test.sort()
        #for a in test:  print "%40.40s   %s" % (a,str(signals_list[0].properties['data']['H:table1384']['features'][a]))

        
        for xml_fpath,xml_dict in test_feature_dict.iteritems():
            fname = xml_fpath[xml_fpath.rfind('/')+1:] # for DEBUGGING print
            signals_list = []
            gen = generators_importers.from_xml(signals_list)
            gen.generate(xml_handle=os.path.expandvars(xml_fpath))
            for filt_name,filt_dict in xml_dict.iteritems():
                for feat_name,feat_val_expected in filt_dict.iteritems():
                    feat_val_gen = signals_list[0].properties['data'][filt_name]['features'][feat_name]
                    try:
                        if ((float(str(feat_val_gen)) >= feat_val_expected - self.pars['mysql_float_condition_accuracy']) and
                            (float(str(feat_val_gen)) <= feat_val_expected + self.pars['mysql_float_condition_accuracy'])):
                            return_bool = return_bool and True
                            #print "OK feature: %40.40s in %s, expected:%lf, generated:%s" % (feat_name, fname, feat_val_expected, str(feat_val_gen))
                        else:
                            print "WARNING: %40.40s mismatch in %s, expected:%lf, generated:%s" % (feat_name, fname, feat_val_expected, str(feat_val_gen))
                            return_bool = return_bool and False # could just set to False & return, but I want to see all features which fail.
                    except:
                        # Probably get here because feat_val_gen is not float()'able
                        print "WARNING: %40.40s mismatch in %s, expected:%lf, generated:%s" % (feat_name, fname, feat_val_expected, str(feat_val_gen))
                        return_bool = return_bool and False # could just set to False & return, but I want to see all features which fail.
        return return_bool


    def populate_ptel_object_tables_single_mosfits(self):
        """ Using a single  Pairitel mos*fits files, extract astrometry,
        photometry and add to MySQL DB.
        Test the object values.
        """
        if self.pars['test_suite__force_astrom_photometry']:
            self.cleanup_ptel_mosfits_dirpath(self.pars['ptel_mosfits_dirpath'])

        fpath = os.path.expandvars(self.pars['ptel_mosfits_dirpath']) + '/' + self.pars['ptel_mosfits_fname_list'][0]
        self.populate_ptel_object_tables_using_list([fpath])

        
    def populate_ptel_object_tables_multi_mosfits(self):
        """ Using a list of Pairitel mos*fits files, extract astrometry,
        photometry and add to MySQL DB.
        """
        if self.pars['test_suite__force_astrom_photometry']:
            self.cleanup_ptel_mosfits_dirpath(self.pars['ptel_mosfits_dirpath'])

        fpath_list = []
        for fname in self.pars['ptel_mosfits_fname_list'][1:]:
            fpath = os.path.expandvars(self.pars['ptel_mosfits_dirpath']) + '/' + fname
            fpath_list.append(fpath)

        self.populate_ptel_object_tables_using_list(fpath_list)


    def populate_ptel_related_sources(self):
        """ Using Pairitel objects existing in test ptel-object database,
        here we construct sources test source values.
        """
        pars = ingest_tools.pars
        pars.update(self.pars['ingest_tools_pars']) # Use TestSuite params
        srcid_index_server_pars = self.generate_index_server_pars('src_id')

        self.srcdbt = ingest_tools.Source_Database_Tools(pars, self.rcd, \
                    self.htm_tools, \
                    rdb_host_ip=pars['rdb_host_ip_4'], \
                    rdb_user=pars['rdb_user_4'],\
                    rdb_name=pars['rdb_name_4'],\
                    srcid_index_server_pars=srcid_index_server_pars)

        ra_range =  self.pars['testvals_ptel_objects_fov_props']['ra_max'] - \
                    self.pars['testvals_ptel_objects_fov_props']['ra_min']
        dec_range = self.pars['testvals_ptel_objects_fov_props']['dec_max'] - \
                    self.pars['testvals_ptel_objects_fov_props']['dec_min']
        box_range = self.pars['testvals_ptel_source_boxrange_table_count'][0]
        ra_midpt = ra_range/2.0 + \
                        self.pars['testvals_ptel_objects_fov_props']['ra_min']
        dec_midpt = dec_range/2.0 + \
                        self.pars['testvals_ptel_objects_fov_props']['dec_min']

        self.tcp_runs.populate_srcid_table_loop(pars, self.srcdbt, self.rdbt, \
                                       ra=ra_midpt, dec=dec_midpt, \
                                       box_degree_range=box_range, \
                                       box_overlap_factor=0.05)


    def get_features_for_ptel_sources(self):
        """ Generate features for some Pairitel sources. Enter in feature table
        """
        import db_importer
        import feature_extraction_interface

        pars = ingest_tools.pars
        pars.update(self.pars['ingest_tools_pars']) # Use TestSuite params

        ra_range =  self.pars['testvals_ptel_objects_fov_props']['ra_max'] - \
                    self.pars['testvals_ptel_objects_fov_props']['ra_min']
        dec_range = self.pars['testvals_ptel_objects_fov_props']['dec_max'] - \
                    self.pars['testvals_ptel_objects_fov_props']['dec_min']
        box_range = self.pars['testvals_ptel_source_boxrange_table_count'][0]
        ra_midpt = ra_range/2.0 + \
                        self.pars['testvals_ptel_objects_fov_props']['ra_min']
        dec_midpt = dec_range/2.0 + \
                        self.pars['testvals_ptel_objects_fov_props']['dec_min']

        xrsio = ingest_tools.XRPC_RDB_Server_Interface_Object(pars, \
                   self.tcp_runs, self.rdbt, self.htm_tools, self.srcdbt, 0, 0)

        xrsio.get_sources_for_radec_with_feature_extraction(ra_midpt, \
                      dec_midpt, self.pars['testvals_ptel_feature_boxrange'], \
                                        write_ps=0, only_sources_wo_features=0)


    def populate_sdss_sources_using_XMLRPC(self):
        """ Populate some sdss sources by querying the XMLRPC server.
        """
        import xmlrpclib
        server_url = "http://%s:%d" % (self.pars['xmlrpc_server_name'], \
                           self.pars['ingest_tools_pars']['xmlrpc_server_port'])
        server = xmlrpclib.ServerProxy(server_url)
        
        src_list = server.get_sources_for_radec(49.556229, -0.883328, 0.05, '')
        print 'len(src_list) :', len(src_list)
        #print server.system.listMethods()

        # TODO test the source values which are returned. (RDB values check?)
 

class Check_Methods:
    """ Each method in this class wraps a seperate process/function test.
    These methods have access to <global> objects. I would like to restrict use
          to only the "tsso" (Test_Suite_Shared_Objects) global object.
    NOTE: I cannot pass objects into this class.
    NOTE: Nor can I have a __init__() method here.
    """
    def check_03_ingest_tools_setup_pars(self):
        result_bool = tsso.ingest_tools__setup_pars()
        return result_bool

    
    def check_04_ingest_tools_table_creation(self):
        """ CREATE MySQL TABLES.
        """
        if not tsso.pars['test_suite__preserve_tables_databases_servers']:
            #tsso.drop_database()
            # NOTE: Currently tsso.create_tables() drops the tables, not the databases:
            tsso.create_tables()
        tsso.init_featdb_object()
        # # # # TODO: need to drop feat_lookup
        if not tsso.pars['test_suite__preserve_tables_databases_servers']:
            tsso.feat_db.drop_feature_tables()
            tsso.feat_db.create_feature_tables()
        # # # # TODO: need to generate & add feat_lookup
        all_exist = tsso.check_for_table_existance()
        return all_exist

    
    def check_05_spawn_index_servers(self):
        """ Spawn off all needed index servers.
        NOTE: Testing of index server usablility occurs in later tests.
        """
        if not tsso.pars['test_suite__preserve_tables_databases_servers']:
            tsso.spawn_index_servers()
        return True


    def check_06_spawn_XMLRPC_server(self):
        """ Spawn off XMLRPC server.
        """
        if not tsso.pars['test_suite__preserve_tables_databases_servers']:
            tsso.spawn_XMLRPC_server()
        return True


    def check_10_populate_ptel_object_tables_single_mosfits(self):
        """ Using a single  Pairitel mos*fits files, extract astrometry,
        photometry and add to MySQL DB.
        Test the object values.
        """
        if not tsso.pars['test_suite__test_all_functionality']:
            return True # NOTE: TO TEST this function, we need files like /home/dstarr/scratch/TCP_tests//mosjSN.112.1-2008Jan09.fits to exist.  Also see check_10_*, check_11_*, check_15_*
        tsso.populate_ptel_object_tables_single_mosfits()
        assert_bool1 = tsso.assert_table_values(\
            tsso.rdbt.cursor, \
            tsso.pars['ingest_tools_pars']['rdb_table_names']['pairitel'], \
            tsso.pars['testvals_single_ptel_object_values'])
        assert_bool2 = tsso.assert_table_values(\
            tsso.rdbt.cursor, \
            tsso.pars['ingest_tools_pars']['footprint_values_tablename'], \
            tsso.pars['testvals_single_ptel_footprint_values'])
        return assert_bool1 and assert_bool2


    def check_11_populate_ptel_object_tables_multi_mosfits(self):
        """ Using a list of Pairitel mos*fits files, extract astrometry,
        photometry and add to MySQL DB.
        """
        if not tsso.pars['test_suite__test_all_functionality']:
            return True # NOTE: TO TEST this function, we need files like /home/dstarr/scratch/TCP_tests//mosjSN.112.1-2008Jan09.fits to exist.  Also see check_10_*, check_11_*, check_15_*
        tsso.populate_ptel_object_tables_multi_mosfits()
        assert_bool = tsso.assert_table_len(\
                 tsso.rdbt.cursor, \
                 tsso.pars['ingest_tools_pars']['rdb_table_names']['pairitel'],\
                 tsso.pars['testvals_ptel_object_table_count'])
        return assert_bool


    # is this obsolete?  Cant do feat-generation Should we instead do check_30*
    def check_12_populate_sdss_object_tables(self):
        """ Using (SDSS-II object-table www repo), photometrically calibrate
        objects and add to MySQL DB.
        """
        return True

        #NOTE: I comment this out, since there appears to be loaded-module 
        #    conflicts of some sort with feature extraction code....
        tsso.populate_sdss_object_tables()
        return True # TODO: call an assert/test method!
        


    def check_15_populate_ptel_related_sources(self):
        """ Using Pairitel objects existing in test ptel-object database,
        here we construct sources test source values.
        """
        if not tsso.pars['test_suite__test_all_functionality']:
            return True # NOTE: TO TEST this function, we need files like /home/dstarr/scratch/TCP_tests//mosjSN.112.1-2008Jan09.fits to exist.  Also see check_10_*, check_11_*, check_15_*
        tsso.populate_ptel_related_sources()
        # This is broken without some (spatial?) constraint.  So I comment out:
        #assert_bool1 = tsso.assert_table_len(\
        #              tsso.srcdbt.cursor, \
        #              tsso.pars['source_table_name'], \
        #              tsso.pars['testvals_ptel_source_boxrange_table_count'][1])
        assert_bool2 = tsso.assert_table_values(\
                                       tsso.srcdbt.cursor, \
                                       tsso.pars['source_table_name'], \
                                       tsso.pars['testvals_ptel_source_values'])
        return assert_bool2


    def check_20_get_features_for_ptel_sources(self):
        """ Generate features for some Pairitel sources, and check feature vals.
        """
        if not tsso.pars['test_suite__test_all_functionality']:
            return True # NOTE: TO TEST this function, we need files like /home/dstarr/scratch/TCP_tests//mosjSN.112.1-2008Jan09.fits to exist.  Also see check_10_*, check_11_*, check_15_*
        tsso.get_features_for_ptel_sources()
        assert_bool = tsso.assert_feature_table_values()
        #### NOTE: I refrain from asserting feature-table lengths, so
        ####       the addition of new features doesn't FAIL the existing tests.
        return assert_bool


    def check_30_populate_sdss_sources_using_XMLRPC(self):
        """ Populate some sdss sources by querying the XMLRPC server.

        # NOTE: This requires a network connection (to SDSS server)
        """
        return True
        time.sleep(10)
        tsso.populate_sdss_sources_using_XMLRPC()
        return True


    def check_40_feature_extraction_sanity_check(self):
        """ Check that most feature extractors work.

        NOTE: This assumes we are on the network.
              - So that we can test features which depend upon sdss, ned,
                                                   nearest-galaxy servers
        ######NOTE: This assumes we are within the Lyra LAN.
        """
        assert_bool = tsso.assert_feature_extraction_and_parse()
        return assert_bool


class Test_Case_Wrapper(unittest.TestCase):
    """ Unit Tests reside here.
    NOTE: My method naming convention allows sequential testing and method calls
    """
    def test_03_ingest_tools_setup_pars(self):
        self.failUnless(cm.check_03_ingest_tools_setup_pars())

    def test_04_ingest_tools_table_creation(self):
        self.failUnless(cm.check_04_ingest_tools_table_creation())

    def test_05_spawn_index_servers(self):
        self.failUnless(cm.check_05_spawn_index_servers())

    def test_06_spawn_XMLRPC_server(self):
        self.failUnless(cm.check_06_spawn_XMLRPC_server())

    def test_10_populate_ptel_object_tables_single_mosfits(self):
        self.failUnless(cm.check_10_populate_ptel_object_tables_single_mosfits())

    def test_11_populate_ptel_object_tables_multi_mosfits(self):
        self.failUnless(cm.check_11_populate_ptel_object_tables_multi_mosfits())

    def test_12_populate_sdss_object_tables(self):
        self.failUnless(cm.check_12_populate_sdss_object_tables())

    def test_15_populate_ptel_related_sources(self):
        self.failUnless(cm.check_15_populate_ptel_related_sources())

    def test_20_get_features_for_ptel_sources(self):
        self.failUnless(cm.check_20_get_features_for_ptel_sources())

    def test_30_populate_sdss_sources_using_XMLRPC(self):
        self.failUnless(cm.check_30_populate_sdss_sources_using_XMLRPC())

    def test_40_feature_extraction_sanity_check(self):
        self.failUnless(cm.check_40_feature_extraction_sanity_check())


if __name__ == '__main__':
    # KLUDGE: Unfortunatly these 2 classes are used as a global objects:
    tsso = Test_Suite_Shared_Objects(pars)
    cm = Check_Methods()

    if pars['test_suite__enable_traceback']:
        method_list = filter(lambda x: x not in ['__doc__', '__init__', \
                                                 '__module__'], dir(cm))
        method_list.sort()
        for method in method_list:
            method_str = "cm." + method + "()"
            print method_str
            #exec(method_str)
            ### This allows stepping into & breaking in check functions:
            if method_str == "cm.check_40_feature_extraction_sanity_check()":
                cm.check_40_feature_extraction_sanity_check()
            else:
                exec(method_str)
    else:
        unittest.main()

    ### NOTE: I disable this so XMLRPC Servers and Index servers remain active
    ###   - this means the user should execute these manually at shell if 
    ###     they wish to rerun testsuite.py :
    #if not pars['test_suite__preserve_tables_databases_servers']:
    #    os.system("pkill -9 -f python.*obj_id_sockets.py")
    #    os.system("pkill -9 -f python.*do_rpc_server.*")
