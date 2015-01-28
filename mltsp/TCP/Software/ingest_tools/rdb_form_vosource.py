#!/usr/bin/env python 
"""
   v0.1 Given a source-id & XML fpath (to be created),
        query RDBs and form, write XML.
   NOTE: To be called by PHP script.

TODO: test this code (form VOSource.xml) for pairitel, tcptutor, sdss

"""
import sys, os
"""
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                'Software/feature_extract/Code'))
# These are only needed in: retrieve_tcptutor_vosource_and_add_features()
from Code import generators_importers

try:
    from Code import *
except:
    pass # lyra fails somewhere in import, probably due to Python2.4 use.
import db_importer
"""
import random

#sys.path.append("/scisoft/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages")
#os.environ["TCP_DIR"] = "/Network/Servers/boom.cluster.private/Home/pteluser/src/TCP/"
import MySQLdb

import ingest_tools # This seems overkill, but module contains all RDB params.
import feature_extraction_interface
import db_importer

class Rdb_Form_VOsource:
    def __init__(self, pars, rdbt, srcdbt, feat_db, dbi_src):
        self.pars = pars
        self.rdbt = rdbt
        self.srcdbt = srcdbt
        self.feat_db = feat_db
        self.rdb_gen_vosource_urlroot = pars['rdb_gen_vosource_urlroot']
        self.rdb_gen_vosource_dirpath = pars['rdb_gen_vosource_dirpath']
        self.dbi_src = dbi_src


    def add_object_table_data_to_sdict(self, src_id, survey_name, sdict):
        """ Query RDB and add data to source's sdict{}.
        """
        # SDSS:
        #SELECT t, jsb_mag, jsb_mag_err FROM sdss_events_a JOIN obj_srcid_lookup USING (obj_id) WHERE obj_srcid_lookup.src_id = 106597;
        # PAIRITEL:
        #SELECT t, jsb_mag, jsb_mag_err,filt FROM pairitel_events_a JOIN obj_srcid_lookup USING (obj_id) WHERE obj_srcid_lookup.src_id = 18804;
        # TCPTUTOR:
        #SELECT obs_data.obsdata_time, obs_data.obsdata_val, obs_data.obsdata_err from obs_data JOIN observations ON observations.observation_id = obs_data.observation_id WHERE observations.source_id = 9183;


        ### Object table query:
        if survey_name == 'tcptutor':
            tcptutor_src_id = src_id - 100000000
            self.db = MySQLdb.connect(host=self.pars['tcptutor_hostname'], user=self.pars['tcptutor_username'], db=self.pars['tcptutor_database'], passwd=self.pars['tcptutor_password'])
            self.cursor = self.db.cursor()
            select_str = "SELECT obs_data.obsdata_time, obs_data.obsdata_val, obs_data.obsdata_err, filters.filter_name from obs_data JOIN observations ON observations.observation_id = obs_data.observation_id JOIN filters ON filters.filter_id = observations.filter_id WHERE observations.source_id = %s" % (tcptutor_src_id)
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
        elif survey_name == 'pairitel':
            select_str = "SELECT t, jsb_mag, jsb_mag_err,filt FROM %s JOIN %s USING (obj_id) WHERE %s.src_id=%d" % \
                         (self.pars['rdb_table_names']['pairitel'], \
                          self.pars['obj_srcid_lookup_tablename'], \
                          self.pars['obj_srcid_lookup_tablename'], src_id)
            self.rdbt.cursor.execute(select_str)
            results = self.rdbt.cursor.fetchall()
        elif survey_name == 'sdss':
            select_str = "SELECT t, jsb_mag, jsb_mag_err,filt FROM %s JOIN %s USING (obj_id) WHERE %s.src_id=%d" % \
                         (self.pars['rdb_table_names']['sdsss'], \
                          self.pars['obj_srcid_lookup_tablename'], \
                          self.pars['obj_srcid_lookup_tablename'], src_id)
            self.rdbt.cursor.execute(select_str)
            results = self.rdbt.cursor.fetchall()
        try:
            for result in results:
                if type(result[3]) == type(2):
                    # sdss & pairitel case
                    filt_name = self.feat_db.final_features.filter_list[result[3]]
                else:
                    # (tcptutor) Explicit filtername given
                    filt_name = result[3]
                if not sdict['ts'].has_key(filt_name):
                    sdict['ts'][filt_name] = {}
                    sdict['ts'][filt_name]['t'] = []
                    sdict['ts'][filt_name]['m'] = []
                    sdict['ts'][filt_name]['m_err'] = []
                sdict['ts'][filt_name]['t'].append(result[0])
                sdict['ts'][filt_name]['m'].append(result[1])
                sdict['ts'][filt_name]['m_err'].append(result[2])
        except:
            print "Failed query:", select_str
            raise


    def add_source_table_data_to_sdict(self, src_id, survey_name, sdict):
        """ Query RDB and add data to source's sdict{}.
        """
        ### Source table query:
        select_str = "SELECT ra, decl, ra_rms, dec_rms, feat_gen_date FROM %s WHERE src_id=%d" % (self.pars['srcid_table_name'], src_id)
        self.srcdbt.cursor.execute(select_str)
        results = self.srcdbt.cursor.fetchall()
        try:
            sdict['ra'] = str(results[0][0])
            sdict['dec'] = str(results[0][1])
            sdict['ra_rms'] = str(results[0][2])
            sdict['dec_rms'] = str(results[0][3])
            sdict['feat_gen_date'] = str(results[0][4])
        except:
            print "Failed query:", select_str
            raise


    def add_feature_table_data_to_sdict(self, src_id, survey_name, sdict):
        """ Query RDB and add data to source's sdict{}.
        """
        ### Features table query:
        select_str = "SELECT %s.feat_val, %s.feat_name, %s.filter_id, %s.doc_str FROM %s JOIN %s USING (feat_id) WHERE %s.src_id = %d" % (self.pars['feat_values_tablename'], self.pars['feat_lookup_tablename'], self.pars['feat_lookup_tablename'], self.pars['feat_lookup_tablename'], self.pars['feat_values_tablename'], self.pars['feat_lookup_tablename'], self.pars['feat_values_tablename'], src_id)
        self.feat_db.cursor.execute(select_str)
        results = self.feat_db.cursor.fetchall()
      
        sdict['feature_docs'] = {}
        try:
            for result in results:
                filt_name = self.feat_db.final_features.filter_list[result[2]]
                sdict['feature_docs'][result[1]] = result[3] # __doc__ string in TABLE
                if not sdict['features'].has_key(filt_name):
                    sdict['features'][filt_name] = {}
                sdict['features'][filt_name][result[1]] = str(result[0])
        except:
            print "Failed query:", select_str
            raise


    def determine_survey_name(self, src_id):
        """ Determine which survey a source-id came from.
        """
        #NOTE: survey_name : 'pairitel', 'sdss', OR 'tcptutor'
        if src_id > 100000000:
            return 'tcptutor'
        else:
            select_str = "SELECT survey_id from %s WHERE src_id=%d LIMIT 1" % \
                               (self.pars['obj_srcid_lookup_tablename'], src_id)
            self.rdbt.cursor.execute(select_str)
            results = self.rdbt.cursor.fetchall()
            if len(results) != 1:
                print "src_id unknown"
                raise
            else:
                for survey_name,survey_id in self.pars['survey_id_dict'].\
                                                                iteritems():
                    if results[0][0] == survey_id:
                        return survey_name
                print "src_id unknown:", type(results[0][0])
                raise
        print "src_id unknown" # probably dont get here
        raise


    def form_sdict_via_rdb_selects(self, src_id, survey_name):
        """ Form db_importer.Source style sdict{} using src_id
        by quering RDB tables.
        """
        sdict = {}
        sdict['src_id'] = src_id
        sdict['features'] = {}
        sdict['ts'] = {}

        self.add_object_table_data_to_sdict(src_id, survey_name, sdict)
        self.add_source_table_data_to_sdict(src_id, survey_name, sdict)
        self.add_feature_table_data_to_sdict(src_id, survey_name, sdict)
        return sdict


    def retrieve_tcptutor_xml_and_merge_with_xml(self,src_id, rdb_gen_xml_str):
        """ Retrieve TCPTUTOR VOSource from TCPTUTOR server and merge with
        given XML, which has feature info.
        """
        tcptutor_src_id = src_id - 100000000
        source_url = "http://lyra.berkeley.edu/tutor/pub/vosource.php?Source_ID=%d" % (tcptutor_src_id)
        wget_fpath = "/tmp/%d.wget" % (random.randint(0,100000000))
        wget_str = "wget -t 1 -T 5 -O %s %s" % (wget_fpath, source_url)
        os.system(wget_str)
        if not os.path.exists(wget_fpath):
            raise
        fp = open(wget_fpath)
        mondo_str = fp.read()
        fp.close()
        lines = mondo_str.split('\n')

        return_xml_str = ""
        i_tcptut_votimeseries_end = 0
        for line in lines:
            return_xml_str += line  + '\n'
            if "</VOTIMESERIES>" in line:
                #i_line_votimeseries_end = i
                break
            i_tcptut_votimeseries_end += 1
        #TODO: append write_xml... to line

        gen_lines = rdb_gen_xml_str.split('\n')
        i = 0
        for line in gen_lines:
            if "<Features>" in line:
                i_gen_features_begin = i
            elif "</Features>" in line:
                i_gen_features_end = i
            i += 1

        for line in gen_lines[i_gen_features_begin:i_gen_features_end+1]:
            return_xml_str += line + '\n'

        for line in lines[i_tcptut_votimeseries_end+1:]:
            return_xml_str += line + '\n'

        os.system("rm " + wget_fpath)
        return return_xml_str

        # TODO: read XML from file
        # find </VOTIMESERIES>
        # insert <Features>
        #          </Features>
        # return resulting XML


    def generate_vosource_file(self, src_id, vosource_fpath):
        """Given a srcid, retrieve from RDB and form VOSource XML.
        Write XML to web local path.
        """
        survey_name = self.determine_survey_name(src_id)

        sdict = self.form_sdict_via_rdb_selects(src_id, survey_name)
        self.dbi_src.source_dict_to_xml(sdict)
        write_xml_str = self.dbi_src.xml_string

        if survey_name == 'tcptutor':
            merged_xml_str = self.retrieve_tcptutor_xml_and_merge_with_xml(\
                                                         src_id, write_xml_str)
            write_xml_str = merged_xml_str

        # KLUDGE: write xml locally, then scp to server/web host (lyra):
        fpath = '/tmp/' + vosource_fpath[vosource_fpath.rfind('/')+1:]

        fp = open(fpath, 'w')
        fp.write(write_xml_str)
        fp.close()
        
        scp_command = "scp -q %s %s:%s" % (fpath, self.pars['rdb_gen_vosource_hostname'], vosource_fpath)
        os.system(scp_command)
        os.system("rm " + fpath)


    def get_vosource_url_for_srcid(self, src_id):
        """ Given a srcid, retrieve from RDB and form VOSource XML.
        Write XML to web local path and return URL to VOSource XML.

        """
        vosource_url = "%s/%d.xml" % (self.rdb_gen_vosource_urlroot, src_id)
        vosource_fpath = "%s/%d.xml" % (self.rdb_gen_vosource_dirpath, src_id)

        # # # # # # # # # #
        # # # # I comment this out for TESTING only.
        #if os.path.exists(vosource_fpath):
        #    return vosource_url # VOSource...xml already exists

        #try:
        if 1:
            self.generate_vosource_file(src_id, vosource_fpath)
        #except:
        #    return "database_query_error"
        print '<A href="%s">Source ID=%d VOSource.xml</A>' % (vosource_url, \
                                                              src_id)
        return '<A href="%s">Source ID=%d VOSource.xml</A>' % (vosource_url, \
                                                              src_id)


if __name__ == '__main__':
    #src_id = 100013522 # 8
    server_ip = "192.168.1.65"
    server_user = "pteluser"
    ingest_tools.pars['rdb_host_ip_2'] = server_ip
    ingest_tools.pars['rdb_user'] = server_user
    ingest_tools.pars['rdb_name_2'] = 'object_test_db'
    ingest_tools.pars['rdb_host_ip_4'] = server_ip
    ingest_tools.pars['rdb_user_4'] = server_user
    ingest_tools.pars['rdb_name_4'] = 'source_test_db'
    ingest_tools.pars['rdb_features_host_ip'] = server_ip
    ingest_tools.pars['rdb_features_user'] = server_user
    ingest_tools.pars['rdb_features_db_name'] = 'source_test_db'
    ingest_tools.pars['tcptutor_hostname'] = 'lyra.berkeley.edu'
    ingest_tools.pars['tcptutor_username'] = 'pteluser'
    ingest_tools.pars['tcptutor_password'] = 'Edwin_Hubble71'
    ingest_tools.pars['source_region_lock_host_ip'] = server_ip
    ingest_tools.pars['source_region_lock_user'] = server_user
    ingest_tools.pars['source_region_lock_dbname'] = 'source_test_db'
    ingest_tools.pars['footprint_host_ip'] = server_ip
    ingest_tools.pars['footprint_user'] = server_user
    ingest_tools.pars['footprint_dbname'] = "object_test_db"

    #if (len(sys.argv) != 2):
    #    print "invalid input"
    #    sys.exit()
    #try:
    #    src_id = int(sys.argv[1])
    #except:
    #    print "invalid src_id"
    #    sys.exit()

    rdbt = ingest_tools.Rdb_Tools(ingest_tools.pars, None, None, \
                rdb_host_ip=ingest_tools.pars['rdb_host_ip_2'], \
                rdb_user=ingest_tools.pars['rdb_user'], \
                rdb_name=ingest_tools.pars['rdb_name_2'])
    srcdbt = ingest_tools.Source_Database_Tools(\
                ingest_tools.pars, None, None, \
                rdb_host_ip=ingest_tools.pars['rdb_host_ip_4'], \
                rdb_user=ingest_tools.pars['rdb_user_4'],\
                rdb_name=ingest_tools.pars['rdb_name_4'])

    feat_db = feature_extraction_interface.Feature_database()
    feat_db.initialize_mysql_connection(\
                    rdb_host_ip=ingest_tools.pars['rdb_features_host_ip'],\
                    rdb_user=ingest_tools.pars['rdb_features_user'], \
                    rdb_name=ingest_tools.pars['rdb_features_db_name'], \
        feat_lookup_tablename=ingest_tools.pars['feat_lookup_tablename'], \
        feat_values_tablename=ingest_tools.pars['feat_values_tablename'])

    dbi_src = db_importer.Source(make_dict_if_given_xml=False)

    #rfv = Rdb_Form_VOsource(ingest_tools.pars, rdbt, srcdbt, feat_db, dbi_src)
    #rfv.get_vosource_url_for_srcid(src_id)
    #sys.exit()
    import SimpleXMLRPCServer
    server = SimpleXMLRPCServer.SimpleXMLRPCServer(\
                          ("lyra.berkeley.edu", \
                           34583))
    #server = SimpleXMLRPCServer.SimpleXMLRPCServer(\
    #                      ("192.168.1.65", \
    #                       34583))
    server.register_instance(Rdb_Form_VOsource(ingest_tools.pars, rdbt, srcdbt, feat_db, dbi_src))
    server.register_multicall_functions()
    server.register_introspection_functions()
    server.serve_forever()
