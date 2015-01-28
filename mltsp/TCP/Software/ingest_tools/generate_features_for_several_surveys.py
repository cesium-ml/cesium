#!/usr/bin/env python
"""
This code will be used to (re)generate features for several surveys and generate .arff files for use by others.

The intent is to develop a repository of .arff and maybe .xml files of features used at different times.

We'd like to have SVN commit comments and versions included, to better record what changes occured to codebase.
   -> maybe which features are included in arff
   -> versions of lomb_scargle / lightcurve code...

NOTE: Need to "svn update TCP"   (the root directory of the trunk) prior to running this.

     - generate_featyres_for_several_surveys.py takes hours  on 8 cores (threaded) for larger surveys (> 02 sources)

NOTE: The final result from running this script is to have the following webpage updated:

    http:/lyra.berkeley.edu/~pteluser/tools/survey_arff_archive.html

TODO: In order to have regeneration of xmls / arff done on a larger scale ipython cluster
     (and no threading being used in populate_feat_db_using_TCPTUTOR_sources.py)
     Need to follow test_pairwise_on_citris33_ipython.py Ipython code.

"""
import sys, os
import MySQLdb
import datetime
#import ingest_tools # This is done to get tcptutor and classdb server configs

import populate_feat_db_using_TCPTUTOR_sources
import generate_weka_classifiers

class Generate_Features_For_Several_Surveys:
    """ Main controlling singleton for generate_features_for_several_surveys.py
    """

    def __init__(self, pars={}):
        self.pars = pars
        self.pfds = populate_feat_db_using_TCPTUTOR_sources.Populate_Feat_DB_Using_Tcptutor_sources(pars)


    def get_recent_svn_commit_info(self, tcp_svn_dirpath=''):
        """ Retrieve svn commit information for the last couple commits on
        the Trunk of the TCP branch.
        """
        svn_dict = {}
        for svn_rev_type in ['COMMITTED', 'PREV']:
            exec_str = "svn log -v -r %s %s" % (svn_rev_type, tcp_svn_dirpath)

            (a,b,c) = os.popen3(exec_str)
            a.close()
            c.close()
            lines_str = b.read()
            b.close()
            svn_dict[svn_rev_type] = lines_str
        return svn_dict

    def parse_srcids_from_arff(self, arff_fpath=''):
        """ Parse a given ARFF string

        Return a srcid list.
        
        Code adapted from rpy2_classifiers.py:parse_arff_header()
        
        """
        fp = open(arff_fpath)
        arff_str = fp.read()
        fp.close()

        lines = arff_str.split('\n')
        feat_list = []
        i_srcs = 0
        count_sources = False
        srcid_list = []
        for line in lines:
            if len(line) == 0:
                continue
            if '@data' in line.lower():
                count_sources = True
            elif count_sources:
                srcid_list.append(int(line[:line.find(',')]))
                
        return srcid_list
    

    def parse_features_from_arff_header(self, arff_fpath='', do_sort=True):
        """ Parse a given ARFF string, replace @attribute with @ignored for attributes in
        ignore_attribs list (ala PARF data specification).

        Return arff header string.

        Code adapted from rpy2_classifiers.py:parse_arff_header()
        
        """
        fp = open(arff_fpath)
        arff_str = fp.read()
        fp.close()

        lines = arff_str.split('\n')
        feat_list = []
        i_srcs = 0
        count_sources = False
        for line in lines:
            if len(line) == 0:
                continue
            if line[:10].upper() == '@ATTRIBUTE':
                feat_name = line.split()[1]
                feat_list.append(feat_name)
            elif '@data' in line.lower():
                count_sources = True
            elif count_sources:
                i_srcs += 1
                
        if do_sort:
            feat_list.sort()
        return {'feat_list':feat_list,
                'n_srcs':i_srcs}


    def parse_feature_value_dict_from_arff(self, arff_fpath='',
                                           all_feat_list=[], features_to_update=[]):
        """ Parse a given ARFF string,

        Return a dictionary of lists-of-feature-values for given features
        
        """
        feat_val_dict = {'src_id':[]}
        index_featname_lookup = {}
        for i, feat_name in enumerate(all_feat_list):
            if feat_name in features_to_update:
                index_featname_lookup[i] = feat_name
                feat_val_dict[feat_name] = []

        fp = open(arff_fpath)
        arff_str = fp.read()
        fp.close()

        lines = arff_str.split('\n')
        feat_list = []
        count_sources = False
        for line in lines:
            if len(line) == 0:
                continue
            if line[:10].upper() == '@ATTRIBUTE':
                feat_name = line.split()[1]
                feat_list.append(feat_name)
            elif '@data' in line.lower():
                count_sources = True
            elif count_sources:
                elems = line.split(',')
                feat_val_dict['src_id'].append(int(elems[0]))
                for i_feat, feat_name in index_featname_lookup.iteritems():
                    try:
                        feat_val_dict[feat_name].append(str(float(elems[i_feat])))
                    except:
                        feat_val_dict[feat_name].append('NULL')
        return feat_val_dict
                

    def make_paths(self, project_id=0):
        """
        """

        schema_id = 10000 + project_id
        feature_timestamp = datetime.datetime.utcnow()
        feature_timestamp_str = str(feature_timestamp).replace(' ','_')

        #import pdb; pdb.set_trace()
        tranx_root_dirpath = "%s/tutor_%d/%s" %(self.pars['tranx_dirpath_historical_archive_featurexmls_arffs'],
                                                project_id,
                                                feature_timestamp_str)

        lyra3_root_dirpath = "%s/tutor_%d/%s" %(self.pars['lyra3_dirpath_historical_archive_featurexmls_arffs'],
                                                project_id,
                                                feature_timestamp_str)
        lyra3_url_root = "historical_archive_featurexmls_arffs/tutor_%d/%s" %(project_id,
                                                feature_timestamp_str)


        #xml_write_dirpath = "/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-01_07:50:04.818898/xmls" # debug
        #tranx_arff_filepath = "/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-01_07:50:04.818898/source_feats.arff" # debug
        path_dict = {'tranx_root_dirpath':tranx_root_dirpath,
                     'lyra3_root_dirpath':lyra3_root_dirpath,
                     'xml_write_dirpath':"%s/xmls" % (tranx_root_dirpath),
                     'tranx_arff_filepath':"%s/source_feats.arff" % (tranx_root_dirpath),
                     'lyra3_arff_filepath':"%s/source_feats.arff" % (lyra3_root_dirpath),
                     'feature_timestamp':feature_timestamp,
                     'lyra3_url_root':lyra3_url_root,
                     'schema_id':schema_id,
                     }

        os.system("mkdir -p " + path_dict['xml_write_dirpath'])

        return path_dict



    def generate_xmls_and_arff_for_project(self, project_id=0, path_dict={}):
        """ Given a TUTOR project_id, generate xmls with features and arff,
        and copy to lyra3 for web-access.
        """

        n_sources_needed_for_class_inclusion = 1 # this is only used for arff generation (not XML)

        
        ##### Populate the xmls:
        srcid_list = self.pfds.get_srcid_list(project_id=project_id,
                                         exclude_existing_xml_sources=False)
        self.pfds.threaded_get_features_populate_rdb(path_dict['schema_id'], srcid_list,
                                                xml_write_dirpath=path_dict['xml_write_dirpath'])

        ##### Generate ARFF file (taken from generate_weka_classifiers.py):
        ParallelArffMaker = generate_weka_classifiers.Parallel_Arff_Maker(pars={})
        ParallelArffMaker.generate_arff_using_xmls(vosource_xml_dirpath=path_dict['xml_write_dirpath'], \
                                                   out_arff_fpath=path_dict['tranx_arff_filepath'], \
                                                   n_sources_needed_for_class_inclusion= \
                                                                n_sources_needed_for_class_inclusion)
        #import pdb; pdb.set_trace()
        
                


    def insert_arff_into_rdb(self, project_id=0, arff_fpath='', path_dict={}):
        """ Given an arff, insert into MySQL database.
        """
        ##### Parse the features in arff file
        parse_dict = self.parse_features_from_arff_header(arff_fpath=arff_fpath)
        arff_features = parse_dict['feat_list']
        n_srcs = parse_dict['n_srcs']

        if n_srcs == 0:
            print 'ERROR: n_srcs == 0!!!'
            raise
        feat_str = '\n'.join(arff_features)

        ##### scp files over:
        
        if project_id == 0:
            project_name = "many TUTOR projects"
        else:
            select_str = 'SELECT project_title FROM projects WHERE project_id=%d' % (project_id)
            self.pfds.tutor_cursor.execute(select_str)
            results = self.pfds.tutor_cursor.fetchall()
            project_name = results[0][0]

        #import pdb; pdb.set_trace()
        exec_lyra3_mkdir = "ssh pteluser@192.168.1.103 mkdir -p %s" % (path_dict['lyra3_root_dirpath'])
        exec_scp = "scp %s pteluser@192.168.1.103:%s" % (path_dict['tranx_arff_filepath'],
                                                path_dict['lyra3_arff_filepath'])
        os.system(exec_lyra3_mkdir)
        os.system(exec_scp)

        ##### Get recent svn commit info:
        tcp_svn_dirpath = os.path.abspath(os.environ.get("TCP_DIR"))
        svn_dict = self.get_recent_svn_commit_info(tcp_svn_dirpath=tcp_svn_dirpath)

        insert_str = 'INSERT INTO archive_featurexmls_arffs (project_id, project_name, dtime, tranx_root_dirpath, lyra3_root_dirpath, svn_committed, svn_prev, feats_used, n_srcs) VALUES (%d, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %d)' % (project_id, project_name, str(path_dict['feature_timestamp']), path_dict['tranx_root_dirpath'], path_dict['lyra3_url_root'], svn_dict["COMMITTED"], svn_dict["PREV"], feat_str, n_srcs)


        self.pfds.classdb_cursor.execute(insert_str)


        ### This table is needed in source_test_db (this is only done once):
        create_table_str = """CREATE TABLE archive_featurexmls_arffs (
                  archive_id INT UNSIGNED AUTO_INCREMENT,
                  project_id INT UNSIGNED,
                  project_name VARCHAR(80),
                  dtime DATETIME,
                  n_srcs INT UNSIGNED,
                  tranx_root_dirpath VARCHAR(160),
                  lyra3_root_dirpath VARCHAR(160),
                  svn_committed VARCHAR(4000),
                  svn_prev VARCHAR(4000),
                  feats_used VARCHAR(4000),
                  PRIMARY KEY (archive_id));
                  """



        ### Additional on webpage:
        # tutor link (using project_id)
        # arff link


    def insert_arff_into_rdb__old(self, project_id=0, arff_fpath='', path_dict={}):
        """ Given an arff, insert into MySQL database.
        """


        ##### Parse the features in arff file
        parse_dict = self.parse_features_from_arff_header(arff_fpath=arff_fpath)
        arff_features = parse_dict['feat_list']
        n_srcs = parse_dict['n_srcs']

        if n_srcs == 0:
            print 'ERROR: n_srcs == 0!!!'
            raise
        feat_str = '\n'.join(arff_features)

        ##### scp files over:
        
        select_str = 'SELECT project_title FROM projects WHERE project_id=%d' % (project_id)
        self.pfds.tutor_cursor.execute(select_str)
        results = self.pfds.tutor_cursor.fetchall()
        project_name = results[0][0]

        #import pdb; pdb.set_trace()
        exec_lyra3_mkdir = "ssh pteluser@192.168.1.103 mkdir -p %s" % (path_dict['lyra3_root_dirpath'])
        exec_scp = "scp %s pteluser@192.168.1.103:%s" % (path_dict['tranx_arff_filepath'],
                                                path_dict['lyra3_arff_filepath'])
        os.system(exec_lyra3_mkdir)
        os.system(exec_scp)

        ##### Get recent svn commit info:
        tcp_svn_dirpath = os.path.abspath(os.environ.get("TCP_DIR"))
        svn_dict = self.get_recent_svn_commit_info(tcp_svn_dirpath=tcp_svn_dirpath)

        insert_str = 'INSERT INTO archive_featurexmls_arffs (project_id, project_name, dtime, tranx_root_dirpath, lyra3_root_dirpath, svn_committed, svn_prev, feats_used, n_srcs) VALUES (%d, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %d)' % (project_id, project_name, str(path_dict['feature_timestamp']), path_dict['tranx_root_dirpath'], path_dict['lyra3_url_root'], svn_dict["COMMITTED"], svn_dict["PREV"], feat_str, n_srcs)


        self.pfds.classdb_cursor.execute(insert_str)


        ### This table is needed in source_test_db (this is only done once):
        create_table_str = """CREATE TABLE archive_featurexmls_arffs (
                  archive_id INT UNSIGNED AUTO_INCREMENT,
                  project_id INT UNSIGNED,
                  project_name VARCHAR(80),
                  dtime DATETIME,
                  n_srcs INT UNSIGNED,
                  tranx_root_dirpath VARCHAR(160),
                  lyra3_root_dirpath VARCHAR(160),
                  svn_committed VARCHAR(4000),
                  svn_prev VARCHAR(4000),
                  feats_used VARCHAR(4000),
                  PRIMARY KEY (archive_id));
                  """



        ### Additional on webpage:
        # tutor link (using project_id)
        # arff link


    def parse_arff_and_update_feature_tables(self, arff_fpath='', features_to_update=[], project_id=-1, do_insert=False):
        """
        For parsing a citris33 (or any) .arff file for tranx mysql known tutor-project_ids

        TODO: just do an UPDATE, thus if the srcid does not exist, a mysql error will occur.


    GenerateFeaturesForSeveralSurveys.parse_arff_and_update_feature_tables( \
    arff_fpath='/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/source_feats.arff',
    features_to_update=['freq1_harmonics_freq_0', 'freq2_harmonics_freq_0', 'freq3_harmonics_freq_0'],
    project_id=126) # project_id=126 # ASAS-ACVS

        """
        feat_name_dict = self.parse_features_from_arff_header(arff_fpath=arff_fpath, do_sort=False)
        feat_list = feat_name_dict['feat_list']

        feat_val_dict = self.parse_feature_value_dict_from_arff(arff_fpath=arff_fpath,
                                                                all_feat_list=feat_list,
                                                                features_to_update=features_to_update)

        db = MySQLdb.connect(host=self.pars['classdb_hostname'], \
                                  user=self.pars['classdb_username'], \
                                  db=self.pars['classdb_database'],\
                                  port=self.pars['classdb_port'])
        cursor = db.cursor()

        # Get the feature-ids from the database (for the default dotastro/tutor filter_id=8):
        feat_name_dbid_dict = {}
        for feat_name in features_to_update:
            select_str = 'SELECT feat_id FROM feat_lookup WHERE filter_id=8 and feat_name like "%' + feat_name + '%"'
            cursor.execute(select_str)
            results = cursor.fetchall()
            feat_name_dbid_dict[feat_name] = results[0][0]

        if do_insert:
            i_incr_size = 100
            i_high_list = range(i_incr_size, len(feat_val_dict['src_id']), i_incr_size)
            i_high_list.append(len(feat_val_dict['src_id']))
            for j, i_high in enumerate(i_high_list):
                if (i_high == i_incr_size):
                    i_low = 0
                else:
                    i_low = i_high_list[j-1]
                # We do this when the (src_id,feat_id) do not yet exist in feat_values table
                insert_list = ["INSERT INTO feat_values (src_id, feat_id, feat_val) VALUES "]
                for i in range(i_low, i_high):
                    srcid = feat_val_dict['src_id'][i]
                    for feat_name, feat_id in feat_name_dbid_dict.iteritems():
                        insert_list.append("(%d, %d, %s), " % \
                                          ( srcid + 100000000, feat_id, feat_val_dict[feat_name][i]))
                cursor.execute(''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE feat_val=VALUES(feat_val)")

            #insert_list = ["INSERT INTO feat_values (src_id, feat_id, feat_val) VALUES "]
            #for i, srcid in enumerate(feat_val_dict['src_id'][:10]):
            #    for feat_name, feat_id in feat_name_dbid_dict.iteritems():
            #        insert_list.append("(%d, %d, %s), " % \
            #                          ( srcid + 100000000, feat_id, feat_val_dict[feat_name][i]))
            #cursor.execute(''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE feat_val=VALUES(feat_val)")
        else:
            # UPDATE the mysql feat_val table for all of the given sources

            update_table_str = "UPDATE feat_values SET feat_val=%s WHERE (src_id=%s AND feat_id=%s)"
            update_table_tups = []

            for i, srcid in enumerate(feat_val_dict['src_id']):
                for feat_name, feat_id in feat_name_dbid_dict.iteritems():
                    update_table_tups.append((feat_val_dict[feat_name][i], srcid + 100000000, feat_id))

            cursor.execute("START TRANSACTION")
            cursor.executemany(update_table_str, update_table_tups)
            cursor.execute("COMMIT")




    def main(self, features_to_update=[]):
        """ main method for Generate_Features_For_Several_Surveys()
        """

        projid_list = [123] #[130] #[123]#, 126]
        #              [126, # ASAS ACVS 20110131 reimport. old:120, # ASAS test (Arien import)
        #               124, # ROTOR TTauri dataset
        #               123, # debosscher3 (2007 paper) 1542 sources
        #               ]

        for project_id in projid_list:
            path_dict = self.make_paths(project_id=project_id)
            self.generate_xmls_and_arff_for_project(project_id=project_id,
                                                    path_dict=path_dict)
            self.insert_arff_into_rdb(project_id=project_id,
                                      arff_fpath=path_dict['tranx_arff_filepath'],
                                      path_dict=path_dict)
        
            self.parse_arff_and_update_feature_tables( \
                                            arff_fpath=path_dict['tranx_arff_filepath'],  #'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/source_feats.arff',
                                            features_to_update=all_feature_name_list,
                                            project_id=project_id)

            import pdb; pdb.set_trace()
            

if __name__ == '__main__':

    #small_feature_name_list = ['freq1_harmonics_freq_0', 'amplitude', 'freq2_harmonics_freq_0', 'freq3_harmonics_freq_0']
    small_feature_name_list = ['freq1_harmonics_amplitude_0', 'freq_signif', 'qso_log_chi2_qsonu', 'qso_log_chi2nuNULL_chi2nu', 'freq1_harmonics_freq_0', 'amplitude', 'freq2_harmonics_freq_0', 'freq3_harmonics_freq_0']

    all_feature_name_list = ['amplitude', 'beyond1std', 'flux_percentile_ratio_mid20', 'flux_percentile_ratio_mid35', 'flux_percentile_ratio_mid50', 'flux_percentile_ratio_mid65', 'flux_percentile_ratio_mid80', 'fold2P_slope_10percentile', 'fold2P_slope_90percentile', 'freq1_harmonics_amplitude_0', 'freq1_harmonics_amplitude_1', 'freq1_harmonics_amplitude_2', 'freq1_harmonics_amplitude_3', 'freq1_harmonics_freq_0', 'freq1_harmonics_rel_phase_0', 'freq1_harmonics_rel_phase_1', 'freq1_harmonics_rel_phase_2', 'freq1_harmonics_rel_phase_3', 'freq2_harmonics_amplitude_0', 'freq2_harmonics_amplitude_1', 'freq2_harmonics_amplitude_2', 'freq2_harmonics_amplitude_3', 'freq2_harmonics_freq_0', 'freq2_harmonics_rel_phase_0', 'freq2_harmonics_rel_phase_1', 'freq2_harmonics_rel_phase_2', 'freq2_harmonics_rel_phase_3', 'freq3_harmonics_amplitude_0', 'freq3_harmonics_amplitude_1', 'freq3_harmonics_amplitude_2', 'freq3_harmonics_amplitude_3', 'freq3_harmonics_freq_0', 'freq3_harmonics_rel_phase_0', 'freq3_harmonics_rel_phase_1', 'freq3_harmonics_rel_phase_2', 'freq3_harmonics_rel_phase_3', 'freq_amplitude_ratio_21', 'freq_amplitude_ratio_31', 'freq_frequency_ratio_21', 'freq_frequency_ratio_31', 'freq_signif', 'freq_signif_ratio_21', 'freq_signif_ratio_31', 'freq_varrat', 'freq_y_offset', 'linear_trend', 'max_slope', 'median_absolute_deviation', 'median_buffer_range_percentage', 'medperc90_2p_p', 'p2p_scatter_2praw', 'p2p_scatter_over_mad', 'p2p_scatter_pfold_over_mad', 'p2p_ssqr_diff_over_var', 'percent_amplitude', 'percent_difference_flux_percentile', 'qso_log_chi2_qsonu', 'qso_log_chi2nuNULL_chi2nu', 'scatter_res_raw', 'skew', 'small_kurtosis', 'std', 'stetson_j', 'stetson_k']

    ### NOTE: most of the RDB parameters were dupliclated from ingest_toolspy::pars{}
    pars = { \
    'tcptutor_hostname':'192.168.1.103', #'lyra.berkeley.edu',
    'tcptutor_username':'dstarr', #'tutor', # guest
    'tcptutor_password':'ilove2mass', #'iamaguest',
    'tcptutor_database':'tutor',
    'tcptutor_port':3306,
    'classdb_hostname':'192.168.1.25', # This is my LOCAL replicated DB
    'classdb_username':'pteluser', #'pteluser',
    'classdb_port':     3306, 
    'classdb_database':'source_test_db', #'source_db',
    'classid_lookup_tablename':'classid_lookup',

    't_sleep':0.2,  # used py populate_feat_db_using_TCPTUTOR_sources.py call of ingest_tools
    'number_threads':10, # used py populate_feat_db_using_TCPTUTOR_sources.py call of ingest_tools
    'tcp_tutor_srcid_offset':100000000,
    'tranx_dirpath_historical_archive_featurexmls_arffs':'/Data/dstarr/Data/historical_archive_featurexmls_arffs', #'/media/raid_0/historical_archive_featurexmls_arffs',
    'lyra3_dirpath_historical_archive_featurexmls_arffs':'/Volumes/Home/pteluser/Sites/historical_archive_featurexmls_arffs',
    }
    #'local_vosource_xml_write_dir':os.path.expandvars('$HOME/scratch/vosource_xml_writedir'),#os.path.expandvars("$TCP_DATA_DIR"),


        
    GenerateFeaturesForSeveralSurveys = Generate_Features_For_Several_Surveys(pars=pars)

    if 0:
        ### Only for the proj_id=123 or small datasets (like debosscher):
        GenerateFeaturesForSeveralSurveys.main(features_to_update=all_feature_name_list) # for generation of features on single machine using threading

    # OBSOLETE OLDER:
    if 0:
        arff_fpath = "/media/raid_0/historical_archive_featurexmls_arffs/tutor_123/2011-05-10_00:27:26.947538/source_feats.arff" # path_dict['tranx_arff_filepath']

        GenerateFeaturesForSeveralSurveys.parse_arff_and_update_feature_tables( \
                                            arff_fpath=arff_fpath,  #'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/source_feats.arff',
                                            features_to_update=all_feature_name_list,
                                            project_id=123)


        sys.exit()

    if 1:
        ### Insert citris33 generated ASAS arff into MySQL RDB
        ### Assuming arff has been copied from citris33 to lyra2:/tmp/citris33_asas.arff
        #project_id = 0 # Use this when the citris33 generated arff contains many TUTOR projects
        project_id=126 # ASAS
        #project_id=121 # SDSS-stipe 82
        path_dict = GenerateFeaturesForSeveralSurveys.make_paths(project_id=project_id)
        scp_str = "scp pteluser@192.168.1.103:/tmp/citris33_asas.arff %s" % (path_dict['tranx_arff_filepath'])
        os.system(scp_str)
        GenerateFeaturesForSeveralSurveys.insert_arff_into_rdb(project_id=project_id,
                                                               arff_fpath=path_dict['tranx_arff_filepath'],
                                                               path_dict=path_dict)
        #import pdb; pdb.set_trace()
        #print

        ### For parsing a citris33 (or any) .arff file for tranx mysql known tutor-project_ids:
        GenerateFeaturesForSeveralSurveys.parse_arff_and_update_feature_tables( \
                                            arff_fpath=path_dict['tranx_arff_filepath'],  #'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/source_feats.arff',
                                            features_to_update=small_feature_name_list, #all_feature_name_list,
                                            do_insert=True, 
                                            project_id=project_id) # project_id=126 # ASAS-ACVS

        #                                    features_to_update=['freq1_harmonics_freq_0',
        #                                                        'freq2_harmonics_freq_0',
        #                                                        'freq3_harmonics_freq_0',
        #                                                        'amplitude'],


    if 0:
        ### This is for just determining which sources exist in one arff and not in another,
        #   and then generate the features for these sources only and write into an arff
        #
        # - TODO: then combine the arffs together.

        full_arff_fpath = "/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-08-17_08:31:25.452093/source_feats.arff"
        partial_arff_fpath = "/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-08-18_16:58:06.668337/source_feats.arff"

        full_srcid_list = GenerateFeaturesForSeveralSurveys.parse_srcids_from_arff(arff_fpath=full_arff_fpath)
        partial_srcid_list = GenerateFeaturesForSeveralSurveys.parse_srcids_from_arff(arff_fpath=partial_arff_fpath)

        missing_srcid_list = list(set(full_srcid_list) - set(partial_srcid_list))#[:10]
        #missing_srcid_list = missing_srcid_list[missing_srcid_list.index(262306)+1:]
        
        n_sources_needed_for_class_inclusion = 1 # this is only used for arff generation (not XML)

        project_id = 126
        schema_id = 10000 + project_id
        xml_write_dirpath="/media/raid_0/temp_xmls"
        out_arff_fpath="/home/pteluser/scratch/asas_eclip_feat_missed_srcids.arff"
        ##### Populate the xmls:
        GenerateFeaturesForSeveralSurveys.pfds.threaded_get_features_populate_rdb(schema_id,
                                                                                  missing_srcid_list,
                                                xml_write_dirpath=xml_write_dirpath)

        ##### Generate ARFF file (taken from generate_weka_classifiers.py):
        ParallelArffMaker = generate_weka_classifiers.Parallel_Arff_Maker(pars={})
        ParallelArffMaker.generate_arff_using_xmls(vosource_xml_dirpath=xml_write_dirpath, \
                                                   out_arff_fpath=out_arff_fpath, \
                                                   n_sources_needed_for_class_inclusion= \
                                                                n_sources_needed_for_class_inclusion)
