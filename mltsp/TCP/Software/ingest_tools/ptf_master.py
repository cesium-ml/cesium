#!/usr/bin/env python 
"""
   v0.2 Version which allows polling and retrieval of objects from PTF TABLE.
   v0.1 Initial version: Poll for PTF objects, spawn source generation tasks.
         - Poll LBL PTF server for new diff-objects
         - apply quick MP checks to diff-object (spawn off a ipython1 task)
         - apply other cuts to diff-objects
         - if diff-object passes cuts/no-MP:
            - spawn off ipython1 task (source gen, feature gen, classify)
         - confirm spawned tasks are completed (successful result)

NOTE: This requires TCP MySQL servers, objid/srcid socket servers, etc. set up:
        ./testsuite.py
 
NOTE: Prior to running, need to initialize Ipython1 Cluster server:
        ipcluster -n 2

TO run, generally just do:
        ./ptf_master.py

"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
import datetime
import math
from . import ingest_tools
import gc # for DEBUGGING
#from guppy import hpy # for DEBUGGING
from numpy import random
import time
#from ipython1.kernel import client
import copy
import signal
import threading
from . import calculate_ptf_mag


def mjd_2_datetime(mjd):
    """ Convert MJD day-decimal date to python datetime object.
    Derived from TCP/Software/AstroPhot/ptel_astrophot.py..ut2mjd()

    NOTE: Leap-second offsets are unpredictable and thus hardcoded as conditions
    """

    mjd_0 =  datetime.datetime(1858,11,17)
    dtime_wo_leapsecond_correction = datetime.timedelta(days=mjd) + mjd_0

    ut = dtime_wo_leapsecond_correction
    # These conditionals are taken from ptel_astrophot.py..ut2mjd():
    if ut > datetime.datetime(2006,1,1):
    	off = 33.0
    elif ut > datetime.datetime(1999,1,1):
    	off = 32.0
    elif ut > datetime.datetime(1997,7,1):
    	off = 31.0
    elif ut > datetime.datetime(1996,1,1):
    	off = 30.0
    elif ut > datetime.datetime(1994,7,1):
    	off = 29.0	
    else:
    	print('dont know how to do this .. actually I do but I laszy')
        return datetime.datetime(1,1,1) # Some obvious ERROR value is returned

    return dtime_wo_leapsecond_correction - datetime.timedelta(seconds=off)


global signal_occurred
signal_occurred = ''
def sig_TERM_handler(signum, frame):
    """ Used to pass user Signal to Condition loop
    """
    global signal_occurred
    signal_occurred = 'SIGTERM'

def sig_INT_handler(signum, frame):
    """ Used to pass user Signal to Condition loop
    """
    global signal_occurred
    signal_occurred = 'SIGINT'


class Diff_Obj_Source_Populator:
    """ Matches/generates source for diff-obj, features...
     - This is instantiated on a ipython1 node
     - This should be initialized (module imports) by PTF-polling thread
     - NOTE: I cant extract this class into a different module, since
        ptf_master invokes methods in clients, via ipython1 
    """
    def __init__(self, use_postgre_ptf=True):
        self.use_postgre_ptf = use_postgre_ptf
        self.import_modules()
        self.pars = {'02mp_arcsec_thresh':5.0,
                     '34mp_arcsec_thresh':24.0,
                     '5mp_arcsec_thresh':30.0} #Last case currently not used.

    def import_modules(self):
        """ Import all module dependencies during client "initialization"
        """
        # store specific function as something local?
        #import ingest_tools
        ingest_tools_pars = ingest_tools.pars
        from . import feature_extraction_interface
        ingest_tools_pars.update({\
            'rdb_name_2':'object_test_db',
            'rdb_name_3':'object_test_db',
            'footprint_dbname':'object_test_db',
            'classdb_database':'source_test_db',
            'rdb_name_4':'source_test_db',
            'rdb_features_db_name':'source_test_db',
            'source_region_lock_dbname':'source_test_db',
            'weka_java_classpath':os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar'),
            })
        self.htm_tools = ingest_tools.HTM_Tools(ingest_tools_pars)
        self.rcd = ingest_tools.RDB_Column_Defs(\
                    rdb_table_names=ingest_tools_pars['rdb_table_names'], \
                    rdb_db_name=ingest_tools_pars['rdb_name_2'], \
                    rdb_port=ingest_tools_pars['rdb_port_2'], \
                    col_definitions=ingest_tools.new_rdb_col_defs)
        self.rcd.generate_internal_structures('ptf')

        self.rdbt = ingest_tools.Rdb_Tools(ingest_tools_pars, self.rcd, \
                    self.htm_tools, \
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_2'], \
                    rdb_user=ingest_tools_pars['rdb_user'], \
                    rdb_name=ingest_tools_pars['rdb_name_2'], \
                    rdb_port=ingest_tools_pars['rdb_port_2'], \
                    use_postgre_ptf=self.use_postgre_ptf)

        self.sdss_fcr_iso = ingest_tools.SDSS_FCR_Ingest_Status_Object(\
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_3'], \
                    rdb_user=ingest_tools_pars['rdb_user'], \
                    rdb_name=ingest_tools_pars['rdb_name_3'], \
                    rdb_port=ingest_tools_pars['rdb_port_3'], \
                    table_name=ingest_tools_pars['sdss_fields_table_name'], \
                    sdss_fields_doc_fpath_list=\
                               ingest_tools_pars['sdss_fields_doc_fpath_list'],\
                    hostname=ingest_tools_pars['hostname'], \
                    db=self.rdbt.db)
        self.srcdbt = ingest_tools.Source_Database_Tools(ingest_tools_pars, \
                                                    self.rcd, self.htm_tools, \
                    rdb_host_ip=ingest_tools_pars['rdb_host_ip_4'], \
                    rdb_user=ingest_tools_pars['rdb_user_4'],\
                    rdb_name=ingest_tools_pars['rdb_name_4'], \
                    rdb_port=ingest_tools_pars['rdb_port_4'])
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
                 rdb_port=ingest_tools_pars['rdb_features_port'], \
              feat_lookup_tablename=ingest_tools_pars['feat_lookup_tablename'],\
              feat_values_tablename=ingest_tools_pars['feat_values_tablename'], \
                 db=self.srcdbt.db)
        self.feat_db.create_feature_lookup_dict()

        # Make this accessible for later use:
        self.get_features_using_srcid_xml_tuple_list = \
                           ingest_tools.get_features_using_srcid_xml_tuple_list

        from . import classification_interface
        self.class_interface = classification_interface.\
                                        ClassificationHandler(ingest_tools_pars, \
                                                              db=self.srcdbt.db)


    def insert_simple_ptf_object(self, ra=None, dec=None,
                                 m=None, m_err=None, t=None):
        """ This inserts a simple object into Mysql PTF object table.

         This is intended for testing use only & not for production use.
        """
        # DEBUG / KLUDGE:
        # NOTE: This is only for testing, since objid, etc.. will be generated
        #        by LBL PTF database stream.
        # NOTE: The count(*) style creation done here is KLUDGY and inefficient
        #       and far from ideal for parallel INSERTs and is intended for
        #       testing purposes only.
        # NOTE: The KLUDGY fix of try/excepting the insert is only used because
        #        insert_simple_ptf_object() method is intended for testing use only.

        # Retrieve n existing rows.
        #   - KLUDGE: this assumes max(objid_candid) == count(*)
        # This KLUDGE assures that we don't INSERT existing object-ids,
        #     but it also assumes the ptf_events object table does not
        #     actually contain polled PTF object-ids (which are incremented
        #     independently).
        select_str = "SELECT count(*) FROM %s" % (\
                                       self.rdbt.pars['rdb_table_names']['ptf'])
        self.rdbt.cursor.execute(select_str)
        results = self.rdbt.cursor.fetchall()

        objid_offset = 1
        while objid_offset <= 100: 
            objid_candid = results[0][0] + objid_offset

            insert_list = ["INSERT INTO %s (%s) VALUES " % ( \
                                       self.rdbt.pars['rdb_table_names']['ptf'], \
                                 ', '.join(self.rdbt.pars['ptf_rdb_columns_list']))]
            insert_list_obj_src_lookup = [ \
                          "INSERT INTO %s (src_id, obj_id, survey_id) VALUES " % ( \
                                      self.rdbt.pars['obj_srcid_lookup_tablename'])]

            # NOTE: there are some kludged / fudged values here:
            # NOTE: I also hard-code ra_error, dec_error:
            obj_epoch = {}
            obj_epoch['flags'] = 0 # PTF defaults
            obj_epoch['flags2'] = 0# PTF defaults
            obj_epoch['objc_type'] = 10 # PTF defaults
            obj_epoch['ra'] = ra
            obj_epoch['dec'] = dec
            obj_epoch['decl'] = dec
            obj_epoch['ra_rms'] = 0.2 #arcseconds? # TODO: get from xy_rms?
            obj_epoch['dec_rms'] = 0.2
            obj_epoch['obj_ids'] = [objid_candid]
            obj_epoch['src_id'] = 0
            obj_epoch['m'] = m # obsolete?
            obj_epoch['m_err'] = m_err # obsolete?
            obj_epoch['mag'] = m
            obj_epoch['mag_err'] = m_err
            obj_epoch['t'] = t # obsolete?
            obj_epoch['ujd'] = t
            obj_epoch['filt'] = 35
            obj_epoch['filts'] = [obj_epoch['filt']]
            obj_epoch['filter_num'] = obj_epoch['filt']
            obj_epoch['filter'] = obj_epoch['filt'] # 20090420 this is needed by ptf_master.py:insert_simple_ptf_object()
            obj_epoch['flux'] = 0.0 # KLUDGE: this is not contained in our existing vosource.xml
            obj_epoch['flux_err'] = 0.0 # KLUDGE: this is not contained in our existing vosource.xml
            obj_epoch['id'] = objid_candid
            obj_epoch['sub_id'] = 0
            obj_epoch['a_major_axis'] = 1 # obsolete?
            obj_epoch['b_minor_axis'] = 1 # obsolete?
            obj_epoch['a_image'] = 1
            obj_epoch['b_image'] = 1
            obj_epoch['mag_deep_ref'] = m + 5
            obj_epoch['mag_sub'] = m #TODO: this 'mag_sub' is currently the primary flux/mag which is used the the feature extractores.  So, either this should be a true magnitude of the candidate, or I need to change the ['mag_sub']->feature_extractor(flux) mapping.
            obj_epoch['nn_a'] = 1
            obj_epoch['nn_b'] = 1
            if ra >= 359.5:
                obj_epoch['nn_ra'] = ra - 0.5 # these are just dummy values
            else:
                obj_epoch['nn_ra'] = ra + 0.5
            if dec >= 89.5:
                obj_epoch['nn_dec'] = dec - 0.5 # these are just dummy values
            else:
                obj_epoch['nn_dec'] = dec + 0.5
            obj_epoch['nn_dist'] = math.sqrt(0.5)
            obj_epoch['nn_mag'] = m - 1.0
            obj_epoch['nn_sigma_mag'] = m_err
            obj_epoch['nn_star2galaxy_sep'] = 1.0
            obj_epoch['percent_incr'] = 0.1
            obj_epoch['sigma_mag_deep_ref'] = m_err / 10.0
            obj_epoch['sigma_mag_sub'] = m_err
            obj_epoch['surface_brightness'] = 1
            obj_epoch['ujd_proc_image'] = t

            # KLUDGE: The following assumes we have colums:
            # ingest_tools.pars['ptf_rdb_columns_list'] = ['id', 'sub_id', 'ra', 'decl', 'a_major_axis', 'b_minor_axis', 'mag_deep_ref', 'mag_sub', 'nn_a', 'nn_b', 'nn_ra', 'nn_dec', 'nn_dist', 'nn_mag', 'nn_sigma_mag', 'nn_star2galaxy_sep', 'percent_incr', 'sigma_mag_deep_ref', 'sigma_mag_sub', 'surface_brightness', 'ra_rms', 'dec_rms', 'ujd_proc_image', 'filter_num']

            obj_attrib_list = []
            for attrib_name in ingest_tools.pars['ptf_rdb_columns_list']:
                obj_attrib_list.append(obj_epoch[attrib_name])
            obj_attrib_tup = tuple(obj_attrib_list)
            #insert_str = "(%d, %d, %lf, %lf, %d, %d, %lf, %lf, %d, %d, %lf, %lf, %lf, %lf, %lf, %d, %lf, %lf, %lf, %d, %lf, %lf, %lf, %d), " % obj_attrib_tup
            insert_str = "(%d, %d, %lf, %lf, %d, %d, %lf, %lf, %lf, %lf, %lf, %lf, %lf, %d), " % obj_attrib_tup

            insert_list.append(insert_str)
            insert_list_obj_src_lookup.append("(0, %d, %d), " % (objid_candid,
                                           self.rdbt.pars['survey_id_dict']['ptf']))
            try:
                self.rdbt.cursor.execute(''.join(insert_list)[:-2])
                self.rdbt.cursor.execute(''.join(insert_list_obj_src_lookup)[:-2])
                break # gets us out of the while loop.
            except:
                objid_offset += 1

        return [obj_epoch]


    # To be obsolete:
    def form_tup_list_using_diff_source(self, diff_obj):
        """ Given a simple diff-source dictionary, form
        tup_list with it's object info.
        """
        #footprint_id is normally generated in insert_object_tuplist_into_rdb()
        #   - retrieved from footprint index server.
        #   - But in PTF case, footprint/limiting mags will be passed in by PTF
        tup_list = []
        tup_list.append([0,
                         diff_obj['t0'],
                         diff_obj['m0'],
                         diff_obj['m_err0'],
                         diff_obj['ra'],
                         diff_obj['dec'],
                         diff_obj['ra_rms'],
                         diff_obj['dec_rms']])
        tup_list.append([0,
                         diff_obj['t1'],
                         diff_obj['m1'],
                         diff_obj['m_err1'],
                         diff_obj['ra'],
                         diff_obj['dec'],
                         diff_obj['ra_rms'],
                         diff_obj['dec_rms']])
        return tup_list


    def ingest_diffobj(self, diff_obj, feat_db=None, do_logging=False, n_epochs_cut=7):
        """ Matches/generates source for diff-obj, gets features; adds to RDBs
        """
        src_list = self.xrsio.get_sources_for_radec_with_feature_extraction(\
                                              diff_obj['ra'], diff_obj['dec'],\
                                              0.000277778*5.0, write_ps=0, \
                                              only_sources_wo_features=0,\
                                              feat_db=feat_db, \
                                              skip_remote_sdss_retrieval=True,
                                              skip_check_sdss_objs=True,
                                              skip_check_ptel_objs=True,
                                              do_logging=do_logging,
                                              do_features_gen_insert=False)
        srcid_xml_tuple_list = []
        srcid_xml_tuple_with_features_list = []
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
        #20090504: added the two following conditions when there were no conditions prior:
        # This INSERT of features into RDB places high load on MySQL query-server and it isnt that critical:
        # This is KLUDGY since it assumes that there is just one source in the signals_list
        # NOTE: This should be: len(src_list) > 0 !!!
        if do_logging:
            print("before: [band_with_mags]['m'] > ...")
        n_epochs = 0
        if len(src_list) > 0:
            band_with_mags = src_list[0].d.get('ts',{}).keys()[0]
            for band,b_dict in src_list[0].d.get('ts',{}).iteritems():
                if 'm' in b_dict:
                    band_with_mags = band
                    break
            n_epochs = len(src_list[0].d.get('ts',{})[band_with_mags]['m'])
	    if 1:
                for source_obj in src_list:
                    src_id = source_obj.d['src_id']
                    srcid_xml_tuple_list.append((src_id, source_obj.xml_string))

                if do_logging:
                    print("before: (ptf_master) self.get_features_using_srcid_xml_tuple_list()")
                (signals_list, srcid_dict) = \
                              self.get_features_using_srcid_xml_tuple_list(\
                                                      srcid_xml_tuple_list, write_ps=0,
                                                      return_featd_xml_string=True) # 20090724 dstarr adds return_featd_xml_string=T
                if do_logging:
                    print("before: source_obj.add_features_to_xml_string(signals_list)")

                # This algorithm is taken from to ingest_tools.py::get_features_for_most_sampled_sources_client_loop():
                for source_obj in src_list:
                    source_obj.x_sdict = source_obj.d
                    source_obj.add_features_to_xml_string(signals_list)

                for source_obj in src_list:
                    src_id = source_obj.d['src_id']
                    srcid_xml_tuple_with_features_list.append(\
                                                       (src_id, source_obj.xml_string))
                ######
                # The following condition may be tweaked:
                #           >= 5   >= 15 > 15 > 5 >= 0 > 10 >= 10 > 7 >= 7  > 8 >= 8:
                if len(src_list[0].d.get('ts',{})[band_with_mags]['m']) >= n_epochs_cut:
                    self.srcdbt.update_featsgen_in_srcid_lookup_table(srcid_dict.keys())
                    self.feat_db.insert_srclist_features_into_rdb_tables(signals_list, \
                                                                       srcid_dict.keys())
		    # So, only source with >= 15 epochs will have features inserted into the feature RDB
                    ######
        if do_logging:
            print("after: [band_with_mags]['m'] > ...")
        return (srcid_xml_tuple_with_features_list, n_epochs)


    def exclude_diffobjs_using_constraints(self, diff_obj_list):
        """ Given a diff_object_list[], apply various constraints such
        as the minor-planet checker to exclude un-intersting difference objects.
        """
        os.chdir(os.path.expandvars("$HOME/src/TCP/Software/mp_checker")) # Needed for import
        is_first_iteration = True
        out_diff_obj_list = []
        for diff_obj in diff_obj_list:        
            ra_h_float = diff_obj['ra'] / 15.0
            ra_h = int(ra_h_float)
            ra_m_float = (ra_h_float - ra_h) * 60.0
            ra_m = int(ra_m_float)
            ra_s_float = (ra_m_float - ra_m) * 60.0
            if ra_s_float > 59.999999:
                ra_s_float = 59.999999 # deal with Python float error, .06"accr

            dec_h_float = diff_obj['dec']
            dec_h = int(dec_h_float)
            dec_m_float = (dec_h_float - dec_h) * 60.0
            dec_m = int(dec_m_float)
            dec_s_float = (dec_m_float - dec_m) * 60.0
            if dec_s_float > 59.999999:
                dec_s_float = 59.999999# deal with Python float error, .004"accr
            
            t_dtime_list = [mjd_2_datetime(diff_obj['dtime_reductn']),
                            mjd_2_datetime(diff_obj['dtime_observe'])]
            is_nearby_mp = False
            for t_dtime in t_dtime_list:
                sys.argv = ['blah',
                            str(ra_h),  str(ra_m),  str(ra_s_float), 
                            str(dec_h), str(dec_m), str(dec_s_float), 
                            str(t_dtime.year), 
                            str(t_dtime.month), 
                            str(t_dtime.day), 
                            str(t_dtime.hour), 
                            str(t_dtime.minute), 
                            str(t_dtime.second + (t_dtime.microsecond / 1e6)), 
                            str(int(self.pars['34mp_arcsec_thresh'])), # len of returned list of close minor planets
                            '10'] # radius in degrees of search region
                if is_first_iteration:
                    import PyMPChecker5
                    is_first_iteration = False
                else:
                    reload(PyMPChecker5)
                for mp_tup in PyMPChecker5.final_sorted_bodies:
                    nearest_mp_arcsec = ((360./(2*math.pi))*3600.*(mp_tup[1]))
                    nearest_mp_uncert_par = int(mp_tup[0][-1])
                    if nearest_mp_uncert_par <= 2:
                        if nearest_mp_arcsec <= self.pars['02mp_arcsec_thresh']:
                            is_nearby_mp = True
                            break # get out of final_sorted_bodies loop
                    elif nearest_mp_uncert_par <= 4:
                        if nearest_mp_arcsec <= self.pars['34mp_arcsec_thresh']:
                            is_nearby_mp = True
                            break # get out of final_sorted_bodies loop
                    ### NOTE: Currently I disable MP uncertainty param >= 5:
                    #elif nearest_mp_uncert_par == 5:
                    #    if nearest_mp_arcsec <= self.pars['5mp_arcsec_thresh']:
                    #        is_nearby_mp = True
                    #        break # get out of final_sorted_bodies loop
                if is_nearby_mp:
                    break # get out of t_dtime_list loop
            if not is_nearby_mp:
                out_diff_obj_list.append(diff_obj)
        return out_diff_obj_list


    # becoming obsolete:
    def retrieve_last_ptf_objects_from_rdb_table(self, n_last_rows=1):
        """ Retrieve the last (couple?) PTF objects from PTF RDB tables.
        """
        # TODO: PTF objects should be contained in a seperate database so migration PostgreSQL is easy.

        # NOTE: For now I retrieve ALL rows, but eventually get last rows (somehow):
        # TODO: this should connect to the postgresql server 
        ###if self.use_postgre_ptf:
        # This first condition is obsolete:
        if False:
            select_str = """SELECT %s FROM %s JOIN %s USING (id)""" % (\
                                   self.rdbt.pars['ptf_postgre_select_columns'],
                              self.rdbt.pars['ptf_postgre_candidate_tablename'],
                              self.rdbt.pars['ptf_postgre_sub_tablename'])
            self.rdbt.pg_cursor = self.rdbt.pg_conn.cursor()
            self.rdbt.pg_cursor.execute(select_str)
            rdb_rows = self.rdbt.pg_cursor.fetchall()
            self.rdbt.pg_cursor.close()
            self.rdbt.pg_conn.rollback()
        else:
            # 20090724: dstarr modifies select to have order by and limit
            #       (since this function is for testing purposes):
            #select_str = """SELECT %s FROM %s """ % (\
            select_str = """SELECT %s FROM %s where id=27760893""" % (\
                                      self.rdbt.pars['ptf_rdb_select_columns'],
                                      self.rdbt.pars['rdb_table_names']['ptf'])
            self.rdbt.cursor.execute(select_str)
            rdb_rows = self.rdbt.cursor.fetchall()

        obj_epoch_list = []
        
        for i in range(len(rdb_rows)-n_last_rows, len(rdb_rows)): 
            row = rdb_rows[i]
            obj_epoch = ingest_tools.extract_obj_epoch_from_ptf_query_row(row)
            obj_epoch_list.append(obj_epoch)
        return obj_epoch_list


class PTF_Poll_And_Spawn:
    """ Spawns PTF-polling thread
     - eventually, this queries remote DB for new object entries, retrieves.
     - quick-kludge: Just use hardcoded diff-objects
    """
    def __init__(self, pars):
        self.pars = pars
        #self.running_ingest_tasks = []


    def initialize_clients(self, mec, use_postgre_ptf=True):
        """ Instantiate ipython1 clients, import all module dependencies.
        """
        try:
            exec_str = """
import sys
import os
sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
import ptf_master
DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=%s)
""" % (str(use_postgre_ptf))
            print(mec.execute(exec_str))
        except:
            print("first try of mec.execute() failed!  Sleeping 60secs")
            time.sleep(60)
            exec_str = """
import sys
import os
sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
import ptf_master
DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=%s)
""" % (str(use_postgre_ptf))
            print(mec.execute(exec_str))


    def exclude_existing_diff_objs(self, tc, diff_obj_list):
        """ This queries that the diff_objects don'texist in the ptf object
        object database.  Only diff_objects which are unique are placed in the
        returned diff_obj_list[].

        NOTE: This method is really just for debugging, since I want to already
              assume that the given diff_objs are unique.

        NOTE: I can think of 2 SQL related solutions, implementing (1) for now:
           (1) For every diff_obj, SELECT whether either epoch in it exists
               in RDB.  If so return TRUE.  Then code doesn't add to return dict
           (2) (If there is a large number of diff_objs to check):
               Insert all diff_objs in question into a temporary-table
               Then SELECT a JOIN of all diff_objs which don't exist in mainRDB.
               Match selected diff_obj indexes with local diff_obj_list indexes
               and return the reduced list.
        """
        ### INITIALIZE Task-Client object:
        #from IPython.kernel import client
        #tc = client.TaskClient()

        out_diff_obj_list = []
        for diff_obj in diff_obj_list:
            exec_str = """
select_str = "SELECT obj_id from ptf_events_htm WHERE \
            (DIF_HTMCircle(%lf,%lf,%lf) AND \
                 ((t >= (%lf - 0.00001)) AND (t <= (%lf + 0.00001))) OR \
                  (t >= (%lf - 0.00001)) AND (t <= (%lf + 0.00001)))"
DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
results = DiffObjSourcePopulator.rdbt.cursor.fetchall()
already_exists = len(results) > 0
            """ % (diff_obj['ra'], diff_obj['dec'], 0.0166666,
                   diff_obj['t0'], diff_obj['t0'],
                   diff_obj['t1'], diff_obj['t1'])
            taskid = tc.run(client.StringTask(exec_str, pull="already_exists"))
            task_result = tc.get_task_result(taskid, block=True)
            if not task_result.results['already_exists']:
                out_diff_obj_list.append(diff_obj)
        return out_diff_obj_list


    def apply_constraints(self, tc, diff_obj_list):
        """ Given a diff_object_list[], apply various constraints such
        as the minor-planet checker to exclude un-intersting difference objects.
        """
        ### DEBUG:
        # for debugging, I can explicitly call this here, although eventually this should be put in each spawned thread.  Actually for right now I disable applying any constraints at all.
        #out_diff_obj_list = DiffObjSourcePopulator.exclude_diffobjs_using_constraints(diff_obj_list)
        return diff_obj_list
        ###

        ### INITIALIZE Task-Client object:
        #from IPython.kernel import client
        #tc = client.TaskClient()

        exec_str = "out_diff_obj_list = DiffObjSourcePopulator.exclude_diffobjs_using_constraints(diff_obj_list)"
        taskid = tc.run(client.StringTask(exec_str, \
                                    push={'diff_obj_list':diff_obj_list}, \
                                    pull="out_diff_obj_list"))
        results = tc.get_task_result(taskid, block=True)
        out_diff_obj_list = results.results["out_diff_obj_list"]
        return out_diff_obj_list


    def spawn_ingestion_tasks_using_diff_objs(self, tc, diff_obj_list, n_diffobjs_per_task=1):
        """ Given a list of dif_obj dictionaries, spawn source/feature tasks
        on ipython1 nodes.
        """
        #           >= 5   >= 15 > 15 > 5 >= 0 > 10 >= 10 > 7 >= 7  > 8 >= 8:
        n_diff_objs = len(diff_obj_list)
        for i in xrange(0,n_diff_objs, n_diffobjs_per_task):
            if i >= n_diff_objs:
                break
            diff_obj_sub_list = copy.deepcopy(diff_obj_list[i:i+n_diffobjs_per_task])# KLUDGE this copy may be overkill
            ####
            #### NOTE: for the (n_objs >= X)  cut, see classification_interface.py:generate_insert_classification_using_vosource_list()
	    #### NOTE: the (n_objs >= 3) ....???
            #### Also NOTE: ingest_diffobj( ... n_epochs_cut=7) is just used to determine whether to insert features into the feature RDB tables.  At present, the features are still calculated for all n_epoch cases (just not added to RDB depending on this cut)
            ####
            exec_str = """
for diff_obj in diff_obj_sub_list:
    (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db, n_epochs_cut=7)
    if n_objs >= 3:
        DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list, n_objs=n_objs)
"""
            # Rename / Enable for debug logging:
            exec_str_debug = """
tmp_stdout = sys.stdout
sys.stdout = open('/tmp/ptf_master.log', 'a')
print '#################################################################################'
for diff_obj in diff_obj_sub_list:
    print 'diff_obj:', diff_obj
    (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db, do_logging=True, n_epochs_cut=7)
    print "before: if n_objs >= 7"
    if n_objs >= 3:
        print "before: classify_and_insert_using_vosource_list"
        DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list, do_logging=True, n_objs=n_objs)
sys.stdout.close()
sys.stdout = tmp_stdout
"""
            taskid = tc.run(client.StringTask(exec_str, \
                                        push={'diff_obj_sub_list':diff_obj_sub_list}, retries=3))


    # NOTE: the above re-hack could add duplicate ptf-objects/epochs to RDB if the task
    #       fails and is restarted again.  This might hapen even with single diff_obj ingestion, anyhow.
    #       but it could happen in a worse way with the above funtion.  So if there is no speedup above,
    #       the below function might be better.
    # obsolete:
    def spawn_ingestion_tasks_using_diff_objs__old(self, tc, diff_obj_list):
        """ Given a list of dif_obj dictionaries, spawn source/feature tasks
        on ipython1 nodes.
        """
        i = 0
        for diff_obj in diff_obj_list:
            exec_str = """(srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj)
DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list)"""
            taskid = tc.run(client.StringTask(exec_str, \
                                        push={'diff_obj':diff_obj}, retries=10))
            i += 1



class PTF_Postgre_Server:
    """ Contains methods for making a connection to the LBL PostgreSQL
    database, as well as retrieve 'recent' diff_objects from the PGSQL server.

    KLUDGE: ptf_events table normally created in testsuite.py execution.
            But this generates the Mysql & shell commands (among other things):

import testsuite
import ingest_tools
testsuite.pars['ingest_tools_pars'].update(ingest_tools.pars)
tsso = testsuite.Test_Suite_Shared_Objects(testsuite.pars)
script_str_list = tsso.generate_table_creation_script_strs()

    """
    def __init__(self, pars=[], rdbt=None, \
                 test_data_substitute_pgsql_with_mysql=False):
        self.pars = pars # These pars contain ingest_tool.pars{} parameters
        self.rdbt = rdbt # This is an object which conatins MySQL RDB connectns

        if test_data_substitute_pgsql_with_mysql:
            return # TESTING CASE: skip the PostgreSQL server connection
        #"""

        # KLUDGE: only connect to PGSQL server on tranx:
        from socket import gethostname
        if gethostname() == 'tranx':
            try:
	        import psycopg2
                self.pg_conn = psycopg2.connect(\
                     "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                                    (self.pars['ptf_postgre_dbname'],\
                                     self.pars['ptf_postgre_user'],\
                                     self.pars['ptf_postgre_host'],\
                                     self.pars['ptf_postgre_password'],\
                                     self.pars['ptf_postgre_port']))
                self.pg_conn.set_isolation_level(2)
                #self.pg_cursor = self.pg_conn.cursor()
            except:
                print('EXCEPT! Unable to connect to PTF PostgreSQL server:', \
                                                       self.pars['ptf_postgre_host'])


            from . import apply_groupthink_filter
            # 20090630: this is becoming more obsolete:
            self.Classify_LBL_PTF_Using_GT = apply_groupthink_filter.Classify_LBL_PTF_Using_GroupThink(pg_cursor=None)


    def insert_pgsql_ptf_objs_into_mysql(self, id_classif_dict, index_offset=0, n_last_rows=1, \
                                         test_data_substitute_pgsql_with_mysql=False, \
                                         do_spatial_query=False, ra=None, dec=None):
        """This retrieves "recent" ptf diff_objects from LBL PGSQL server
        and inserts into a local Mysql object RDB, which is the queried
        for these "recent" objects and inserted into diff_obj_list format

        Returns: ptf_diff_obj_list
        """
        #import apply_groupthink_filter

        #rdb_rows = [(2,1,169.19735286,14.842781629,1.031,0.655,19.3739,0.093,2454892.9273,'g')]

        if test_data_substitute_pgsql_with_mysql:
            # THIS IS A TESTING CASE ONLY!  See: test.ptf_events__160k_20090326.  Remove ra_rms, dec_rms
            col_list = self.pars['ptf_rdb_columns_list'][:-4]
            col_list.extend(self.pars['ptf_rdb_columns_list'][-2:])
            select_str = "SELECT %s FROM object_test_db.ptf_events__160k_20090326 ORDER BY id LIMIT %d,%d" % (\
                    ', '.join(col_list), index_offset, n_last_rows)
            self.rdbt.cursor.execute(select_str)
            rdb_rows = self.rdbt.cursor.fetchall()
        else:
            if do_spatial_query:
                #select_str = """SELECT %s FROM %s JOIN %s ON (%s.sub_id = %s.id) JOIN %s ON (%s.id = %s.candidate_id) WHERE circle '((123, 45), 0.1)' @> point(ra,dec) AND %s.rb_model_id = %d""" % (\
                select_str = """SELECT %s FROM %s JOIN %s ON (%s.sub_id = %s.id) JOIN %s ON (%s.id = %s.candidate_id) WHERE ra between %lf and %lf and dec between %lf and %lf AND %s.rb_model_id = %d""" % (\
                        self.pars['ptf_postgre_select_columns'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_sub_tablename'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_sub_tablename'],
                        self.pars['ptf_postgre_realbogus_tablename'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_realbogus_tablename'],
                        ra - 0.01,
                        ra + 0.01,
                        dec - 0.01,
                        dec + 0.01,
                        self.pars['ptf_postgre_realbogus_tablename'],
                        self.pars['ptf_postgre_realbogus_current_model_id'],
                        )
            else:
                #select_str = """SELECT %s FROM %s JOIN %s ON (%s.sub_id = %s.id) LIMIT %d OFFSET %d""" % (\
                ### 20090428: dstarr comments out this conditional so that ptf_events.py will work on a (crashed) restart.  Maybe this should not be a permenant fix?:
                select_str = """SELECT %s FROM %s JOIN %s ON (%s.sub_id = %s.id) JOIN %s ON (%s.id = %s.candidate_id) WHERE %s.id >= %d AND %s.id <= %d AND %s.rb_model_id = %d""" % (\
                        self.pars['ptf_postgre_select_columns'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_sub_tablename'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_sub_tablename'],
                        self.pars['ptf_postgre_realbogus_tablename'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        self.pars['ptf_postgre_realbogus_tablename'],
                        self.pars['ptf_postgre_candidate_tablename'],
                        index_offset,
                        self.pars['ptf_postgre_candidate_tablename'],
                        n_last_rows + index_offset,
                        self.pars['ptf_postgre_realbogus_tablename'],
                        self.pars['ptf_postgre_realbogus_current_model_id'],
                        )
            do_pgsql_query = True
            while do_pgsql_query:
                try:
                    self.pg_cursor = self.pg_conn.cursor()
                    self.pg_cursor.execute(select_str)
                    rdb_rows = self.pg_cursor.fetchall()
                    self.pg_cursor.close()
                    self.pg_conn.rollback()
                    do_pgsql_query = False
                except:
                    import psycopg2 # KLUDGE
                    print('EXCEPT near L652: self.pg_cursor.execute().   Waiting 30 secs...')
                    time.sleep(30) # something happened to the LBL PostgreSQL server.  Wait a bit.
                    self.pg_conn = psycopg2.connect(\
                              "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                                (self.pars['ptf_postgre_dbname'],\
                                 self.pars['ptf_postgre_user'],\
                                 self.pars['ptf_postgre_host'],\
                                 self.pars['ptf_postgre_password'],\
                                 self.pars['ptf_postgre_port']))
                    self.pg_conn.set_isolation_level(2)
                    #self.pg_cursor = self.pg_conn.cursor()

        ### Here we use the rows,  get groupthink metrics:
        #id_classif_dict = self.Classify_LBL_PTF_Using_GT.\
        #                                   get_groupthink_classifications( \
        #                                       id_low=index_offset,
        #                                       id_high=n_last_rows + index_offset)
        #real_rows = self.Classify_LBL_PTF_Using_GT.\
        #                                   get_ptf_rows_with_good_classification( \
        #                                         rdb_rows,
        #                                         id_classif_dict=id_classif_dict,
        #                                         gt_perc_cut=0.25) #.15 shows a lot of spurious sources at te 19 mag and brighter range.  0.10 is useless (galaxies, etc...)

        realbogus_internal_colname_list = ['bogus', 'suspect', 'unclear', 'maybe', 'real', 'realbogus']
        realbogus_mysql_colname_list = ['bogus', 'suspect', 'unclear', 'maybe', 'realish', 'realbogus']

        insert_list = ["INSERT INTO %s (%s) VALUES " % ( \
                                   self.pars['rdb_table_names']['ptf'], \
                                  ', '.join(self.pars['ptf_rdb_columns_list']))]
        insert_list_obj_src_lookup = [\
                      "INSERT INTO %s (src_id, obj_id, survey_id) VALUES " % ( \
                                       self.pars['obj_srcid_lookup_tablename'])]
        #print "%s Num of classification reduced rows: %d of total: %d" % (str(datetime.datetime.utcnow()), len(real_rows), n_last_rows)
        mysql_style_rows = []
        obj_epoch_list = []
        #for row in rdb_rows:
        for row in rdb_rows:
            reduced_row_list = list(row[:-13])
            reduced_row_list.extend([1.0,1.0])# 20090314dstarr@gmail: Peter recommends hardcoding ra_rms & dec_rms to [0.1,0.1] #[0.2,0.2]
            reduced_row_list.extend(row[-13:])
            # # # # # # #
            # Also add the GroupThink/RealBogus metric to the end of the row list:
            #reduced_row_list.extend([id_classif_dict[row[0]][x] for x in realbogus_internal_colname_list])

            obj_epoch = ingest_tools.extract_obj_epoch_from_ptf_query_row(reduced_row_list)

            total_mag = calculate_ptf_mag.calculate_total_mag({'f_aper':obj_epoch['f_aper'],
                                                               'flux_aper':obj_epoch['flux_aper'],
                                                               'ub1_zp_ref':obj_epoch['ub1_zp_ref'],
                                                               'mag_ref':obj_epoch['mag_ref'],
                                                               'sub_zp':obj_epoch['sub_zp'][0],
                                                               'pos_sub':obj_epoch['pos_sub'][0]})
            if ((str(total_mag) == 'nan') or (str(total_mag) == 'inf')):
                ### NOTE: 20090831: This condition was used to cull ptf candidates assocuated with ptf09xxx sources, candidates which were bad subtractions (total_mag == NAN):
                #fp = open('/tmp/deleted_ptf', 'a')
                #fp.write(str(obj_epoch) + '\n')
                #fp.close()
                #self.rdbt.cursor.execute("DELETE from object_test_db.ptf_events where id=%d" % (obj_epoch['obj_ids'][0]))
                continue # skip this epoch since it's a bad LBL subtraction
            obj_epoch['m'] = total_mag
            obj_epoch_list.append(obj_epoch)
            reduced_row_list[6] = total_mag


            #mysql_style_rows.append(reduced_row_list)
            str_with_L = "(%s), " % (str(reduced_row_list)[1:-1])
            insert_list.append(str_with_L.replace('L',''))
            insert_list_obj_src_lookup.append("(0, %d, %d), " % (row[0],
                                            self.pars['survey_id_dict']['ptf']))
        on_duplicate_update_str = ' ON DUPLICATE KEY UPDATE '
        for col_name in self.pars['ptf_rdb_columns_list']:
            on_duplicate_update_str += "%s=VALUES(%s), " % (col_name, col_name)

        #if len(rdb_rows) > 0:
        if len(insert_list) > 1:
	    try:
	        self.rdbt.cursor.execute(''.join(insert_list)[:-2] + on_duplicate_update_str[:-2])
                ###### pre 20091018:
		#self.rdbt.cursor.execute(''.join(insert_list_obj_src_lookup)[:-2] + " ON DUPLICATE KEY UPDATE src_id=VALUES(src_id), obj_id=VALUES(obj_id), survey_id=VALUES(survey_id)")
		self.rdbt.cursor.execute(''.join(insert_list_obj_src_lookup)[:-2] + " ON DUPLICATE KEY UPDATE obj_id=VALUES(obj_id), survey_id=VALUES(survey_id)") # this "ON DUPLICATE KEY UPDATE" essentially does nothing, but allows the INSERT to occur when an object already exists in obj_srcid_lookup TABLE.
	    except:
	        print("RDB INSERT ERROR (from select into rdb):", select_str)
	        pass

        ### WAS: retrieve_last_ptf_objects_from_rdb_table()
        #select_str = """SELECT %s FROM %s """ % (\
        #                              self.rdbt.pars['ptf_rdb_select_columns'],
        #                              self.rdbt.pars['rdb_table_names']['ptf'])
        #self.rdbt.cursor.execute(select_str)
        #rdb_rows = self.rdbt.cursor.fetchall()

        #for row in mysql_style_rows:
        #    obj_epoch = ingest_tools.extract_obj_epoch_from_ptf_query_row(row)
        #    obj_epoch_list.append(obj_epoch)
        return obj_epoch_list


    def get_ptf_ids_not_ingested_due_to_error(self, id_classif_dict, ingest_id_high, \
                                              num_ids_to_attempt_ingest, \
                                              test_data_substitute_pgsql_with_mysql=False):
        """ Invoked only on the initial startup of ptf_master.py, this
        queries the obj_srcid_lookup table for obj_ids which are just
        0 < 1000 higher than current max_id, and determines whether
        no src_id > 0 exists for each obj_id.  If the src_id == 0 for
        an obj_id, then we return thes obj_id in a list so that these
        can be re-ingested (sourced, featured, classified).

        NOTE: this function was derived from insert_pgsql_ptf_objs_into_mysql()
        """
        if test_data_substitute_pgsql_with_mysql:
            return [] # skip case where: simulated ptf candidates using local mysql
        select_str = "SELECT obj_id FROM %s WHERE (obj_id > %d) and (obj_id < %d + %d) and (survey_id = %d) and (src_id = 0)" % ( \
                         self.pars['obj_srcid_lookup_tablename'],
                         ingest_id_high,
                         ingest_id_high,
                         num_ids_to_attempt_ingest,
                         self.pars['survey_id_dict']['ptf'])
        self.rdbt.cursor.execute(select_str)
        rdb_rows = self.rdbt.cursor.fetchall()
        objid_list = []
        for row in rdb_rows:
            objid_list.append(int(row[0]))

        realbogus_internal_colname_list = ['bogus', 'suspect', 'unclear', 'maybe', 'real', 'realbogus']

        # Now we get all info for these ptf candidates:
        obj_epoch_dict_list = []
        for obj_id in objid_list:
            select_str = """SELECT %s FROM %s JOIN %s ON (%s.sub_id = %s.id) JOIN %s ON (%s.id = %s.candidate_id) WHERE %s.id = %d AND %s.rb_model_id = %d""" % (\
                    self.pars['ptf_postgre_select_columns'],
                    self.pars['ptf_postgre_candidate_tablename'],
                    self.pars['ptf_postgre_sub_tablename'],
                    self.pars['ptf_postgre_candidate_tablename'],
                    self.pars['ptf_postgre_sub_tablename'],
                    self.pars['ptf_postgre_realbogus_tablename'],
                    self.pars['ptf_postgre_candidate_tablename'],
                    self.pars['ptf_postgre_realbogus_tablename'],
                    self.pars['ptf_postgre_candidate_tablename'],obj_id,
                    self.pars['ptf_postgre_realbogus_tablename'],
                    self.pars['ptf_postgre_realbogus_current_model_id'])
            self.pg_cursor = self.pg_conn.cursor()
            self.pg_cursor.execute(select_str)
            rdb_rows = self.pg_cursor.fetchall()
            self.pg_cursor.close()
            self.pg_conn.rollback()
            mysql_style_rows = []
            for row in rdb_rows:
                #reduced_row_list = list(row[:-2])
                reduced_row_list = list(row[:-12])
                reduced_row_list.extend([1.0,1.0])# 20090314dstarr@gmail: Peter recommends hardcoding ra_rms & dec_rms to [0.1,0.1] #[0.2,0.2]
                #reduced_row_list.extend(row[-2:])
                reduced_row_list.extend(row[-12:])
                # # # # # # #
                # Also add the GroupThink/RealBogus metric to the end of the row list:

                if row[0] in id_classif_dict:
                    print("  if: get_ptf_ids_not_ingested_due_to_error() row[0]=", row[0])
                    reduced_row_list.extend([id_classif_dict[row[0]][x] for x in realbogus_internal_colname_list])
                else:
                    # shouldn't get here more than only very occasionally...
                    print("else: get_ptf_ids_not_ingested_due_to_error() row[0]=", row[0])
                    id_classif_dict = self.Classify_LBL_PTF_Using_GT.\
                                           get_groupthink_classifications( \
                                               id_low=row[0],
                                               id_high=row[0])
                    reduced_row_list.extend([id_classif_dict[row[0]][x] for x in realbogus_internal_colname_list])

                mysql_style_rows.append(reduced_row_list)
                #str_with_L = "(%s), " % (str(reduced_row_list)[1:-1])
                #insert_list.append(str_with_L.replace('L',''))
                #insert_list_obj_src_lookup.append("(0, %d, %d), " % (row[0],
                #                                self.pars['survey_id_dict']['ptf']))

            for row in mysql_style_rows:
                try:
                    obj_epoch = ingest_tools.extract_obj_epoch_from_ptf_query_row(row)
                    obj_epoch_dict_list.append(obj_epoch)
                except:
                    print("Except in get_ptf_ids_not_ingested_due_to_error(): row=", row)
                    print(row)
                    raise
        return obj_epoch_dict_list



    # becoming obsolete:
    def add_most_recent_postgre_diffobj_to_mysql(self, index_offset=0):
        """ This retrieves "recent" ptf diff_objects from LBL PGSQL server
        and inserts into a local Mysql object RDB, which is the queried
        for these "recent" objects and inserted into diff_obj_list format

        Returns: ptf_diff_obj_list

        TODO: Eventually a method similar to this will poll the PTF PGSQL server
        and send new ptf_diff_obj_lists (or single element lists) to
        Ipython1 clients for source/feature/classification creation.

        TODO: So, eventually we will retrieve the last rows, which requires
              accounting of which object index number was already retrieved.
        """

        # TODO: remove self.use_postgre_ptf checks in ingest_tools.py
        #       since obsolete.

        # KLUDGE: the LIMIT 1 is for testing purposes:
        select_str = """SELECT %s FROM %s JOIN %s USING (id) LIMIT 1 OFFSET %d""" % (\
                self.pars['ptf_postgre_select_columns'],
                self.pars['ptf_postgre_candidate_tablename'],
                self.pars['ptf_postgre_sub_tablename'], index_offset)
        self.pg_cursor = self.pg_conn.cursor()
        self.pg_cursor.execute(select_str)
        rdb_rows = self.pg_cursor.fetchall()
        self.pg_cursor.close()
        self.pg_conn.rollback()

        # DEBUG:
        #if rdb_rows[0][6] == 0.0:
        #    raise "doh!"

        insert_list = ["INSERT INTO %s (%s) VALUES " % ( \
                                   self.pars['rdb_table_names']['ptf'], \
                                  ', '.join(self.pars['ptf_rdb_columns_list']))]

        insert_list_obj_src_lookup = [\
                      "INSERT INTO %s (src_id, obj_id, survey_id) VALUES " % ( \
                                       self.pars['obj_srcid_lookup_tablename'])]

        for row in rdb_rows:
            reduced_row_list = list(row[:-6])
            reduced_row_list.extend([1.0,1.0])# 20090314dstarr@gmail: Peter recommends hardcoding ra_rms & dec_rms to [0.1,0.1] #[0.2,0.2]
            reduced_row_list.extend(row[-6:])
            str_with_L = "(%s), " % (str(reduced_row_list)[1:-1])
            insert_list.append(str_with_L.replace('L',''))
            insert_list_obj_src_lookup.append("(0, %d, %d), " % (row[0],
                                            self.pars['survey_id_dict']['ptf']))
        self.rdbt.cursor.execute(''.join(insert_list)[:-2])
        self.rdbt.cursor.execute(''.join(insert_list_obj_src_lookup)[:-2])


def try_insert_classprob_into_top3(class_prob_list, class_name, prob):
    """ Given a class_name & associated probability, attempt to insert it
    into a list of the top 3 [(class_name,prob),..]
    """
    ### Dont need this since class_prob_list is filled with nulls:
    #if len(class_prob_list) == 0:
    #    class_prob_list.append((class_name,prob))
    #    return
    for i, (list_class_name,list_prob) in enumerate(class_prob_list):
        if prob > list_prob:
            class_prob_list.insert(i,(class_name,prob))
            if len(class_prob_list) > 3:
                class_prob_list.pop()
            return


def test_nonthread_nonipython1(use_postgre_ptf=True, \
                              case_simulate_ptf_stream_using_vosource=False, \
                              vosource_xml_fpath='',
                              case_poll_for_recent_postgre_table_entries=False,\
                              insert_row_into_iterative_class_probs=False):
    """ Use this non-ipython1 version for PDB step-through debugging.

    NOTE: A bit KLUDGEY since this just repeats PTF_Poll_And_Spawn methods.

    Case: using a vosource.xml, iterate over each epoch, inserting into
          mysql table and getting ptf_diff_obj_list, which is source processed
    Case: poll ptf postgresql table for "recent" entries, insert into mysql
          table and get ptf_obj_list, which is source processed
    Case: (obsolete) generate some random epoch and insert into ptf obj table
                     and get ptf_obj_list, which is source processed
    """
    DiffObjSourcePopulator = Diff_Obj_Source_Populator( \
                                                use_postgre_ptf=use_postgre_ptf)

    if case_simulate_ptf_stream_using_vosource:
        # NOTE: This case if for TESTING and simulating a science stream.

        # TODO: extract list [(ra,dec,m,me,t),..] from Vosource XML
        # Use : vosource_xml_fpath

        # ? where do I already parse using db_importer for parsing multiepochs
        #    - the TUTOR database insert code?
        """
        srcid_xml_tuple_list = [(srcid_num, vosource_xml_fpath)]
	(signals_list, srcid_dict) = \
                        ingest_tools.get_features_using_srcid_xml_tuple_list( \
                             srcid_xml_tuple_list, ps_fpath='',\
                             return_gendict=True, \
                             xmlstring_dict_tofill=None)
        """
        # NOTE: it seems that the above function creates features
        #       which I don't really want to be done yet.

        # NOTE: this module is imported in ingest_tools.py:
        signals_list = []
        gen = ingest_tools.generators_importers.from_xml(signals_list)
        gen.generate(xml_handle=vosource_xml_fpath)

        # KLUDGE: I need to do a test which weeds out vosource.xml which
        #      have non-magnitude data.  Some TUTOR sources are relative flux
        # TODO: Or, I could just convert these into magnitudes which are
        #           relative to some arbitrary reference flux.

        if (len(gen.sig.x_sdict['ts'].values()[0].get('m',[])) == 0):
            print("SKIPPING (due to len(gen.sig.x_sdict['ts'].values()[0].get('m',[])) == 0)")
            return
        elif (min(gen.sig.x_sdict['ts'].values()[0]['m']) < -26):
            # 20090211 dstarr comments out condition and modifies to above:
            # elif (min(gen.sig.x_sdict['ts'].values()[0]['m']) < 1):
            # Then probably TUTOR differential fluxes & not magnitudes,
            #  so we skip this source.
            print("SKIPPING (due to mag_min=%lf): %s\n\t max=%lf" % ( \
                                    min(gen.sig.x_sdict['ts'].values()[0]['m']),
                                    vosource_xml_fpath,
                                    max(gen.sig.x_sdict['ts'].values()[0]['m'])))
            return

        # gen.sig.x_sdict # This contains the source data structure
        # NOTE: features are still generated in the above function

        # Since we run this for TESTING, 
        #   We generate random ra,dec so that we don't overlap with
        #   existing sources/objects in the assumingly sparse test DB.
        ra = random.random() * 360.0
        dec = (random.random() * 60.0) - 10.0

        if insert_row_into_iterative_class_probs:
            import MySQLdb
            db = MySQLdb.connect(host=ingest_tools.pars['rdb_host_ip_4'], 
                                 user=ingest_tools.pars['rdb_user_4'],
                                 db=ingest_tools.pars['rdb_name_4'],
                                 port=ingest_tools.pars['rdb_port_4'])
            icp_cursor = db.cursor()
            insert_list = ['INSERT INTO iterative_class_probs (src_id, epoch_id, class_0, class_1, class_2, prob_0, prob_1, prob_2) VALUES ']
        
        #i_filt = gen.sig.x_sdict['ts'].keys()[0]
        # Choose the most sampled filter:
        tup_list = []
        for x_filt in gen.sig.x_sdict['ts'].keys():
            n_pts = len(gen.sig.x_sdict['ts'][x_filt].get('m',[]))
            tup_list.append((n_pts, x_filt))
        tup_list.sort(reverse=True)
        i_filt = tup_list[0][1]
        
        for i in xrange((len(gen.sig.x_sdict['ts'][i_filt]['m']))):
            gc.collect() # DEBUG : force garbage collection on each iteration.  generally gets 6-7k of collectable things (Python internal/accounting tuples, lists, dicts, some classes)
            # # # # # # # heap_obj.iso(<var>) # list the shortest paths to a variable (P24)
            # # # # # # # heap_obj.pb()  # create a TK GUI profile browser. (P24)
            # # # # # # #
            # # # # # # #
            # # # # # # #
            # # # # # # #
            # Debug stuff:
            #heap_obj = hpy()
            #print heap_obj.heap()
            #print heap_obj.heap().more
            #print heap_obj.heap().more.more
            #print heap_obj.heap().more.more.more
            #print heap_obj.heap().more.more.more.more
            #print heap_obj.heap().more.more.more.more.more
            #print heap_obj.heap().more.more.more.more.more.more
            #xxx = heap_obj.heap().more.__str__()
            # TODO: I would like to parse into a list of tups:
            #                    >Count<  >Kind...<  >Count * Size<
            #       So that I can compare which variables increase in
            #       number on each classification iteration.

            # TODO: see guppy/heapy document which discribes the process of
            #       tracking down memory leaks.

            # - I suspect "amara" may be duplicating on each iteration
            #     - if so, I should pass in a single amara instance?
            #     - or del()
            
            # # # # # # #
            # # # # # # #
            ptf_diff_obj_list =DiffObjSourcePopulator.insert_simple_ptf_object(\
                ra=gen.sig.x_sdict['ra'], # ra
                dec=gen.sig.x_sdict['dec'], #dec
                m=gen.sig.x_sdict['ts'][i_filt]['m'][i],
                m_err=gen.sig.x_sdict['ts'][i_filt]['m_err'][i],
                t=gen.sig.x_sdict['ts'][i_filt]['t'][i])
            for diff_obj in ptf_diff_obj_list:
                (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(\
                                                                       diff_obj, \
                                             feat_db=DiffObjSourcePopulator.feat_db)
                DiffObjSourcePopulator.class_interface.\
                                       classify_and_insert_using_vosource_list(\
                                       srcid_xml_tuple_list)
            # IF FLAGGED:
            #  - query for current classification and insert into table:
            #           iterative_class_probs 
            if insert_row_into_iterative_class_probs:
                src_id = gen.sig.x_sdict['src_id']
                # If single-lens, if >0.85,  then attempt adding prob.
                # any other plugin_name, insert if prob fits into top 3.
                class_prob_list = [('',0.),('',0.),('',0.)]
                for plugin_name,tup_list in DiffObjSourcePopulator.class_interface.\
                                     classname_classprob_classrank_list.iteritems():
                    if plugin_name == 'mlens3 MicroLens':
                        if tup_list[0][1] >= 0.85:
                            try_insert_classprob_into_top3(class_prob_list, tup_list[0][0], tup_list[0][1])
                    else:
                        if plugin_name == 'Dovi SN':
                            # I only attempt to add top 2 DoviSN:
                            tup_list = tup_list[:2]
                        for (class_name, class_prob, class_rank) in tup_list:
                            try_insert_classprob_into_top3(class_prob_list, class_name, class_prob)

                # Then use this list to to append to insert_list
                # so it contains [(name,prob), ...]
                insert_list.append("(%d, %d, '%s', '%s', '%s', %lf, %lf, %lf), " % \
                                   (src_id, i+1, class_prob_list[0][0], class_prob_list[1][0],
                                    class_prob_list[2][0], class_prob_list[0][1],
                                    class_prob_list[1][1], class_prob_list[2][1]))
                # # # # # # #
                # DEBUG / KLUDGE? :
                #DiffObjSourcePopulator. < del(the features modules/objects/classes) >
        if insert_row_into_iterative_class_probs:
            icp_cursor.execute(''.join(insert_list)[:-2])

        db.close() # KLUDGY placement of this. (this function is too long!)

    elif case_poll_for_recent_postgre_table_entries:
        #assert(use_postgre_ptf) # TODO: probably don't need this flag anymore
        PTFPostgreServer = PTF_Postgre_Server(pars=ingest_tools.pars, \
                                          rdbt=DiffObjSourcePopulator.rdbt)

        # Do some kind of triggerable while loop here:
        n_objs_to_insert = 10000000 # ==1 KLUDGE : since we are just retrieving the same row from the PTF PostgreSQL database below.
        for i in xrange(n_objs_to_insert):
            # This retrieves "recent" ptf diff_objects from LBL PGSQL server
            #  and inserts into a local Mysql object RDB, which is the queried
            #  for these "recent" objects and inserted into diff_obj_list format
            # # # # 20090724: dstarr comments out the next 5 lines:
            # #try:
            # #    PTFPostgreServer.add_most_recent_postgre_diffobj_to_mysql(index_offset=i)
            # #except:
            # #    print "EXCEPT!: Probably PTF row already exists in MySQL DB."
            # #    continue # 20090315: dstarr adds this continue
            ptf_diff_obj_list = DiffObjSourcePopulator.\
                    retrieve_last_ptf_objects_from_rdb_table(n_last_rows=1)
            # TODO: I would like to retrieve the "latest" ptf from PGSQL db
            #    and insert it into local tables, and then retrieve a diff_obje
            #    and pass it on like this method:
            for diff_obj in ptf_diff_obj_list:
                (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(\
                                                                       diff_obj, \
                                              feat_db=DiffObjSourcePopulator.feat_db)
                #try:
                DiffObjSourcePopulator.class_interface.\
                                       classify_and_insert_using_vosource_list(\
                                           srcid_xml_tuple_list)
                #except:
                #    print 'EXCEPT: srcid=%d : Already exists in Table: src_class_probs?' % (srcid_xml_tuple_list[0][0])


class Task_Master:
    """ This singleton controls the periodic restart of ipcontroller
    which is needed due to its inevitable per-task memory leak.  

    NOTE: There should be a table existing in 'object_test_db', which
    is used here for accounting of what lbl-ptf id ranges have been
    ingested into local MySQL tables & have been source-gen & classified.

    """
    def __init__(self, pars):
        self.pars = pars

    def initialize_classes(self):
        """ Initialize ipython controller and other classes
        """
        self.mec = client.MultiEngineClient()
        self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()

        self.PTFPollAndSpawn = PTF_Poll_And_Spawn(self.pars)
        self.PTFPollAndSpawn.initialize_clients(self.mec, use_postgre_ptf=True)

        self.DiffObjSourcePopulator = Diff_Obj_Source_Populator( \
                                                    use_postgre_ptf=True)
        self.PTFPostgreServer = PTF_Postgre_Server(pars=ingest_tools.pars, \
                                          rdbt=self.DiffObjSourcePopulator.rdbt,
                                          test_data_substitute_pgsql_with_mysql=\
                                      self.pars['test_data_substitute_pgsql_with_mysql'])


    def wait_for_nsched_to_decrease(self):
        """ Waiting Loop.  Periodically checks how many tasks are
        in task-scheduler queue.
        """
        num_scheduled = self.tc.queue_status()['scheduled']
        while (num_scheduled >= (self.pars['num_ids_to_attempt_ingest']/ \
                                float(self.pars['n_diffobjs_per_task']))):
           # We WAIT for num scheduled to get smaller
           time.sleep(5) # give LBL server a breath
           num_scheduled = self.tc.queue_status()['scheduled']
           print(self.tc.queue_status())
        if num_scheduled == 0:
            return True # this triggers tc/mec garbage collection


    def get_lbl_maxid(self):
        """ Query LBL PgSQL (or testing mysql emulated table)
        and return count(*)
        """
        if self.pars.get('test_data_substitute_pgsql_with_mysql',False):
            # THIS IS A TESTING CASE ONLY!  See: test.ptf_events__160k_20090326.  Remove ra_rms, dec_rms
            col_list = ingest_tools.pars['ptf_rdb_columns_list'][:-4]
            col_list.extend(ingest_tools.pars['ptf_rdb_columns_list'][-2:])
            select_str = "SELECT max(id) FROM object_test_db.ptf_events__160k_20090326"
            self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
            rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        else:
            select_str = """SELECT max(id) FROM %s """ % (\
                             ingest_tools.pars['ptf_postgre_candidate_tablename'])
            do_pgsql_query = True
            while do_pgsql_query:
                try:
                    self.PTFPostgreServer.pg_cursor = self.PTFPostgreServer.pg_conn.cursor()
                    self.PTFPostgreServer.pg_cursor.execute(select_str)
                    rdb_rows = self.PTFPostgreServer.pg_cursor.fetchall()
                    self.PTFPostgreServer.pg_cursor.close()
                    self.PTFPostgreServer.pg_conn.rollback()
                    do_pgsql_query = False
                except:
                    import psycopg2 # KLUDGE
                    print(datetime.datetime.utcnow(), 'EXCEPT near L1098: self.pg_cursor.execute().   Waiting 30 secs...')
                    time.sleep(30) # something happened to the LBL PostgreSQL server.  Wait a bit.
                    try:
                        self.pg_conn = psycopg2.connect(\
                              "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                                (ingest_tools.pars['ptf_postgre_dbname'],\
                                 ingest_tools.pars['ptf_postgre_user'],\
                                 ingest_tools.pars['ptf_postgre_host'],\
                                 ingest_tools.pars['ptf_postgre_password'],\
                                 ingest_tools.pars['ptf_postgre_port']))
                        self.pg_conn.set_isolation_level(2)
                        #self.PTFPostgreServer.pg_cursor = self.pg_conn.cursor()
                    except:
                        print("unable to do: conn = psycopg2.connect()")
                
        if len(rdb_rows) > 0:
            return int(rdb_rows[0][0])
        else:
            print("!!! NO rows in PTF LBL table!")
            return 0


    def get_n_rows_ingestacct(self):
        """ Get the number of rows in local object_test_db.lbl_ingest_acct
        TABLE.
        """
        select_str = "SELECT count(*) FROM %s" % ( \
                              self.pars['ingest_account_db.tablename'])
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0][0]
        else:
            print("!!! count(*) FAILed in get_n_rows_ingestacct()")
            return 0


    def get_max_rangeid_in_ingestacct(self):
        """ Get the max id_range in local object_test_db.lbl_ingest_acct
        TABLE.
        """
        select_str = "SELECT max(range_id) FROM %s" % ( \
                              self.pars['ingest_account_db.tablename'])
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0][0]
        else:
            print("!!! count(*) FAILed in get_n_rows_ingestacct()")
            return 0


        
    def get_ingestacct_matching_range(self, lbl_max_id):
        """ See if any rows in lbl_ingest_acct TABLE match
        the given id (from LBL ptf table).

        Return (range_id,id_low,id_high), (-1,0,0) otherwise.
        """
        #select_str = "SELECT range_id, id_low, id_high FROM %s WHERE id_low <= %d AND id_high >= %d" % (\
        select_str = "SELECT range_id, id_low, id_high FROM %s WHERE %d >= id_low AND %d <= id_high_initial" % (\
                              self.pars['ingest_account_db.tablename'],
                              lbl_max_id, lbl_max_id)
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0]
        else:
            return (-1, 0, 0)


    def get_max_id_from_ingestacct(self):
        """ See if any rows in lbl_ingest_acct TABLE match
        the given id (from LBL ptf table).

        RETURN: (id_high, id_low) for the row which has max(id_high)

        Return (range_id,id_low,id_high), (-1,0,0) otherwise.
        """
        select_str = "SELECT id_high, id_low, range_id FROM %s ORDER BY id_high DESC LIMIT 1" % ( \
                              self.pars['ingest_account_db.tablename'])
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0]
        else:
            # we get here from within get_lbl_id_range_for_ingestion()
            #   where there are no more rows in lbl_ingest_acct TABLE and
            #   we have already ingested all pgsql ptf candidates.
            # So, for the get_lbl_id_range_for_ingestion() case,
            #    we will time.sleep() when (None... ) is found.
            return (None, None, None)


    def get_lowest_max_id_from_ingestacct(self):
        """ See if any rows in lbl_ingest_acct TABLE match
        the given id (from LBL ptf table).

        RETURN: (id_high, id_low) for the row which has max(id_high)

        Derived from get_max_id_from_ingestacct()

        Return (range_id,id_low,id_high), (-1,0,0) otherwise.
        """
        select_str = "SELECT range_id, id_low, id_high FROM %s ORDER BY id_high ASC LIMIT 1" % ( \
                              self.pars['ingest_account_db.tablename'])
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0]
        else:
            # we get here from within get_lbl_id_range_for_ingestion()
            #   where there are no more rows in lbl_ingest_acct TABLE and
            #   we have already ingested all pgsql ptf candidates.
            # So, for the get_lbl_id_range_for_ingestion() case,
            #    we will time.sleep() when (None... ) is found.
            return (None,0,0)


    def get_specific_rangeid_from_ingestacct(self, ingest_specific_range_id):
        """ This special function allows the forcing to initally ingest a specific
        range_id, before proceeding to ingest from the lowest range_id.

        RETURN: (id_high, id_low) for the row which has max(id_high)

        Derived from get_max_id_from_ingestacct()

        Return (range_id,id_low,id_high), (-1,0,0) otherwise.
        """
        select_str = "SELECT range_id, id_low, id_high FROM %s WHERE range_id=%d" % ( \
                              self.pars['ingest_account_db.tablename'],
                              ingest_specific_range_id)
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            return rdb_rows[0]
        else:
            # we get here from within get_lbl_id_range_for_ingestion()
            #   where there are no more rows in lbl_ingest_acct TABLE and
            #   we have already ingested all pgsql ptf candidates.
            # So, for the get_lbl_id_range_for_ingestion() case,
            #    we will time.sleep() when (None... ) is found.
            return (None,0,0)


    def insert_row_into_ingestacct(self, range_id, id_low, id_high):
        """
        """
        insert_str = "INSERT INTO %s (range_id, id_low, id_high, id_high_initial, dtime_touch) VALUES (%d, %d, %d, %d, NOW())" % ( \
                              self.pars['ingest_account_db.tablename'],
                              range_id, id_low, id_high, id_high)
        self.DiffObjSourcePopulator.rdbt.cursor.execute(insert_str)


    def update_row_in_ingestacct(self, range_id, id_low, id_high):
        """
        """
        insert_str = "UPDATE %s SET id_low=%d, id_high=%d, dtime_touch=NOW() WHERE (range_id=%d)" % ( \
                              self.pars['ingest_account_db.tablename'],
                              id_low, id_high, range_id)
        self.DiffObjSourcePopulator.rdbt.cursor.execute(insert_str)


    def delete_row_in_ingestacct(self, range_id):
        """
        """
        insert_str = "DELETE FROM %s WHERE (range_id=%d)" % ( \
                              self.pars['ingest_account_db.tablename'],
                              range_id)
        self.DiffObjSourcePopulator.rdbt.cursor.execute(insert_str)


    def get_mysql_ptfevents_maxid(self):
        """ Get the max(id) from local mysql ptf_events TABLE.
        """
        select_str = "SELECT max(id) FROM %s.%s" % ( \
                              ingest_tools.pars['rdb_name_3'],
                              ingest_tools.pars['rdb_table_names']['ptf'])
        self.DiffObjSourcePopulator.rdbt.cursor.execute(select_str)
        rdb_rows = self.DiffObjSourcePopulator.rdbt.cursor.fetchall()
        if len(rdb_rows) > 0:
            if rdb_rows[0][0] is None:
                return 0
            return int(rdb_rows[0][0])
        else:
            return 0 # I think it is ok to get here the first time ever.

       
    def get_lbl_id_range_for_ingestion(self, n_rows_in_lbl_ingest_acct, max_rangeid):
        """ Query tables to determine the (range_id, id_low, id_high)
        of LBL ptf objects which should be source generated & classified.
        """
        lbl_max_id = self.get_lbl_maxid()
        mysql_max_id = self.get_mysql_ptfevents_maxid()
        if lbl_max_id > self.current_max_id_being_ingested: 
            (range_id,id_low,id_high) = self.get_ingestacct_matching_range(lbl_max_id)
            if range_id > 0: 
                return (range_id,id_low,id_high)
            else:
                #20090723 comment out:
                #range_id = n_rows_in_lbl_ingest_acct + 1
                range_id = int(max_rangeid) + 1
                id_high = lbl_max_id
                if n_rows_in_lbl_ingest_acct > 0:
                    id_low = self.get_max_id_from_ingestacct()[0] + 1
                else:
                    # Here there are no rows at all in lbl_ingest_accounting
                    #     meaning we believe all lbl_ptf rows have been ingested up
                    #     to local mysql ptf_event's max(id)
                    id_low = mysql_max_id + 1
                if id_low == id_high:
                    return (-1,0,0)
                self.insert_row_into_ingestacct(range_id, id_low, id_high)
                return (range_id,id_low,id_high)
        else:
            # ??? Here we need to whittle from an id_range in the ll_ingest_acct TABLE
            # # #here (lbl_max_id <= self.current_max_id_being_ingested) and we have a buggy case when there are no rows in lbl_ingest_acct table.
            (id_high, id_low, range_id) = self.get_max_id_from_ingestacct()
            return (range_id,id_low,id_high)
            # id_low should just be the bottom of the id_range since this will be 1000 truncated later.


    # obsolete:
    def get_lbl_id_range_for_ingestion_old(self, n_rows_in_lbl_ingest_acct):
        """ Query tables to determine the (range_id, id_low, id_high)
        of LBL ptf objects which should be source generated & classified.
        """
        lbl_max_id = self.get_lbl_maxid()
        mysql_max_id = self.get_mysql_ptfevents_maxid()
        #if lbl_max_id > self.current_max_id_being_ingested: 
        #     (then we can see if there are any existing i_range which matches this id)
        #     (  if not, then we generate a new range_id, and ranges)
        
        # else:
        #     ( then we are currently ingesting a range which contains this lbl_max_id)
        #     ( so, we should queue the next 1000 from lbl_ingest_accounting TABLE
        # TODO: I want to see if any existing i_range matches lbl_max
        (range_id,id_low,id_high) = self.get_ingestacct_matching_range(lbl_max_id)
        if range_id > 0: 
            return (range_id,id_low,id_high)
        else:
            new_range_id = n_rows_in_lbl_ingest_acct + 1
            id_high = lbl_max_id
            if n_rows_in_lbl_ingest_acct > 0:
                id_low = self.get_max_id_from_ingestacct() + 1
            else:
                # Here there are no rows at all in lbl_ingest_accounting
                #     meaning we believe all lbl_ptf rows have been ingested up
                #     to local mysql ptf_event's max(id)
                id_low = mysql_max_id + 1
            if id_low == id_high:
                return (-1,0,0)

            self.insert_row_into_ingestacct(new_range_id, id_low, id_high)
            return (new_range_id,id_low,id_high)


    def ingest_some_lbl_epochs(self, ingest_greatest_ids=True, ingest_specific_range_id=None):
        """ Query LBL Postgresql server, get epochs we haven't ingested yet,
        add them to local mysql database, form diff_objs, task of source tasks
        to ipcontroller for eventual ipengine source identification and
        classification.
        """
        #is_really_first_time = True
        is_first_time = self.wait_for_nsched_to_decrease()
        if is_first_time:
            self.tc.clear() # This supposedly clears the list of finished task objects in the task-client
            self.mec.flush() # This doesnt seem to do much in our system.
            #print '>>> TaskClient CLEARED'
        
        hasbeen_ingested_ptf_obj_list = []
        n_rows_in_lbl_ingest_acct = 1 # KLUDGE: just get into loop first time
        while ((len(hasbeen_ingested_ptf_obj_list) < \
                          self.pars['num_ids_to_attempt_ingest']) and
                 (n_rows_in_lbl_ingest_acct > 0)):
            n_rows_in_lbl_ingest_acct = self.get_n_rows_ingestacct()
            max_rangeid = self.get_max_rangeid_in_ingestacct()
            n_to_ingest_this_iteration = self.pars['num_ids_to_attempt_ingest'] - \
                                                     len(hasbeen_ingested_ptf_obj_list)
            # # # # NOTE: have a version of this function, which gets the lowest id range when flagged:
            #         - this should be easy, just return the bottom-most range.


            if (ingest_specific_range_id != None):
                (range_id,id_low,id_high) = self.get_specific_rangeid_from_ingestacct(ingest_specific_range_id)
                ingest_specific_range_id = range_id
            # NOTE: if the specific_range_id no longer exists in DB,
            #       then range_id returned above is None, and below is done:
            if (ingest_specific_range_id is None):
                if ingest_greatest_ids:
                    (range_id,id_low,id_high) = self.get_lbl_id_range_for_ingestion(n_rows_in_lbl_ingest_acct, max_rangeid)
                else:
                    (range_id,id_low,id_high) = self.get_lowest_max_id_from_ingestacct()

            #is_really_first_time = False

            if range_id is None:
                # This is when everything has been done in lbl_ingest_acct table,
                #    and there are no new rows in the LBL pgsql ptf candidates table.
                print("Nothing in lbl_ingest_acct, PTF ingestion up-to-date.  Sleep(60)...")
                time.sleep(60)
                continue # go back to the top

            if (id_high - id_low) > n_to_ingest_this_iteration:
                #NOTE: have a case when we are ingesting the lowest ids first
                if ingest_greatest_ids:
                    ingest_id_high = id_high
                    ingest_id_low = id_high - n_to_ingest_this_iteration
                    self.update_row_in_ingestacct(range_id, id_low, ingest_id_low -1)
                else:
                    ingest_id_high = id_low + n_to_ingest_this_iteration
                    ingest_id_low = id_low
                    self.update_row_in_ingestacct(range_id, ingest_id_high+1, id_high)
            elif (id_high - id_low) > 0:
                # We will ingest all of these in a sec, so remove from acct table
                ingest_id_low = id_low
                ingest_id_high = id_high 
                self.delete_row_in_ingestacct(range_id)
            elif id_high > 0:
                # Unlikely, but we just insert a single row (the max(id) from lbl_ptf)
                ingest_id_low = id_high
                ingest_id_high = id_high
            else:
                print("Here max(id) from lbl_ptf == 0, not considered likely.  Probably something else.")
                raise

            # TODO: if this is the first time through, I could check whether:
            #   - there are src_id==0 epochs in obj_srcid_lookup for ids within id_high and id_high+1000
            #       - which means they were not correctly source-found and classified.
            #   - I could then add these obj_id to the ptf_diff_obj_list.

            print(range_id,id_low,id_high, ingest_id_low, ingest_id_high - ingest_id_low)

            #id_classif_dict = self.PTFPostgreServer.Classify_LBL_PTF_Using_GT.\
            #                               get_groupthink_classifications( \
            #                                   id_low=ingest_id_low,
            #                                   id_high=(ingest_id_high - ingest_id_low) + ingest_id_low)
            id_classif_dict = {}

            ptf_diff_obj_list = self.PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql( \
                                                  id_classif_dict,
                                                  index_offset=ingest_id_low,
                                                  n_last_rows=(ingest_id_high - ingest_id_low), \
                                                  test_data_substitute_pgsql_with_mysql= \
                                                  self.pars['test_data_substitute_pgsql_with_mysql'])
            if is_first_time:
                # # # # # # # #
                ##### 20090623: dstarr disables this, since we now have object epochs which are not associated with any sources (thus have src_id=0):
                ##### This means that now we will potentially not identify sources for some LBL retrieved epochs if ptf_master.py is abnormally stopped and restarted.
                #missed_objs_list = self.PTFPostgreServer.get_ptf_ids_not_ingested_due_to_error( \
                #                             id_classif_dict, \
                #                             ingest_id_high, self.pars['num_ids_to_attempt_ingest'], \
                #                             test_data_substitute_pgsql_with_mysql= \
                #                                   self.pars['test_data_substitute_pgsql_with_mysql'])
                #ptf_diff_obj_list.extend(missed_objs_list)
                is_first_time = False

            ptf_diff_obj_list = self.PTFPollAndSpawn.apply_constraints(self.tc, ptf_diff_obj_list)
        
            self.PTFPollAndSpawn.spawn_ingestion_tasks_using_diff_objs(self.tc, \
                                                              ptf_diff_obj_list, \
                                                    n_diffobjs_per_task=self.pars['n_diffobjs_per_task'])

            hasbeen_ingested_ptf_obj_list.extend(ptf_diff_obj_list)
            n_rows_in_lbl_ingest_acct = self.get_n_rows_ingestacct()
            if ingest_id_high > self.current_max_id_being_ingested:
                self.current_max_id_being_ingested = ingest_id_high

        return len(hasbeen_ingested_ptf_obj_list)


    def main(self):
        """ Task_Master main function.
        """
        global signal_occurred

        self.initialize_classes()
        self.current_max_id_being_ingested = -1 # this variable is KLUDGY
        while True:
            # Stay in this loop until SIGTERM 
            total_n_diff_obj_ingested = 0
            while ((signal_occurred != 'SIGTERM') and
                   (signal_occurred != 'SIGINT') and
                   (total_n_diff_obj_ingested < self.pars['n_tasks_before_ipy_restart'])):

                #num_diffobjs_ingested = self.ingest_some_lbl_epochs(ingest_greatest_ids=True)
                # For below to work, you can custom edit object_test_db.lbl_ingest_acct TABLE
                #   to have:  (when interested in ingesting the 130 range):
                #| range_id | id_low   | id_high  | id_high_initial | dtime_touch         |
                #+----------+----------+----------+-----------------+---------------------+
                #|      128 | 13829677 | 13836141 |        13839144 | 2009-07-07 16:35:59 | 
                #|      129 | 14286232 | 27000000 |        27000001 | 2009-07-24 11:03:43 |
                #|      130 | 27000001 | 27736685 |        27741686 | 2009-07-24 11:01:16 | 
                num_diffobjs_ingested = self.ingest_some_lbl_epochs(ingest_greatest_ids=True)#False, ingest_specific_range_id=2) #20090723 dstarr adds the last keyword, expecting it to be removed  quickly.
                total_n_diff_obj_ingested +=  num_diffobjs_ingested

            # TODO: wait for (tc.queue_status()['scheduled'] == 0)
            if ((signal_occurred == 'SIGTERM') or
                (signal_occurred == 'SIGINT')):
                print('Recieved: %s, shutting down...' % (signal_occurred))
                # now all tasks have finished, so we can exit.
                return
            else:
                print("TODO: restart ipengines, ipcontroller. using ipython_cluster_setup.py methods")
                num_scheduled = self.tc.queue_status()['scheduled']
                while (num_scheduled > 0):
                   # We WAIT for num scheduled to get smaller
                   time.sleep(5) # give LBL server a breath
                   num_scheduled = self.tc.queue_status()['scheduled']
                   print('WAITING for 0:', self.tc.queue_status())

                os.system('/home/pteluser/src/TCP/Software/ingest_tools/ipython_cluster_setup.py')
                #time.sleep(180)
                try:
                    self.mec = client.MultiEngineClient()
                    self.tc = client.TaskClient()
                except:
                    self.mec = client.MultiEngineClient()
                    self.tc = client.TaskClient()                    
                time.sleep(70) # We give some time for ipengines to initialize (sgn02 requires > 30secs)
                self.PTFPollAndSpawn.initialize_clients(self.mec, use_postgre_ptf=True)
                #time.sleep(60)


if __name__ == '__main__':

    ##### MODE: FOR NON-PARALLEL PDB DEBUGGING:
    if 0:
        # Connect to LBL PTF database for new objects
        test_nonthread_nonipython1(use_postgre_ptf=True, \
                               case_simulate_ptf_stream_using_vosource=False, 
                               vosource_xml_fpath='',
                               case_poll_for_recent_postgre_table_entries=True)
        sys.exit()

    #else:
    #    # Simulate PTF stream using (TUTOR vosource xml filepath):
    #    #13#vosource_xml_fpath =os.path.expandvars('$TCP_DIR/Data/mira_HIP_100599.xml')
    #    vosource_xml_fpath = os.path.expandvars('$TCP_DIR/Data/rr_lyrae_fundemental_mode_HIP_90053.xml')
    #    test_nonthread_nonipython1(use_postgre_ptf=False, \
    #                           case_simulate_ptf_stream_using_vosource=True, 
    #                           vosource_xml_fpath=vosource_xml_fpath,
    #                           case_poll_for_recent_postgre_table_entries=False)
    #sys.exit()

    master_pars = {
        'n_diffobjs_per_task':5, #5 #first10M: 1# number of epochs/diff_objs per ipengine task.  Since ipython tasks FAIL occasionally, so 1 is ideal to reduce the number of duplicates/missed epochs in local MySQL tables.
        'num_ids_to_attempt_ingest':1000,# 6000,# 2000 #first10M: 1000 #20000 1000 # Add this many epochs to task-queue before waiting for adding again.
        'n_tasks_before_ipy_restart':300000, #400000#first10M: 100000 # 500000 50000
        'test_data_substitute_pgsql_with_mysql':False, # For TESTING only (using non LBL/PGSQL server):
        'ingest_account_db.tablename':'object_test_db.lbl_ingest_acct',
        }

    signal.signal(signal.SIGTERM, sig_TERM_handler) # signal 'kill/term' catcher
    signal.signal(signal.SIGINT, sig_INT_handler)
    from IPython.kernel import client

    TaskMaster = Task_Master(master_pars)
    TaskMaster.main()
    print("ALL DONE!")
    time.sleep(5) # is this needed?
    sys.exit()


    #######################
    # OBSOLETE:
    #######################

    #start_ptf_obj_id = 0
    #n_diffobjs_per_task = 1 # By having several objs be crunched per ipengine task node, some thuroughput is saved, as well as this reduces the mysterious caching on ipcontroller.
    #num_ids_to_attempt_ingest = 1000 # 10
    n_objs_to_insert = 3290000 # ==1 KLUDGE : since we are just retrieving the same row from the PTF PostgreSQL database below.
    # # # # # #
    # For TESTING only (using non LBL/PGSQL server):
    #test_data_substitute_pgsql_with_mysql = True
    n_objs_to_insert = 170000 # number of rows in test table
    # # # # # #

    for i in xrange(0,n_objs_to_insert,num_ids_to_attempt_ingest):
        # TODO: do a sleep(), or better: wait for ipython1 list to drop below ~20 queued tasks.
        
        # TODO: eventually, on ptf_master.py startup, retrive largest obj_id from mysql ptf DB, and
        #       start with index_offset = max_obj_id + 1
        # COMBINE THESE FUNCTIONS & RETURN ptf_diff_obj_list
        #PTFPostgreServer.add_most_recent_postgre_diffobj_to_mysql(index_offset=start_ptf_obj_id)
        #ptf_diff_obj_list = DiffObjSourcePopulator.\
        #                        retrieve_last_ptf_objects_from_rdb_table(n_last_rows=1)
        ptf_diff_obj_list = PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql(index_offset=i,
                                                  n_last_rows=num_ids_to_attempt_ingest,
                                                  test_data_substitute_pgsql_with_mysql=\
                                                       test_data_substitute_pgsql_with_mysql)

        # TODO: this following task could actually be done (parallel) on each spawned task client:
        ptf_diff_obj_list = PTFPollAndSpawn.apply_constraints(tc, ptf_diff_obj_list)
        
        PTFPollAndSpawn.spawn_ingestion_tasks_using_diff_objs(tc, ptf_diff_obj_list, \
                                                              n_diffobjs_per_task=n_diffobjs_per_task)

        num_scheduled = tc.queue_status()['scheduled']
        
        while num_scheduled >= (num_ids_to_attempt_ingest/float(n_diffobjs_per_task)):
            print("num_scheduled=%d,  num_ids_to_attempt_ingest=%d" % (num_scheduled,num_ids_to_attempt_ingest))
            print("i=%d, n_objs_to_insert=%d, ,num_ids_to_attempt_ingest=%d" % (i,n_objs_to_insert,num_ids_to_attempt_ingest))
            time.sleep(5) # give LBL server a breath
            num_scheduled = tc.queue_status()['scheduled']
            print(tc.queue_status())
        if i != 0:
            # I feel weird doing this on the first iteration...
            tc.clear()  # This periodically clears the list of finished task objects in the task-client
            mec.flush()
            print('######################################################')
            print('               TaskClient   CLEARED')
            print('######################################################')
    # TODO (want): PTFPollAndSpawn.<check for timed-out tasks>
    #   - This would then connect back to tasks / barrier tasks
    #   - This would require tasks being stored in a PTF_Poll_And_Spawn property


    # TODO: test that adding data to a source (later time data) will:
    #   - correctly add to existing source, be included as objects
    #   - source features will be re-generated.
    #   - maybe add these tests to testsuite.py


    # TODO: rather than weed out all MP matches, it might be useful to also return a MP-matched list, which we can then plot/analyze.

    # TODO: Test a ra,dec,t which coincides with a Minor-planet, so I can see this source excluded.

    #######################
    #######################
    # Old IPython case:
    PTFPollAndSpawn.initialize_clients(use_postgre_ptf=True)
    # Generally, we should assume diff_objs are unique and haven't been
    #   submitted yet.  But, for debugging I'd like to assert these aren't dups:
    ptf_diff_obj_list = PTFPollAndSpawn.\
                                   exclude_existing_diff_objs(ptf_diff_obj_list)

    ptf_diff_obj_list = PTFPollAndSpawn.apply_constraints(ptf_diff_obj_list)

    PTFPollAndSpawn.spawn_ingestion_tasks_using_diff_objs(ptf_diff_obj_list)

    # TODO (want): PTFPollAndSpawn.<check for timed-out tasks>
    #   - This would then connect back to tasks / barrier tasks
    #   - This would require tasks being stored in a PTF_Poll_And_Spawn property


    # TODO: test that adding data to a source (later time data) will:
    #   - correctly add to existing source, be included as objects
    #   - source features will be re-generated.
    #   - maybe add these tests to testsuite.py


    # TODO: rather than weed out all MP matches, it might be useful to also return a MP-matched list, which we can then plot/analyze.


    # TODO: Test a ra,dec,t which coincides with a Minor-planet, so I can see this source excluded.

