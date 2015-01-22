#!/bin/sh
#REFERENCE ONLY#/home/dstarr/src/TCP/Software/Noisification/generate_noisy_tutor.py --reference_xml_dir=/home/dstarr/scratch/vosource_xml_writedir --n_noisified_per_orig_vosource=50 --noisified_xml_final_dirpath=/home/dstarr/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9/generated_vosource --n_epochs_in_vosource=19 --archive_dirpath=/home/dstarr/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9 --progenitor_class_list_fpath=/home/dstarr/src/TCP/Software/Noisification/all_progenitor_class_list.txt --fit_metric_cutoff=0.05
#REFERENCE ONLY#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=19 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --train_mode                   

### with 8 nodes:
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=11 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=20 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=9 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=10 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=33 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified

#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=31 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=33 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified

#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified

###./generate_weka_classifiers.py -u src_3611089_b  --n_noisified_per_orig_vosource=20 --n_epochs=0 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_noisified --use_srcid_times=3611089



### USE: beowulf_start_ipengines.py to use all nodes for the next bit
### With 96 nodes:
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=11 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=20 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=9 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=10 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=33 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode

#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=31 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode

#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode

#sleep 10
#./generate_weka_classifiers.py -u src_3611089_b  --n_noisified_per_orig_vosource=20 --n_epochs=0 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --regenerate_features --train_mode


### Java .model creation (this could be run on tranx, I think:
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=11 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=20 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=9 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=10 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_17.9  --n_noisified_per_orig_vosource=20 --n_epochs=33 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model

#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_2.9d  --n_noisified_per_orig_vosource=20 --n_epochs=31 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model


#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=13 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=15 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=17 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=19 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --gabdefrsenerate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=21 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=23 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=25 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=27 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u j48_ptfmod  --n_noisified_per_orig_vosource=20 --n_epochs=29 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model

#./generate_weka_classifiers.py -u src_3611089_b  --n_noisified_per_orig_vosource=20 --n_epochs=0 --n_sources_needed_for_class_inclusion=40 --fit_metric_cutoff=0.05 --generate_model


##########
##### NOTE: 
#####    1st edit regenerate_vosource_xmls.py ~L236  : select period / no-period noisified data:
#####    Also edit generate_noisy_tutor.py ~L299  : choose a random.exp() time-cadence distribution function


#./generate_weka_classifiers.py -u surveynoise_linearlombfreq  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=10 --fit_metric_cutoff=0.1 --generate_noisified

#./generate_weka_classifiers.py -u surveynoise_linearlombfreq  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=10 --fit_metric_cutoff=0.1 --regenerate_features --train_mode

#./generate_weka_classifiers.py -u surveynoise_linearlombfreq  --n_noisified_per_orig_vosource=50 --n_epochs=20 --n_sources_needed_for_class_inclusion=10 --fit_metric_cutoff=0.1 --generate_model


##### NOTE: reduce ipython...py nodes == 4 before running this:

./get_classifications_for_ptf_srcid_and_class_schema.py 50nois_20epch_010need_0.100mtrc_surveynoise_linearlombfreq

#./get_classifications_for_ptf_srcid_and_class_schema.py 50nois_00epch_010need_0.100mtrc_per900ep10day
#./get_classifications_for_ptf_srcid_and_class_schema.py 70nois_00epch_010need_0.100mtrc_per900ep10day


#./get_classifications_for_ptf_srcid_and_class_schema.py 20nois_00epch_040need_0.050mtrc_src_3342980
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_nonper500ep20day
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_nonper600ep30day
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_noper300ep10day
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_per300ep10day
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_per500ep20day
#./get_classifications_for_ptf_srcid_and_class_schema.py 40nois_00epch_080need_0.050mtrc_per600ep30day
#./get_classifications_for_ptf_srcid_and_class_schema.py 50nois_00epch_100need_0.050mtrc_no_period
#./get_classifications_for_ptf_srcid_and_class_schema.py 50nois_00epch_100need_0.050mtrc_src_3342980
