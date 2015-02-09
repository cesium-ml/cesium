#!/bin/bash
###
### This regenerate  pairwise classifier, training arff, confusion html, feat_dist plot .pngs :
###
### See tranx_coding_notes.py with similar header string for further timings ,notes
###

./populate_feat_db_using_TCPTUTOR_sources.py
./generate_weka_classifiers.py --train_mode --train_xml_dir=/home/pteluser/scratch/vosource_xml_writedir --train_arff_path=/home/pteluser/scratch/dotastro_ge1srcs_period_nonper.arff --n_sources_needed_for_class_inclusion=1
# #./dotastro_sciclass_tools.py --old_arff_fpath=/home/pteluser/scratch/dotastro_ge1srcs_period_nonper.arff

##### NOTE: IPython was used, but it is OK TO NOT re-initialize Ipython cluster (This generates the classifier):

# #rm /home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/*
# #./pairwise_classification.py --debosscher_classes --arff_fpath=~/scratch/dotastro_ge1srcs_period_nonper__exclude_non_debosscher.arff --classifier_dir=~/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher --result_name=WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher --feat_dist_plots

###############################################################
##### NOTE: IPython was used, MUST re-initialize Ipython cluster
##### NOTE: can use the MULTI-COMPUTER IPYTHON :

#./analysis_deboss_tcp_source_compare.py

###### DO BACKUP, incase pairwise_classification.py crashes and needs rerun: 
#rm /home/pteluser/scratch/pairwise_trainingsets__back2/*
#cp -p -R /home/pteluser/scratch/pairwise_trainingsets/* /home/pteluser/scratch/pairwise_trainingsets__back2/

##### NOTE: IPython was used, MUST re-initialize Ipython cluster

#./generate_weka_classifiers.py --train_mode --train_xml_dir=/home/pteluser/scratch/xmls_deboss_percentage_exclude_2 --train_arff_path=/home/pteluser/scratch/xmls_deboss_percentage_exclude.arff --n_sources_needed_for_class_inclusion=1
#rm /home/pteluser/scratch/xmls_deboss_percentage_exclude__classified.pkl.gz
#mv /home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result.pkl.gz /home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result.pkl.gz__old

##### NOTE: IPython was used, MUST re-initialize Ipython cluster  (multi-node)

##### following 2 lines are good when pairwise_classification.py has crashed
#rm /home/pteluser/scratch/pairwise_trainingsets/*
#cp -p /home/pteluser/scratch/pairwise_trainingsets__back2/* /home/pteluser/scratch/pairwise_trainingsets/ 

#./pairwise_classification.py --deboss_percentage_exclude_analysis --arff_fpath=/home/pteluser/scratch/xmls_deboss_percentage_exclude.arff --classifier_dir=~/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher --result_name=xmls_deboss_percentage_exclude__pairwise_result 


#rm /home/pteluser/scratch/pairwise_trainingsets/*
#cp -p /home/pteluser/scratch/pairwise_trainingsets__back2/* /home/pteluser/scratch/pairwise_trainingsets/ 
#./pairwise_classification.py --deboss_percentage_exclude_analysis --arff_fpath=/home/pteluser/scratch/xmls_deboss_percentage_exclude.arff --classifier_dir=~/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher --result_name=xmls_deboss_percentage_exclude__pairwise_result 

#cp -p ~/scratch/xmls_deboss_percentage_exclude.ps /home/pteluser/Dropbox/Public/work/
#./analysis_deboss_tcp_source_compare.py --percent_sample__component_classifier_analysis

###########

#mkdir /media/raid_0/debosscher_classification_analysis/20100918a
#mkdir /media/raid_0/debosscher_classification_analysis/20100918a/datafiles
#mkdir /media/raid_0/debosscher_classification_analysis/20100918a/feature_pngs
#mkdir /media/raid_0/debosscher_classification_analysis/20100918a/confid_pngs
#mkdir /media/raid_0/debosscher_classification_analysis/20100918a/xmls
#mkdir /media/raid_0/debosscher_classification_analysis/20100918a/pairwise_trainingsets
#cp -p ~/scratch/pairwise_trainingsets/* /media/raid_0/debosscher_classification_analysis/20100918a/pairwise_trainingsets/
#cp -p /home/pteluser/scratch/plot_confids_vs_percent__per_classifier_final*png /media/raid_0/debosscher_classification_analysis/20100918a/confid_pngs/
#cp -p /home/pteluser/scratch/xmls_deboss_percentage_exclude__classified.pkl.gz /media/raid_0/debosscher_classification_analysis/20100918a/
#cp -p /home/pteluser/scratch/classifier_confidence_analysis.pkl.gz /media/raid_0/debosscher_classification_analysis/20100918a/
#cp -p ~/scratch/xmls_deboss_percentage_exclude.ps /media/raid_0/debosscher_classification_analysis/20100918a/
#cp -p /home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/* /media/raid_0/debosscher_classification_analysis/20100918a/datafiles/
#cp -p /home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher_classif_stats.html /media/raid_0/debosscher_classification_analysis/20100918a/confusion_matricies.html
#cp -p /home/pteluser/scratch/pairwise_scp_data/* /media/raid_0/debosscher_classification_analysis/20100918a/feature_pngs/
#pushd /media/raid_0/debosscher_classification_analysis/20100918a/xmls
#cp -p /home/pteluser/src/TCP/Algorithms/debosscher_vosourcexml_copy.sh ./
#./debosscher_vosourcexml_copy.sh
#rm debosscher_vosourcexml_copy.sh
#popd

