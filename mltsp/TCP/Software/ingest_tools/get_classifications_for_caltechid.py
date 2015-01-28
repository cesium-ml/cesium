#!/usr/bin/env python 
""" Given a PTF-ID, generate Josh RB & TCP classifications, summarize results.

TODO:
 - get infor (candidate.id) for a ptf-id
 - get Josh classifier results for candidate.id


 # TODO: need tcp_classif{} to contain final science_class and probability
 #       so that ['prob'] can be used in variale determination.

TODO: Table displays:
  - <a href> to TCP srcid URL
  - <a href> to Caltech candidate URL
  - realbogus 5-barchart
  - JDAC piechart
  - (not critical) subtraction thumbnail?

TODO: condense classifiers into 4 classes:

if is_rock_epoch_count > 0
       return (is_rock)

if is_variable and 
   n_epochs  > 8
       ==> determine most probable science_class
       ==> return is_variable, science_class, probability
    ??? is_variable :: ?
      - variable probability > 0.8
      - realbogus_ratio >= 0.8
      - n_epochs > 8

if <Josh transient cuts>
       return (is_transient)
     - nearby_rb_is_interest_count > 80%

if is_junk
       return (is_junk)
   - is_junk :: ?
   - nearby_rb_is_interest_count < 10%


return (is_undetermined)

"""
import sys, os
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

from optparse import OptionParser

def parse_options():
    """ Deal with parsing command line options & --help.  Return options object.
    """
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-a","--do_general_classifier",
                      dest="do_general_classifier", \
                      action="store_true", default=False, \
                      help="Do general classification, JDAC, weka classifications, pympchecker...")
    parser.add_option("-b","--do_varstar_j48_weka_classifications",
                      dest="do_varstar_j48_weka_classifications", \
                      action="store_true", default=False, \
                      help="Do j48 weka classifications of PTF VarStar sources.")
    parser.add_option("-c","--do_ipython_parallel",
                      dest="do_ipython_parallel", \
                      action="store_true", default=False, \
                      help="Use Ipython Parallel nodes with weka classifications of PTF VarStar sources.")

    (options, args) = parser.parse_args()
    print "For help use flag:  --help" # KLUDGE since always: len(args) == 0
    return options


class LBLDB:
    """  Everythoing related to LBL database.
    """

    def get_lbl_candidate_info_for_radec(self, ra=None, dec=None):
        """
        """
        pass


class CaltechDB:
    """ Everything related to connections with caltech pgsql db
    """

    def get_ptf_candid_info___non_caltech_db_hack(self, cand_shortname=""):
        """ Given a candidate shortname, get candidate ra,dec, other info.

        NOTE: this version just retrieves from local mysql database while caltech is down.

        """
        import MySQLdb
        self.mysql_db = MySQLdb.connect(host="192.168.1.25", user="pteluser", db="object_test_db")
        self.mysql_cursor = self.mysql_db.cursor()

        #(a lbl objid), ptf_shortname, ra, dec, <mag> <type <scanner> <type2> <class> <isspec> <rundate>

        # 
        
        select_str = 'SELECT object_test_db.obj_srcid_lookup.obj_id, caltech_candidate_shortname, tcp_source_id, source_test_db.srcid_lookup.ra, source_test_db.srcid_lookup.decl FROM source_test_db.caltech_classif_summary JOIN source_test_db.srcid_lookup ON (source_test_db.caltech_classif_summary.tcp_source_id=source_test_db.srcid_lookup.src_id) JOIN object_test_db.obj_srcid_lookup ON (source_test_db.srcid_lookup.src_id=object_test_db.obj_srcid_lookup.src_id AND object_test_db.obj_srcid_lookup.survey_id=3) WHERE caltech_candidate_shortname="%s" LIMIT 1' % (cand_shortname)

        self.mysql_cursor.execute(select_str)
        results = self.mysql_cursor.fetchall()
        if len(results) < 1:
            return {}
        out_dict = {'srcid':results[0][2],
                    'id':results[0][0],
                    'shortname':results[0][1],
                    'ra':results[0][3],
                    'dec':results[0][4],
                    'mag':'',
                    'type':'',
                    'scanner':'',
                    'type2':'',
                    'class':'',
                    'isspectra':'',
                    'rundate':''}
        return out_dict


    def get_ptf_candid_info(self, cand_shortname=""):
        """ Given a candidate shortname, get candidate ra,dec, other info.
        """
        try:
            import psycopg2
        except:
            print "UNABLE to import psycopg2"
            return {}
        conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        pg_cursor = conn.cursor()
        column_list = ['id', 'shortname', 'ra', 'dec', 'mag', 'type', 'scanner', 'type2', 'class', 'isspectra', 'rundate']
        column_str = ', '.join(column_list)
        select_str = "SELECT %s FROM saved_cands WHERE shortname='%s'" % (column_str, cand_shortname)

        pg_cursor.execute(select_str)
        rows = pg_cursor.fetchall()
        conn.close()

        out_dict = {}
        if len(rows) > 0:
            for i,val in enumerate(rows[0]):
                out_dict[column_list[i]] = val

        return out_dict

    def get_caltech_shortnames(self, conditional_str='shortname > 0'):
        """
        """
        try:
            import psycopg2
        except:
            print "UNABLE to import psycopg2"
            return []

        conn = psycopg2.connect("dbname='ptfcands' user='tcp' host='navtara.caltech.edu' password='classify'");
        pg_cursor = conn.cursor()
        column_list = ['id', 'shortname', 'ra', 'dec', 'mag', 'type', 'scanner', 'type2', 'class', 'isspectra', 'rundate']
        column_str = ', '.join(column_list)
        select_str = "SELECT shortname FROM saved_cands WHERE %s" % (conditional_str)

        pg_cursor.execute(select_str)
        rows = pg_cursor.fetchall()
        conn.close()

        shortname_list = []
        out_dict = {}
        if len(rows) > 0:
            for val in rows:
                shortname_list.append(val[0])
        return shortname_list


class GetClassificationsForPtfid:
    """ Main Class
    """
    def __init__(self, rdbt=None, PTFPostgreServer=None, DiffObjSourcePopulator=None):
        self.rdbt=rdbt
        self.PTFPostgreServer=PTFPostgreServer
        self.DiffObjSourcePopulator=DiffObjSourcePopulator
        self.ordered_colname_list = []
        self.cand_lblq= cand.LBLq()
        self.cond_class_dict = {}
        self.pars = {'overall_cuts':{ \
                        'variable_n_epoch_cut':8,   # (non?)periodic_variable:  n_epochs >= cut
                        'realbogus_ratio_cut':0.73, # (non?)periodic_variable:  rb_ratio >= cut
                        'realbogus_cut':0.165,      # if (epoch rb > cut), then added to rb_ratio
                        'general_class_weight_cut':0.3,  # OBSOLETE?
                        'rbscale_combined_avg_cut':4.0, # like sqrt() below but for source epochs' average
                        'transient_combined_metric_cut':4.0, # count +=1:    sqrt(rb_scale_simp * rb_scale) >= cut
                        'transient_interesting_count_cut': 1, # transient:   count >= cut
                        'periodic_var_prob_cut':0.452, # periodic_variable:  prob >= cut
                        'rb_slope_cut':-3.5, # rb_slope >= cut (Josh says >= ~-3) # aka in cand.py as "rb_shape"
                        'caltech_cand_rbscale_cut':4., # caltech_candidate rb_scale >= cut
                        'caltech_cand_ellip_cut':0.32,  # ellip_avg <= cut
                        'fewsample_nepoch_cut':6, # shortsampled_cand : n_epochs <= cut
                        'fewsample_deltat_cut':7, # (days) shortsampled_cand : delta_t <= cut
                        'bad_period_short_cut':0.02, # period < 30 mins
                        'bad_period_long_cut':14., # period > 14 days
                        },
                     }


    def get_srcid_summary_dict(self, ingested_srcids):
        """ Fill a dictionary with info about candidates associated with each source.
        """
        srcid_summary_dict = {}
        checked_srcids = []
        for src_id in ingested_srcids:
            if src_id in checked_srcids:
                continue # skip since done already
            checked_srcids.append(src_id)
            srcid_summary_dict[src_id] = {'obj_id':[],
                                          'realbogus':[],
                                          'ujd':[]}
            select_str = """SELECT src_id, ptf_events.id, realbogus, ujd, srcid_lookup.ra, srcid_lookup.decl
FROM object_test_db.obj_srcid_lookup
JOIN object_test_db.ptf_events ON (object_test_db.ptf_events.id=obj_srcid_lookup.obj_id)
JOIN source_test_db.srcid_lookup USING (src_id)
WHERE obj_srcid_lookup.survey_id=3 AND src_id=%d """ % (src_id)

            self.rdbt.cursor.execute(select_str)
            rows = self.rdbt.cursor.fetchall()
            for row in rows:
                (src_id, obj_id, realbogus, ujd, ra, dec) = row
                srcid_summary_dict[src_id]['obj_id'].append(obj_id)
                srcid_summary_dict[src_id]['realbogus'].append(realbogus)
                srcid_summary_dict[src_id]['ujd'].append(ujd)
                srcid_summary_dict[src_id]['ra'] = ra
                srcid_summary_dict[src_id]['dec'] = dec
                srcid_summary_dict[src_id]['src_id'] = src_id
        return srcid_summary_dict


    def get_closest_source(self, srcid_summary_dict, ptf_cand_dict):
        """
        """
        distance_dict = {}
        for src_id,src_dict in srcid_summary_dict.iteritems():
            d_ra = src_dict['ra'] - ptf_cand_dict['ra']
            d_dec = src_dict['dec'] - ptf_cand_dict['dec']
            distance = math.sqrt((d_ra*d_ra) + (d_dec*d_dec))
            distance_dict[distance] = src_dict

        dist_list = distance_dict.keys()
        dist_list.sort()
        min_dist = dist_list[0]
        return distance_dict[min_dist]


    def get_srcid_containing_candidate(self, srcid_summary_dict, ptf_cand_dict):
        """
        """
        for src_id,src_dict in srcid_summary_dict.iteritems():
            if ptf_cand_dict['id'] in src_dict['obj_id']:
                return src_dict
        return {}


    def get_closest_matching_tcp_source(self, ptf_cand_dict, ingested_srcids):
        """ Given a ptf-candidate info dict and a list of nearby/related source-ids,
        Get the closest matching sourceid, and return matching source info in a dict.
        """
        srcid_summary_dict = self.get_srcid_summary_dict(ingested_srcids)

        # TODO: check for candidate_id in dict
        matching_source_dict = {}
        if ptf_cand_dict.has_key('id'):
            matching_source_dict = self.get_srcid_containing_candidate( \
                                              srcid_summary_dict, ptf_cand_dict)
        if len(matching_source_dict) == 0:
            try:
                matching_source_dict = self.get_closest_source(srcid_summary_dict, ptf_cand_dict)
            except:
                # For caltech sources where candidate.id's realbogus <0.1 and only 1 epoch source,  then there will be no source created at this point.  So, abre excepts.
                return {}
        
        return matching_source_dict


    def get_is_rock_info(self, matching_source_dict, ptf_cand_dict):
        """ Compile Pympchecker is_rock info for this source.

            rez = pym.isrock()
            rez = \
{'dec': '+59:13:43.6272',
 'dec_rock': '',
 'dist_rock_arcsec': '',
 'error': False,
 'isrock': False,
 'mag_rock': '',
 'name_rock': '',
 'ra': '17:18:42.8761',
 'ra_rock': '',
 'radius': 30,
 'ts': '2009/6/20 9:1:54',
 'tt': [],
 'unc_rock': '',
 'url': 'http://dotastro.org/mpc_data/ascii_tables/17h18m42.88s_59d13m43.63s_39982.876319_30.00.txt'}
        """
        rock_dist = 30
        
        ra = matching_source_dict['ra']
        dec = matching_source_dict['dec']

        is_rock_count = 0
        obj_ids_matched = False
        for i, ujd in enumerate(matching_source_dict['ujd']):
            # we just do this single epoch case to make things run faster:
            do_pymp = False
            if not ptf_cand_dict.has_key('id'):
                do_pymp = True
            elif matching_source_dict['obj_id'][i] == ptf_cand_dict['id']:
                do_pymp = True

            if do_pymp:
                obj_ids_matched = True
                pym = cand.pymp(pos=(ptf_cand_dict['ra'],ptf_cand_dict['dec']), time_obs=ujd,
                       radius=rock_dist)
                print ra, dec, pym.pos
                try:
                    rez = pym.isrock()
                    if rez['isrock']:
                        is_rock_count += 1
                except:
                    pass # KLUDGE: skip epoch where web access fails
                break
        if not obj_ids_matched:
            is_rock_count = -1
        return {'is_rock_count':is_rock_count}


    # obsolete:
    def get_is_rock_info__old(self, matching_source_dict):
        """ Compile Pympchecker is_rock info for this source.

            rez = pym.isrock()
            rez = \
{'dec': '+59:13:43.6272',
 'dec_rock': '',
 'dist_rock_arcsec': '',
 'error': False,
 'isrock': False,
 'mag_rock': '',
 'name_rock': '',
 'ra': '17:18:42.8761',
 'ra_rock': '',
 'radius': 30,
 'ts': '2009/6/20 9:1:54',
 'tt': [],
 'unc_rock': '',
 'url': 'http://dotastro.org/mpc_data/ascii_tables/17h18m42.88s_59d13m43.63s_39982.876319_30.00.txt'}
        """
        rock_dist = 30
        
        ra = matching_source_dict['ra']
        dec = matching_source_dict['dec']

        is_rock_count = 0
        for ujd in matching_source_dict['ujd']:
            pym = cand.pymp(pos=(ra,dec), time_obs=ujd,
                       radius=rock_dist)
            print ra, dec, pym.pos
            rez = pym.isrock()
            if rez['isrock']:
                is_rock_count += 1
        if is_rock_count == 0:
            is_rock_count = 'Null'

        return {'is_rock_count':is_rock_count}


    def get_rb_slope(self, candidate_id=None):
        """ SELECT 5 realbougs values from mysql RDB for a candidate id and
        use cand.py function to calculate RB slope metric.
        """
        # todo get from mysql rdb
        select_str = "SELECT bogus, suspect, unclear, maybe, realish FROM object_test_db.ptf_events WHERE id=%d" % (candidate_id)
        self.rdbt.cursor.execute(select_str)
        rows = self.rdbt.cursor.fetchall()
        if len(rows) > 0:
            (bogus, suspect, unclear, maybe, realish) = rows[0]
            rb_slope_str = self.cand_lblq.reckon_rb_shape(realish, maybe, unclear, suspect, bogus)
            try:
                rb_slope_val = int(rb_slope_str[:2])
            except:
                rb_slope_val = -10 # "unknown"
        else:
            rb_slope_val = -11 # "unknown"
        return rb_slope_val


    def get_nearby_classifier_info(self, matching_source_dict, ptf_cand_dict):
        """ Get Nearby candidate information, count the number of
        significant/interesting candidates are associated with this source.
        """
        is_interesting_count = 0
        is_interesting_cand_dict = {}
        # This loop takes too long, and I figured we'd just get the NN rb/sym values for the classification class_id since this is much faster
        candidate_id_list = matching_source_dict.get('obj_id',[])
        #candidate_id_list = [ptf_cand_dict['id']]
        ptf_cand_summarize_dict = {}

        rbscale_combined_list = []
        ellip_list = []
        for candidate_id in candidate_id_list:
            nearby_class = self.cand_lblq.summarize_nearby_candidates(candidate_id)
            nearby_class['is_interesting'] = False
            try:
                combined_metric = math.sqrt(nearby_class['rb_scale_simp'] * \
                                        nearby_class['rb_scale'])
            except:
                #combined_metric = -1 # ASSUME not interesting
                combined_metric = 0 # KLUDGE(since affects average calculation) ASSUME not interesting
            rbscale_combined_list.append(combined_metric)
            if combined_metric >= self.pars['overall_cuts']['transient_combined_metric_cut']:
                is_interesting_count += 1
                is_interesting_cand_dict[candidate_id] = copy.copy(nearby_class)

            ellip_list.append(self.cand_lblq.get_candidates_ellip(candidate_id))
            if ptf_cand_dict.has_key('id'):
                if candidate_id == ptf_cand_dict['id']:
                    ptf_cand_summarize_dict = copy.deepcopy(nearby_class)

        #if len(is_interesting_cand_dict) == 0:
        #    print 'yo'
        out_dict = {'is_interesting_count':is_interesting_count,
                    'is_interesting_cand_dict':is_interesting_cand_dict,
                    'ptf_cand_summarize_dict':ptf_cand_summarize_dict,
                    'nearby_sqrt_rbscales_avg':sum(rbscale_combined_list) / float(len(rbscale_combined_list))}
        if str(out_dict['nearby_sqrt_rbscales_avg']) == 'nan':
            out_dict['nearby_sqrt_rbscales_avg'] = 'Null'

        if ptf_cand_dict.has_key('id'):
            rb_slope_val = self.get_rb_slope(candidate_id=ptf_cand_dict['id'])
            out_dict['rb_slope_val'] = rb_slope_val

        slope_val_list = []
        for c_id in candidate_id_list:
            rb_slope_val = self.get_rb_slope(candidate_id=c_id)
            slope_val_list.append(rb_slope_val)
        out_dict['rb_slope_val_avg'] = sum(slope_val_list)/float(len(slope_val_list))
        
        if ptf_cand_dict.has_key('id'):
            out_dict['ellip'] = self.cand_lblq.get_candidates_ellip(ptf_cand_dict['id'])
        out_dict['ellip_avg'] = sum(ellip_list) / float(len(ellip_list))

        return out_dict


    def populate_TCP_sources_for_ptf_radec(self, ra=None, dec=None, ptf_cand_dict={}, do_get_classifications=True):
        """ Get TCP classifications when given (ra,dec) or ...
        return in some condensed dict.
        """

        ##### Select all ptf candidates for surrounding ra,dec region, and insert into local RDB.
        ptf_diff_obj_list = self.PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql({}, index_offset=0, \
                                                                           n_last_rows=1, \
                                                          test_data_substitute_pgsql_with_mysql=False, \
                                                          do_spatial_query=True, \
                                                          ra=ra, dec=dec)

        ##### generate the TCP sources for these candidates:
        # NOTE: The following can also be done in PARALLEL by:
        #           PTFPostgreServer.spawn_ingestion_tasks_using_diff_objs()

        # TODO: we really just need to insert the ptf-candidate
        ingested_srcids = []
        ingested_src_xmltuple_dict = {}
        is_done = False
        for diff_obj in ptf_diff_obj_list:
            for obj_id in diff_obj['obj_ids']:
                if obj_id == ptf_cand_dict['id']:
                    # NOTE: unlike normal TCP / ptf_master.py: we generate features for n_epochs >= 1 so that srcid_xml_tuple_list is made available below:
                    (srcid_xml_tuple_list, n_objs) = self.DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=self.DiffObjSourcePopulator.feat_db, n_epochs_cut=1)
                    if (n_objs >= 1) and (do_get_classifications):
                        self.DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list)
                    for srcid,xmllines in srcid_xml_tuple_list:
                        ingested_srcids.append(srcid)
                        ingested_src_xmltuple_dict[srcid] = xmllines
                    is_done = True    
                    break
            if is_done:
                break
        return (ingested_srcids, ingested_src_xmltuple_dict)


    def populate_TCP_sources_for_ptf_radec__old2(self, ra=None, dec=None):
        """ Get TCP classifications when given (ra,dec) or ...
        return in some condensed dict.
        """

        ##### Select all ptf candidates for surrounding ra,dec region, and insert into local RDB.
        ptf_diff_obj_list = PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql({}, index_offset=0, \
                                                                           n_last_rows=1, \
                                                          test_data_substitute_pgsql_with_mysql=False, \
                                                          do_spatial_query=True, \
                                                          ra=ra, dec=dec)

        ##### generate the TCP sources for these candidates:
        # NOTE: The following can also be done in PARALLEL by:
        #           PTFPostgreServer.spawn_ingestion_tasks_using_diff_objs()

        # TODO: we really just need to insert the ptf-candidate
        ingested_srcids = []
        for diff_obj in ptf_diff_obj_list:
            # TODO: I need to query whether there is an associated source for any of the obj_ids in diff_obj['obj_ids']
            #    - if there is a source, we do not need to re-ingest. (or we re-ingest once).
            do_ingest_diffobj = True
            for obj_id in diff_obj['obj_ids']:
                select_str = "SELECT src_id FROM object_test_db.obj_srcid_lookup where obj_id=%d AND survey_id=3" % (\
                                                                  obj_id)
                self.rdbt.cursor.execute(select_str)
                rows = self.rdbt.cursor.fetchall()
                for row in rows:
                    if int(row[0]) in ingested_srcids:
                        do_ingest_diffobj = False
                        break
                if not do_ingest_diffobj:
                    break
            if do_ingest_diffobj:
                (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db, n_epochs_cut=7)
                if n_objs >= 7:
                    DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list)
                for srcid,xmllines in srcid_xml_tuple_list:
                    ingested_srcids.append(srcid)
        return ingested_srcids


    def populate_TCP_sources_for_ptf_radec__old(self, ra=None, dec=None):
        """ Get TCP classifications when given (ra,dec) or ...
        return in some condensed dict.
        """

        ##### Select all ptf candidates for surrounding ra,dec region, and insert into local RDB.
        ptf_diff_obj_list = PTFPostgreServer.insert_pgsql_ptf_objs_into_mysql({}, index_offset=0, \
                                                                           n_last_rows=1, \
                                                          test_data_substitute_pgsql_with_mysql=False, \
                                                          do_spatial_query=True, \
                                                          ra=ra, dec=dec)

        ##### generate the TCP sources for these candidates:
        # NOTE: The following can also be done in PARALLEL by:
        #           PTFPostgreServer.spawn_ingestion_tasks_using_diff_objs()
        ingested_srcids = []
        for diff_obj in ptf_diff_obj_list:
            # TODO: I need to query whether there is an associated source for any of the obj_ids in diff_obj['obj_ids']
            #    - if there is a source, we do not need to re-ingest. (or we re-ingest once).

            (srcid_xml_tuple_list, n_objs) = DiffObjSourcePopulator.ingest_diffobj(diff_obj, feat_db=DiffObjSourcePopulator.feat_db, n_epochs_cut=7)
            if n_objs >= 7:
                DiffObjSourcePopulator.class_interface.classify_and_insert_using_vosource_list(srcid_xml_tuple_list)
            for srcid,xmllines in srcid_xml_tuple_list:
                ingested_srcids.append(srcid)
        return ingested_srcids


    def get_TCP_classifications(self, matching_source_dict):
        """ Get TCP classifications for matching TCP source.
        return a summary dict.
        """
        min_class_schema_id = 41
        avg_weighted_prob_cut = 0.01 # For now let everything slip through.  maybe eventually 1.0*0.8 or 0.7*0.7
        #realbogus_cut = 0.165
        # #realbogus_ratio_cut = 0.8 # 0.8
        src_id = matching_source_dict['src_id']

        # TODO: query RDB for src_id & get clssification results

        select_str = """SELECT schema_comment, class_name, prob, class_rank
FROM source_test_db.src_class_probs
JOIN source_test_db.classid_lookup USING (schema_id, class_id)
WHERE src_id = %d AND schema_id >= %d
        """ % (src_id, min_class_schema_id)

        self.rdbt.cursor.execute(select_str)
        rows = self.rdbt.cursor.fetchall()

        all_classif_dict = {}
        for (schema_comment, class_name, prob, class_rank) in rows:
            all_classif_dict[(schema_comment, class_name)] = { \
                'schema_comment':schema_comment,
                'class_name':class_name,
                'prob':prob,
                'class_rank':class_rank}

        out_dict = {'all_classif_dict':all_classif_dict}

        prob_key_classdict = {}
        weighted_prob_list = []
        for (schema_comment, class_name),class_dict in all_classif_dict.iteritems():
            class_def_dict = ingest_tools.pars['class_schema_definition_dicts'].get(schema_comment,{})
            class_weight = class_def_dict.get('specific_class_weight_dict',{}).get(class_name,None)
            if class_weight == None:
                class_weight = class_def_dict.get('general_class_weight',0.0)

            # So, if the schema has general_class_weight > (some number) then
            #     it is a class to consider for is_variable calculation
            if class_weight >= self.pars['overall_cuts']['general_class_weight_cut']:                
                prob_weighted = class_weight * class_dict['prob']
                weighted_prob_list.append(prob_weighted)
                class_dict['prob_weighted'] = prob_weighted
                prob = class_dict['prob']
                if prob_key_classdict.has_key(prob):
                    prob += 0.0001 # KLUDGE, just to make unique and get in dict
                prob_key_classdict[prob] = class_dict


        avg_weighted_prob = 0
        if len(weighted_prob_list) > 0:
            avg_weighted_prob = sum(weighted_prob_list) / len(weighted_prob_list)
        out_dict['avg_weighted_prob'] = avg_weighted_prob

        n_realbogus_pass = 0
        for realbogus in matching_source_dict['realbogus']:
            if realbogus >= self.pars['overall_cuts']['realbogus_cut']:
                n_realbogus_pass += 1

        realbogus_ratio = n_realbogus_pass / float(len(matching_source_dict['realbogus']))
        #rb_ratio_pass = False
        #if realbogus_ratio >= realbogus_ratio_cut:
        #    rb_ratio_pass = True

        #out_dict['rb_ratio_pass'] = rb_ratio_pass
        out_dict['realbogus_ratio'] = realbogus_ratio
        out_dict['n_epochs'] = len(matching_source_dict['ujd'])
        out_dict['delta_t'] = max(matching_source_dict['ujd']) - min(matching_source_dict['ujd'])


        #is_variable = False
        #if (rb_ratio_pass and
        #    (avg_weighted_prob >= avg_weighted_prob_cut) and
        #    (out_dict['n_epochs'] >= 8)):
        #    is_variable = True
        #out_dict['is_variable'] = is_variable



        select_str = 'select feat_val from source_test_db.feat_values join source_test_db.feat_lookup using (feat_id) where filter_id = 8 and src_id=%d and feat_lookup.feat_name="freq1_harmonics_freq_0"' % (src_id)
        self.rdbt.cursor.execute(select_str)
        rows = self.rdbt.cursor.fetchall()

        if len(rows) > 0:
            out_dict['freq'] = rows[0][0]
        if out_dict.get('freq', None) == None:
            out_dict['freq'] = 'Null'

        #if is_variable:
        if 1:
            prob_list = prob_key_classdict.keys()
            prob_list.sort(reverse=True)
            if len(prob_list) > 0:
                out_dict['1st_class_dict'] = prob_key_classdict[prob_list[0]]
            if len(prob_list) > 1:
                out_dict['2nd_class_dict'] = prob_key_classdict[prob_list[1]]
            if len(prob_list) > 2:
                out_dict['3rd_class_dict'] = prob_key_classdict[prob_list[2]]

        # TODO: do some sort of count of classes, and prob weights

        final_science_class_name = out_dict.get('1st_class_dict',{}).get('class_name',' ')   
        final_science_class_prob = out_dict.get('1st_class_dict',{}).get('prob',-1)          

        out_dict['period'] = -1
        if out_dict['freq'] != 'Null':
            out_dict['period'] = 1. / out_dict['freq']

        if (('Ursae' in final_science_class_name) and
            (final_science_class_prob >= self.pars['overall_cuts']['periodic_var_prob_cut']) and
            (out_dict['period'] >= 0.088) and
            (out_dict['period'] <= 0.265)):
            out_dict['final_science_class_name'] = "RR Lyrae shortperiod"
            out_dict['final_science_class_prob'] = final_science_class_prob
        elif (('Lyrae' in final_science_class_name) and
            (final_science_class_prob >= self.pars['overall_cuts']['periodic_var_prob_cut']) and
            (out_dict['period'] >= 0.175) and
            (out_dict['period'] <= 0.49)):
            out_dict['final_science_class_name'] = "RR Lyrae longperiod"
            out_dict['final_science_class_prob'] = final_science_class_prob
        else:
            out_dict['final_science_class_name'] = ' '
            out_dict['final_science_class_prob'] = -1          

        #out_dict['final_science_class_name'] = out_dict.get('1st_class_dict',{}).get('class_name',' ')
        #out_dict['final_science_class_prob'] = out_dict.get('1st_class_dict',{}).get('prob',-1)          
        return out_dict


    def add_to_condensed_dict(self, col_name, col_val):
        self.ordered_colname_list.append(col_name)
        self.cond_class_dict[col_name] = col_val


    def generate_overall_classification(self, matching_source_dict, 
                                        tcp_classif, 
                                        rock_classif, 
                                        nearby_classif, 
                                        jdac_class, 
                                        ptf_cand_dict):
        """ Generate the final classification of roughly: rock/variable/transient/junk.
        """
        pars = self.pars['overall_cuts']

        if rock_classif['is_rock_count'] > 0:
            return {'overall_type':'rock'}
        else:
            rock_classif['is_rock_count'] = 'Null' # so the webpage looks nice

        if ((tcp_classif['n_epochs'] >= pars['variable_n_epoch_cut']) and 
            (tcp_classif['realbogus_ratio'] > pars['realbogus_ratio_cut']) and
            (tcp_classif['final_science_class_prob'] > -1)):
                # TODO: also check for a primary period / frequence found, and that it is in some freq range.
                return {'overall_type':'periodic_variable', 
                        'science_class':tcp_classif['final_science_class_name'],  
                        'class_prob':tcp_classif['final_science_class_prob']}


        if ((nearby_classif['nearby_sqrt_rbscales_avg'] >= pars['rbscale_combined_avg_cut']) and
            (nearby_classif['rb_slope_val_avg'] >= pars['rb_slope_cut']) and
            (nearby_classif['ellip_avg'] <= pars['caltech_cand_ellip_cut'])):
            #20090831: dstarr comments out: (nearby_classif['ptf_cand_summarize_dict'].get('rb_scale',9999) >= pars['caltech_cand_rbscale_cut']) and

            if ((tcp_classif['delta_t'] <= pars['fewsample_deltat_cut']) and
                (tcp_classif['n_epochs'] <= pars['fewsample_nepoch_cut'])):
                if ((jdac_class['jdac_class_name'] == '"SN"') or
                    (jdac_class['jdac_class_name'] == '"AGN"')):
                    return {'overall_type':jdac_class['jdac_class_name'].strip('"') + "_short_candid", 
                            'class_prob':jdac_class['jdac_class_prob']}
                else:
                    return {'overall_type':'short_candid'}
            else:
                #x
                if ((jdac_class['jdac_class_name'] == '"SN"') or
                    (jdac_class['jdac_class_name'] == '"AGN"')):
                    return {'overall_type':jdac_class['jdac_class_name'].strip('"') + "_long_candid", 
                            'class_prob':jdac_class['jdac_class_prob']}
                if (tcp_classif['realbogus_ratio'] > pars['realbogus_ratio_cut']):
                    if ((tcp_classif['period'] >= pars['bad_period_short_cut']) and
                        (tcp_classif['period'] <= pars['bad_period_long_cut'])):
                        # TODO: put this case at 'x':
                        return {'overall_type':'RBRatio_periodic_candid'}
                    else:
                        return {'overall_type':'RBRatio_nonperiodic_candid'}
                else:
                    return {'overall_type':'nonRBRatio_long_candid'}
        if ((jdac_class['jdac_class_name'] == '"SN"') or
            (jdac_class['jdac_class_name'] == '"AGN"')):
            return {'overall_type':jdac_class['jdac_class_name'].strip('"') + "_junk", 
                    'class_prob':jdac_class['jdac_class_prob']}
        if ((tcp_classif['realbogus_ratio'] > pars['realbogus_ratio_cut']) and
            (tcp_classif['n_epochs'] > pars['fewsample_nepoch_cut'])):
            return {'overall_type':'RBRatio_pass_only'}
        return {'overall_type':'junk'}



    def make_condensed_classif_dict(self, matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, ptf_cand_dict, overall_classification):
        """ condense the various classification dictionars into a single depth dict
        which can be inserted into a RDB table.
        """
        self.add_to_condensed_dict('caltech_candidate_shortname', '"' + ptf_cand_dict.get('shortname','') + '"')
        self.add_to_condensed_dict('tcp_source_id', matching_source_dict['src_id'])
        self.add_to_condensed_dict('caltech_candidate_id', ptf_cand_dict.get('id',-1))
        self.add_to_condensed_dict('overall_class_type', '"' + overall_classification['overall_type'] + '"')
        self.add_to_condensed_dict('overall_science_class', '"' + overall_classification.get('science_class',' ') + '"')
        self.add_to_condensed_dict('overall_class_prob', overall_classification.get('class_prob','Null'))
        self.add_to_condensed_dict('is_rock_epoch_count', rock_classif['is_rock_count'])
        self.add_to_condensed_dict('n_epochs', tcp_classif['n_epochs'])
        self.add_to_condensed_dict('nearby_sqrt_rbscales_avg', nearby_classif['nearby_sqrt_rbscales_avg'])
        self.add_to_condensed_dict('nearby_sqrt_rbscales_passes', nearby_classif['is_interesting_count'])
        self.add_to_condensed_dict('realbogus_ratio', tcp_classif['realbogus_ratio'])
        if tcp_classif['freq'] != "Null":
            self.add_to_condensed_dict('period', 1./tcp_classif['freq'])
        else:
            self.add_to_condensed_dict('period', 'Null')
        self.add_to_condensed_dict('rb_slope_avg', nearby_classif['rb_slope_val_avg'])
        self.add_to_condensed_dict('rb_slope', nearby_classif.get('rb_slope_val','Null'))

        if len(nearby_classif['is_interesting_cand_dict']) > 0:
            nearby_rb = nearby_classif['is_interesting_cand_dict'][nearby_classif['is_interesting_cand_dict'].keys()[0]]
        else:
            nearby_rb = {'rb_scale':-1, 'sym_scale':-1}
        if str(nearby_rb['sym_scale']) == 'nan':
            nearby_rb['sym_scale'] = -1

        self.add_to_condensed_dict('nearby_rb_rbscale', nearby_rb['rb_scale'])
        self.add_to_condensed_dict('nearby_rb_symscale', nearby_rb['sym_scale'])
        self.add_to_condensed_dict('ellip', nearby_classif.get('ellip','Null'))
        self.add_to_condensed_dict('ellip_avg', nearby_classif.get('ellip_avg','Null'))
        self.add_to_condensed_dict('caltech_candidate_ra', ptf_cand_dict.get('ra',-1))
        self.add_to_condensed_dict('caltech_candidate_dec', ptf_cand_dict.get('dec',-1))
        self.add_to_condensed_dict('tcp_source_ra', matching_source_dict['ra'])
        self.add_to_condensed_dict('tcp_source_dec', matching_source_dict['dec'])
        self.add_to_condensed_dict('caltech_candidate_rundate', '"' + ptf_cand_dict.get('rundate','') + '"')
        self.add_to_condensed_dict('caltech_candidate_scanner', '"' + ptf_cand_dict.get('scanner','')+ '"')
        self.add_to_condensed_dict('caltech_candidate_type', '"' + str(ptf_cand_dict.get('type','')) + '"')
        self.add_to_condensed_dict('caltech_candidate_type2', '"' + str(ptf_cand_dict.get('type2','')) + '"')

        self.add_to_condensed_dict('avg_weighted_prob', tcp_classif['avg_weighted_prob'])
        self.add_to_condensed_dict('tcp_1st_class_prob', tcp_classif.get('1st_class_dict',{}).get('prob',-1))
        self.add_to_condensed_dict('tcp_1st_class_name', '"' + tcp_classif.get('1st_class_dict',{}).get('class_name',"")+'"')
        self.add_to_condensed_dict('tcp_1st_class_schema', '"' + tcp_classif.get('1st_class_dict',{}).get('schema_comment',"") + '"')
        self.add_to_condensed_dict('tcp_2nd_class_prob',  tcp_classif.get('2nd_class_dict',{}).get('prob',-1))
        self.add_to_condensed_dict('tcp_2nd_class_name', '"' + tcp_classif.get('2nd_class_dict',{}).get('class_name',"")+ '"')
        self.add_to_condensed_dict('tcp_2nd_class_schema','"' + tcp_classif.get('2nd_class_dict',{}).get('schema_comment',"") + '"')
        self.add_to_condensed_dict('tcp_3rd_class_prob',  tcp_classif.get('3rd_class_dict',{}).get('prob',-1))
        self.add_to_condensed_dict('tcp_3rd_class_name', '"' + tcp_classif.get('3rd_class_dict',{}).get('class_name',"")+ '"')
        self.add_to_condensed_dict('tcp_3rd_class_schema','"' + tcp_classif.get('3rd_class_dict',{}).get('schema_comment',"") + '"')

        self.add_to_condensed_dict('jdac_nearest_type', jdac_class['jdac_nearest_type'])
        self.add_to_condensed_dict('jdac_nearest_type_confid', jdac_class['jdac_nearest_type_confid'])
        self.add_to_condensed_dict('jdac_class_name', jdac_class['jdac_class_name'])
        self.add_to_condensed_dict('jdac_class_prob', jdac_class['jdac_class_prob'])

        return (self.ordered_colname_list, self.cond_class_dict)


    def insert_into_table(self, ordered_colname_list, cond_class_dict, tablename=""):
        """ Insert these Caltech classifications into an RDB TABLE
        """
        insert_list = ["INSERT INTO %s (%s) VALUES " % ( \
                              tablename,
                              ', '.join(self.ordered_colname_list))]

        val_list = []
        for k in self.ordered_colname_list:
            val_list.append(str(cond_class_dict[k]))
        insert_list.append("(%s), " % ', '.join(val_list))

        on_duplicate_update_str = ' ON DUPLICATE KEY UPDATE '
        for col_name in self.ordered_colname_list:
            on_duplicate_update_str += "%s=VALUES(%s), " % (col_name, col_name)
            
        insert_str = ''.join(insert_list)[:-2] + on_duplicate_update_str[:-2]
        print insert_str
        self.rdbt.cursor.execute(insert_str)


    def extract_jdac_classifs(self, ptf_cand_dict):
        """ This extracts the JDAC classification info from the somewhat complex dictionary.
        """
        try:
            j = jdac.JDAC(pos=(ptf_cand_dict['ra'], \
                               ptf_cand_dict['dec']), \
                          do_sdss=False)  # False: so that external SDSS server isn't queried
            jdac_class = j.val_add
        except:
            jdac_class = {}

        jdac_class['jdac_nearest_type'] = '"' + jdac_class.get('nearest_type','FAIL') + '"'
        jdac_class['jdac_nearest_type_confid'] = jdac_class.get('nearest_type_confidence',-1)
        if len(jdac_class.get('prob',{})) == 0:
            jdac_class['jdac_class_name'] = '""'
            #     This makes some JDAC dictionary formatting assumptions:
            jdac_class['jdac_class_prob'] = -1
        else:
            jdac_class['jdac_class_name'] =  '"' + jdac_class.get('prob',{"":-1}).keys()[0] + '"'
            try:
                jdac_class_prob = jdac_class['prob'][jdac_class['prob'].keys()[0]].values()[0]
            except:
                jdac_class_prob = jdac_class.get('prob',{-1:-1}).values()[0]
            if jdac_class_prob == {}:
                jdac_class_prob = -1
            jdac_class['jdac_class_prob'] = jdac_class_prob
        return jdac_class




def table_insert_ptf_cand(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB, ptf_cand_shortname=''):
    """ Given a caltech / ptf candidate ptf09xxx name, INSERT classifications into RDB TABLE

    CREATE TABLE source_test_db.caltech_classif_summary (
    caltech_candidate_shortname VARCHAR(20),
    tcp_source_id BIGINT,
    caltech_candidate_id BIGINT,
    overall_class_type VARCHAR(20),
    overall_science_class VARCHAR(20),
    overall_class_prob VARCHAR(20),
    is_rock_epoch_count INT,
    n_epochs FLOAT,
    nearby_sqrt_rbscales_avg FLOAT,
    realbogus_ratio FLOAT,
    period FLOAT,
    rb_slope_avg FLOAT,
    rb_slope INT,
    nearby_rb_rbscale FLOAT,
    nearby_rb_symscale FLOAT,
    ellip_avg FLOAT,
    ellip FLOAT,
    nearby_sqrt_rbscales_passes INT,
    caltech_candidate_ra DOUBLE,
    caltech_candidate_dec DOUBLE,
    tcp_source_ra DOUBLE,
    tcp_source_dec DOUBLE,
    caltech_candidate_rundate VARCHAR(20),
    caltech_candidate_scanner VARCHAR(20),
    caltech_candidate_type VARCHAR(20),
    caltech_candidate_type2 VARCHAR(20),
    avg_weighted_prob FLOAT,
    tcp_1st_class_prob FLOAT,
    tcp_1st_class_name VARCHAR(80),
    tcp_1st_class_schema VARCHAR(80),
    tcp_2nd_class_prob FLOAT,
    tcp_2nd_class_name VARCHAR(80),
    tcp_2nd_class_schema VARCHAR(80),
    tcp_3rd_class_prob FLOAT,
    tcp_3rd_class_name VARCHAR(80),
    tcp_3rd_class_schema VARCHAR(80),
    jdac_nearest_type VARCHAR(20),
    jdac_nearest_type_confid FLOAT,
    jdac_class_name VARCHAR(20),
    jdac_class_prob FLOAT,
    PRIMARY KEY (caltech_candidate_shortname));

    """

    ##### Get the LBL candidate ids which correlate to a ptf-id (or are near it)
    #     - I have code which gets caltech candidates for a ra,dec.
    #     - should be able to get ra,dec for a caltech-id.

    # # # # #20100127: dstarr disables this because Caltech database currently is down:
    # # # # #ptf_cand_dict = Caltech_DB.get_ptf_candid_info(cand_shortname=ptf_cand_shortname)
    ptf_cand_dict = Caltech_DB.get_ptf_candid_info___non_caltech_db_hack(cand_shortname=ptf_cand_shortname)

    print ptf_cand_dict

    #if ptf_cand_dict['id'] == 12035841:
    #    # This is a case where ingested_srcids is not filled:
    #    print 'yo'
    (ingested_srcids,ingested_src_xmltuple_dict) = Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
                                                   ra=ptf_cand_dict['ra'], \
                                                   dec=ptf_cand_dict['dec'], \
                                                   ptf_cand_dict=ptf_cand_dict)
    #print ingested_srcids
    matching_source_dict = Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                     ptf_cand_dict, ingested_srcids)

    if len(matching_source_dict) == 0:
        print "no associate / generated / matching source found for:"
        print "ptf_cand_dict=", ptf_cand_dict
        print "ingested_srcids=",  ingested_srcids
        return 
    
    ##### TCP classifications:
    tcp_classif = Get_Classifications_For_Ptfid.get_TCP_classifications(matching_source_dict)
    print tcp_classif

    ##### IsRock / PyMPChecker Classifier:
    rock_classif = Get_Classifications_For_Ptfid.get_is_rock_info(matching_source_dict, ptf_cand_dict)
    print "rock_classif['is_rock_count']", rock_classif['is_rock_count']

    ##### Josh's D.A. Classifier:
    # # # # This should do all of the following in a function and the L689 - 704 stuff, just returning/adding to jdac_dict:
    #        extracted_prob(float,'Null'), extracted_name(string,'Null'), extracted_confid(float, 'Null')
    jdac_class = Get_Classifications_For_Ptfid.extract_jdac_classifs(ptf_cand_dict)
    print "JDAC:", jdac_class


    # TODO: I should actually do a count for all epochs in source...
    ##### Nearby candidate classifier:
    nearby_classif = Get_Classifications_For_Ptfid.get_nearby_classifier_info(matching_source_dict, ptf_cand_dict)
    print "nearby_classif['is_interesting_count']", nearby_classif['is_interesting_count']

    #tcp_classif['is_junk'] = False
    #if nearby_classif['is_interesting_count'] <= 1:
    #    tcp_classif['is_junk'] = True

    overall_classification = Get_Classifications_For_Ptfid.generate_overall_classification(matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, ptf_cand_dict)


    (ordered_colname_list, cond_class_dict) = Get_Classifications_For_Ptfid.make_condensed_classif_dict(matching_source_dict, tcp_classif, rock_classif, nearby_classif, jdac_class, ptf_cand_dict, overall_classification)
    
    Get_Classifications_For_Ptfid.insert_into_table(ordered_colname_list, cond_class_dict, tablename="source_test_db.caltech_classif_summary")
    Get_Classifications_For_Ptfid.ordered_colname_list = []
    Get_Classifications_For_Ptfid.cond_class_dict = {}

    ## 20100127: dstarr adds this return (no return was declared earlier):
    #return matching_source_dict


if __name__ == '__main__':

    options = parse_options()
    #pars = { \
    #    '':options.n_noisified_per_orig_vosource,
    #    }

    if options.do_ipython_parallel and options.do_varstar_j48_weka_classifications:
        # Then we do PTF sources and IPython-parallel:
        from IPython.kernel import client
        mec = client.MultiEngineClient()
        tc = client.TaskClient()
        task_id_list = []

        Caltech_DB = CaltechDB()
        exec_str = """
import sys, os
import get_classifications_for_caltechid
import ptf_master
import ingest_tools
DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                 rdbt=DiffObjSourcePopulator.rdbt)
Get_Classifications_For_Ptfid = get_classifications_for_caltechid.GetClassificationsForPtfid(rdbt=DiffObjSourcePopulator.rdbt, PTFPostgreServer=PTFPostgreServer, DiffObjSourcePopulator=DiffObjSourcePopulator)
Caltech_DB = get_classifications_for_caltechid.CaltechDB()
"""
        #exec(exec_str) # DEBUG
        mec.execute(exec_str)
	time.sleep(2) # This may be needed.
        shortname_list = Caltech_DB.get_caltech_shortnames( \
                            conditional_str="shortname > 0 AND type = 'VarStar'")
        for short_name in shortname_list:
	    exec_str = """
ptf_cand_dict = Caltech_DB.get_ptf_candid_info(cand_shortname=short_name)
(ingested_srcids,ingested_src_xmltuple_dict) = Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
                                       ra=ptf_cand_dict['ra'], \
                                       dec=ptf_cand_dict['dec'], \
                                       ptf_cand_dict=ptf_cand_dict)
matching_source_dict = Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                 ptf_cand_dict, ingested_srcids)
if len(matching_source_dict) == 0:
    pass
else:
    tcp_classif = Get_Classifications_For_Ptfid.get_TCP_classifications(matching_source_dict)
"""
            #	    exec_str = """
            #tmp_stdout = sys.stdout
            #sys.stdout = open('/tmp/999', 'a')
            #print '#################################################################################'
            #ptf_cand_dict = Caltech_DB.get_ptf_candid_info(cand_shortname=short_name)
            #print ptf_cand_dict
            #sys.stdout.close()
            #sys.stdout = tmp_stdout
            #ingested_srcids = Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
            #                                       ra=ptf_cand_dict['ra'], \
            #                                       dec=ptf_cand_dict['dec'], \
            #                                       ptf_cand_dict=ptf_cand_dict)
            #"""         
            #exec(exec_str) # DEBUG
            try:
                taskid = tc.run(client.StringTask(exec_str, \
                                            push={'short_name':short_name}))#, retries=3))
                task_id_list.append(taskid)
            except:
                print "EXCEPT!: taskid=", taskid, exec_str



    else:
        DiffObjSourcePopulator = ptf_master.Diff_Obj_Source_Populator(use_postgre_ptf=True)
        PTFPostgreServer = ptf_master.PTF_Postgre_Server(pars=ingest_tools.pars, \
                                                         rdbt=DiffObjSourcePopulator.rdbt)
        Get_Classifications_For_Ptfid = GetClassificationsForPtfid(rdbt=DiffObjSourcePopulator.rdbt, PTFPostgreServer=PTFPostgreServer, DiffObjSourcePopulator=DiffObjSourcePopulator)
        Caltech_DB = CaltechDB()

        # 20100127: dstarr disabled the following 2 lines:
        #shortname_list = Caltech_DB.get_caltech_shortnames( \
        #                    conditional_str="shortname > 0 AND type = 'VarStar'")
        shortname_list = [] #['10xp']
        if (not options.do_ipython_parallel) and options.do_varstar_j48_weka_classifications:
            # this just runs in serial
            for short_name in shortname_list:
                ptf_cand_dict = Caltech_DB.get_ptf_candid_info(cand_shortname=short_name)
                # # # # # # #
                # TODO: need to test this (to make sure no tcp source's epochs are reset, ... :
                (ingested_srcids,ingested_src_xmltuple_dict) = Get_Classifications_For_Ptfid.populate_TCP_sources_for_ptf_radec( \
                                                       ra=ptf_cand_dict['ra'], \
                                                       dec=ptf_cand_dict['dec'], \
                                                       ptf_cand_dict=ptf_cand_dict)

                matching_source_dict = Get_Classifications_For_Ptfid.get_closest_matching_tcp_source( \
                                                                 ptf_cand_dict, ingested_srcids)
                if len(matching_source_dict) == 0:
                    print "no associate / generated / matching source found for:"
                    print "ptf_cand_dict=", ptf_cand_dict
                    print "ingested_srcids=",  ingested_srcids
                    continue
                tcp_classif = Get_Classifications_For_Ptfid.get_TCP_classifications(matching_source_dict)
                #print tcp_classif
                #fp = open("/home/pteluser/scratch/caltech_srcid.dat","a")
                #fp.write("%s %d\n" % (short_name, matching_source_dict['src_id']))
                #fp.close()
                


        elif options.do_general_classifier:
            #table_insert_ptf_cand(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB, ptf_cand_shortname='09qn')
            # # #shortname_list = Caltech_DB.get_caltech_shortnames()
            reduced_list = shortname_list #[shortname_list.index('09aau')+1:] # KLUDGE
            # 20091118 added:
           # reduced_list = ['09byh', '09clg', '09cyr', '09dit', '09dnv', '09eam', '09eoz','09esy', '09fip', '09goo', '09hmg', '09hmf', '09hme', '09hmd']
            reduced_list = ['10xk']
            for short_name in reduced_list:
                table_insert_ptf_cand(DiffObjSourcePopulator, PTFPostgreServer, Get_Classifications_For_Ptfid, Caltech_DB, ptf_cand_shortname=short_name)

            # tcp_classif, rock_classif, nearby_classif, jdac_class, ptf_cand_dict
            # TODO: form some PTF_source TABLE with all classification values.
            #    - on subsequent gret_classifications_for_ptfid.py run, INSERT ON DUPLICATE UPDATE ...
            #   - some spetial fuinction which generates a 1-level dict where the keys will be column names,
            #       - built from the various structured dictionaries


            # TODO: store caltech source results and these classifications in final table which can be html'd
            # TODO: maybe generate a webpage which contains all of this info generated in some table for all caltech-ids
            #        - and this script could continually poll caltech DB for newly classified caltech-ids & generate new rows (and display in PHP page)
            # ptf09xxx | source_id <URL link> | is_rock_class | ...classifications |


            # TODO: input should optionally be (ra,dec) as well ast caltech-id
            #    - should also be able to take input of a TCP srcid, LBL candidate.id

            # TODO: disable the repative source identification and classification with TCP diff_obj code

            # Todo: evalute which TCP class schema and classes are valid and write weights in ingest_tools.pars{}
            #      -> this will most easiy be done with that large class_schema webpage


            # TODO: will want dome final science class, which incorperates all of the classifiers, nearest_neighbor cuts, etc


            # todo want a simple PHP page for now which just queries TABLE and displays in an html table.

            # TODO: RB ratio > 0.5?

