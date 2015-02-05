#!/usr/bin/env python 
"""
Tool for debugging the dependence of a rpy2 RandomForest classifier on various features 
in order to determine/debug mismatched of noisy featutes.

TODO:

 - should use two different Debosscher arff, with features generated from differeing algorithms.
   - Should be able to disable certain features in arff datasets to see whether 
     crossvalidation errors change by the same ammount.

"""
from __future__ import print_function
import os, sys
import numpy
import pprint
import datetime
import time

algorithms_dirpath = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')
sys.path.append(algorithms_dirpath)
import rpy2_classifiers

class Debug_Feature_Class_Dependence:
    """
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.load_rpy2_rc()


    def load_rpy2_rc(self, algorithms_dirpath=''):
        """ This object contains hooks to R
        """
        if len(algorithms_dirpath) == 0:
            algorithms_dirpath=self.pars.get('algorithms_dirpath','')
        self.rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algorithms_dirpath)

 
    def exclude_features_in_arff(self, arff_str='', noisify_attribs=[]):
        """ Insert some missing-value features to arff rows.
        Exepect the input to be a single string representation of arff with \n's.
        Returning a similar single string.
        """
        # # # TODO: do not add the missing features to the arff header
        out_lines = []
        misattrib_name_to_id = {}
        i_attrib = 0
        lines = arff_str.split('\n')
        do_attrib_parse = True
        for line in lines:
            if do_attrib_parse:
                if line[:10] == '@ATTRIBUTE':
                    feat_name = line.split()[1]
                    if feat_name in noisify_attribs:
                        misattrib_name_to_id[feat_name] = i_attrib
                        i_attrib += 1
                        continue # skip out_lines.append(line) for this feature
                    else:
                        i_attrib += 1
                elif '@data' in line.lower():
                    do_attrib_parse = False
                out_lines.append(line)
                continue
            ### Should only get here after hitting @data line, which means just feature lines
            #if random.random() > prob_source_has_missing:
            #    out_lines.append(line)
            #    continue # don't set any attributes as missing for this source
            attribs = line.split(',')
            new_attribs = []
            for i, attrib_val in enumerate(attribs):
                if i in misattrib_name_to_id.values():
                    # Then do not add this feature
                    #import pdb; pdb.set_trace()
                    #print
                    continue
                    #if random.random() <= prob_misattrib_is_missing:
                    #    new_attribs.append('?')
                    #    continue
                new_attribs.append(attrib_val)
            new_line = ','.join(new_attribs)
            out_lines.append(new_line)
        new_train_arff_str = '\n'.join(out_lines)
        return new_train_arff_str


    def get_crossvalid_errors_for_single_arff(self, arff_fpath='',
                                              noisify_attribs=[],
                                              ntrees=None,
                                              mtry=None,
                                              nodesize=None,
                                              n_iters=None,
                                              classifier_base_dirpath='',
                                              algorithms_dirpath=''):
        """ Given an arff file, features to exclude, params
         - use the arff for training and testing, by doing some fractional partioning

        """
        train_arff_str = open(arff_fpath).read()
        train_arff_str = self.exclude_features_in_arff(arff_str=train_arff_str,
                                                              noisify_attribs=noisify_attribs)

        traindata_dict = self.rc.parse_full_arff(arff_str=train_arff_str, fill_arff_rows=True)
        arff_header = self.rc.parse_arff_header(arff_str=train_arff_str)#, ignore_attribs=['source_id'])

        Gen_Fold_Classif = rpy2_classifiers.GenerateFoldedClassifiers()

        all_fold_data = Gen_Fold_Classif.generate_fold_subset_data(full_data_dict=traindata_dict,
                                                                   n_folds=10,
                                                                   do_stratified=False,
                                                                   classify_percent=40.)

        meta_parf_avgs = []
        meta_R_randomForest_avgs = []
        meta_R_cforest_avgs = []
        out_dict = {'means':[],
                    'stds':[]}
        for k in range(n_iters):
            error_rate_list = []
            results_dict = {}
            for i_fold, fold_dict in all_fold_data.iteritems():
                results_dict[i_fold] = {}

            ### Do the R randomForest here:
            do_ignore_NA_features = False
            for i_fold, fold_data in all_fold_data.iteritems():
                classifier_fpath = os.path.expandvars("%s/classifier_RF_%d.rdata" % (classifier_base_dirpath, i_fold))
                Gen_Fold_Classif.generate_R_randomforest_classifier_rdata(train_data=fold_data['train_data'],
                                                                 classifier_fpath=classifier_fpath,
                                                                 do_ignore_NA_features=do_ignore_NA_features,
                                                                 algorithms_dirpath=algorithms_dirpath,
                                                                 ntrees=ntrees, mtry=mtry,
                                                                 nfolds=10, nodesize=nodesize)

                r_name='rf_clfr'
                classifier_dict = {'class_name':r_name}
                self.rc.load_classifier(r_name=r_name,
                               fpath=classifier_fpath)
                classif_results = self.rc.apply_randomforest(classifier_dict=classifier_dict,
                                                data_dict=fold_data['classif_data'],
                                                do_ignore_NA_features=do_ignore_NA_features)

                print("classif_results['error_rate']=", classif_results['error_rate'])

                results_dict[i_fold]['randomForest'] = {'class_error':classif_results['error_rate']}

                error_rate_list.append(classif_results['error_rate'])
            out_dict['means'].append(numpy.mean(error_rate_list))
            out_dict['stds'].append(numpy.std(error_rate_list))
        return out_dict


    def initialize_mec(self, client=None):
        """ partially adapted from citris33/arff_generateion_master.py
        """
        mec = client.MultiEngineClient()
        mec.reset(targets=mec.get_ids()) # Reset the namespaces of all engines
        tc = client.TaskClient()

        mec_exec_str = """
import sys, os
import numpy
import random
sys.path.append(os.path.abspath('/global/home/users/dstarr/src/TCP/Software/ingest_tools'))
import debug_feature_classifier_dependence
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))
import rpy2_classifiers
DebugFeatureClassDependence = debug_feature_classifier_dependence.Debug_Feature_Class_Dependence()
"""

        print('before mec()')
        #print mec_exec_str
        #import pdb; pdb.set_trace()
        engine_ids = mec.get_ids()
        pending_result_dict = {}
        for engine_id in engine_ids:
            pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
        n_pending = len(pending_result_dict)
        i_count = 0
        while n_pending > 0:
            still_pending_dict = {}
            for engine_id, pending_result in pending_result_dict.iteritems():
                try:
                    result_val = pending_result.get_result(block=False)
                except:
                    print("get_result() Except. Still pending on engine: %d" % (engine_id))
                    still_pending_dict[engine_id] = pending_result
                    result_val = None # 20110105 added
                if result_val is None:
                    print("Still pending on engine: %d" % (engine_id))
                    still_pending_dict[engine_id] = pending_result
            if i_count > 10:
                mec.clear_pending_results()
                pending_result_dict = {}
                mec.reset(targets=still_pending_dict.keys())
                for engine_id in still_pending_dict.keys():
                    pending_result_dict[engine_id] = mec.execute(mec_exec_str, targets=[engine_id], block=False)
                ###
                time.sleep(20) # hack
                pending_result_dict = [] # hack
                ###
                i_count = 0
            else:
                print("sleeping...")
                time.sleep(5)
                pending_result_dict = still_pending_dict
            n_pending = len(pending_result_dict)
            i_count += 1

        print('after mec()')
        time.sleep(5) # This may be needed, although mec() seems to wait for all the Ipython clients to finish
        print('after sleep()')
        #import pdb; pdb.set_trace()
        return tc


    def wait_for_task_completion(self, task_id_list=[], tc=None):
        """ partially adapted from citris33/arff_generateion_master.py
        """
        new_orig_feat_tups = []
        
        while ((tc.queue_status()['scheduled'] > 0) or
               (tc.queue_status()['pending'] > 0)):
            tasks_to_pop = []
            for task_id in task_id_list:
                temp = tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('new_orig_feat_tups',None)
                if results is None:
                    continue # skip some kind of NULL result
                if len(results) > 0:
                    tasks_to_pop.append(task_id)
                    new_orig_feat_tups.append(results)
            for task_id in tasks_to_pop:
                task_id_list.remove(task_id)
            print(tc.queue_status())
            print('Sleep... 20 in wait_for_task_completion()', datetime.datetime.utcnow())
            time.sleep(20)
        # IN CASE THERE are still tasks which have not been pulled/retrieved:
        for task_id in task_id_list:
            temp = tc.get_task_result(task_id, block=False)
            if temp is None:
                continue
            temp2 = temp.results
            if temp2 is None:
                continue
            results = temp2.get('new_orig_feat_tups',None)
            if results is None:
                continue #skip some kind of NULL result
            if len(results) > 0:
                tasks_to_pop.append(task_id)
                new_orig_feat_tups.append(results)
        return new_orig_feat_tups


    def main_ipython_cluster(self, noisify_attribs=[],
             ntrees = 100,
             mtry=25,
             nodesize=5,
             n_iters=23):
        """ Main() for Debug_Feature_Class_Dependence

        Partially adapted from compare_randforest_classifers.py

do training and crossvalidation on just Debosscher data for spped.
   - parse debosscher arff
   - remove certain features
   - train/test classifier using cross validation
   - store error rates for those removed features
        """
        try:
            from IPython.kernel import client
        except:
            pass

        tc = self.initialize_mec(client=client)

        result_dict = {}
        new_orig_feat_tups = []

        task_id_list = []
        for feat_name in noisify_attribs:
            tc_exec_str = """
new_orig_feat_tups = ''
task_randint = random.randint(0,1000000000000)
classifier_base_dirpath = os.path.expandvars("$HOME/scratch/debug_feature_classifier_dependence/%d" % (task_randint))
os.system("mkdir -p %s" % (classifier_base_dirpath))
try:
    DebugFeatureClassDependence = debug_feature_classifier_dependence.Debug_Feature_Class_Dependence(pars={'algorithms_dirpath':os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')})
    out_dict = DebugFeatureClassDependence.get_crossvalid_errors_for_single_arff(arff_fpath=pars['orig_arff_dirpath'],
                                                      noisify_attribs=[feat_name],
                                                      ntrees=ntrees,
                                                      mtry=mtry,
                                                      nodesize=nodesize,
                                                      n_iters=n_iters,
                                                      classifier_base_dirpath=classifier_base_dirpath,
                                                      algorithms_dirpath=os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))

    orig_wa = numpy.average(out_dict['means'], weights=out_dict['stds'])
    DebugFeatureClassDependence.load_rpy2_rc(algorithms_dirpath=os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))
    out_dict = DebugFeatureClassDependence.get_crossvalid_errors_for_single_arff(arff_fpath=pars['new_arff_dirpath'],
                                                          noisify_attribs=[feat_name],
                                                          ntrees=ntrees,
                                                          mtry=mtry,
                                                          nodesize=nodesize,
                                                          n_iters=n_iters,
                                                          classifier_base_dirpath=classifier_base_dirpath,
                                                          algorithms_dirpath=os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/'))
    new_wa = numpy.average(out_dict['means'], weights=out_dict['stds'])
    new_orig_feat_tups = (new_wa - orig_wa, feat_name, numpy.std(out_dict['means']))


except:
    new_orig_feat_tups = str(sys.exc_info())
            """


            taskid = tc.run(client.StringTask(tc_exec_str,
                                              push={'pars':pars,
                                                    'feat_name':feat_name,
                                                    'ntrees':ntrees,
                                                    'mtry':mtry,
                                                    'nodesize':nodesize,
                                                    'n_iters':n_iters},
                                              pull='new_orig_feat_tups', #'new_orig_feat_tups', 
                                              retries=3))
            task_id_list.append(taskid)
            if 0:
                ### debug: This inspect.getmembers() only works if task doesnt fail:
                time.sleep(60)
                temp = tc.get_task_result(taskid, block=False)
                import inspect
                for a,b in inspect.getmembers(temp):
                    print(a, b)
                out_dict =  temp.results.get('new_orig_feat_tups',None)
                import pdb; pdb.set_trace()
                print()
            ######


        new_orig_feat_tups = self.wait_for_task_completion(task_id_list=task_id_list,
                                                           tc=tc)

        new_orig_feat_tups.sort()
        pprint.pprint(new_orig_feat_tups)
        import pdb; pdb.set_trace()
        print()


    def main(self, noisify_attribs=[],
             ntrees = 100,
             mtry=25,
             nodesize=5,
             n_iters=23):
        """ Main() for Debug_Feature_Class_Dependence

        Partially adapted from compare_randforest_classifers.py

do training and crossvalidation on just Debosscher data for spped.
   - parse debosscher arff
   - remove certain features
   - train/test classifier using cross validation
   - store error rates for those removed features


        """
        result_dict = {}
        new_orig_feat_tups = []

        for feat_name in noisify_attribs:
            result_dict[feat_name] = {}
            print('orig:', feat_name)
            out_dict = self.get_crossvalid_errors_for_single_arff(arff_fpath=self.pars['orig_arff_dirpath'],
                                                                  noisify_attribs=[feat_name],
                                                                  ntrees=ntrees,
                                                                  mtry=mtry,
                                                                  nodesize=nodesize,
                                                                  n_iters=n_iters,
                                                                  algorithms_dirpath=self.pars['algorithms_dirpath'])
            pprint.pprint(out_dict)
            orig_wa = numpy.average(out_dict['means'], weights=out_dict['stds'])
            print('weighted average:', orig_wa)
            result_dict[feat_name]['orig'] = (orig_wa,
                                              numpy.std(out_dict['means']))

            self.load_rpy2_rc()
            print('new:', feat_name)
            out_dict = self.get_crossvalid_errors_for_single_arff(arff_fpath=self.pars['new_arff_dirpath'],
                                                                  noisify_attribs=[feat_name],
                                                                  ntrees=ntrees,
                                                                  mtry=mtry,
                                                                  nodesize=nodesize,
                                                                  n_iters=n_iters,
                                                                  algorithms_dirpath=self.pars['algorithms_dirpath'])
            pprint.pprint(out_dict)
            new_wa = numpy.average(out_dict['means'], weights=out_dict['stds'])
            print('weighted average:', new_wa)
            result_dict[feat_name]['new'] = (new_wa,
                                             numpy.std(out_dict['means']))
            result_dict[feat_name]['0_new-orig'] = new_wa - orig_wa
            new_orig_feat_tups.append((new_wa - orig_wa, feat_name, numpy.std(out_dict['means'])))

        pprint.pprint(result_dict)
        new_orig_feat_tups.sort()
        pprint.pprint(new_orig_feat_tups)
        import pdb; pdb.set_trace()
        print()


if __name__ == '__main__':
    
    #pars = {'algorithms_dirpath':algorithms_dirpath,
    #        'orig_arff_dirpath':'/media/raid_0/historical_archive_featurexmls_arffs/tutor_123/2011-04-30_00:32:56.250499/source_feats.arff',
    #        'new_arff_dirpath':'/media/raid_0/historical_archive_featurexmls_arffs/tutor_123/2011-05-13_04:22:08.073940/source_feats.arff',
    #        }
    pars = {'algorithms_dirpath':algorithms_dirpath,
            'orig_arff_dirpath':'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-06-13_17:51:12.002706/source_feats__ACVSclasses.arff',
            'new_arff_dirpath':'/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-06-13_17:51:12.002706/source_feats__ACVSclasses.arff',
            'ntrees':100,
            'mtry':25,
            'nodesize':5,
            'n_iters':11,
            }


    """
    noisify_attribs = ['freq1_harmonics_amplitude_0',
                       'freq2_harmonics_amplitude_0',
                       'freq3_harmonics_amplitude_0',
                       'freq2_harmonics_freq_0',
                       'freq3_harmonics_freq_0',
                       'freq_signif_ratio_21',
                       'fold2P_slope_90percentile',
                       'medperc90_2p_p',
                       'p2p_scatter_pfold_over_mad',
                       'p2p_ssqr_diff_over_var',
                       'qso_log_chi2_qsonu',
                       'qso_log_chi2nuNULL_chi2nu',
                       'std',
                       'amplitude',
                       'stetson_j',
                       'percent_difference_flux_percentile']
    """

    noisify_attribs = [ \
'amplitude',
'beyond1std'
'flux_percentile_ratio_mid20',
'flux_percentile_ratio_mid35',
'flux_percentile_ratio_mid50',
'flux_percentile_ratio_mid65',
'flux_percentile_ratio_mid80',
'fold2P_slope_10percentile',
'fold2P_slope_90percentile',
'freq1_harmonics_amplitude_0',
'freq1_harmonics_amplitude_1',
'freq1_harmonics_amplitude_2',
'freq1_harmonics_amplitude_3',
'freq1_harmonics_freq_0',
'freq1_harmonics_rel_phase_0',
'freq1_harmonics_rel_phase_1',
'freq1_harmonics_rel_phase_2',
'freq1_harmonics_rel_phase_3',
'freq2_harmonics_amplitude_0',
'freq2_harmonics_amplitude_1',
'freq2_harmonics_amplitude_2',
'freq2_harmonics_amplitude_3',
'freq2_harmonics_freq_0',
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
'freq_amplitude_ratio_21',
'freq_amplitude_ratio_31',
'freq_frequency_ratio_21',
'freq_frequency_ratio_31',
'freq_signif',
'freq_signif_ratio_21',
'freq_signif_ratio_31',
'freq_varrat',
'freq_y_offset',
'linear_trend',
'max_slope',
'median_absolute_deviation',
'median_buffer_range_percentage',
'medperc90_2p_p',
'p2p_scatter_2praw',
'p2p_scatter_over_mad',
'p2p_scatter_pfold_over_mad',
'p2p_ssqr_diff_over_var',
'percent_amplitude',
'percent_difference_flux_percentile',
'qso_log_chi2_qsonu',
'qso_log_chi2nuNULL_chi2nu',
'scatter_res_raw',
'skew',
'small_kurtosis',
'std',
'stetson_j',
'stetson_k']

    if 0:
        # This is to generate the error_rate differences dict:
        DebugFeatureClassDependence = Debug_Feature_Class_Dependence(pars=pars)
        DebugFeatureClassDependence.main_ipython_cluster(noisify_attribs=noisify_attribs,
                                         ntrees = pars['ntrees'],
                                         mtry=pars['mtry'],
                                         nodesize=pars['nodesize'],
                                         n_iters=pars['n_iters'])
        #DebugFeatureClassDependence.main(noisify_attribs=noisify_attribs,
        #                                 ntrees = self.pars['ntrees'],
        #                                 mtry=self.pars['mtry'],
        #                                 nodesize=self.pars['nodesize'],
        #                                 n_iters=self.pars['n_iters'])

    if 1:
        # This is to generate a plot of error_rate differences vs freq

        asas_recent_diff_fpath = "/home/pteluser/scratch/debug_feature_classifier_dependence_dicts/asas_niters11_2011-06-13_17:51:12.002706_2011-06-13_17:51:12.002706.dict"
        exec(open(asas_recent_diff_fpath).read())
        asas_recent_diff = data

        asas_newold_diff_fpath = "/home/pteluser/scratch/debug_feature_classifier_dependence_dicts/asas_niters11_2011-04-30_02:53:31.959591_2011-06-13_17:51:12.002706.dict"
        exec(open(asas_newold_diff_fpath).read())
        asas_newold_diff = data

        deboss_recent_diff_fpath = "/home/pteluser/scratch/debug_feature_classifier_dependence_dicts/deboss_niters23_2011-06-08_17:40:25.373520_2011-06-13_18:40:44.673995.dict"
        exec(open(deboss_recent_diff_fpath).read())
        deboss_recent_diff = data


        deboss_newold_diff_fpath = "/home/pteluser/scratch/debug_feature_classifier_dependence_dicts/deboss_niters23_2011-04-30_00:32:56.250499_2011-05-13_04:22:08.073940.dict"
        exec(open(deboss_newold_diff_fpath).read())
        deboss_newold_diff = data

        deboss_newold_diff['error_diffs'] = []
        for ediff, featname in deboss_newold_diff['error_diffs_2tup']:
            deboss_newold_diff['error_diffs'].append((ediff, featname, deboss_newold_diff['old_dict'][featname]['new'][1]))

        ###(new_wa - orig_wa, feat_name, numpy.std(out_dict['means']))
        ###new:0.22895141275051539 - orig:0.23029385649882161 ==  -0.001342  :: improvement in new classifier




        #data_dict = deboss_newold_diff
        #data_dict3 = deboss_recent_diff
        #data_name = "deboss"

        data_dict = asas_newold_diff
        data_dict3 = asas_recent_diff
        data_name = "ASAS"

        data_list = data_dict['error_diffs']
        data_list3 = data_dict3['error_diffs']

        data3_dict = {}
        for (errordiff, featname, stdev) in data_list3:
            data3_dict[featname] = (errordiff, stdev)

        errordiff_list = []
        featname_list = []
        stddev_list = []
        sort_list = []
        for i, (errordiff, featname, stdev) in enumerate(data_list):
            errordiff_list.append(errordiff)
            featname_list.append(featname)
            stddev_list.append(stdev)
            sort_list.append((errordiff_list, i))
        sort_list.sort()

        errordiff_list2 = []
        featname_list2 = []
        stddev_list2 = []

        errordiff_list3 = []
        stddev_list3 = []

        x_inds3 = []
        for j, (errordiff, i) in enumerate(sort_list):
            errordiff_list2.append(errordiff_list[i])
            featname_list2.append(featname_list[i])
            stddev_list2.append(stddev_list[i])

            if featname_list[i] in data3_dict:
                errordiff_list3.append(data3_dict[featname_list[i]][0])
                stddev_list3.append(data3_dict[featname_list[i]][1])
                x_inds3.append(j)
            #else:
            #    errordiff_list3.append(None)
            #    stddev_list3.append(None)

        import matplotlib.pyplot as plt
        fig = plt.figure() #figsize=(5,3), dpi=100)
        ax = fig.add_subplot(211)

        x_inds = range(len(errordiff_list2))

        #ax.plot(range(len(errordiff_list2)), errordiff_list2)
        plt_errordiff =  ax.errorbar(x_inds, errordiff_list2, yerr=stddev_list, fmt='bo')
        plt_errordiff3 =  ax.errorbar(x_inds3, errordiff_list3, yerr=stddev_list3, fmt='ro')
        plt.grid(True)

        newold_new_date = data_dict['new_arff_dirpath'].split('/')[-2].split('_')[0]
        newold_old_date = data_dict['orig_arff_dirpath'].split('/')[-2].split('_')[0]

        newnew_new_date = data_dict3['new_arff_dirpath'].split('/')[-2].split('_')[0]
        newnew_old_date = data_dict3['orig_arff_dirpath'].split('/')[-2].split('_')[0]

        ax.legend((plt_errordiff[0], plt_errordiff3[0]),
                   ("%s - %s" % (newold_new_date, newold_old_date),
                    "%s - %s" % (newnew_new_date, newnew_old_date)), loc='lower right', numpoints=1)
        ax.set_xticks(x_inds)

        xtickNames = plt.setp(ax, xticklabels=featname_list2)
        plt.setp(xtickNames, rotation=90, fontsize=8)
        ax.set_ylabel("New ARFF Error - Older ARFF Error")

        ax.annotate("Newer ARFF has lower error", xy=(0.2, 0.1), xycoords='axes fraction',
                    horizontalalignment='center',
                    verticalalignment='top',
                    fontsize=10)

        ax.annotate("Newer ARFF has higher error", xy=(0.2, 0.9), xycoords='axes fraction',
                    horizontalalignment='center',
                    verticalalignment='top',
                    fontsize=10)

        title_str = "%s ARFFs" % (data_name)
        plt.title(title_str)

        fpath = "/home/pteluser/scratch/debug_feature_classifier_dependence_dicts/%s_%s_%s.ps" % ( \
                                        data_name,
                                        "%s-%s" % (newold_new_date, newold_old_date),
                                        "%s-%s" % (newnew_new_date, newnew_old_date))
        plt.savefig(fpath)
        #plt.show()

        os.system("gv %s &" % (fpath))

        import pdb; pdb.set_trace()
        print()
        
