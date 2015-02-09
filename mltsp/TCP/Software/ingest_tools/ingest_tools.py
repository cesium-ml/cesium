#!/usr/bin/env python 
###NOTE: This works with Python 2.5.1
"""
   v0.5 More optimized source generation, feature generation.
         - Using epoch-object table scheme 3 : DIF HTM 14,25 object & source tbs
         - PAIRITEL & SDSS-II seamless source, feature population.
   v0.4 Most functions implemented:
         - Using epoch-object table scheme 2 : rtree, htm-25 index tables
         - source identification, and population of 2 tables (no index tb yet)
         - basic XMLRPC connection and source population/query capability
         - random (f,c,r) epoch-object table population
   v0.3 Renamed ingest_tools.py from sdss_fpobjc_parse.py, moved to the
        TCP svn project.  Make TCP software self contained, for multi-node use.
   v0.2 Ingests SDSS & PAIRITEL data, calls photometric pipelines if needed.
         - object/epoch points are placed in RDB.
         - XMLDB phased out until Machine Learning code is integrated.
   v0.1 Initial version: ingests SDSS fits table, places objects into VOEvent
        container, queries and then forms results in simple HTML table output.

Parses SDSS-II fpObjc...fits tables and places individual object information
  in VOEvent'esque containers.

NOTE: RDB database & table creation instructions are printed to stdio during
      sdss_fpobjc_parse.py execution.

   PDB command:
/usr/lib/python2.5/pdb.py ingest_tools.py do_populate_sdss=1

   Common command-line Examples:
./ingest_tools.py do_plot_radec=1 show_plot=yes ra=38.406350 dec=37.625132 degree_range=0.005
./ingest_tools.py do_populate_sdss=1
./ingest_tools.py do_sdss_ingest_radec=1 ra=49.599497 dec=-1.0050998
./ingest_tools.py do_plot_radec=1 show_plot=yes ra=49.599497 dec=-1.0050998 degree_range=0.0333333
./ingest_tools.py do_get_sources_radec=1 ra=49.599497 dec=-1.0050998 degree_range=0.0333333
./ingest_tools.py do_get_source_features_radec=1 ra=49.599497 dec=-1.0050998 degree_range=0.0333333
./ingest_tools.py do_pairitel_pkl_ingest=1 ptel_pkl_fpath=/media/disk/src/voevent/phot.mosGRB.10752.1-2007May21_GRB.10752.1.s9.pkl
"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
#20081020 NOT USED? # import traceback
import glob
from . import dan_utils
try:
    import pyfits
except:
    pass
import datetime
try:
    import MySQLdb
except:
    pass
import copy
import time
import random
try:
    import pylab # For plotting
except:
    pass # fails for webservers, etc which have no X11
###pylab.hold(True) ### These are needed to allow continual poplting scatter()
###pylab.show()     ### These are needed to allow continual poplting scatter()
###       NOTE:  To enable the gradial obj/src plotting, uncomment this and
###              other '###pylab.{scatter,plot}' comments
import numpy 
#import numarray # only for source determining algorithms
import cPickle
from . import obj_id_sockets
import urllib
from . import param_tool
import socket # Just for getting the hostname
#socket.setdefaulttimeout(10) # urllib.urlopen() needs a short timeout forced
from .dan_utils import smon_to_nmon
from . import calculate_ptf_mag

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \

                                'Software/AstroPhot'))
try:
    import sdss_astrophot
except:
    pass
try:
    import ptel_astrophot
except:
    pass
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                'Algorithms/SpatialClustering'))
try:
    import cluster # just for is_object_associated_with_source_algorithm()
except:
    pass

# For: db_importer, feature_extraction_interface:
#sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
#                                      'Software/feature_extract/Code'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code')) # 20071226 dstarr hacks this in

#from Code import db_importer # 20071226 dstarr hacks this in
# NOTE: I think the "from ../package import blah" which Maxime used in "Code" requires Python 2.5+, which means the Lyra/bang* can't do feature extraction (until we upgrade them & that'll be a certain bugaboo)
#if 1:
try:
    from Code import *
except:
    pass # print "Except!: ingest_tools.py : from Code import *"

from . import feature_extraction_interface# NEEDED BY: self.get_src_obj_list() 
#                                               Feature_database()...

new_rdb_col_defs = [\
               {'fits_key':'obj_id',
                'accessor_name':'obj_id',
                'rdb_type':'INT UNSIGNED',
                'fits_ext':-1,
                'internal_type':'internal',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'index_type':'primary',
                'xpath':''},
               {'fits_key':'footprint_id',
                'accessor_name':'footprint_id',
                'rdb_type':'INT UNSIGNED',
                #'rdb_insert_format':"%s",
                'fits_ext':-1,
                'internal_type':'internal',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'index_type':'normal',
                'xpath':'$entry/What/footprint_id'},
               #{'fits_key':'htm',
               # 'accessor_name':'htm',
               # 'rdb_type':'VARBINARY(16)',
               # 'rdb_insert_format':"binary('0x%s')",
               # 'fits_ext':-1,
               # 'internal_type':'internal',
               # 'cooresp_survey':['sdss','pairitel', 'ptf'],
               # 'index_type':'normal',
               # 'xpath':'$entry/What/htm'},
               {'fits_key':'filt',
                'accessor_name':'filt',
                'rdb_type':'TINYINT UNSIGNED',
                'rdb_insert_format':'%s',
                'internal_type':'filt',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/MultiEpochs/Epoch/filt'},
               {'fits_key':'objc_type',
                'accessor_name':'objc_type',
                'rdb_type':'TINYINT UNSIGNED',
                'rdb_insert_format':'%s',
                'fits_ext':1,
                'internal_type':'row_1',
                'cooresp_survey':['sdss'],
                'xpath':'$entry/MultiEpochs/Epoch/objc_type'},
               {'fits_key':'flags',
                'accessor_name':'flags',
                'rdb_type':'INT',
                'rdb_insert_format':'%s',
                'fits_ext':1,
                'internal_type':'row_5',
                'cooresp_survey':['sdss'],
                'xpath':'$entry/MultiEpochs/Epoch/flags'},
               {'fits_key':'flags2',
                'accessor_name':'flags2',
                'rdb_type':'INT',
                'rdb_insert_format':'%s',
                'fits_ext':1,
                'internal_type':'row_5',
                'cooresp_survey':['sdss'],
                'xpath':'$entry/MultiEpochs/Epoch/flags2'},
               {'fits_key':'t',
                'accessor_name':'t',
                'rdb_type':'DOUBLE',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_5',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/MultiEpochs/Epoch/t'},
               {'fits_key':'jsb_mag',
                'accessor_name':'jsb_mag',
                'rdb_type':'FLOAT',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_5',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/MultiEpochs/Epoch/jsb_mag'},
               {'fits_key':'jsb_mag_err',
                'accessor_name':'jsb_mag_err',
                'rdb_type':'FLOAT',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_5',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/MultiEpochs/Epoch/jsb_mag_err'},
               {'fits_key':'ra',
                'accessor_name':'ra',
                'rdb_type':'DOUBLE',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_1',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/What/ra'},
               {'fits_key':'dec',
                'accessor_name':'dec',
                'rdb_type':'DOUBLE',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_1',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'rdb_col_name':'decl',
                'xpath':'$entry/What/dec'},
               {'fits_key':'ra_rms',
                'accessor_name':'ra_rms',
                'rdb_type':'FLOAT',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_1',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/What/ra_rms'},
               {'fits_key':'dec_rms',
                'accessor_name':'dec_rms',
                'rdb_type':'FLOAT',
                'rdb_insert_format':'%s',
                'fits_ext':5,
                'internal_type':'row_1',
                'cooresp_survey':['sdss','pairitel', 'ptf'],
                'xpath':'$entry/What/dec_rms'},
        ]

ptf_candidate_table_columns_tups = \
    [('id','BIGINT'),
     ('sub_id','BIGINT'),
     ('ra','DOUBLE'),
     ('decl','DOUBLE'),# NOTE: need this to be 'decl' since this is used in MySQL table creation, and a .replace() will catch it for PTF PostgreSQL strings
     ('a_image','DOUBLE'),#('a_major_axis','DOUBLE'),
     ('b_image','DOUBLE'),#('b_minor_axis','DOUBLE'),
     ('mag','FLOAT'),#('mag','DOUBLE'),
     ('mag_err','FLOAT'),#('mag_err','DOUBLE'),
     ('flux','DOUBLE'),
     ('flux_err','DOUBLE'),
     ('mag_ref', 'FLOAT'),
     ('mag_ref_err', 'FLOAT'),
     ('flux_aper', 'DOUBLE'),
     ('flux_aper_err', 'DOUBLE'),
     ('f_aper', 'DOUBLE'),
     ('f_aper_err', 'DOUBLE'),
     ('pos_sub', 'TINYINT'),
     #
     ('ra_rms','DOUBLE'),   # REQUIRED, not in PostgreSQL, but is in MySQL table
     ('dec_rms','DOUBLE'),] # REQUIRED, not in PostgreSQL, but is in MySQL table #[0..21]
ptf_sub_table_columns_tups = \
    [('ujd','DOUBLE'), #('ujd_proc_image','DOUBLE'),
     ('filter','VARCHAR(20)'), #('filter_num','INT')
     ('lmt_mg_ref', 'FLOAT'),
     ('lmt_mg_new', 'FLOAT'),
     ('ub1_zp_ref', 'FLOAT'),
     ('ub1_zp_new', 'FLOAT'),
     ('sub_zp', 'DOUBLE'),
     ]
ptf_realbogus_table_columns_tups = \
    [('bogus','FLOAT'),
     ('suspect','FLOAT'),
     ('unclear', 'FLOAT'),
     ('maybe', 'FLOAT'),
     ('realish', 'FLOAT'),
     ('realbogus', 'FLOAT'),
     ]

####
ptf_candidate_table_columns_list = []
for a_tup in ptf_candidate_table_columns_tups:
    ptf_candidate_table_columns_list.append(a_tup[0])

ptf_sub_table_columns_list = []
for a_tup in ptf_sub_table_columns_tups:
    ptf_sub_table_columns_list.append(a_tup[0])

ptf_realbogus_table_columns_list = []
for a_tup in ptf_realbogus_table_columns_tups:
    ptf_realbogus_table_columns_list.append(a_tup[0])


ptf_rdb_columns_list = copy.copy(ptf_candidate_table_columns_list)
ptf_rdb_columns_list.extend(ptf_sub_table_columns_list)
ptf_rdb_columns_list.extend(ptf_realbogus_table_columns_list)

cur_pid = str(os.getpid())
hostname = socket.gethostname()
pars = {\
    'do_test_a':0,
    'do_pairitel_pkl_ingest':0,
    'do_populate_srcid':0,
    'do_get_sources_radec':0,
    'do_get_source_features_radec':0,
    'do_populate_feats_client_loop':0,
    'do_rpc_server':0,
    'do_sdss_ingest_radec':0,
    'do_get_sources_using_xml_file_with_feature_extraction':0,
    'do_delete_existing_featvals':0,
    'do_plot_radec':0,
    'do_populate_sdss':0,
    'ra':49.599497,
    'dec':-1.0050998,
    'degree_range':0.0166666666666 * 10.0, #*20:allows MYSQL to handle 8 on tranx plus probably 6 more populating instances.
    'show_plot':'no', #'yes'
    'vosource_srcid':0,
    'vosource_url':'',
    'obj_same_epoch_dt':datetime.timedelta(seconds=1.0/86400.0), # (day units) NOTE: this should be small since we doubly assume objects are in the same survey if they fall within the same epoch
    'src_create_delay_delta_m':0.2,
    'src_create_delay_realbogus_cut':0.09,  #0.25 is nice but too large
    'src_assoc_sigma_0':60.0, #3.0
    'ptel_pkl_fpath':'',
    'xmlrpc_server_name':"192.168.1.25",
    'xmlrpc_server_port':8008, #8000
    'feature_extracted_vosource_repo_dirpath':os.path.abspath(\
                          os.environ.get("TCP_DATA_DIR") + "feature_vosource"),
    'local_vosource_xml_write_dir':os.path.expandvars('$HOME/scratch/vosource_xml_writedir'),#os.path.expandvars("$TCP_DATA_DIR"),
    'rdb_gen_vosource_urlroot':\
             'http://192.168.1.103/~jbloom/dstarr/vosource_outs',
    'rdb_gen_vosource_dirpath':'/Network/Servers/boom.cluster.private/Home/pteluser/www/dstarr/vosource_outs',
    'rdb_gen_vosource_hostname':'lyra.berkeley.edu',
    'feature_summary_webserver_name':'192.168.1.103',
    'feature_summary_webserver_user':'pteluser',
    'feature_summary_webserver_dirpath':'/Network/Servers/boom.cluster.private/Home/pteluser/www/dstarr/feature_outs',
    'feature_summary_webserver_url_prefix':'http://192.168.1.103/~jbloom/dstarr/feature_outs/',
    'htm_cpp_intersect_exec_fpath':os.path.abspath(os.environ.get("TCP_DIR") +\
                                        'Software/htmIndex_cpp/bin/intersect'),
    'htm_cpp_lookup_exec_fpath':os.path.abspath(os.environ.get("TCP_DIR") + \
                                           'Software/htmIndex_cpp/bin/lookup'),
    'htm_intersect_exec_fpath':os.path.abspath(os.environ.get("TCP_DIR") + \
                                            'Software/htmIndex/bin/intersect'),
    'htm_intersect_scratch_fpath':"/tmp/intersect.domainfile." + cur_pid,
    'htm_lookup_exec_fpath':os.path.abspath(os.environ.get("TCP_DIR") + \
                                        'Software/htmIndex/bin/lookup_HTMout'),
    'htm_id_database_depth':25,
    'htm_id_query_depth':12, #obsolete dbxml
    'srcid_table_name':'srcid_lookup',
    'srcid_table_name_DIF_HTM14':'srcid_lookup_htm',
    'srcid_table_name_DIF_HTM25':'srcid_lookup_htm25xx',
    'degree_threshold_DIFHTM_14_to_25':0.0005555, #Rect side <thresh: HTM25 used
    'srcid_htm_lookup_table_name':'srcid_htm_lookup',
    'srcid_rtree_lookup_table_name':'srcid_rtree_lookup',
    'srcid_feats_done_tablename':'srcid_feats_done',
    'local_tuplist_scratch_dirpath':'/tmp',
    'remote_tuplist_scratch_dirpath':'/tmp',
    'hostname':hostname,
    'cur_pid':cur_pid,
    'obj_index_server_dict':{'sdss':'obj_id',
                             'pairitel':'ptel_obj_id'},
    'obj_srcid_lookup_tablename':'obj_srcid_lookup', #'obj_srcid_lookup_test',
    'ptel_obj_htm_lookup_tablename':'ptel_obj_htm_lookup',
    'ptel_obj_rtree_lookup_tablename':'ptel_obj_rtree_lookup',
    'ptel_ingest_acct_tablename':'pairitel_ingest_accounting',
    'sdss_obj_htm_lookup_tablename':'sdss_obj_htm_lookup',
    'sdss_obj_rtree_lookup_tablename':'sdss_obj_rtree_lookup',
    #'sdss_obj_fcr_lookup_tablename':'sdss_obj_fcr_lookup',
    'survey_id_dict':{'sdss':0,
                      'pairitel':1,
                      'ptf':3},
    'pairitel_filter_num_dict':{'j':5,'h':6,'k':7}, # used by RDB filt column
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
    'src_class_probs_tablename':'src_class_probs',
    'sci_class_schema_id':-1, # Passed during populate_feat_db_using_TCPTUTOR_sources.py calls.  This id represents the features & science-class schema used (when concerning feature and sci-class database accesss)
    # NOTE: The following dict{} contains all class-schema defining parameters:
    #       The class names are hardcode referenced in plugin_classifier.py when filled
    ### NOTE: schema_id == 3 is a default, unused index
    'class_schema_definition_dicts':{ \
        'mlens3 MicroLens':{ \
            'schema_id':0, #1 For Weka, this can be found/generat by code
            'schema_comment':'mlens3 algo gen 0/0/1900',
            'n_features':99, # User keeps these up-to-date:
            'class_list':['single-lens'],#, 'galactic', 'erxtragalactic'],
            'predicts_multiple_classes':False,
            },
        'Dovi SN':{ \
            'schema_id':1, #2 For Weka, this can be found/generat by code
            'schema_comment':'DoviSN algo gen 2/1/2009',
            'n_features':99, # User keeps these up-to-date:
            'class_list':['SN Ia', 'SN CC', 'SN Ibc', 'SN IIP', 'SN IIn'],
            'predicts_multiple_classes':True,
            },
        'General':{ \
            'schema_id':2, #2 For Weka, this can be found/generat by code
            'schema_comment':'Overall classifier 9/1/2009',
            'n_features':99, # User keeps these up-to-date:
            'class_list':['other', 'SN_junk', 'AGN_junk', 'AGN_long_candid', 'SN_long_candid', 'SN_short_candid', 'RBRatio_pass_only', 'RBRatio_nonperiodic_', 'junk', 'rock', 'periodic_variable', 'RBRatio_periodic_can', 'nonRBRatio_long_cand', 'short_candid', 'AGN_short_candid', "RR Lyrae shortperiod", "RR Lyrae longperiod"],
            'predicts_multiple_classes':False,
            },
        '20nois_09epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':41, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_09epch_040need_0.050mtrc_j48_17.9/20nois_09epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_09epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_09epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_10epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':42, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_10epch_040need_0.050mtrc_j48_17.9/20nois_10epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_10epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_10epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_11epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':43, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_11epch_040need_0.050mtrc_j48_17.9/20nois_11epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_11epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_11epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_13epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':44, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_17.9/20nois_13epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_13epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_15epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':45, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_17.9/20nois_15epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_15epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_19epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':47, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_17.9/20nois_19epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_19epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_20epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':48, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_20epch_040need_0.050mtrc_j48_17.9/20nois_20epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_20epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_20epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_21epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':49, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_17.9/20nois_21epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_21epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_23epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':50, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_17.9/20nois_23epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_23epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_25epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':51, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_17.9/20nois_25epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_25epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_27epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':52, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_17.9/20nois_27epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_27epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_29epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':53, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_17.9/20nois_29epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_29epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_33epch_040need_0.050mtrc_j48_17.9':{ \
            'schema_id':54, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_33epch_040need_0.050mtrc_j48_17.9/20nois_33epch_040need_0.050mtrc_j48_17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_33epch_040need_0.050mtrc_j48_17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_33epch_040need_0.050mtrc_j48_17.9',
            'predicts_multiple_classes':True,
            },
        '20nois_13epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':55, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_2.9d/20nois_13epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_13epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_15epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':56, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_2.9d/20nois_15epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_15epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_17epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':57, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_17epch_040need_0.050mtrc_j48_2.9d/20nois_17epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_17epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_17epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_19epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':58, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_2.9d/20nois_19epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_19epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_21epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':59, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_2.9d/20nois_21epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_21epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_23epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':60, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_2.9d/20nois_23epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_23epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_25epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':61, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_2.9d/20nois_25epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_25epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_27epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':62, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_2.9d/20nois_27epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_27epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_29epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':63, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_2.9d/20nois_29epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_29epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_31epch_040need_0.050mtrc_j48_2.9d':{ \
            'schema_id':64, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_31epch_040need_0.050mtrc_j48_2.9d/20nois_31epch_040need_0.050mtrc_j48_2.9d.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_31epch_040need_0.050mtrc_j48_2.9d/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_31epch_040need_0.050mtrc_j48_2.9d',
            'predicts_multiple_classes':True,
            },
        '20nois_13epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':65, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_ptfmod/20nois_13epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_13epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_13epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_15epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':66, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_ptfmod/20nois_15epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_15epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_15epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_17epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':67, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_17epch_040need_0.050mtrc_j48_ptfmod/20nois_17epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_17epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_17epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_19epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':68, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_ptfmod/20nois_19epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_19epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_19epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_21epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':69, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_ptfmod/20nois_21epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_21epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_21epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_23epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':70, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_ptfmod/20nois_23epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_23epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_23epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_25epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':71, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_ptfmod/20nois_25epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_25epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_25epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_27epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':72, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_ptfmod/20nois_27epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_27epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_27epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        '20nois_29epch_040need_0.050mtrc_j48_ptfmod':{ \
            'schema_id':73, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_ptfmod/20nois_29epch_040need_0.050mtrc_j48_ptfmod.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20nois_29epch_040need_0.050mtrc_j48_ptfmod/noisified_for_training.arff'),
            'schema_comment':\
                                              '20nois_29epch_040need_0.050mtrc_j48_ptfmod',
            'predicts_multiple_classes':True,
            },
        },
    'rdb_user':"pteluser",
    #'rdb_host_ip_2':"192.168.1.55",
    #'rdb_name_2':'tcp_db_5', #'tcp_db_2',
    'rdb_host_ip_2':"192.168.1.25",
    'rdb_name_2':'object_test_db', #'tcp_db_2',
    'rdb_port_2':3306,
    'rdb_host_ip_3':"127.0.0.1",
    'rdb_name_3':'object_test_db',
    'rdb_port_3':3306,
    'rdb_table_names':{'sdss':'sdss_events_a', # More optimal object tables
                       'pairitel':'pairitel_events_a',
                       'ptf':'ptf_events'},
    'ptf_object_table_name_DIF_HTM14':'ptf_events_htm',
    'ptf_object_table_name_DIF_HTM25':'ptf_events_htm25xx',
    'ptel_object_table_name_DIF_HTM14':'pairitel_events_a_htm',
    'ptel_object_table_name_DIF_HTM25':'pairitel_events_a_htm25xx',
    'sdss_object_table_name_DIF_HTM14':'sdss_events_a_htm',
    'sdss_object_table_name_DIF_HTM25':'sdss_events_a_htm25xx',
    'ptf_postgre_dbname':'subptf', #'subtest' 'deepsky',
    'ptf_postgre_user':'dstarr',
    'ptf_postgre_host':'sgn02.nersc.gov',#'davinci.nersc.gov',
    'ptf_postgre_password':'*2ta77',
    'ptf_postgre_port':6540, #subtest:6540, 6545
    'ptf_postgre_sub_tablename':'subtraction', # NOTE: also update: 'ptf_postgre_select_columns'
    'ptf_postgre_candidate_tablename':'candidate',
    'ptf_postgre_realbogus_tablename':'rb_classifier',
    'ptf_postgre_realbogus_current_model_id':1,  # NOTE: This is incremented as LBL/Janet/Peter occasionally generate new RealBogus models
    'ptf_mysql_candidate_footprint':'ptf_candidate_footprint',
    #'rdb_host_ip_4':"192.168.1.45", # "192.168.1.65",
    #'rdb_user_4':"pteluser",
    #'rdb_name_4':'tcp_db_4',
    'rdb_host_ip_4':"192.168.1.25", # "192.168.1.65",
    'rdb_user_4':"pteluser",
    'rdb_name_4':'source_test_db',
    'rdb_port_4':3306,
    'rdb_features_host_ip':"127.0.0.1",
    'rdb_features_user':"pteluser",
    'rdb_features_db_name':'source_test_db',
    'rdb_features_port':3306,
    'feat_lookup_tablename':'feat_lookup',
    'feat_values_tablename':'feat_values',
    'sdss_astrom_repo_host_ip':"127.0.0.1",
    'sdss_astrom_repo_user':"pteluser",
    'sdss_astrom_repo_dirpath':'/media/raid_0/sdss_astrom_repository',
    'sdss_astrom_local_dirpath':os.environ.get("TCP_DATA_DIR"),
    'sdss_fields_doc_fpath_list':[\
      os.path.abspath(os.environ.get("TCP_DIR") + 'Data/sdss_run_fields.dat'),\
      os.path.abspath(os.environ.get("TCP_DIR") + 'Data/20070629_tssup_rerun.dat')],
    'sdss_fields_table_name':'rfc_ingest_status',
    'source_region_lock_host_ip':'127.0.0.1',
    'source_region_lock_port':3306,
    'source_region_lock_user':'pteluser',
    'source_region_lock_dbname':'source_test_db',
    'source_region_lock_tablename':'source_region_locks',
    'footprint_host_ip':'127.0.0.1',
    'footprint_port':3306,
    'footprint_user':'pteluser',
    'footprint_dbname':'object_test_db',
    'footprint_regions_tablename':'footprint_regions',
    'footprint_values_tablename':'footprint_values',
    'sdssii_mag_bright_cut':5.0,
    'sdssii_magerr_bad_cut':10.0,
    'footprint_preamble':"""inputFile=;do_bestBox=yes;Submit=Submit%20Request""",
    'sdss_footprint_urls':{'DRSN1':"http://sdssw1.fnal.gov/DRSN1-cgi-bin/FOOT?",
                           'DRsup':"http://sdssw1.fnal.gov/DRsup-cgi-bin/FOOT?"},
    # pre 20090723:
    #'sdss_data_urls':{'DRSN1':"http://das.sdss.org/DRSN1/data/imaging/",
    #                  'DRsup':"http://das.sdss.org/DRsup/data/imaging/"},
    'sdss_data_urls':{'single_catalog':"http://das.sdss.org/imaging/"},
    'filter_conv_dict':{'g':'ptf_g', 'R':'ptf_r'}, # 20091102: This is not used much, just the minor form_vosource_xml_using_rdb.py right now.

    'ptf_filter_num_conv_dict':{'g':8, 'R':9},
    'filters':{0:'u',1:'g',2:'r',3:'i',4:'z',5:'j',6:'h',7:'k',8:'ptf_g',9:'ptf_r',35:'ptf_r'}, #'filters':['u','g','r','i','z','j','h','k','ptf_g','ptf_r'], # cooresponds to RDB 'filt' indexes: [SDSS(5), PTEL(3)]
    'plot_symb':['o','s','v','d','>','<','^'], # '+', 'x','.'
    'plot_fpath_for_source_object_spatial_summary':'',#if len()>0, this .ps fpath will contain a summary of ligtcurve and spactial distribution of objects used to generate a source.
    'result_col_fitskeys':['jsb_mag',
                   'jsb_mag_err',
                   'run',
                   'field',
                   'camcol',
                   'flags',
                   'flags2'],#[] == display all columns.
    'obj_type':{\
        0:'UNK',
        1:'CR',
        2:'DEFECT',
        3:'GALAXY',
        4:'GHOST',
        5:'KNOWNOBJ',
        6:'STAR',
        7:'TRAIL',
        8:'SKY',
        9:'NTYPE',
        },
    'obj1_bitmsk':{\
        'CANONICAL_CENTER':1,
        'BRIGHT':2,
        'EDGE':4,
        'BLENDED':8,
        'CHILD':16,
        'PEAKCENTER':32,
        'NODEBLEND':64,
        'NOPROFILE':128,
        'NOPETRO':256,
        'MANYPETRO':512,
        'NOPETRO_BIG':1024,
        'DEBLEND_TOO_MANY_PEAKS':2048,
        'CR':4096,
        'MANYR50':8192,
        'MANYR90':16384,
        'BAD_RADIAL':32768,
        'INCOMPLETE_PROFILE':65536,
        'INTERP':131072,
        'SATUR':262144,
        'NOTCHECKED':524288,
        'SUBTRACTED':1048576,
        'NOSTOKES':2097152,
        'BADSKY':4194304,
        'PETROFAINT':8388608,
        'TOO_LARGE':16777216,
        'DEBLENDED_AS_PSF':33554432,
        'DEBLEND_PRUNED':67108864,
        'ELLIPFAINT':134217728,
        'BINNED1':268435456,
        'BINNED2':536870912,
        'BINNED4':1073741824,
        'MOVED':-214748364,
        },
    'obj2_bitmsk':{\
        'DEBLENDED_AS_MOVING':1,
        'NODEBLEND_MOVING':2,
        'TOO_FEW_DETECTIONS':4,
        'BAD_MOVING_FIT':8,
        'STATIONARY':16,
        'PEAKS_TOO_CLOSE':32,
        'BINNED_CENTER':64,
        'LOCAL_EDGE':128,
        'BAD_COUNTS_ERROR':256,
        'BAD_MOVING_FIT_CHILD':512,
        'DEBLEND_UNASSIGNED_FLUX':1024,
        'SATUR_CENTER':2048,
        'INTERP_CENTER':4096,
        'DEBLENDED_AT_EDGE':8192,
        'DEBLEND_NOPEAK':16384,
        'PSF_FLUX_INTERP':32768,
        'TOO_FEW_GOOD_DETECTIONS':65536,
        'CENTER_OFF_AIMAGE':131072,
        'DEBLEND_DEGENERATE':262144,
        'BRIGHTEST_GALAXY_CHILD':524288,
        'CANONICAL_BAND':1048576,
        'AMOMENT_UNWEIGHTED':2097152,
        'AMOMENT_SHIFT':4194304,
        'AMOMENT_MAXITER':8388608,
        'MAYBE_CR':16777216,
        'MAYBE_EGHOST':33554432,
        'NOTCHECKED_CENTER':67108864,
        'HAS_SATUR_DN':134217728,
        'DEBLEND_PEEPHOLE':268435456,
        'SPARE3':536870912,
        'SPARE2':1073741824,
        'SPARE1':-2147483648,
    },
    'ptf_postgre_select_columns':("candidate.%s, subtraction.%s, rb_classifier.%s" % (\
              ', candidate.'.join(ptf_candidate_table_columns_list[:-2]), 
              ', subtraction.'.join(ptf_sub_table_columns_list),
              ', rb_classifier.'.join(ptf_realbogus_table_columns_list))).replace('decl','dec'),
    'ptf_rdb_columns_list':ptf_rdb_columns_list,
    'ptf_rdb_select_columns':', '.join(ptf_rdb_columns_list),
    'ptf_rdb_select_columns__t1':'t1.' + ', t1.'.join(ptf_rdb_columns_list),
    'ptf_sub_table_columns_list':ptf_sub_table_columns_list,
    'ptf_candidate_table_columns_list':ptf_candidate_table_columns_list,
    'ptf_candidate_table_columns_tups':ptf_candidate_table_columns_tups,
    'ptf_sub_table_columns_tups':ptf_sub_table_columns_tups,
}

# For debugging where I need to externally invoke a SIGNAL to break code
#    at a sticky spot:
#from signal_break import *
#listen()
###This prints the traceback stack when SIGUSR1 signal is given;
### Eg.:      os.kill(pid, signal.SIGUSR1)
#import signal
#import traceback
#signal.signal(signal.SIGUSR1, lambda sig, stack: traceback.print_stack(stack))


def extract_obj_epoch_from_ptf_query_row(row):
    """ Given a row retrieved from a RDB SELECT of PTF tables, form obj_epoch{}

    NOTE: This assumes SELECTed columns as defined above in string variable:
                                                pars['ptf_rdb_select_columns']
    """
    filt_num = 35 # ptf_r as defined ~ingest_tools.py:430
    if row[19] == 'g':
        filt_num = 8
    else:
        filt_num = 9 # 'R'?        
    obj_epoch = {}
    obj_epoch['flags'] = 0 # PTF defaults
    obj_epoch['flags2'] = 0# PTF defaults
    obj_epoch['objc_type'] = 10 # PTF defaults
    obj_epoch['ra'] = row[2]
    obj_epoch['dec'] = row[3] # select_and_form_objepoch_dict_using_constraint___ptf_case() wants
    obj_epoch['decl'] = row[3] # retrieve_objects_dict_near_radec_where_src0__ptf_specific() wants
    obj_epoch['ra_rms'] = row[17] #arcseconds? # TODO: get from xy_rms?
    obj_epoch['dec_rms'] = row[18]
    obj_epoch['obj_ids'] = [row[0]]
    obj_epoch['src_id'] = 0
    obj_epoch['sub_m'] = row[6]
    obj_epoch['sub_m_err'] = row[7]
    obj_epoch['flux'] = row[8]
    obj_epoch['flux_err'] = row[9]
    obj_epoch['mag_ref'] = row[10]
    obj_epoch['flux_aper'] = row[12]
    obj_epoch['flux_aper_err'] = row[13]
    obj_epoch['f_aper'] = row[14]
    obj_epoch['f_aper_err'] = row[15]
    obj_epoch['mag_ref_err'] = row[11]
    obj_epoch['lmt_mag_ref'] = row[21]
    obj_epoch['lmt_mg_new'] = row[22]
    obj_epoch['ub1_zp_ref'] = row[23]
    obj_epoch['ub1_zp_new'] = row[24]
    obj_epoch['m'] = -2.5 * numpy.log10(obj_epoch['flux_aper'] + obj_epoch['f_aper']) + obj_epoch['ub1_zp_ref']# row[6] # row[10] + row[12]
    obj_epoch['m_err'] = obj_epoch['sub_m_err'] #row[7] # numpy.sqrt((row[13]**2) + (row[11]**2))
    obj_epoch['t'] = row[19] # row[41]
    obj_epoch['filt'] = filt_num # row[38]+8 #ptf_g or ptf_r # select_and_form_objepoch_dict_using_constraint___ptf_case() wants
    obj_epoch['filts'] = [filt_num] #[row[38]+8],#ptf_g or ptf_r # retrieve_objects_dict_near_radec_where_src0__ptf_specific() wants
    obj_epoch['bogus'] = row[26]
    obj_epoch['suspect'] = row[27]
    obj_epoch['unclear'] = row[28]
    obj_epoch['maybe'] = row[29]
    obj_epoch['realish'] = row[30]
    obj_epoch['realbogus'] = row[31]

    #obj_epoch['objid_candid'] = row[         0 ]
    for i in xrange(len(ptf_rdb_columns_list)):
        # conditional is a kludge since PTF tables share some similar column
        #    names as my variables (yuck):
        if ptf_rdb_columns_list[i] not in obj_epoch:
            #obj_epoch[ptf_rdb_columns_list[i]] = row[i]
            obj_epoch[ptf_rdb_columns_list[i]] = [row[i]]
    return obj_epoch


def get_features_using_srcid_xml_tuple_list(srcid_xml_tuple_list, \
                              write_ps=0, ps_fpath='', return_gendict=False, \
                              return_featd_xml_string=False,
                              xmlstring_dict_tofill=None):
        """ Given a list of (integer_source_id, xml_handle);
        where the src_id could just be int(0)  and
        the xml_handle may be either a xml_string or a filepointer/path.

        This function generates features and writes summary PS if flagged.
        """
        from . import feature_extraction_interface

        ##### KLUDGE: 20110710 dstarr adds nomad_color code:
        from .get_colors_for_tutor_sources import Parse_Nomad_Colors_List
        ParseNomadColorsList = Parse_Nomad_Colors_List(fpath=os.path.abspath(os.environ.get("TCP_DIR") + '/Data/best_nomad_src_list'))
        #####

        signals_list = []
        gen = generators_importers.from_xml(signals_list)
	out_srcid_dict = {}
        for (src_id, xml_handle) in srcid_xml_tuple_list:
            # This generates features for the source(s) -> signals_list:

            ##### KLUDGE: 20110710 dstarr adds nomad_color code:
            new_xml_str = ParseNomadColorsList.get_colors_for_srcid(xml_str=xml_handle, srcid=src_id - 100000000)
            #####

            gen.generate(xml_handle=new_xml_str)
            #gen.generate(xml_handle="/home/dstarr/src/TCP/Software/feature_extract/Code/source_5.xml")
            # This generates a plot summary of features for each source:
            # this assert doesn't work when gen.sig.x_sdict['src_id'] is a URI string:
	    #assert(src_id == gen.sig.x_sdict['src_id'])


            if return_gendict:
                out_srcid_dict[src_id] = copy.deepcopy(gen.sig.x_sdict)
            elif return_featd_xml_string:
                gen.sig.add_features_to_xml_string(signals_list)
                out_srcid_dict[src_id] = copy.deepcopy(gen.sig.xml_string)
            else:
                out_srcid_dict[src_id] = {}

            # This is WAY KLUDGEY: If passed in dictionary, here we fill with: {srcid:xml_string}:
            if (type(xmlstring_dict_tofill) == type({})) and not return_featd_xml_string:
                gen.sig.add_features_to_xml_string(signals_list)
                xmlstring_dict_tofill[src_id] = copy.deepcopy(gen.sig.xml_string)

            if (write_ps != 0) or (len(ps_fpath) > 0):
                try:
                    ps = feature_extraction_interface.Plot_Signals(\
                                                         signals_list, gen)
                    if len(ps_fpath) == 0:
                        ps_fpath = "/tmp/feature_plots_srcid_%d.ps" % (src_id)
                    ps.write_multi_filter_ps_files(ps_fpath=ps_fpath)
                except:
                    print("EXCEPT in feature_extraction_interface.Plot_Signals(): no X11?")

        # Here we add the featues to all xml_strings & insert back into
        #         srcid_xml_tuple_list[]
        #db_importer.add_features_to_xml_string(signals_list)
        #for i in xrange(len(srcid_xml_tuple_list)):
        #    src_id = srcid_xml_tuple_list[i][0]
        #    for source_obj in signals_list:
        #        if source_obj.d['src_id'] == src_id:
        #            srcid_xml_tuple_list[i][1] =copy.copy(source_obj.xml_string)
        #            break

            # Another way to do this: have add_reatures_to_xml_string()
            #     pass out all xml_strings (vs srcid)

            # # # # # # # # # # #
            # TODO: Can I get featues here?
            # TODO : I need get_features_using_srcid_xml_tuple_list()
            #    to add extracted features to source_obj.xml_string
            #   - and update passed-in: srcid_xml_tuple_list[]
            #    <<db_importer.py>>.add_features_to_xml_string(signals_list)

        del(gen) # 20081216 DEBUG


	# KLUDGE? I am making the assumption that signals_list == 1 and thus
	#     gen.sig.x_sdict['src_id'] cooresponds to that signal
	#  - if this isn't so, maybe gen.sig.x_sdict['src_id'] changes with each
	#       Plot_signals().write_multi_filter_ps_files()
	assert(len(signals_list) == len(srcid_xml_tuple_list))
        return (signals_list, out_srcid_dict)
        #source_features_list = []
        #for signal_obj in signals_list:
        # here I need to add something which can call the
        #   insert_features_into_databass()
        #return source_features_list


# looks to be unused / obsolete:
def is_object_associated_with_source_algorithm(n_sources, \
                          obj_ra, obj_dec, obj_ra_rms, obj_dec_rms, \
                          src_ra, src_dec, src_ra_rms, src_dec_rms, sigma_0):
    """ Source matching algorithm
    Input: obj & source ra,dec,errors
    Return: True/False conditional result
    """
    midpt = [(obj_ra/obj_ra_rms**2 + \
              src_ra/src_ra_rms**2) / \
             (1.0/obj_ra_rms**2 + \
              1.0/src_ra_rms**2), \
             (obj_dec/obj_dec_rms**2 + \
              src_dec/src_dec_rms**2) / \
             (1.0/obj_dec_rms**2 + \
              1.0/src_dec_rms**2)]    
    cos_dec_term = 1 # the cos term makes no sense if we are zeroing the src coords by subtracting the midpoint coords
    #cos_dec_term = numpy.cos(midpt[1]*numpy.pi/180.0)
    simple_odds = -0.5*((cos_dec_term * (src_ra - midpt[0])/ \
                         (src_ra_rms/3600.0))**2 + \
                        ((src_dec - midpt[1]) / \
                         (src_dec_rms/3600.0))**2) - \
                   0.5*((cos_dec_term * (src_ra - midpt[0]) / \
                         (obj_ra_rms/3600.0))**2 + \
                        ((src_dec - midpt[1]) / \
                         (obj_dec_rms/3600.0))**2)
    sigma_n            = pylab.sqrt(2.0*pylab.log(n_sources))
    return ((-2.828*simple_odds < sigma_n**2 + sigma_0**2),simple_odds,sigma_n)


def show_create_commands(rcd, srcdbt):
    """ Print all MySQL CREATE strings which are needed to set
    """
    for create_str in rcd.create_event_table_str_dict.values():
        print(create_str)
    print(rcd.create_sdss_obj_fcr_lookup_str)
    print(rcd.create_sdss_obj_htm_lookup_str)
    print(rcd.create_sdss_obj_rtree_lookup_str)
    print(rcd.create_ptel_obj_htm_lookup_str)
    print(rcd.create_ptel_obj_rtree_lookup_str)
    print(srcdbt.create_source_table_str) 
    print(srcdbt.create_obj_srcid_lookup_str)
    print(srcdbt.create_srcid_htm_lookup_str)
    print(srcdbt.create_srcid_rtree_lookup_str)


# TODO: Need to find a home for this function.  Used by srcid & objid tasks:
def form_constraint_str_for_rtree_rectangle(ra_low, ra_high, dec_low, dec_high, col_name='radec'):
    """ Given a ra,dec 'rectangle' range, form the conditional constraint
    string which uses rtree/SPATIAL indexed geometry.  Retrun string.
    """
    #(Contains(GeomFromText('POLYGON((0 0, 0 1, 1 1, 2 0, 0 0))'), loc) =1)
    constraint_str = "MBRContains(GeomFromText('POLYGON((%lf %lf, %lf %lf, %lf %lf, %lf %lf, %lf %lf))'), %s)" % (ra_low, dec_high, ra_high, dec_high, ra_high, dec_low, ra_low, dec_low, ra_low, dec_high, col_name)
    return constraint_str


# This class could be contained in a seperate file:
class Source_Region_Lock:
    """ This class is used to handle accounting of which regions are currently
    being 'worked' on.  We are assuming that the activity is rather small,
    infrequent, and not thorough-put critical, so this ID insert is acceptable.

    NOTE: Requires the following TABLE to be created (in source database):

    CREATE TABLE source_region_locks (region_id INT, radec_region GEOMETRY NOT NULL, lock_dtime DATETIME, SPATIAL INDEX(radec_region));

    # TEST with:
        mrl = Source_Region_Lock(rdb_host_ip='192.168.1.65',rdb_user='pteluser', rdb_name='source_db_a', table_name='source_region_locks')

    region_id = mrl.try_lock_region(ra0=55.1,  dec0=30.0, ra1=59.0,  dec1=35.0)
    mrl.unlock_region(region_id)
    """
    def __init__(self, rdb_host_ip='', rdb_user='', rdb_name='', rdb_port=3306, table_name='source_region_locks'):
        # TODO: initiate a MySQL connection.
        self.rdb_host_ip = rdb_host_ip
        self.rdb_user = rdb_user
        self.rdb_name = rdb_name
        self.rdb_port = rdb_port
        self.table_name = table_name
        
        self.db = MySQLdb.connect(host=self.rdb_host_ip, user=self.rdb_user, db=self.rdb_name, port=self.rdb_port)
        self.cursor = self.db.cursor()


    def try_lock_region(self, ra0=-999, dec0=-999, ra1=-999, dec1=-999):
        """ Attempt to lock the region.  Return coorsponding random lock-ID if
        successful.  If can't lock, return -1. 

        NOTE: INSERT fails if spatial region already exists in the lock table
        """
        geom_str = "GeomFromText('POLYGON((%lf %lf, %lf %lf, %lf %lf, %lf %lf, %lf %lf))')" % (ra0, dec1, ra1, dec1, ra1, dec0, ra0, dec0, ra0, dec1)
        # This returns a result when a region in Table "overlaps" this region:
        select_str = "SELECT region_id FROM %s WHERE ((MBRContains(%s,radec_region)) OR (MBREqual(%s,radec_region)) OR (MBRIntersects(%s,radec_region)) OR (MBRWithin(%s,radec_region)))" % (self.table_name, geom_str, geom_str, geom_str, geom_str)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        row_matches = 0
        try:
            if results[0][0] > 0:
                row_matches = 1
        except:
            pass # Nothing matches
        if row_matches == 1:
            return -1 # Tell calling function that this geom confits with RDB

        region_id = numpy.random.random_integers(1000000000) # random & unique
        insert_str = "INSERT INTO %s VALUES (%d, GeomFromText('POLYGON((%lf %lf, %lf %lf, %lf %lf, %lf %lf, %lf %lf))'), NOW())" % (\
            self.table_name, region_id, ra0, dec1, ra1, dec1, ra1, dec0, ra0, dec0, ra0, dec1)
        self.cursor.execute(insert_str)

        select_str = "SELECT region_id FROM %s WHERE (region_id = %d)" % (self.table_name, region_id)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        try:
            if long(results[0][0]) == region_id:
                return region_id
        except:
            pass
        return -1 # Didn't successfully insert new geometry.

    
    def unlock_region(self, region_id):
        """ This will remove the RDB row of the locked region, using lock_id.
        """
        delete_str = "DELETE FROM %s WHERE (region_id = %d)" % (\
                                                  self.table_name, region_id)
        self.cursor.execute(delete_str)


class HTM_Tools:
    """ Singleton object which manages all HTM related methods.

    TODO NOTE(s):
    htmwrap
    /home/pteluser/src/TCP/Software/htm_python_wrapper/htmwrap_module.c

    - malloc() nodes
    - get_radius(nodes...) # This intersects a 'domain' with an HTM-index
        - returns partially and fully intersected nodes.

    get_radius() is found in:
    /home/dstarr/src/HTM_sql/c/
       circle_query.c HTM_query.c HTM_query_HTM.c HTM_query_main.c

    - If I could just call circle_*'s get_radius() function from anywhere
       - Then I could wrap this function in Python.

    See code in /media/usb/src/HTM_sql/c/
     - htm_lookup_module.c htmlookup.py setup.py
     - In order to incorperate get_radius(nodes...) into a python module.
     - ??? I thought there was an already constructed module which 
       wrapped the HTM-id generation.
        - does the existing sdss_fp*py code call this?
        - Maybe this code is in trans1's TCP path?
     - See /media/usb/src/tcp/Software/htmIndex/app on trans1
        - since the python-module install installs the file in /usr/...
        - also, HTM-id test code is just uncommitted & in ~/src/voevent/ on
          trans1
    """
    def __init__(self, pars):
        self.pars = pars
        self.htm_cpp_lookup_exec_fpath = pars['htm_cpp_lookup_exec_fpath']
        self.htm_lookup_exec_fpath = pars['htm_lookup_exec_fpath']
        self.htm_intersect_exec_fpath = pars['htm_intersect_exec_fpath']
        self.htm_intersect_scratch_fpath = pars['htm_intersect_scratch_fpath']
        self.htm_id_depth = pars['htm_id_database_depth']
        
        self.radian_per_degree = (numpy.float64(3.14159265358979323846) /\
                                  numpy.float64(180.0))


    def form_htm_constraint_str_using_htm_ranges(self, htm_ranges, table_prefix=''):
        """ Form SELECT constraint using a list of htm ranges.
        This string can be used within WHERE (%s).
        """
        if table_prefix == '':
            str_mask = "((htm >= binary('0x%s')) and (htm <= binary('0x%s'))) or "
        else:
            str_mask = "((" + table_prefix + ".htm >= binary('0x%s')) and (" + table_prefix + ".htm <= binary('0x%s'))) or "

        constraint_list = []
        for (htm_low,htm_high) in htm_ranges:
            constraint_list.append(str_mask % (htm_low, htm_high))
        constraint_str = ''.join(constraint_list)[:-3] # exclude trailing 'or'
        return constraint_str


    def generate_htm_id(self, ra, dec, htm_id_depth=0):
        """ Generates an HTM ID for the given ra, dec.  
        Uses a simplified version of the HTM C code.
        Returns the HTM-ID
        """
        if htm_id_depth == 0:
            htm_id_depth = self.htm_id_depth
        command_str = "%s %d %lf %lf" % (self.htm_lookup_exec_fpath, \
                                         htm_id_depth, ra, dec)
        (a,b,c) = os.popen3(command_str)
        a.close()
        c.close()
        htm_id = b.read()
        b.close()
        return htm_id
    

    def generate_hex_htm_id(self, ra, dec, htm_id_depth=0):
        """ Generates an HTM ID for the given ra, dec.  
        Uses a simplified version of the HTM C code.
        Returns the HTM-ID
        """
        if htm_id_depth == 0:
            htm_id_depth = self.htm_id_depth
        # kludge: the cpp 'lookup' doesn't like (-) decs, whereas the 'c' does
        if dec < 0: 
            dec += 360
        command_str = "%s -hex %d %lf %lf" % (self.htm_cpp_lookup_exec_fpath, \
                                         htm_id_depth, ra, dec)
        (a,b,c) = os.popen3(command_str)
        a.close()
        c.close()
        lines = b.read().split('\n')
        b.close()
        if len(lines) == 6:
            try:
                htm_id = lines[4].split()[2]
                return htm_id
            except:
                pass
        return '' # Error: HTM-id not found

    
    def get_htmranges_using_radec_box(self,ra_low, ra_high, dec_low, dec_high):
        """ Given a box defined by (ra,dec) ranges, execute an HTM intersect
        for this range, and retrieve the HTM ranges, return in a list of tups.
        NOTE: cpp intersect output looks like:
           dstarr@bin/$ ./intersect -range 15 domain_rect
           Ranges of nodes : 
           3DF5F4401:N3133113310100001 3DF5F4401:N3133113310100001
        """
        domain_file_lines = """#DOMAIN
1
#RECTANGLE_RADEC
%s %s
%s %s
%s %s
%s %s""" % (numpy.str(ra_low), numpy.str(dec_low),\
                    numpy.str(ra_low), numpy.str(dec_high),\
                    numpy.str(ra_high), numpy.str(dec_low),\
                    numpy.str(ra_high), numpy.str(dec_high))
        if os.path.exists(self.htm_intersect_scratch_fpath):
            os.system('rm ' + self.htm_intersect_scratch_fpath)
        fp_scratch = open(self.htm_intersect_scratch_fpath, 'w')
        fp_scratch.writelines(domain_file_lines)
        fp_scratch.close()

        command_str = "%s -range %d %s" % (self.pars['htm_cpp_intersect_exec_fpath'], self.pars['htm_id_database_depth'], self.htm_intersect_scratch_fpath)

        (a,b,c) = os.popen3(command_str)
        a.close()
        c.close()
        raw_str = b.read()
        b.close()

        htm_range_list = []
        raw_lines = raw_str.split('\n')
        for line in raw_lines:
            if ((not 'Ranges of' in line) and (len(line) > 0)):
                htm_range_list.append((line.split()[0].split(':')[0], line.split()[1].split(':')[0]))
        if os.path.exists(self.htm_intersect_scratch_fpath):
            os.system('rm ' + self.htm_intersect_scratch_fpath)
        return htm_range_list


    def get_htmids_using_ra_dec_arcangle(self, ra, dec, arc_angle, \
                                                              htm_id_depth=0):
        """ Given ra, dec, arcangle: Form and write intersect domain
        file; form & execute the intersect code using os.popen3();
        Parse stdout output & place into htm_id list; Return this.

        NOTE: (ra, dec, arc_angle) are in degrees.

        NOTE: this function is a bit of a KLUDGE, since a python-wrapped
              module would be much more effecient, if this is called often.
        """
        bisect_length = numpy.cos(arc_angle * self.radian_per_degree)
        domain_file_lines = """#DOMAIN
1
#CONVEX_RADEC
1
%s %s %s""" % (numpy.str(ra), numpy.str(dec), numpy.str(bisect_length))
        if os.path.exists(self.htm_intersect_scratch_fpath):
            os.system('rm ' + self.htm_intersect_scratch_fpath)
        fp_scratch = open(self.htm_intersect_scratch_fpath, 'w')
        fp_scratch.writelines(domain_file_lines)
        fp_scratch.close()

        if htm_id_depth == 0:
            htm_id_depth = self.htm_id_depth
        ## NOTE: I think the cpp version of 'intersect' (or a custom version?)
        ##    had more options, and produced more simple HTM output:
        ## ?CPP? version:  intersect -verbose -1 -range 2 /tmp/insert.file
        ##command_str = "%s -1 -range %d %s" % (self.htm_intersect_exec_fpath, htm_id_depth, self.htm_intersect_scratch_fpath)
        # C version: ./intersect 15 1 /tmp/jojo
        command_str = "%s %d 1 %s" % (self.htm_intersect_exec_fpath, htm_id_depth, self.htm_intersect_scratch_fpath)

        (a,b,c) = os.popen3(command_str)
        a.close()
        c.close()
        raw_str = b.read()
        b.close()

        htmids_list = []
        raw_lines = raw_str.split('\n')
        for line in raw_lines:
            if ((not 'List of' in line) and (len(line) > 0)):
                elems = line.split()
                htmids_list.append(elems[2])
        return htmids_list


class Empty_Class:
    """ Just an empty, placeholder Class for simple objects.
    """
    def __init__(self):
        pass


class RDB_Column_Defs:
    """ Object which generates and stores all RDB column info, which is 
    refered to by algorithms.
    """
    def __init__(self, rdb_table_names='', rdb_db_name='', \
                 rdb_port=3306, col_definitions=[]):
        # List order defines MySQL database column order:
        self.rdb_db_name = rdb_db_name
        self.rdb_port=rdb_port
        self.rdb_table_names = rdb_table_names
        self.rdb_ind = {}
        self.create_event_table_str_dict = {}
        if len(col_definitions) > 0:
            self.col_definitions = col_definitions
        else:
            self.col_definitions = [] # Currently this is filled later.
            

    def create_obj_rtree_lookup(self, table_name):
        """ Create the MySQL Table which is used for finding obj_ids using
        the MySQL native SPATIAL index (rtree indicies).
        a range of spatial htm indicies.
        Contains columns:
            obj_id & htm, both which have indexes.
        """
        return "CREATE TABLE %s (obj_id INT UNSIGNED, radec GEOMETRY NOT NULL, SPATIAL INDEX(radec), INDEX(obj_id))" % (table_name)


    def create_obj_htm_lookup(self, table_name):
        """ Create the MySQL Table which is used for finding obj_ids for
        a range of spatial htm indicies.
        Contains columns:
            obj_id & htm, both which have indexes.
        """
        return "CREATE TABLE %s (obj_id INT UNSIGNED, htm VARBINARY(16), PRIMARY KEY (obj_id), INDEX(htm))" % (table_name)


    def create_sdss_obj_fcr_lookup(self, table_name):
        """ Create the MySQL Table which is used for finding obj_ids for
        a tuple of (field,camcol,run).
        Contains columns:
            obj_id, rerun, (field, camcol, run)
        primary INDEX: (field, camcol, run)
           - I don't think it'd be any more efficient with sub-index of obj_id
        """
        self.create_sdss_obj_fcr_lookup_str = "CREATE TABLE %s (obj_id INT UNSIGNED, field SMALLINT UNSIGNED, camcol TINYINT UNSIGNED, run SMALLINT UNSIGNED, rerun TINYINT UNSIGNED, INDEX(field, camcol, run))" % (table_name)


    def init_generate_mysql_strings(self, pars):
        """ Generate CREATE, INSERT Mysql string templates.
        These are defined seperatly from __init__() so that
        self.col_definitions can be difined seperatly.
        """
        self.generate_internal_structures('sdss')
        self.generate_internal_structures('pairitel')

        #self.create_sdss_obj_fcr_lookup(pars['sdss_obj_fcr_lookup_tablename'])
        self.create_sdss_obj_htm_lookup_str = \
              self.create_obj_htm_lookup(pars['sdss_obj_htm_lookup_tablename'])
        self.create_sdss_obj_rtree_lookup_str = \
          self.create_obj_rtree_lookup(pars['sdss_obj_rtree_lookup_tablename'])

        self.create_ptel_obj_htm_lookup_str = \
              self.create_obj_htm_lookup(pars['ptel_obj_htm_lookup_tablename'])
        self.create_ptel_obj_rtree_lookup_str = \
          self.create_obj_rtree_lookup(pars['ptel_obj_rtree_lookup_tablename'])


    def generate_internal_structures(self, survey_name):
        """ Generate internal data structures and parameters which are in
        forms needed by external methods.

        NOTE: the association of 'accessor_name' to a column index allows
          external methods (specifically XMLDB construction) to use RDB row
          output lists when contructing XML structures, while using generic
          srcd.ra, srcd.jsb_mag,... references to row indicies.
        """
        self.rdb_ind[survey_name] = Empty_Class()
        create_table_str = "CREATE TABLE %s (" % \
                                           (self.rdb_table_names[survey_name])
        self.rdb_ind[survey_name].insert_str = "INSERT INTO %s (" % \
                                           (self.rdb_table_names[survey_name])
        self.rdb_ind[survey_name].load_str_mask = """LOAD DATA INFILE "%s" INTO TABLE """ + self.rdb_table_names[survey_name] + " ("
        self.rdb_ind[survey_name].rdb_col_list = []
        if survey_name == 'sdss':
            self.sdss_rdb_header_dict = {}
            self.sdss_rdb_row_1_dict = {}
            self.sdss_rdb_row_5_dict = {}

        #20080222
        # A Hack to insert the self-generate indexes:
        #if survey_name == 'sdss':    
        #    self.rdb_ind[survey_name].insert_str += 'obj_id, '
        #    self.rdb_ind[survey_name].insert_str += 'footprint_id, '
        #    insert_suffix = '%d, %d, '
        #elif survey_name == 'pairitel':    
        #    self.rdb_ind[survey_name].insert_str += 'obj_id, '
        #    self.rdb_ind[survey_name].insert_str += 'footprint_id, '
        #    insert_suffix = '%d, %d, '
        #else:
        #    insert_suffix = ''
        ##### 20090403: dstarr comments out 1 line:
        #self.rdb_ind[survey_name].insert_str += 'obj_id, '
        self.rdb_ind[survey_name].insert_str += 'footprint_id, '
        ##### 20090530 dstarr replaces next line:
        #insert_suffix = '%d, %d, '
        insert_suffix = '%d, '

        i = 0 # Used for determining RDB column index
        for col_dict in self.col_definitions:
            if not survey_name in col_dict['cooresp_survey']:
                continue # skip this col_dict: not needed for this survey
            col_name = col_dict['fits_key']

            self.rdb_ind[survey_name].rdb_col_list.append(col_dict['fits_key'])
            if survey_name == 'sdss':                
                if col_dict['internal_type'] == 'header':
                    self.sdss_rdb_header_dict[col_name] = col_dict['fits_ext']
                elif col_dict['internal_type'] == 'row_1':
                    self.sdss_rdb_row_1_dict[col_name] = col_dict['fits_ext']
                elif col_dict['internal_type'] == 'row_5':
                    self.sdss_rdb_row_5_dict[col_name] = col_dict['fits_ext']
            #elif survey_name == 'pairitel':
            #    pass # any special bits, like header or row1 variable addon.

            if 'rdb_col_name' not in col_dict:
                col_dict['rdb_col_name'] = col_dict['fits_key']
            create_table_str += col_dict['rdb_col_name'] + ' ' + \
                                                    col_dict['rdb_type'] + ', '
            if 'rdb_insert_format' in col_dict:
                self.rdb_ind[survey_name].insert_str += \
                                                col_dict['rdb_col_name'] + ', '
                self.rdb_ind[survey_name].load_str_mask += \
                                                col_dict['rdb_col_name'] + ', '
                insert_suffix += col_dict['rdb_insert_format'] + ', '
                #NOTE: I use explicit variable names here to remove dict lookup
                #       when accessing these variables... to speed things up
                exec_str = "self.rdb_ind['" + survey_name + "']." + \
                                    col_dict['accessor_name'] + ' = ' + str(i)
                exec exec_str
                i+= 1
        # Add indicies to CREATE TABLE:  (append as last columns):
        for col_dict in self.col_definitions:
            if col_dict.get('index_type','') == 'normal':
                create_table_str +='INDEX('+col_dict['rdb_col_name']+'), '
            elif col_dict.get('index_type','') == 'unique':
                create_table_str += 'UNIQUE INDEX(' + \
                                                 col_dict['rdb_col_name']+'), '
            elif col_dict.get('index_type','') == 'primary':
                create_table_str +='PRIMARY KEY ('+col_dict['rdb_col_name']+'), '
        create_table_str = create_table_str[:-2] + ')'
        self.rdb_ind[survey_name].insert_str = \
                                  self.rdb_ind[survey_name].insert_str[:-2] + \
                                  ') VALUES (' + insert_suffix[:-2] + ')'
        self.rdb_ind[survey_name].load_str_mask = self.rdb_ind[survey_name].load_str_mask[:-2] + ')'
        #print 'INSERT:', self.rdb_ind[survey_name].insert_str
        #print 'LOAD STRING: ', self.rdb_ind[survey_name].load_str_mask
        #print 'drop table %s;' % (self.rdb_table_names[survey_name])
        self.create_event_table_str_dict[survey_name] = create_table_str + ';'


class Source_Database_Tools:
    """ Singleton object which contains methods for accessing the source-id
    database.

    This class should connect to the mysql database, using the same database
      - but maybe be in-mem, if table is small enough.
    Internal Methods:
      - (a) query & return source-rows for a ra,dec range.
      - (b) generate src-id for unmathced (ra,dec, rms), return src-id
      - (c) given list of ra,dec,rms entries (from epochs-query)
         - condense same obsid-name, filters to single ra,dec epochs entries
         - Get the min & max (ra,dec) of this epoch list, extend range ~+-15rms
         - call (a) to get known source-ids list.
         - for each condensed epoch-entry:
           - call is_observation_associated_with_a_source(condepoch, srcidlist)
           - if no associated srcid:
              - src_id = (b)
              - append new src_id to (source-ids list)
          - if already srcid:
              - update epoch_RDB with srcid, for the 5-associatated epochobsids
    External related method:
      - update epoch rdb with new srcid
         - this epoch will have a (ra, dec, *rms)

    # One use of this class is when a sdss obj-epochs list is ingested into
    #       the epochs table,
    #   - here we retain the epoch info of all datapoints, since they are new
    #   - we reduce the list to (5 filter independent epoch groups)
    #   - Get the min & max (ra,dec) of this epoch list, extend range ~+-15rms
    #   - Query the source-id database for:
    #      - all source-ids in this ra,dec range
    #      - this source_list will be passed into:
    #            is_observation_associated_with_a_source()
    """
    def __init__(self, pars, srcd, htm_tools, rdb_host_ip='', rdb_user='', \
                     rdb_name='', rdb_port=3306, srcid_index_server_pars={}):
        self.pars = pars
        self.srcd = srcd
        self.htm_tools = htm_tools
        self.null_dt_dtime = datetime.timedelta(seconds=0)

        self.rdb_host_ip = rdb_host_ip
        self.rdb_user = rdb_user
        self.rdb_name = rdb_name
        self.rdb_port = rdb_port
        self.db = MySQLdb.connect(host=self.rdb_host_ip, user=self.rdb_user, db=self.rdb_name, port=self.rdb_port)
        self.cursor = self.db.cursor()

        self.create_source_table_str = "CREATE TABLE %s (src_id INT, ra DOUBLE, decl DOUBLE, ra_rms FLOAT, dec_rms FLOAT, nobjs SMALLINT UNSIGNED, PRIMARY KEY (src_id));" % (self.pars['srcid_table_name'])
        self.create_obj_srcid_lookup_str = "CREATE TABLE %s (src_id INT, obj_id INT UNSIGNED, survey_id TINYINT, PRIMARY KEY (survey_id, obj_id), INDEX(src_id));" % (self.pars['obj_srcid_lookup_tablename'])
        #self.create_srcid_rtree_lookup_str = "CREATE TABLE %s (src_id INT, radec GEOMETRY NOT NULL, SPATIAL INDEX(radec), INDEX(src_id))" % (self.pars['srcid_rtree_lookup_table_name'])
        #if len(srcid_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    self.srcid_socket_client = obj_id_sockets.socket_client({}, \
        #                                      server_type='src_id')
        #else:
        #    self.srcid_socket_client = obj_id_sockets.socket_client( \
        #                                      srcid_index_server_pars)


    def retrieve_sources_using_radec_box(self, rdbt, ra_low, ra_high, dec_low,\
                                         dec_high, force_HTM25=0, skip_check_sdss_objs=False,
                                         skip_check_ptel_objs=False, skip_check_ptf_objs=False):
        """ Query and return source-ids for a (ra,dec) range, using HTM.
        """
        #col_name = "%s.radec" % (self.pars['srcid_rtree_lookup_table_name'])
        #constraint_str = form_constraint_str_for_rtree_rectangle(ra_low, ra_high, dec_low, dec_high, col_name=col_name)
        #select_str = "SELECT %s.src_id, %s.ra, %s.decl, %s.ra_rms, %s.dec_rms, %s.nobjs FROM %s JOIN %s USING (src_id) WHERE (%s)" %(\
        #    self.pars['srcid_rtree_lookup_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    self.pars['srcid_rtree_lookup_table_name'], \
        #    self.pars['srcid_table_name'], \
        #    constraint_str)
        if (((ra_high - ra_low) < \
                       self.pars['degree_threshold_DIFHTM_14_to_25']) or \
           ((dec_high - dec_low) < \
                       self.pars['degree_threshold_DIFHTM_14_to_25']) or\
            (force_HTM25 == 1)):
            DIF_HTM_tablename = self.pars['srcid_table_name_DIF_HTM25']
        else:
            DIF_HTM_tablename = self.pars['srcid_table_name_DIF_HTM14']

        constraint_str = "DIF_HTMRectV(%lf, %lf, %lf, %lf)" % (ra_low, dec_low, ra_high, dec_high)
        # NOTE: I've noticed that the HTM Circle-Query may return duplicates.
        select_str = "SELECT DISTINCT src_id, ra, decl, ra_rms, dec_rms, nobjs FROM %s WHERE %s" % (DIF_HTM_tablename, constraint_str)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()

        src_list = []
        for result in results:
            src_list.append({'ra':result[1], 'decl':result[2], 'ra_rms':result[3], 'dec_rms':result[4], 'nobjs':result[5], 'src_id':result[0]})
        # Here I should debug/watch how long this takes:
        objid_to_filt_dict = {}
        objid_to_time_dict = {}
        objid_to_survey_dict = {}
        for src_dict in src_list:
            if rdbt.sdss_tables_available == 1 and (skip_check_sdss_objs==False):
                select_str = "SELECT obj_srcid_lookup.obj_id, %s.filt, %s.t FROM obj_srcid_lookup JOIN %s USING (obj_id) WHERE ((obj_srcid_lookup.survey_id = 0) AND (obj_srcid_lookup.src_id = %s))" % (self.pars['rdb_table_names']['sdss'], self.pars['rdb_table_names']['sdss'], self.pars['rdb_table_names']['sdss'], src_dict['src_id'])
                rdbt.cursor.execute(select_str)
                results = rdbt.cursor.fetchall()
                src_dict['obj_ids'] = []
                for result in results:
                    #src_dict['obj_ids'].append(result[0]) #NOTE:(20080117) ['obj_ids'] don't seem to be used.  For compatability, just a list[] is needed here.  This also means there is no bug with different surveys using the same objid (here, at least).
                    objid_to_filt_dict[result[0]] = result[1]
                    objid_to_time_dict[result[0]] = result[2]
                    objid_to_survey_dict[result[0]] = 0 # 0 == SDSS
            elif rdbt.ptel_tables_available == 1 and (skip_check_ptel_objs==False):
                select_str = "SELECT obj_srcid_lookup.obj_id, %s.filt, %s.t FROM obj_srcid_lookup JOIN %s USING (obj_id) WHERE ((obj_srcid_lookup.survey_id = 1) AND (obj_srcid_lookup.src_id = %s))" % (\
                        self.pars['rdb_table_names']['pairitel'],\
                        self.pars['rdb_table_names']['pairitel'],\
                        self.pars['rdb_table_names']['pairitel'],\
                        src_dict['src_id'])
                rdbt.cursor.execute(select_str)
                results = rdbt.cursor.fetchall()
                src_dict['obj_ids'] = []
                for result in results:
                    #src_dict['obj_ids'].append(result[0]) #NOTE:(20080117) ['obj_ids'] don't seem to be used.  For compatability, just a list[] is needed here.  This also means there is no bug with different surveys using the same objid (here, at least).
                    objid_to_filt_dict[result[0]] = result[1]
                    objid_to_time_dict[result[0]] = result[2]
                    objid_to_survey_dict[result[0]] = 1 # 1 == PAIRITEL
            # (20090727 dstarr added): PTF case is always tried:
            if (skip_check_ptf_objs==False):
                select_str = "SELECT obj_srcid_lookup.obj_id, %s.filter, %s.ujd FROM obj_srcid_lookup JOIN %s ON (obj_srcid_lookup.obj_id=%s.id) WHERE ((obj_srcid_lookup.survey_id = 3) AND (obj_srcid_lookup.src_id = %d))" % (\
                        self.pars['rdb_table_names']['ptf'],\
                        self.pars['rdb_table_names']['ptf'],\
                        self.pars['rdb_table_names']['ptf'],\
                        self.pars['rdb_table_names']['ptf'],\
                        src_dict['src_id'])
                rdbt.cursor.execute(select_str)
                results = rdbt.cursor.fetchall()
                src_dict['obj_ids'] = []
                for result in results:
                    objid_to_filt_dict[result[0]] = self.pars['ptf_filter_num_conv_dict'][result[1]]
                    objid_to_time_dict[result[0]] = result[2]
                    objid_to_survey_dict[result[0]] = 3 # 3 == PTF
        return (src_list, objid_to_filt_dict, objid_to_time_dict, objid_to_survey_dict)


    def insert_new_sources_into_rdb(self, local_srcdbt_sources, \
                 tempsrcid_to_realsrcid, srcindex_tobe_inserted):
        """ For all source(indexes) which are to be inserted into RDB;
        this method forms a large insert string & DB-INSERTs into relevant
        source tables.
        """
        # NOTE: Large INSERTs allow for single compressible interaction with DB
        # NOTE: I chose to ''.join() a list since it is much more effiecient
        #       than iterative string '+=' appends.
        if len(srcindex_tobe_inserted) == 0:
            return # Nothing to do here.
        insert_str_list_source_table = [\
           "INSERT INTO %s (ra, decl, ra_rms, dec_rms, nobjs) VALUES "%\
                                        (self.pars['srcid_table_name'])]
        #insert_str_list_rtree_lookup_table = [\
        #                            "INSERT INTO %s (src_id, radec) VALUES " %\
        #                          (self.pars['srcid_rtree_lookup_table_name'])]
        for src_i in srcindex_tobe_inserted:
            ra = local_srcdbt_sources[src_i]['ra']
            dec = local_srcdbt_sources[src_i]['decl']
            ra_rms = local_srcdbt_sources[src_i]['ra_rms']
            dec_rms = local_srcdbt_sources[src_i]['dec_rms']
            nobjs = local_srcdbt_sources[src_i]['nobjs']
            #src_id = tempsrcid_to_realsrcid[\
            #                             local_srcdbt_sources[src_i]['src_id']]
            insert_str_list_source_table.append(\
                           "(%lf, %lf, %lf, %lf, %d), " % \
                            (ra, dec, ra_rms, dec_rms, nobjs))
            #insert_str_list_rtree_lookup_table.append(\
            #      "(%d, GeomFromText('POINT(%lf %lf)')), " % (src_id, ra, dec))

        self.cursor.execute(''.join(insert_str_list_source_table)[:-2])
        #self.cursor.execute(''.join(insert_str_list_rtree_lookup_table)[:-2])
        self.cursor.execute("SELECT last_insert_id()")
        rows = self.cursor.fetchall()
        if self.cursor.rowcount > 0:
            first_new_row_id = rows[0][0]
        else:
            raise # shouldnt get here
        return (first_new_row_id, first_new_row_id + len(srcindex_tobe_inserted) - 1)


    def update_sources_in_rdb(self, local_srcdbt_sources, \
                              srcindex_tobe_updated):
        """ For all sources which need to be updated in the source RDB;
        this method forms a set of UPDATE commands which are executemany()'d.

        - I'm not sure if executemany() truly sends a single command string
          to the MySQL server (thus compressible), or if it is a python-
          internal command and really executes seperate MySQL commands.
        """
        if len(srcindex_tobe_updated) == 0:
            return # Nothing to do here.
        update_source_table_str = "UPDATE " + self.pars['srcid_table_name'] +\
                                 " SET ra=%s, decl=%s, ra_rms=%s, dec_rms=%s, nobjs=%s WHERE (src_id=%s)"
        #update_rtree_lookup_table_str="UPDATE " + \
        #                         self.pars['srcid_rtree_lookup_table_name'] + \
        #            " SET radec=GeomFromText('POINT(%s %s)') WHERE (src_id=%s)"
        # declare update tup list...
        update_source_table_tups = []
        #update_rtree_lookup_table_tups = []
        
        for src_i in srcindex_tobe_updated:
            src_id = local_srcdbt_sources[src_i]['src_id']
            ra = local_srcdbt_sources[src_i]['ra']
            dec = local_srcdbt_sources[src_i]['decl']
            ra_rms = local_srcdbt_sources[src_i]['ra_rms']
            dec_rms = local_srcdbt_sources[src_i]['dec_rms']
            nobjs = local_srcdbt_sources[src_i]['nobjs']
            # NOTE: for some reason I have to fuss more with UPDATEd htm strs:
            #  for INSERT, just a plain N... str works with: htm=binary('0x%s')
            #  I think this is due to how cursor.executemany() is implemented.
            update_source_table_tups.append(\
                                     (ra, dec, ra_rms, dec_rms, nobjs, src_id))
            #update_rtree_lookup_table_tups.append((ra, dec, src_id))

        self.cursor.executemany(update_source_table_str, \
                                update_source_table_tups)
        #self.cursor.executemany(update_rtree_lookup_table_str, \
        #                        update_rtree_lookup_table_tups)


    def recalc_assoc_srcid(self, obj_dict_compare, src_index,\
             rdb_obj_dict, local_srcdbt_sources):
        """ Recalculate the source position and errors using object-dict.
        Update the RDB row which corresponds with assoc_srcid.
        """
        # NOTE: we must recalculate using values from all associated positions:
        related_objids = []
        for obj_dict in rdb_obj_dict.values():
            if obj_dict['src_id'] == local_srcdbt_sources[src_index]['src_id']:
                related_objids.append(obj_dict)
        related_objids.append(obj_dict_compare) # Include the new assoc object.

        raa = numpy.array([x['ra'] for x in related_objids])
        raerra_2 = numpy.array([x['ra_rms'] for x in related_objids])**2
        deca = numpy.array([x['decl'] for x in related_objids])
        decerra_2 = numpy.array([x['dec_rms'] for x in related_objids])**2
        
        ra  = numpy.sum(raa/raerra_2)/numpy.sum(1.0/raerra_2)
        dec =  numpy.sum(deca/decerra_2)/numpy.sum(1.0/decerra_2)
        raerr  = pylab.sqrt(1.0/numpy.sum(1.0/raerra_2))
        decerr =  pylab.sqrt(1.0/numpy.sum(1.0/decerra_2))

        local_srcdbt_sources[src_index]['ra'] = ra
        local_srcdbt_sources[src_index]['decl'] = dec
        local_srcdbt_sources[src_index]['ra_rms'] = raerr
        local_srcdbt_sources[src_index]['dec_rms'] = decerr
        local_srcdbt_sources[src_index]['nobjs'] += 1


    # ?obsolete? (as of 20080519) : I don't like the conditional agorithms in this.  It seems SDSS already has a lot of dublicat objects with similar magnitudes and almost same time (and same ra,dec). 
    def check_double_source(self, assoc_srcid_dict, objid_to_time_dict, \
                        obj_dict, objid_to_filt_dict, objid_range=20000):
        """ Occasionally we may have an object which is associated with an 
        existing source, but in reality is a second, real source in the same
        filter & frame.  We descern this here so we can create a new source.
        """
        same_epoch_dt_days = self.pars['obj_same_epoch_dt']
        obj_dict_objids = obj_dict['obj_ids']
        obj_dict_t = obj_dict['t']
        n_epoch_matches = 0
        for assoc_src_objid in assoc_srcid_dict['obj_ids']:
            for obj_id in obj_dict_objids:
                if (objid_to_filt_dict[obj_id] == objid_to_filt_dict[\
                                                             assoc_src_objid]):
                    if (abs(obj_id - assoc_src_objid) < objid_range):
                        del_t = datetime.timedelta(seconds=abs(obj_dict_t - \
                                          objid_to_time_dict[assoc_src_objid]))
                        if (del_t == self.null_dt_dtime):
                            return 2 # This duplicate object shouldn't be included into the potential associated source pool.
                        elif (del_t <= same_epoch_dt_days):
                            return 0 # one of the source's object-epochs is from the same 'frame'/tile as this object, so we can't add this object to this source.  This object must become a new source.
        return 1 # OK to add this object to the source


    def check_whether_new_source_to_be_created(self, objs_dict, obj_dict, \
                       odds_list, matching_src_dict,  srcindex_tobe_inserted, \
                           srcindex_tobe_updated, \
                           objid_to_filt_dict, objid_to_time_dict, \
                           local_srcdbt_sources, do_check_double_source=False):
        """ Check whether a new source should be created.
        """
        make_new_source = 1
        for odds_val in odds_list:
            assoc_srcid_dict = matching_src_dict[odds_val]
            src_index = assoc_srcid_dict['src_id']
            # 20080519: dstarr decides to disable "double source check" since the check_double_source() algorithms seem kludgy and it is probably better to have spurious data added to a source then to have that source split arbitrarily among nearby sources (which are most likely parts of that source).
            ###if do_check_double_source or \
            ###   (len(assoc_srcid_dict['obj_ids']) == 0):
            ###    # NOTE: if (len(odds_list) > 0) and (do_check_double_source != 'yes'): 
            ###    #          - we will automatically add to existing src:
            ###    add_obj_to_src = 1
            ###else:
            ###    add_obj_to_src =self.check_double_source(assoc_srcid_dict,\
            ###                  objid_to_time_dict, obj_dict, objid_to_filt_dict)
            ###if add_obj_to_src == 1:
            if True:
                # Do add the object to this source
                matching_src_index = 'blah'
                for test_src_dict in local_srcdbt_sources:
                    if test_src_dict['src_id'] == src_index:
                        #print 7, 'test_src_dict:', test_src_dict
                        matching_src_index = local_srcdbt_sources.index(test_src_dict)
                self.recalc_assoc_srcid(obj_dict, matching_src_index, \
                      objs_dict, local_srcdbt_sources)
                if ((not matching_src_index in srcindex_tobe_inserted) and
                    (not matching_src_index in srcindex_tobe_updated)):
                    srcindex_tobe_updated.append(matching_src_index)
                local_srcdbt_sources[matching_src_index]['obj_ids'].extend(\
                                                   obj_dict['obj_ids'])
                obj_dict['src_id'] = src_index
                make_new_source = 0
                break # get out of the for loop, since obj was added
            ###elif add_obj_to_src == 2:
            ###    print "@@@@ DO NOT ADD or UPDATE source WITH object (add_obj_to_src == 2)"
            ###    # Do not add object to source, or create a new source
            ###    make_new_source = 0
        return make_new_source    

    
    # It appears that this is not used / obsolete:
    def calculate_obj_source_associations_new(self, objs_dict, local_srcdbt_sources, objid_to_filt_dict, objid_to_time_dict, objid_to_survey_dict):
        """ Given objects and existing sources for a ra,dec region; 
	Calculate object associations with existing sources, as well as
	generate new sources when needed.

        DERIVED FROM: calculate_obj_source_associations_original()

        This new version iterativly finds sources & determines the best matches

        TODO: Make sure that variables which should be updated for: return ()
              Are only done once at the very end (when we have a certain set
              of sources...

        TEST by having test_source_reeval.py emulate method like:
                 test_nonthread_nonipython1()
             but instead, have it wrap:
                 calculate_obj_source_associations_original()
             and have it make "prints" of mismatched sources, etc...
	"""
        srcindex_tobe_inserted = []
        srcindex_tobe_updated = []
        orig_objs_dict_list = objs_dict.values()

        # NOTE: Setting of objid_to_filt_dict{}, objid_to_time_dict{}
        #       Should be done only once.
        for obj_dict in objs_dict.values():
            for i in xrange(len(obj_dict['obj_ids'])):
                objid_to_filt_dict[obj_dict['obj_ids'][i]]=obj_dict['filts'][i]
                objid_to_time_dict[obj_dict['obj_ids'][i]] = obj_dict['t']
        objid_to_survey_dict = {} # Not filled with anything useful right now.

        n_iters = 10
        source_structs_list = []
        for i in xrange(n_iters):
            objs_reordered_list = objs_dict.values()
            random.shuffle(objs_reordered_list)

            #####
            source_structs = {'objs_list':objs_reordered_list,
                              'local_srcdbt_sources':local_srcdbt_sources,
                              'objid_to_filt_dict':objid_to_filt_dict,
                              'objid_to_time_dict':objid_to_time_dict,
                              'objid_to_survey_dict':objid_to_survey_dict}
            self.calculate_obj_source_associations_original(
                source_structs['objs_list'],
                local_srcdbt_sources,
                objid_to_filt_dict,
                objid_to_time_dict,
                objid_to_survey_dict)
            #####

            fake_srcid = 0 # This is decremented, so all temporary srcids
            #          are negative.  Before UPDATEing sources, I will determine
            #          Database-valid src-id indexes, and assign them instead.
            skipped_obj_dicts = []


            #TODO: now we do the source finding.  Extract to seperate function?
            for obj_dict_temp in objs_reordered_list:
                #print j, '/', len(objs_dict) #DEBUG
                #j += 1 #DEBUG
                obj_dict = obj_dict_temp
                (odds_list, matching_src_dict) = \
                                         self.is_object_associated_with_source(\
                                                 obj_dict, local_srcdbt_sources)
                do_make_new_source =self.check_whether_new_source_to_be_created(
                                      objs_dict, obj_dict, odds_list,
                                      matching_src_dict, srcindex_tobe_inserted,
                                      srcindex_tobe_updated, objid_to_filt_dict,
                                      objid_to_time_dict, local_srcdbt_sources,
                                      do_check_double_source=True)
                if do_make_new_source == 1:
                    if obj_dict['m_err'] >self.pars['src_create_delay_delta_m']:
                        skipped_obj_dicts.append(obj_dict)
                    else:
                        # Make new source:
                        fake_srcid -= 1
                        associated_srcid = fake_srcid
                        src_dict = {'nobjs':1, \
                            'src_id':fake_srcid, \
                            'ra':obj_dict['ra'], 'decl':obj_dict['decl'], \
                            'ra_rms':obj_dict['ra_rms'], \
                            'dec_rms':obj_dict['dec_rms'],\
                            'obj_ids':obj_dict['obj_ids']}
                        local_srcdbt_sources.append(src_dict)
                        srcindex_tobe_inserted.append(len(local_srcdbt_sources) -1)
                        obj_dict['src_id'] = associated_srcid
            #KLUDGE: I attempt the source finding one more time on skipped objs:
            #    So, the following is duplicate code from above.
            print("Mana mana")
            for obj_dict in skipped_obj_dicts:
                (odds_list, matching_src_dict) = \
                            self.is_object_associated_with_source(\
                                   obj_dict, local_srcdbt_sources)
                # NOTE: if len(odds_list) > 0: we automatic add to existing src:
                do_make_new_source = \
                                   self.check_whether_new_source_to_be_created(\
                                      objs_dict, obj_dict, odds_list,
                                      matching_src_dict, srcindex_tobe_inserted,
                                      srcindex_tobe_updated, objid_to_filt_dict,
                                      objid_to_time_dict, local_srcdbt_sources,
                                      do_check_double_source=False)
                if do_make_new_source == 1:
                    # Make new source:
                    fake_srcid -= 1
                    associated_srcid = fake_srcid
                    src_dict = {'nobjs':1, 'src_id':fake_srcid, 
                                'ra':obj_dict['ra'], 'decl':obj_dict['decl'], 
                                'ra_rms':obj_dict['ra_rms'],
                                'dec_rms':obj_dict['dec_rms'],\
                                'obj_ids':obj_dict['obj_ids']}
                    local_srcdbt_sources.append(src_dict)
                    srcindex_tobe_inserted.append(len(local_srcdbt_sources) - 1)
                    obj_dict['src_id'] = associated_srcid

            # This is useless / redundant:
            srcids_to_ignore = []
            reduced_srcindex_tobe_inserted = []
            for src_i in srcindex_tobe_inserted:
                reduced_srcindex_tobe_inserted.append(src_i)

            #####
            source_structs_list.append(source_structs)
            #NOTE: important vars: (reduced_srcindex_tobe_inserted, srcids_to_ignore)


        # TODO: Algorithmically get the best defined sources.
        #   final-fill structures: (this means intermed structs above are temp)
        #     - local_srcdbt_sources
        #     - srcindex_tobe_updated
        #     - srcindex_tobe_inserted
        #   and return:
        #     (reduced_srcindex_tobe_inserted, srcids_to_ignore)

        #TODO: this "best source Algorithm" should use (a list of) the
        #     resultant structs from xrange(10)

        #return (reduced_srcindex_tobe_inserted, srcids_to_ignore, srcindex_tobe_updated, srcindex_tobe_inserted)


    def calculate_obj_source_associations_original(self, objs_dict, local_srcdbt_sources, objid_to_filt_dict, objid_to_time_dict, objid_to_survey_dict, do_logging=False):
        """ Given objects and existing sources for a ra,dec region; 
	Calculate object associations with existing sources, as well as
	generate new sources when needed.
	"""
        srcindex_tobe_inserted = []
        srcindex_tobe_updated = []
        fake_srcid = 0 # This is decremented, so all temporary srcids
        #          are negative.  Before UPDATEing sources, I will determine
        #          Database-valid src-id indexes, and assign them instead.
        skipped_obj_dicts = []
        for obj_dict_temp in objs_dict.values():
            obj_dict = obj_dict_temp
            for i in range(len(obj_dict['obj_ids'])):
                #objid_to_survey_dict # ????
                objid_to_filt_dict[obj_dict['obj_ids'][i]] = \
                                                           obj_dict['filts'][i]
                objid_to_time_dict[obj_dict['obj_ids'][i]] = obj_dict['t']
            if do_logging:
                print("before:is_object_associated_with_source()")
            (odds_list, matching_src_dict) = \
                                      self.is_object_associated_with_source(\
                                             obj_dict, local_srcdbt_sources)
            if do_logging:
                print("before:check_whether_new_source_to_be_created()")
                print("""objs_dict, obj_dict, odds_list, matching_src_dict, \
                              srcindex_tobe_inserted, srcindex_tobe_updated, \
                              objid_to_filt_dict, objid_to_time_dict, \
                            local_srcdbt_sources""")
                import pprint
                pprint.pprint((objs_dict, obj_dict, odds_list, matching_src_dict, \
                              srcindex_tobe_inserted, srcindex_tobe_updated, \
                              objid_to_filt_dict, objid_to_time_dict, \
                            local_srcdbt_sources))
            do_make_new_source = self.check_whether_new_source_to_be_created(\
                           objs_dict, obj_dict, odds_list, matching_src_dict, \
                              srcindex_tobe_inserted, srcindex_tobe_updated, \
                              objid_to_filt_dict, objid_to_time_dict, \
                            local_srcdbt_sources, do_check_double_source=True)
            if do_make_new_source == 1:
                # 20090601: dstarr adds code so that realbogus is cut with if the obj_dict has that info.
                #if obj_dict['m_err'] > self.pars['src_create_delay_delta_m']:
                #    skipped_obj_dicts.append(obj_dict)
                should_make_source = False
                if 'realbogus' in obj_dict:
                    if obj_dict['realbogus'] >= \
                                     self.pars['src_create_delay_realbogus_cut']:
                        should_make_source = True
                else:
                    if obj_dict['m_err'] <= self.pars['src_create_delay_delta_m']:
                        should_make_source = True
                if not should_make_source:
                    skipped_obj_dicts.append(obj_dict)
                else:
                    # Make new source:
                    fake_srcid -= 1
                    associated_srcid = fake_srcid
                    src_dict = {'nobjs':1, \
                        'src_id':fake_srcid, \
                        'ra':obj_dict['ra'], 'decl':obj_dict['decl'], \
                        'ra_rms':obj_dict['ra_rms'], \
                        'dec_rms':obj_dict['dec_rms'],\
                        'obj_ids':obj_dict['obj_ids']}
                    local_srcdbt_sources.append(src_dict)
                    srcindex_tobe_inserted.append(len(local_srcdbt_sources) -1)
                    obj_dict['src_id'] = associated_srcid
        #KLUDGE: I attempt the source finding one more time on skipped objs:
        #    So, the following is duplicate code from above.
        print("Mana mana")
        for obj_dict in skipped_obj_dicts:
            if do_logging:
                print("before:(2)is_object_associated_with_source()")
            (odds_list, matching_src_dict) = \
                        self.is_object_associated_with_source(\
                               obj_dict, local_srcdbt_sources)
            # NOTE: if len(odds_list) > 0: we automatic add to existing src:
            if do_logging:
                print("before:(2)check_whether_new_source_to_be_created()")
            do_make_new_source = self.check_whether_new_source_to_be_created(\
                           objs_dict, obj_dict, odds_list, matching_src_dict, \
                              srcindex_tobe_inserted, srcindex_tobe_updated,\
                              objid_to_filt_dict, objid_to_time_dict, \
                             local_srcdbt_sources, do_check_double_source=False)
            if do_make_new_source == 1:
                should_make_source = False
                if 'realbogus' in obj_dict:
                    if obj_dict['realbogus'] >= \
                                     self.pars['src_create_delay_realbogus_cut']:
                        should_make_source = True
                if not should_make_source:
                    continue # Do not make source.  Skip this obj_dict

                # Make new source:
                fake_srcid -= 1
                associated_srcid = fake_srcid
                src_dict = {'nobjs':1, 'src_id':fake_srcid, \
                    'ra':obj_dict['ra'], 'decl':obj_dict['decl'], \
                    'ra_rms':obj_dict['ra_rms'],'dec_rms':obj_dict['dec_rms'],\
                    'obj_ids':obj_dict['obj_ids']}
                local_srcdbt_sources.append(src_dict)
                srcindex_tobe_inserted.append(len(local_srcdbt_sources) - 1)
                obj_dict['src_id'] = associated_srcid

        if do_logging:
            print("after:(2)check_whether_new_source_to_be_created()")
        # KLUDGE: I've decided I need to reduce the srcindex_tobe_inserted
        #   list to only include sources where nobjs > 1.  This means
        #   I also need to reset/not update objects which had these
        #   sources associated with them, above.
        srcids_to_ignore = []
        reduced_srcindex_tobe_inserted = []
        for src_i in srcindex_tobe_inserted:
            reduced_srcindex_tobe_inserted.append(src_i)
            # 20080517: dstarr allows nobj>=1 sources by commenting out:
            #if local_srcdbt_sources[src_i]['nobjs'] > 1:
            #    reduced_srcindex_tobe_inserted.append(src_i)
            #else:
            #    srcids_to_ignore.append(local_srcdbt_sources[src_i]['src_id'])
        return (reduced_srcindex_tobe_inserted, srcids_to_ignore, srcindex_tobe_updated, srcindex_tobe_inserted)
	       

    def populate_srcids_using_objs_dict(self, rdbt, objs_dict, \
                                        ra_low, ra_high, dec_low, dec_high, \
                                        skip_check_sdss_objs=False, skip_check_ptel_objs=False, do_logging=False, \
                                        skip_check_ptf_objs=False):
        """ Given a dictionary of object/epochs (filter condensed),
        identify sources and populate/update the source RDB tables with them.
        """
        if len(objs_dict) == 0:
            return

        if do_logging:
            print("before: retrieve_sources_using_radec_box()")

        i_blah = 0
        (local_srcdbt_sources, objid_to_filt_dict, objid_to_time_dict, objid_to_survey_dict) = self.retrieve_sources_using_radec_box(rdbt, ra_low, ra_high, dec_low, dec_high, skip_check_sdss_objs=skip_check_sdss_objs, \
                            skip_check_ptel_objs=skip_check_ptel_objs, skip_check_ptf_objs=skip_check_ptf_objs)

        if do_logging:
            print("before: calculate_obj_source_associations_original()")
            import pprint
            print("objs_dict:")
            pprint.pprint(objs_dict)

            print("local_srcdbt_sources:")
            pprint.pprint(local_srcdbt_sources)

            print("objid_to_filt_dict:")
            pprint.pprint(objid_to_filt_dict)

            print("objid_to_time_dict:")
            pprint.pprint(objid_to_time_dict)

            print("objid_to_survey_dict:")
            pprint.pprint(objid_to_survey_dict)

	##### TODO: replace this wih a smarter source-finding/generating algorm
	##### ::::::::
	(reduced_srcindex_tobe_inserted, srcids_to_ignore, srcindex_tobe_updated, srcindex_tobe_inserted) = \
	         self.calculate_obj_source_associations_original( \
		                   objs_dict, local_srcdbt_sources, 
		     	 	   objid_to_filt_dict, objid_to_time_dict,
				   objid_to_survey_dict, do_logging=do_logging)
	##### ^^^^^^^^^^

        if do_logging:
            print("after: calculate_obj_source_associations_original()")

        tempsrcid_to_realsrcid = {}
        if len(reduced_srcindex_tobe_inserted) > 0:
            #(row_i_low, row_i_high) = self.srcid_socket_client.\
            #                               get_index_range_from_server(\
            #                               len(reduced_srcindex_tobe_inserted))
            print(datetime.datetime.now(), "INSERT:", \
                              len(reduced_srcindex_tobe_inserted), "sources.")
            # ??? Can I delay doing this a couple lines? :
            (row_i_low, row_i_high) = self.insert_new_sources_into_rdb( \
                        local_srcdbt_sources, \
                        tempsrcid_to_realsrcid, reduced_srcindex_tobe_inserted)
            i = 0
            for real_srcid in xrange(row_i_low, row_i_high + 1):
                tempsrcid_to_realsrcid[\
                       local_srcdbt_sources[reduced_srcindex_tobe_inserted[i]]\
                                                       ['src_id']] = real_srcid
                i += 1
        self.update_sources_in_rdb(local_srcdbt_sources, srcindex_tobe_updated)
        rdbt.update_objid_in_rdb(objs_dict, tempsrcid_to_realsrcid, \
                                 srcids_to_ignore)
        print("srcindex_tobe_INSERTed:", reduced_srcindex_tobe_inserted)
        print("srcindex_tobe_UPDATEd:", srcindex_tobe_updated)


    def is_object_associated_with_source(self, obj_dict, sources_list, \
                                             sigma_0=3.0):
        """ This is derived from cluster.is_associated_with_source().
        This returns a 0/1 whether this object is associated with existing
        sources in the srcid-list.

        NOTE: This is to be called by the external "(c)"  method, which finds a source_id for each object.
        INPUT:  obj_dict, sources_list
        OUTPUT: (odds_list, matching_src_dict)
        """
        yes_source = []
        source_odds = []
        matching_src_dict = {}
        so = {}
        for source in sources_list:
            obj_ra = 3600.0 * obj_dict['ra']
            obj_dec = 3600.0 * obj_dict['decl']
            src_ra = 3600.0 * source['ra']
            src_dec = 3600.0 * source['decl']
            (match_bool, simple_odds, sigma_n, midpt) = \
                cluster.is_object_associated_with_source_algorithm_jbloom(\
                    source['nobjs'], \
                    obj_ra, obj_dec, obj_dict['ra_rms'], obj_dict['dec_rms'], \
                    src_ra, src_dec, source['ra_rms'],source['dec_rms'],sigma_0)
            if match_bool:
                matching_src_dict[simple_odds] = source
                yes_source.append(source)
                source_odds.append(simple_odds)

        if len(yes_source) == 0:
            #print ("no association",obj_dict)
            return ([], {})
        else:
            return (matching_src_dict.keys(), matching_src_dict)


    def update_featsgen_in_srcid_lookup_table(self, srcid_list, used_filters_list=[]):
        """ Update feat_gen_date column in srcid_lookup table, for all given
        source-ids.
        """
        for i, src_id in enumerate(srcid_list):
            if len(used_filters_list) > 0:
                update_str = 'UPDATE %s SET feat_gen_date=NOW(), feats_used_filt="%s" WHERE src_id=%d' % (self.pars['srcid_table_name'], used_filters_list[i], src_id)
            else:
                update_str = "UPDATE %s SET feat_gen_date=NOW() WHERE src_id=%d" % (self.pars['srcid_table_name'], src_id)
                
            self.cursor.execute(update_str)


class Rdb_Tools:
    """ Singleton object which contains methods for accessing the single-epoch
    event database.
    """
    def __init__(self, pars, srcd, htm_tools, rdb_host_ip='', rdb_user='', \
                     rdb_name='', rdb_port=3306, \
                                  footprint_index_server_pars={}, \
                                  ptel_obj_index_server_pars={}, \
                                  sdss_obj_index_server_pars={}, \
                                  ptf_obj_index_server_pars={}, \
                                  use_postgre_ptf=False):
        self.use_postgre_ptf = use_postgre_ptf
        self.pars = pars
        self.srcd = srcd
        self.htm_tools = htm_tools
        self.rdb_host_ip = rdb_host_ip
        self.rdb_user = rdb_user
        self.rdb_name = rdb_name
        self.rdb_port = rdb_port

        # Often when many tasks try to make connections at the same time, this fails:
        connection_made = False
        while not connection_made:
            try:
                self.db = MySQLdb.connect(host=self.rdb_host_ip, \
                                          user=self.rdb_user, \
                                          db=self.rdb_name, \
                                          port=self.rdb_port, \
                                          connect_timeout=30) #compress=1, 
                connection_made = True
            except:
                print('! NO Rdb_Tools DB connection! PID(', str(os.getpid()), ')', self.rdb_host_ip, self.rdb_user, self.rdb_name, self.rdb_port)
                time.sleep(0.5) # KLUDGEY
        self.cursor = self.db.cursor()

        if self.use_postgre_ptf:
            # TODO: then we make a postgresql connection here.
            # 20090503 dstarr disables the Postgresql LBL connection:
            """
            import psycopg2
            try:
                self.pg_conn = psycopg2.connect(\
                     "dbname='%s' user='%s' host='%s' password='%s' port=%d" % \
                                    (self.pars['ptf_postgre_dbname'],\
                                     self.pars['ptf_postgre_user'],\
                                     self.pars['ptf_postgre_host'],\
                                     self.pars['ptf_postgre_password'],\
                                     self.pars['ptf_postgre_port']));
                self.pg_conn.set_isolation_level(2)
                # 20090630 This is just a test, used to create cursor for reals here:
                self.pg_cursor = self.pg_conn.cursor()
                self.pg_cursor.close()
            except:
                print 'EXCEPT! Unable to connect to PTF PostgreSQL server:', \
                                                   self.pars['ptf_postgre_host']
            """
            
        self.ptel_ingest_acct_tablename = \
                                        self.pars['ptel_ingest_acct_tablename']
        self.sdss_tables_available = 0 # 1 == <tables are available>
        self.ptel_tables_available = 0 # 1 == <tables are available>
        self.ptf_tables_available = 0 # 1 == <tables are available>
        self.test_table_availability()
        self.srl = Source_Region_Lock(\
                        rdb_host_ip=pars['source_region_lock_host_ip'],\
                        rdb_user=pars['source_region_lock_user'],\
                        rdb_name=pars['source_region_lock_dbname'], \
                        rdb_port=pars['source_region_lock_port'], \
                        table_name=pars['source_region_lock_tablename'])
        self.footprint_db = MySQLdb.connect(\
                                    host=self.pars['footprint_host_ip'], \
                                    user=self.pars['footprint_user'], \
                                    db=self.pars['footprint_dbname'], \
                                    port=self.pars['footprint_port'])
        self.footprint_cursor = self.footprint_db.cursor()

        #if len(footprint_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    self.footprint_socket_client = obj_id_sockets.socket_client({},\
        #                                      server_type='footprint_id')
        #else:
        #    self.footprint_socket_client = obj_id_sockets.socket_client( \
        #                                      footprint_index_server_pars)
        #if len(ptel_obj_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    self.ptel_socket_client = obj_id_sockets.socket_client({},\
        #                                      server_type='ptel_obj_id')
        #else:
        #    self.ptel_socket_client = obj_id_sockets.socket_client( \
        #                                      ptel_obj_index_server_pars)
        #if len(ptf_obj_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    self.ptf_socket_client = obj_id_sockets.socket_client({},\
        #                                      server_type='ptf_obj_id')
        #else:
        #    self.ptf_socket_client = obj_id_sockets.socket_client( \
        #                                      ptf_obj_index_server_pars)
        #if len(sdss_obj_index_server_pars) == 0:
        #    # Default case where no explicit index socket server params given
        #    self.sdss_socket_client = obj_id_sockets.socket_client({},\
        #                                      server_type='obj_id')
        #else:
        #    self.sdss_socket_client = obj_id_sockets.socket_client( \
        #                                      sdss_obj_index_server_pars)

        
    def test_table_availability(self):
        """ Test that tables are available and queriable for each survey
        (SDSS, PAIRITEL, PTF).
        If access/table error, flag that survey unavailable.
        """
        table_names_dict = {\
            'pairitel':[self.pars['obj_srcid_lookup_tablename'],
                        self.pars['rdb_table_names']['pairitel']],
            'ptf':[self.pars['obj_srcid_lookup_tablename'],
                        self.pars['rdb_table_names']['ptf']],
            'sdss':[self.pars['obj_srcid_lookup_tablename'],
                    self.pars['rdb_table_names']['sdss']]}
        for survey_name,table_names in table_names_dict.iteritems():
            n_ok_tables = 0
            for table_name in table_names:
                select_str = "SELECT count(*) FROM %s" % (table_name)
                try:
                    self.cursor.execute(select_str)
                    result = self.cursor.fetchall()
                    try:
                        if result[0][0] >= 0:
                            n_ok_tables += 1
                    except:
                        pass
                except:
                    pass
            if n_ok_tables != len(table_names):
                print('ERROR: test_table_availability(): Unable to load DB:', \
                      survey_name, ':', table_names)
            else:
                if survey_name == 'pairitel':
                    self.ptel_tables_available = 1
                elif survey_name == 'sdss':
                    self.sdss_tables_available = 1
                elif survey_name == 'ptf':
                    self.ptf_tables_available = 1


    def extract_obsid_and_date_from_mosfits_or_pkl(self, file_path, obs_tup=(),\
                                                   filt_name=''):
        """ Extract obsid, date, filt from given (mos*fits fpath) or pickle file
        Then insert these into the Pairitel 'ingested' RDB table.
        NOTE: table contains columns:
            proj VARCHAR(8),
            obj SMALLINT UNSIGNED,
            obs SMALLINT UNSIGNED,
            filt TINYINT UNSIGNED,
            obs_dtime DATETIME
            ingest_dtime DATETIME

        This is KLUDGY since 3 different kind of inputs may occur:
            (proj, obj, obs, date_str, filt_name)
                mosjSN.112.23-2008Feb20.fits
            phot.mosSN.109.25-2008Mar15.pkl    #ASSUME fpath real, to parse filt
            phot.mos.j.SN.109.25-2008Mar15.pkl
        """
        if len(obs_tup) > 0:
            (proj, obj, obs, date_str, filt_name) = obs_tup
        else:
            #     mosjSN.112.23-2008Feb20.fits
            # phot.mosSN.109.25-2008Mar15.pkl
            # phot.mos.j.SN.109.25-2008Mar15.pkl
            fname_nodir = file_path[file_path.rfind('/')+1:]
            fname_noext = fname_nodir[:fname_nodir.rfind('.')]
            if fname_noext[:8] == 'phot.mos':
                x_root = fname_noext[8:]
                # Determine whether filter exists in fname:
                if x_root[0] == '.':
                    filt_name = x_root[1]
                    obs_root = x_root[3:]
                else:
                    # CASE: x_root contains no filter
                    obs_root = x_root
                    fp = open(file_path)
                    temp_pickle = cPickle.load(fp)
                    filt_list = temp_pickle.keys()
                    if len(filt_list) != 1:
                        print("ERROR: pickle file has more than 1 filter:", \
                                                   file_path)
                        raise # FAIL horribly here.
                    filt_name = filt_list[0]
                    fp.close()
            elif (fname_noext[:3] == 'mos'):
                filt_name = fname_noext[3]
                obs_root = fname_noext[4:] # SN.112.23-2008Feb20
            # TODO: at this point we have:
            #       filt_name, obs_root == 'SN.112.23-2008Feb20'
            ind_dot_1 = obs_root.find('.')
            ind_dot_2 = obs_root.find('.',ind_dot_1 + 1)
            ind_hash = obs_root.find('-',ind_dot_2 + 1)
            proj = obs_root[:ind_dot_1]
            obj = obs_root[ind_dot_1 + 1:ind_dot_2]
            obs = obs_root[ind_dot_2 + 1:ind_hash]
            date_str = obs_root[ind_hash + 1:]
        # At this point we have:
        #       (proj, obj, obs, date_str, filt_name)

        filt_num = self.pars['pairitel_filter_num_dict'][filt_name]

        ind_hash_1 = date_str.find('-')
        ind_hash_2 = date_str.find('-',ind_hash_1 + 1)

        # 2007-12-31
        year = date_str[:4]
        mon_str = date_str[4:7]
        day = date_str[7:]
        obs_dtime = "%s-%d-%s" % (year, smon_to_nmon(mon_str), day)
        return (proj, obj, obs, filt_num, obs_dtime)


    def add_obsid_to_ingested_table(self, file_path, obs_tup=(), filt_name=''):
        """ Extract obsid, date, filt from given (mos*fits fpath) or pickle file
        Then insert these into the Pairitel 'ingested' RDB table.
        NOTE: table contains columns:
            proj VARCHAR(8),
            obj SMALLINT UNSIGNED,
            obs SMALLINT UNSIGNED,
            filt TINYINT UNSIGNED,
            obs_dtime DATETIME
            ingest_dtime DATETIME

        This is KLUDGY since 3 different kind of inputs may occur:
            (proj, obj, obs, date_str, filt_name)
                mosjSN.112.23-2008Feb20.fits
            phot.mosSN.109.25-2008Mar15.pkl    #ASSUME fpath real, to parse filt
            phot.mos.j.SN.109.25-2008Mar15.pkl
        """
        (proj, obj, obs, filt_num, obs_dtime) = \
                     self.extract_obsid_and_date_from_mosfits_or_pkl(\
                                file_path, obs_tup=obs_tup, filt_name=filt_name)
        insert_str = "INSERT INTO %s (proj, obj, obs, filt, obs_dtime, ingest_dtime) VALUES ('%s', %s, %s, %d, DATE('%s'), now())" % (self.ptel_ingest_acct_tablename, \
                              proj, str(obj), str(obs), filt_num, obs_dtime)
        self.cursor.execute(insert_str)
        #insert_str = "INSERT INTO %s (mosfits_name, ingest_dtime) VALUES ('%s', now())" % (self.ptel_ingest_acct_tablename, mosfits_name)
        #self.cursor.execute(insert_str)


    def check_obsid_has_been_ingested(self, mosfits_name):
        """ Check whether given Obsid ID string is in the Pairitel 'ingested'
        RDB table.  If so, return 1, if not ingested: return 0.
        mosfits_name  ::  VARCHAR(30)
        ingest_dtime  ::  DATETIME
        """
        (proj, obj, obs, filt_num, obs_dtime) = \
                     self.extract_obsid_and_date_from_mosfits_or_pkl(\
                                                                   mosfits_name)

        #select_str = "SELECT * FROM %s WHERE (mosfits_name = '%s')" % (self.ptel_ingest_acct_tablename, mosfits_name)
        select_str = "SELECT * FROM %s WHERE (proj='%s' AND obj=%d AND obs=%d AND filt=%d and obs_dtime=DATE('%s'))" % \
                     (self.ptel_ingest_acct_tablename, proj, \
                      int(obj), int(obs), filt_num, obs_dtime)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        try:
            if len(results) > 0:
                return 1 # TODO: test that this is hit correctly
        except:
            # We couldn't this mosfits_name from the Table.  Doesn't exist.
            return 0
        return 0

    
    def open_fitstable(self, table_fpath):
        """ Open pyfits table and return return file-pointer
        """
        try:
            fp = pyfits.open(table_fpath)
            if not (fp[1].data.size() > 0):
                print('FAIL: open_fitstable(): bad size', table_fpath)
                raise
            elif len(fp[1].data) != len(fp[5].data):
                print('FITS Table ext1 1,5 len mismatch')
                raise
        except:
            print('ERROR: open_fitstable(): open/parse:', table_fpath)
            traceback.format_exc()
            raise
        return fp


    def get_tup_list_from_sdss_fits_fp(self, fp):
        """ Uses SDSS-II pyfits table to generate a tuple-list for RDB ingest.
        """
        print("insert_fits_fp_data() python code...")
        # I get dict pointers to speed things up:
        ###?this no longer needed???# filter_list = self.pars['filters']
        #20080213 commented out: #ordered_col_list = self.srcd.rdb_ind['sdss'].rdb_col_list[2:]# skip first 3 cols since added explicitly below
        ordered_col_list = self.srcd.rdb_ind['sdss'].rdb_col_list[2:]# skip first 3 cols since added explicitly below
        sdss_header_to_xml = self.srcd.sdss_rdb_header_dict
        sdssrow_to_xml_1_dict = self.srcd.sdss_rdb_row_1_dict
        sdssrow_to_xml_5_dict = self.srcd.sdss_rdb_row_5_dict
        sdssrow_to_xml_5_dict_keys = self.srcd.sdss_rdb_row_5_dict.keys()
        range_filt_list = range(5)

        fcr_field = int(fp[0].header['field'])
        fcr_camcol = int(fp[0].header['camcol'])
        fcr_run = int(fp[0].header['run'])
        fcr_rerun = int(fp[0].header['rerun'])
        fcrr_list = (fcr_field, fcr_camcol, fcr_run, fcr_rerun)

        header_dict = {}
        for fits_key,ext in sdss_header_to_xml.iteritems():
            header_dict[fits_key] = int(fp[ext].header[fits_key]) # KLUDGE: currently assume all interested header values are integer
        len_data = len(fp[1].data)
        tup_list = []
        #obj_id_prefix = 'sdss' + str(header_dict['field']) + '_' + str(header_dict['camcol']) + '_' + str(header_dict['run']) + '_' + str(header_dict['rerun']) + '_' 
        for row_i in xrange(len_data):
            obj_dict = header_dict.copy()
            for fits_key,ext in sdssrow_to_xml_1_dict.iteritems():
                obj_dict[fits_key] = fp[ext].data[row_i].field(fits_key)
            ####htm_id = self.htm_tools.generate_hex_htm_id(obj_dict['ra'], \
            ####   obj_dict['dec'], htm_id_depth=self.pars['htm_id_database_depth'])

            for filt_i in range_filt_list:
                if ((fp[sdssrow_to_xml_5_dict['jsb_mag']].data[row_i].field('jsb_mag')[filt_i] < self.pars['sdssii_mag_bright_cut']) or (fp[sdssrow_to_xml_5_dict['jsb_mag_err']].data[row_i].field('jsb_mag_err')[filt_i] > self.pars['sdssii_magerr_bad_cut'])):
                    continue  # we skip weird valued objects/epochs
                #obj_id = obj_id_prefix + str(row_i) + '_' + str(filt_i)
                #####insert_list = [htm_id]#objid,xmlid,htm
                insert_list = []
                for col_name in ordered_col_list:
                    if col_name in sdssrow_to_xml_5_dict_keys:
                        insert_list.append(fp[sdssrow_to_xml_5_dict[col_name]]\
                                          .data[row_i].field(col_name)[filt_i])
                    elif (col_name == 'filt'):
                        insert_list.append(filt_i)
                    else:
                        insert_list.append(obj_dict[col_name])
                tup_list.append(insert_list)
        return (tup_list, fcrr_list)


    def get_tup_list_from_pairitel_phot_dict(self, phot_dict):
        """ Using Pairitel objects-dict, form object tup_list for later 
        RDB insertion.  Return tup_list

        phot_dict['j']['photometry']['array_header'] = \
                        ['ra', 'dec', 'psf', 'mag', 'merr', 'ra_err', 'dec_err']
        phot_dict['j']['photometry']['data'][obj_ind] = numpy(5) ^^^^^
        """
        #ra_list = []
        #dec_list = []
        filter_num_dict = self.pars['pairitel_filter_num_dict']
        filters = phot_dict.keys() #Usually ['j','h','k'], but possib miss filt

        ordered_col_list = self.srcd.rdb_ind['pairitel'].rdb_col_list[2:]# skip first 3 cols since added explicitly below
        t_val = phot_dict[filters[0]]['time']['mjdmid']
        ###obj_id_prefix = 'ptel' + str(t_val) + '_'

        tup_list = []
        for filt in filters:
            if not phot_dict[filt]['trustworthy_astrometry'] == True:
                continue # skip this filter, since not trustworthy photometry
            elem_i = 0
            filt_num = filter_num_dict[filt]
            for phot_elem in phot_dict[filt]['photometry']['data']:
                obj_dict = {}
                obj_dict['ra'] = phot_elem[0]
                obj_dict['dec'] = phot_elem[1]
                obj_dict['psf'] = phot_elem[2]
                obj_dict['jsb_mag'] = phot_elem[3]
                obj_dict['jsb_mag_err'] = phot_elem[4]
                obj_dict['ra_rms'] = phot_elem[5]
                obj_dict['dec_rms'] = phot_elem[6]
                obj_dict['filt'] = filt_num

                #ra_list.append(obj_dict['ra'])
                #dec_list.append(obj_dict['dec'])

                ###obj_id = obj_id_prefix + str(elem_i) + '_' + str(filt_num)
                #htm_id = self.htm_tools.generate_htm_id(obj_dict['ra'], \
                #  obj_dict['dec'], htm_id_depth=self.pars['htm_id_database_depth'])
                # 20071029: dstarr comments this out:
                #insert_list = [obj_id, '0', htm_id] #objid,dbxmlid,htmid
                #insert_list = [htm_id] #objid,dbxmlid,htmid
                insert_list = [] #objid,dbxmlid,htmid

                for col_name in ordered_col_list:
                    if col_name == 't':
                        insert_list.append(str(t_val))
                    else:
                        insert_list.append(str(obj_dict[col_name]))
                tup_list.append(insert_list)
                # NOTE: this tup_list should mirror: 
                #    self.srcd.rdb_ind['pairitel'].insert_str
                elem_i += 1
        #print "ptel FOV Mean (ra,dec):", sum(ra_list) / len(ra_list), sum(dec_list) / len(dec_list)
        return tup_list


    # 20070913 obsolete (no longer insert into FCR_lookup:
    def rdb_insert_sdss_fcr_lookup_data(self,fcrr_list, row_i_low, row_i_high):
        """ Form & INSERT objid's (f,c,r) info into object/epoch RDB.
        """
        insert_list_fcr_lookup = []
        for obj_id in xrange(row_i_low, row_i_high + 1):
            insert_list_fcr_lookup.append((obj_id, fcrr_list[0], \
                                     fcrr_list[1], fcrr_list[2], fcrr_list[3]))
        insert_str_list_fcr_lookup = []
        insert_str_list_fcr_lookup.append(\
            "INSERT INTO %s (obj_id, field, camcol, run, rerun) VALUES " % \
            (self.pars['sdss_obj_fcr_lookup_tablename']))
        for i in xrange(len(insert_list_fcr_lookup)):
            insert_str_list_fcr_lookup.append(\
                       "(%s, %d, %d, %d, %d), " % (insert_list_fcr_lookup[i]))
        self.cursor.execute(''.join(insert_str_list_fcr_lookup)[:-2])


    def insert_footprints_into_rdb(self, tup_list, limit_mags_dict, survey_num, rdb_ind):
        """ This enters fov region, limiting magnitude information into
        footprint-server tables.
        """
        # KLUDGE: We estimate the Footprint region from just the min/max ra/dec
        # KLUDGE: Since tup_list contains string elements (since this object
        #        was originally intended as object-table INSERT valuses),
        #        I need to kludgily recast to float here:
        ra_list = []
        dec_list = []
        for tup_elem in tup_list:
            ra_list.append(float(tup_elem[rdb_ind.ra]))
            dec_list.append(float(tup_elem[rdb_ind.dec]))

        ra_max = max(ra_list)
        ra_min = min(ra_list)
        dec_max = max(dec_list)
        dec_min = min(dec_list)

        # this should just give 1 index number:
        #(footprint_id, row_i_high) = self.footprint_socket_client.\
        #                                          get_index_range_from_server(1)

        ### TODO: here we should insert a footprint and then retrieve the footprint_id


        #KLUDGE: technically, the footprint covers a time range (SDSS & PTEL)
        t_val = float(tup_list[0][rdb_ind.t])

        # KLUDGY: 20081223 needed:
        filterid_to_filternum = {}
        for filt_num,filt_name in self.pars['filters'].iteritems():
            filterid_to_filternum[filt_name] = filt_num

        # # # # # # #
        # KLUDGE: I should be entering some kind of limiting mags here, for all surveys:
        if len(limit_mags_dict) >0:
            insert_list = ["INSERT INTO %s (footprint_id, filter_id, mag_type, mag_val) VALUES " %  (self.pars['footprint_values_tablename'])]
            for filter_id,filter_mags in limit_mags_dict.iteritems():
                # 20081223: this is list use is obsolete now?: filter_num = self.pars['filters'].index(filter_id)
                filter_num = filterid_to_filternum[filter_id]
                for mag_type, mag_val in filter_mags.iteritems():
                    insert_list.append("(%d, %d, %d, %lf), " % (footprint_id, int(filter_num), int(mag_type), float(mag_val)))
            self.cursor.execute(''.join(insert_list)[:-2])
            self.cursor.execute("SELECT last_insert_id()")
            rows = self.cursor.fetchall()
            if self.cursor.rowcount > 0:
                footprint_id = rows[0][0]
            else:
                raise # shouldnt get here
            
            insert_str = "INSERT INTO %s (footprint_id, survey_id, t, ing_date, radec_region) VALUES (%d, %d, %lf, NOW(), GeomFromText('POLYGON((%lf %lf, %lf %lf, %lf %lf, %lf %lf, %lf %lf))'))" % (self.pars['footprint_regions_tablename'], footprint_id, survey_num, t_val, ra_min, dec_max, ra_max, dec_max, ra_max, dec_min, ra_min, dec_min, ra_min, dec_max)
            self.footprint_cursor.execute(insert_str)
        return footprint_id


    def insert_object_tuplist_into_rdb(self, tup_list=[], fcrr_list=[], \
                 obj_htm_tablename='', obj_rtree_tablename='', survey_name='', \
                 limit_mags_dict={}):
        """ Using a tup list from a SDSS-II object fits-table, executes large
        RDB batch-inserts for each row & color object.
        """
        survey_num = self.pars['survey_id_dict'][survey_name]
        rdb_ind = self.srcd.rdb_ind[survey_name]

        ####
        # 20090530: dstarr disables this since right now we do not have a footprint socket server running, and no-one seems to be using footprint queries of SDSS tables:
        #footprint_id = self.insert_footprints_into_rdb(tup_list, \
        #                                  limit_mags_dict, survey_num, rdb_ind)
        footprint_id = 0
        ####


        #if survey_name == 'pairitel':
        #    (row_i_low, row_i_high) = self.ptel_socket_client.\
        #                             get_index_range_from_server(len(tup_list))
        #elif survey_name == 'ptf':
        #    (row_i_low, row_i_high) = self.ptf_socket_client.\
        #                             get_index_range_from_server(len(tup_list))
        #elif survey_name == 'sdss':
        #    (row_i_low, row_i_high) = self.sdss_socket_client.\
        #                             get_index_range_from_server(len(tup_list))
	#if (row_i_low, row_i_high) == (-1,-1):
	#    return []
        #return_objid_list = range(row_i_low, row_i_high + 1)
        #if survey_name == 'sdss':
        #    self.rdb_insert_sdss_fcr_lookup_data(fcrr_list, row_i_low, \
        #                                                    row_i_high)

        # NOTE: I chose to ''.join() a list since it is much more efficient
        #       than iterative string '+=' appends.
        insert_list_obj_data = []
        insert_list_htm_lookup = []
        insert_list_rtree_lookup = []
        insert_list_srcid_lookup = []
        # KLUDGE: kinda lame to check survey_name in conditional, but....
        #obj_id = row_i_low
        if survey_name == 'sdss':
            for tup_elem in tup_list:
                insert_list_obj_data.append((footprint_id, \
                                             tup_elem[rdb_ind.filt], \
                                             tup_elem[rdb_ind.objc_type], \
                                             tup_elem[rdb_ind.flags], \
                                             tup_elem[rdb_ind.flags2], \
                                             tup_elem[rdb_ind.t], \
                                             tup_elem[rdb_ind.jsb_mag], \
                                             tup_elem[rdb_ind.jsb_mag_err], \
                                             tup_elem[rdb_ind.ra], \
                                             tup_elem[rdb_ind.dec], \
                                             tup_elem[rdb_ind.ra_rms], \
                                             tup_elem[rdb_ind.dec_rms]))
                #insert_list_srcid_lookup.append((obj_id))
                #obj_id += 1
        elif survey_name == 'pairitel':
            for tup_elem in tup_list:
                insert_list_obj_data.append((footprint_id, \
                                             tup_elem[rdb_ind.filt], \
                                             tup_elem[rdb_ind.t], \
                                             tup_elem[rdb_ind.jsb_mag], \
                                             tup_elem[rdb_ind.jsb_mag_err], \
                                             tup_elem[rdb_ind.ra], \
                                             tup_elem[rdb_ind.dec], \
                                             tup_elem[rdb_ind.ra_rms], \
                                             tup_elem[rdb_ind.dec_rms]))
                #insert_list_srcid_lookup.append((obj_id))
                #obj_id += 1
        elif survey_name == 'ptf':
            for tup_elem in tup_list:
                assert(not self.use_postgre_ptf)# only INSERT obj_data in testing, MySQL case.  I place this within the loop since we only get here if actually inserting something.
                insert_list_obj_data.append((footprint_id, \
                                             tup_elem[rdb_ind.filt], \
                                             tup_elem[rdb_ind.t], \
                                             tup_elem[rdb_ind.jsb_mag], \
                                             tup_elem[rdb_ind.jsb_mag_err], \
                                             tup_elem[rdb_ind.ra], \
                                             tup_elem[rdb_ind.dec], \
                                             tup_elem[rdb_ind.ra_rms], \
                                             tup_elem[rdb_ind.dec_rms]))
                #insert_list_srcid_lookup.append((obj_id))
                #obj_id += 1

        obj_data_prefix_i = rdb_ind.insert_str.rfind('VALUES (') + 7
        #obj_data_str_mask = rdb_ind.insert_str[obj_data_prefix_i-1:] + ','
        obj_data_str_mask = rdb_ind.insert_str[obj_data_prefix_i-1:] + ','
        insert_str_list_obj_data = [rdb_ind.insert_str[:obj_data_prefix_i]]
        insert_str_list_srcid_lookup = [\
                      "INSERT INTO %s (obj_id, src_id, survey_id) VALUES " % \
                       (self.pars['obj_srcid_lookup_tablename'])]

        for i in xrange(len(insert_list_obj_data)):
            insert_str_list_obj_data.append(obj_data_str_mask % \
                                             (insert_list_obj_data[i]))

        self.cursor.execute(''.join(insert_str_list_obj_data)[:-1])
        # TODO: now I want to retrieve the object_ids which were used.
        self.cursor.execute("SELECT last_insert_id()")
        rows = self.cursor.fetchall()
        if self.cursor.rowcount > 0:
            row_i_low = rows[0][0]
            row_i_high = row_i_low + len(tup_list) - 1
        else:
            raise # shouldnt get here

        insert_list_srcid_lookup.extend(range(row_i_low, row_i_high + 1))

        for i in xrange(len(insert_list_obj_data)):
            insert_str_list_srcid_lookup.append("(%s, 0, %d), " % \
                                     (insert_list_srcid_lookup[i], survey_num))

        self.cursor.execute(''.join(insert_str_list_srcid_lookup)[:-2])
        return_objid_list = range(row_i_low, row_i_high + 1)
        return return_objid_list


    def get_limiting_mags_from_ptel_photdict(self, phot_dict):
        """ Get the limiting magnitudes from photometry-dict, and return
        in a dictionary.
        """
        limit_mags_dict = {}
        for filt_name,filt_dict in phot_dict.iteritems():
            limit_mags_dict[filt_name] = copy.deepcopy(\
                                             filt_dict['photometry']['limits'])
        return limit_mags_dict


    def get_median_limiting_mags_from_tup_list(self, tup_list, survey_name=''):
        """ Using the tup_list structure, generate somewhat KLUDGY
        median based limiting magnitudes.
        TODO: Ideally, these limiting magnitudes would be 2,5,10-sigma magnituds
        """
        mag_index = self.srcd.rdb_ind[survey_name].jsb_mag
        filt_index = self.srcd.rdb_ind[survey_name].filt
        mag_dict = {}
        for tup_elem in tup_list:
            filt_i = int(tup_elem[filt_index])
            if filt_i not in mag_dict:
                mag_dict[filt_i] = []
            mag_dict[filt_i].append(tup_elem[mag_index])
                
        limit_mags_dict = {}
        for filt_num,mag_list in mag_dict.iteritems():
            mag_list.sort()
            n_mags = len(mag_list)
            m_median_01 = mag_list[int(n_mags * 0.1)]
            m_median_05 = mag_list[int(n_mags * 0.5)]
            m_median_08 = mag_list[int(n_mags * 0.8)]
            m_median_09 = mag_list[int(n_mags * 0.9)]
            filt_name = self.pars['filters'][filt_num]
            limit_mags_dict[filt_name] = {1:m_median_01, \
                                          5:m_median_05, \
                                          8:m_median_08, \
                                          9:m_median_09}
        return limit_mags_dict
    

    # obsolete:
    def get_fov_region_from_phot_dict_objects(self, phot_dict):
        """ Determine the (ra,dec) corner points of the FOV from the span
        of objects contained in phot_dict.
        This is a quick way to estimate the fov's footprint.
        Better methods may use only objects which have magnitudes to some limit
        or, may assume an odd shaped (effective) footprint (as is seen sometimes
        in final Pairitel mosaics).
        """
        # TODO: get fov region from max & min (ra,dec)
        ###########################################################
        # /usr/lib/python2.5/pdb.py test.py

        # TODO: compile an array of ra,dec and sort()
        """
        ra_array = []
        dec_array = []
        for filt in filters:
            if not phot_dict[filt]['trustworthy_astrometry'] == True:
                continue # skip this filter, since not trustworthy photometry
            elem_i = 0
            filt_num = filter_num_dict[filt]
            for phot_elem in phot_dict[filt]['photometry']['data']:
                obj_dict = {}
        """
        pass

    
    def insert_pairitel_astrometry_into_rdb(self,pickle_fpath='',phot_dict={},\
                                            mosfits_fpath=''):

        """ Given a PAIRITEL astrometry pickle file, 
        Insert the objects into RDB.
        """
        if len(pickle_fpath) > 0:
            try:
                fp = open(pickle_fpath)
            except:
                print("Error opening:", pickle_fpath)
                return
            phot_dict = cPickle.load(fp)
            fp.close()
        elif len(phot_dict) == 0:
            print("Error: insert_pairitel_astrometry_into_rdb(): given phot_dict{} is empty.")
            return

        #limit_mags_dict = self.get_limiting_mags_from_ptel_photdict(phot_dict)
        tup_list = self.get_tup_list_from_pairitel_phot_dict(phot_dict)
        limit_mags_dict = self.get_median_limiting_mags_from_tup_list(\
                                           tup_list, survey_name='pairitel')

        objids_list = self.insert_object_tuplist_into_rdb(tup_list=tup_list, \
                       survey_name='pairitel', limit_mags_dict=limit_mags_dict)
        n_ingest = len(objids_list)
        #     obj_htm_tablename=self.pars['ptel_obj_htm_lookup_tablename'], \
        #     obj_rtree_tablename=self.pars['ptel_obj_rtree_lookup_tablename'],\
        if n_ingest == 0:
            print("WARNING: No PAIRITEL data ingested into object-database!")
            #return
        #self.add_obsid_to_ingested_table(mos_globpath[mos_globpath.rfind('/')+1:][:30])
        if len(pickle_fpath) != 0:
            self.add_obsid_to_ingested_table(pickle_fpath)
        else:
            self.add_obsid_to_ingested_table(mosfits_fpath)


    def select_return_rdb_rows(self, select_constraint_str, select_cols='*', \
                                   rdb_table_name='', row_limit=100):
        """ This retrieves some RDB rows, which match the given select
        constraint.  There is a limit to the number of rows returned.
        The results are converted into a known, usable dictionary form.

        NOTE: I am assuming we don't want to retrieve all rows at once, since
              there could be cases where there are many 10000s returned
        """
        select_str = "SELECT " + select_cols + " FROM " + \
                     rdb_table_name + " WHERE " + \
                     select_constraint_str + " LIMIT " + str(row_limit)
        self.cursor.execute(select_str)
        rows = self.cursor.fetchall()
        if self.cursor.rowcount < 1:
            return []
        return rows


        #(collection("%s")/VOEvent[%s]/MultiEpochs/Epoch)
        #return <dan>{data($entry/../../../VOEvent/@uid),data($entry/%s)}</dan>""" % ("test.dbxml", constr_xquery, epoch_elem_str)
        #'data(collection("%s")/VOEvent[%s]/MultiEpochs/Epoch/%s)' % ("test.dbxml", constr_xquery, epoch_elem_str)
        #'data(collection("%s")/VOEvent[%s]/MultiEpochs/Epoch[(filt = %d)]/%s)' % ("test.dbxml", constr_xquery, filter_i, epoch_elem_str)
        #full_xquery = """for $entry in
        #      (collection("%s")/VOEvent[%s]/MultiEpochs/Epoch)
        #      return (data($entry/../../../VOEvent/@uid),data($entry/../../What/ra), data($entry/../../What/dec), data($entry/../../What/htm), data($entry/%s))""" % ("test.dbxml", constr_xquery, epoch_elem_str)


    def get_first_srcid0_object_epoch(self, box_degree_range):
        """ Retrieve the first object where srcid==0.
        Return its (ra,dec)
        NOTE: this now ignores survey tables which have earlier been determined
             as unaccessible.
        NOTE: When iterativly adding sources, this is done in a random way,
           - which could be done more efficiently, say if a tiled patter is used
        TODO: I might want to input a ra,dec range, to get source from (RNDMLY)

        """
        # Kludge: keep trying different random fields, which don't
        #       overlap currently-being-source-populated fields:
        for i in xrange(1000000):
            
            survey_condition_list = []
            if self.sdss_tables_available == 0:
                survey_condition_list.append("(%s.survey_id != %d)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['survey_id_dict']['sdss']))
            if self.ptel_tables_available == 0:
                survey_condition_list.append("(%s.survey_id != %d)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['survey_id_dict']['pairitel']))

            survey_condition = ' AND '.join(survey_condition_list)
            if len(survey_condition) > 0:
                survey_condition = 'AND ' + survey_condition

            rand_row_num = numpy.random.random_integers(100000)
            #select_str = "elect obj_id,survey_id from obj_srcid_lookup WHERE ((obj_srcid_lookup.src_id=0) ) limit 100000,1;

            select_str = "SELECT obj_id, survey_id FROM %s WHERE ((%s.src_id=0) %s) LIMIT %d,1" % (self.pars['obj_srcid_lookup_tablename'], self.pars['obj_srcid_lookup_tablename'], survey_condition, rand_row_num)
            #select_str = "SELECT FLOOR(RAND() * COUNT(*)) FROM %s WHERE ((%s.src_id=0) %s)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['obj_srcid_lookup_tablename'], survey_condition)
            self.cursor.execute(select_str)
            rdb_rows = self.cursor.fetchall()
            if len(rdb_rows) < 1:
                print("NO MORE srcdid==0 ROWS in get_first_srcid0_object_epoch()")
                return (-1,0,0,0,0) # Signal exit.

            #select_str = "SELECT obj_id,survey_id FROM %s LIMIT %d, 1" % (self.pars['obj_srcid_lookup_tablename'], row_number)
            #self.cursor.execute(select_str)
            #rdb_rows = self.cursor.fetchall()
            # KLUDGE Lets just Traceback if we run out of non-source_id'd objects
            obj_id = rdb_rows[0][0]
            survey_id = rdb_rows[0][1]

            if survey_id == self.pars['survey_id_dict']['pairitel']:
                obj_table_name = self.pars['rdb_table_names']['pairitel']
            elif survey_id == self.pars['survey_id_dict']['sdss']:
                obj_table_name = self.pars['rdb_table_names']['sdss']
            
            # KLUDGE: This Tracebacks when no obj_table_name (for debugging/warning)
            select_str ="SELECT HIGH_PRIORITY ra,decl FROM %s WHERE (obj_id=%d)" %\
                                                           (obj_table_name, obj_id)
            self.cursor.execute(select_str)
            rdb_rows = self.cursor.fetchall()
            ra = rdb_rows[0][0]
            dec = rdb_rows[0][1]

            half_range = box_degree_range / 2.0
            ra_low = ra - half_range
            ra_high = ra + half_range
            dec_low = dec - half_range
            dec_high = dec + half_range

            region_id = self.srl.try_lock_region(ra0=ra_low,  dec0=dec_low, \
                                                 ra1=ra_high,  dec1=dec_high)
            if region_id != -1:
                return (ra_low, ra_high, dec_low, dec_high, region_id)
        return (-1,0,0,0,0) # Give up trying to find regions to get sourcesfrm


    # obsolete:
    def get_first_srcid0_object_epoch_old(self):
        """ Retrieve the first object where srcid==0.
        Return its (ra,dec)
        NOTE: this now ignores survey tables which have earlier been determined
             as unaccessible.
        NOTE: When iterativly adding sources, this is done in a random way,
           - which could be done more efficiently, say if a tiled patter is used
        TODO: I might want to input a ra,dec range, to get source from (RNDMLY)

        """
        survey_condition_list = []
        if self.sdss_tables_available == 0:
            survey_condition_list.append("(%s.survey_id != %d)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['survey_id_dict']['sdss']))
        if self.ptel_tables_available == 0:
            survey_condition_list.append("(%s.survey_id != %d)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['survey_id_dict']['pairitel']))

        survey_condition = ' AND '.join(survey_condition_list)
        if len(survey_condition) > 0:
            survey_condition = 'AND ' + survey_condition

        select_str = "SELECT FLOOR(RAND() * COUNT(*)) FROM %s WHERE ((%s.src_id=0) %s)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['obj_srcid_lookup_tablename'], survey_condition)
        self.cursor.execute(select_str)
        rdb_rows = rdbt.cursor.fetchall()
        try:
            row_number = rdb_rows[0][0]
        except:
            row_number = -1
        if row_number < 0:
            print("NO MORE srcdid==0 ROWS in get_first_srcid0_object_epoch()")
            return (-1,-1) # Signal exit.

        select_str = "SELECT obj_id,survey_id FROM %s LIMIT %d, 1" % (self.pars['obj_srcid_lookup_tablename'], row_number)
        #select_str = "SELECT obj_id,survey_id FROM %s WHERE ((%s.src_id=0) %s)" % (self.pars['obj_srcid_lookup_tablename'], self.pars['obj_srcid_lookup_tablename'], survey_condition)
        self.cursor.execute(select_str)
        rdb_rows = rdbt.cursor.fetchall()
        # KLUDGE Lets just Traceback if we run out of non-source_id'd objects
        obj_id = rdb_rows[0][0]
        survey_id = rdb_rows[0][1]

        if survey_id == self.pars['survey_id_dict']['pairitel']:
            obj_table_name = self.pars['rdb_table_names']['pairitel']
        elif survey_id == self.pars['survey_id_dict']['sdss']:
            obj_table_name = self.pars['rdb_table_names']['sdss']
        
        # KLUDGE: This Tracebacks when no obj_table_name (for debugging/warning)
        select_str ="SELECT HIGH_PRIORITY ra,decl FROM %s WHERE (obj_id=%d)" %\
                                                       (obj_table_name, obj_id)
        self.cursor.execute(select_str)
        rdb_rows = rdbt.cursor.fetchall()
        ra = rdb_rows[0][0]
        dec = rdb_rows[0][1]
        return (ra, dec)


    def retrieve_objects_dict_near_radec_where_src0(self, \
                ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1, \
                objepoch_table_name='', obj_rtree_table_name='', survey_id=-1):
        """ Given an ra,dec, and a spatial range, retrieve info from
        all bound objects where srcid==0 (no sources yet associated for them).
        Organize results in a dictionary of unique objects (condense filters).
        Return the object dictionary.
        """
        # NOTE/DEBUG:
        #  - If objects tend to be inserted in the object-epoch database
        #    in the -ra, -dec direction, then retrieving objects starting at
        #    (ra,dec) and contained in a box in the positive ra,dec direction
        #    will tend to select already source-populated boxes.
        #  - I'm assuming objects are inserted in the positive radec direction
        # TODO: test this assertion.
        #col_name = "%s.radec" % (obj_rtree_table_name)
        #constraint_str = form_constraint_str_for_rtree_rectangle(ra_low, ra_high, dec_low, dec_high, col_name=col_name)
        #if do_src0_constraint == 1:
        #    constraint_str = "(%s) and (%s.src_id=0) and (%s.survey_id=%d)" % \
        #            (constraint_str, self.pars['obj_srcid_lookup_tablename'], \
        #             self.pars['obj_srcid_lookup_tablename'], survey_id)
        #select_str = "SELECT HIGH_PRIORITY %s.obj_id, %s.ra, %s.decl, %s.ra_rms, %s.dec_rms, %s.jsb_mag, %s.jsb_mag_err, %s.t, %s.filt FROM %s JOIN %s USING (obj_id) JOIN %s USING (obj_id) WHERE (%s)" % ( \
        #    obj_rtree_table_name,\
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    objepoch_table_name, \
        #    obj_rtree_table_name,\
        #    objepoch_table_name, \
        #    self.pars['obj_srcid_lookup_tablename'], \
        #    constraint_str)
        if do_src0_constraint == 1:
            constraint_str = "(%s.src_id=0) and (%s.survey_id=%d)" % ( \
                  self.pars['obj_srcid_lookup_tablename'], \
                  self.pars['obj_srcid_lookup_tablename'], survey_id)
        else:
            constraint_str = "%s.survey_id=%d" % ( \
                  self.pars['obj_srcid_lookup_tablename'], survey_id)

        ### NOTE: 20080126: There seems to be a MySQL issue in optimizing JOINs
        #    when MySQL functions are used to return intermediate results.
        #    So, this is SLOW:
        #select_str = "SELECT HIGH_PRIORITY %s.obj_id, %s.ra, %s.decl, %s.ra_rms, %s.dec_rms, %s.jsb_mag, %s.jsb_mag_err, %s.t, %s.filt FROM %s JOIN %s USING (obj_id) WHERE (%s)" % ( \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         objepoch_table_name, \
        #         self.pars['obj_srcid_lookup_tablename'], \
        #         constraint_str)
        ### Instead, I KLUDGELY create a temporary table:
        create_str = "CREATE TEMPORARY TABLE blah ENGINE MEMORY select obj_id, ra, decl, ra_rms, dec_rms, jsb_mag, jsb_mag_err, t, filt FROM %s WHERE (DIF_HTMRectV(%lf, %lf, %lf, %lf))" % ( \
                 objepoch_table_name, \
                 ra_low, dec_low, ra_high, dec_high)
        #print '!!!', create_str
        #t0 = datetime.datetime.utcnow()
        self.cursor.execute(create_str)
        #print '   !!!', datetime.datetime.utcnow() - t0
        select_str = "SELECT obj_id, ra, decl, ra_rms, dec_rms, jsb_mag, jsb_mag_err, t, filt FROM blah JOIN %s USING (obj_id) WHERE (%s)" % ( \
                 self.pars['obj_srcid_lookup_tablename'], \
                 constraint_str)
        self.cursor.execute(select_str)
        rdb_rows = self.cursor.fetchall()
        self.cursor.execute("DROP TABLE blah")
        rdb_obj_dict = {}
        for row in rdb_rows:
            # KLUDGE: SDSS & PTEL will have multi-filter samples in a single "object" (since we assume we are ingesting only one FITS frame at a time right here); but for PTF we may recieve two different time samples (same filter) for the same position - which we want to consider seperate "objects".  So, for PTF, we need the dict_key to have time included, whereas SDSS/PTEL the dict_key can be time-invariant in this function.
            if survey_id == 3:
                dict_key = (row[1],row[2],row[3],row[4], row[7], survey_id) # object unique (time is important for this instument's samples)
            else:
                dict_key = (row[1],row[2],row[3],row[4], 0, survey_id) # object unique (all filters will have this key) - each filter is assumed around the same point in time for this instrument
            # TODO: I need to covert t into datetime.
            #    - I need a canned method for mysql-date -> datetime
            if dict_key not in rdb_obj_dict:
                rdb_obj_dict[dict_key] = {'ra':row[1], 'decl':row[2], 'ra_rms':row[3], 'dec_rms':row[4], 'obj_ids':[row[0]], 'src_id':0, 'm':row[5], 'm_err':row[6], 't':row[7], 'filts':[row[8]], 'survey_id':survey_id} #'filt':row[8]
            else:
                rdb_obj_dict[dict_key]['obj_ids'].append(row[0])
                rdb_obj_dict[dict_key]['filts'].append(row[8])
        return rdb_obj_dict


    ############# Revised version: 
    # These queries will interface with LBL's MySQL PTF diff-object database:
    def retrieve_objects_dict_near_radec_where_src0__ptf_specific(self, ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1, objepoch_table_name='', obj_rtree_table_name='', survey_id=-1, do_logging=False):
        """ Given an ra,dec, and a spatial range, retrieve info from
        all bound objects where srcid==0 (no sources yet associated for them).
        Organize results in a dictionary of unique objects (condense filters).
        Return the object dictionary.
        """
        if do_src0_constraint == 1:
            constraint_str = "(%s.src_id=0) and (%s.survey_id=%d)" % ( \
                  self.pars['obj_srcid_lookup_tablename'], \
                  self.pars['obj_srcid_lookup_tablename'], survey_id)
        else:
            constraint_str = "%s.survey_id=%d" % ( \
                  self.pars['obj_srcid_lookup_tablename'], survey_id)

        # NOTE: The JOIN in this is not optimal, making this ideal query perform very slowly (So instead I have to use the CREATE TEMPORARY TABLE route):
        #   SELECT id, sub_id, ra, decl, a_major_axis FROM ptf_events_htm JOIN obj_srcid_lookup ON ptf_events_htm.id=obj_srcid_lookup.obj_id WHERE (DIF_HTMRectV(325.006173, 24.895027, 325.007562, 24.896416) AND obj_srcid_lookup.src_id < 1000000 AND obj_srcid_lookup.survey_id=3);

        #if do_logging:
        #    print "before: CREATE TEMPORARY TABLE"

        ### Instead, I KLUDGELY create a temporary table:
        #create_str = "CREATE TEMPORARY TABLE blah ENGINE MEMORY SELECT %s FROM %s WHERE (DIF_HTMRectV(%lf, %lf, %lf, %lf))" % ( \
        #         self.pars['ptf_rdb_select_columns'], \
        #         objepoch_table_name, \
        #         ra_low, dec_low, ra_high, dec_high)
        #self.cursor.execute(create_str)
        if do_logging:
            print("before: SELECT <ptf columns from local RDB>")
        #select_str = "SELECT %s FROM (SELECT %s FROM %s WHERE (DIF_HTMRectV(%lf, %lf, %lf, %lf))) AS blah JOIN %s ON id=obj_srcid_lookup.obj_id WHERE (%s)" % ( \
        #         self.pars['ptf_rdb_select_columns'], \
        #         self.pars['ptf_rdb_select_columns'], \
        #         objepoch_table_name, \
        #         ra_low, dec_low, ra_high, dec_high,
        #         self.pars['obj_srcid_lookup_tablename'], \
        #         constraint_str)
        select_str = """SELECT %s FROM (SELECT id FROM %s WHERE (DIF_HTMRectV(%lf, %lf, %lf, %lf))) AS blah
        JOIN %s ON blah.id=obj_srcid_lookup.obj_id
        JOIN %s AS t1 ON blah.id=t1.id
        WHERE (%s)""" % ( \
                 self.pars['ptf_rdb_select_columns__t1'], \
                 objepoch_table_name, \
                 ra_low, dec_low, ra_high, dec_high,
                 self.pars['obj_srcid_lookup_tablename'], \
                 self.pars['rdb_table_names']['ptf'], \
                 constraint_str)
        self.cursor.execute(select_str)
        rdb_rows = self.cursor.fetchall()
        #self.cursor.execute("DROP TABLE blah")

        if do_logging:
            print("before: extract_obj_epoch_from_ptf_query_row(row)")
        rdb_obj_dict = {}
        for row in rdb_rows:
            # NOTE: This tuple is only used as a unique identifier, useful
            #      only with multi-filter objects (SDSS...),
            #   So it just needs to be unique for PTF here:
            #          (ra    ,decl  ,ra_rms,decrms, t     , survey_id)
            dict_key = (row[2],row[3],row[8],row[9],row[10], survey_id) # object unique (time is important for this instument's samples)
            # TODO: the above function needs to know the SELECTed columns, which could also be a global string.
            # NOTE: it is important to note that eventually we will be selecting several tables
            # NOTE: here we make the assumption that dict_key is always unique for ptf objects:
            rdb_obj_dict[dict_key] = extract_obj_epoch_from_ptf_query_row(row)
            # # # # 20090828: dstarr disables this since this rdb_obj_dict seems to only
            #      be used for source identification (using positions, realbogus, mag_err only).
            #      So, calibrated mags are not needed, and there is a chance that
            #      some source associated epochs do not yet have pos_sub, sub_zp retrieved from LBL
            #      and ON DUPLICATE UPDATED the mysql ptf_events table.
            #total_mag = calculate_ptf_mag.calculate_total_mag({'f_aper':rdb_obj_dict[dict_key]['f_aper'],
            #                                                   'flux_aper':rdb_obj_dict[dict_key]['flux_aper'],
            #                                                   'ub1_zp_ref':rdb_obj_dict[dict_key]['ub1_zp_ref'],
            #                                                   'mag_ref':rdb_obj_dict[dict_key]['mag_ref'],
            #                                                   'sub_zp':rdb_obj_dict[dict_key]['sub_zp'][0],
            #                                                   'pos_sub':rdb_obj_dict[dict_key]['pos_sub'][0]})
            #rdb_obj_dict[dict_key]['m'] = total_mag

            rdb_obj_dict[dict_key]['survey_id'] = survey_id
        return rdb_obj_dict
    #############


    def update_objid_in_rdb(self, objs_dict, tempsrcid_to_realsrcid, \
                                                             srcids_to_ignore):
        """ For every object-id, rdb UPDATE its associated srcid in the
        obj_srcid_lookup table.  These object-ids should currently have
        srcd_id==0.
        """
        update_obj_srcid_lookup_str = "UPDATE " + \
                            self.pars['obj_srcid_lookup_tablename'] + \
                            " SET src_id=%s WHERE (obj_id=%s and survey_id=%s)"
        update_obj_srcid_lookup_tups = []
        for obj_dict in objs_dict.values():
            for obj_id in obj_dict['obj_ids']:
                src_id = obj_dict['src_id']
                # Bug:
                #if ((src_id < 0) and (src_id not in srcids_to_ignore)):
                #    update_obj_srcid_lookup_tups.append(\
                #         (tempsrcid_to_realsrcid[src_id], obj_id,\
                #          obj_dict['survey_id']))
                #else:
                #    update_obj_srcid_lookup_tups.append(\
                #         (src_id, obj_id, obj_dict['survey_id']))

                if (src_id < 0):
                    if (src_id not in srcids_to_ignore):
                        update_obj_srcid_lookup_tups.append(\
                            (tempsrcid_to_realsrcid[src_id], obj_id,\
                             obj_dict['survey_id']))
                else:
                    update_obj_srcid_lookup_tups.append(\
                         (src_id, obj_id, obj_dict['survey_id']))
        if len(update_obj_srcid_lookup_tups) > 0:
            self.cursor.executemany(update_obj_srcid_lookup_str, \
                                                  update_obj_srcid_lookup_tups)


    def do_xmlquery_using_htm(self, dbxml_cont, ra, dec, filter_i=2):
        """ Query the XML-DB for existing XML containers which matches
        the row_tup's spatial coordinates.
        Return all XML container URIs which match, after grooming a bit.
        """
        epoch_elem_str="(filt | t | jsb_mag | jsb_mag_err)"
        htm_id = self.htm_tools.generate_htm_id(ra, dec, htm_id_depth=self.pars['htm_id_query_depth'])
        print('>', htm_id)
        constr_xquery = '(starts-with(What/htm,"%s"))' % (htm_id)
        full_xquery = """collection("%s")/VOEvent[%s]/@uid""" % \
                                                 ("test.dbxml", constr_xquery)
        matching_dbxmlid_list = dbxml_cont.query(full_xquery)

        # TODO/KLUDGE/NOTE: HTM-ID isn't really needed to be returned:
        # TODO: we additionally want ra_rms, dec_rms returned...
        return_col_str ="t, jsb_mag, jsb_mag_err, filt, src_id, ra, decl, ra_rms, dec_rms, htm"
        result_list = []
        for src_id_str in matching_dbxmlid_list:
            # TODO: I could hardcode indexes here for speed:
            src_id = src_id_str[src_id_str.find('"')+1:src_id_str.rfind('"')]
            constraint = '(src_id = "%s")' % (src_id)
            result_rows = self.select_return_rdb_rows(constraint, \
                             rdb_table_name=self.srcd.rdb_table_names['sdss'],\
                             select_cols=return_col_str, row_limit=100000)
            result_list.extend(result_rows)
            result_rows = self.select_return_rdb_rows(constraint, \
                         rdb_table_name=self.srcd.rdb_table_names['pairitel'],\
                         select_cols=return_col_str, row_limit=100000)
            result_list.extend(result_rows)

        # TODO: Make usre that the aboive dbxml query works as well...
        # TODO: test that result_list is of the correct form...
        #
        for (t,m,me,f,did,ra,dec,ra_rms,dec_rms,htm) in result_list: print(t,m,me,f,did,ra,dec,ra_rms,dec_rms,htm)
        return result_list


    def select_and_form_objepoch_dict_using_constraint(self, constraint_str, \
                object_tablename, survey_name='', survey_num=0, join_str='', \
                filter_duplicate_time_data=False):
        """ Create SELECT string using given constraint str, retrieve sources
        matching spatial range.  Construct a 'tme-tuple' list of
        characteristics and return this.

        NOTE: Here we assume sources have been determined for all objects
             in constraint region.
        """
        # Current Output: (flags, flags2, objc_type,t,m,me,f,sid,ra,dec,ra_rms,dec_rms)
        if survey_name == 'sdss':
            flags_str = "%s.flags, %s.flags2, %s.objc_type" % (\
                                      object_tablename,\
                                      object_tablename,\
                                      object_tablename)
        elif survey_name == 'pairitel':
            # NOTE: PAIRITEL data doesnt have these flags in their data so
            #       I set to default/unused values:
            flags_str = "0 as flags, 0 as flags2, 10 as objc_type"
        elif survey_name == 'ptf':
            # NOTE: PTF data doesnt have these flags in their data so
            #       I set to default/unused values:
            flags_str = "0 as flags, 0 as flags2, 10 as objc_type"

        # Here we get objects, using a spatial constraint, and JOIN 
        #
        # %s.src_id   self.pars['obj_srcid_lookup_tablename']
        #
        create_str = "CREATE TEMPORARY TABLE blah ENGINE MEMORY Select %s, %d as survey_id, %s.obj_id, %s.t, %s.jsb_mag, %s.jsb_mag_err, %s.filt, %s.ra, %s.decl, %s.ra_rms, %s.dec_rms FROM %s %s WHERE (%s)" %(\
            flags_str, \
            survey_num, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, \
            object_tablename, join_str, constraint_str)
        self.cursor.execute(create_str)
        select_str = "SELECT HIGH_PRIORITY blah.flags, blah.flags2, blah.objc_type, blah.t, blah.jsb_mag, blah.jsb_mag_err, blah.filt, %s.src_id, blah.ra, blah.decl, blah.ra_rms, blah.dec_rms, %s.%s.feat_gen_date FROM blah JOIN %s USING (survey_id, obj_id) JOIN %s.%s USING (src_id)" %(\
            self.pars['obj_srcid_lookup_tablename'], self.pars['rdb_name_4'], self.pars['srcid_table_name'], self.pars['obj_srcid_lookup_tablename'], self.pars['rdb_name_4'], self.pars['srcid_table_name'])

        #######
        self.cursor.execute(select_str)
        rdb_rows = self.cursor.fetchall()
        self.cursor.execute("DROP TABLE blah")
        print("> Number SELECT returned object/epoch rows:", len(rdb_rows))

        # For SDSS, we often get duplicate 'object' data points due to astrometric reductions of drift-scan files....  So I average the magnitude & mag error (which seem to be consistantly close in duplicates).
        if filter_duplicate_time_data:
            time_data_tup_dict = {}
            for rdb_row in rdb_rows: 
                t = rdb_row[3]
                m = rdb_row[4]
                f = rdb_row[6]
                no_match = True
                for (row_filt, t_low, t_high, m_low, m_high),entry in \
                                                time_data_tup_dict.iteritems():
                    if (f == row_filt) and (t >= t_low) and (t <= t_high) and \
                                           (m >= m_low) and (m <= m_high):
                        entry[4] += rdb_row[4] # magnitude
                        entry[5] += rdb_row[5] # magnitude error
                        entry[-1] += 1.0 # counter
                        no_match = False
                        break
                if no_match:
                    obj_list = list(rdb_row)
                    obj_list.append(1.0) # number of objects counter
                    time_data_tup_dict[(f, t - 1.1574e-5, t + 1.1574e-5, \
                                                m - 0.05, m + 0.05)] = obj_list
            rdb_rows = []
            for (f, t_low,t_high, m_low,m_high),entry in \
                                                time_data_tup_dict.iteritems():
                entry[4] /= entry[-1]
                entry[5] /= entry[-1]
                rdb_rows.append(tuple(entry[:-1]))
                
        obj_epoch_list = []
        for (flags, flags2, objc_type, \
                t,m,me,f,sid,ra,dec,ra_rms,dec_rms,feat_gen_date) in rdb_rows: 
            obj_epoch = {}
            obj_epoch['flags'] = flags
            obj_epoch['flags2'] = flags2
            obj_epoch['objc_type'] = objc_type
            obj_epoch['t'] = t
            obj_epoch['m'] = m
            obj_epoch['m_err'] = me
            obj_epoch['filt'] = int(f) # I think all MySQL results are str's
            obj_epoch['srcid'] = sid
            obj_epoch['ra'] = ra
            obj_epoch['dec'] = dec
            obj_epoch['ra_rms'] = ra_rms
            obj_epoch['dec_rms'] = dec_rms
            obj_epoch['feat_gen_date'] = feat_gen_date
            obj_epoch_list.append(obj_epoch)
        return obj_epoch_list


    ############# Revised version: 
    # These queries will interface with LBL's MySQL PTF diff-object database:
    def select_and_form_objepoch_dict_using_constraint___ptf_case(self, constraint_str, object_tablename, survey_name='', survey_num=0, join_str='', filter_duplicate_time_data=False, only_constrain_using_srcid=None):
        """ Create SELECT string using given constraint str, retrieve sources
        matching spatial range.  Construct a 'tme-tuple' list of
        characteristics and return this.

        NOTE: Here we assume sources have been determined for all objects
             in constraint region.
        """
        #select_str = "SELECT x.%s, %s, %s.survey_id, %s.%s.feat_gen_date, %s.%s.src_id FROM (SELECT %d as survey_id, id AS obj_id, %s.* FROM %s WHERE (%s)) AS x JOIN %s ON (%s.survey_id=%d AND x.id=%s.obj_id) JOIN %s.%s USING (src_id)" % (\
        #      ', x.'.join(self.pars['ptf_rdb_columns_list']),
        #      "x.bogus, x.suspect, x.unclear, x.maybe, x.realish, x.realbogus", \
        #      self.pars['obj_srcid_lookup_tablename'],
        #      self.pars['rdb_name_4'], self.pars['srcid_table_name'],
        #      self.pars['rdb_name_4'], self.pars['srcid_table_name'],
        #      survey_num, object_tablename, object_tablename,
        #      constraint_str,
        #      self.pars['obj_srcid_lookup_tablename'],
        #      self.pars['obj_srcid_lookup_tablename'],
        #      survey_num,
        #      self.pars['obj_srcid_lookup_tablename'],
        #      self.pars['rdb_name_4'], self.pars['srcid_table_name'])

        if only_constrain_using_srcid != None:
            select_str = """SELECT %s, %s.survey_id, %s.%s.feat_gen_date, %s.%s.src_id
                FROM %s
                JOIN %s AS t1 ON %s.obj_id=t1.id
                JOIN %s.%s USING (src_id)
                WHERE survey_id=%d and src_id=%d""" % (\
                    self.pars['ptf_rdb_select_columns__t1'],
                    self.pars['obj_srcid_lookup_tablename'],
                    self.pars['rdb_name_4'], self.pars['srcid_table_name'],
                    self.pars['rdb_name_4'], self.pars['srcid_table_name'],
                    self.pars['obj_srcid_lookup_tablename'],
                    self.pars['rdb_table_names']['ptf'], 
                    self.pars['obj_srcid_lookup_tablename'],
                    self.pars['rdb_name_4'], self.pars['srcid_table_name'],
                    survey_num, only_constrain_using_srcid)
        else:
            ##### Here we get objects, using a spatial constraint, and JOIN 
            select_str = """SELECT %s, %s.survey_id, %s.%s.feat_gen_date, %s.%s.src_id
            FROM (SELECT %d as survey_id, id FROM %s WHERE (%s)) AS x
            JOIN %s ON (%s.survey_id=%d AND x.id=%s.obj_id)
            JOIN %s AS t1 ON x.id=t1.id
            JOIN %s.%s USING (src_id)""" % (\
              self.pars['ptf_rdb_select_columns__t1'],
              self.pars['obj_srcid_lookup_tablename'],
              self.pars['rdb_name_4'], self.pars['srcid_table_name'],
              self.pars['rdb_name_4'], self.pars['srcid_table_name'],
              survey_num, object_tablename,
              constraint_str,
              self.pars['obj_srcid_lookup_tablename'],
              self.pars['obj_srcid_lookup_tablename'],
              survey_num,
              self.pars['obj_srcid_lookup_tablename'],
              self.pars['rdb_table_names']['ptf'], 
              self.pars['rdb_name_4'], self.pars['srcid_table_name'])

        self.cursor.execute(select_str)
        rdb_rows = self.cursor.fetchall()
        #print "> Number SELECT returned object/epoch rows:", len(rdb_rows)

        #obj_epoch_list = []
        last_index_object_table = len(self.pars['ptf_rdb_columns_list'])
        mag_time_id_dict = {}
        for row in rdb_rows: 
            obj_epoch = extract_obj_epoch_from_ptf_query_row(row)
            if obj_epoch['pos_sub'][0] is None:
                # This case occurs when the mysql ptf_events table has not
                #     has not been updated with new values from lbl pgsql database.
                # This should only be the case for epochs not associated with the source
                #      (very far from it spatially).
                continue # skip this epoch
            total_mag = calculate_ptf_mag.calculate_total_mag({'f_aper':obj_epoch['f_aper'],
                                                               'flux_aper':obj_epoch['flux_aper'],
                                                               'ub1_zp_ref':obj_epoch['ub1_zp_ref'],
                                                               'mag_ref':obj_epoch['mag_ref'],
                                                               'sub_zp':obj_epoch['sub_zp'][0],
                                                               'pos_sub':obj_epoch['pos_sub'][0]})
            if str(total_mag) == 'nan':
                ### NOTE: 20090831: This condition was used to cull ptf candidates assocuated with ptf09xxx sources, candidates which were bad subtractions (total_mag == NAN):
                #fp = open('/tmp/deleted_ptf', 'a')
                #fp.write(str(obj_epoch) + '\n')
                #fp.close()
                #self.cursor.execute("DELETE from object_test_db.ptf_events where id=%d" % (obj_epoch['obj_ids'][0]))
                continue # skip this epoch since it's a bad LBL subtraction
            obj_epoch['m'] = total_mag
            obj_epoch['feat_gen_date'] = row[last_index_object_table + 1]
            obj_epoch['srcid'] = row[last_index_object_table + 2]
            #obj_epoch_list.append(obj_epoch)
            mag_time_id_dict[(obj_epoch['m'],obj_epoch['t'],obj_epoch['obj_ids'][0])] = obj_epoch

        # KLUDGY:
        final_obj_epoch_list = []
        added_mag_time_id_list = []
        mag_time_id_list = mag_time_id_dict.keys()
        for (mag,t,objid),obj_epoch in mag_time_id_dict.iteritems():
            if (mag,t,objid) in added_mag_time_id_list:
                continue # the equivalent obj_epoch already exists so go to next tuple
            already_added = False
            for (mag2,t2,objid2) in mag_time_id_list:
                if ((abs(mag - mag2) < 0.001) and \
                    (abs(t - t2) < 0.00001) and
                    (objid != objid2)):
                    #mag_time_id_list.remove((mag2,t2,objid2))
                    mag_time_id_list.remove((mag ,t ,objid ))
                    if not (mag2,t2,objid2) in added_mag_time_id_list:
                        final_obj_epoch_list.append(obj_epoch)
                        added_mag_time_id_list.append((mag2,t2,objid2))
                    already_added = True
                    break
            if not already_added:
                final_obj_epoch_list.append(obj_epoch)
                
        return final_obj_epoch_list


    # UNUSED method, but keep for reference:
    def populate_xmldb_using_rdb(self, dbxml_cont, rdb_ind, \
                                     rdb_table_name, row_limit=100):
        """ Retrieve all RDB (indbxml=0) entries, and add them to the xmlDB.
        Then update the cooresponding RDB entries.
        """
        do_retrieve = 1
        debug_i = 0
        while do_retrieve == 1:
            already_updated_htms = []
            rdb_indbxml_list = self.select_return_rdb_rows("(in_dbxml = 0)", \
                            rdb_table_name=rdb_table_name, row_limit=row_limit)
            if len(rdb_indbxml_list) == 0:
                break # get out of here: no more rows to retrieve.
            for row_list in rdb_indbxml_list:
                htm_id = row_list[rdb_ind.htm]
                if not htm_id in already_updated_htms:
                    dbxmlid_select = self.srcd.lookup_dbxmlid_select_mask % (htm_id) #  + "%")
                    self.cursor.execute(dbxmlid_select)
                    src_id_str = self.cursor.fetchall()

                    #full_xquery = """collection("%s")/VOEvent[(starts-with(What/htm,"%s"))]/@uid""" % ("test.dbxml", htm_id)
                    #src_id_str = dbxml_cont.query(full_xquery)
                    if len(src_id_str) > 0:
                        # TODO: I could hardcode indexes here for speed:
                        src_id = src_id_str[0][0][src_id_str[0][0].find('"')+1:src_id_str[0][0].rfind('"')]
                        src_id = src_id_str[0][0]
                    else:
                        src_id = row_list[rdb_ind.obj_id] # the obj_id is unique, which is all that matters
                        add_row_str = self.srcd.lookup_insert_mask % (htm_id, src_id)
                        self.cursor.execute(add_row_str)
                    #self.dbxml_add_new_container_using_rdb_row(\
                    #          row_list, dbxml_cont, \
                    #          rdb_ind, htm_id=htm_id, src_id=src_id)
                    update_str = """UPDATE %s SET src_id="%s", in_dbxml=1 WHERE (htm="%s")""" % (rdb_table_name, src_id, htm_id)
                    self.cursor.execute(update_str)
                    already_updated_htms.append(htm_id)
            debug_i += row_limit
            print(debug_i)


    def add_limitmags_to_sourcedict(self, source_dict):
        """ This function queries for PTF limting mags from MySQL tabke and
        and adds limit_mag lists to source_dict[srcid][filter]['limitmags']={'t':[],'lmt_mg':[]}

        KLUDGE: There is a redundant bit, where the limiting magnitudes for both filters
                are added to both source_dict[srcid]['ptf_g'] and ['ptf_r']
        """
        filter_conv_dict = {'g':'ptf_g', 'R':'ptf_r'}
        for srcid in source_dict.keys():
            for temp_filter_name,temp_filter_dict in source_dict[srcid].iteritems():
                if 'ra' in temp_filter_dict:
                    ra = temp_filter_dict['ra']
                    dec = temp_filter_dict['dec']
                    break # get out of for loop.
                    
            for filt_name in filter_conv_dict.values():
                if filt_name not in source_dict[srcid]:
                    source_dict[srcid][filt_name] = {}
                if 'limitmags' not in source_dict[srcid][filt_name]:
                    source_dict[srcid][filt_name]['limitmags'] = {'t':[], 'lmt_mg':[]}
            select_str = "SELECT filter, ujd, lmt_mg from %s WHERE (MBRContains(radec_region, GeomFromText('POINT(%lf %lf)'))) ORDER BY filter, ujd" % (self.pars['ptf_mysql_candidate_footprint'], ra, dec)
            self.cursor.execute(select_str)
            rdb_rows = self.cursor.fetchall()

            for filt_name,filt_dict in source_dict[srcid].iteritems():
                for row in rdb_rows: 
                    (filt, ujd, lmt_mg) = row
                    filt_name = filter_conv_dict[filt]
                    source_dict[srcid][filt_name]['limitmags']['t'].append(float(ujd))
                    source_dict[srcid][filt_name]['limitmags']['lmt_mg'].append(float(lmt_mg))


    # Obsolete:
    def add_limitmags_to_sourcedict__old(self, source_dict):
        """ This function queries for PTF limting mags from MySQL tabke and
        and adds limit_mag lists to source_dict[srcid][filter]['limitmags']={'t':[],'lmt_mg':[]}

        KLUDGE: There is a redundant bit, where the limiting magnitudes for both filters
                are added to both source_dict[srcid]['ptf_g'] and ['ptf_r']
        """
        filter_conv_dict = {'g':'ptf_g', 'R':'ptf_r'}
        for srcid in source_dict.keys():
            temp_dict = source_dict[srcid].values()[0]
            ra = temp_dict['ra']
            dec = temp_dict['dec']
            for filt_dict in source_dict[srcid].values():
                if 'limitmags' not in filt_dict:
                    filt_dict['limitmags'] = {}
                    for filt_name in filter_conv_dict.values():
                        filt_dict['limitmags'][filt_name] = {'t':[], 'lmt_mg':[]}
            select_str = "SELECT filter, ujd, lmt_mg from %s WHERE (MBRContains(radec_region, GeomFromText('POINT(%lf %lf)'))) ORDER BY filter, ujd" % (self.pars['ptf_mysql_candidate_footprint'], ra, dec)
            self.cursor.execute(select_str)
            rdb_rows = self.cursor.fetchall()

            for filt_dict in source_dict[srcid].values():
                for row in rdb_rows: 
                    (filt, ujd, lmt_mg) = row
                    filt_name = filter_conv_dict[filt]
                    filt_dict['limitmags'][filt_name]['t'].append(float(ujd))
                    filt_dict['limitmags'][filt_name]['lmt_mg'].append(float(lmt_mg))


class Make_Plots:
    """ Singleton object which contains .ps plot generating methods.
    """
    def __init__(self, pars):
        self.pars = pars

    def form_source_dict_using_obj_epoch_list(self, obj_epoch_list):
        """ Given a list of objects(object characs), 
        form a dictionary of {<source>:{<filt>:{..source t[],m[],ra,dec,...}}}
        """
        plotd = {}
        #for (flags, flags2, objc_type,t,m,me,f,did,ra,dec,ra_rms,dec_rms,htm) in tme_list:
        for obj_epoch in obj_epoch_list:
            srcid = obj_epoch['srcid']
            filt = self.pars['filters'][obj_epoch['filt']]
            t = obj_epoch['t']
            m = obj_epoch['m']
            m_err = obj_epoch['m_err']
            flags = obj_epoch['flags']
            flags2 = obj_epoch['flags2']
            objc_type = obj_epoch['objc_type']
            feat_gen_date = obj_epoch['feat_gen_date']

            ra = obj_epoch['ra']
            dec = obj_epoch['dec']
            ra_rms = obj_epoch['ra_rms'] / 3600.0
            dec_rms = obj_epoch['dec_rms'] / 3600.0
            if srcid not in plotd:
                plotd[srcid] = {}
            if filt not in plotd[srcid]:
                plotd[srcid][filt]= {'t':[],'m':[],'m_err':[],'ra':0, 'dec':0,\
                                     'flags':[], 'flags2':[], 'objc_type':[]}
                if 'objid_candid' in obj_epoch:
                    a_dict = plotd[srcid][filt]
                    a_dict['objid_candid'] = []
                    a_dict['objid_subtract'] = []
                    a_dict['ra_candidate'] = []
                    a_dict['dec_candidate'] = []
                    a_dict['x_candidate'] = []
                    a_dict['y_candidate'] = []
                    a_dict['x_subtref'] = []
                    a_dict['y_subtref'] = []
                    a_dict['signoise_subt_normap'] = []
                    a_dict['signoise_subt_big_ap'] = []
                    a_dict['mag_subtr'] = []
                    a_dict['mag_sig_subtr'] = []
                    a_dict['mag_refer'] = []
                    a_dict['mag_sig_refer'] = []
                    a_dict['a_elip_candid'] = []
                    a_dict['b_elip_candid'] = []
                    a_dict['positive_pix_ratio'] = []
                    a_dict['fwhm_obj_subtr'] = []
                    a_dict['fwhm_obj_candid'] = []
                    a_dict['fourier_factor'] = []
                    a_dict['percent_incres'] = []
                    a_dict['surf_bright'] = []
                    a_dict['quality_factor'] = []
                    a_dict['nn_mag'] = []
                    a_dict['nn_mag_sig'] = []
                    a_dict['nn_a_elip'] = []
                    a_dict['nn_b_elip'] = []
                    a_dict['nn_x'] = []
                    a_dict['nn_y'] = []
                    a_dict['nn_ra'] = []
                    a_dict['nn_dec'] = []
                    a_dict['nn_distance'] = []
                    a_dict['nn_star_galaxy'] = []
                    a_dict['imgname_subtract'] = []
                    a_dict['img_id_candid'] = []
                    a_dict['img_id_refer'] = []
                    a_dict['field_id'] = []
                    a_dict['chip_id'] = []
                    a_dict['filter_id'] = []
                    a_dict['ra_subtract'] = []
                    a_dict['dec_subtract'] = []
                    a_dict['dtime_observe'] = []
                    a_dict['dtime_reductn'] = []
                    a_dict['perc_cand_saved'] = []
                    a_dict['zp_candidate'] = []
                    a_dict['zp_reference'] = []
                    a_dict['hp_kern_radius'] = []
                    a_dict['hp_rss'] = []
                    a_dict['hp_newskybkg'] = []
                    a_dict['hp_refskybkg'] = []
                    a_dict['hp_newskysig'] = []
                    a_dict['hp_refskysig'] = []
                    a_dict['hp_il'] = []
                    a_dict['hp_iu'] = []
                    a_dict['hp_tl'] = []
                    a_dict['hp_tu'] = []
                    a_dict['hp_nsx'] = []
                    a_dict['hp_nsy'] = []



            plotd[srcid][filt]['t'].append(t)
            plotd[srcid][filt]['m'].append(m)
            plotd[srcid][filt]['m_err'].append(m_err)
            plotd[srcid][filt]['flags'].append(flags)
            plotd[srcid][filt]['flags2'].append(flags2)
            plotd[srcid][filt]['objc_type'].append(objc_type)

            plotd[srcid][filt]['feat_gen_date'] = feat_gen_date 
            plotd[srcid][filt]['ra'] = ra
            plotd[srcid][filt]['dec'] = dec
            plotd[srcid][filt]['ra_rms'] = ra_rms
            plotd[srcid][filt]['dec_rms'] = dec_rms
            plotd[srcid][filt]['src_id'] = srcid

            # # # # # # I need to add PTF dict stuff :
            if 'objid_candid' in obj_epoch:
                a_dict = plotd[srcid][filt]
                a_dict['objid_candid'].append(obj_epoch['objid_candid'])
                a_dict['objid_subtract'].append(obj_epoch['objid_subtract'])
                a_dict['ra_candidate'].append(obj_epoch['ra_candidate'])
                a_dict['dec_candidate'].append(obj_epoch['dec_candidate'])
                a_dict['x_candidate'].append(obj_epoch['x_candidate'])
                a_dict['y_candidate'].append(obj_epoch['y_candidate'])
                a_dict['x_subtref'].append(obj_epoch['x_subtref'])
                a_dict['y_subtref'].append(obj_epoch['y_subtref'])
                a_dict['signoise_subt_normap'].append(obj_epoch['signoise_subt_normap'])
                a_dict['signoise_subt_big_ap'].append(obj_epoch['signoise_subt_big_ap'])
                a_dict['mag_subtr'].append(obj_epoch['mag_subtr'])
                a_dict['mag_sig_subtr'].append(obj_epoch['mag_sig_subtr'])
                a_dict['mag_refer'].append(obj_epoch['mag_refer'])
                a_dict['mag_sig_refer'].append(obj_epoch['mag_sig_refer'])
                a_dict['a_elip_candid'].append(obj_epoch['a_elip_candid'])
                a_dict['b_elip_candid'].append(obj_epoch['b_elip_candid'])
                a_dict['positive_pix_ratio'].append(obj_epoch['positive_pix_ratio'])
                a_dict['fwhm_obj_subtr'].append(obj_epoch['fwhm_obj_subtr'])
                a_dict['fwhm_obj_candid'].append(obj_epoch['fwhm_obj_candid'])
                a_dict['fourier_factor'].append(obj_epoch['fourier_factor'])
                a_dict['percent_incres'].append(obj_epoch['percent_incres'])
                a_dict['surf_bright'].append(obj_epoch['surf_bright'])
                a_dict['quality_factor'].append(obj_epoch['quality_factor'])
                a_dict['nn_mag'].append(obj_epoch['nn_mag'])
                a_dict['nn_mag_sig'].append(obj_epoch['nn_mag_sig'])
                a_dict['nn_a_elip'].append(obj_epoch['nn_a_elip'])
                a_dict['nn_b_elip'].append(obj_epoch['nn_b_elip'])
                a_dict['nn_x'].append(obj_epoch['nn_x'])
                a_dict['nn_y'].append(obj_epoch['nn_y'])
                a_dict['nn_ra'].append(obj_epoch['nn_ra'])
                a_dict['nn_dec'].append(obj_epoch['nn_dec'])
                a_dict['nn_distance'].append(obj_epoch['nn_distance'])
                a_dict['nn_star_galaxy'].append(obj_epoch['nn_star_galaxy'])
                a_dict['imgname_subtract'].append(obj_epoch['imgname_subtract'])
                a_dict['img_id_candid'].append(obj_epoch['img_id_candid'])
                a_dict['img_id_refer'].append(obj_epoch['img_id_refer'])
                a_dict['field_id'].append(obj_epoch['field_id'])
                a_dict['chip_id'].append(obj_epoch['chip_id'])
                a_dict['filter_id'].append(obj_epoch['filter_id'])
                a_dict['ra_subtract'].append(obj_epoch['ra_subtract'])
                a_dict['dec_subtract'].append(obj_epoch['dec_subtract'])
                a_dict['dtime_observe'].append(obj_epoch['dtime_observe'])
                a_dict['dtime_reductn'].append(obj_epoch['dtime_reductn'])
                a_dict['perc_cand_saved'].append(obj_epoch['perc_cand_saved'])
                a_dict['zp_candidate'].append(obj_epoch['zp_candidate'])
                a_dict['zp_reference'].append(obj_epoch['zp_reference'])
                a_dict['hp_kern_radius'].append(obj_epoch['hp_kern_radius'])
                a_dict['hp_rss'].append(obj_epoch['hp_rss'])
                a_dict['hp_newskybkg'].append(obj_epoch['hp_newskybkg'])
                a_dict['hp_refskybkg'].append(obj_epoch['hp_refskybkg'])
                a_dict['hp_newskysig'].append(obj_epoch['hp_newskysig'])
                a_dict['hp_refskysig'].append(obj_epoch['hp_refskysig'])
                a_dict['hp_il'].append(obj_epoch['hp_il'])
                a_dict['hp_iu'].append(obj_epoch['hp_iu'])
                a_dict['hp_tl'].append(obj_epoch['hp_tl'])
                a_dict['hp_tu'].append(obj_epoch['hp_tu'])
                a_dict['hp_nsx'].append(obj_epoch['hp_nsx'])
                a_dict['hp_nsy'].append(obj_epoch['hp_nsy'])
        return plotd


    def make_plot_using_obj_epoch_list(self, obj_epoch_list, source_dict, \
              out_fpath='/tmp/out.ps', do_show='no', query_ra=0, query_dec=0):
        """ Given a list of [(time, mag, mag_err), (...), (...),...]
        This generates a .ps plot and saves in the ps_fpath file.
        """
        all_mag_list = []
        all_ra_list = []
        all_dec_list = []
        for obj_epoch in obj_epoch_list:
            all_mag_list.append(obj_epoch['m'])
            all_ra_list.append(obj_epoch['ra'])
            all_dec_list.append(obj_epoch['dec'])

        plot_sym_list = self.pars['plot_symb'] * \
                        (1 + len(source_dict)/len(self.pars['plot_symb']))
        mag_mean = numpy.array(all_mag_list).mean()
        mag_max = max(all_mag_list)
        mag_min = min(all_mag_list)
        ra_max = max(all_ra_list) + 0.0001
        ra_min = min(all_ra_list) - 0.0001
        ra_mean = numpy.array(all_ra_list).mean()
        ra_diff = ra_max - ra_min
        if ra_diff == 0:
            ra_diff = 1 # ??? 1 degree?  I take it this range is arbitrary...

        dec_max = max(all_dec_list) + 0.0001
        dec_min = min(all_dec_list) - 0.0001
        dec_mean = numpy.array(all_dec_list).mean()
        dec_diff = dec_max - dec_min
        if dec_diff == 0:
            dec_diff = 1 # ??? 1 degree?  I take it this range is arbitrary...

        mag_reduce_factor = 0.06
        all_m_decoff = []
        #for (t,m,me,f,did,ra,dec,ra_rms,dec_rms,htm) in tme_list:
        for obj_epoch in obj_epoch_list:
            srcid = obj_epoch['srcid']
            filt = self.pars['filters'][obj_epoch['filt']]
            # KLUDGY:
            if 'm_raoff' not in source_dict[srcid][filt]:
                source_dict[srcid][filt]['m_raoff'] = []
            if 'm_decoff' not in source_dict[srcid][filt]:
                source_dict[srcid][filt]['m_decoff'] = []
            t = obj_epoch['t']
            m = obj_epoch['m']
            ra = obj_epoch['ra']
            dec = obj_epoch['dec']

            ra_cur_diff = ra - ra_mean
            m_raoff = m - mag_mean  +ra_cur_diff * (mag_max - mag_min)/ ra_diff
            source_dict[srcid][filt]['m_raoff'].append(m_raoff)
            dec_cur_diff = dec - dec_mean
            m_decoff = mag_reduce_factor * (m - mag_mean) + \
                       dec_cur_diff * (mag_max - mag_min) / dec_diff
            source_dict[srcid][filt]['m_decoff'].append(m_decoff)
            all_m_decoff.append(m_decoff)

        all_m_decoff_min = min(all_m_decoff)
        all_m_decoff_max = max(all_m_decoff)
        pylab.rcParams.update({'figure.figsize':[10,10]}) # ??x?? inches
        try:
            pylab.hold(True)
        except:
            print('ERROR Generating pylab plot: DISPLAY issue?')

        ###### M vs time
        ax = pylab.subplot(211)
        pylab.title("Query: RA=" + str(query_ra) + ", Dec=" + str(query_dec) +\
                  "  HTM_DB_dpth=" + str(self.pars['htm_id_database_depth']) +\
                  "  HTM_qry_dpth=" + str(self.pars['htm_id_query_depth']))
        num_points = len(source_dict)
        num_levels = num_points / 3
        factor_incr = 1.0/(num_levels + 1)
        color_tup_list = [] # len of num_points, filled with 5 color rgb tups
        cur_incr = factor_incr
        for i_point in xrange((num_points/3) +1):
            for i_rgb in xrange(3):
                ref_rgb = [cur_incr, cur_incr, cur_incr]
                ref_rgb[i_rgb] = 1.0
                point_rgb_list = []
                for brt_fact in [0.2, 0.4, 0.6, 0.8, 1.0]:
                    cur_rgb = [0,0,0]
                    for i in xrange(3):
                        cur_rgb[i] = ref_rgb[i] * brt_fact
                        if cur_rgb[i] > 1:
                            cur_rgb[i] = 1
                    point_rgb_list.append(tuple(cur_rgb))
                color_tup_list.append(point_rgb_list)
            cur_incr += factor_incr

        i_did = 0
        for did_dict in source_dict.values():
            i_f = 0
            for filt,f_dict in did_dict.iteritems():
                symbol = plot_sym_list[i_did]
                pylab.errorbar(numpy.array(f_dict['t']),\
                               numpy.array(f_dict['m']),\
                          yerr=numpy.array(f_dict['m_err']),\
                               fmt=symbol, marker=symbol, \
                               color=color_tup_list[i_did][i_f])
                i_f += 1
            i_did += 1
        ax.autoscale_view()
        pylab.ylim( (min(all_mag_list)-0.2,max(all_mag_list)+0.2) )
        pylab.xlabel('t')
        pylab.ylabel('m')

        ##### M-offset(DEC) vs time
        ax = pylab.subplot(224)
        i_did = 0
        for did_dict in source_dict.values():
            i_f = 0
            for filt,f_dict in did_dict.iteritems():
                symbol = plot_sym_list[i_did]
                pylab.plot(numpy.array(f_dict['t']), numpy.array(f_dict['m_decoff']), symbol, marker=symbol, color=color_tup_list[i_did][i_f])
                i_f += 1
            i_did += 1
        ax.autoscale_view()
        pylab.ylim( (all_m_decoff_min,all_m_decoff_max) )
        pylab.xlabel('t')
        pylab.ylabel('pseudo M_Dec')

        ##### RA,DEC PLOT:
        ax = pylab.subplot(223)
        i_did = 0
        for did_dict in source_dict.values():
            symbol = plot_sym_list[i_did]
            dd_i = did_dict.keys()[0] # Just an arbitrary dict index
            pylab.errorbar([did_dict[dd_i]['ra']], [did_dict[dd_i]['dec']], \
                       xerr=did_dict[dd_i]['ra_rms'],\
                       yerr=did_dict[dd_i]['dec_rms'],\
                       fmt=symbol, marker=symbol, color=color_tup_list[i_did][4]) ### NO: I use the [0] filter, for the symbol color.  there should always be 1 color...
            i_did += 1
        pylab.plot([query_ra], [query_dec], 'rx', markersize=15, \
                       markeredgewidth=1)
        pylab.xlim( (ra_min,ra_max) )
        pylab.ylim( (dec_min,dec_max) )
        pylab.xlabel('RA')
        pylab.ylabel('Dec')

        if do_show == 'yes':
            pylab.show()
        if os.path.exists(out_fpath):
            os.system('rm ' + out_fpath)
        pylab.savefig(out_fpath)

        print("WROTE:", out_fpath)
        pylab.close()
        try:
            pylab.hold(False)
        except:
            print('ERROR Generating pylab plot: DISPLAY issue?')

    # This is obsolete:
    def query_plot_ra_dec(self, pars, rdbt, htm_tools, ra, dec, box_degree_range):
        """ Query the RDBs using (ra,dec,arcangle), generating a list of 
        HTMids using a HTM circle-query.  Plot the results.
        """
        half_range = box_degree_range / 2.0
        ra_low = ra - half_range
        ra_high = ra + half_range
        dec_low = dec - half_range
        dec_high = dec + half_range

        # Do a HTM circle query at ra,dec using arcangle circle bisection:
        #htm_ranges = htm_tools.get_htmranges_using_radec_box(ra_low, ra_high,\
        #                                                    dec_low, dec_high)
        #constraint_str = htm_tools.form_htm_constraint_str_using_htm_ranges(\
        #   htm_ranges, table_prefix=pars['sdss_obj_htm_lookup_tablename'])
        col_name = "%s.radec" % (pars['sdss_obj_rtree_lookup_tablename'])
        constraint_str = form_constraint_str_for_rtree_rectangle(ra_low, ra_high, dec_low, dec_high, col_name=col_name)
        obj_epoch_list = rdbt.select_and_form_objepoch_dict_using_constraint(\
                                                               constraint_str)
        ### Render the results in a PS PLOT:
        #mp = Make_Plots(pars)
        source_dict =self.form_source_dict_using_obj_epoch_list(obj_epoch_list)
        self.make_plot_using_obj_epoch_list(obj_epoch_list, source_dict, \
            out_fpath='/tmp/out.ps', do_show='yes', query_ra=ra, query_dec=dec)


class SDSS_Local_Fits_Repository:
    """ This contains methods which are used for generating dirpaths which
    are valid for the astrometry code (using a given f,c,r).
    This also contains methods for scp astrometry dirctories to/from the local
    scratch disks to the 'local' repository server/disk.
    """
    def __init__(self, pars):
        self.pars = pars
    
    def scp_local_astrom_dirs_to_repository(self, field=0, camcol=0, run=0):
        """ This method scps the local astrometry dirpath and subdirectories
        to the corresponding repository astrom dirpath, for later retrieval.
        """
        # Attempt to create the astrom dirs on the repository.  Ok, if exists:
        if self.pars['sdss_astrom_repo_host_ip'] == "127.0.0.1":
            mkdir_cmd = "mkdir %s/%d" % (self.pars['sdss_astrom_repo_dirpath'], run)
        else:
            mkdir_cmd = "ssh -x -n %s@%s mkdir %s/%d" % (self.pars['sdss_astrom_repo_user'], self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run)
        os.system(mkdir_cmd)
        if self.pars['sdss_astrom_repo_host_ip'] == "127.0.0.1":
            mkdir_cmd = "mkdir %s/%d/%d" % (self.pars['sdss_astrom_repo_dirpath'], run, field)
        else:
            mkdir_cmd = "ssh -x -n %s@%s mkdir %s/%d/%d" % (self.pars['sdss_astrom_repo_user'], self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field)
        os.system(mkdir_cmd)

        local_astrom_path = "%s%d/%d" % (self.pars['sdss_astrom_local_dirpath'], run, field)
        cwd = os.getcwd()
        os.chdir(local_astrom_path)
        tar_command = "tar -czf %s/%d_%d_%d.tgz *%d-r%d-*%d.* *%d-%d-*%d.*" % (local_astrom_path, run, camcol, field, run, camcol, field, run, camcol, field)
        os.system(tar_command)

        # scp files from local dirpath to repository:
        if self.pars['sdss_astrom_repo_host_ip'] == "127.0.0.1":
            scp_command = "cp %s/%d_%d_%d.tgz %s/%d/%d/" % (local_astrom_path, run, camcol, field, self.pars['sdss_astrom_repo_dirpath'], run, field)
        else:
            scp_command = "scp -q %s/%d_%d_%d.tgz %s@%s:%s/%d/%d/" % (local_astrom_path, run, camcol, field, self.pars['sdss_astrom_repo_user'], self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field)
        os.system(scp_command)
        rm_cmd = "rm %s/%d_%d_%d.tgz" % (local_astrom_path, run, camcol, field)
        os.system(rm_cmd)
        os.chdir(cwd)
        
        # NOTE: The next called function should mark the FCR ingest_status=11


    def scp_repository_astrom_dirs_to_local(self, field=0, camcol=0, run=0):
        """ This method scps the repository astrom dirpath and subdirectories
        to the corresponding repository astrom dirpath, for later retrieval.
        """
        # Check repository path has >0 files : return (-1/error) otherwise:
        #check_nfiles_ssh_cmd = "ssh -x -n %s ls %s/%d/%d/*%d{-r,-}%d-*%d\.*" % (self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field)
        if self.pars['sdss_astrom_repo_host_ip'] == "127.0.0.1":
            check_nfiles_ssh_cmd = "ls %s/%d/%d/%d_%d_%d.tgz" % (self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field)
        else:
            check_nfiles_ssh_cmd = "ssh -x -n %s@%s ls %s/%d/%d/%d_%d_%d.tgz" % (self.pars['sdss_astrom_repo_user'], self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field)
        (a,b,c) = os.popen3(check_nfiles_ssh_cmd)
        a.close()
        c.close()
        file_list = b.read()
        b.close()
        if len(file_list) < 1:
            return -1 

        # Create local dirpath if not exist:
        local_astrom_dirpath = "%s%d" % (self.pars['sdss_astrom_local_dirpath'], run)
        if not os.path.exists(local_astrom_dirpath):
            os.system('mkdir ' + local_astrom_dirpath)
        local_astrom_dirpath = "%s%d/%d" % (self.pars['sdss_astrom_local_dirpath'], run, field)
        if not os.path.exists(local_astrom_dirpath):
            os.system('mkdir ' + local_astrom_dirpath)

        # scp files from repository to local dirpath:
        # NOTE: I should determine whether -C compression helps while the 
        #       TCP is fully loaded.
        if self.pars['sdss_astrom_repo_host_ip'] == "127.0.0.1":
            scp_command = "cp %s/%d/%d/%d_%d_%d.tgz %s/%d/%d/" % (self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field, self.pars['sdss_astrom_local_dirpath'], run, field)
        else:
            scp_command = "scp -q %s@%s:%s/%d/%d/%d_%d_%d.tgz %s/%d/%d/" % (self.pars['sdss_astrom_repo_user'], self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field, self.pars['sdss_astrom_local_dirpath'], run, field)

        #scp_command = "scp %s:%s/%d/%d/*%d{-r,-}%d-*%d\.* %s/" % (self.pars['sdss_astrom_repo_host_ip'], self.pars['sdss_astrom_repo_dirpath'], run, field, run, camcol, field, self.pars['sdss_astrom_local_dirpath'])
        os.system(scp_command)

        local_astrom_path = "%s/%d/%d" % (self.pars['sdss_astrom_local_dirpath'], run, field)
        cwd = os.getcwd()
        os.chdir(local_astrom_path)
        tar_command = "tar -xzf %s/%d_%d_%d.tgz" % (local_astrom_path, run, camcol, field)
        os.system(tar_command)
        rm_cmd = "rm %s/%d_%d_%d.tgz" % (local_astrom_path, run, camcol, field)
        os.system(rm_cmd)
        os.chdir(cwd)

        # TODO: TEST (at least once, or in a test class???) That scp cps files
        # - return (1/ok)
        return 1 # success


class TCP_Runtime_Methods:
    """ A suite of TCP populating and querying methods which coordinate 
    various other object tasks together.

    NOTE: we try to keep this Class/Object as transparent as possible, passing
        only required variables into methods.
    Although: scratch directory paths will be generated and cleaned up here.
    """
    def __init__(self, cur_pid=0):
        """ Will only have a TCP Scratch/Data directory as an internal variable
        """
        self.cur_pid = cur_pid
        if "TCP_DATA_DIR" in os.environ:
            if not os.path.exists(os.environ.get("TCP_DATA_DIR")):
                os.system("mkdir -p %s" % (os.environ.get("TCP_DATA_DIR")))
            self.tcp_data_dir_old = os.environ.get("TCP_DATA_DIR")
            self.tcp_data_dir = os.environ.get("TCP_DATA_DIR") + '/' + \
                'ingtools' + cur_pid
            if not os.path.exists(self.tcp_data_dir):
                os.system("mkdir " + self.tcp_data_dir)
            # 20080522: dstarr comments this out, but maybe this is needed
            #      during SDSS object ingestion & sdss_ingest_monitory.py?
            #      If so, that's super KLUDGY.
            #os.environ["TCP_DATA_DIR"] = self.tcp_data_dir # for sdss_*py
            return
        print("ERROR: BAD environ var TCP_DATA_DIR:", os.environ.get("TCP_DATA_DIR"))
        sys.exit()


    # NOTE: I feel this should belong in a source-class, excluding the rdbt use
    def populate_srcid_table_loop(self, pars, srcdbt, rdbt, ra=-999, dec=-999,\
                 box_degree_range=0.02, box_overlap_factor=0.05, force_HTM25=0, \
                                  skip_check_sdss_objs=False, \
                                  skip_check_ptel_objs=False, \
                                  skip_check_ptf_objs=False, \
                                  do_logging=False):
        """ While loop which iterates (indefinitly?), RDB retrieving the first
        obj_id where (src_id==0).  Then it calls <src_id creation algorithm)>
        using that objid's (ra,dec).

        I've modified this so if (ra,dec) are specified, the sources
        will be built centered on (ra,dec) and using box_degree_range.

        NOTE: I want sources from a region slightly larger than the
           object-box when querying for possibly related sources,
           since the border objects may belong to sources just outside
           of the object region.

        TODO: I could call get_sources_for_radec_with_feature_extraction()
             for each loop iteration, and generate features in the RECTs
             (for sources which have had no features generated).
             This would certainly slow down the source-finding algorithms.
              - should have a flag to enable this.
        """
        buffer_width = box_degree_range * box_overlap_factor
        if ((ra != -999) and (dec != -999)):
            n_iters = 1
            half_range = box_degree_range / 2.0
            ra_low = ra - half_range
            ra_high = ra + half_range
            dec_low = dec - half_range
            dec_high = dec + half_range
            src_ra_low = ra - half_range - buffer_width
            src_ra_high = ra + half_range + buffer_width
            src_dec_low = dec - half_range - buffer_width
            src_dec_high = dec + half_range + buffer_width
        else:
            n_iters = 1000000 #Go until (-1,-1) return/exit.
            
        (obj_ra, obj_dec) = (ra, dec) # Define these just for 'print' below...
        for i in xrange(n_iters):
            # TODO/KLUDGE/NOTE: This will have problems at ra:0/360 discontin.:
            if n_iters != 1:
                #(obj_ra, obj_dec) = rdbt.get_first_srcid0_object_epoch()
                (ra_low, ra_high, dec_low, dec_high, region_id) = \
                            rdbt.get_first_srcid0_object_epoch(box_degree_range)
                if ra_low == -1:
                    return
                src_ra_low = ra_low - buffer_width
                src_ra_high = ra_high + buffer_width
                src_dec_low = dec_low - buffer_width
                src_dec_high = dec_high + buffer_width
            print("%s Get objects in region (low corner): %0.4f %0.4f" % (\
                                 str(datetime.datetime.now()), ra_low, dec_low))
            objs_dict = {}
            if ((rdbt.sdss_tables_available == 1) and (skip_check_sdss_objs==False)):
                if (((ra_high - ra_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                   ((dec_high - dec_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                    (force_HTM25 == 1)):
                    DIF_HTM_tablename = \
                                   pars['sdss_object_table_name_DIF_HTM25']
                else:
                    DIF_HTM_tablename = \
                                   pars['sdss_object_table_name_DIF_HTM14']
                objs_dict = rdbt.retrieve_objects_dict_near_radec_where_src0(\
                     ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1,\
                     objepoch_table_name=DIF_HTM_tablename, survey_id=0)
            if ((rdbt.ptel_tables_available == 1) and (skip_check_ptel_objs==False)):
                if (((ra_high - ra_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                   ((dec_high - dec_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                    (force_HTM25 == 1)):
                    DIF_HTM_tablename = \
                                   pars['ptel_object_table_name_DIF_HTM25']
                else:
                    DIF_HTM_tablename = \
                                   pars['ptel_object_table_name_DIF_HTM14']
                ptel_objs_dict = \
                            rdbt.retrieve_objects_dict_near_radec_where_src0(\
                     ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1, \
                     objepoch_table_name=DIF_HTM_tablename, survey_id=1)
                objs_dict.update(ptel_objs_dict)
            if rdbt.ptf_tables_available == 1:
                #if not self.use_postgre_ptf:
                # KLUDGE: for now I do this condition in both postgre and mysql PTF cases.
                if (((ra_high - ra_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                   ((dec_high - dec_low) < \
                             pars['degree_threshold_DIFHTM_14_to_25']) or \
                    (force_HTM25 == 1)):
                    DIF_HTM_tablename = \
                                   pars['ptf_object_table_name_DIF_HTM25']
                else:
                    DIF_HTM_tablename = \
                                   pars['ptf_object_table_name_DIF_HTM14']
                if do_logging:
                    print("before: rdbt.retrieve_objects_dict_near_radec_where_src0__ptf_specific()")
                ptf_objs_dict = \
                  rdbt.retrieve_objects_dict_near_radec_where_src0__ptf_specific(\
                       ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1, \
                       objepoch_table_name=DIF_HTM_tablename, survey_id=3, do_logging=do_logging)
                #ptf_objs_dict = \
                #            rdbt.retrieve_objects_dict_near_radec_where_src0(\
                #    ra_low, ra_high, dec_low, dec_high, do_src0_constraint=1, \
                #     objepoch_table_name=DIF_HTM_tablename, survey_id=3)
                objs_dict.update(ptf_objs_dict)

            print(datetime.datetime.now(), "Got", len(objs_dict), "objects in region")
            srcdbt.populate_srcids_using_objs_dict(rdbt, objs_dict, \
                            src_ra_low, src_ra_high, src_dec_low, src_dec_high, \
                            skip_check_sdss_objs=skip_check_sdss_objs, \
                            skip_check_ptel_objs=skip_check_ptel_objs, \
                            skip_check_ptf_objs=skip_check_ptf_objs, \
                                                   do_logging=do_logging)
            if do_logging:
                print("after: srcdbt.populate_srcids_using_objs_dict()")
            # KLUDGY Placement:
            if n_iters != 1:
                rdbt.srl.unlock_region(region_id)


    def add_sdssii_to_rdb_using_sdss_blocklist(self, slfits_repo, rdbt, \
                        block_list, scp_repo_retrieve_success, survey='DRSN1'):
        """ Using a given [{field,camcol,run}, ...]; retrieves SDSSII 
        data-tables, recalibrates and ingests into SDSSII RDB.
        """
        ingest_success = 3 # Incomplete astrophot run
        run_status = ''
        print("Populating MySQL DB with SDSS FITS tables...")
        table_fpath_list = []
        b = sdss_astrophot.SDSS_multiblock()
        b.make_light_curve = 0 # Needed to not invoke plot routines
        #           fail in the plotting routines, even when else ok.
        data_url = rdbt.pars['sdss_data_urls'][survey]

        #if 1:
        print("Doing: sdss_astrophot.SDSS_multiblock.run_block_list(block_list, data_url=%s)" % (data_url))
        try:
            status = b.run_block_list(block_list, data_url=data_url)
            table_fpath_list = b.jsb_files
            run_status = b.statusi[0]
        except:
            #if 0:
            return 4 # ERROR in astrometry routines
        if status == -1:
            return 4 # Error in block_list/block_dict
        if 'failed [zps]' in run_status:
            return 4 # unsuccessful, astrophot failed-zps
        elif not ('completed' in run_status):
            print('run_status:', run_status)
            return 3 # unsuccessful, astrophot incomplete

        # NOTE(20070820): In current ingestion implementation, only a single
        #    tuple exists in block_list[], which generates a single FITS Table
        #    in table_fpath_list[].  So this loop is generally done only once.:
        # NOTE(20080314): If we retrieved astrom from repo tgz file, no 
        #      need to tar.gz and send back to astrom repository.
        if scp_repo_retrieve_success != 1:
            for rfc_dict in block_list:
                slfits_repo.scp_local_astrom_dirs_to_repository(\
                           field=rfc_dict['field'], camcol=rfc_dict['camcol'],\
                           run=rfc_dict['run'])
        if len(table_fpath_list) == 1:
            try:
                fp = rdbt.open_fitstable(table_fpath_list[0])
            except:
                print("Error opening:", table_fpath_list[0])
                return 2
            (tup_list, fcrr_list) = rdbt.get_tup_list_from_sdss_fits_fp(fp)
            fp.close()
            limit_mags_dict = rdbt.get_median_limiting_mags_from_tup_list(\
                                                  tup_list, survey_name='sdss')
            # 20090530 (no change: leaves try/except):
            try:
                objids_list = rdbt.insert_object_tuplist_into_rdb(\
                              tup_list=tup_list, \
                              fcrr_list=fcrr_list, survey_name='sdss', \
                              obj_htm_tablename=\
                                  rdbt.pars['sdss_obj_htm_lookup_tablename'], \
                              obj_rtree_tablename=\
                                 rdbt.pars['sdss_obj_rtree_lookup_tablename'],\
                              limit_mags_dict=limit_mags_dict)
                n_ingest = len(objids_list)
            except:
                print("EXCEPT in insert_object_tuplist_into_rdb()")
                return 4 # unsuccessful.  Except generally is a mysql error at the insert_str_list_obj_data INSERT. :: OperationalError: (2006, 'MySQL server has gone away')
            if n_ingest == 0:
                print("WARNING: No SDSS data ingested for:",table_fpath_list[0])
                return 2
            else:
                return 11 # fully successful ingest
        return -999 # This older/unused case doesn't use function output.


    def get_field_cam_run_using_radec(self, pars, ra, dec, survey='DRSN1'):
        """ Given a (ra,dec), retrieve a list of SDSS (field,camcol,run).
        This code is derived from jbloom's sdss_astrophot.py.run_from_pos()
        """
        # Pre 20090723:
	# http://sdssw1.fnal.gov/DRSN1-cgi-bin/FOOT?csvIn=ra%2Cdec%0D%0A30.0%2C-1.0%0D%0A;inputFile=;do_bestBox=yes;Submit=Submit%20Request
        # (current) post 20090723:
        #http://cas.sdss.org/Stripe82/en/tools/search/x_radial.asp?ra=15.5&dec=0.5&radius=0.1&min_u=0&max_u=20&min_g=0&max_g=20&min_r=0&max_r=20&min_i=0&max_i=20&min_z=0&max_z=20&entries=all&topnum=10&format=csv
        
	#tmp = """ra,dec\n%f,%f""" % (ra,dec)
	#params = urllib.urlencode({'csvIn': tmp})
        random_fpath ="/tmp/%d.wget"%(numpy.random.random_integers(1000000000))
        url_str = "http://cas.sdss.org/Stripe82/en/tools/search/x_radial.asp?ra=%lf&dec=%lf&radius=0.1&min_u=0&max_u=20&min_g=0&max_g=20&min_r=0&max_r=20&min_i=0&max_i=20&min_z=0&max_z=20&entries=all&topnum=10&format=csv" % (ra, dec)
        wget_str = 'wget -t 1 -T 5 -O %s "%s"' % (random_fpath, url_str)
        print("wget do:", wget_str)
        os.system(wget_str)
        print("wget done")
        footret = open(random_fpath).read()
        os.system("rm %s" % (random_fpath))
	#f =urllib.urlopen(pars['sdss_footprint_urls'][survey], "%s;%s" % (params,pars['footprint_preamble']))
	#footret =  f.read()
        #f.close()
        if len(footret) < 10:
            print("ERROR: Bad return from footprint server.(ra,dec):", ra, dec)
            return
	res_string = footret#[start+5:end]
        res_str_list = res_string.split('\n')
        #res_string:
        #objid,run,rerun,camcol,field,obj,type,ra,dec,u,g,r,i,z,Err_u,Err_g,Err_r,Err_i,Err_z
        #8658201042601051118,7161,40,5,551,1006,8,15.49928788,0.50114768,21.795298,26.294159,27.620859,25.056583,24.421753,0.735364,1.831846,0.552887,3.526816,1.49893
        out_fcr_tup_list = []
        # NOTE: I believe the first line of res_string
        #       is a preamble and can be skipped:
        for row in res_str_list:
            if ((len(row) < 10) or ('camcol' in row)):
                continue # skip (normally) the first and last lines
            vals = row.split(',')
            fcr_tup = (vals[4].strip(), vals[3].strip(), vals[1].strip())
            out_fcr_tup_list.append(fcr_tup)
        return out_fcr_tup_list


    def get_field_cam_run_using_radec__old(self, pars, ra, dec, survey='DRSN1'):
        """ Given a (ra,dec), retrieve a list of SDSS (field,camcol,run).
        This code is derived from jbloom's sdss_astrophot.py.run_from_pos()
        """
	# http://sdssw1.fnal.gov/DRSN1-cgi-bin/FOOT?csvIn=ra%2Cdec%0D%0A30.0%2C-1.0%0D%0A;inputFile=;do_bestBox=yes;Submit=Submit%20Request
	tmp = """ra,dec\n%f,%f""" % (ra,dec)
	params = urllib.urlencode({'csvIn': tmp})
        random_fpath ="/tmp/%d.wget"%(numpy.random.random_integers(1000000000))
        wget_str = 'wget -t 1 -T 5 -O %s "%s%s;%s"' % (random_fpath, \
                                         pars['sdss_footprint_urls'][survey], \
                                         params, pars['footprint_preamble'])
        print("wget do:", wget_str)
        os.system(wget_str)
        print("wget done")
        footret = open(random_fpath).read()
        os.system("rm %s" % (random_fpath))
	#f =urllib.urlopen(pars['sdss_footprint_urls'][survey], "%s;%s" % (params,pars['footprint_preamble']))
	#footret =  f.read()
        #f.close()
	start = footret.find("<pre>")
	end = footret.find("</pre>")
	if start == -1 or end == -1:
            print("ERROR: Bad return from footprint server.(ra,dec):", ra, dec)
            return
	res_string = footret[start+5:end]
        res_str_list = res_string.split('\n')
        #res_string:
        #ra,        dec,       run,  rerun, camcol, field,  rowc, colc
        # 49.621196,  -1.008420, 4849,   40,    1,  786,   611.30, 443.51
        #...
        # 49.621196,  -1.008420, 6314,   40,    1,  658,   743.15, 448.94
        out_fcr_tup_list = []
        # NOTE: I believe the first line of res_string
        #       is a preamble and can be skipped:
        for row in res_str_list:
            if ((len(row) < 10) or ('rowc, colc' in row)):
                continue # skip (normally) the first and last lines
            vals = row.split(',')
            fcr_tup = (vals[5].strip(), vals[4].strip(), vals[2].strip())
            out_fcr_tup_list.append(fcr_tup)
        return out_fcr_tup_list


    def sdss_rfc_ingest_using_rfc_dict(self, rdbt, slfits_repo, sdss_fcr_iso,\
                 cur_i, total_i, rfc_dict, do_delete_scratch_dir=0, \
                                       survey='DRSN1'):
        """This retrieves, computes astrometry, and ingests data into local RDB
        """
        if len(sdss_fcr_iso.hostname) > 10:
            host_name_str = sdss_fcr_iso.hostname[:10]
        else:
            host_name_str = sdss_fcr_iso.hostname

        current_ingest_status = sdss_fcr_iso.check_fcr_rdb_ingested(\
                   field=rfc_dict['field'], camcol=rfc_dict['camcol'], \
                   run=rfc_dict['run'])
        #print "%d/%d %s current_ingest_status=%d" % (i, len(fcr_tup_list),\
        #                     str(fcr_tup), current_ingest_status)

        # NOTE: if the fcr_status == 3 or 4, then we've already tried
        #       to ingest, and failed. so we should skip.
        #    ==10 : this has already been ingested into the RDB.
        if ((current_ingest_status >= 10) or (current_ingest_status == 3) or (current_ingest_status == 4)):
            return # This (f,c,r) has already been ingested.  Skip.
        elif (current_ingest_status == -1):
            # This means we need to add this FCR to table.
            update_str = """INSERT INTO %s (ingest_status, ingest_date, host, run, field, camcol) VALUES (1, now(), "%s", %d, %d, %d)""" % (sdss_fcr_iso.table_name, host_name_str, rfc_dict['run'], rfc_dict['field'], rfc_dict['camcol'])
        ###
        else:
            update_str = """UPDATE %s SET ingest_status=1, ingest_date=now(), host="%s" WHERE (run=%d AND field=%d AND camcol=%d)""" % (sdss_fcr_iso.table_name, host_name_str, rfc_dict['run'], rfc_dict['field'], rfc_dict['camcol'])
        sdss_fcr_iso.cursor.execute(update_str)
        ###

        scp_repo_retrieve_success = 0
        if (current_ingest_status == 7):
            # We copy existing astrometry files from astrom repository:
            scp_repo_retrieve_success = \
                              slfits_repo.scp_repository_astrom_dirs_to_local(\
                     field=rfc_dict['field'], camcol=rfc_dict['camcol'], \
                      run=rfc_dict['run'])
            if scp_repo_retrieve_success == -1:
                print("Error scp from repo->local where status=7:", \
                     rfc_dict['field'], rfc_dict['camcol'], rfc_dict['run'])
            
        ingest_success = self.add_sdssii_to_rdb_using_sdss_blocklist(\
                           slfits_repo, rdbt, [rfc_dict], \
                           scp_repo_retrieve_success, survey=survey)
        print("sdss_rfc_ingest_using_ra_dec(%d/%d) %d,%d,%d success:%d" %\
              (cur_i, total_i, rfc_dict['run'], rfc_dict['field'], \
               rfc_dict['camcol'], ingest_success))
        sdss_fcr_iso.update_RDB_with_ingested_rfc_dict(rfc_dict, \
                                                          ingest_success)
        if do_delete_scratch_dir == 1:
            scratch_dirpath = "%s/%d/%d" % (\
          os.environ["TCP_DATA_DIR"][:os.environ["TCP_DATA_DIR"].rfind('/')], \
                                      rfc_dict['run'], rfc_dict['field'])
            #This is where regexp use in syscommand would help:'-r?%d-'
            # This doesn't work:
            #os.system("rm -Rf %s/*{-r,-}%d-*" % (scratch_dirpath, \
            #                               rfc_dict['camcol']))
            os.system("rm -Rf %s/*-%d-*" % (scratch_dirpath, \
                                           rfc_dict['camcol']))
            os.system("rm -Rf %s/*-r%d-*" % (scratch_dirpath, \
                                           rfc_dict['camcol']))
            #scratch_dirpath = "%s/%d/%d" % (os.environ["TCP_DATA_DIR"], \
            #                          rfc_dict['run'], rfc_dict['field'])
            #if os.path.exists(scratch_dirpath):
            #    os.system("rm -Rf " + scratch_dirpath)


    def sdss_rfc_ingest_using_ra_dec(self, pars, rdbt, slfits_repo, \
                         sdss_fcr_iso, ra=0, dec=0, do_delete_scratch_dir=0):
        """ Using an (ra,dec), this determines all (f,c,r) FITS tables,
        and retrieves from SDSS server.  It then ingests their data into
        the local RDB.
        """
        fcr_tup_list = self.get_field_cam_run_using_radec(pars, ra, dec, survey='single_catalog')
        if ((fcr_tup_list==None) or (fcr_tup_list == [('0', '0', '0')])):
            pass # no f,c,r are found for that ra,dec OR no web access.
        else:
            i = -1
            for fcr_tup in fcr_tup_list:
                i += 1
                rfc_dict = {'field':int(fcr_tup[0]), 'camcol':int(fcr_tup[1]), \
                            'run':int(fcr_tup[2])}
                self.sdss_rfc_ingest_using_rfc_dict(rdbt, slfits_repo, \
                                 sdss_fcr_iso, i, len(fcr_tup_list), rfc_dict, \
                                 do_delete_scratch_dir=1, survey='single_catalog')


    def loop_sdss_rfc_ingest(self, rdbt, sdss_fcr_iso, n_iters=1, \
                                                     do_delete_scratch_dir=0):
        """ Loop over the SDSS rfc ingestion into RDB.
        """
        for i in xrange(n_iters):
            #rfc_dict = {'field': 266, 'camcol': 1, 'run': 5759}
            rfc_dict = sdss_fcr_iso.get_uningested_rfc_dict()
            if len(rfc_dict) == 0:
                continue # Some error occured in retrieving a rfc tuple. Skip.
            self.sdss_rfc_ingest_using_rfc_dict(rdbt, slfits_repo, \
                   sdss_fcr_iso, i, n_iters, rfc_dict, do_delete_scratch_dir=1)
            """
            ingest_success = self.add_sdssii_to_rdb_using_sdss_blocklist(\
                                                             rdbt, [rfc_dict])
            print "loop_sdss_rfc_ingest(%d/%d) %d,%d,%d success:%d" % \
                            (i, n_iters, rfc_dict['run'], rfc_dict['field'], \
                             rfc_dict['camcol'], ingest_success)
            sdss_fcr_iso.update_RDB_with_ingested_rfc_dict(rfc_dict, \
                                                               ingest_success)
            if do_delete_scratch_dir == 1:
                # In a loop, this limits diskspace use, but takes time rm-Rf
                scratch_dirpath = "%s%d/%d" % (os.environ["TCP_DATA_DIR"][:os.environ["TCP_DATA_DIR"].rfind('/')], \
                                          rfc_dict['run'], rfc_dict['field'])
                if os.path.exists(scratch_dirpath):
                    #This is where regexp use in syscommand would help:'-r?%d-'
                    os.system("rm -Rf %s/*-%d-*" % (scratch_dirpath, \
                                                   rfc_dict['camcol']))
                    os.system("rm -Rf %s/*-r%d-*" % (scratch_dirpath, \
                                                   rfc_dict['camcol']))
            """


class SDSS_FCR_Ingest_Status_Object:
    """ Object which wraps all methods pertaining to the MySQL Table
    which contains accounting of which (field,camcol,run) has successfully
    been ingested into the SDSS object/epoch ('sdss_events') table.

    NOTE: this table will use its own mysql database server connections so
    it's access can be seperated from other, more query intense mysql servers.
    This should allow for quick query and access of this table.
    """
    def __init__(self, rdb_host_ip='', rdb_user='', rdb_name='', rdb_port=3306, \
                     table_name='',\
                     sdss_fields_doc_fpath_list='', hostname='', db=None):
        self.rdb_host_ip = rdb_host_ip
        self.rdb_user = rdb_user
        self.rdb_name = rdb_name
        self.rdb_port = rdb_port
        self.table_name = table_name
        self.hostname = hostname
        self.sdss_fields_doc_fpath_list = sdss_fields_doc_fpath_list
        if db is None:
            self.db = MySQLdb.connect(host=self.rdb_host_ip, user=self.rdb_user, db=self.rdb_name, port=self.rdb_port)
        else:
            self.db = db
        self.cursor = self.db.cursor()
        self.get_num_uningested_fcr()
        self.insert_prefix = 'INSERT INTO ' + self.table_name + ' (run, field, camcol, error, ingest_status) VALUES (%s, %s, %s, %s, %s)'
        self.create_command = """CREATE TABLE %s (run SMALLINT, field SMALLINT, camcol TINYINT, error TINYINT, ingest_status TINYINT, ingest_date DATETIME, host VARCHAR(10), INDEX USING HASH (field, camcol, run)) ENGINE=MEMORY""" % (self.table_name)

    
    def get_num_uningested_fcr(self):
        """ Get the number of SDSS (f,c,r) cases which have not yet been 
        ingested or even have been attempted to be ingested.
        """
        try:
            select_str = 'SELECT count(*) FROM ' + self.table_name + \
                         ' WHERE ((ingest_status = 0) or (ingest_status = 7))'
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            self.n_uningested_rfc = results[0][0]
        except:
            #In case fail where ['sdss_fields_table_name'] table doesn't exist
            self.n_uningested_rfc = 0


    def generate_rfc_insert_table(self, rf_list):
        """ Generate a table of all run,field,camcol elems, in format 
        for a RDB executemany() insert into RDB table.

        Conditional: (not row_list in rdb_table_list) is inefficient, but
        only done once, ever.
        """ 
        run_field_list = []
        rdb_table_list = []
        i = 1
        len_i = len(rf_list)
        for (run, field_start, field_end) in rf_list:
            print(i, len_i)
            i += 1
            run_str = str(run)
            fields = range(field_start, field_end + 1)
            for field in fields:
                field_str = str(field)
                rf_str = "%d_%d" % (run,field)
                if not rf_str in run_field_list:
                    run_field_list.append(rf_str)
                    add_list = [[run_str, field_str, '1', '0', '0'], \
                                [run_str, field_str, '2', '0', '0'], \
                                [run_str, field_str, '3', '0', '0'], \
                                [run_str, field_str, '4', '0', '0'], \
                                [run_str, field_str, '5', '0', '0'], \
                                [run_str, field_str, '6', '0', '0']]
                    rdb_table_list.extend(add_list)
        return rdb_table_list


    def get_sdss_rf_list_from_doc(self):
        """ Read the document file lines, and return a list
        of [[run, field_start, field_end], ...]
        """
        out_list = []
        for dat_fpath in self.sdss_fields_doc_fpath_list:
            lines = open(dat_fpath).readlines()
            for line in lines:
                elems = line.split()
                out_list.append((int(elems[0]), int(elems[1]), int(elems[2])))
        return out_list


    def populate_rfc_rdb_table(self):
        """ Create and populate the RDB with table which contains all 
        possible {Run, Field, Camcol} permutations needed for compete 
        RDB ingest of SDSS.
        """
        rf_list = self.get_sdss_rf_list_from_doc()
        rfc_insert_table = self.generate_rfc_insert_table(rf_list)
        self.cursor.executemany(self.insert_prefix, rfc_insert_table)


    def check_fcr_rdb_ingested(self, field=0, camcol=0, run=0):
        """ Check the rfc_ingest_status table whether this (f,c,r) has been ingested
        into the RDB (sdss_events... table) already.
        """
        select_str = "SELECT ingest_status FROM %s WHERE (field=%d and camcol=%d and run=%d)" % (self.table_name, field, camcol, run)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        if len(results) == 0:
            # For some reason, FCR is not in rfc_ingest_status table. Newly Add?
            return -1 # This signal means we need to add this FCR to table.
        return int(results[0][0]) # NOTE: This will Traceback if, for some reason, we have no entry in the fcr database


    def update_RDB_with_ingested_rfc_dict(self, rfc_dict, ingest_success):
        """ Given a rfc_dict, update the SDSS RDB Table's coorsponding row
        that this case has been ingested.  Also update the finished ingest
        datetime in the row.
        
        ingest_success values:
        0 : no ingest attempt made
        1 : being ingested
        2 : unsuccessful ingest: No objects found
        3 : unsuccessful ingest: incomplete astrophot run
        4 : unsuccessful ingest: astrophot 'failed [zps]': no sdss1 catalog?
        7 : not ingested in RDB, but astrometry files exist in local repository
        9 : successfully ingested
        10: v2.0 Table scheme: a (f,c,r) object dataset successfully ingested
        11: v2.1 object dataset ingested & astrometry files saved to local repo
        """
        update_str = """UPDATE %s SET ingest_status=%d, ingest_date=now() WHERE (run=%d AND field=%d AND camcol=%d)""" % (self.table_name, ingest_success, rfc_dict['run'], rfc_dict['field'], rfc_dict['camcol'])
        self.cursor.execute(update_str)


    def get_uningested_rfc_dict(self):
        """ Query the RFC SDSS RDB table for a single un-ingested row.
        Update table row that it is currently being ingested,
           and record the current ingest_date
        Return the rfc_dict for this row

        NOTE: This is really a complete KLUDGE since I'd rather not perform 
        a select to determine the exact number of (ingest_status==0) rows
        every time I want a new (rfc) tuple.  So, if there are >10000 rows where (ingest_status==0), I just randomly select within the known number of rows.  
        This is a kludge because there may be other instances of 
        ingest_tools.py running, which are also decreasing the number of
        (ingest_status==0) rows.

        So, eventually, when we've ingested most of SDSS's data, we'll
        transition to the <10000 rows algorithm.

        # TODO: it might be smart to SELECT (LIMIT 1) and UPDATE ingest_status=1 and return the run, field, camcol all in one command, so there is no chance of another process also running on this rfc
        """
        # Get a random offset of the available, uningested rfc rows:
        #  - KLUDGE: don't 'select count(*)' if there are many rows available
        if self.n_uningested_rfc > 10000:
            offset = int((self.n_uningested_rfc-8000) * numpy.random.random())
        else:
            print("NOTE: I prefer not performing this query very much...")
            select_str = 'SELECT count(*) FROM ' + self.table_name + \
                          ' WHERE ((ingest_status = 0) or (ingest_status = 7))'
            self.cursor.execute(select_str)
            results = self.cursor.fetchall()
            self.n_uningested_rfc = results[0][0]
            offset = int(self.n_uningested_rfc * numpy.random.random())

        select_str = 'SELECT run, field, camcol FROM ' + self.table_name + \
                     ' WHERE ((ingest_status = 0) or (ingest_status = 7)) LIMIT 1 OFFSET ' + str(offset)
        self.cursor.execute(select_str)
        results = self.cursor.fetchall()
        if len(results) == 0:
            return {}
        try:
            rfc_tup = results[0]
        except:
            print("ERROR: rfc_tup = results[0] offset:", offset)
            return {}
        if len(rfc_tup) != 3:
            print("ERROR: rfc row didn't contain a complete (r,f,c): offset:", offset)
            return {} 

        # # # # TODO: the following should be common to any add_sdss_to_rdb code
        #if len(self.hostname) > 10:
        #    host_name_str = self.hostname[:10]
        #else:
        #    host_name_str = self.hostname
        #update_str = """UPDATE %s SET ingest_status=1, ingest_date=now(), host="%s" WHERE (run=%d AND field=%d AND camcol=%d)""" % (self.table_name, host_name_str, rfc_tup[0], rfc_tup[1], rfc_tup[2])
        #self.cursor.execute(update_str)
        self.n_uningested_rfc -= 1
        return {'run':rfc_tup[0], 'field':rfc_tup[1], 'camcol':rfc_tup[2]}


class XRPC_RDB_Server_Interface_Object:
    """An object intended for use via a xmlrpclib/SimpleXMLRPCServer interface.
    Once the server connection is made, this object's methods are available
    for remote execution via the XMLRPC protocol.
    
    This object provides method access of the object/source Relational Database
    with functionality such as: 
      - get sources for a ra,dec, arcmin range
      ...
    
# Example of remote call/use:
import xmlrpclib
server = xmlrpclib.ServerProxy("http://192.168.1.45:8000")
print server.system.listMethods()
print server.system.methodHelp("get_sources_for_radec")
#src_list = server.get_sources_for_radec(ra, dec, box_range)
src_list = server.get_sources_for_radec(49.599497, -1.0050998, 0.0166666, '')
    """
    def __init__(self, pars, tcp_runs, rdbt, htm_tools, srcdbt,\
                     sdss_fcr_iso, slfits_repo):
        self.pars = pars
        self.tcp_runs = tcp_runs
        self.rdbt = rdbt
        self.htm_tools = htm_tools
        self.srcdbt = srcdbt
        self.sdss_fcr_iso = sdss_fcr_iso
        self.slfits_repo = slfits_repo


    def get_sources_for_radec(self, ra, dec, box_range, summary_ps_fpath, \
                              only_plot=0, force_HTM25=0, \
                              skip_remote_sdss_retrieval=False,
                              skip_check_sdss_objs=False,
                              skip_check_ptel_objs=False,
                              skip_check_ptf_objs=False,
                              do_logging=False):
        """ Given a position and length of the square region side (in degrees),
        This retrieves a dictionary of sources contained within this region.
        Intermediate steps, to get the sources may include:
          - retrieving SDSS FITS tables from Sloan server
          - re-computing astrometry for these SDSS files
          - insert objects into the Relational Database
          - compute sources for these objects, insert these into source
            database.
          - query sources for this region
        Once this method has successfully run once, the above intermediate
           steps will be internally skipped & subsequent execution will be
           much faster.
        NOTE: initial execution may take 1-10 mins due to possible SDSS data retrieval.
          - subsequent runs should take ~10s seconds.

          - For now I don't allow box_range > 10 arcmin.
          - This will be fixed soon with better spatial query methods.

        Input (in degrees): ra, dec, box_range
             Optional Flag: summary_ps_fpath='/localpath.ps' # generate a local
                            postscript plot.

        Output list: [{<source dict>}, {<source dict>}, ...]
           where <source dict> = {<filter>:{<dict of source characteristics>}}
        """
        if ((ra < 0) or (ra >= 360) or (dec <= -90) or (dec >= 90) or 
            (box_range < 0.00001) or (box_range > 0.30)):
            print("Warning: given out of range input:", ra, dec, box_range)
            return []

        if only_plot != 1:
            if not skip_remote_sdss_retrieval:
                if self.rdbt.sdss_tables_available == 1:
                    # If SDSS database is unavailable, skip retrieval:
                    #    will still try to use PAIRITEL, other surveys below...
                    self.tcp_runs.sdss_rfc_ingest_using_ra_dec(self.pars, \
                               self.rdbt, self.slfits_repo, self.sdss_fcr_iso, \
                               ra=ra, dec=dec, do_delete_scratch_dir=0)
            self.tcp_runs.populate_srcid_table_loop(self.pars, self.srcdbt,\
                        self.rdbt, ra=ra, dec=dec, box_degree_range=box_range, \
                                                    box_overlap_factor=0.05, \
                                                    skip_check_sdss_objs=skip_check_sdss_objs, \
                                                    skip_check_ptel_objs=skip_check_ptel_objs, \
                                                    skip_check_ptf_objs=skip_check_ptf_objs, \
                                                    do_logging=do_logging)
        if do_logging:
            print("after: self.tcp_runs.populate_srcid_table_loop()")

        half_range = box_range / 2.0
        ra_low = ra - half_range
        ra_high = ra + half_range
        dec_low = dec - half_range
        dec_high = dec + half_range

        # NOTE: I have to break up the obj_srcid_lookup.survey_id=? to make
        #        the SELECT statement resonable:
        obj_epoch_list = []
        if (self.rdbt.sdss_tables_available == 1) and (skip_check_sdss_objs==False):
            if (((ra_high - ra_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
               ((dec_high - dec_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
                (force_HTM25 == 1)):
                DIF_HTM_tablename =self.pars['sdss_object_table_name_DIF_HTM25']
            else:
                DIF_HTM_tablename =self.pars['sdss_object_table_name_DIF_HTM14']
            constraint_str = "DIF_HTMRectV(%lf, %lf, %lf, %lf)" % (\
                                             ra_low, dec_low, ra_high, dec_high)
            obj_epoch_list = self.rdbt.select_and_form_objepoch_dict_using_constraint(constraint_str, DIF_HTM_tablename, survey_name='sdss', survey_num=0)

        if (self.rdbt.ptel_tables_available == 1) and (skip_check_ptel_objs==False):
            if (((ra_high - ra_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
               ((dec_high - dec_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
                (force_HTM25 == 1)):
                DIF_HTM_tablename =self.pars['ptel_object_table_name_DIF_HTM25']
            else:
                DIF_HTM_tablename =self.pars['ptel_object_table_name_DIF_HTM14']
            constraint_str = "DIF_HTMRectV(%lf, %lf, %lf, %lf)" % (ra_low, dec_low, ra_high, dec_high)
            obj_epoch_list_2 = self.rdbt.select_and_form_objepoch_dict_using_constraint(constraint_str, DIF_HTM_tablename, survey_name='pairitel', survey_num=1)
            obj_epoch_list.extend(obj_epoch_list_2)

        #####
        # # # # # # # TODO: have 'ptf' case work for:
        # # # # # # # self.rdbt.select_and_form_objepoch_dict_using_constraint()
        # # # # # # #
        # # # # # # # TODO: eventually have this make use of LBL's Q3C PTF table
        if self.rdbt.ptf_tables_available == 1:
            # KLUDGE: I do this in both postgresql and mysql PTF cases, which is not needed.
            if (((ra_high - ra_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
               ((dec_high - dec_low) < \
                           self.pars['degree_threshold_DIFHTM_14_to_25']) or \
                (force_HTM25 == 1)):
                DIF_HTM_tablename =self.pars['ptf_object_table_name_DIF_HTM25']
            else:
                DIF_HTM_tablename =self.pars['ptf_object_table_name_DIF_HTM14']
            # this first condition is obsolete:
            #if self.rdbt.use_postgre_ptf:
            #    constraint_str = "(ra >= %lf and dec >= %lf and ra <= %lf and dec <= %lf)" % (ra_low, dec_low, ra_high, dec_high)
            #else:
            constraint_str = "DIF_HTMRectV(%lf, %lf, %lf, %lf)" % (ra_low, dec_low, ra_high, dec_high)
            #obj_epoch_list_2 = self.rdbt.select_and_form_objepoch_dict_using_constraint(constraint_str, DIF_HTM_tablename, survey_name='ptf', survey_num=3)
            obj_epoch_list_2 = self.rdbt.select_and_form_objepoch_dict_using_constraint___ptf_case(constraint_str, DIF_HTM_tablename, survey_name='ptf', survey_num=3)
            obj_epoch_list.extend(obj_epoch_list_2)
        #####
        if do_logging:
            print("before: mp.form_source_dict_using_obj_epoch_list(obj_epoch_list)")
        mp = Make_Plots(self.pars)
        source_dict = mp.form_source_dict_using_obj_epoch_list(obj_epoch_list)
        if ((len(summary_ps_fpath) > 0) and (len(obj_epoch_list) != 0)):
            try:
                mp.make_plot_using_obj_epoch_list(obj_epoch_list, source_dict, \
                    out_fpath=summary_ps_fpath, do_show=self.pars['show_plot'],\
                    query_ra=ra, query_dec=dec)
            except:
                print('Source summary PS plot failed')

        if do_logging:
            print("after: mp.form_source_dict_using_obj_epoch_list(obj_epoch_list)")

        # Adds PTF limiting-mags, ordered by src-id, for ra,dec region
        self.rdbt.add_limitmags_to_sourcedict(source_dict)
        if do_logging:
            print("after: self.rdbt.add_limitmags_to_sourcedict(source_dict)")
        # The returned list of sources should be sorted by distance from ra,dec:
        distance_dict = {}
        for srcid,src_dict in source_dict.iteritems():
            for filt_dict in src_dict.values():
                if 'ra' in filt_dict:
                    src_ra = filt_dict['ra']
                    src_dec = filt_dict['dec']
                    break # get out of for:
            dist2 = (src_ra - ra)**2 + (src_dec - dec) **2
            if dist2 in distance_dict:
                while dist2 in distance_dict:
                    dist2 += 0.00000001 # KLUDGE!
            distance_dict[dist2] = src_dict
        sorted_dist2s = distance_dict.keys()
        sorted_dist2s.sort()
        
        out_src_list = []
        for dist2 in sorted_dist2s:
            out_src_list.append(distance_dict[dist2])
        return out_src_list


    def form_objepochlist_for_ptf_using_srcid(self, src_id):
        """ Given a srcid, form and return an obj_epoch_list.
        This is different from the other workhorse function:
                   get_sources_for_radec()
        In that a spatial query is not done, and new epochs are potentially
           not added to the source, as well as only the ptf table is queried
           for epochs associated with the source.
        So, this should only be used if we are certain the srcid
           already contains all epochs.
        """
        obj_epoch_list = self.rdbt.select_and_form_objepoch_dict_using_constraint___ptf_case("",
                                     "ptf_events", survey_name='ptf', survey_num=3, \
                                     only_constrain_using_srcid=src_id)
        mp = Make_Plots(self.pars)
        source_dict = mp.form_source_dict_using_obj_epoch_list(obj_epoch_list)
        self.rdbt.add_limitmags_to_sourcedict(source_dict)
        rez = [source_dict[src_id]] # This makes the assumption that there will be a source with src_id
        return rez


    def get_vosourcelist_for_ptf_using_srcid(self, src_id):
        """ Given a srcid, form and return a vosource_list, which contains an
        xml_string with features in it.
        Only PTF candidates will be contained within this vosource xml.
        """
        import db_importer
        rez = self.form_objepochlist_for_ptf_using_srcid(src_id)
        pe = db_importer.PositionExtractor(doplot=False, write_xml=False, do_remote_connection=0) #pos=(0., 0.), radius=0., 
        pe.construct_sources(rez)
        src_obj_list = pe.sources   # source_obj.d['ts'][filt]['m']
        srcid_xml_tuple_list = []
        for source_obj in src_obj_list:
            src_id = source_obj.d['src_id']
            srcid_xml_tuple_list.append((src_id, source_obj.xml_string))
        srcid_xmlstr_withfeats_tup = get_features_using_srcid_xml_tuple_list(\
                                                          srcid_xml_tuple_list, write_ps=0, \
                                                          return_featd_xml_string=True)
        # For some reason srcid_xmlstr_withfeats_dict[0] is a <Code.signal_objects.signal_xml object>
        #    so we set it to the srcid int:
        return [(src_id, srcid_xmlstr_withfeats_tup[1][src_id])]
                                                          

    def get_src_obj_list(self, ra_numpy64, dec_numpy64, box_range_numpy64,\
                         feat_db, only_sources_wo_features=0, \
                         skip_remote_sdss_retrieval=False, skip_check_sdss_objs=False,skip_check_ptel_objs=False, do_logging=False):
        """ Intended for INTERNAL calling only.
        Given ra,dec,box-size; finds sources & returns a list of source objects
        """
        ra = float(ra_numpy64) # REDUNDANT, but floats are expected by xmlrpc
        dec = float(dec_numpy64) # REDUNDANT, but floats are expected by xmlrpc
        box_range = float(box_range_numpy64) # REDUNDANT, but floats are expect

        if ((ra < 0) or (ra >= 360) or (dec <= -90) or (dec >= 90) or 
            (box_range < 0.00001) or (box_range > 0.5)):
            #20080225# (box_range < 0.00001) or (box_range > 0.166666)):
            print("Warning: given out of range input:", ra, dec, box_range)
            return {}

        import db_importer
        #import generators_importers

        #######################
	#pe = db_importer.PositionExtractor(pos=(ra, dec),radius=box_range, host="192.168.1.45",port=8000, doplot=False, write_xml=False)

	#pe.search_pos(summary_ps_fpath='/tmp/sources_summary.ps')
	#pe.search_pos(summary_ps_fpath='/tmp/sources_summary.ps', \
        #              get_sources_for_radec_method=\
        #              self.get_sources_for_radec, \
        #              skip_construct_sources=True)
        #new_rez = feat_db.get_rez_for_featureless_sources(pe.rez)
        #pe.construct_sources(new_rez) #, out_xml_fpath='/tmp/out.xml')
        #######################
        # NOTE: This adds sources to RDB:
        rez = self.get_sources_for_radec(ra, dec, box_range, \
                     self.pars['plot_fpath_for_source_object_spatial_summary'],\
                          skip_remote_sdss_retrieval=skip_remote_sdss_retrieval,skip_check_sdss_objs=skip_check_sdss_objs,skip_check_ptel_objs=skip_check_ptel_objs, do_logging=do_logging)
        if do_logging:
            print("before: feat_db.get_rez_for_featureless_sources(rez)")

        (featureless_srcids, reduced_rez) = \
                                   feat_db.get_rez_for_featureless_sources(rez)
        if do_logging:
            print("after: feat_db.get_rez_for_featureless_sources(rez)")

        if only_sources_wo_features:
            new_rez = reduced_rez
        else:
            new_rez = rez
        pe = db_importer.PositionExtractor(pos=(ra, dec), radius=box_range, doplot=False, write_xml=False, do_remote_connection=0)
        pe.construct_sources(new_rez) #, out_xml_fpath='/tmp/out.xml')
        if do_logging:
            print("after: pe.construct_sources(new_rez)")

        if only_sources_wo_features:
            out_sources_list = []
            for source_dict in pe.sources:
                if source_dict.d['feat_gen_date'] is None:
                    out_sources_list.append(source_dict)
            return (featureless_srcids, out_sources_list)
        else:
            return (featureless_srcids, pe.sources)


    def get_src_obj_list_old(self, ra_numpy64, dec_numpy64, box_range_numpy64,\
                         feat_db, only_sources_wo_features=0):
        """ Intended for INTERNAL calling only.
        Given ra,dec,box-size; finds sources & returns a list of source objects
        """
        ra = float(ra_numpy64) # REDUNDANT, but floats are expected by xmlrpc
        dec = float(dec_numpy64) # REDUNDANT, but floats are expected by xmlrpc
        box_range = float(box_range_numpy64) # REDUNDANT, but floats are expect

        if ((ra < 0) or (ra >= 360) or (dec <= -90) or (dec >= 90) or 
            (box_range < 0.00001) or (box_range > 0.5)):
            #20080225# (box_range < 0.00001) or (box_range > 0.166666)):
            print("Warning: given out of range input:", ra, dec, box_range)
            return {}

        import db_importer
        #import generators_importers

	pe = db_importer.PositionExtractor(pos=(ra, dec),radius=box_range, host="192.168.1.45",port=8000, doplot=False, write_xml=False)

	#pe.search_pos(summary_ps_fpath='/tmp/sources_summary.ps')
	pe.search_pos(summary_ps_fpath='/tmp/sources_summary.ps', \
                      get_sources_for_radec_method=\
                      self.get_sources_for_radec, \
                      skip_construct_sources=True)
        new_rez = feat_db.get_rez_for_featureless_sources(pe.rez)
        pe.construct_sources(new_rez) #, out_xml_fpath='/tmp/out.xml')
        if only_sources_wo_features == 1:
            out_sources_list = []
            for source_dict in pe.sources:
                if source_dict.d['feat_gen_date'] is None:
                    out_sources_list.append(source_dict)
            return out_sources_list
        else:
            return pe.sources


    def get_sources_for_radec_with_feature_extraction(self, ra_numpy64, \
                                   dec_numpy64, box_range_numpy64, write_ps=0,\
                                   only_sources_wo_features=0, \
                                   feat_db=None,
                                   skip_remote_sdss_retrieval=False, skip_check_sdss_objs=False,skip_check_ptel_objs=False, do_logging=False, do_features_gen_insert=True):
        """ Given a position and length of the square region side (in degrees),
        This retrieves a dictionary of sources contained within this region.
        Intermediate steps, to get the sources may include:
          - retrieving SDSS FITS tables from Sloan server
          - re-computing astrometry for these SDSS files
          - insert objects into the Relational Database
          - compute sources for these objects, insert these into source
            database.
          - query sources for this region
        Once this method has successfully run once, the above intermediate
           steps will be internally skipped & subsequent execution will be
           much faster.
        NOTE: initial execution may take 1-10 mins due to possible SDSS data retrieval.
          - subsequent runs should take ~10s seconds.

          - For now I don't allow box_range > 10 arcmin.
          - This will be fixed soon with better spatial query methods.

        Input (in degrees): ra, dec, box_range
             Optional Flag: write_ps==1 # generate a local plot (/tmp/out.ps)

        Output list: [{<source dict>}, {<source dict>}, ...]
           where <source dict> = {<filter>:{<dict of source characteristics>}}
        """
        if feat_db is None:
            #import generators_importers # NEEDED BY: get_features_using_srcid_xml_tuple_list()
            from . import feature_extraction_interface# NEEDED BY: self.get_src_obj_list() 
	    #                                               Feature_database()...

	    feat_db = feature_extraction_interface.Feature_database()
	    feat_db.initialize_mysql_connection(\
                                    rdb_host_ip=self.pars['rdb_features_host_ip'],\
                                    rdb_user=self.pars['rdb_features_user'], \
                                    rdb_name=self.pars['rdb_features_db_name'], \
                                    rdb_port=self.pars['rdb_features_port'], \
                        feat_lookup_tablename=self.pars['feat_lookup_tablename'], \
                        feat_values_tablename=self.pars['feat_values_tablename'])
            feat_db.create_feature_lookup_dict()

        # TODO: pass a flag which limits returned sources to
        #       sources which have had no features generated.
        # TODO: get_src_obj_list() should add a flag to src_obj_list elements:
        #        src_obj_list[0].d['feats_exist'] == 1/0
        (featureless_srcids, src_obj_list) = self.get_src_obj_list(ra_numpy64,\
                                     dec_numpy64, box_range_numpy64, feat_db, \
                             only_sources_wo_features=only_sources_wo_features,\
                          skip_remote_sdss_retrieval=skip_remote_sdss_retrieval,skip_check_sdss_objs=skip_check_sdss_objs,skip_check_ptel_objs=skip_check_ptel_objs, do_logging=do_logging)
        # HACK: Sort and plot only for the top 3 sampled sources:
        sort_source_tuplist = []
        for source_obj in src_obj_list:
            len_list = []
            for filt in source_obj.d['ts'].keys():
                if 'm' in source_obj.d['ts'][filt]:
                    len_list.append(len(source_obj.d['ts'][filt]['m']))
            max_len = max(len_list)
            # 20090717: dstarr comments this:
            #if ((max_len >= 3) and \
            #                   (source_obj.d['src_id'] in featureless_srcids)):
            # 20090717: dstarr uncomments this since we want to generate features again even for sources which had features previously generated (assumedly with fewer epochs):
            if max_len >= 3:
                sort_source_tuplist.append( (max_len,source_obj) )
        sort_source_tuplist.sort()
        sort_source_tuplist.reverse()
        
        srcid_xml_tuple_list = []
        # TODO: Have a nobjs > [thresh], to limit to only well sampled sources:
        #for i in xrange(3):  # This just limited feature generate to 3 srcids
        #    if (len(sort_source_tuplist) >= i+1):
        for i in xrange(len(sort_source_tuplist)):
            (length,source_obj) = sort_source_tuplist[i]
            src_id = source_obj.d['src_id']
            print('N Samples:', length, 'src_id:', src_id)
            srcid_xml_tuple_list.append((src_id, source_obj.xml_string))

        # NOTE: in get_sources_for_radec_with_feature_extraction() we assume
        #       that all given sources do not have features generated.
        if do_logging:
            print("before: get_features_using_srcid_xml_tuple_list()")

        # 20090717: dstarr disables write_ps=1:
        #(signals_list, srcid_dict) = get_features_using_srcid_xml_tuple_list(\
        #                                      srcid_xml_tuple_list, write_ps=1)
        # # # # # #
        if do_features_gen_insert:
    	    (signals_list, srcid_dict) = get_features_using_srcid_xml_tuple_list(\
                                                  srcid_xml_tuple_list, write_ps=0) #, return_gendict=True)
            if do_logging:
                print("before: self.srcdbt.update_featsgen_in_srcid_lookup_table()")

            self.srcdbt.update_featsgen_in_srcid_lookup_table(srcid_dict.keys())
            if do_logging:
                print("before: feat_db.insert_srclist_features_into_rdb_tables()")
    	    feat_db.insert_srclist_features_into_rdb_tables(signals_list,\
                                                            srcid_dict.keys())
            if do_logging:
                print("after: feat_db.insert_srclist_features_into_rdb_tables()")
    	    #return signals_list # This contains feature data
            #NOTE: I think we really just want all sources returned:
        return src_obj_list


    def get_features_for_most_sampled_sources_client_loop(self, srcid_list=[]):
        """ This function continuously polls socket server which returns
        a list of source-ids which have not had features generated, and which
        are reserved for this client function to generated features for.
        Once features are generated, all applicable RDB Tables are updated.

        It is assumed that the srcid-socket server periodically queries for
        most-sampled, but non-feature generated sources, which it has not
        already delegated off as tasks, and passes sources in this list to
        clients.  (obj_id_socket.py)
        """
        import db_importer
	feat_db = feature_extraction_interface.Feature_database()
	feat_db.initialize_mysql_connection(\
                                rdb_host_ip=self.pars['rdb_features_host_ip'],\
                                rdb_user=self.pars['rdb_features_user'], \
                                rdb_name=self.pars['rdb_features_db_name'], \
                                rdb_port=self.pars['rdb_features_port'], \
                    feat_lookup_tablename=self.pars['feat_lookup_tablename'], \
                    feat_values_tablename=self.pars['feat_values_tablename'])
        feat_db.create_feature_lookup_dict()

        if len(srcid_list) > 0:
            unfeated_srcid_list = srcid_list
        else:
            print("ERROR: No sources returned from socket-server")
            raise "ERROR: No sources returned from socket-server"
        # TODO/DEBUG: For now I want to only retrieve sources from socket server
        #else:
        #    select_srcids_str = "SELECT * from srcid_lookup WHERE (feat_gen_date is NULL) ORDER BY nobjs DESC LIMIT 100000"
        #    feat_db.cursor.execute(select_srcids_str)
        #    results = feat_db.cursor.fetchall()
        #    unfeated_srcid_list = []
        #    for result in results:
        #        unfeated_srcid_list.append(result[0])
        return_srcid_xml_tuple_list = []
        rdb_write_srcid_strs = []
        for unfeat_srcid in unfeated_srcid_list:
            obj_epoch_list = []
            if self.rdbt.sdss_tables_available == 1:
                join_str = "JOIN %s USING (obj_id)" % (\
                                       self.pars['obj_srcid_lookup_tablename'])
                constraint_str = "(obj_srcid_lookup.src_id = %d)" % (\
                                                                  unfeat_srcid)
                obj_epoch_list = self.rdbt.select_and_form_objepoch_dict_using_constraint(constraint_str, self.pars['rdb_table_names']['sdss'], survey_name='sdss', survey_num=0, join_str=join_str, filter_duplicate_time_data=True)
            # Comment out pairitel source stuff for now:
            #if self.rdbt.ptel_tables_available == 1:
            #    if (((ra_high - ra_low) < \
            #                   self.pars['degree_threshold_DIFHTM_14_to_25']) or \
            #       ((dec_high - dec_low) < \
            #                   self.pars['degree_threshold_DIFHTM_14_to_25']) or \
            #        (force_HTM25 == 1)):
            #        DIF_HTM_tablename =self.pars['ptel_object_table_name_DIF_HTM25']
            #    else:
            #        DIF_HTM_tablename =self.pars['ptel_object_table_name_DIF_HTM14']
            #    constraint_str = "DIF_HTMRectV(%lf, %lf, %lf, %lf)" % (ra_low, dec_low, ra_high, dec_high)
            #    obj_epoch_list_2 = self.rdbt.select_and_form_objepoch_dict_using_constraint(constraint_str, DIF_HTM_tablename, survey_name='pairitel', survey_num=1)
            #    obj_epoch_list.extend(obj_epoch_list_2)

            mp = Make_Plots(self.pars)
            source_dict = mp.form_source_dict_using_obj_epoch_list(obj_epoch_list)
            rez = source_dict.values()# each value-dict corresponds toa a srcid.

            #    ??? I think 'pos' flag can be empty:
            pe = db_importer.PositionExtractor(doplot=False, write_xml=False, do_remote_connection=0)
            try:
                pe.construct_sources(rez) #, out_xml_fpath='/tmp/out.xml')
            except:
                continue # skip this source.  KLUDGE: Every subsequent run will fail on this top-sampled source, unless we can flag it bad somehow.
            src_obj_list = pe.sources
            srcid_table_update_str = ""
            total_feats_insert_list = []
            srcid_xml_tuple_list = []
            for source_obj in src_obj_list:
                src_id = source_obj.d['src_id']
                print('src_id:', src_id)
                
                srcid_xml_tuple_list.append((src_id, source_obj.xml_string))
                #(signals_list, srcid_dict) = \
                #                      get_features_using_srcid_xml_tuple_list(\
                #                              srcid_xml_tuple_list, write_ps=0)
                #for srcid in srcid_dict.keys():
                #    srcid_table_update_str += "UPDATE %s SET feat_gen_date=NOW() WHERE src_id=%d; " % (self.pars['srcid_table_name'], src_id)
                #individ_feats_insert_list = feat_db.insert_srclist_features_into_rdb_tables(signals_list,srcid_dict.keys(), do_rdb_insert=False)
                #total_feats_insert_list.extend(individ_feats_insert_list)

            # 20080608: dstarr drops the next few lines out of "for loop":
            (signals_list, srcid_dict) = \
                                      get_features_using_srcid_xml_tuple_list(\
                                              srcid_xml_tuple_list, write_ps=0)
            
            # Here we add the features to each source's xml-string
            #    and re-store it so we can parse it later.
            for source_obj in src_obj_list:
                source_obj.x_sdict = source_obj.d # I think this works
                source_obj.add_features_to_xml_string(signals_list)
            for i in xrange(len(srcid_xml_tuple_list)):
                src_id = srcid_xml_tuple_list[i][0]
                for source_obj in src_obj_list:
                    if source_obj.d['src_id'] == src_id:
                        srcid_xml_tuple_list[i] = (src_id, \
                                               copy.copy(source_obj.xml_string))
                        break

            return_srcid_xml_tuple_list.extend(srcid_xml_tuple_list) # Do this
            #   here because srcid_xml_tuple_list[] has been updated with
            #   feature included xml_strings

            for src_id in srcid_dict.keys():
                srcid_table_update_str += "UPDATE %s SET feat_gen_date=NOW() WHERE src_id=%d; " % (self.pars['srcid_table_name'], src_id)
            #self.srcdbt.update_featsgen_in_srcid_lookup_table(\
            #                                             srcid_dict.keys())
            (individ_feats_insert_list, used_filters_list) = feat_db.insert_srclist_features_into_rdb_tables(signals_list,srcid_dict.keys(), do_rdb_insert=False)
            total_feats_insert_list.extend(individ_feats_insert_list)

        total_feats_insert_list.insert(0,"INSERT INTO %s (src_id, feat_id, feat_val, feat_weight) VALUES " % (feat_db.feat_values_tablename))

        feat_db.cursor.execute(''.join(total_feats_insert_list)[:-2])
        self.srcdbt.cursor.execute("LOCK TABLES %s WRITE" % (self.pars['srcid_table_name']))
        self.srcdbt.cursor.execute(srcid_table_update_str)
        self.srcdbt.cursor.execute("UNLOCK TABLES")
        return return_srcid_xml_tuple_list


    def get_sources_using_xml_file_with_feature_extraction(self, srcid_uri, \
                                    xml_fpath, only_sources_wo_features=0, \
                                    do_delete_existing_featvals=False):
        """ XML-file adaptation of (above)
                                get_sources_for_radec_with_feature_extraction()
        """
	feat_db = feature_extraction_interface.Feature_database()
	feat_db.initialize_mysql_connection(\
                                rdb_host_ip=self.pars['rdb_features_host_ip'],\
                                rdb_user=self.pars['rdb_features_user'], \
                                rdb_name=self.pars['rdb_features_db_name'], \
                                rdb_port=self.pars['rdb_features_port'], \
                    feat_lookup_tablename=self.pars['feat_lookup_tablename'], \
                    feat_values_tablename=self.pars['feat_values_tablename'])
        feat_db.create_feature_lookup_dict()

        use_fpath = xml_fpath
        summary_img_fpath = xml_fpath + '.png'
        if "http" in xml_fpath:
            random_str = "%d" % (numpy.random.random_integers(1000000000))
            wget_fpath = "/tmp/%s.wget" % (random_str)
            summary_img_fpath = "/tmp/%s_feat_summary.png" % (random_str)

            # 20100706 older: #wget_str = "wget -t 30 -T 5 -O %s %s" % (wget_fpath, xml_fpath)
            fp_xml = urllib.urlopen(xml_fpath)
            use_fpath = fp_xml.read()
            fp_xml.close()
            
            """ # 20100706 older:
            os.system(wget_str)
            if os.path.exists(wget_fpath):
                use_fpath = wget_fpath
            else:
                wget_str = "wget -t 30 -T 5 -O %s %s" % (wget_fpath, xml_fpath)
                os.system(wget_str)
                if os.path.exists(wget_fpath):
                    use_fpath = wget_fpath
                else:
                    return -1
            """

        #if 'ivo' in srcid_uri:
        #    srcid_num = int(srcid_uri[srcid_uri.rfind('#')+1:])
        #else:
        #    srcid_num = int(srcid_uri)
        srcid_num = int(srcid_uri)
        srcid_xml_tuple_list = [(srcid_num, use_fpath)]

        srcid_xmlstring_dict = {}
        # NOTE: in get_sources_for_radec_with_feature_extraction() we assume
        #       that all given sources do not have features generated.
	(signals_list, srcid_dict) = get_features_using_srcid_xml_tuple_list( \
                             srcid_xml_tuple_list, ps_fpath=summary_img_fpath,\
                             return_gendict=True, \
                             xmlstring_dict_tofill=srcid_xmlstring_dict)

        os.system("rm " + use_fpath) # remove temporary wget'd xml file

        # Write xml_strings to file, for later use by ARFFify code:
        for src_id,xml_string in srcid_xmlstring_dict.iteritems():
            #fpath = "/home/pteluser/scratch/TUTOR_vosources/%d.xml" % (src_id)
            #20090319#fpath = os.path.expandvars("$TCP_DATA_DIR/%d.xml" % (src_id))
            fpath = "%s/%d.xml" % (self.pars['local_vosource_xml_write_dir'],src_id)
            if os.path.exists(fpath):
                os.system("rm " + fpath)
            fp = open(fpath, 'w').write(xml_string)

        insert_str = "INSERT INTO %s (src_id, ra, decl, ra_rms, dec_rms, nobjs, feat_gen_date) VALUES (%d, %lf, %lf, %lf, %lf, %d, NOW())" % \
                     (self.pars['srcid_table_name'], srcid_num, srcid_dict[srcid_num]['ra'], srcid_dict[srcid_num]['dec'], srcid_dict[srcid_num]['ra_rms'], srcid_dict[srcid_num]['dec_rms'], len(srcid_dict[srcid_num]['ts'][srcid_dict[srcid_num]['ts'].keys()[0]]['t']))
        
        try:
            self.srcdbt.cursor.execute(insert_str)
        except:
            print("ERROR: source", srcid_num, "already exists in", self.pars['srcid_table_name'], "Continuing...")


        srcid_list = srcid_dict.keys()
	(insert_list, used_filters_list) = feat_db.insert_srclist_features_into_rdb_tables( \
                                                      signals_list, srcid_list, \
                                                      do_delete_existing_featvals=do_delete_existing_featvals)
        self.srcdbt.update_featsgen_in_srcid_lookup_table(srcid_list, used_filters_list=used_filters_list)
        remote_img_url = feat_db.scp_feat_summary_img_to_webserver(\
                       summary_img_fpath=summary_img_fpath,\
                       feature_summary_webserver_name=\
                           self.pars['feature_summary_webserver_name'],\
                       feature_summary_webserver_user=\
                           self.pars['feature_summary_webserver_user'],\
                       feature_summary_webserver_dirpath=\
                           self.pars['feature_summary_webserver_dirpath'],\
                       feature_summary_webserver_url_prefix=\
                           self.pars['feature_summary_webserver_url_prefix'])


        # TODO: access srcid_dict[srd_id]['classes'] and insert into RDB.
        # TODO: test that this code runs on it's own, using
        #     populate_feat_db_using_TCPTUTOR_sources.py ssh case.

        # TODO: need shema_id & source_id
        self.pars['sci_class_schema_id']

        classdb_db = MySQLdb.connect(host=self.pars['classdb_hostname'], \
                                  user=self.pars['classdb_username'], \
                                  db=self.pars['classdb_database'],\
                                  port=self.pars['classdb_port'])
        classdb_cursor = classdb_db.cursor()

        #insert_str = "INSERT INTO src_class_probs (schema_id, class_id, src_id, gen_dtime) VALUES (%s, %d, %d, NOW())" % (self.pars['sci_class_schema_id'], class_id, srcid_num) 

        #insert_list = ["INSERT INTO src_class_probs (schema_id, class_id, src_id, is_primary_class, gen_dtime) VALUES "]
        insert_list = ["INSERT INTO src_class_probs (schema_id, class_id, src_id, class_rank, gen_dtime) VALUES "]
        for source_id,source_dict in srcid_dict.iteritems():
            ## ## ##first_class = 1
            ### KLUDGE 20100702 dstarr comments out and makes modified insert 2 lines below:
            #insert_list.append("(%s, (SELECT DISTINCT class_id FROM classid_lookup WHERE class_short_name='%s'), %d, %d, NOW()), " % (self.pars['sci_class_schema_id'], source_dict['class'], srcid_num, first_class))
            insert_list.append("(%d, (SELECT class_id FROM classid_lookup WHERE class_name='%s' AND schema_id=%d ORDER BY class_id LIMIT 1), %d, 0, NOW()), " % (int(self.pars['sci_class_schema_id']), source_dict['class'], int(self.pars['sci_class_schema_id']), srcid_num))
            ## ## ## This is useful if we had multiple classes, probabilities:
            #if first_class:
            #    first_class = 0
        ### 20100702: disabled try/except
        #try:
        if 1:
            classdb_cursor.execute(''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE class_id=VALUES(class_id), gen_dtime=VALUES(gen_dtime)")
        #except:
        #    print ''.join(insert_list)[:-2]
        #    print "MySQL src_class_probs table INSERT error.  Probably classid_lookup table unknown class: ", source_dict['class']
        

        
        #############
	#return signals_list # This contains feature data
        #NOTE: I think we really just want all sources returned:

        # # # # # # # #
        # TODO: scp image to web server/directory
        # print to stdio: URL of image
        # print to stdio: feature Database id
        # print to stdio: feature values???  
        # return:
        #  - formatted table with image-link
        #  - srcid info.
        #  - with srcid info so php can query feature database and select *

        if "http" in xml_fpath:
            os.system("rm %s" % (wget_fpath))
            os.system("rm %s" % (summary_img_fpath))
        return (srcid_num, remote_img_url)


if __name__ == '__main__':
    t_start = datetime.datetime.now()

    param_tool.add_command_args(pars, 0)
    htm_tools = HTM_Tools(pars)

    rcd = RDB_Column_Defs(\
                rdb_table_names=pars['rdb_table_names'], \
                rdb_db_name=pars['rdb_name_2'], \
                rdb_port=pars['rdb_port_2'],
                col_definitions=new_rdb_col_defs)
    rcd.init_generate_mysql_strings(pars)

    rdbt = Rdb_Tools(pars, rcd, htm_tools, \
                rdb_host_ip=pars['rdb_host_ip_2'], \
                rdb_user=pars['rdb_user'], \
                rdb_name=pars['rdb_name_2'], \
                rdb_port=pars['rdb_port_2'])

    sdss_fcr_iso = SDSS_FCR_Ingest_Status_Object(\
                rdb_host_ip=pars['rdb_host_ip_3'], \
                rdb_user=pars['rdb_user'], \
                rdb_name=pars['rdb_name_3'], \
                rdb_port=pars['rdb_port_3'], \
                table_name=pars['sdss_fields_table_name'], \
                sdss_fields_doc_fpath_list=pars['sdss_fields_doc_fpath_list'],\
                hostname=pars['hostname'])

    srcdbt = Source_Database_Tools(pars, rcd, htm_tools, \
                rdb_host_ip=pars['rdb_host_ip_4'], \
                rdb_user=pars['rdb_user_4'],\
                rdb_name=pars['rdb_name_4'], \
                rdb_port=pars['rdb_port_4'])
    slfits_repo = SDSS_Local_Fits_Repository(pars)

    # DEBUG PRINT: 
    #show_create_commands(rcd, srcdbt)
    tcp_runs = TCP_Runtime_Methods(cur_pid=cur_pid)

    ra = numpy.float64(float(pars['ra']))
    dec = numpy.float64(float(pars['dec']))
    box_degree_range = numpy.float64(float(pars['degree_range']))# total: x' on a side

    if pars['do_pairitel_pkl_ingest'] == '1':
        rdbt.insert_pairitel_astrometry_into_rdb(pickle_fpath=\
                                                        pars['ptel_pkl_fpath'])
    elif pars['do_populate_srcid'] == '1':
        # This TESTS the main source finding algorithms (w/o XMLRPC wrapper):
        ### Run a source-finding loop:
        #tcp_runs.populate_srcid_table_loop(pars, srcdbt, rdbt, \
        #                               box_degree_range=box_degree_range, \
        #                               box_overlap_factor=0.05)
        ### Run just for a single ra,dec:
        tcp_runs.populate_srcid_table_loop(pars, srcdbt, rdbt, \
                                       box_degree_range=box_degree_range, \
                                       box_overlap_factor=0.05, \
                                       ra=float(pars['ra']), \
                                       dec=float(pars['dec']))
    elif pars['do_plot_radec'] == '1':
        # dstarr's source field plotting routines:
        xrsio = XRPC_RDB_Server_Interface_Object(pars, tcp_runs, rdbt, htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)
        src_list =xrsio.get_sources_for_radec(ra, dec, box_degree_range, \
                                              '/tmp/out.ps')
        print("Num sources found:", len(src_list))
        # USING the following routines is obsolete, since no source generation:
        #mp = Make_Plots(pars)
        #mp.query_plot_ra_dec(pars, rdbt, htm_tools, ra, dec, \
        #                                                 box_degree_range/2.0)
    elif pars['do_get_sources_radec'] == '1':
        # XMLRPC non-feature source population:
        # # # # # #
        # NOTE: we assume here we are only interested in populating non PTF (i.e. SDSS) data & sources for this data.
        xrsio = XRPC_RDB_Server_Interface_Object(pars, tcp_runs, rdbt, htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)
        src_list =xrsio.get_sources_for_radec(ra, dec, box_degree_range, '', skip_check_ptf_objs=True, \
                                              only_plot=0) #only_plot=0: means sources will be found for objects in field.  # ??? Also, I seem to recall that flags can't be used with XMLRPC ???
        print("Num sources found:", len(src_list))
    elif pars['do_get_source_features_radec'] == '1':
        # XMLRPC Source population with feature generation:
        xrsio = XRPC_RDB_Server_Interface_Object(pars, tcp_runs, rdbt, \
                                   htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)
        src_list = xrsio.get_sources_for_radec_with_feature_extraction(ra,dec,\
                                                 box_degree_range, write_ps=1,\
                                                 only_sources_wo_features=0)
        print("Num sources found:", len(src_list))
    elif pars['do_get_sources_using_xml_file_with_feature_extraction'] == '1':
        xrsio = XRPC_RDB_Server_Interface_Object(pars, tcp_runs, rdbt, \
                                  htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)
        if pars['do_delete_existing_featvals'] == 0:
            # This is the default case defined in pars.  Any other set value will be a string
            do_delete_existing_featvals = False
        else:
            do_delete_existing_featvals = True
        xrsio.get_sources_using_xml_file_with_feature_extraction(\
                            pars['vosource_srcid'], \
                            pars['vosource_url'], only_sources_wo_features=0, \
                            do_delete_existing_featvals=do_delete_existing_featvals)

    elif pars['do_populate_feats_client_loop'] == '1':
        # XMLRPC Source population with feature generation:
        xrsio = XRPC_RDB_Server_Interface_Object(pars, tcp_runs, rdbt, \
                                   htm_tools, srcdbt, sdss_fcr_iso, slfits_repo)
        xrsio.get_features_for_most_sampled_sources_client_loop(\
                                                    do_write_vosource_xml=True)
    elif pars['do_test_a'] == '1':
        # XMLRPC Source population with feature generation:
        srcid_xml_tuple_list = [('srcidblah', '/home/dstarr/scratch/xml/source3.blah.xml')]
        (signals_list, srcid_dict) = get_features_using_srcid_xml_tuple_list(srcid_xml_tuple_list, write_ps=1)

    elif pars['do_rpc_server'] == '1':
        print("XMLRPC Server Mode...")
        import SimpleXMLRPCServer
        server = SimpleXMLRPCServer.SimpleXMLRPCServer(\
                              (pars['xmlrpc_server_name'], \
                               int(pars['xmlrpc_server_port'])),\
                               allow_none=True)
        server.register_instance(XRPC_RDB_Server_Interface_Object(\
           pars, tcp_runs, rdbt, htm_tools, srcdbt, sdss_fcr_iso, slfits_repo))
        server.register_multicall_functions()
        server.register_introspection_functions()
        server.serve_forever()
    elif pars['do_sdss_ingest_radec'] == '1':
        # Populate the sdss_events table with all (f,c,r) data, for a (ra,dec):
        tcp_runs.sdss_rfc_ingest_using_ra_dec(pars, rdbt, slfits_repo, \
                         sdss_fcr_iso, ra=ra, dec=dec, do_delete_scratch_dir=0)
    elif pars['do_populate_sdss'] == '1':
        # This populates the sdss_events table by randomly choosing an uningested (fcr):
        tcp_runs.loop_sdss_rfc_ingest(rdbt, sdss_fcr_iso, \
                                     n_iters=100000, do_delete_scratch_dir=1)


    # NOTE: I tried doing this in a __del__(), and then executing "del tcp_runs" here, but it didn't work, so I explicitly do this:
    if len(tcp_runs.tcp_data_dir) > 9:
        os.system("rm -Rf " + tcp_runs.tcp_data_dir)

    t_finish = datetime.datetime.now()
    print("Run Time:", str(t_finish - t_start))

    ################################
    # NOTES:
    ################################
    """
    ### UNCOMMENT the following, to populate the DBXML-DATABASE:
    import dbxml_test

    print 'Populating XML DB with MySQL DB entries...'
    import dbxml_test
    db_fpath = '/tmp/test.dbxml'
    dbxml_cont = dbxml_test.DBXML_Container_Instance()

    os.system('rm ' + db_fpath) # DEBUG KLUDGE TODO: I'm not using the dbxml at the moment
    if not os.path.exists(db_fpath):
        dbxml_cont.create(db_fpath)
    else:
        dbxml_cont.open(db_fpath)
    rdbt.populate_xmldb_using_rdb(dbxml_cont, rcd.rdb_ind['pairitel'], \
                          rcd.rdb_table_names['pairitel'], row_limit=100)
    rdbt.populate_xmldb_using_rdb(dbxml_cont, rcd.rdb_ind['sdss'], \
                          rcd.rdb_table_names['sdss'], row_limit=100)
    dbxml_cont.close()

    ### THE FOLLOWING DOES A SIMPLE XQUERY search of the XML-Database:
    #     using positional accuracy:   pars['htm_id_query_depth']
    print 'Querying XML DB...'
    dbxml_cont.open(db_fpath)
    tme_list = rdbt.do_xmlquery_using_htm(dbxml_cont, query_ra, query_dec, \
                                                filter_i=query_filter_num)
    dbxml_cont.close()
    """
    """
(13:28:29) Josh: yeah...that's not gonna happend. Can you give some thought to implimentation of a footprint server in postgresl or mysql?
(13:28:38) Josh: I think we need to be able to ask:
(13:29:01) Josh: "At this RA, DEC what observations we taken"
(13:29:30) Josh: "What were the limiting magnitudes at this point in the sky"
(13:29:41) Josh: the JHU footprint server
(13:29:44) Josh: is good
(13:29:51) Josh: but I dont want to host stuff offsite
(13:30:03) Josh: it's also Microsoft + SQLServer + HTM
(13:30:15) Josh: and I'd rather do q3c + postgresl
(13:30:46) me: ok, I'll start thinking about that in a survey/observatory independent way
(13:30:54) Josh: underneath the hood it seems that once the spatial overlaps are computed
(13:30:57) Josh: then it's trivial

        'WEKA full':{ \
            'schema_id':2, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$TCP_DIR/Data/current_weka_full.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$TCP_DIR/Data/current_training_weka_full.arff'),
            'schema_comment':\
                   'Trained using 20090129 33class arff',
            'predicts_multiple_classes':True,
            },


    """
    """ 20090707 commented out:
        '50nois_09epch_100need_0.050mtrc_short1':{ \
            'schema_id':10, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_09epch_100need_0.050mtrc_short1/50nois_09epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_09epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_09epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_07epch_100need_0.050mtrc_short1':{ \
            'schema_id':13, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_07epch_100need_0.050mtrc_short1/50nois_07epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_07epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_07epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_11epch_100need_0.050mtrc_short1':{ \
            'schema_id':14, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_11epch_100need_0.050mtrc_short1/50nois_11epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_11epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_11epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_08epch_100need_0.050mtrc_sh7.5':{ \
            'schema_id':23, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_sh7.5/50nois_08epch_100need_0.050mtrc_sh7.5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_sh7.5/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_08epch_100need_0.050mtrc_sh7.5',
            'predicts_multiple_classes':True,
            },
        '50nois_12epch_100need_0.050mtrc_sh7.5':{ \
            'schema_id':25, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_12epch_100need_0.050mtrc_sh7.5/50nois_12epch_100need_0.050mtrc_sh7.5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_12epch_100need_0.050mtrc_sh7.5/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_12epch_100need_0.050mtrc_sh7.5',
            'predicts_multiple_classes':True,
            },
        '50nois_15epch_100need_0.050mtrc_sh7.5':{ \
            'schema_id':26, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_sh7.5/50nois_15epch_100need_0.050mtrc_sh7.5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_sh7.5/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_15epch_100need_0.050mtrc_sh7.5',
            'predicts_multiple_classes':True,
            },


    
    """
    """ Pre 200906:
        '20090417_50noisy_10epoch_100needed_004metric_thinned5':{ \
            'schema_id':2, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_10epoch_100needed_004metric_thinned5/20090417_50noisy_10epoch_100needed_004metric_thinned5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_10epoch_100needed_004metric_thinned5/noisified_for_training.arff'),
            'schema_comment':\
                   '20090417_50noisy_10epoch_100needed_004metric_thinned5',
            'predicts_multiple_classes':True,
            },
        '20090417_50noisy_15epoch_100needed_005metric_thinned5':{ \
            'schema_id':3, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_15epoch_100needed_005metric_thinned5/20090417_50noisy_15epoch_100needed_005metric_thinned5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_15epoch_100needed_005metric_thinned5/noisified_for_training.arff'),
            'schema_comment':\
                   '20090417_50noisy_15epoch_100needed_005metric_thinned5',
            'predicts_multiple_classes':True,
            },
        '20090417_50noisy_20epoch_100needed_005metric_thinned5':{ \
            'schema_id':4, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_20epoch_100needed_005metric_thinned5/20090417_50noisy_20epoch_100needed_005metric_thinned5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/20090417_50noisy_20epoch_100needed_005metric_thinned5/noisified_for_training.arff'),
            'schema_comment':\
                   '20090417_50noisy_20epoch_100needed_005metric_thinned5',
            'predicts_multiple_classes':True,
            },
        '50nois_05epch_100need_0.050mtrc_1':{ \
            'schema_id':5, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_05epch_100need_0.050mtrc_1/50nois_05epch_100need_0.050mtrc_1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_05epch_100need_0.050mtrc_1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_05epch_100need_0.050mtrc_1',
            'predicts_multiple_classes':True,
            },
        '50nois_06epch_100need_0.050mtrc_1':{ \
            'schema_id':6, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_06epch_100need_0.050mtrc_1/50nois_06epch_100need_0.050mtrc_1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_06epch_100need_0.050mtrc_1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_06epch_100need_0.050mtrc_1',
            'predicts_multiple_classes':True,
            },
        '50nois_07epch_100need_0.050mtrc_1':{ \
            'schema_id':7, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_07epch_100need_0.050mtrc_1/50nois_07epch_100need_0.050mtrc_1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_07epch_100need_0.050mtrc_1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_07epch_100need_0.050mtrc_1',
            'predicts_multiple_classes':True,
            },
        '50nois_08epch_100need_0.050mtrc_1':{ \
            'schema_id':8, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_1/50nois_08epch_100need_0.050mtrc_1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_08epch_100need_0.050mtrc_1',
            'predicts_multiple_classes':True,
            },
        '50nois_09epch_100need_0.050mtrc_1':{ \
            'schema_id':9, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_09epch_100need_0.050mtrc_1/50nois_09epch_100need_0.050mtrc_1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_09epch_100need_0.050mtrc_1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_09epch_100need_0.050mtrc_1',
            'predicts_multiple_classes':True,
            },
    ######### Commented out on 20090817:

        '50nois_08epch_100need_0.050mtrc_short1':{ \
            'schema_id':11, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_short1/50nois_08epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_08epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_10epch_100need_0.050mtrc_short1':{ \
            'schema_id':12, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_short1/50nois_10epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_10epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_06epch_100need_0.050mtrc_short1':{ \
            'schema_id':15, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_06epch_100need_0.050mtrc_short1/50nois_06epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_06epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_06epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_15epch_100need_0.050mtrc_short1':{ \
            'schema_id':16, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_short1/50nois_15epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_15epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_20epch_100need_0.050mtrc_short1':{ \
            'schema_id':17, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_short1/50nois_20epch_100need_0.050mtrc_short1.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_short1/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_20epch_100need_0.050mtrc_short1',
            'predicts_multiple_classes':True,
            },
        '50nois_08epch_100need_0.050mtrc_sh17.9':{ \
            'schema_id':18, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_sh17.9/50nois_08epch_100need_0.050mtrc_sh17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_08epch_100need_0.050mtrc_sh17.9/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_08epch_100need_0.050mtrc_sh17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_10epch_100need_0.050mtrc_sh17.9':{ \
            'schema_id':19, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_sh17.9/50nois_10epch_100need_0.050mtrc_sh17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_sh17.9/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_10epch_100need_0.050mtrc_sh17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_12epch_100need_0.050mtrc_sh17.9':{ \
            'schema_id':20, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_12epch_100need_0.050mtrc_sh17.9/50nois_12epch_100need_0.050mtrc_sh17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_12epch_100need_0.050mtrc_sh17.9/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_12epch_100need_0.050mtrc_sh17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_15epch_100need_0.050mtrc_sh17.9':{ \
            'schema_id':21, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_sh17.9/50nois_15epch_100need_0.050mtrc_sh17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_sh17.9/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_15epch_100need_0.050mtrc_sh17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_20epch_100need_0.050mtrc_sh17.9':{ \
            'schema_id':22, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_sh17.9/50nois_20epch_100need_0.050mtrc_sh17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_sh17.9/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_20epch_100need_0.050mtrc_sh17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_10epch_100need_0.050mtrc_sh7.5':{ \
            'schema_id':24, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_sh7.5/50nois_10epch_100need_0.050mtrc_sh7.5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_10epch_100need_0.050mtrc_sh7.5/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_10epch_100need_0.050mtrc_sh7.5',
            'predicts_multiple_classes':True,
            },
        '50nois_20epch_100need_0.050mtrc_sh7.5':{ \
            'schema_id':27, # For Weka, this can be found/generated by code
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_sh7.5/50nois_20epch_100need_0.050mtrc_sh7.5.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_sh7.5/noisified_for_training.arff'),
            'schema_comment':\
                   '50nois_20epch_100need_0.050mtrc_sh7.5',
            'predicts_multiple_classes':True,
            },


###### 20091018 removed:
        '50nois_20epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':28, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_qk17.9/50nois_20epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_20epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_20epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_15epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':29, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_qk17.9/50nois_15epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_15epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_15epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_23epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':30, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_23epch_100need_0.050mtrc_qk17.9/50nois_23epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_23epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_23epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_11epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':31, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_11epch_100need_0.050mtrc_qk17.9/50nois_11epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_11epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_11epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_13epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':32, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_13epch_100need_0.050mtrc_qk17.9/50nois_13epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_13epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_13epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_17epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':33, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/50nois_17epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_17epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_19epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':34, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9/50nois_19epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_19epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_21epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':35, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_21epch_100need_0.050mtrc_qk17.9/50nois_21epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_21epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_21epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_25epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':36, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_25epch_100need_0.050mtrc_qk17.9/50nois_25epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_25epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_25epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_27epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':37, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_27epch_100need_0.050mtrc_qk17.9/50nois_27epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_27epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_27epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_30epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':38, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_30epch_100need_0.050mtrc_qk17.9/50nois_30epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_30epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_30epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_35epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':39, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_35epch_100need_0.050mtrc_qk17.9/50nois_35epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_35epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_35epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },
        '50nois_40epch_100need_0.050mtrc_qk17.9':{ \
            'schema_id':40, # For Weka, this can be found/generated by code
            'general_class_weight':1.0,
            'specific_class_weight_dict':{},
            'weka_training_model_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_40epch_100need_0.050mtrc_qk17.9/50nois_40epch_100need_0.050mtrc_qk17.9.model'),
            'weka_training_arff_fpath':os.path.expandvars(\
                  '$HOME/scratch/Noisification/50nois_40epch_100need_0.050mtrc_qk17.9/noisified_for_training.arff'),
            'schema_comment':\
                                              '50nois_40epch_100need_0.050mtrc_qk17.9',
            'predicts_multiple_classes':True,
            },




    """
