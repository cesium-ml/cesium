#!/usr/bin/env python
import sys, os
import cPickle
import time
import gzip
sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
import pairwise_classification
#pid = str(os.getpid())
#os.system('echo "' + pid + '" > /tmp/pairwise_pid.pid')
#time.sleep(2)
#pid_read = open('/tmp/pairwise_pid.pid').read().strip()
#if pid == pid_read:
    #os.system(os.path.expandvars("scp -c blowfish pteluser@192.168.1.25:/home/pteluser/scratch/pairwise_trainingsets.tar.gz $HOME/scratch/"))
    #os.system(os.path.expandvars("scp -c blowfish pteluser@192.168.1.25:/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz $HOME/scratch/"))
#os.system(os.path.expandvars("tar -C $HOME/scratch -xzf /home/pteluser/scratch/pairwise_trainingsets.tar.gz"))

WekaPairwiseClassification = pairwise_classification.Weka_Pairwise_Classification(pars={'pruned_classif_summary_stats_pkl_fpath': '/global/home/users/dstarr/scratch/pruned_classif_summary_stats.pkl', 'feat_dist_plots': False, 'pairwise_classifier_pklgz_dirpath': '/global/home/users/dstarr/scratch/pairwise_classifiers', 'taxonomy_prune_defs': {'terminating_classes': ['mira', 'sreg', 'rv', 'dc', 'piic', 'cm', 'rr-ab', 'rr-c', 'rr-d', 'ds', 'lboo', 'bc', 'spb', 'gd', 'be', 'pvsg', 'CP', 'wr', 'tt', 'haebe', 'sdorad', 'ell', 'alg', 'bly', 'wu']}, 'crossvalid_nfolds': 10, 't_sleep': 0.20000000000000001, 'feat_dist_image_remote_scp_str': 'pteluser@lyra.berkeley.edu:www/dstarr/pairwise_images/', 'pairwise_schema_name': 'noprune', 'debosscher_classes': False, 'arff_has_ids': False, 'classification_summary_pklgz_fpath': '/global/home/users/dstarr/scratch/xmls_deboss_percentage_exclude__pairwise_result_classification_summary.pkl.gz', 'feat_distrib_classes': {'target_class': 'lboo', 'comparison_classes': ['pvsg', 'gd', 'ds']}, 'tcp_port': 3306, 'pairwise_classifier_dirpath': '/global/home/users/dstarr/scratch/pairwise_classifiers', 'min_num_sources_for_pairwise_class_inclusion': 6, 'arff_has_classes': True, 'num_percent_epoch_error_iterations': 1, 'debosscher_confusion_table3_fpath': '/global/home/users/dstarr/src/TCP/Data/debosscher_table3.html', 'cyto_work_final_fpath': '/global/home/users/dstarr/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher', 'cyto_network_fname': 'pairwise_class.cyto.network', 'crossvalid_do_stratified': False, 'pairwise_trainingset_dirpath': '/global/home/users/dstarr/scratch/pairwise_trainingsets', 'tcp_database': 'source_test_db', 'dotastro_arff_fpath': '/global/home/users/dstarr/scratch/xmls_deboss_percentage_exclude.arff', 'arff_sciclass_dict_pkl_fpath': '/global/home/users/dstarr/scratch/arff_sciclass_dict.pkl', 'trainset_pruned_pklgz_fpath': '/global/home/users/dstarr/scratch/xmls_deboss_percentage_exclude__pairwise_result.pkl.gz', 'feat_dist_image_rooturl': 'http://lyra.berkeley.edu/~jbloom/dstarr/pairwise_images', 'tcp_username': 'pteluser', 'crossvalid_pklgz_fpath': '/global/home/users/dstarr/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result__crossvalid_data.pkl.gz', 'tcp_hostname': '192.168.1.25', 'confusion_stats_html_fpath': '/global/home/users/dstarr/scratch/xmls_deboss_percentage_exclude__pairwise_result_classif_stats.html', 'debosscher_class_lookup': {'BE': 'be', 'RRAB': 'rr-ab', 'MIRA': 'mira', 'WR': 'wr', 'SDBV': 'sdbv', 'FUORI': 'fuor', 'RVTAU': 'rv', 'DMCEP': 'cm', 'GDOR': 'gd', 'LBV': 'sdorad', 'ROAP': 'rot', 'RRD': 'rr-d', 'RRC': 'rr-c', 'DAV': 'pwd', 'SXPHE': 'sx', 'HAEBE': 'haebe', 'SPB': 'spb', 'LBOO': 'lboo', 'ELL': 'ell', 'XB': 'xrbin', 'BCEP': 'bc', 'EA': 'alg', 'PTCEP': 'piic', 'SLR': 'NOTMATCHED', 'EB': 'bly', 'EW': 'wu', 'CP': 'CP', 'CV': 'cv', 'PVSG': 'pvsg', 'TTAU': 'tt', 'DSCUT': 'ds', 'CLCEP': 'dc', 'SR': 'sreg', 'GWVIR': 'gw', 'DBV': 'pwd'}, 'debosscher_confusion_table4_fpath': '/global/home/users/dstarr/src/TCP/Data/debosscher_table4.html', 'pairwise_scratch_dirpath': '/media/raid_0/pairwise_scratch', 'feat_dist_image_local_dirpath': '/media/raid_0/pairwise_scratch/pairwise_scp_data', 'feat_distrib_colors': ['#000000', '#ff3366', '#660000', '#aa0000', '#ff0000', '#ff6600', '#996600', '#cc9900', '#ffff00', '#ffcc33', '#ffff99', '#99ff99', '#666600', '#99cc00', '#00cc00', '#006600', '#339966', '#33ff99', '#006666', '#66ffff', '#0066ff', '#0000cc', '#660099', '#993366', '#ff99ff', '#440044'], 'number_threads': 13, 'cyto_nodeattrib_fname': 'pairwise_class.cyto.nodeattrib', 'plot_symb': ['o', 's', 'v', 'd', '<'], 'weka_pairwise_classifiers_pkl_fpath': '/global/home/users/dstarr/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/weka_pairwise_classifier.pkl'})
fp=open(os.path.expandvars('$HOME/scratch/pairwise_classifier__debosscher_table3.pkl.gz'),'rb')
pairwise_dict=cPickle.load(fp)
fp.close()
WekaPairwiseClassification.load_weka_classifiers(classifier_dict=pairwise_dict)
WekaPairwiseClassification.initialize_temp_cyto_files()
fp=gzip.open(os.path.expandvars('$HOME/scratch/xmls_deboss_percentage_exclude__pairwise_result.pkl.gz'))
pruned_sciclass_dict=cPickle.load(fp)
fp.close()
set_num = 0
percent = 1.00
out_dict = WekaPairwiseClassification.ipython_client__deboss_percentage_exclude_analysis(set_num, percent, pairwise_dict, pruned_sciclass_dict)
import pprint
pprint.pprint(out_dict)
