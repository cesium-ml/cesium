#!/usr/bin/env python 
"""
* Get fortran code running for comparisons with R's party:cforest
** install cforest
** have script which runs forest and cforest on some dataset
** also run parf rf classifier on dataset
*** betsy: ~/scratch/rf_parf/parf
** compare results  (will need to do crossvalidation)
** First try out on non-missing-value dataset
** Need some missing-feature datasets to try out

"""
from __future__ import print_function
from __future__ import absolute_import
import os, sys
import numpy

def example_initial_r_randomforest():
    """ Initial example which trains and classifies a R randomForest classifier
    Using 1 40/60 fold of debosscher data.
    """

    algorithms_dirpath = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')
    sys.path.append(algorithms_dirpath)
    from . import rpy2_classifiers
    rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algorithms_dirpath)

    train_arff_str = open(os.path.expandvars("$HOME/scratch/full_deboss_1542srcs_20110106.arff")).read()
    traindata_dict = rc.parse_full_arff(arff_str=train_arff_str)

    Gen_Fold_Classif = rpy2_classifiers.GenerateFoldedClassifiers()
    all_fold_data = Gen_Fold_Classif.generate_fold_subset_data(full_data_dict=traindata_dict,
                                                               n_folds=10,
                                                               do_stratified=False,
                                                               classify_percent=40.)
    i_fold = 0  # of 10 folds
    fold_data = all_fold_data[i_fold]
    do_ignore_NA_features = False
    classifier_fpath = os.path.expandvars("$HOME/scratch/classifier_RF_0.rdata")# % (i_fold))
    Gen_Fold_Classif.generate_R_randomforest_classifier_rdata(train_data=fold_data['train_data'],
                                                     classifier_fpath=classifier_fpath,
                                                     do_ignore_NA_features=do_ignore_NA_features,
                                                     algorithms_dirpath=algorithms_dirpath)

    r_name='rf_clfr'
    classifier_dict = {'class_name':r_name}
    rc.load_classifier(r_name=r_name,
                   fpath=classifier_fpath)
    classif_results = rc.apply_randomforest(classifier_dict=classifier_dict,
                                    data_dict=fold_data['classif_data'],
                                    do_ignore_NA_features=do_ignore_NA_features)

    print("classif_results['error_rate']=", classif_results['error_rate'])
    import pdb; pdb.set_trace()
    print()


    
def count_classes(class_list=[]):
    """
    """
    count_dict = {}
    for class_name in class_list:
        if class_name not in count_dict:
            count_dict[class_name] = 0
        count_dict[class_name] += 1
    return count_dict


def generate_parf_header_with_weighted_classes(count_dict={},
                                               n_sources=0, arff_header=[]):
    """ Given some class information and an existing arff header list,
    generate a parf style @attribute class entry which has inverse proportional class weights.
    """
    new_arff_header = []
    for line in arff_header:
        #if '@attribute source_id' in line.lower():
        #    new_arff_header.append('@ignored source_id NUMERIC')
        #    continue
        if not "@attribute class" in line.lower():
            new_arff_header.append(line)
            continue
        sub_line = line[line.find('{')+1:line.rfind('}')]
        class_list = sub_line.split("','")
        new_line = line[:line.find('{')+1]
        total_weight = 0 # for sanity check only
        for quoted_class_name in class_list:
            class_name = quoted_class_name.strip("'")
            class_weight = count_dict[class_name] / float(n_sources)

            ###Using NO WEIGHT:#
            new_line += "'%s', " % (class_name)
            ### USING WEIGHTS (which, as calculated seem to worsen the final classification error)
            ###   - it seems internal weights are used by PARF since nowt error rate agrees with R:randomForest
            #new_line += "'%s' (%f), " % (class_name, class_weight)

            total_weight += class_weight
        new_line = new_line[:-2] + line[line.rfind('}'):]
        print('total_weight=', total_weight)
        #print 'line:    ', line
        #print 'new_line:', new_line
        new_arff_header.append(new_line)

    return new_arff_header


if __name__ == '__main__':

    #example_initial_r_randomforest()

    # I want to do the following over the same folded datasets
    # I also want to use the same parms
    #####parf --verbose -t ~/scratch/full_deboss_1542srcs_20110106.arff -a ~/scratch/full_deboss_1542srcs_20110106.arff -n 1000 -m 25

    # NOTE: this is compiled differently (with different FFLAGS, CFLAGS) than for library/python wrapping version:
    parf_exec_fpath = '/home/pteluser/scratch/rf_parf__back_copy2/parf/parf'

    noisify_attribs = [ \
            'freq1_harmonics_amplitude_0',
            'freq1_harmonics_amplitude_1',
            'freq1_harmonics_amplitude_2',
            'freq1_harmonics_amplitude_3',
            'freq1_harmonics_rel_phase_0',
            'freq1_harmonics_rel_phase_1',
            'freq1_harmonics_rel_phase_2',
            'freq1_harmonics_rel_phase_3',
            'freq2_harmonics_amplitude_0',
            'freq2_harmonics_amplitude_1',
            'freq2_harmonics_amplitude_2',
            'freq2_harmonics_amplitude_3',
            'freq2_harmonics_rel_phase_0',
            'freq2_harmonics_rel_phase_1',
            'freq2_harmonics_rel_phase_2',
            'freq2_harmonics_rel_phase_3',
            'freq3_harmonics_amplitude_0',
            'freq3_harmonics_amplitude_1',
            'freq3_harmonics_amplitude_2',
            'freq3_harmonics_amplitude_3',
            'freq3_harmonics_freq_0',
            'freq3_harmonics_rel_phase_0',
            'freq3_harmonics_rel_phase_1',
            'freq3_harmonics_rel_phase_2',
            'freq3_harmonics_rel_phase_3',
            'freq_amplitude_ratio_31',
            'freq_frequency_ratio_31',
            'freq_signif_ratio_31',
            'skew',
            'qso_log_chi2_qsonu',
            'qso_log_chi2nuNULL_chi2nu',
            'median_absolute_deviation',
            'std',
            'stetson_j',
            'percent_difference_flux_percentile']


    ntrees = 100
    mtry=25
    nodesize=5
    use_missing_values = True
    prob_source_has_missing=0.3
    prob_misattrib_is_missing=0.5


    algorithms_dirpath = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')
    sys.path.append(algorithms_dirpath)
    from . import rpy2_classifiers
    rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algorithms_dirpath)

    train_arff_str = open(os.path.expandvars("$HOME/scratch/full_deboss_1542srcs_20110106.arff")).read()


    if use_missing_values:
        train_arff_str = rc.insert_missing_value_features(arff_str=train_arff_str,
                                                          noisify_attribs=noisify_attribs,
                                                          prob_source_has_missing=prob_source_has_missing,
                                                          prob_misattrib_is_missing=prob_misattrib_is_missing)

    traindata_dict = rc.parse_full_arff(arff_str=train_arff_str, fill_arff_rows=True)
    arff_header = rc.parse_arff_header(arff_str=train_arff_str)#, ignore_attribs=['source_id'])

    Gen_Fold_Classif = rpy2_classifiers.GenerateFoldedClassifiers()

    all_fold_data = Gen_Fold_Classif.generate_fold_subset_data(full_data_dict=traindata_dict,
                                                               n_folds=10,
                                                               do_stratified=False,
                                                               classify_percent=40.)

    temp_arff_fpath_root = os.path.expandvars("/tmp/parf")

    meta_parf_avgs = []
    meta_R_randomForest_avgs = []
    meta_R_cforest_avgs = []
    for k in range(50):
        parf_fpath_dict = {}
        results_dict = {}
        for i_fold, fold_dict in all_fold_data.items():
            parf_fpath_dict[i_fold] = {}
            results_dict[i_fold] = {}
            for data_case in fold_dict.keys():
                if data_case == 'train_data':
                    count_dict = count_classes(class_list=fold_dict['train_data']['class_list'])
                    n_sources = len(fold_dict['train_data']['class_list'])
                    new_arff_header = generate_parf_header_with_weighted_classes(count_dict=count_dict, n_sources=n_sources, arff_header=arff_header)
                else:
                    new_arff_header = arff_header
                fold_arff_lines = []
                fold_arff_lines.extend(new_arff_header)
                fold_arff_lines.extend(fold_dict[data_case]['arff_rows'])
                fold_arff_fpath = "%s_%s_%d" % (temp_arff_fpath_root, data_case, i_fold)
                if os.path.exists(fold_arff_fpath):
                    os.system('rm ' + fold_arff_fpath)
                fp = open(fold_arff_fpath, 'w')
                for line in fold_arff_lines:
                    fp.write(line + '\n')
                fp.close()
                parf_fpath_dict[i_fold][data_case] = fold_arff_fpath

            ### Do parf classification
            exec_parf_str = '%s -t %s -a %s -n %d -m %d -xs %d -ri source_id -uu source_id' % ( \
                                                parf_exec_fpath,
                                                parf_fpath_dict[i_fold]['train_data'],
                                                parf_fpath_dict[i_fold]['classif_data'],
                                                ntrees, mtry, nodesize)
            print(exec_parf_str)
            (a,b,c) = os.popen3(exec_parf_str)
            a.close()
            c.close()
            lines_str = b.read()
            b.close()
            lines = lines_str.split('\n')
            for line in lines:
                if not 'Testset classification error' in line:
                    continue
                vals = line.split()
                    
            class_error = float(vals[4].strip('%'))
            kappa = float(vals[8])
            results_dict[i_fold]['parf'] = {'class_error':class_error,
                                            'kappa':kappa}

        if not use_missing_values:
            ### Do the R randomForest here:
            do_ignore_NA_features = False
            for i_fold, fold_data in all_fold_data.items():
                classifier_fpath = os.path.expandvars("$HOME/scratch/classifier_RF_%d.rdata" % (i_fold))
                Gen_Fold_Classif.generate_R_randomforest_classifier_rdata(train_data=fold_data['train_data'],
                                                                 classifier_fpath=classifier_fpath,
                                                                 do_ignore_NA_features=do_ignore_NA_features,
                                                                 algorithms_dirpath=algorithms_dirpath,
                                                                 ntrees=ntrees, mtry=mtry,
                                                                 nfolds=10, nodesize=nodesize)

                r_name='rf_clfr'
                classifier_dict = {'class_name':r_name}
                rc.load_classifier(r_name=r_name,
                               fpath=classifier_fpath)
                classif_results = rc.apply_randomforest(classifier_dict=classifier_dict,
                                                data_dict=fold_data['classif_data'],
                                                do_ignore_NA_features=do_ignore_NA_features)

                print("classif_results['error_rate']=", classif_results['error_rate'])

                results_dict[i_fold]['randomForest'] = {'class_error':classif_results['error_rate']}


        # # # # # #
        # # # # # #
        # # # # # #
        ### Do the R cforest here:
        do_ignore_NA_features = False
        for i_fold, fold_data in all_fold_data.items():
            classifier_fpath = os.path.expandvars("$HOME/scratch/classifier_RF_%d.rdata" % (i_fold))
            print('generating cforest...')
            Gen_Fold_Classif.generate_R_randomforest_classifier_rdata(train_data=fold_data['train_data'],
                                                             classifier_fpath=classifier_fpath,
                                                             do_ignore_NA_features=do_ignore_NA_features,
                                                             algorithms_dirpath=algorithms_dirpath,
                                                             ntrees=ntrees, mtry=mtry,
                                                             nfolds=10, nodesize=nodesize,
                                                             classifier_type='cforest')

            r_name='rf_clfr'
            classifier_dict = {'class_name':r_name}
            rc.load_classifier(r_name=r_name,
                           fpath=classifier_fpath)
            
            print('applying cforest...')
            classif_results_cforest = rc.apply_cforest(classifier_dict=classifier_dict,
                                            data_dict=fold_data['classif_data'],
                                            do_ignore_NA_features=do_ignore_NA_features)

            print("classif_results['error_rate']=", classif_results_cforest['error_rate'])

            results_dict[i_fold]['cforest'] = {'class_error':classif_results_cforest['error_rate']}

            


        ##### Analyze the results (compare the classifiers):
        parf_errors = []
        randomForest_errors = []
        cforest_errors = []
        for i_fold in all_fold_data.keys():
            parf_errors.append(results_dict[i_fold]['parf']['class_error'] / 100.)
            randomForest_errors.append(results_dict[i_fold].get('randomForest',{}).get('class_error',-1))
            cforest_errors.append(results_dict[i_fold]['cforest']['class_error'])

        #meta_parf_avgs.append(numpy.mean(parf_errors))
        #meta_R_randomForest_avgs.append(numpy.mean(randomForest_errors))
        #meta_R_cforest_avgs.append(numpy.mean(cforest_errors))
        meta_parf_avgs.extend(parf_errors)
        meta_R_randomForest_avgs.extend(randomForest_errors)
        meta_R_cforest_avgs.extend(cforest_errors)
            
        print("PARF         mean=%lf,  std=%lf" % (numpy.mean(parf_errors), numpy.std(parf_errors)))
        print("randomForest mean=%lf,  std=%lf" % (numpy.mean(randomForest_errors), numpy.std(randomForest_errors)))
        print("cforest mean=%lf,  std=%lf" % (numpy.mean(cforest_errors), numpy.std(cforest_errors)))


        #### Put this within the inner loop so can see how this is improving:
        print('META PARF        :', numpy.mean(meta_parf_avgs), numpy.std(meta_parf_avgs), k*10 + i_fold)
        print('META randomForest:', numpy.mean(meta_R_randomForest_avgs), numpy.std(meta_R_randomForest_avgs), k*10 + i_fold)
        print('META cforest     :', numpy.mean(meta_R_cforest_avgs), numpy.std(meta_R_cforest_avgs), k*10 + i_fold)
        
    print('Final META PARF        :', numpy.mean(meta_parf_avgs), numpy.std(meta_parf_avgs))
    print('Final META randomForest:', numpy.mean(meta_R_randomForest_avgs), numpy.std(meta_R_randomForest_avgs))
    print('Final META cforest     :', numpy.mean(meta_R_cforest_avgs), numpy.std(meta_R_cforest_avgs))

    import pdb; pdb.set_trace()
    print()

