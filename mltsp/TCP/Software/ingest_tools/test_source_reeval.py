#!/usr/bin/env python 
"""
   v0.1 Test script for SDSS source re-evaluation

NOTE: derived from ptf_master.py
"""
import sys, os
import random


class Diff_Obj_Source_Populator:
    """ Matches/generates source for diff-obj, features...
     - This is instantiated on a ipython1 node
     - This should be initialized (module imports) by PTF-polling thread
     - NOTE: I cant extract this class into a different module, since
        ptf_master invokes methods in clients, via ipython1 
    """
    def __init__(self, pars):
        self.pars = pars
        self.import_modules()

    def import_modules(self):
        """ Import all module dependencies during client "initialization"
        """
        # store specific function as something local?
        import ingest_tools
        ingest_tools_pars = ingest_tools.pars
        import feature_extraction_interface
        ingest_tools_pars.update({\
            'rdb_name_2':self.pars['object_dbname'],
            'rdb_name_3':self.pars['object_dbname'],
            'footprint_dbname':self.pars['object_dbname'],
            'classdb_database':self.pars['source_dbname'],
            'rdb_name_4':self.pars['source_dbname'],
            'rdb_features_db_name':self.pars['source_dbname'],
            'source_region_lock_dbname':self.pars['source_dbname'],
            })
        self.htm_tools = ingest_tools.HTM_Tools(ingest_tools_pars)
        self.rcd = ingest_tools.RDB_Column_Defs(\
                    rdb_table_names=ingest_tools_pars['rdb_table_names'], \
                    rdb_db_name=ingest_tools_pars['rdb_name_2'], \
                    col_definitions=ingest_tools.new_rdb_col_defs)
        self.rcd.generate_internal_structures('ptf')

        self.rdbt = ingest_tools.Rdb_Tools(ingest_tools_pars, self.rcd, \
                    self.htm_tools, \
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_2'], \
                    rdb_user=ingest_tools_pars['rdb_user'], \
                    rdb_name=ingest_tools_pars['rdb_name_2'])

        self.sdss_fcr_iso = ingest_tools.SDSS_FCR_Ingest_Status_Object(\
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_3'], \
                    rdb_user=ingest_tools_pars['rdb_user'], \
                    rdb_name=ingest_tools_pars['rdb_name_3'], \
                    table_name=ingest_tools_pars['sdss_fields_table_name'], \
                    sdss_fields_doc_fpath_list=\
                               ingest_tools_pars['sdss_fields_doc_fpath_list'],\
                    hostname=ingest_tools_pars['hostname'])
        self.srcdbt = ingest_tools.Source_Database_Tools(ingest_tools_pars, \
                                                    self.rcd, self.htm_tools, \
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_4'], \
                    rdb_user=ingest_tools_pars['rdb_user_4'],\
                    rdb_name=ingest_tools_pars['rdb_name_4'])
        self.slfits_repo = ingest_tools.SDSS_Local_Fits_Repository(\
                                                              ingest_tools_pars)
        self.tcp_runs = ingest_tools.TCP_Runtime_Methods(\
                                                       cur_pid=str(os.getpid()))
        self.xrsio = ingest_tools.XRPC_RDB_Server_Interface_Object(\
                   ingest_tools_pars, self.tcp_runs, self.rdbt, self.htm_tools,\
                   self.srcdbt, self.sdss_fcr_iso, self.slfits_repo)

        self.feat_db = feature_extraction_interface.Feature_database()
        self.feat_db.initialize_mysql_connection(\
                 rdb_host_ip=ingest_tools_pars['rdb_features_host_ip'],\
                 rdb_user=ingest_tools_pars['rdb_features_user'], \
                 rdb_name=ingest_tools_pars['rdb_features_db_name'], \
             feat_lookup_tablename=ingest_tools_pars['feat_lookup_tablename'],\
             feat_values_tablename=ingest_tools_pars['feat_values_tablename'])
        self.feat_db.create_feature_lookup_dict()

        # Make this accessible for later use:
        self.get_features_using_srcid_xml_tuple_list = \
                           ingest_tools.get_features_using_srcid_xml_tuple_list


class Source_Reevaluation:
    """ Used for testing, to re-evaluate whether objects are still associated
    with existing sources.
    """
    def __init__(self, pars):
        self.pars = pars

    def retrieve_obj_dict_alldict(self):
        """ Retrieve a list of object_dict{} for a ra,dec rectangle region.
        """
        select_str = """SELECT obj_id, ra, decl, ra_rms, dec_rms, filt, t, jsb_mag_err FROM %s WHERE DIF_HTMRectV(%lf, %lf, %lf, %lf)
        """ % (self.pars['object_htm_tablename'],
               self.pars['ra_low'],
               self.pars['dec_low'],
               self.pars['ra_high'],
               self.pars['dec_high'],
               )
        self.dosp.rdbt.cursor.execute(select_str)
        results = self.dosp.rdbt.cursor.fetchall()

        obj_dict_alldict = {}
        for result in results:
            #obj_dict = {'obj_id':result[0],
            obj_dict = {'obj_ids':[result[0]],
                        'ra':result[1],
                        'decl':result[2],
                        'ra_rms':result[3],
                        'dec_rms':result[4],
                        'filts':[result[5]],
                        't':result[6],
                        'm_err':result[7],
                        'src_id':0,
                }
            obj_dict_alldict[result[0]] = obj_dict
        return obj_dict_alldict


    def retrieve_source_dict_alldict(self):
        """ Retrieve a dict of source_dict{} for a ra,dec rectangle region.
        """
        select_str = """SELECT src_id, ra, decl, ra_rms, dec_rms, nobjs
        FROM %s WHERE DIF_HTMRectV(%lf, %lf, %lf, %lf)
        """ % (self.pars['source_htm_tablename'],
               self.pars['ra_low'],
               self.pars['dec_low'],
               self.pars['ra_high'],
               self.pars['dec_high'],
               )
        self.dosp.srcdbt.cursor.execute(select_str)
        results = self.dosp.srcdbt.cursor.fetchall()

        source_dict_alldict = {}
        for result in results:
            source_dict = {'src_id':result[0],
                        'ra':result[1],
                        'decl':result[2],
                        'ra_rms':result[3],
                        'dec_rms':result[4],
                        'nobjs':result[5],
                }
            source_dict_alldict[result[0]] = source_dict
        return source_dict_alldict

    
    def retrieve_objid_srcid_lookupdict(self, srcid_list):
        """ Retrieve a lookup dict for getting srcid = __dict__[objid]
        """
        objid_srcid_lookup = {}
        for src_id in srcid_list:
            select_str = """SELECT obj_id 
            FROM %s WHERE src_id=%d AND survey_id=%d
            """ % (self.pars['obj_srcid_tablename'],
                   src_id,
                   self.pars['survey_id'],
                   )
            self.dosp.rdbt.cursor.execute(select_str)
            results = self.dosp.rdbt.cursor.fetchall()

            for result in results:
                objid_srcid_lookup[result[0]] = src_id

        return objid_srcid_lookup


    def test_multi_source_generation(self):
        """ Determine a set of objects for a ra,dec region, randomize list.
        Generate source for this object list, store obj-source lookup dict.
        Do this generation several times, compare obj-source lookup dicts
           for each unique object randomization.

        The obj-source matching shoul represent how effectiove the algorithm is.
        """
        self.dosp = Diff_Obj_Source_Populator(self.pars)

        obj_dict_alldict = self.retrieve_obj_dict_alldict()

        local_srcdbt_sources = []

        objid_to_filt_dict = {}
        objid_to_time_dict = {}
        objid_to_survey_dict = {}
        # ??? The output of the following function is whatever is needed to
        #    update/add sources.


        (reduced_srcindex_tobe_inserted, srcids_to_ignore, srcindex_tobe_updated, srcindex_tobe_inserted) = \
              self.dosp.srcdbt.calculate_obj_source_associations_new(obj_dict_alldict, local_srcdbt_sources, objid_to_filt_dict, objid_to_time_dict, objid_to_survey_dict)


    # obsolete:
    def test_multi_source_generation_old(self):
        """ Determine a set of objects for a ra,dec region, randomize list.
        Generate source for this object list, store obj-source lookup dict.
        Do this generation several times, compare obj-source lookup dicts
           for each unique object randomization.

        The obj-source matching shoul represent how effectiove the algorithm is.
        """
        n_reeval_iterations = 2
        
        self.dosp = Diff_Obj_Source_Populator(self.pars)

        obj_dict_alldict = self.retrieve_obj_dict_alldict()

        srcindex_tobe_inserted = []
        srcindex_tobe_updated = []
        fake_srcid = 0 # This is decremented, so all temporary srcids
        #          are negative.  Before UPDATEing sources, I will determine
        #          Database-valid src-id indexes, and assign them instead.
        skipped_obj_dicts = []

        for i_reeval in xrange(n_reeval_iterations):

            local_srcdbt_sources = []

            reordered_obj_lists = source_dict_alldict.values()
            random.shuffle(reordered_obj_lists)

            for obj_id,obj_dict in obj_dict_alldict.iteritems():

                for i in range(len(obj_dict['obj_ids'])):
                    objid_to_filt_dict[obj_dict['obj_ids'][i]] = \
                                                            obj_dict['filts'][i]
                    objid_to_time_dict[obj_dict['obj_ids'][i]] = obj_dict['t']

                (odds_list, matching_src_dict) = \
                            self.dosp.srcdbt.is_object_associated_with_source(\
                            obj_dict, local_srcdbt_sources, sigma_0=3.0)
                do_make_new_source = \
                       self.dosp.srcdbt.check_whether_new_source_to_be_created(\
                            objs_dict, obj_dict, odds_list, matching_src_dict, \
                               srcindex_tobe_inserted, srcindex_tobe_updated, \
                                  objid_to_filt_dict, objid_to_time_dict, \
                             local_srcdbt_sources, do_check_double_source=True)
                # TODO: add the rest of calculate_obj_source_associations_original() ... the important obj-source lookup table is in ???



    def test_nonthread_nonipython1(self):
        """ Use this non-ipython1 version for PDB step-through debugging.

        NOTE: A bit KLUDGEY since this just repeats PTF_Poll_And_Spawn methods.
        """
        self.dosp = Diff_Obj_Source_Populator(self.pars)

        obj_dict_alldict = self.retrieve_obj_dict_alldict()
        source_dict_alldict = self.retrieve_source_dict_alldict()

        objid_srcid_lookup = self.retrieve_objid_srcid_lookupdict(
                                                    source_dict_alldict.keys())

        for obj_id,obj_dict in obj_dict_alldict.iteritems():
            (odds_list, matching_src_dict) = self.dosp.srcdbt.is_object_associated_with_source(obj_dict, source_dict_alldict.values(), sigma_0=3.0)
            #print obj_id, objid_srcid_lookup.get(obj_id,'NONE'), odds_list, matching_src_dict
            if len(matching_src_dict) > 1:
                print "+1 ASSOCIATED SOURCE", obj_id, objid_srcid_lookup.get(obj_id,'NONE'), odds_list, matching_src_dict
            if objid_srcid_lookup.get(obj_id,'NONE') != matching_src_dict.values()[0]['src_id']:
                print "MISMATCH", obj_id, objid_srcid_lookup.get(obj_id,'NONE'), odds_list, matching_src_dict
            print '! odds_list = %d \tmatching_src_dict = %d\tnobjs = %d' % (len(odds_list), len(matching_src_dict), matching_src_dict.values()[0]['nobjs'])
        print 'yo'

        # TODO: what I really want is to re-generate all sources using
        #     obj_dict_alldict.

        # This would take the obj_dict_alldict[]
        #   and essentially execute
        #      calculate_obj_source_associations_original()
        # - using an empty local_srcdbt_sources, to start with
        # - and randomizing the object list, which is currently generated
        #      by objs_dict.values()
        

        # And, remember, the point is to find

        # If I have some sort of obj -> source dict which
        #    i

        # there should be a linera algebra way of solving this.

        #For  obj_list order & it's corresponding associated srcids dict:
        #   - I check to see that an object's pointed-two source-list
        #      contais the same objects for another obj-list association ontol

        # obj_1 : * to src_1 [obj_1_id]
        # obj_2 : * to src_2 [obj_2_id, obj_3_id]
        # obj_3 : * to src_2 [obj_2_id, obj_3_id]
        # obj_4 : * to src_3 [obj_4_id]

        #################

        # So, it seems that running is_object_associated_with_source() using
        #    existing sources still preserves the same object<->source mapping
        #  - meaning: every object is associated with the same, orig source.

        # So, to re-evaluate sources, I need to:
        #  - generate new sources,
        #  - determine whether new sources are duplictes of old-sources
        #     - this will be difficult to do.
        #     - maybe match sources by those with the greatest number of shared
        #       objects.
        #     -
        # The other option would be to:
        #  - Upon source creation, we randomize the object-list, and generate
        #    sources.
        #  - Then, we compare the sources in several different src-generations
        #    and identify which sources have essentially the same objects (80%)
        #  - Then, we create a source-dict/list of the strongest-found sources
        #     and their most/all associated objects
        #  - And we then continue building source for the rest of the objects.
        #   

        ###########
        # TODO: I need the outer interface to this source creating algorithm to be exactly like existing code:
        # - EMULATE: populate_srcids_using_objs_dict()
        # - INPUT: objs_dict
        # - INPUT: local_srcdbt_sources, objid_to_filt_dict,
        #          objid_to_time_dict, objid_to_survey_dict

        # TODO: I need to be able to iterate some arbitrary number of times,
        #    randominzing the object-ingestion list
        #  - forming & returning new source-dicts

        # TODO: I need to compare the resulting complete set of source-dicts
        #  - match sources in differnt lists by having > 80% similar objects
        #      - test that 80% is good: raise the % to see if not many fewer
        #          sources are matched (find a sweet spot, with reliability).
        #  - return a normal source dict of the strongly matched source
        #        (and their associated objects)
        #  - OUTPUT like: ___existing_function___

        # TODO: do a final source-matching/creation for the remainding objects
        #    using this reliable source-dict

        #####
        # TEST: test that sources found don't have convolved light curves
        #         - plot for Josh's case.
        # TODO: make sure that re-eval software-agent code can run correctly
        # TODO: make sure that on-the-fly source re-evaluation can be called
        #       for newly inserted objects
        #    - using objects from multiple surveys, etc...
        # TODO: re-populate sources for all of SDSS?

if __name__ == '__main__':

    #pars = {
    #    'survey_id':1, # 1: Pairitel
    #    'object_htm_tablename':'pairitel_events_a_htm',
    #    'object_dbname':'object_test_db',
    #    'source_dbname':'source_test_db',
    #    'source_htm_tablename':'srcid_lookup_htm',
    #    'obj_srcid_tablename':'obj_srcid_lookup',
    #    'ra_low':137.40,
    #    'ra_high':137.49,
    #    'dec_low':33.01,
    #    'dec_high':33.20,
    #    }

    pars = {
        'survey_id':0, # 1: Pairitel
        'object_htm_tablename':'sdss_events_a_htm',
        'object_dbname':'object_db',
        'source_dbname':'source_db',
        'source_htm_tablename':'srcid_lookup_htm',
        'obj_srcid_tablename':'obj_srcid_lookup',
        'ra_low':316.500208,
        'ra_high':316.503208,
        'dec_low':0.428389,
        'dec_high':0.431389,
        }

    SourceReevaluation = Source_Reevaluation(pars)
    #SourceReevaluation.test_nonthread_nonipython1()
    SourceReevaluation.test_multi_source_generation()
