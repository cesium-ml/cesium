#!/usr/bin/env python 
###!/Library/Frameworks/Python.framework/Versions/Current/bin/python
"""
   v0.1 Given a local RDB valid source-id, this code forms a VOSouce.xml
        which will then be written to file (for export).

NOTE: This file (form_vosource_xml_using_rdb.py) is really only used by PHP script
      which generates an XML for users pressing a webpage link/button.

NOTE: so, the classes and mthods in here are not critical and probably shouldnt be depended upon in other code since there are some kludges and hacks.

NOTE: debug using:

/Library/Frameworks/Python.framework/Versions/Current/lib/python2.5/pdb.py form_vosource_xml_using_rdb.py 402126

"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
#os.system("whoami")
#os.environ["PYTHON_EGG_CACHE"] = "/Library/Frameworks/Python.framework/Versions/4.1.30101/lib/python2.5/site-packages/"

#os.environ["TCP_REDUX_DIR"]="/Network/Servers/boom.cluster.private/Home/pteluser/src/redux/"
#os.environ["TCP_DATA_DIR"]="/tmp/TCP_scratch/"
#os.environ["TCP_DIR"]="/Network/Servers/boom.cluster.private/Home/pteluser/src/TCP/"
#os.environ["TCP_WCSTOOLS_DIR"]="/Network/Servers/boom.cluster.private/Home/pteluser/src/install/wcstools-3.6.4/bin/"
#os.environ["TCP_SEX_BIN"]="/scisoft/bin/sex"
#os.environ["MPLCONFIGDIR"]="/tmp"

import MySQLdb
import copy

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                   'Software/feature_extract/Code'))
import db_importer

from . import ingest_tools
ingest_tools_pars = ingest_tools.pars



class MakeVosourceUsingRdb:
    """ This clss primarily does:
    Given a local RDB valid source-id, this code forms a VOSouce.xml
        which will then be written to file (for export).
    """


    def __init__(self, pars={}):
        self.pars = pars

        # source/classif/feature db connection:
        self.src_db = MySQLdb.connect(host=pars['rdb_host_ip_4'],
                                      user=pars['rdb_user_4'],
                                      db=pars['rdb_name_4'],
                                      port=pars['rdb_port_4'])
        self.src_cursor = self.src_db.cursor()

        # object db connection:
        self.obj_db = MySQLdb.connect(host=pars['rdb_host_ip_2'],
                                      user=pars['rdb_user'],
                                      db=pars['rdb_name_2'],
                                      port=pars['rdb_port_2'])
        self.obj_cursor = self.obj_db.cursor()


    def fill_sdict_with_sourcedb_data(self, src_id, sdict):
        """  query source_db
        """
        select_str = "SELECT ra, decl, ra_rms, dec_rms FROM %s WHERE src_id=%d" % (\
            self.pars['srcid_table_name'], src_id)
        self.src_cursor.execute(select_str)
        results = self.src_cursor.fetchall()

        assert(len(results) == 1) # sanity check

        sdict['ra'] = results[0][0]
        sdict['dec'] = results[0][1]
        sdict['ra_rms'] = results[0][2]
        sdict['dec_rms'] = results[0][3]
        

    def fill_sdict_with_limiting_mag_data(self, srcid, s_dict):
        """  query limiting magnitudes table, store results

        NOTE: This is derived from:
        ingest_tools.py::add_limitmags_to_sourcedict(self, source_dict)
        """
        filter_conv_dict = {'g':'ptf_g', 'R':'ptf_r'}
        #for srcid in source_dict.keys():
        if 1:
            if 'ra' in s_dict:
                ra = s_dict['ra']
                dec = s_dict['dec']
            
            for filt_name in filter_conv_dict.values():
                if filt_name not in s_dict['ts']:
                    s_dict['ts'][filt_name] = {}
                if 'limitmags' not in s_dict['ts'][filt_name]:
                    s_dict['ts'][filt_name]['limitmags'] = {'t':[], 'lmt_mg':[]}
            select_str = "SELECT filter, ujd, lmt_mg from %s WHERE (MBRContains(radec_region, GeomFromText('POINT(%lf %lf)'))) ORDER BY filter, ujd" % (self.pars['ptf_mysql_candidate_footprint'], ra, dec)
            self.obj_cursor.execute(select_str)
            rdb_rows = self.obj_cursor.fetchall()

            for filt_name,filt_dict in s_dict['ts'].iteritems():
                for row in rdb_rows: 
                    (filt, ujd, lmt_mg) = row
                    filt_name = filter_conv_dict[filt]
                    s_dict['ts'][filt_name]['limitmags']['t'].append(float(ujd))
                    s_dict['ts'][filt_name]['limitmags']['lmt_mg'].append(float(lmt_mg))


    def fill_sdict_with_objectdb_data(self, src_id, sdict):
        """  query object_db
        """
        select_str = "SELECT ujd, mag, mag_err, filter FROM %s JOIN %s ON (%s.id = %s.obj_id) WHERE %s.src_id=%d AND %s.survey_id=%d" % (\
            self.pars['rdb_table_names']['ptf'],
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['rdb_table_names']['ptf'],
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['obj_srcid_lookup_tablename'],
            src_id,
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['survey_id_dict']['ptf'])


        self.obj_cursor.execute(select_str)
        results = self.obj_cursor.fetchall()

        data_dict = {}
        for result in results:
            filt_name = self.pars['filter_conv_dict'][result[3]] # this translates to: ptf_g or ptf_r
            if filt_name not in data_dict:
                data_dict[filt_name] = {'t_list':[],
                                        'm_list':[],
                                        'm_err_list':[]}
            data_dict[filt_name]['t_list'].append(result[0])
            data_dict[filt_name]['m_list'].append(result[1])
            data_dict[filt_name]['m_err_list'].append(result[2])

        for filt_name,filt_dict in data_dict.iteritems():
            sdict['ts'] = {filt_name:{'IDs': ['col1', 'col2', 'col3'],
                                      'ordered_column_names': ['t', 'm', 'm_err'],
                                      'units': ['day', 'mag', 'mag'],
                                      'ucds': [None,
                                               'phot.mag;em.opt.%s' % (filt_name),
                                               'stat.error;phot.mag;em.opt.%s' % (filt_name)],
                                      'm':filt_dict['m_list'],
                                      'm_err':filt_dict['m_err_list'],
                                      't':filt_dict['t_list'],
                                      }
                           }
        return filt_name
    

    # obsolete: pre 20091102:
    def fill_sdict_with_objectdb_data__old(self, src_id, sdict):
        """  query object_db
        """
        select_str = "SELECT ujd, mag, mag_err, filter FROM %s JOIN %s ON (%s.id = %s.obj_id) WHERE %s.src_id=%d AND %s.survey_id=%d" % (\
            self.pars['rdb_table_names']['ptf'],
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['rdb_table_names']['ptf'],
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['obj_srcid_lookup_tablename'],
            src_id,
            self.pars['obj_srcid_lookup_tablename'],
            self.pars['survey_id_dict']['ptf'])


        self.obj_cursor.execute(select_str)
        results = self.obj_cursor.fetchall()

        filt_name = results[0][3]

        t_list = []
        m_list = []
        m_err_list = []
        for result in results:
            t_list.append(result[0])
            m_list.append(result[1])
            m_err_list.append(result[2])

        sdict['ts'] = {filt_name:{'IDs': ['col1', 'col2', 'col3'],
                                  'ordered_column_names': ['t', 'm', 'm_err'],
                                  'units': ['day', 'mag', 'mag'],
                                  'ucds': [None,
                                           'phot.mag;em.opt.%s' % (filt_name),
                                           'stat.error;phot.mag;em.opt.%s' % (filt_name)],
                                  'm':m_list,
                                  'm_err':m_err_list,
                                  't':t_list,
                                  }
                       }
        return filt_name


    def generate_classification_xmlstring(self, src_id, vosource_class_obj):
        """  query source_db for classifications related data
        and then form the classification section of vosource.xml string
        since db_importer.py has methods to do this only.
        Return the string.
        """
        select_str = "SELECT %s.class_name, %s.prob, %s.schema_comment FROM %s JOIN %s USING (schema_id, class_id) WHERE %s.src_id = %d" % (\
            self.pars['classid_lookup_tablename'],
            self.pars['src_class_probs_tablename'],
            self.pars['classid_lookup_tablename'],
            self.pars['src_class_probs_tablename'],
            self.pars['classid_lookup_tablename'],
            self.pars['src_class_probs_tablename'],
            src_id)

        self.src_cursor.execute(select_str)
        results = self.src_cursor.fetchall()
        
        #classname_list = []
        #prob_list = []
        #schema_comment_list = []
        for result in results:
            #classname_list.append(results[0][0])
            #prob_list.append(results[0][1])
            #schema_comment_list.append(results[0][2])

            classname = result[0]
            prob = result[1]
            schema_comment = result[2]

            vosource_class_obj.add_classif_prob(class_name=classname,
                                                prob=prob,
                                                class_schema_name=schema_comment,
                                                human_algo="machine")


    def fill_sdict_with_features_data(self, src_id, sdict, filt_name):
        """ Retrieve features from source-db, and insert them into sdict
        
        sdict["features"][filt_name][feat_name] = feat_str_val

        """
        select_str = "SELECT %s.feat_name, %s.doc_str, %s.feat_val FROM %s JOIN %s USING (feat_id) WHERE %s.src_id=%s" % (\
                    self.pars['feat_lookup_tablename'],
                    self.pars['feat_lookup_tablename'],
                    self.pars['feat_values_tablename'],
                    self.pars['feat_values_tablename'],
                    self.pars['feat_lookup_tablename'],
                    self.pars['feat_values_tablename'],
                    src_id)

        self.src_cursor.execute(select_str)
        results = self.src_cursor.fetchall()

        sdict["features"] = {filt_name:{}}
        sdict["feature_docs"] = {filt_name:{}}
        for result in results:
            feat_name = result[0]
            doc_str = result[1]
            if result[2] is None:
                feat_val = "None"
            else:
                feat_val = str(result[2])

            sdict["features"][filt_name][feat_name] = feat_val
            sdict["feature_docs"][filt_name][feat_name] = doc_str


    def retrieve_sdict_for_srcid(self, src_id, vosource_class_obj):
        """ query rdb using src_id.  Fill a db_importer style sdict
        """
        sdict = {}
        sdict['src_id'] = src_id
        sdict['feat_gen_date'] = ""
        filt_name = self.fill_sdict_with_objectdb_data(src_id, sdict)
        self.fill_sdict_with_sourcedb_data(src_id, sdict)
        self.fill_sdict_with_limiting_mag_data(src_id, sdict)
        self.fill_sdict_with_features_data(src_id, sdict, filt_name)
        self.generate_classification_xmlstring(src_id, vosource_class_obj)

        return sdict
    

    def generate_vsrc_xml_using_srcid(self, src_id=-1, out_xml_fpath=""):
        """ Given a source-id which is in local RDB,
        This forms and writes a vosource.xml to given filepath.
        """
        vosource_class_obj = db_importer.vosource_classification_obj()
        
        sdict = self.retrieve_sdict_for_srcid(src_id, vosource_class_obj)

        source = db_importer.Source(make_dict_if_given_xml=False,
	                         make_xml_if_given_dict=False,
	                         doplot=False)

        source.source_dict_to_xml(sdict)
        xmlstr_with_classes = vosource_class_obj.add_class_xml_to_existing_vosource_xml(\
                                                                      source.xml_string)
        source.xml_string = xmlstr_with_classes
        if len(out_xml_fpath) > 3:
	        source.write_xml(out_xml_fpath=out_xml_fpath)
	else:
		print(source.xml_string)


if __name__ == '__main__':

    #print "USAGE: ./form_vosource_xml_using_rdb.py <src_id> <out_xml_fpath>"

    if len(sys.argv) > 1:
        src_id = int(sys.argv[1])
    else:
        src_id = 29267

    out_xml_fpath = ""
    if len(sys.argv) > 2:
        out_xml_fpath = sys.argv[2]
    #else:
    #    out_xml_fpath = '/tmp/rdb_%d.xml' % (src_id)

    pars = ingest_tools_pars

    Make_Vosource_Using_Rdb = MakeVosourceUsingRdb(pars=pars)

    Make_Vosource_Using_Rdb.generate_vsrc_xml_using_srcid( \
                    src_id=src_id, out_xml_fpath=out_xml_fpath)
