#!/bin/sh
#REFERENCE ONLY#/home/dstarr/src/TCP/Software/Noisification/generate_noisy_tutor.py --reference_xml_dir=/home/dstarr/scratch/vosource_xml_writedir --n_noisified_per_orig_vosource=50 --noisified_xml_final_dirpath=/home/dstarr/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9/generated_vosource --n_epochs_in_vosource=19 --archive_dirpath=/home/dstarr/scratch/Noisification/50nois_19epch_100need_0.050mtrc_qk17.9 --progenitor_class_list_fpath=/home/dstarr/src/TCP/Software/Noisification/all_progenitor_class_list.txt --fit_metric_cutoff=0.05
#REFERENCE ONLY#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=19 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --train_mode                   
### with 8 nodes:
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=19 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
### With 96 nodes:
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=19 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
### BACKGROUND:
### TODO: also see if previous JAVA is done so that another "--generate_model" case can be run in the background
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=19 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model


### with 8 nodes:
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=21 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=25 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=13 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=11 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=27 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=30 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=35 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=40 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_noisified

### TODO: use beowulf_start_ipengines.py to use all nodes for the next bit


### With 96 nodes:
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=21 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=25 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=13 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=11 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=27 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=30 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=35 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=40 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --regenerate_features --train_mode

### Java .model creation (this could be run on tranx, I think:
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=21 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=25 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
#./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=13 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=11 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=27 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=30 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=35 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
./generate_weka_classifiers.py -u qk17.9  --n_noisified_per_orig_vosource=50 --n_epochs=40 --n_sources_needed_for_class_inclusion=100 --fit_metric_cutoff=0.05 --generate_model
