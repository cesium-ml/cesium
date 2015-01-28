#!/usr/bin/env python 
"""
   v0.1 snclassifier_testing_wrapper.py

   Script used to test out Dovi SN-classifier results.

NOTE: much has been adapted from get_classifications_for_caltechid.py..__main__()
"""
import os, sys
import pprint

import snlc_classifier
import get_classifications_for_caltechid

import copy
import math
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                'Software/RealBogus/Code'))
import cand
import ingest_tools
import ptf_master
import jdac
import numpy
import time

### This is needed for the snlc_classifier stuff:
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract')
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code')
from Code import generators_importers
sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors')
import mlens3  # for microlensing classification



def apply_sn_classifier(xml_fpath):
    """ Apply Dovi SN classifier to the source described in the given vosource.xml filepath

    """
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=os.path.expandvars(xml_fpath))
    gen.sig.add_features_to_xml_string(gen.signals_list)
    #NOTE: this is a string:   gen.sig.xml_string


    # For TESTING:
    #d = mlens3.EventData(os.path.abspath(os.environ.get("TCP_DIR") + "/Data/vosource_tutor12881.xml"))

    d = mlens3.EventData(gen.sig.xml_string)

    #gen.sig.write_xml(out_xml_fpath=new_xml_fpath)

    #NOTE: print gen.sig.x_sdict.keys()
    #['feat_gen_date', 'src_id', 'ra', 'features', 'feature_docs', 'dec', 'dec_rms', 'class', 'ra_rms', 'ts']

    sn =  snlc_classifier.Dovi_SN(datamodel=d,x_sdict=gen.sig.x_sdict,doplot=False)#,doplot=True)

    return sn.final_results


def get_ptfids_from_berkeley_local_db():
    """ Get from tranx local mysql db.

    This is intended to be used only while the Caltech DB is down.
    """
    import MySQLdb
    reduced_list = []
    mysql_db = MySQLdb.connect(host="192.168.1.25", user="pteluser", db="object_test_db")
    mysql_cursor = mysql_db.cursor()

    select_str = "SELECT caltech_candidate_shortname FROM source_test_db.caltech_classif_summary"
    mysql_cursor.execute(select_str)
    results = mysql_cursor.fetchall()
    for row in results:
        if row[0] != 'None':
            reduced_list.append(row[0])
    return reduced_list



if __name__ == '__main__':

       
    pars = {'intermediate_xml_dirpath':os.path.expandvars('$HOME/scratch/ptf_snclassifer_intermediate_xmls')}

    DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
    PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                     rdbt=DiffObjSourcePopulator.rdbt)
    Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassificationsForPtfid(rdbt=DiffObjSourcePopulator.rdbt, PTFPostgreServer=PTFPostgreServer, DiffObjSourcePopulator=DiffObjSourcePopulator)
    Caltech_DB = get_classifications_for_caltechid.CaltechDB()

    if len(sys.argv) > 1:
        reduced_list = sys.argv[1:]
    else:
        # Get a list of ptf_ids from all Berkeley-locally available database...
        reduced_list = get_ptfids_from_berkeley_local_db()

    #reduced_list = ['10xk'] # TODO: use a longer list of ptf-ids, or allow argv commandline input:

    final_sn_classifications = {}
    for short_name in reduced_list:
        #matching_source_dict = get_classifications_for_caltechid.table_insert_ptf_cand(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB, ptf_cand_shortname=short_name)
        ptf_cand_dict = Caltech_DB.get_ptf_candid_info___non_caltech_db_hack(cand_shortname=short_name)
        #TODO: check if srcid.xml composed from ptf_cand_dict{srcid} is in the expected directory.  If so, just pass that xml-fpath as xml_handle.  Otherwise, generate the xml string (and write to file) and pass that.
        xml_fpath = "%s/%d_%s.xml" % (pars['intermediate_xml_dirpath'], ptf_cand_dict['srcid'], short_name)
        if os.path.exists(xml_fpath):
            print "Found on disk:", xml_fpath 
        else:
            # NOTE: Since the Caltech database is currently down and we know we've ingested these ptf-ids already into our local database...
            #"""
            (ingested_srcids, ingested_src_xmltuple_dict) = Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
                                                   ra=ptf_cand_dict['ra'], \
                                                   dec=ptf_cand_dict['dec'], \
                                                   ptf_cand_dict=ptf_cand_dict, \
                                                   do_get_classifications=False) # 20100127: dstarr added the last False term due to Caltech's database being down, and our lack of interest in general classifications right now.

            matching_source_dict = Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                     ptf_cand_dict, ingested_srcids)
            #pprint.pprint(matching_source_dict)
            #"""
            
            fp = open(xml_fpath, 'w')
            fp.write(ingested_src_xmltuple_dict[ptf_cand_dict['srcid']])
            fp.close()
            print "Wrote on disk:", xml_fpath 
            #pprint.pprint(ptf_cand_dict)


        sn_classifier_final_results = apply_sn_classifier(xml_fpath)
        #pprint.pprint(sn_classifier_final_results)

        final_sn_classifications[short_name] = sn_classifier_final_results

    # This contains the final classification results:
    pprint.pprint(final_sn_classifications)
    print
