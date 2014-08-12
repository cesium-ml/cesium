#!/usr/bin/env python 
"""
   NOTE: This is OBSOLETE?

   v0.2 This is now just a single-instance copy of a ptf_master.py task.
        - This is just intended for PDB debugging and stepping through task code
   v0.1 Initial version: Simulate recieving a PTF transient diff-mag object.
        - NOW see ptf_master.py for this functionality.
"""
import sys, os

ptf_diff_source = {\
    't0':55555.5555, # days
    't1':55555.6000, # days
    'm0':18.0,
    'm1':17.0,
    'm_err0':0.1,
    'm_err1':0.1,
    'ra':123.0,
    'dec':15.0,
    'ra_rms':2.78e-05, # deg
    'dec_rms':2.78e-05,# deg
    }

import ingest_tools
ingest_tools_pars = ingest_tools.pars
import feature_extraction_interface

ingest_tools_pars.update({\
    'rdb_name_2':'object_test_db',
    'rdb_name_3':'object_test_db',
    'footprint_dbname':'object_test_db',
    'classdb_database':'source_test_db',
    'rdb_name_4':'source_test_db',
    'rdb_features_db_name':'source_test_db',
    'source_region_lock_dbname':'source_test_db',
    })


def form_tup_list_using_diff_source(diff_source):
    """ Given a simple diff-source dictionary, form
    tup_list with it's object info.
    """
    #footprint_id is normally generated in insert_object_tuplist_into_rdb()
    #   - retrieved from footprint index server.
    #   - But in PTF case, footprint/limiting mags will be passed in by PTF

    tup_list = []
    tup_list.append([0,
                     diff_source['t0'],
                     diff_source['m0'],
                     diff_source['m_err0'],
                     diff_source['ra'],
                     diff_source['dec'],
                     diff_source['ra_rms'],
                     diff_source['dec_rms']])
    tup_list.append([0,
                     diff_source['t1'],
                     diff_source['m1'],
                     diff_source['m_err1'],
                     diff_source['ra'],
                     diff_source['dec'],
                     diff_source['ra_rms'],
                     diff_source['dec_rms']])
    return tup_list


if __name__ == '__main__':

    htm_tools = ingest_tools.HTM_Tools(ingest_tools_pars)
    rcd = ingest_tools.RDB_Column_Defs(\
                rdb_table_names=ingest_tools_pars['rdb_table_names'], \
                rdb_db_name=ingest_tools_pars['rdb_name_2'], \
                col_definitions=ingest_tools.new_rdb_col_defs)
    rcd.generate_internal_structures('ptf')

    rdbt = ingest_tools.Rdb_Tools(ingest_tools_pars, rcd, htm_tools, \
                rdb_host_ip=ingest_tools_pars['rdb_host_ip_2'], \
                rdb_user=ingest_tools_pars['rdb_user'], \
                rdb_name=ingest_tools_pars['rdb_name_2'])

    sdss_fcr_iso = ingest_tools.SDSS_FCR_Ingest_Status_Object(\
                rdb_host_ip=ingest_tools_pars['rdb_host_ip_3'], \
                rdb_user=ingest_tools_pars['rdb_user'], \
                rdb_name=ingest_tools_pars['rdb_name_3'], \
                table_name=ingest_tools_pars['sdss_fields_table_name'], \
                sdss_fields_doc_fpath_list=\
                               ingest_tools_pars['sdss_fields_doc_fpath_list'],\
                hostname=ingest_tools_pars['hostname'])

    srcdbt = ingest_tools.Source_Database_Tools(ingest_tools_pars, rcd, \
                                                htm_tools, \
                rdb_host_ip=ingest_tools_pars['rdb_host_ip_4'], \
                rdb_user=ingest_tools_pars['rdb_user_4'],\
                rdb_name=ingest_tools_pars['rdb_name_4'])
    slfits_repo = ingest_tools.SDSS_Local_Fits_Repository(ingest_tools_pars)

    tcp_runs = ingest_tools.TCP_Runtime_Methods(cur_pid=str(os.getpid()))
    xrsio = ingest_tools.XRPC_RDB_Server_Interface_Object(ingest_tools_pars, \
                   tcp_runs, rdbt, htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)

    feat_db = feature_extraction_interface.Feature_database()
    feat_db.initialize_mysql_connection(\
             rdb_host_ip=ingest_tools_pars['rdb_features_host_ip'],\
             rdb_user=ingest_tools_pars['rdb_features_user'], \
             rdb_name=ingest_tools_pars['rdb_features_db_name'], \
             feat_lookup_tablename=ingest_tools_pars['feat_lookup_tablename'], \
             feat_values_tablename=ingest_tools_pars['feat_values_tablename'])
    feat_db.create_feature_lookup_dict()

    tup_list = form_tup_list_using_diff_source(ptf_diff_source)
    ###limit_mags_dict = self.get_median_limiting_mags_from_tup_list(\
    ###                                   tup_list, survey_name='pairitel')
    objids_list = rdbt.insert_object_tuplist_into_rdb(tup_list=tup_list, \
                                                              survey_name='ptf')
    n_ingest = len(objids_list)
    src_list = xrsio.get_sources_for_radec_with_feature_extraction(\
                                                ptf_diff_source['ra'], \
                                                ptf_diff_source['dec'], \
                                                0.000277778*5.0, write_ps=0, \
                                                only_sources_wo_features=0,\
                                                skip_remote_sdss_retrieval=True)
    print "Num sources found:", len(src_list)
    print objids_list, src_list

    # ASSERT that len(src_list)==1 AND (src_list[0].d['src_id'] contains all
    #                                   unique src_ids in objids_list[]
    select_str = "SELECT src_id FROM obj_srcid_lookup WHERE survey_id=3 and ("
    for objid in objids_list:
        select_str += "(obj_id = %d) or " % (objid)
    select_str = select_str[:-4] + ")"
    rdbt.cursor.execute(select_str)
    results = rdbt.cursor.fetchall()

    result_srcid_list = []
    for result in results:
        result_srcid_list.append(int(result[0]))

    all_found_sources_in_lookup_table = True
    for source_obj in src_list:
        if source_obj.d['src_id'] not in result_srcid_list:
            print "WARNING: >0 clustered sources were not in obj_srcid_lookup table", result_srcid_list, source_obj.d['src_id']
            all_found_sources_in_lookup_table = False
            break

    srcid_xml_tuple_list = []

    for source_obj in src_list:
        src_id = source_obj.d['src_id']
        srcid_xml_tuple_list.append((src_id, source_obj.xml_string))

    # NOTE: in get_sources_for_radec_with_feature_extraction() we assume
    #       that all given sources do not have features generated.
    (signals_list, srcid_dict) = ingest_tools.\
                                       get_features_using_srcid_xml_tuple_list(\
                                       srcid_xml_tuple_list, write_ps=0)

    srcdbt.update_featsgen_in_srcid_lookup_table(srcid_dict.keys())
    feat_db.insert_srclist_features_into_rdb_tables(signals_list,\
                                                    srcid_dict.keys())
    
    # TODO: classify PTF source.

    # ??? what happens if ptf source existed, but has new points added to it?
    # TODO: Test case:
    #  - testsuite wrapper of ptf_simulation
    #  - this should really test:
    #     - that certain ptf diff-objs are added
    #     - that certain feature values are generated for diff-objs
    #     - that diff-obj data can be incorperated/clustered with SDSS sources

    ##################
    # Will code poll PTF for new sources? & then spawn ipython tasks?

    # TODO: Main PTF Server:
    #  - poll PTF
    #  - for each diff-object:
    #     - apply quick MP checks to diff-object (spawn off a ipython1 task)
    #     - apply other cuts to diff-objects
    #     - if diff-object passes cuts/no-MP:
    #        - spawn off ipython1 task (source gen, feature gen, classify)
    #     - confirm spawned tasks are completed (successful result)

    ######
    # Spawned task:
    #  - should run on a client which already has "import's" initialized.
    #     - does this work?
