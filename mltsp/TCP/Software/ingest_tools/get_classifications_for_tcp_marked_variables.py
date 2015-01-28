#!/usr/bin/env python 
""" This queries all sources in the source_test_db.exp_user_classifs TABLE
and re-generates total_mags using LBL pgsql, updates mysql ptf_events,
(culls bad subtraction epochs), and regenerates features and classifications.
"""

import sys, os
import MySQLdb
import ingest_tools
import ptf_master
import get_classifications_for_caltechid

def get_srcid_positions_dict():
    """ get {srcid:{'ra':.., 'dec':...}, ..} for sources in
    source_test_db.exp_user_classifs TABLE
    """
    pars = { \
    'mysql_user':"pteluser",
    'mysql_hostname':"192.168.1.25",
    'mysql_database':'source_test_db',
    'mysql_port':3306,
        }

    db = MySQLdb.connect(host=pars['mysql_hostname'],
                         user=pars['mysql_user'],
                         db=pars['mysql_database'],
                         port=pars['mysql_port'])
    cursor = db.cursor()

    select_str = "SELECT src_id, ra, decl, class_name FROM source_test_db.exp_user_classifs"

    cursor.execute(select_str)
    results = cursor.fetchall()

    out_dict = {}
    for row in results:
        out_dict[row[0]] = {'ra':row[1],
                            'dec':row[2],
                            'class_name':row[3]}
    for src_id, src_dict in out_dict.iteritems():
        select_str = "SELECT obj_id from object_test_db.obj_srcid_lookup where survey_id=3 and src_id=%d" % (src_id)
        cursor.execute(select_str)
        results = cursor.fetchall()
        src_dict['obj_ids'] = []
        for row in results:
            src_dict['obj_ids'].append(row[0])
    return out_dict


def populate_TCP_sources_for_nonptf_radec(ra=None, dec=None, PTFPostgreServer=None, DiffObjSourcePopulator=None):
    """ Get TCP classifications when given (ra,dec) or ...
    return in some condensed dict.
    """

    ptf_diff_obj_list = PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql({}, index_offset=0, \
                                                                           n_last_rows=1, \
                                                          test_data_substitute_pgsql_with_mysql=False, \
                                                          do_spatial_query=True, \
                                                          ra=ra, \
                                                          dec=dec)
    ingested_srcids = []
    is_done = False
    for diff_obj in ptf_diff_obj_list:
        for obj_id in diff_obj['obj_ids']:
            #if obj_id in src_dict['obj_ids']:
            if 1:
                # NOTE: unlike normal TCP / ptf_master.py: we generate features for n_epochs >= 1 so that srcid_xml_tuple_list is made available below:
                (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db, n_epochs_cut=1)
                #if n_objs >= 1:
                #    DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list, n_objs=n_objs)
                for srcid,xmllines in srcid_xml_tuple_list:
                    ingested_srcids.append(srcid)
                is_done = True    
                break
        if is_done:
            break
    return ingested_srcids


def get_overall_classification_without_repopulation(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB=None, matching_source_dict={}):
    """ Similar function (derived from):
          get_classifications_for_caltechid.py:table_insert_ptf_cand()
    """
    src_dict = matching_source_dict
    return {'overall_type':'junk'}

    """
    ##### TCP classifications:
    tcp_classif = Get_Classifications_For_Ptfid.get_TCP_classifications(matching_source_dict)
    #print tcp_classif

    ##### IsRock / PyMPChecker Classifier:
    rock_classif = Get_Classifications_For_Ptfid.get_is_rock_info(matching_source_dict, src_dict)
    #print "rock_classif['is_rock_count']", rock_classif['is_rock_count']

    ##### Josh's D.A. Classifier:
    # # # # This should do all of the following in a function and the L689 - 704 stuff, just returning/adding to jdac_dict:
    #        extracted_prob(float,'Null'), extracted_name(string,'Null'), extracted_confid(float, 'Null')
    jdac_class = Get_Classifications_For_Ptfid.extract_jdac_classifs(src_dict)
    #print "JDAC:", jdac_class


    # TODO: I should actually do a count for all epochs in source...
    ##### Nearby candidate classifier:
    nearby_classif = Get_Classifications_For_Ptfid.get_nearby_classifier_info(matching_source_dict, src_dict)
    #print "nearby_classif['is_interesting_count']", nearby_classif['is_interesting_count']

    overall_classification = Get_Classifications_For_Ptfid.generate_overall_classification(matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, src_dict)
    return overall_classification
    """



def table_insert_tcp_marked_variables(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB=None, src_dict={}):
    """ Similar function (derived from):
          get_classifications_for_caltechid.py:table_insert_ptf_cand()
    """
    ingested_srcids = populate_TCP_sources_for_nonptf_radec(ra=src_dict['ra'], \
                                                            dec=src_dict['dec'],
                                                            PTFPostgreServer=PTFPostgreServer,
                                                            DiffObjSourcePopulator=DiffObjSourcePopulator)

    matching_source_dict = Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                 src_dict, ingested_srcids)

    if len(matching_source_dict) == 0:
        print "no associate / generated / matching source found for:"
        print "src_dict=", src_dict
        print "ingested_srcids=",  ingested_srcids
        return 

    # # # # # # # # # # # # # # # # # #
    # # TODO: still get the following functions to work for non-ptf case:
    # # # # # #

    ##### TCP classifications:
    tcp_classif = Get_Classifications_For_Ptfid.get_TCP_classifications(matching_source_dict)
    print tcp_classif

    ##### IsRock / PyMPChecker Classifier:
    rock_classif = Get_Classifications_For_Ptfid.get_is_rock_info(matching_source_dict, src_dict)
    print "rock_classif['is_rock_count']", rock_classif['is_rock_count']

    ##### Josh's D.A. Classifier:
    # # # # This should do all of the following in a function and the L689 - 704 stuff, just returning/adding to jdac_dict:
    #        extracted_prob(float,'Null'), extracted_name(string,'Null'), extracted_confid(float, 'Null')
    jdac_class = Get_Classifications_For_Ptfid.extract_jdac_classifs(src_dict)
    print "JDAC:", jdac_class


    # TODO: I should actually do a count for all epochs in source...
    ##### Nearby candidate classifier:
    nearby_classif = Get_Classifications_For_Ptfid.get_nearby_classifier_info(matching_source_dict, src_dict)
    print "nearby_classif['is_interesting_count']", nearby_classif['is_interesting_count']

    #tcp_classif['is_junk'] = False
    #if nearby_classif['is_interesting_count'] <= 1:
    #    tcp_classif['is_junk'] = True

    overall_classification = Get_Classifications_For_Ptfid.generate_overall_classification(matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, src_dict)


    (ordered_colname_list, cond_class_dict) = Get_Classifications_For_Ptfid.make_condensed_classif_dict(matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, src_dict, overall_classification)
    
    Get_Classifications_For_Ptfid.insert_into_table(ordered_colname_list, cond_class_dict, tablename="source_test_db.tcpvariable_classif_summary")
    Get_Classifications_For_Ptfid.ordered_colname_list = []
    Get_Classifications_For_Ptfid.cond_class_dict = {}





if __name__ == '__main__':


    srcid_position_dict = get_srcid_positions_dict()

    DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)

    PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                     rdbt=DiffObjSourcePopulator.rdbt)
    Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassificationsForPtfid(rdbt=DiffObjSourcePopulator.rdbt)

    # TODO: get list of srcids from Mysql table   (with ra, dec)
    # TODO: get diff_obj{} for src_id
    # TODO: INSERT .... ON DUPLICATE UPDATE:
    #       - like get_classifications_for_caltechid.py:get_classifications_for_ptfid()

    for src_id,src_dict in srcid_position_dict.iteritems():
        print '>>>', src_id
        table_insert_tcp_marked_variables(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB=None, src_dict=src_dict)

