#!/usr/bin/env python 
""" This generates TCP science class pairwise classifiers which are based on
    the tinyboost Eads modified Adaboost (with confidences) classifier.

    - This determines Dotastro.org sources for wach science class.
    - This generates seperate adaboost pair classifiers.
    - This code may also test applying these adaboost classifiers for some source
        - although ideally this will be done with parallel code, such as Hadoop based.

 TODO:
#  - parse dotastro.org and group into different science class groups
#     - <science class>:{<arff linenumber>:arff row}
#     - put this in some .pkl
#     - maybe also store the counts of sources per sci class, like in count_class_names.py
  - then generate science class pairs
     - TODO: eventually these pairs will be grouped by higher science-class parents.
#     - generate a .arff containing these science class pairs
     - train an adaboost classifier using this .arff
        - identify this pair classifier so that Hadoop can uese these names on the fly.
  - then try classifying some source (initally taken from the trainingset)
     - apply every pairwise classifier and combine to find the final classification.
     
"""
from __future__ import print_function
from __future__ import absolute_import
import os, sys
import cPickle
import gzip
import copy
import pprint   ### For debugging only
import numpy
try:
    import MySQLdb
except:
    pass
import matplotlib
import matplotlib.pyplot as plt
#from matplotlib import rcParams
import time
import threading  
import random

from optparse import OptionParser

from . import dotastro_sciclass_tools

#20100927: dstarr doesnt rember why this is done: #os.environ['TCP_DIR'] = os.path.expandvars('$HOME/src/TCP/')
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR")+'/Software/RealBogus/Code'))
try: 
    # This should only be needed for adaboost classification (will raise an exception if tinyboost compiled package is not installed)
    import classifier_adaboost_wrapper
except:
    pass

def parse_options():
    """ Deal with parsing command line options & --help.  Return options object.
    """
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-a","--generate",
                      dest="generate", \
                      action="store_true", default=False, \
                      help="Generate Pairwise classifier using AdaBoost classifiers (not weka)")
    parser.add_option("-b","--generate_weka",
                      dest="generate_weka", \
                      action="store_true", default=False, \
                      help="Generate Pairwise classifier using WEKA J48 classifiers")
    parser.add_option("-c","--test",
                      dest="test", \
                      action="store_true", default=False, \
                      help="Classify using the Adaboost based pairwise classifier")
    parser.add_option("-d","--test_weka",
                      dest="test_weka", \
                      action="store_true", default=False, \
                      help="Classify using the WEKA-J48 based pairwise classifier")
    parser.add_option("-e","--make_scidict_pkl_using_arff",
                      dest="make_scidict_pkl_using_arff", \
                      action="store_true", default=False, \
                      help="Using arff file and sciclass prunning info, generate a scidict pkl")
    parser.add_option("-f","--arff_fpath",
                      dest="arff_fpath", \
                      action="store", \
                      default="", \
                      help="Arff fpath used for generating classifiers")
    parser.add_option("-g","--classifier_dir",
                      dest="classifier_dir", \
                      action="store", \
                      default="", \
                      help="Path to dir which (will) contain pairwise classifier and cyto files")
    parser.add_option("-i","--result_name",
                      dest="result_name", \
                      action="store", \
                      default="", \
                      help="Root name to be used in classification result files and .pkl which (will) contain pruned data which will be classified.  Requires --arff_fpath when generating .pkl")
    parser.add_option("-j","--arffrow_has_ids",
                      dest="arffrow_has_ids", \
                      action="store_true", default=False, \
                      help="Boolean flag that arff rows have source-ids")
    parser.add_option("-k","--arffrow_has_no_classes",
                      dest="arffrow_has_no_classes", \
                      action="store_true", default=False, \
                      help="Boolean flag that arff rows *does not* have classes")
    parser.add_option("-l","--debosscher_classes",
                      dest="debosscher_classes", \
                      action="store_true", default=False, \
                      help="Use Debosscher science classes")
    parser.add_option("-m","--feat_dist_plots",
                      dest="feat_dist_plots", \
                      action="store_true", default=False, \
                      help="Generate Plots of feature distributions for specific classes")
    parser.add_option("-n","--deboss_percentage_exclude_analysis",
                      dest="deboss_percentage_exclude_analysis", \
                      action="store_true", default=False, \
                      help="Do Analysis using classifier on percentage variants of debosscher lightcurves")


    (options, args) = parser.parse_args()
    print("For help use flag:  --help") # KLUDGE since always: len(args) == 0
    return options


class Feature_Distribution_Plots:
    """ Generate feature-value distribution plots (.png) for some
        specific science classes.  This is useful for determining which features are
        effective or ambiguous for distinguishing between several science classes.
    
    """
    def __init__(self, pars):
        self.pars = pars
        self.tcp_db = MySQLdb.connect(host=self.pars['tcp_hostname'], \
                                      user=self.pars['tcp_username'], \
                                      db=self.pars['tcp_database'], \
                                      port=self.pars['tcp_port'])
        self.tcp_cursor = self.tcp_db.cursor()


    def get_feature_names_from_primary_arff(self):
        """ Parse the header of the original arff file which was used to generate pairwise arff training sets.
        Extract all feature-names used.
        Return a list of feature-names.
        These are the features which should be plotted in pairwise_images .pngs
        """
        featname_list = []
        lines = open(pars['dotastro_arff_fpath']).readlines() # this is a large file., so could be smarter and read top 100 lines.
        for line in lines:
            if '@attribute' in line.lower():
                line_elems = line.split()
                if (line_elems[1] != 'class') and (line_elems[1] != 'source_id'):
                    featname_list.append(line_elems[1])
            elif '@data' in line.lower():
                break # we are done parsing the file
        return featname_list


    def get_featvals_for_srcids(self, classif_summary_dict):
        """ For a several lists of dotastro srcids, retrieve all feature-values.

        Return a dictionary of structure:

                # # # #{<feat_name>:{<class_name>:{<srcid>:<featval>}}}
                {<feat_name>:{<srcid>:<featval>}}
        

select src_id, feat_values.feat_val, feat_lookup.feat_name, feat_lookup.filter_id from feat_values join feat_lookup ON (feat_values.feat_id=feat_lookup.feat_id and filter_id=8) where src_id=100148829 order by feat_name;
        """
        featname_list = self.get_feature_names_from_primary_arff()

        featvals_dict = {}
        for feat_name in featname_list:
            featvals_dict[feat_name] = {}

        for srcid in classif_summary_dict['srcid_classif_summary']['srcid_dict'].keys():
            select_str = "SELECT feat_lookup.feat_name, feat_values.feat_val FROM feat_values JOIN feat_lookup ON (feat_values.feat_id=feat_lookup.feat_id and filter_id=8) where src_id=%d" % (srcid + 100000000)
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            for row in results:
                feat_name = row[0]
                if feat_name in featname_list:
                    featvals_dict[feat_name][srcid] = row[1]
            # # # # # #
            #if srcid in [148115, 148556, 148113, 148108, 148116, 161336, 148107, 161335, 161337, 148369, 148114, 148167, 148530, 148562, 148164]:
            #    import pprint
            #    pprint.pprint((srcid, featvals_dict['freq1_harmonics_freq_0'][srcid]))
            #    import pdb; pdb.set_trace()
            #    print
        return featvals_dict


    def generate_feature_distribution_plots(self, pairwise_pruned_dict={}, classif_summary_dict={},
                                            featvals_dict={},
                                            img_fpath='', target_class_name=''):
        """ Generate feature-value distribution plots (.png) for some
        specific science classes.  This is useful for determining which features are
        effective or ambiguous for distinguishing between several science classes.

        TODO: use pars{}:
                    'feat_distrib_classes':{'target_class':'lboo',
                                    'comparison_classes':['pvsg', 'gd']},

        NEED:
          - lists of sources correctly classified for each 'comparison_classes'
          - (percentage ordered) list of classes which the 'target_class' sources were confused with
               - these classes will contain the 'comparison_classes' and maybe other clases
          - features valuesfor each source
               - probably retrieved from RDB
               - check that these feature values are the same in the .arff and are used for cla

        """

        plot_log2_featnames = ['freq1_harmonics_amplitude_0',
                               'freq2_harmonics_amplitude_0',
                               'freq3_harmonics_amplitude_0',
                               'freq1_harmonics_amplitude_1',
                               'freq2_harmonics_amplitude_1',
                               'freq3_harmonics_amplitude_1',
                               'freq1_harmonics_amplitude_2',
                               'freq2_harmonics_amplitude_2',
                               'freq3_harmonics_amplitude_2',
                               'freq1_harmonics_amplitude_3',
                               'freq2_harmonics_amplitude_3',
                               'freq3_harmonics_amplitude_3']

        plot_log10_featnames = ['freq1_harmonics_freq_0',
                                'freq2_harmonics_freq_0',
                                'freq3_harmonics_freq_0']


        ### Just make plots which compare target_class will all other classes:
        self.pars['feat_distrib_classes']['comparison_classes'] = \
                                  copy.copy(classif_summary_dict['confusion_matrix_index_list'])
        #self.pars['feat_distrib_classes']['comparison_classes'].remove(target_class_name)
        ###


        matplotlib.rcParams['axes.unicode_minus'] = False
        fig = plt.figure(figsize=(18,70), dpi=100)
        feat_keys = featvals_dict.keys()
        feat_keys.sort()
        for i_feat, feat_name in enumerate(feat_keys):
            feat_dict = featvals_dict[feat_name]

            classes_confused_with_targetclass = []

            n_cols = 4
            n_rows = len(featvals_dict) / n_cols + 1
            i_row = (i_feat) / n_cols # + 1
            i_col = (i_feat) % n_cols # + 1
            ax = fig.add_subplot(n_rows, n_cols, i_feat + 1)

            y_labels = []
            y_tick_vals = []

            featval_list = []
            # SAME:   in classif_summary_dict['srcid_classif_summary']['origclass_dict']['lboo']
            target_color_list = []
            for srcid_str in pairwise_pruned_dict[target_class_name]['srcid_list']:
                srcid_int = int(srcid_str)
                if srcid_int not in feat_dict:
                    continue
                sym_color = self.pars['feat_distrib_colors'][0]
                for i, compare_class in enumerate(self.pars['feat_distrib_classes']['comparison_classes']):
                    if srcid_int in classif_summary_dict['srcid_classif_summary']['pairclass_dict'][compare_class]:
                        sym_color = self.pars['feat_distrib_colors'][i+1]
                        ### KLUDGY: this is used below to plot lines only for classes which are confused with target class:
                        if not compare_class in classes_confused_with_targetclass:
                            classes_confused_with_targetclass.append(compare_class)
                        break
                target_color_list.append(sym_color)
                featval_list.append(feat_dict[srcid_int])
            target_featval_arr = numpy.array(featval_list)
            if feat_name in plot_log2_featnames:
                ### Make some of the plots match Debosscher's figures and use Log2()
                target_featval_arr = numpy.log2(target_featval_arr)
            elif feat_name in plot_log10_featnames:
                ### Make some of the plots match Debosscher's figures and use Log10()
                target_featval_arr = numpy.log10(target_featval_arr)


            #y_labels.append(target_class_name)
            #y_tick_vals.append(0.)
            target_y_arr = numpy.ones(len(target_featval_arr)) * 0.  # more explicit than zeros()
            #ax.plot(target_featval_arr, y_arr, '*', color=color_list)
            #if len(target_featval_arr) == 0:
            #    ax.plot([],[])
            #else:
            #    ax.scatter(target_featval_arr, target_y_arr, s=100, marker='^', c=color_list)

            for i, compare_class_name in enumerate(self.pars['feat_distrib_classes']['comparison_classes']):

                featval_list = []
                for srcid_int in classif_summary_dict['srcid_classif_summary']['pairclass_dict'][compare_class_name]:
                    if srcid_int not in feat_dict:
                        continue
                    featval_list.append(feat_dict[srcid_int])
                featval_arr = numpy.array(featval_list)
                if feat_name in plot_log2_featnames:
                    ### Make some of the plots match Debosscher's figures and use Log2()
                    featval_arr = numpy.log2(featval_arr)
                elif feat_name in plot_log10_featnames:
                    ### Make some of the plots match Debosscher's figures and use Log10()
                    featval_arr = numpy.log10(featval_arr)
                y_labels.append(compare_class_name)
                y_tick_vals.append((-1 * i) - 1)
                y_arr = numpy.ones(len(featval_arr)) * (-1 * i) - 1
                if compare_class_name == target_class_name:
                    if len(target_featval_arr) == 0:
                        ax.plot([],[])
                    else:
                        y_arr = numpy.ones(len(target_featval_arr)) * (-1 * i) - 1
                        ax.scatter(target_featval_arr, y_arr, s=100, marker='^', c=target_color_list)
                    continue
                if compare_class_name in classes_confused_with_targetclass:
                    ax.plot([min(target_featval_arr), max(target_featval_arr)],[(-1 * i) - 1, (-1 * i) - 1],
                            color=self.pars['feat_distrib_colors'][i+1],
                            linestyle='solid', linewidth=2)
                if len(featval_arr) > 0:
                    color_list = [self.pars['feat_distrib_colors'][i+1]] * len(featval_arr)
                    ax.scatter(featval_arr, y_arr, s=50, c=color_list, marker='d') #marker='h')

            ax.set_ylim(-1 * len(self.pars['feat_distrib_classes']['comparison_classes']) - .5, 1.5)
            ax.set_yticks(y_tick_vals)
            ax.set_yticklabels(y_labels)
            #ax.set_xticks([])
            #ax.set_xticklabels([])
            if feat_name in plot_log2_featnames:
                feat_name = "Log2(%s)" % (feat_name)
            elif feat_name in plot_log10_featnames:
                feat_name = "Log10(%s)" % (feat_name)
            title_str = feat_name.replace('harmonics','harm').replace('amplitude','amp').replace('freq','freq').replace('moments','moment').replace('error','err').replace('percentage','perc').replace('phase','phase').replace('distance','dist').replace('peak2peak','pk2pk').replace('nearest','near').replace('galaxy','gal')
            ax.set_title(title_str, fontsize=12)
            #ax.annotate(title_str, xy=(.5, 0.95), xycoords='axes fraction',
            #            horizontalalignment='center',
            #            verticalalignment='top',
            #            fontsize=7)
        #img_fpath = self.pars['feat_dist_image_fpath']
        plt.savefig(img_fpath)

        ### DEBUG PRINT:
        #for k, class_n in enumerate(self.pars['feat_distrib_classes']['comparison_classes']):
        #    print self.pars['feat_distrib_colors'][k+1], class_n



    def threaded_gen_dist_plots_for_all_classes(self, pairwise_pruned_dict={}, classif_summary_dict={}):
        """ Do generate_feature_distribution_plots() for all science classes, using threading.
        """
        running_threads = []
        featvals_dict = self.get_featvals_for_srcids(classif_summary_dict)

        local_img_fpath_list = []
        #for class_name in ['lboo']:
        for class_name in classif_summary_dict['confusion_matrix_index_list']:
            for thr in running_threads:
                if not thr.isAlive():
                    running_threads.remove(thr)
            n_tasks_to_spawn = self.pars['number_threads'] - \
                                                       len(running_threads)
            while n_tasks_to_spawn < 1:
                time.sleep(self.pars['t_sleep'])
                for thr in running_threads:
                    if not thr.isAlive():
                        running_threads.remove(thr)
                n_tasks_to_spawn = self.pars['number_threads'] - \
                                                       len(running_threads)

            img_fpath = "%s/confused_%s.png" % (self.pars['feat_dist_image_local_dirpath'], class_name)

            t = threading.Thread(target=self.generate_feature_distribution_plots, \
                                 kwargs={'pairwise_pruned_dict':pairwise_pruned_dict,
                                         'classif_summary_dict':classif_summary_dict,
                                         'featvals_dict':featvals_dict,
                                         'img_fpath':img_fpath,
                                         'target_class_name':class_name})
            t.start()
            running_threads.append(t)
            local_img_fpath_list.append(img_fpath)

        print()
        while len(running_threads) > 0:
            time.sleep(self.pars['t_sleep'])
            for thr in running_threads:
                if not thr.isAlive():
                    running_threads.remove(thr)
        time.sleep(1) # just ensure the files are written before scp'ing
        scp_str = "scp -C %s/* %s" % (self.pars['feat_dist_image_local_dirpath'],
                                   self.pars['feat_dist_image_remote_scp_str'])
        os.system(scp_str)




class Weka_Pairwise_Classification:
    """ Do Pairwise Classification using weka (rather than AdaBoost)

    JPype classification code taken from plugin_classifier.py: L71, L83, L165

    """
    def __init__(self, pars={}):
        self.pars = pars
        self.wc = {}

        import jpype
        os.environ["JAVA_HOME"] = '/usr/lib/jvm/java-6-sun-1.6.0.03'
        os.environ["CLASSPATH"] += os.path.expandvars(':$TCP_DIR/Software/ingest_tools')
        if not jpype.isJVMStarted():
            #TODO / DEBUG: disable the next line for speed-ups once stable?
            _jvmArgs = ["-ea"] # enable assertions
            _jvmArgs.append("-Djava.class.path=" + \
                                os.environ["CLASSPATH"])
            ###20091905 dstarr comments out:
            #_jvmArgs.append("-Xmx1000m")
            #_jvmArgs.append("-Xmx12000m") # 20100726 : dstarr comments out, tries smaller value:
            _jvmArgs.append("-Xmx2200m") # 4000 & 5000m works, 3500m doesnt for some WEKA .models
            if 0:
                jpype.startJVM(jpype.getDefaultJVMPath(), *_jvmArgs)

        if 1:
            pass
            ######
            """
            wc = weka_classifier.WekaClassifier(weka_training_model_fpath, weka_training_arff_fpath)
            arff_record = [0.65815,3.518955,0.334025,0.79653,44.230391,3.163003,0.025275,0.004501,0.295447,-0.133333,3.144411,-0.65161,None,None]

            for class_schema_name in class_schema_name_list:
                class_schema_dict = self.class_schema_definition_dicts[class_schema_name]
                weka_training_model_fpath = class_schema_dict['weka_training_model_fpath']
                weka_training_arff_fpath = class_schema_dict['weka_training_arff_fpath']
                self.wc[class_schema_name] = weka_classifier.WekaClassifier( \
                                      weka_training_model_fpath, weka_training_arff_fpath)

            #classified_result = wc.classify(arff_record)

            classified_result = self.wc[plugin_name].get_class_distribution(arff_record)

            out_plugin_classification_dict[src_id] = {plugin_name:{'probabilities':{}}}
            for i, (class_name,class_prob) in enumerate(classified_result[:3]):
                class_id = self.class_schema_definition_dicts[plugin_name] \
                                                  ['class_name_id_dict'][class_name]
                class_probs_dict[src_id].append(\
                                 {'schema_id':self.class_schema_definition_dicts\
                                                   [plugin_name]['schema_id'],
                                  'class_id':class_id,
                                  'class_name':class_name,
                                  'prob':class_prob,
                                  'class_rank':i,
                                  'prob_weight':prob_weight})
                out_plugin_classification_dict[src_id][plugin_name] \
                                  ['probabilities'][class_name] = {'prob':class_prob, \
                                                                   'prob_weight':1.0} # WEKA default KLUDGE
                # # # # # # #
                # TODO: eventually add WEKA ['value_added_properties'] to the returned dict
            """


    def load_weka_classifiers(self, classifier_dict={}, pair_path_replace_tup=None):
        """ Load the JPype classifiers for each pairwise case using weka .model files.
        """
        from . import weka_classifier
        for pair_name, pair_dict in classifier_dict.iteritems():
            if pair_path_replace_tup is None:
                self.wc[pair_name] = weka_classifier.WekaClassifier( \
                                                           pair_dict['model_fpath'], 
                                                           pair_dict['arff_fpath'])
            else:
                self.wc[pair_name] = weka_classifier.WekaClassifier( \
                                                      pair_dict['model_fpath'].replace(pair_path_replace_tup[0],
                                                                                       pair_path_replace_tup[1]),
                                                      pair_dict['arff_fpath'].replace(pair_path_replace_tup[0],
                                                                                      pair_path_replace_tup[1]))


    def reload_weka_classifiers(self, classifier_dict={}, pair_path_replace_tup=None):
        """ Load the JPype classifiers for each pairwise case using weka .model files.
        """
        for pair_name, pair_dict in classifier_dict.iteritems():
            if pair_path_replace_tup is None:
                self.wc[pair_name].reload_model_for_same_classes( \
                                                           pair_dict['model_fpath'])
            else:
                self.wc[pair_name].reload_model_for_same_classes( \
                                              pair_dict['model_fpath'].replace(pair_path_replace_tup[0],
                                                                               pair_path_replace_tup[1]))



            
    def convert_to_weka_record(self, arff_row):
        """ Convert arff row string into a "weka record" list which is usable by:

                   weka_classifier.py::get_class_distribution(record)

        """
        feat_values = arff_row.split(',')
        num_list = []

        for elem in feat_values:
            #if elem == 't':
            #    num_list.append([1])
            #elif elem == 'f':
            #    num_list.append([0])
            if elem == '?':
                #num_list.append([numpy.NaN])
                num_list.append(None)
            else:
                #num_list.append([float(elem)])
                num_list.append(float(elem))
        return num_list


    def generate_weka_j48_top_feats(self, class_summary):
        """
        # TODO: need to add top_feats to class_summary[class_name]['top_feats']
        #   - like L413 in get_classifications_for_pruned_trainset_rows()



(Pdb) pprint.pprint(class_summary['c'])
{'n_other_srcs_incorrectly_final_classified': 0,
 'n_sources': 0,
 'top_feats': [],
 'tot_correctly_final_classified': 0,
 'tot_correctly_sub_classified': 0,
 'tot_incorrect_final_classified': 0,
 'tot_incorrect_sub_classified': 0}

???? I think we should be generating the top_feats not just for a scienc lass,
     - but, per: (science_class, pairwise)
     - so that cytoscape attribsnfor connection between source and science_class 

        """
        for class_name, class_dict in class_summary.iteritems():
            class_dict['top_feats'] = [(0.0,'blah1'), (0.0,'blah2')]
        print()
        # # #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + '/Software/web'))
        # # #import apply_J48_classification
        # # #ApplyJ48Classification = apply_J48_classification.Apply_J48_Classification(pars={})
        # # #print

        # TODO: for each pairwise in class_suummary, open .result file and parse lines
        #ApplyJ48Classification.parse_decisiontree_lines_into_tuplist(unmarked_classif_tree_lines)

        """
blah[feat_name] = (count_val)
   ->>> this is done for every pairwise classifier (which applies to a
   science class)

use aprse_dcisiontree_lines_into_tuplist
 - then iterate over tuples
    - when get to a line with >0 train_class_count
        - calculate and update each feature since last ( >0
          train_class_count) occurance


blah[feat_name] = (count_val)
   ->>> this is done for every pairwise classifier (which applies to a
   science class)

use aprse_dcisiontree_lines_into_tuplist
 - then iterate over tuples
    - when get to a line with >0 train_class_count
        - calculate and update each feature since last ( >0
          train_class_count) occurance

* each feature along branch (xxx/yyy)is given the value : (xxx - yyy) / N_depth
   - I expect to see some of these as most significant for c___rr-lyr:
     freq1_harmonics_freq_0
     ws_variability_self
     flux_percentile_ratio_mid65

        """


        

    def do_pairwise_classification(self, classifier_dict={}, pairwise_pruned_dict={}, set_num=None, store_confids=True):
        """
* assuming a .model has been generated for a pairwise classification
* it might be easiest to have a function which is similar to:
     get_classifications_for_pruned_trainset_row()
** Parse the classification model Pickle
*** .model fpath
** Parse (trainingset .arff-row Pickle)
** Do: 
*** generate classifications
*** tally individual pairwise classifications
        """
        if len(self.pars['taxonomy_prune_defs']['terminating_classes']) == 0:
            class_shortname_list = pairwise_pruned_dict.keys()
            class_shortname_list.sort()
        else:
            class_shortname_list = self.pars['taxonomy_prune_defs']['terminating_classes']

        confusion_matrix = numpy.zeros((len(class_shortname_list),
                                        len(class_shortname_list)))
        confusion_matrix_index_class_dict = {}
        for i, class_name in enumerate(class_shortname_list):
            
            confusion_matrix_index_class_dict[class_name] = i

        class_summary = {}
        for class_name in class_shortname_list:
            class_summary[class_name] = {'n_sources':0,
                                         'tot_correctly_sub_classified':0,
                                         'tot_incorrect_sub_classified':0,
                                         'tot_correctly_final_classified':0,
                                         'tot_incorrect_final_classified':0,
                                         'n_other_srcs_incorrectly_final_classified':0,
                                         'top_feats':[]}

        tally_dict_empty = {}
        for classifier_name in class_shortname_list:
            tally_dict_empty[classifier_name] = {'classif_count':0,
                                                 'notclassif_count':0,
                                                 'classif_conf_total':0.,
                                                 'notclassif_conf_total':0.}

        # TODO: need to add top_feats to class_summary[class_name]['top_feats']
        #   - like L413 in get_classifications_for_pruned_trainset_rows()
        self.generate_weka_j48_top_feats(class_summary)

        srcid_classif_summary = {'origclass_dict':{},
                                 'pairclass_dict':{},
                                 'srcid_dict':{},
                                 'confids':{}}
        for class_name in class_shortname_list:
            srcid_classif_summary['origclass_dict'][class_name] = []
            srcid_classif_summary['pairclass_dict'][class_name] = []

        if store_confids:
            for classifier_name in classifier_dict.keys():
                srcid_classif_summary['confids'][classifier_name]={'class_pred':[],
                                                               'class_conf':[],
                                                               'orig_class':[]}

        i_inputrow = 0
        for orig_class, orig_class_dict in pairwise_pruned_dict.iteritems():
            print(orig_class)
            if self.fp_cyto_nodeattrib != None:
                self.fp_cyto_nodeattrib.write("%s\t%s\t0\n" % (orig_class, orig_class))
            if orig_class not in class_summary:
                continue # # # # # This occurs in test_pairwise_on_citris33_ipython.py call, when using all 1392 debosscher sources.  SX is available in xml, but not used by debosscher-25class confusion matrix, thus the pruning of the dotastrodataset to 25 classes still results in SX existing in pairwise_pruned_dict.
            class_summary[orig_class]['n_sources'] = orig_class_dict['count']

            for i_src, arff_row in enumerate(orig_class_dict['arffrow_wo_classnames']):
                srcid_dotastro = orig_class_dict['srcid_list'][i_src]
                if type(srcid_dotastro) == type(''):
                    if srcid_dotastro.count('_') > 0:
                        srcid_dotastro = int(orig_class_dict['srcid_list'][i_src].split('_')[0])
                        if set_num is None:
                            set_source = int(orig_class_dict['srcid_list'][i_src].split('_')[2])
                        else:
                            set_source = int(orig_class_dict['srcid_list'][i_src].split('_')[2])
                            if set_source != set_num:
                                continue # Skip classifying this source since it doesnt belong to the specified set.
                            

                    else:
                        srcid_dotastro = int(srcid_dotastro)
                #if ((orig_class == 'puls') or (orig_class == 'rot')):
                #    print orig_class, "%s_%d\t%s\t1\thttp://lyra.berkeley.edu/tcp/dotastro_periodfold_plot.php?srcid=%d\n" % (orig_class, i_src, orig_class, srcid_dotastro + 100000000)
                #self.fp_cyto_nodeattrib.write("%s_%d\t%s\t1\n" % (orig_class, i_src, orig_class))
                if self.fp_cyto_nodeattrib != None:
                    self.fp_cyto_nodeattrib.write("%s_%d\t%s\t1\thttp://lyra.berkeley.edu/tcp/dotastro_periodfold_plot.php?srcid=%d\n" % (orig_class, i_src, orig_class, srcid_dotastro + 100000000))

                weka_record = self.convert_to_weka_record(arff_row)

                tally_dict = copy.deepcopy(tally_dict_empty)
                for classifier_name in classifier_dict.keys():
                    # # # #import pdb; pdb.set_trace()
                    classified_result = self.wc[classifier_name].get_class_distribution(weka_record)
                    
                    if classified_result[0][1] > classified_result[1][1]:
                        sciclass_pred = classified_result[0][0]
                        notpred_sciclass = classified_result[1][0]
                        confidence = classified_result[0][1]
                    else:
                        sciclass_pred = classified_result[1][0]
                        notpred_sciclass = classified_result[0][0]
                        confidence = classified_result[1][1]

                    if store_confids:
                        srcid_classif_summary['confids'][classifier_name]['class_pred'].append(sciclass_pred)
                        srcid_classif_summary['confids'][classifier_name]['class_conf'].append(confidence)
                        srcid_classif_summary['confids'][classifier_name]['orig_class'].append(orig_class)
                    
                    if sciclass_pred == orig_class:
                        class_summary[orig_class]['tot_correctly_sub_classified'] += 1

                    tally_dict[sciclass_pred]['classif_count'] += confidence
                    tally_dict[notpred_sciclass]['notclassif_count'] += confidence
                sort_list = []
                for sciclass, class_dict in tally_dict.iteritems():
                    sort_list.append((class_dict['classif_count'], sciclass))
                sort_list.sort(reverse=True)

                ### Store some summary information:
                srcid_classif_summary['origclass_dict'][orig_class].append(srcid_dotastro)
                srcid_classif_summary['pairclass_dict'][sort_list[0][1]].append(srcid_dotastro)
                if store_confids:
                    srcid_classif_summary['srcid_dict'][srcid_dotastro] = {'origclass':copy.copy(orig_class),
                                                                   'pairclass_sorted_tups':copy.deepcopy(sort_list)}

                #for count, sciclass in sort_list[:3]:
                for count, sciclass in sort_list[:2]:
                    ### I want the 3rd weight to be 1, and the others to be (count_n - count_3rd)**3
                    #weight = (count - sort_list[2][0] + 1)**3
                    ### I want the 2nd weight to be 1, and the others to be (count_n - count_2nd)**3
                    weight = (count - sort_list[1][0] + 1)**3
                    if self.fp_cyto_network != None:
                        self.fp_cyto_network.write("%s_%d\t%s\t%lf\t%s\t%s\t%s_%lf\t%s_%lf\n" % (orig_class, i_src, sciclass, weight, orig_class, sciclass, class_summary[sciclass]['top_feats'][0][1], class_summary[sciclass]['top_feats'][0][0], class_summary[sciclass]['top_feats'][1][1], class_summary[sciclass]['top_feats'][1][0]))

                i_orig_class = confusion_matrix_index_class_dict[orig_class]
                i_predict_class = confusion_matrix_index_class_dict[sort_list[0][1]]
                confusion_matrix[i_orig_class][i_predict_class] += 1
                
                if sort_list[0][1] == orig_class:
                    class_summary[orig_class]['tot_correctly_final_classified'] += 1
                else:
                    class_summary[sort_list[0][1]]['n_other_srcs_incorrectly_final_classified'] += 1
            #pprint.pprint((orig_class, orig_class_dict['count'], class_summary[orig_class]))
        return {'confusion_matrix':confusion_matrix,
                'confusion_matrix_index_class_dict':confusion_matrix_index_class_dict,
                'confusion_matrix_index_list':class_shortname_list,
                'srcid_classif_summary':srcid_classif_summary}


    def initialize_temp_cyto_files(self):
        """ Open cytoscape importable files for writing.  Delete if exist already.
        """
        fpath = "/tmp/%s" % (self.pars['cyto_network_fname'])
        if os.path.exists(fpath):
            os.system('rm ' + fpath)
        self.fp_cyto_network = open(fpath, 'w')

        fpath = "/tmp/%s" % (self.pars['cyto_nodeattrib_fname'])
        if os.path.exists(fpath):
            os.system('rm ' + fpath)
        self.fp_cyto_nodeattrib = open(fpath, 'w')


    def copy_cyto_file_to_final_path(self):
        """ Copy cyto files to a seperate location.  This is done since Dropbox seems
        to have issues with slowly written (or often updated) files.
        """
        self.fp_cyto_network.close()
        self.fp_cyto_nodeattrib.close()

        cp_str = "cp /tmp/%s %s/%s" % (self.pars['cyto_network_fname'],
                                       self.pars['cyto_work_final_fpath'],
                                       self.pars['cyto_network_fname'])
        os.system(cp_str)

        cp_str = "cp /tmp/%s %s/%s" % (self.pars['cyto_nodeattrib_fname'],
                                       self.pars['cyto_work_final_fpath'],
                                       self.pars['cyto_nodeattrib_fname'])
        os.system(cp_str)


    def add_pretty_indents_to_elemtree(self, elem, level=0):
        """ in-place prettyprint formatter

        This more recently came from tet_py_j48RF_classifier_onPTF.py
        This came from db_importer.py
        """
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                if (elem.tag == "MAG") or (elem.tag == "TIME"):
                    elem.tail = "\n" + (level+1)*"  "
                    continue
                self.add_pretty_indents_to_elemtree(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i



        
    def fill_stats_tables(self, table_stats=None, classif_summary_dict={},
                          debosscher_confusion_data=None):
        """ Fill stats like true positive rate, false positive rate...
        """
        from xml.etree import ElementTree

        val_list = []
        class_total_counts = []
        for row_list in classif_summary_dict['confusion_matrix']:
            row_val_list = []
            for elem in row_list:
                val_list.append(elem)
                row_val_list.append(elem)
            class_total_counts.append(sum(row_val_list))
        val_list.sort(reverse=True)

        tr = ElementTree.SubElement(table_stats, "TR")
        ElementTree.SubElement(tr, "TD", bgcolor="#2a2a2a").text = "N srcs"
        ElementTree.SubElement(tr, "TD", bgcolor="#2a2a2a").text = "TP_rate"
        ElementTree.SubElement(tr, "TD", bgcolor="#2a2a2a").text = "FP_rate"
        
        tr_list = [] # This is used to add extra statistics on the final column
        diagonal_sum = 0
        for i, row_list in enumerate(classif_summary_dict['confusion_matrix']):
            tr = ElementTree.SubElement(table_stats, "TR")
            elem = row_list[i] # the diagonal value
            try:
                percent_of_class = float(elem) / float(class_total_counts[i])
            except:
                percent_of_class = 0.0

            diagonal_sum += elem

            col_sum = classif_summary_dict['confusion_matrix'][:,i].sum()
            other_classes_sum = classif_summary_dict['confusion_matrix'][:i,:].sum()
            other_classes_sum += classif_summary_dict['confusion_matrix'][i+1:,:].sum()
            fp_rate = (col_sum - elem) / float(other_classes_sum)

            percent_full_hex_str = "%2.2x" % (int((0 * 255)))
            percent_hex_str = percent_full_hex_str[percent_full_hex_str.rfind('x')+1:]
            if debosscher_confusion_data != None:
                ElementTree.SubElement(tr, "TD", bgcolor="#%s0000" % \
                                   (percent_hex_str)).text = "%d/%d" % (class_total_counts[i],
                                             debosscher_confusion_data['class_total_counts'][i])
            else:
                ElementTree.SubElement(tr, "TD", bgcolor="#%s0000" % \
                                   (percent_hex_str)).text = "%3d" % (class_total_counts[i])

            ElementTree.SubElement(tr, "TD", bgcolor="#%s0000" % \
                                   (percent_hex_str)).text = "%0.3lf" % (percent_of_class)
            ElementTree.SubElement(tr, "TD", bgcolor="#%s0000" % \
                                   (percent_hex_str)).text = "%0.3lf" % (fp_rate)

            ElementTree.SubElement(tr, "TD", bgcolor="#2a2a2a").text = \
                                 "%s" % (classif_summary_dict['confusion_matrix_index_list'][i])
            tr_list.append(tr)


        ### add extra statistics on the final column: 
        false_classification_rate = 1 - (diagonal_sum / float(sum(class_total_counts)))
        ### I think I want each elem of diag to be devided by class_total_counts[i]

        ElementTree.SubElement(tr_list[0], "TD", bgcolor="#2a2a2a").text = "True_Class_Error"
        ElementTree.SubElement(tr_list[1], "TD", bgcolor="#2a2a2a").text = "%0.3lf" % (false_classification_rate)



    def parse_debosscher_confusion_table(self, table_fpath):
        """ Parse a html table which Debosscher uses to display a classifier's confusion matrix
        """
        # TODO retrieve html (or have shortened form placed in Data/ , xmlize, parse into structure, generate confusion html matrix (with heatmap colors)
        from xml.etree import ElementTree
        
        t = ElementTree.fromstring(open(table_fpath).read())

        class_name_list = []
        confusion_dict = {}
        for class_elem in t[0][1:]:
            class_name = class_elem.text
            class_name_list.append(class_name)
            confusion_dict[class_name] = []

        for table_row in t[1:-2]:
            #class_name = table_row[0].text
            for i, elem in enumerate(table_row[1:]):
                class_name = class_name_list[i]
                confusion_dict[class_name].append(int(elem.text))

        return {'class_name_list':class_name_list,
                'confusion_dict':confusion_dict}


    def fill_confusion_tables(self, table_count=None, table_percent=None,
                              confusion_matrix=[], class_name_list=[],
                              insert_image_links=False,
                              table_count_name='count', table_percent_name='percent',
                              do_transpose=True):
        """ Parse Confusion matrix data from html tables found from Debosscher 2007 paper :
        http://www.aanda.org/index.php?option=com_article&access=standard&Itemid=129&url=/articles/aa/full/2007/45/aa7638-07/aa7638-07.html

        NOTE: The input html tables have already been trimmed into xml parseable files.

        """
        from xml.etree import ElementTree
        from string import ascii_letters

        val_list = []
        class_total_counts = []
        for row_list in confusion_matrix:
            row_val_list = []
            for elem in row_list:
                val_list.append(elem)
                row_val_list.append(elem)
            class_total_counts.append(sum(row_val_list))
        val_list.sort(reverse=True)
        count_color_count_max = max(val_list[3:])

        if do_transpose:
            temp_arr = numpy.array(confusion_matrix)
            temp_b = temp_arr.transpose()
            confusion_matrix = temp_b.tolist()


        ######
        #number_classified_as_a_class = []
        #for row_list in confusion_matrix:
        #    row_val_list = []
        #    for elem in row_list:
        #        val_list.append(elem)
        #        row_val_list.append(elem)
        #    class_total_counts.append(sum(row_val_list))
        ######



        if table_count != None:
            tr_count = ElementTree.SubElement(table_count, "TR")
            for i in range(len(class_name_list)):
                ElementTree.SubElement(tr_count, "TD", bgcolor="#2a2a2a").text = "%s" % (ascii_letters[i])
            ElementTree.SubElement(tr_count, "TD", bgcolor="#000000").text = "%s" % (table_count_name)

        tr_percent = ElementTree.SubElement(table_percent, "TR")
        for i in range(len(class_name_list)):
            ElementTree.SubElement(tr_percent, "TD", bgcolor="#2a2a2a").text = "%s" % (ascii_letters[i])
        ElementTree.SubElement(tr_percent, "TD", bgcolor="#000000").text = "%s" % (table_percent_name)
            
        for i, row_list in enumerate(confusion_matrix):
            if table_count != None:
                tr_count = ElementTree.SubElement(table_count, "TR")
            tr_percent = ElementTree.SubElement(table_percent, "TR")
            for j, elem in enumerate(row_list):
                ### Figure out the Color intensity for the count table:
                try:
                    count_color_fraction = float(elem) / float(count_color_count_max)                    
                except:
                    count_color_fraction = 0.0 # div by zero catch

                str_val = "%3.0d" % (int(elem))
                if (i == j):
                    str_val = "%3.3d" % (int(elem))
                    
                if ((count_color_fraction > 0.0099999) and (count_color_fraction < 0.15)):
                    count_color_fraction = 0.15 # give small count_color_fractions some minimum color
                elif (count_color_fraction > 1.0):
                    count_color_fraction = 1.0
                count_full_hex_str = "%2.2x" % (int((count_color_fraction * 255)))
                count_hex_str = count_full_hex_str[count_full_hex_str.rfind('x')+1:]
                if table_count != None:
                    ElementTree.SubElement(tr_count, "TD", bgcolor="#%s0000" % (count_hex_str)).text = str_val

                ### Figure out the percentages for the percent table:
                try:
                    #percent_of_class = float(elem) / float(class_total_counts[i])
                    percent_of_class = float(elem) / float(class_total_counts[j])
                except:
                    percent_of_class = 0.0

                if (percent_of_class < 0.00099999) and (i != j):
                    percent_of_class_str = "" #"&nbsp&nbsp&nbsp&nbsp&nbsp"
                elif (percent_of_class == 1.0):
                    percent_of_class_str = "1.0"
                else:
                    percent_of_class_str_a = "%2.2f" % (percent_of_class)
                    percent_of_class_str = percent_of_class_str_a[1:] # get rid of the preceeding 0

                if (percent_of_class <= 0.00099999):
                    percent_color_fraction = 0.0
                elif (percent_of_class < 0.10):
                    percent_color_fraction = 0.2 # give small count_color_fractions some minimum color
                elif (percent_of_class <= 0.50):
                    percent_color_fraction = (percent_of_class / 0.50)
                elif (percent_of_class > 0.50):
                    percent_color_fraction = 1.0

                percent_full_hex_str = "%2.2x" % (int((percent_color_fraction * 255)))
                percent_hex_str = percent_full_hex_str[percent_full_hex_str.rfind('x')+1:]
                ElementTree.SubElement(tr_percent, "TD", bgcolor="#%s0000" % \
                                       (percent_hex_str)).text = percent_of_class_str
            if table_count != None:
                ElementTree.SubElement(tr_count, "TD", bgcolor="#2a2a2a").text = \
                      "%s=%s" % (ascii_letters[i], class_name_list[i])
            if insert_image_links:
                cell = ElementTree.SubElement(tr_percent, "TD", bgcolor="#2a2a2a")
                img_url = "%s/confused_%s.png" % (self.pars['feat_dist_image_rooturl'], class_name_list[i])
                ElementTree.SubElement(cell, "A", href=img_url).text = \
                      "%s=%s" % (ascii_letters[i], class_name_list[i])
            else:
                # Done in the deboscher confusion matrix case since there are no .png with deboscher-class names
                ElementTree.SubElement(tr_percent, "TD", bgcolor="#2a2a2a").text = \
                      "%s=%s" % (ascii_letters[i], class_name_list[i])

        return {'class_total_counts':class_total_counts}


    def fill_difference_confusion_tables(self, table_count=None, table_percent=None,
                                      confusion_matrix=[], class_name_list=[],
                                         table_count_name='count', table_percent_name='percent'):
        """ Parse Confusion matrix data from html tables found from Debosscher 2007 paper :
        http://www.aanda.org/index.php?option=com_article&access=standard&Itemid=129&url=/articles/aa/full/2007/45/aa7638-07/aa7638-07.html

        NOTE: The input html tables have already been trimmed into xml parseable files.

        NOTE: Adapted from fill_confusion_tables()

        """
        from xml.etree import ElementTree
        from string import ascii_letters

        val_list = []
        class_total_counts = []

        #### OTOD maybe do this for 
        for row_list in confusion_matrix:
            row_val_list = []
            for elem in row_list:
                val_list.append(elem)
                row_val_list.append(elem)
            class_total_counts.append(sum(row_val_list))
        val_list.sort(reverse=True)
        count_color_count_max = max(val_list[3:])

        if table_count != None:
            tr_count = ElementTree.SubElement(table_count, "TR")
            for i in range(len(class_name_list)):
                ElementTree.SubElement(tr_count, "TD", bgcolor="#2a2a2a").text = "%s" % (ascii_letters[i])
            ElementTree.SubElement(tr_count, "TD", bgcolor="#000000").text = "%s" % (table_count_name)

        tr_percent = ElementTree.SubElement(table_percent, "TR")
        for i in range(len(class_name_list)):
            ElementTree.SubElement(tr_percent, "TD", bgcolor="#2a2a2a").text = "%s" % (ascii_letters[i])
        ElementTree.SubElement(tr_percent, "TD", bgcolor="#000000").text = "%s" % (table_percent_name)
            
        for i, row_list in enumerate(confusion_matrix):
            #import pdb; pdb.set_trace()
        
            if table_count != None:
                tr_count = ElementTree.SubElement(table_count, "TR")
            tr_percent = ElementTree.SubElement(table_percent, "TR")
            for j, elem in enumerate(row_list):
                ### Figure out the Color intensity for the count table:
                try:
                    count_color_fraction = float(elem) / float(count_color_count_max)                    
                except:
                    count_color_fraction = 0.0 # div by zero catch

                str_val = "%3.0d" % (int(elem))
                if (i == j):
                    str_val = "%3.3d" % (int(elem))
                    
                if ((count_color_fraction > 0.0099999) and (count_color_fraction < 0.15)):
                    count_color_fraction = 0.15 # give small count_color_fractions some minimum color
                elif (count_color_fraction > 1.0):
                    count_color_fraction = 1.0
                count_full_hex_str = "%2.2x" % (int((count_color_fraction * 255)))
                count_hex_str = count_full_hex_str[count_full_hex_str.rfind('x')+1:]
                if table_count != None:
                    ElementTree.SubElement(tr_count, "TD", bgcolor="#%s0000" % (count_hex_str)).text = str_val

                ### Figure out the percentages for the percent table:
                if str(numpy.nan) == str(elem):
                    # KLUDGE since I cant do direct comparison of numpy float and float64 (just NaN issue?)
                    percent_of_class = 0.0
                else:
                    percent_of_class = float(elem)# / float(class_total_counts[i])

                sign = 1.0
                if percent_of_class < 0:
                    sign = -1.0
                    percent_of_class *= -1.0

                if (percent_of_class < 0.00099999) and (i != j):
                    percent_of_class_str = "" #"&nbsp&nbsp&nbsp&nbsp&nbsp"
                elif (percent_of_class == 1.0):
                    percent_of_class_str = "1.0"
                else:
                    # # # # # TODO: may want to use %3.3f:
                    percent_of_class_str_a = "%2.2f" % (percent_of_class)
                    percent_of_class_str = percent_of_class_str_a[1:] # get rid of the preceeding 0
                    #percent_of_class_str = "%2.2f" % (percent_of_class)

                # # # # # TODO: probably want to tweak these numbers:

                if (percent_of_class <= 0.00099999):
                    percent_color_fraction = 0.0
                elif (percent_of_class < 0.1):
                    percent_color_fraction = 0.2 # give small count_color_fractions some minimum color
                elif (percent_of_class <= 0.50):
                    percent_color_fraction = (percent_of_class / 0.50)
                elif (percent_of_class > 0.50):
                    percent_color_fraction = 1.0

                percent_full_hex_str = "%2.2x" % (int((percent_color_fraction * 255)))
                percent_hex_str = percent_full_hex_str[percent_full_hex_str.rfind('x')+1:]
                if (sign > 0) and (i == j):
                    ElementTree.SubElement(tr_percent, "TD", bgcolor="#%s0000" % \
                                       (percent_hex_str)).text = percent_of_class_str
                elif (sign > 0) and (i != j):
                    color = "#%s0030" % (percent_hex_str)
                    if percent_of_class_str == '':
                        color = "#000000"
                    ElementTree.SubElement(tr_percent, "TD", bgcolor=color \
                                           ).text = percent_of_class_str
                else:
                    ElementTree.SubElement(tr_percent, "TD", bgcolor="#0019%s" % \
                                       (percent_hex_str)).text = percent_of_class_str

            if table_count != None:
                ElementTree.SubElement(tr_count, "TD", bgcolor="#2a2a2a").text = \
                      "%s=%s" % (ascii_letters[i], class_name_list[i])
            ElementTree.SubElement(tr_percent, "TD", bgcolor="#2a2a2a").text = \
                      "%s=%s" % (ascii_letters[i], class_name_list[i])

        return {'class_total_counts':class_total_counts}


    def write_confusionmatrix_heatmap_html(self, classif_summary_dict, html_fpath='',
                                           debosscher_confusion_data={},
                                           crossvalid_summary_dict={}):
        """ Generate a .html which makes a heatmap table of the confusion
        matrix in given datastructure.

        This is adapted from test_py_j48RF_classifier_onPTF.py::add_matrix_with_heatmap()

        """
        from xml.etree import ElementTree

        html = ElementTree.Element("HTML")
        body = ElementTree.SubElement(html, "BODY", link="#99CCFF", vlink="#FF99FF")
        table_main = ElementTree.SubElement(body, "TABLE", BORDER="1", CELLPADDING="1", CELLSPACING="1")
        tr_main = ElementTree.SubElement(table_main, "TR")

        ### This table contains counts of classifications and mis-classifications for
        ###    Pairsise classifier.  This is less informative than the percentage table:        
        #table_count = ElementTree.SubElement(ElementTree.SubElement(tr_main, "TD"),
        #                                     "TABLE", BORDER="1",
        #                                     CELLPADDING="2", CELLSPACING="1",
        #                                     style="color: white;")


        table_debosscher_percent = ElementTree.SubElement(ElementTree.SubElement(tr_main, "TD"),
                                             "TABLE", BORDER="1",
                                             CELLPADDING="2", CELLSPACING="1",
                                             style="color: white;")
        table_percent = ElementTree.SubElement(ElementTree.SubElement(tr_main, "TD"),
                                             "TABLE", BORDER="1",
                                             CELLPADDING="2", CELLSPACING="1",
                                             style="color: white;")
        table_stats = ElementTree.SubElement(ElementTree.SubElement(tr_main, "TD"),
                                             "TABLE", BORDER="1",
                                             CELLPADDING="2", CELLSPACING="1",
                                             style="color: white;")

        tr_line_2 = ElementTree.SubElement(table_main, "TR")
        table_diff_percent = ElementTree.SubElement(ElementTree.SubElement(tr_line_2, "TD"),
                                             "TABLE", BORDER="1",
                                             CELLPADDING="2", CELLSPACING="1",
                                             style="color: white;")
        table_crossvalid = ElementTree.SubElement(ElementTree.SubElement(tr_line_2, "TD"),
                                             "TABLE", BORDER="1",
                                             CELLPADDING="2", CELLSPACING="1",
                                             style="color: white;")

        ###This would put on of the feature-value distribution multi-plot images on the webpage:
        #table_featdist = ElementTree.SubElement(body, "TABLE", BORDER="1", CELLPADDING="1", CELLSPACING="1")
        #row_featdist = ElementTree.SubElement(table_featdist, "TR")
        #ElementTree.SubElement(ElementTree.SubElement(row_featdist, "TD"),
        #                                     "img", src=self.pars['feat_dist_image_url'])

        # OBSOLETE:
        #tr_debosscher = ElementTree.SubElement(table_main, "TR")
        ### This table contains counts of classifications and mis-classifications for
        ###    for the Debosscher classifier taken from 2007 Paper's HTML table.
        #table_debosscher_count = ElementTree.SubElement(ElementTree.SubElement(tr_debosscher, "TD"),
        #                                     "TABLE", BORDER="1",
        #                                     CELLPADDING="2", CELLSPACING="1",
        #                                     style="color: white;")
        table_debosscher_count = None
        

        if pars['debosscher_classes']:
            confusion_matrix = []
            for class_name in debosscher_confusion_data['class_name_list']:
                confusion_matrix.append(debosscher_confusion_data['confusion_dict'][class_name])

            debos_count_dict = self.fill_confusion_tables(table_count=table_debosscher_count,
                                                          table_percent=table_debosscher_percent,
                                                          confusion_matrix=confusion_matrix,
                                                    class_name_list=debosscher_confusion_data['class_name_list'],
                                                          table_percent_name='Debosschr')
            debosscher_confusion_data.update(debos_count_dict)


            #diff_confusion_matrix = []
            #for i,deb_row_list in enumerate(confusion_matrix):
            #    new_row = []
            #    for j,deb_val in enumerate(deb_row_list):
            #        new_row.append(classif_summary_dict['confusion_matrix'][i][j] - deb_val)
            #    diff_confusion_matrix.append(new_row)


        blah__crossvalid_count_dict = self.fill_confusion_tables(table_count=None,
                                           table_percent=table_crossvalid,
                                           confusion_matrix=crossvalid_summary_dict['confusion_matrix'],
                                           class_name_list=crossvalid_summary_dict['confusion_matrix_index_list'],
                                                         insert_image_links=True,
                                           table_percent_name='Cross_Val')

        pairwise_count_dict = self.fill_confusion_tables(table_count=None,
                                           table_percent=table_percent,
                                           confusion_matrix=classif_summary_dict['confusion_matrix'],
                                           class_name_list=classif_summary_dict['confusion_matrix_index_list'],
                                           insert_image_links=True, table_percent_name='SelfClass')
        # # # # # # # # #
        # # # TODO: could have the other stats table as well....
        #self.fill_stats_tables(table_stats=table_stats,
        #                       classif_summary_dict=classif_summary_dict,
        #                       debosscher_confusion_data=debosscher_confusion_data)
        # # # # Just trying this out: crossvalid_summary_dict
        self.fill_stats_tables(table_stats=table_stats,
                               classif_summary_dict=crossvalid_summary_dict,
                               debosscher_confusion_data=debosscher_confusion_data)

        if pars['debosscher_classes']:
            percdiff_confusion_matrix = []
            for i,deb_row_list in enumerate(confusion_matrix):
                new_row = []
                for j,debos_count in enumerate(deb_row_list):
                    new_row.append( \
                                   (classif_summary_dict['confusion_matrix'][i][j] /
                                    float(pairwise_count_dict['class_total_counts'][i])) - 
                                   (debos_count) / float(debosscher_confusion_data['class_total_counts'][i]))
                percdiff_confusion_matrix.append(new_row)

            self.fill_difference_confusion_tables(table_count=None,
                                                  table_percent=table_diff_percent,
                                                  confusion_matrix=percdiff_confusion_matrix,
                                                  class_name_list=debosscher_confusion_data['class_name_list'],
                                                  table_percent_name='SelfDebos')


        ### Make HTML pretty, write:
        self.add_pretty_indents_to_elemtree(html, 0)
	tree = ElementTree.ElementTree(html)

        if os.path.exists(html_fpath):
            os.system('rm ' + html_fpath)
        fp = open(html_fpath, 'w')
	tree.write(fp, encoding="UTF-8")
        fp.close()


    def partition_sciclassdict_into_folds(self, n_folds=None, do_stratified=True, sciclass_dict={}, crossvalid_fold_percent=None):
        """ Divide a sciclass_dict into n_fold partitions, for use as
        crossvalidation trainingset and classification dataset.

        if n_folds is None:   then use the minimum n_sources any sci-class has. (if this is > 10, then n_folds = 10
        """
        crossval_data_dict = []
        n_sources_list = []
        for class_name, class_dict in sciclass_dict.iteritems():
            if class_dict['count'] > 0:
                n_sources_list.append(class_dict['count'])

        if n_foldsis None:
            min_n_srcs = min(n_sources_list)
            if min_n_srcs > 10:
                n_folds = 10
            else:
                n_folds = min_n_srcs

        for i_fold in range(n_folds):
            crossvalid_dict = {'train':{}, 'classify':{}}
            for class_name, class_dict in sciclass_dict.iteritems():
                crossvalid_dict['train'][class_name] =    {'count': 0, 'arffrow_with_classnames': [],
                                                           'arffrow_wo_classnames': [], 'srcid_list': []}
                crossvalid_dict['classify'][class_name] = {'count': 0, 'arffrow_with_classnames': [],
                                                           'arffrow_wo_classnames': [], 'srcid_list': []}
            crossval_data_dict.append(copy.deepcopy(crossvalid_dict))


        if do_stratified:
            for class_name, class_dict in sciclass_dict.iteritems():
                n_to_classify = class_dict['count'] / n_folds # we exclude only 1 point if n_srcs < (n_folds * 2)
                ind_list = range(len(class_dict['srcid_list']))
                random.shuffle(ind_list)
                
                for i_fold in range(n_folds):
                    sub_range = ind_list[i_fold * n_to_classify:((i_fold + 1) * n_to_classify)]
                    for i in sub_range:
                        crossval_data_dict[i_fold]['classify'][class_name]['count'] += 1
                        crossval_data_dict[i_fold]['classify'][class_name]['arffrow_with_classnames'].append( \
                                                                          class_dict['arffrow_with_classnames'][i])
                        crossval_data_dict[i_fold]['classify'][class_name]['arffrow_wo_classnames'].append( \
                                                                          class_dict['arffrow_wo_classnames'][i])
                        crossval_data_dict[i_fold]['classify'][class_name]['srcid_list'].append( \
                                                                          class_dict['srcid_list'][i])
                    train_inds = filter(lambda x: x not in sub_range, ind_list)
                    for i in train_inds:
                        crossval_data_dict[i_fold]['train'][class_name]['count'] += 1
                        crossval_data_dict[i_fold]['train'][class_name]['arffrow_with_classnames'].append( \
                                                                       class_dict['arffrow_with_classnames'][i])
                        crossval_data_dict[i_fold]['train'][class_name]['arffrow_wo_classnames'].append( \
                                                                       class_dict['arffrow_wo_classnames'][i])
                        crossval_data_dict[i_fold]['train'][class_name]['srcid_list'].append( \
                                                                       class_dict['srcid_list'][i])
                    #print class_name, 'n_src:', class_dict['count'], 'i_fold:', i_fold, 'n_to_classify:', n_to_classify, 'len/range:', 'train:', len(crossval_data_dict[class_name][i_fold]['train']['srcid_list']), 'classify:', len(crossval_data_dict[class_name][i_fold]['classify']['srcid_list'])
        else:
            # The non cross-validation using stratified folds:
            for class_name, class_dict in sciclass_dict.iteritems():
                if crossvalid_fold_percent is None:
                    n_to_classify = class_dict['count'] / n_folds # we exclude only 1 point if n_srcs < (n_folds * 2)
                else:
                    n_to_classify = int(class_dict['count'] * (crossvalid_fold_percent / 100.))
                ind_list = range(len(class_dict['srcid_list']))
                for i_fold in range(n_folds):
                    random.shuffle(ind_list)
                    sub_range = ind_list[:n_to_classify]
                    for i in sub_range:
                        crossval_data_dict[i_fold]['classify'][class_name]['count'] += 1
                        crossval_data_dict[i_fold]['classify'][class_name]['arffrow_with_classnames'].append( \
                                                                          class_dict['arffrow_with_classnames'][i])
                        crossval_data_dict[i_fold]['classify'][class_name]['arffrow_wo_classnames'].append( \
                                                                          class_dict['arffrow_wo_classnames'][i])
                        crossval_data_dict[i_fold]['classify'][class_name]['srcid_list'].append( \
                                                                          class_dict['srcid_list'][i])
                    train_inds = filter(lambda x: x not in sub_range, ind_list)
                    for i in train_inds:
                        crossval_data_dict[i_fold]['train'][class_name]['count'] += 1
                        crossval_data_dict[i_fold]['train'][class_name]['arffrow_with_classnames'].append( \
                                                                       class_dict['arffrow_with_classnames'][i])
                        crossval_data_dict[i_fold]['train'][class_name]['arffrow_wo_classnames'].append( \
                                                                       class_dict['arffrow_wo_classnames'][i])
                        crossval_data_dict[i_fold]['train'][class_name]['srcid_list'].append( \
                                                                       class_dict['srcid_list'][i])
                    #print class_name, 'n_src:', class_dict['count'], 'i_fold:', i_fold, 'n_to_classify:', n_to_classify, 'len/range:', 'train:', len(crossval_data_dict[class_name][i_fold]['train']['srcid_list']), 'classify:', len(crossval_data_dict[class_name][i_fold]['classify']['srcid_list'])
            


        return {'n_folds':n_folds,
                'crossval_data_dict':crossval_data_dict}


    def partition_sciclassdict_into_folds__old(self, n_folds=10, sciclass_dict={}):
        """ Divide a sciclass_dict into n_fold partitions, for use as
        crossvalidation trainingset and classification dataset.

        if n_folds is None:   then use the minimum n_sources any sci-class has.
        
        """
        crossval_data_dict = []
        n_sources_list = []
        for class_name, class_dict in sciclass_dict.iteritems():
            if class_dict['count'] > 0:
                n_sources_list.append(class_dict['count'])

        min_n_srcs = min(n_sources_list)
        if min_n_srcs > 10:
            n_folds = 10
        else:
            n_folds = min_n_srcs


        for i_fold in range(n_folds):
            crossvalid_dict = {'train':{}, 'classify':{}}
            for class_name, class_dict in sciclass_dict.iteritems():
                crossvalid_dict['train'][class_name] =    {'count': 0, 'arffrow_with_classnames': [],
                                                           'arffrow_wo_classnames': [], 'srcid_list': []}
                crossvalid_dict['classify'][class_name] = {'count': 0, 'arffrow_with_classnames': [],
                                                           'arffrow_wo_classnames': [], 'srcid_list': []}
            crossval_data_dict.append(copy.deepcopy(crossvalid_dict))

        for class_name, class_dict in sciclass_dict.iteritems():
            n_to_classify = class_dict['count'] / n_folds # we exclude only 1 point if n_srcs < (n_folds * 2)
            ind_list = range(len(class_dict['srcid_list']))
            random.shuffle(ind_list)
            
            for i_fold in range(n_folds):
                sub_range = ind_list[i_fold * n_to_classify:((i_fold + 1) * n_to_classify)]
                for i in sub_range:
                    crossval_data_dict[i_fold]['classify'][class_name]['count'] += 1
                    crossval_data_dict[i_fold]['classify'][class_name]['arffrow_with_classnames'].append( \
                                                                      class_dict['arffrow_with_classnames'][i])
                    crossval_data_dict[i_fold]['classify'][class_name]['arffrow_wo_classnames'].append( \
                                                                      class_dict['arffrow_wo_classnames'][i])
                    crossval_data_dict[i_fold]['classify'][class_name]['srcid_list'].append( \
                                                                      class_dict['srcid_list'][i])
                train_inds = filter(lambda x: x not in sub_range, ind_list)
                for i in train_inds:
                    crossval_data_dict[i_fold]['train'][class_name]['count'] += 1
                    crossval_data_dict[i_fold]['train'][class_name]['arffrow_with_classnames'].append( \
                                                                   class_dict['arffrow_with_classnames'][i])
                    crossval_data_dict[i_fold]['train'][class_name]['arffrow_wo_classnames'].append( \
                                                                   class_dict['arffrow_wo_classnames'][i])
                    crossval_data_dict[i_fold]['train'][class_name]['srcid_list'].append( \
                                                                   class_dict['srcid_list'][i])
                #print class_name, 'n_src:', class_dict['count'], 'i_fold:', i_fold, 'n_to_classify:', n_to_classify, 'len/range:', 'train:', len(crossval_data_dict[class_name][i_fold]['train']['srcid_list']), 'classify:', len(crossval_data_dict[class_name][i_fold]['classify']['srcid_list'])

        return {'n_folds':n_folds,
                'crossval_data_dict':crossval_data_dict}


    def generate_cross_validation_statistics(self, dotastro_classes=[], pruned_sciclass_dict={}, n_folds=None, do_stratified=True, crossvalid_fold_percent=None):
        """ Using IPython parallelization, do 10-fold cross validation by
        generating different pairiwise classifiers using training and classification subsets.

        Return dictionary of statistics which can be translated into summary HTML tables.

        """
        from IPython.kernel import client

        # TODO: Pass these to the clients:
        self.pars['taxonomy_prune_defs']['terminating_classes']

        self.mec = client.MultiEngineClient()
        #THE FOLLOWING LINE IS DANGEROUS WHEN OTHER TYPES OF TASKS MAY BE OCCURING:
        self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()
        self.tc.clear() # This supposedly clears the list of finished task objects in the task-client
        self.mec.flush() # This doesnt seem to do much in our system.
        #self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        exec_str = """import os,sys
import copy
import cPickle
os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')
os.environ['CLASSPATH']=os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar')
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
import pairwise_classification
PCVPWorker = pairwise_classification.Pairwise_Cross_Validation_Parallel_Worker(pars={})
        """
        self.mec.execute(exec_str)
	time.sleep(2) # This may be needed.

	self.task_id_list = []

        cross_valid_dataset = self.partition_sciclassdict_into_folds(n_folds=n_folds,
                                                                     do_stratified=do_stratified,
                                                                     sciclass_dict=pruned_sciclass_dict,
                                                                     crossvalid_fold_percent=crossvalid_fold_percent)
        worker_dirpath_list = []
        list_of_folded_confmatricies = []
        cumulative_class_source_counts = numpy.zeros((len(pruned_sciclass_dict)))

        for i_fold in range(cross_valid_dataset['n_folds']):
            ##### This would be done via mec()
            PCVPWorker = Pairwise_Cross_Validation_Parallel_Worker()

            ##### We would iterate over this part, for the ipython nodes:
            if len(worker_dirpath_list) == 0:
                dirpath = "%s/node_0" % (self.pars['pairwise_scratch_dirpath'])
            else:
                dirpath = "%s/node_%d" % (self.pars['pairwise_scratch_dirpath'],
                                          len(worker_dirpath_list))
            worker_dirpath_list.append(dirpath)

            node_pars = copy.deepcopy(self.pars)
            node_pars_uniq = PCVPWorker.generate_node_pars(scratch_dirpath=dirpath)
            node_pars.update(node_pars_uniq)
            PCVPWorker.pars = node_pars
            #classif_summary_dict = PCVPWorker.do_cross_validation_element(cross_valid_dataset=cross_valid_dataset, i_fold=i_fold)
            #exec_str = """PCVPWorker.pars = %s
            #exec_str = """PCVPWorker = pairwise_classification.Pairwise_Cross_Validation_Parallel_Worker(pars=%s)""" % (str(node_pars))
            # classif_summary_dict = PCVPWorker.do_cross_validation_element(cross_valid_dataset=cross_valid_dataset, i_fold=i_fold)""" % (str(node_pars))

            #if 1:
            #    # debug only
            #    PCVPWorker = Pairwise_Cross_Validation_Parallel_Worker(pars=node_pars)
            #    classif_summary_dict = PCVPWorker.do_cross_validation_element(cross_valid_dataset=cross_valid_dataset, i_fold=i_fold)
            exec_str = """PCVPWorker = pairwise_classification.Pairwise_Cross_Validation_Parallel_Worker(pars=%s)
classif_summary_dict = PCVPWorker.do_cross_validation_element(cross_valid_dataset=cross_valid_dataset, i_fold=i_fold)""" % (str(node_pars))
            taskid = self.tc.run(client.StringTask(exec_str, retries=3, 
                                                   push={'cross_valid_dataset':cross_valid_dataset,
                                                         'i_fold':i_fold},
                                                   pull='classif_summary_dict'))
            self.task_id_list.append(taskid)

	while ((self.tc.queue_status()['scheduled'] > 0) or
 	       (self.tc.queue_status()['pending'] > 0)):
            tasks_to_pop = []
	    for task_id in self.task_id_list:
	        temp = self.tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('classif_summary_dict',None)
                if results is None:
                    continue # skip these 
                if len(results) > 0:
		    tasks_to_pop.append(task_id)
                    classif_summary_dict = results
                    list_of_folded_confmatricies.append(classif_summary_dict['confusion_matrix'])

	    for task_id in tasks_to_pop:
	        self.task_id_list.remove(task_id)
            print(self.tc.queue_status())
            print('Sleep... 10  in generate_pairwise_classifications_for_perc_subset_lightcurves()')
	    time.sleep(10)

        total_confmatrix = numpy.zeros((list_of_folded_confmatricies[0].shape[0],
                                        list_of_folded_confmatricies[0].shape[0]))
        for confmatrix in list_of_folded_confmatricies:
            for i, class_row in enumerate(confmatrix):
                src_sum = sum(class_row)
                cumulative_class_source_counts[i] += src_sum
            total_confmatrix += confmatrix


        return {'confusion_matrix':total_confmatrix,
                'confusion_matrix_index_list':dotastro_classes}


    def partition_test_sciclass_dict_into_sampling_percentages(self, pruned_sciclass_dict):
        """ Given a pairwise sciclass_dict which has source_ids of the form 12345_0.4,
        Which represents a percentage or epochs which are used in that source.
        
        """
        perc_pruned_sciclass_dict = {}
        for class_name, class_dict in pruned_sciclass_dict.iteritems():
            for i, src_name in enumerate(class_dict['srcid_list']):
                srcname_list = src_name.split('_')
                src_id = srcname_list[0]
                percent = srcname_list[1]
                if percent not in perc_pruned_sciclass_dict:
                    perc_pruned_sciclass_dict[percent] = {}
                if class_name not in perc_pruned_sciclass_dict[percent]:
                    perc_pruned_sciclass_dict[percent][class_name] = {'count':0,
                                                                      'arffrow_with_classnames':[],
                                                                      'arffrow_wo_classnames':[],
                                                                      'srcid_list':[]}
                perc_pruned_sciclass_dict[percent][class_name]['count'] += 1
                perc_pruned_sciclass_dict[percent][class_name]['arffrow_with_classnames'].append( \
                                                    class_dict['arffrow_with_classnames'][i])
                perc_pruned_sciclass_dict[percent][class_name]['arffrow_wo_classnames'].append( \
                                                    class_dict['arffrow_wo_classnames'][i])
                perc_pruned_sciclass_dict[percent][class_name]['srcid_list'].append(src_name)
        return perc_pruned_sciclass_dict


    def tally_correctly_classified_for_percent(self, percent, set_num, pw_classifier_name, classif_summary_dict, percent_tally_summary_dict, classifier_confidence_analysis_dict={}):
        """
        This fills a dictionary which will be used to generate an analysis plot:
        
            percent_tally_summary_dict[class_name]{'error':[F/total errors array],
                                                   'percent':[percent LC array]}
        """
        if percent not in classifier_confidence_analysis_dict:
            classifier_confidence_analysis_dict[percent] = {}

        classifier_confidence_analysis_dict[percent][set_num] = {\
                         'confids':copy.deepcopy(classif_summary_dict['srcid_classif_summary']['confids']),
                         'confusion_matrix':copy.deepcopy(classif_summary_dict['confusion_matrix']),
                         'confusion_matrix_index_class_dict':copy.deepcopy(classif_summary_dict['confusion_matrix_index_class_dict']),
                         'confusion_matrix_index_list':copy.deepcopy(classif_summary_dict['confusion_matrix_index_list'])}
        
        index = None   # Kind of KLUDGEY way to do this
        
        #for class_name, class_dict in classif_summary_dict:
        for i, confusion_row in enumerate(classif_summary_dict['confusion_matrix']):
            class_name = classif_summary_dict['confusion_matrix_index_list'][i]
            if class_name not in percent_tally_summary_dict:
                percent_tally_summary_dict[class_name] = {}
            if pw_classifier_name not in percent_tally_summary_dict[class_name]:
                percent_tally_summary_dict[class_name][pw_classifier_name] = {}
                for j_set in xrange(self.pars['num_percent_epoch_error_iterations']):
                    percent_tally_summary_dict[class_name][pw_classifier_name][j_set] = {\
                                                                     'percent_false_list':[],
                                                                     'sampling_percent_list':[],
                                                                     'count_total':[],
                                                                     'count_true':[]}
            # here we can assume this exists: 
            #     percent_tally_summary_dict[class_name][set_num]['sampling_percent_list']
            
            # # Maybe we can do the following on a higher function level
            #   - need to do the following on after all proccess have completed

            count_total = sum(confusion_row)

            # # # # debug only:
            if (class_name == 'mira') or (class_name == 'rr-c'):
                print(percent, set_num, pw_classifier_name, class_name, 'count_total:', count_total, 'pairwise:L1561')
                #import pdb; pdb.set_trace()
            # # # # 

            if count_total > 0:
                ### Only do this if there are sources for this science_class
                samp_perc_list = percent_tally_summary_dict[class_name][pw_classifier_name][set_num]['sampling_percent_list']
                ### This 'index' is the ordering-index of the sampling_percent, which can be determined with any of the science-classes
                if index is None:
                    ### Determine which index to place values, depending upon sampling-percent value:
                    if len(samp_perc_list) == 0:
                        index = 0
                    else:
                        for j in range(len(samp_perc_list)):
                            if (float(samp_perc_list[j]) >= float(percent)):
                                index = j
                                break
                        if index is None:
                            index = len(samp_perc_list) # percent is > all perc in samp_perc_list
                count_true = confusion_row[i]
                percent_false = (count_total - count_true) / float(count_total)

                # # # # # #
                # TODO: want to take one set of sources for percent & class, get the percent_false
                #        - then do the same for the next complete set of sources

                #if index is None:
                #    import pdb; pdb.set_trace()
                percent_tally_summary_dict[class_name][pw_classifier_name][set_num]['percent_false_list'].insert(index, percent_false)
                percent_tally_summary_dict[class_name][pw_classifier_name][set_num]['sampling_percent_list'].insert(index, percent)
                percent_tally_summary_dict[class_name][pw_classifier_name][set_num]['count_total'].insert(index, count_total)
                percent_tally_summary_dict[class_name][pw_classifier_name][set_num]['count_true'].insert(index, count_true)
            


    # OBSOLETE:
    def tally_correctly_classified_for_percent__old(self, percent, set_num, classif_summary_dict, percent_tally_summary_dict):
        """
        This fills a dictionary which will be used to generate an analysis plot:
        
            percent_tally_summary_dict[class_name]{'error':[F/total errors array],
                                                   'percent':[percent LC array]}
        """
        index = None   # Kind of KLUDGEY way to do this
        
        #for class_name, class_dict in classif_summary_dict:
        for i, confusion_row in enumerate(classif_summary_dict['confusion_matrix']):
            class_name = classif_summary_dict['confusion_matrix_index_list'][i]
            if class_name not in percent_tally_summary_dict:
                percent_tally_summary_dict[class_name] = {}
                for set_num in xrange(self.pars['num_percent_epoch_error_iterations']):
                    percent_tally_summary_dict[class_name][set_num] = {'percent_false_list':[],
                                                                       'sampling_percent_list':[]}
            count_total = sum(confusion_row)
            if count_total > 0:
                samp_perc_list = percent_tally_summary_dict[class_name][set_num]['sampling_percent_list']
                if index is None:
                    ### Determine which index to place values, depending upon percent value:
                    if len(samp_perc_list) == 0:
                        index = 0
                    else:
                        for j in range(len(samp_perc_list)):
                            if (float(samp_perc_list[j]) >= float(percent)):
                                index = j
                                break
                        if index is None:
                            index = len(samp_perc_list) # percent is > all perc in samp_perc_list
                count_true = confusion_row[i]
                percent_false = (count_total - count_true) / float(count_total)

                # # # # # #
                # TODO: want to take one set of sources for percent & class, get the percent_false
                #        - then do the same for the next complete set of sources

                #if index is None:
                #    import pdb; pdb.set_trace()
                percent_tally_summary_dict[class_name][set_num]['percent_false_list'].insert(index, percent_false)
                percent_tally_summary_dict[class_name][set_num]['sampling_percent_list'].insert(index, percent)



    def plot_percent_tally_summary_dict(self, percent_tally_summary_dict,
                                        img_fpath='/home/pteluser/scratch/xmls_deboss_percentage_exclude.ps'):
        """ Generate a plot of: percent_false_classifications vs percent epochs used in sources,
               for each science class
        """
        matplotlib.rcParams['axes.unicode_minus'] = False
        matplotlib.rcParams['legend.fontsize'] = 7
        fig = plt.figure(figsize=(10,6), dpi=100)
        ax = fig.add_subplot(1, 1, 1)

        #class_name_list = percent_tally_summary_dict.keys()
        class_name_list = self.pars['taxonomy_prune_defs']['terminating_classes']
        allclass_percent_count_total_dict = {}
        allclass_percent_count_true_dict = {}
        #allclass_percent_false_dict = {}

        sampling_percent_list = []
        for str_perc in self.pars['percent']:
            sampling_percent_list.append(float(str_perc))

        sampling_percent_array = numpy.array(sampling_percent_list)

        for i, class_name in enumerate(class_name_list):
            # for each percent, want to get all (3) percent_false
            #   - then I can later avg & std these
            
            ### (I think this logic is needed):
            #sampling_percent_list = []
            a_match = False
            for a_dict in percent_tally_summary_dict[class_name].values():
                if len(a_dict[0]['percent_false_list']) > 0:
                    a_match = True
                    #for samp_perc_str in a_dict[0]['sampling_percent_list']:
                    #    sampling_percent_list.append(float(samp_perc_str))
                    break
            if a_match == False:
                continue # There is no data for this science_class(assumed for all sets), so we don't attempt to plot it.
            #sampling_percent_list = []
            #for samp_perc_str in percent_tally_summary_dict[class_name].values()[0][0]['sampling_percent_list']:
            #    sampling_percent_list.append(float(samp_perc_str))


            percent_false_dict = {}
            #for set_num, set_dict in enumerate(percent_tally_summary_dict[class_name]):
            for pw_classifier_name, pw_dict in percent_tally_summary_dict[class_name].iteritems():
                for set_num, set_dict in pw_dict.iteritems():
                    if len(set_dict['percent_false_list']) == 0:
                        continue # skip this set
                        #pre20101015: raise "?Mybe forgot to ensure pars['num_percent_epoch_error_iterations'] is the same in pairwise_classification.py and analysis_deboss_tcp_source_compare.py?" # shouldnt get here due to no-data condition/continue above.
                    for j, elem in enumerate(set_dict['sampling_percent_list']):
                        samp_perc = float(elem)
                        if samp_perc not in percent_false_dict:
                            percent_false_dict[samp_perc] = []
                        #if set_dict['percent_false_list'][j] > 0.:
                        #    print 'yo!'
                        # # # # This next line doesn't make sense?:
                        percent_false_dict[samp_perc].append(set_dict['percent_false_list'][j])
                        if samp_perc not in allclass_percent_count_total_dict:
                            allclass_percent_count_total_dict[samp_perc] = {}
                            allclass_percent_count_true_dict[samp_perc] = {}
                        if pw_classifier_name not in allclass_percent_count_total_dict[samp_perc]:
                            allclass_percent_count_total_dict[samp_perc][pw_classifier_name] = {}
                            allclass_percent_count_true_dict[samp_perc][pw_classifier_name] = {}
                        if set_num not in allclass_percent_count_total_dict[samp_perc][pw_classifier_name]:
                            allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num] = 0
                            allclass_percent_count_true_dict[samp_perc][pw_classifier_name][set_num] = 0
                        allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num] += set_dict['count_total'][j]
                        allclass_percent_count_true_dict[samp_perc][pw_classifier_name][set_num] += set_dict['count_true'][j]
                        #20110106#print '!!!', 'j:', j, 'samp_perc:', samp_perc, 'pw_classifier_name:', pw_classifier_name, 'set_num:', set_num, 'count_total:', allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num], 'count_true:', allclass_percent_count_true_dict[samp_perc][pw_classifier_name][set_num], class_name#, "set_dict['sampling_percent_list']:", set_dict['sampling_percent_list']

                
                        #allclass_percent_count_total_dict[samp_perc].append(set_dict['count_total'][j])
                        #allclass_percent_count_true_dict[samp_perc].append(set_dict['count_true'][j])

                        ######allclass_percent_false_dict[samp_perc].append((set_dict['count_total'][j] - set_dict['count_true'][j]) / float(set_dict['count_total'][j]))

            #sampling_percent_array = numpy.array(sampling_percent_list)

            #print class_name, percent_false_dict


            # # # # # # # # # 
            # ??? is the following needed anymore? :
            # # # # # # # # # 
            sort_tups = []
            for samp_perc in sampling_percent_list:
                if samp_perc in percent_false_dict:
                    per_false_list = percent_false_dict[samp_perc]
                    #20110106#print ">>> %s samp_perc=%f len(per_false_list)=%d" % (class_name, samp_perc, len(per_false_list))
                    sort_tups.append((samp_perc, numpy.average(per_false_list), numpy.std(per_false_list)))
                #else:
                #    print percent_tally_summary_dict[class_name]['rf_7'][0]['sampling_percent_list']
                #    print "@@@ %s samp_perc=%f percent_false_dict.keys():%s" % (class_name, samp_perc, str(percent_false_dict.keys()))
                #    print '   rf_0', percent_tally_summary_dict[class_name]['rf_0'][0]['sampling_percent_list']
                #    print '   rf_1', percent_tally_summary_dict[class_name]['rf_1'][0]['sampling_percent_list']
                #    print '   rf_2', percent_tally_summary_dict[class_name]['rf_2'][0]['sampling_percent_list']
                #    print '   rf_3', percent_tally_summary_dict[class_name]['rf_3'][0]['sampling_percent_list']
                #    print '   rf_4', percent_tally_summary_dict[class_name]['rf_4'][0]['sampling_percent_list']
                #    print '   rf_5', percent_tally_summary_dict[class_name]['rf_5'][0]['sampling_percent_list']
                #    print '   rf_6', percent_tally_summary_dict[class_name]['rf_6'][0]['sampling_percent_list']
                #    print '   rf_7', percent_tally_summary_dict[class_name]['rf_7'][0]['sampling_percent_list']
                #    print '   rf_8', percent_tally_summary_dict[class_name]['rf_8'][0]['sampling_percent_list']
                #    print '   rf_9', percent_tally_summary_dict[class_name]['rf_9'][0]['sampling_percent_list']
                #    ###sort_tups.append((samp_perc, 1.0, 0.0))



            #import pdb; pdb.set_trace()
            sort_tups.sort()

            perc_list = []
            avg_perfalse_list = []
            std_perfalse_list = []
            for (samp_perc, avg, std) in sort_tups:
                perc_list.append(samp_perc)
                avg_perfalse_list.append(avg)
                std_perfalse_list.append(std)
            ###
            #avg_perfalse_list = []
            #std_perfalse_list = []
            #for samp_perc in sampling_percent_list:
            #    per_false_list = percent_false_dict[samp_perc]
            #    avg_perfalse_list.append(numpy.average(per_false_list))
            #    std_perfalse_list.append(numpy.std(per_false_list))
            ###


            color_list = [self.pars['feat_distrib_colors'][i+1]] * len(set_dict['percent_false_list'])
            #ax.plot(sampling_percent_array, avg_perfalse_list, c=self.pars['feat_distrib_colors'][i+1],
            ax.plot(perc_list, avg_perfalse_list, c=self.pars['feat_distrib_colors'][i+1],
                    label=class_name, linewidth=3,
                    marker=self.pars['plot_symb'][i % len(self.pars['plot_symb'])], markersize=4)

            # # # #Used this prior to 20101109:
            #ax.errorbar(sampling_percent_array, avg_perfalse_list, yerr=std_perfalse_list,
            #            c=self.pars['feat_distrib_colors'][i+1], label=class_name, linewidth=3,
            #            elinewidth=1,
            #            marker=self.pars['plot_symb'][i % len(self.pars['plot_symb'])], markersize=4)

        #sampling_percent_list = allclass_percent_count_total_dict.keys()
        #sampling_percent_list.sort()

        avg_all_perc_false_list = []
        std_all_perc_false_list = []
        for samp_perc in sampling_percent_list:
            perc_false_list = []
            # # # TODO: need to actually iterate over classifier and append these to the list
            #     - but, this requires allclass_percent_count_total_dict to have classifier
            for pw_classifier_name in allclass_percent_count_total_dict[samp_perc].keys():
                for set_num in allclass_percent_count_total_dict[samp_perc][pw_classifier_name].keys():
                    if float(allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num]) == 0:
                        percent_false = 0 # 20101224 added 
                    else:
                        percent_false = (allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num] - allclass_percent_count_true_dict[samp_perc][pw_classifier_name][set_num]) / float(allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num])
                    #if percent_false != 0:
                    #    import pdb; pdb.set_trace()
                    print('>>> set:', set_num, 'perc:', samp_perc, pw_classifier_name, \
                        'all:', allclass_percent_count_total_dict[samp_perc][pw_classifier_name][set_num], \
                        'true:', allclass_percent_count_true_dict[samp_perc][pw_classifier_name][set_num], \
                        'F%:', percent_false)
                    #if percent_false != 0:
                    #    import pdb; pdb.set_trace()
                    perc_false_list.append(percent_false)
                    #print "perc=%f set=%d total=%d true=%d perc_false=%lf" % (samp_perc, set_num, allclass_percent_count_total_dict[samp_perc][set_num], allclass_percent_count_true_dict[samp_perc][set_num], percent_false)
            avg_all_perc_false_list.append(numpy.average(perc_false_list))
            std_all_perc_false_list.append(numpy.std(perc_false_list))
            #print "perc=%f avg_perc_false=%f std_perc_false=%f" % (samp_perc, numpy.average(perc_false_list), numpy.std(perc_false_list))

        #ax.plot(sampling_percent_array, total_perc_false_list, c='#000000',
        #        label='(ALL)', linewidth=5,
        #        marker='o', markersize=4)

        ax.errorbar(sampling_percent_list, avg_all_perc_false_list, yerr=std_all_perc_false_list,
                    c='#000000', label='(ALL)', linewidth=3,
                    elinewidth=1, marker='o', markersize=4)
        
        # TITLE: missing points for a (class,percent) mean no predictions were made for that class

        ax.set_xlim(.1, 1.01)
        ax.set_ylim(-0.01, 1.01)
        ax.set_xticks(numpy.arange(0.1, 1.1, 0.1))
        ax.set_yticks(numpy.arange(0,   1.1, 0.1))
        ax.set_xlabel("Percent of epochs used (missing points mean no predictions made for class,percent)")
        ax.set_ylabel("Percent of False classifications")
        ax.legend(loc=3, ncol=2, columnspacing=1)
        
        plt.savefig(img_fpath)


    def form_debosscher_classes_name(self, debosscher_confusion_data={}):
        """ Form a string which characterizes the sciences classes contained in the
        given debosscher confusion data
        """
        class_list = copy.deepcopy(debosscher_confusion_data['class_name_list'])
        class_list.sort()
        name_str = ""
        for class_name in class_list:
            name_str += class_name[0]
        return name_str


    def debosscher_main(self):
        """
        For generating pairwise & classifying using Debosscher data and science-class sets.
        Adapted from Weka_Pairwise_Classification.main()

        """
        debosscher_confusion_data = self.parse_debosscher_confusion_table( \
                                           self.pars['debosscher_confusion_table3_fpath'])

        dotastro_classes = []
        for deboss_class in debosscher_confusion_data['class_name_list']:
            dotastro_classes.append(self.pars['debosscher_class_lookup'][deboss_class])

        self.pars['taxonomy_prune_defs']['terminating_classes'] = dotastro_classes


        #deboss_classes_name = self.form_debosscher_classes_name(\
        #                                  debosscher_confusion_data=debosscher_confusion_data)
        deboss_classes_name = self.pars['debosscher_confusion_table3_fpath'][ \
                                           self.pars['debosscher_confusion_table3_fpath'].rfind('/')+1:
                                           self.pars['debosscher_confusion_table3_fpath'].rfind('.')]
        
        self.pars['trainset_pruned_pklgz_fpath'] = "%s/pairwise_trainset__%s.pkl.gz" % ( \
                                                   self.pars['cyto_work_final_fpath'], deboss_classes_name)
        self.pars['weka_pairwise_classifiers_pkl_fpath'] = "%s/pairwise_classifier__%s.pkl.gz" % ( \
                                                   self.pars['cyto_work_final_fpath'], deboss_classes_name)

        # TODO: if we want to parallelize the classifications (for each debosscher table),
        #       we need to make self.pars['pairwise_trainingset_dirpath'] unique for each deb table

        if not os.path.exists(self.pars['trainset_pruned_pklgz_fpath']):

            #self.pars['trainset_pruned_pklgz_fpath'] = pkl_fpath
            PairwiseClassification = Pairwise_Classification(self.pars)
            ### This gets the classifier (pairwise_dict):
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            pairwise_pruned_dict = a_dict['pruned_sciclass_dict']
            pairwise_dict = a_dict['pairwise_dict']

            #self.pars['weka_pairwise_classifiers_pkl_fpath'] = 
            PairwiseClassification.generate_weka_classifiers(pairwise_dict=pairwise_dict,
                                                        arff_has_ids=arff_has_ids,
                                                        arff_has_classes=arff_has_classes)            
        else:
            fp=open(self.pars['weka_pairwise_classifiers_pkl_fpath'],'rb')
            ### This gets the classifier (pairwise_dict):
            pairwise_dict=cPickle.load(fp)
            fp.close()

            fp=gzip.open(self.pars['trainset_pruned_pklgz_fpath'],'rb')
            pairwise_pruned_dict=cPickle.load(fp)
            fp.close()

        if not os.path.exists(self.pars['crossvalid_pklgz_fpath']):
            crossvalid_summary_dict = self.generate_cross_validation_statistics( 
                                           dotastro_classes=dotastro_classes, 
                                           pruned_sciclass_dict=pairwise_pruned_dict,
                                           n_folds=self.pars['crossvalid_nfolds'],
                                           crossvalid_fold_percent=self.pars['crossvalid_fold_percent'],
                                           do_stratified=self.pars['crossvalid_do_stratified'])
            fp = gzip.open(self.pars['crossvalid_pklgz_fpath'],'wb')
            cPickle.dump(crossvalid_summary_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp = gzip.open(self.pars['crossvalid_pklgz_fpath'],'rb')
            crossvalid_summary_dict = cPickle.load(fp)
            fp.close()


        self.load_weka_classifiers(classifier_dict=pairwise_dict)
        
        # TODO: it might be nice to be able to generate this pairwise_pruned dict for any
        #     .arff dict so that we can generate classifications and a confusion matrix
        #       for any given .arff file.
        #  - this wouldnt help with any class pruning, since that requires the classifier
        #      to also be trained on similar pruned classes.

        # TODO: maybe have the pairwise_pruned dict be some sort of 90% dataset, for cross validation

        self.initialize_temp_cyto_files()
        if not os.path.exists(self.pars['classification_summary_pklgz_fpath']):
            classif_summary_dict = self.do_pairwise_classification(classifier_dict=pairwise_dict,
                                                               pairwise_pruned_dict=pairwise_pruned_dict)
            fp = gzip.open(self.pars['classification_summary_pklgz_fpath'],'wb')
            cPickle.dump(classif_summary_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp = gzip.open(self.pars['classification_summary_pklgz_fpath'],'rb')
            classif_summary_dict = cPickle.load(fp)
            fp.close()
            

        self.copy_cyto_file_to_final_path()
        self.write_confusionmatrix_heatmap_html(classif_summary_dict,
                                                html_fpath=self.pars['confusion_stats_html_fpath'],
                                                debosscher_confusion_data=debosscher_confusion_data,
                                                crossvalid_summary_dict=crossvalid_summary_dict)

        if self.pars['feat_dist_plots']:
            FDPlots = Feature_Distribution_Plots(self.pars)
            ##### NOTE: it seems this threaded bit doesnt seem to handle plotting well, gives error: Gtk-CRITICAL **: gtk_settings_get_for_screen: assertion `GDK_IS_SCREEN (screen)' failed
            #####     - probably ipthon would work rather than threading
            #FDPlots.threaded_gen_dist_plots_for_all_classes(pairwise_pruned_dict=pairwise_pruned_dict,
            #                                                classif_summary_dict=classif_summary_dict)
            #"""
            local_img_fpath_list = []
            featvals_dict = FDPlots.get_featvals_for_srcids(classif_summary_dict)

            for class_name in classif_summary_dict['confusion_matrix_index_list']:

                img_fpath = "%s/confused_%s.png" % (self.pars['feat_dist_image_local_dirpath'], class_name)

                FDPlots.generate_feature_distribution_plots(pairwise_pruned_dict=pairwise_pruned_dict,
                                                            classif_summary_dict=classif_summary_dict,
                                                            featvals_dict=featvals_dict,
                                                            img_fpath=img_fpath,
                                                            target_class_name=class_name)
                local_img_fpath_list.append(img_fpath)
            time.sleep(1) # just ensure the files are written before scp'ing
            scp_str = "scp -C %s/* %s" % (self.pars['feat_dist_image_local_dirpath'],
                                       self.pars['feat_dist_image_remote_scp_str'])
            os.system(scp_str)
            #"""


    def ipython_client__deboss_percentage_exclude_analysis(self, set_num, percent, pairwise_dict, pruned_sciclass_dict):
        """
        To be invoked on an IPython client, by function:
            ipython_master__deboss_percentage_exclude_analysis()

        """
        classif_summary_dict = self.do_pairwise_classification(classifier_dict=pairwise_dict,
                                                               pairwise_pruned_dict=pruned_sciclass_dict,
                                                               set_num=set_num)

        return {'classif_summary_dict':classif_summary_dict,
                'percent':percent,
                'set_num':set_num}



    def ipython_master__deboss_percentage_exclude_analysis(self):
        """
        NOTE: This is adapted from Weka_Pairwise_Classification.main()

        NOTE: some of the IPython control is adapted from analysis_deboss_tcp_source_compare.py
               generate_pairwise_classifications_for_perc_subset_lightcurves()
        """
        classifier_confidence_analysis_dict = {}

        debosscher_confusion_data = self.parse_debosscher_confusion_table( \
                                           self.pars['debosscher_confusion_table3_fpath'])
        dotastro_classes = []
        for deboss_class in debosscher_confusion_data['class_name_list']:
            dotastro_classes.append(self.pars['debosscher_class_lookup'][deboss_class])
        self.pars['taxonomy_prune_defs']['terminating_classes'] = dotastro_classes

        ########## NOTE: the Ipython clients also do this via .mec() above:
        fp=open('/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz','rb')
        pairwise_dict=cPickle.load(fp)
        fp.close()
        ### Load JPype weka classifiers using .model info:
        self.load_weka_classifiers(classifier_dict=pairwise_dict)
        ##########

        # TODO: it might be nice to be able to generate this pairwise_pruned dict for any
        #     .arff dict so that we can generate classifications and a confusion matrix
        #       for any given .arff file.
        #  - this wouldnt help with any class pruning, since that requires the classifier
        #      to also be trained on similar pruned classes.

        if not os.path.exists(self.pars['trainset_pruned_pklgz_fpath']):
            PairwiseClassification = Pairwise_Classification(self.pars)
            # NOTE: The following function does write the pkl to disk
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            #pairwise_dict = a_dict['pairwise_dict']
            
        else:
            fp=gzip.open(self.pars['trainset_pruned_pklgz_fpath'],'rb')
            #pairwise_pruned_dict=cPickle.load(fp)
            pruned_sciclass_dict=cPickle.load(fp)
            fp.close()


        self.initialize_temp_cyto_files()

        #pprint.pprint(percent_tally_summary_dict)
        pklgz_fpath = '/home/pteluser/scratch/xmls_deboss_percentage_exclude__classified.pkl.gz'
        if not os.path.exists(pklgz_fpath):


            ####################

            try:
                from IPython.kernel import client
            except:
                pass

            self.mec = client.MultiEngineClient()
            # 20100821: dstarr tried re-enabling the mex.reset(), but it didnt help
            #self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
            self.tc = client.TaskClient()
            self.task_id_list = []

            pairwise_dict_classifier_fpath = '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz'
            pairwise_classifier_tarball_fpath = '/home/pteluser/scratch/pairwise_trainingsets.tar.gz'
            if os.path.exists(pairwise_classifier_tarball_fpath):
                os.system("rm %s" % (pairwise_classifier_tarball_fpath))
            os.system("tar -C /home/pteluser/scratch/ -czf %s pairwise_trainingsets" % (pairwise_classifier_tarball_fpath))

            node_local_pairwise_dict_fpath = pairwise_dict_classifier_fpath[pairwise_dict_classifier_fpath.rfind('/')+1:]

            pars_str = str(self.pars)#pprint.pformat(self.pars)

            #KLUDGE: I will do the scp to tranx and all nodes, for convenience:
            mec_exec_str = """
import sys, os
import cPickle
import time
sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/ingest_tools'))
import pairwise_classification
pid = str(os.getpid())
os.system('echo "' + pid + '" > /tmp/pairwise_pid.pid')
time.sleep(2)
pid_read = open('/tmp/pairwise_pid.pid').read().strip()
if pid == pid_read:
    os.system(os.path.expandvars("scp -c blowfish pteluser@192.168.1.25:%s $HOME/scratch/"))
    os.system(os.path.expandvars("scp -c blowfish pteluser@192.168.1.25:%s $HOME/scratch/"))
    os.system(os.path.expandvars("tar -C $HOME/scratch -xzf %s"))

WekaPairwiseClassification = pairwise_classification.Weka_Pairwise_Classification(pars=%s)
fp=open(os.path.expandvars('$HOME/scratch/%s'),'rb')
pairwise_dict=cPickle.load(fp)
fp.close()
WekaPairwiseClassification.load_weka_classifiers(classifier_dict=pairwise_dict)
WekaPairwiseClassification.initialize_temp_cyto_files()
""" % (pairwise_classifier_tarball_fpath, pairwise_dict_classifier_fpath,
       pairwise_classifier_tarball_fpath,
       pars_str,
       pairwise_dict_classifier_fpath[pairwise_dict_classifier_fpath.rfind('/')+1:])
            #WekaPairwiseClassification.initialize_temp_cyto_files() ### ??? Not sure if this is needed in Ipython clients:
            
            self.mec.execute(mec_exec_str)
            time.sleep(2) # This may be needed.

            ####################


            perc_pruned_sciclass_dict = self.partition_test_sciclass_dict_into_sampling_percentages( \
                                                                               pruned_sciclass_dict)
            percent_list = perc_pruned_sciclass_dict.keys()
            #percent_list.sort()
            percent_list.sort(reverse=True)
            for percent in percent_list:
                pruned_sciclass_dict = perc_pruned_sciclass_dict[percent]
                print('Percent:', percent)

                if 0:
                    from . import pairwise_classification
                    WekaPairwiseClassification = pairwise_classification.Weka_Pairwise_Classification(pars={'pruned_classif_summary_stats_pkl_fpath': '/home/pteluser/scratch/pruned_classif_summary_stats.pkl', 'feat_dist_plots': False, 'pairwise_classifier_pklgz_dirpath': '/home/pteluser/scratch/pairwise_classifiers', 'taxonomy_prune_defs': {'terminating_classes': ['mira', 'sreg', 'rv', 'dc', 'piic', 'cm', 'rr-ab', 'rr-c', 'rr-d', 'ds', 'lboo', 'bc', 'spb', 'gd', 'be', 'pvsg', 'CP', 'wr', 'tt', 'haebe', 'sdorad', 'ell', 'alg', 'bly', 'wu']}, 'number_threads': 13, 'feat_dist_image_remote_scp_str': 'pteluser@lyra.berkeley.edu:www/dstarr/pairwise_images/', 'pairwise_schema_name': 'noprune', 'debosscher_classes': False, 'arff_has_ids': False, 'classification_summary_pklgz_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result_classification_summary.pkl.gz', 'feat_distrib_classes': {'target_class': 'lboo', 'comparison_classes': ['pvsg', 'gd', 'ds']}, 'tcp_port': 3306, 'pairwise_classifier_dirpath': '/home/pteluser/scratch/pairwise_classifiers', 'min_num_sources_for_pairwise_class_inclusion': 6, 'arff_has_classes': True, 'num_percent_epoch_error_iterations': 1, 'debosscher_confusion_table3_fpath': '/home/pteluser/src/TCP/Data/debosscher_table3.html', 'cyto_work_final_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher', 'cyto_network_fname': 'pairwise_class.cyto.network', 'pairwise_trainingset_dirpath': '/home/pteluser/scratch/pairwise_trainingsets', 'tcp_database': 'source_test_db', 'dotastro_arff_fpath': '/home/pteluser/scratch/xmls_deboss_percentage_exclude.arff', 'arff_sciclass_dict_pkl_fpath': '/home/pteluser/scratch/arff_sciclass_dict.pkl', 'trainset_pruned_pklgz_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result.pkl.gz', 'feat_dist_image_rooturl': 'http://lyra.berkeley.edu/~jbloom/dstarr/pairwise_images', 'tcp_username': 'pteluser', 'crossvalid_pklgz_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result__crossvalid_data.pkl.gz', 'tcp_hostname': '192.168.1.25', 'confusion_stats_html_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/xmls_deboss_percentage_exclude__pairwise_result_classif_stats.html', 'debosscher_class_lookup': {'BE': 'be', 'RRAB': 'rr-ab', 'MIRA': 'mira', 'WR': 'wr', 'SDBV': 'sdbv', 'FUORI': 'fuor', 'RVTAU': 'rv', 'DMCEP': 'cm', 'GDOR': 'gd', 'LBV': 'sdorad', 'ROAP': 'rot', 'RRD': 'rr-d', 'RRC': 'rr-c', 'DAV': 'pwd', 'SXPHE': 'sx', 'HAEBE': 'haebe', 'SPB': 'spb', 'LBOO': 'lboo', 'ELL': 'ell', 'XB': 'xrbin', 'BCEP': 'bc', 'EA': 'alg', 'PTCEP': 'piic', 'SLR': 'NOTMATCHED', 'EB': 'bly', 'EW': 'wu', 'CP': 'CP', 'CV': 'cv', 'PVSG': 'pvsg', 'TTAU': 'tt', 'DSCUT': 'ds', 'CLCEP': 'dc', 'SR': 'sreg', 'GWVIR': 'gw', 'DBV': 'pwd'}, 'debosscher_confusion_table4_fpath': '/home/pteluser/src/TCP/Data/debosscher_table4.html', 'pairwise_scratch_dirpath': '/media/raid_0/pairwise_scratch', 'feat_dist_image_local_dirpath': '/media/raid_0/pairwise_scratch/pairwise_scp_data', 'feat_distrib_colors': ['#000000', '#ff3366', '#660000', '#aa0000', '#ff0000', '#ff6600', '#996600', '#cc9900', '#ffff00', '#ffcc33', '#ffff99', '#99ff99', '#666600', '#99cc00', '#00cc00', '#006600', '#339966', '#33ff99', '#006666', '#66ffff', '#0066ff', '#0000cc', '#660099', '#993366', '#ff99ff', '#440044'], 't_sleep': 0.20000000000000001, 'cyto_nodeattrib_fname': 'pairwise_class.cyto.nodeattrib', 'plot_symb': ['o', 's', 'v', 'd', '<'], 'weka_pairwise_classifiers_pkl_fpath': '/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/weka_pairwise_classifier.pkl'})
                    fp=open("/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz",'rb')
                    pairwise_dict=cPickle.load(fp)
                    fp.close()
                    WekaPairwiseClassification.load_weka_classifiers(classifier_dict=pairwise_dict)
                    WekaPairwiseClassification.initialize_temp_cyto_files()
                    for set_num in xrange(self.pars['num_percent_epoch_error_iterations']):
                        out_dict = WekaPairwiseClassification.ipython_client__deboss_percentage_exclude_analysis(set_num, percent, pairwise_dict, pruned_sciclass_dict)
                    #import pdb; pdb.set_trace()

                for set_num in xrange(self.pars['num_percent_epoch_error_iterations']):
                    tc_exec_str = "out_dict = WekaPairwiseClassification.ipython_client__deboss_percentage_exclude_analysis(set_num, percent, pairwise_dict, pruned_sciclass_dict)"
                    taskid = self.tc.run(client.StringTask(tc_exec_str, pull='out_dict', retries=3,
                                                       push={'set_num':set_num,
                                                             'percent':percent,
                                                             'pairwise_dict':pairwise_dict,
                                                             'pruned_sciclass_dict':pruned_sciclass_dict}))
                    self.task_id_list.append(taskid)

            percent_tally_summary_dict = {}
	    while ((self.tc.queue_status()['scheduled'] > 0) or
 	           (self.tc.queue_status()['pending'] > 0)):
                tasks_to_pop = []
	        for task_id in self.task_id_list:
	            temp = self.tc.get_task_result(task_id, block=False)
                    if temp is None:
                        continue
                    temp2 = temp.results
                    if temp2 is None:
                        continue
                    results = temp2.get('out_dict',None)
                    if results is None:
                        continue # skip these sources (I think generally UNKNOWN ... science classes)
                    out_dict = results
                    if len(out_dict) > 0:
                        tasks_to_pop.append(task_id)
                        ##### Do the tally stuff:
                        self.tally_correctly_classified_for_percent(out_dict['percent'],
                                                                    out_dict['set_num'],
                                                                    out_dict['classif_summary_dict'],
                                                                    percent_tally_summary_dict,
                                                                    classifier_confidence_analysis_dict=classifier_confidence_analysis_dict)
	        for task_id in tasks_to_pop:
	            self.task_id_list.remove(task_id)
                print(self.tc.queue_status())
                print('Sleep... 10  in ipython_master__deboss_percentage_exclude_analysis()')
	        time.sleep(10)
                print('yoyoyo')
            # IN CASE THERE are still tasks which have not been pulled/retrieved:
            for task_id in self.task_id_list:
	        temp = self.tc.get_task_result(task_id, block=False)
                if temp is None:
                    continue
                temp2 = temp.results
                if temp2 is None:
                    continue
                results = temp2.get('out_dict',None)
                if results is None:
                    continue # skip these sources (I think generally UNKNOWN ... science classes)
                out_dict = results
                if len(out_dict) > 0:
                    tasks_to_pop.append(task_id)
                    ##### Do the tally stuff:
                    self.tally_correctly_classified_for_percent(out_dict['percent'],
                                                                out_dict['set_num'],
                                                                out_dict['classif_summary_dict'],
                                                                percent_tally_summary_dict,
                                                                classifier_confidence_analysis_dict=classifier_confidence_analysis_dict)
            fp = gzip.open(pklgz_fpath,'wb')
            cPickle.dump(percent_tally_summary_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp=gzip.open(pklgz_fpath,'rb')
            percent_tally_summary_dict=cPickle.load(fp)
            fp.close()

        classifier_confidence_analysis_fpath = '/home/pteluser/scratch/classifier_confidence_analysis.pkl.gz'
        if os.path.exists(classifier_confidence_analysis_fpath):
            os.system('rm ' + classifier_confidence_analysis_fpath)
        fp = gzip.open(classifier_confidence_analysis_fpath,'wb')
        cPickle.dump(classifier_confidence_analysis_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()

        #import pdb; pdb.set_trace()
        self.plot_percent_tally_summary_dict(percent_tally_summary_dict)


    ##### To be obsolete once IPython code above works:
    def main_deboss_percentage_exclude_analysis(self):
        """
        NOTE: This is adapted from Weka_Pairwise_Classification.main()

        """

        debosscher_confusion_data = self.parse_debosscher_confusion_table( \
                                           self.pars['debosscher_confusion_table3_fpath'])
        dotastro_classes = []
        for deboss_class in debosscher_confusion_data['class_name_list']:
            dotastro_classes.append(self.pars['debosscher_class_lookup'][deboss_class])
        self.pars['taxonomy_prune_defs']['terminating_classes'] = dotastro_classes

        fp=open('/home/pteluser/Dropbox/work/WEKAj48_dotastro_ge1srcs_period_nonper__exclude_non_debosscher/pairwise_classifier__debosscher_table3.pkl.gz','rb')
        pairwise_dict=cPickle.load(fp)
        fp.close()

        ### Load JPype weka classifiers using .model info:
        self.load_weka_classifiers(classifier_dict=pairwise_dict)

        # TODO: it might be nice to be able to generate this pairwise_pruned dict for any
        #     .arff dict so that we can generate classifications and a confusion matrix
        #       for any given .arff file.
        #  - this wouldnt help with any class pruning, since that requires the classifier
        #      to also be trained on similar pruned classes.

        if not os.path.exists(self.pars['trainset_pruned_pklgz_fpath']):
            PairwiseClassification = Pairwise_Classification(self.pars)
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            #pairwise_dict = a_dict['pairwise_dict']
            
        else:
            fp=gzip.open(self.pars['trainset_pruned_pklgz_fpath'],'rb')
            #pairwise_pruned_dict=cPickle.load(fp)
            pruned_sciclass_dict=cPickle.load(fp)
            fp.close()


        self.initialize_temp_cyto_files()

        #pprint.pprint(percent_tally_summary_dict)
        pklgz_fpath = '/home/pteluser/scratch/xmls_deboss_percentage_exclude__classified.pkl.gz'
        if not os.path.exists(pklgz_fpath):

            perc_pruned_sciclass_dict = self.partition_test_sciclass_dict_into_sampling_percentages( \
                                                                               pruned_sciclass_dict)
            percent_tally_summary_dict = {}
            percent_list = perc_pruned_sciclass_dict.keys()
            #percent_list.sort()
            percent_list.sort(reverse=True)
            for percent in percent_list:
                pruned_sciclass_dict = perc_pruned_sciclass_dict[percent]
                print('Percent:', percent)
                classif_summary_dict = self.do_pairwise_classification(classifier_dict=pairwise_dict,
                                                                       pairwise_pruned_dict=pruned_sciclass_dict)
                self.tally_correctly_classified_for_percent(percent, classif_summary_dict, percent_tally_summary_dict)

            fp = gzip.open(pklgz_fpath,'wb')
            cPickle.dump(percent_tally_summary_dict,fp,1) # ,1) means a binary pkl is used.
            fp.close()
        else:
            fp=gzip.open(pklgz_fpath,'rb')
            percent_tally_summary_dict=cPickle.load(fp)
            fp.close()

        self.plot_percent_tally_summary_dict(percent_tally_summary_dict)


    # NOTE: This is becoming more obsolete:
    def main(self):
        """
        Weka_Pairwise_Classification .main()

        """
        #debosscher_confusion_data=self.parse_debosscher_confusion_table( \
        #                          self.pars['debosscher_confusion_table3_fpath'])

        #debos_classes_name = self.form_debosscher_classes_name(\
        #                                  debosscher_confusion_data=debosscher_confusion_data)
        

        #fp=gzip.open(self.pars['weka_pairwise_classifiers_pkl_fpath'],'rb')
        fp=open(self.pars['weka_pairwise_classifiers_pkl_fpath'],'rb')
        pairwise_dict=cPickle.load(fp)
        fp.close()

        ### Load JPype weka classifiers using .model info:
        self.load_weka_classifiers(classifier_dict=pairwise_dict)

        # TODO: it might be nice to be able to generate this pairwise_pruned dict for any
        #     .arff dict so that we can generate classifications and a confusion matrix
        #       for any given .arff file.
        #  - this wouldnt help with any class pruning, since that requires the classifier
        #      to also be trained on similar pruned classes.

        if not os.path.exists(self.pars['trainset_pruned_pklgz_fpath']):
            PairwiseClassification = Pairwise_Classification(self.pars)
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            pairwise_dict = a_dict['pairwise_dict']
            

        fp=gzip.open(self.pars['trainset_pruned_pklgz_fpath'],'rb')
        pairwise_pruned_dict=cPickle.load(fp)
        fp.close()

        self.initialize_temp_cyto_files()
        classif_summary_dict = self.do_pairwise_classification(classifier_dict=pairwise_dict,
                                                               pairwise_pruned_dict=pairwise_pruned_dict)
        self.copy_cyto_file_to_final_path()
        self.write_confusionmatrix_heatmap_html(classif_summary_dict,
                                                html_fpath=self.pars['confusion_stats_html_fpath'])



class Test_Example:
    """ Test case / example class
    """
    def __init__(self, pars={}):
        self.pars = pars


    def get_classifications_for_test_case(self):
        """
        """
        arffrow_tups = [("sne", "2.162,2.0,0.0053282182438,2.55090195635,0.702928248516,0.188299399184,0.0853351581732,0.306187780088,0.205958893895,0.216289555174,0.0053282182438,-0.124394776891,23.3580520327,0.00367702648004,-0.904973211272,6.05564055936,0.0350294994587,2.80813223337,5.27392523503,-2.23428210218,-2.86580747521,0.349652335223,2.69069983158,0.31463106821,1.69707408596,3.48520407775,7.83568496402,2.75038673891,0.0053282182438,0.39160330964,0.0665352511945,0.0607257947202,0.0406020944045,0.0053282182438,0.439950111808,37.7034063201,-0.22184590449,-0.515693283073,7.97774524672,0.447686493506,1.7921955914,1.34471480133,0.180273221282,1.39787119835,1.48542920427,-1.54289099897,1.41100587329,0.17488709034,0.169280134169,0.32265377148,2.01871518912,0.0539946935208,0.0184983669692,0.00152904572163,0.00246177414402,0.00351218024472,0.0539946935208,0.65646684733,3.3519012806,0.38221127332,-2.09925632409,17.6179404532,14.6861040649,57.6000889149,0.127980248486,0.181313917301,1.67435402877,1.58195296201,2.01890019525,1.20891221146,9.28586368803,4.47649040333,3.14714961224,0.315492615375,0.0053282182438,0.0,25.0,0.333333333333,-0.402873531426,57697.7027284")]
        AdaboostWrapper = classifier_adaboost_wrapper.Adaboost_Wrapper(pars)
        #####
        pklgz_fpath = "%s/%s.pkl.gz" % (pars['pairwise_classifier_pklgz_dirpath'], 
                                        pars['pairwise_schema_name'])
        fp=gzip.open(pklgz_fpath,'rb')
        pairwise_schema_dict=cPickle.load(fp)
        fp.close()
        #####

        tally_dict_empty = {}
        for classifier_name in self.pars['taxonomy_prune_defs']['terminating_classes']:
            tally_dict_empty[classifier_name] = {'classif_count':0,
                                                 'notclassif_count':0,
                                                 'classif_conf_total':0.,
                                                 'notclassif_conf_total':0.}

        i_inputrow = 0
        for i_src, (class_expected, arff_row) in enumerate(arffrow_tups):
            tally_dict = copy.deepcopy(tally_dict_empty)
            for classifier_name in pairwise_schema_dict.keys():
                line = "%d %s %d %s" % (i_inputrow, classifier_name, i_src, arff_row)

                # # # # #
                elems = line.strip().split()
                if len(elems) == 0:
                    continue
                line_id = elems[0]
                pkl_fname = elems[1]
                src_id = elems[2]
                arff_row = elems[3]

                pair_name = pkl_fname #pkl_fname[:pkl_fname.rfind('.')]
                classifier_dict = pairwise_schema_dict[pair_name]

                feat_values = arff_row.split(',')
                num_list = []

                for elem in feat_values:
                    if elem == 't':
                        num_list.append([1])
                    elif elem == 'f':
                        num_list.append([0])
                    elif elem == '?':
                        num_list.append([numpy.NaN])
                    else:
                        num_list.append([float(elem)])

                train_data = numpy.array(num_list)
                #train_data = train_data.T # want: (29, 574) similar shape

                normalized_preds = AdaboostWrapper.apply_classifier( \
                                                                toclassify_data=train_data,
                                                                classifier_dict=classifier_dict)
                
                if normalized_preds[0] < 0:
                    sciclass_pred = classifier_dict['classname_tup'][0]
                    notpred_sciclass = classifier_dict['classname_tup'][1]
                else:
                    sciclass_pred = classifier_dict['classname_tup'][1]
                    notpred_sciclass = classifier_dict['classname_tup'][0]

                confidence = numpy.abs(normalized_preds[0])
                print("%s;%s;%lf;%s" % (src_id, sciclass_pred, confidence, classifier_dict['fname_root']))
                tally_dict[sciclass_pred]['classif_count'] += 1
                tally_dict[sciclass_pred]['classif_conf_total'] += confidence
                tally_dict[notpred_sciclass]['notclassif_count'] += 1
                tally_dict[notpred_sciclass]['notclassif_conf_total'] += confidence
            sort_list = []
            for sciclass, class_dict in tally_dict.iteritems():
                sort_list.append((class_dict['classif_count'], sciclass))
            sort_list.sort(reverse=True)
            for count, sciclass in sort_list[:10]:
                if tally_dict[sciclass]['classif_count'] != 0:
                    avgconf = tally_dict[sciclass]['classif_conf_total']/ \
                                             float(tally_dict[sciclass]['classif_count'])
                else:
                    avgconf = 0
                if tally_dict[sciclass]['notclassif_count'] != 0:
                    avgnotconf = tally_dict[sciclass]['notclassif_conf_total']/ \
                                             float(tally_dict[sciclass]['notclassif_count'])
                else:
                    avgnotconf = 0
                print("(%s) %8.8s\t count=%d \t avgconf=%8.8s\t notclassif=%d\t avgnotconf=%f" % (\
                       class_expected, sciclass, 
                       tally_dict[sciclass]['classif_count'], str(avgconf),
                       tally_dict[sciclass]['notclassif_count'], avgnotconf))
        return


    def get_classifications_for_pruned_trainset_rows(self):
        """ Read all (pruned) trainingset arff rows from .pkl.gz and
        generate classifications for them, summarizing the results
        """

        fp=gzip.open(self.pars['trainset_pruned_pklgz_fpath'],'rb')
        pairwise_pruned_dict=cPickle.load(fp)
        fp.close()

        #arffrow_tups = [("sne", "2.162,2.0,0.0053282182438,2.55090195635,0.702928248516,0.188299399184,0.0853351581732,0.306187780088,0.205958893895,0.216289555174,0.0053282182438,-0.124394776891,23.3580520327,0.00367702648004,-0.904973211272,6.05564055936,0.0350294994587,2.80813223337,5.27392523503,-2.23428210218,-2.86580747521,0.349652335223,2.69069983158,0.31463106821,1.69707408596,3.48520407775,7.83568496402,2.75038673891,0.0053282182438,0.39160330964,0.0665352511945,0.0607257947202,0.0406020944045,0.0053282182438,0.439950111808,37.7034063201,-0.22184590449,-0.515693283073,7.97774524672,0.447686493506,1.7921955914,1.34471480133,0.180273221282,1.39787119835,1.48542920427,-1.54289099897,1.41100587329,0.17488709034,0.169280134169,0.32265377148,2.01871518912,0.0539946935208,0.0184983669692,0.00152904572163,0.00246177414402,0.00351218024472,0.0539946935208,0.65646684733,3.3519012806,0.38221127332,-2.09925632409,17.6179404532,14.6861040649,57.6000889149,0.127980248486,0.181313917301,1.67435402877,1.58195296201,2.01890019525,1.20891221146,9.28586368803,4.47649040333,3.14714961224,0.315492615375,0.0053282182438,0.0,25.0,0.333333333333,-0.402873531426,57697.7027284")]
        

        AdaboostWrapper = classifier_adaboost_wrapper.Adaboost_Wrapper(pars)
        #####
        pklgz_fpath = "%s/%s.pkl.gz" % (pars['pairwise_classifier_pklgz_dirpath'], 
                                        pars['pairwise_schema_name'])
        fp=gzip.open(pklgz_fpath,'rb')
        pairwise_schema_dict=cPickle.load(fp)
        fp.close()
        #####


        class_summary = {}
        for class_name in self.pars['taxonomy_prune_defs']['terminating_classes']:
            class_summary[class_name] = {'n_sources':0,
                                         'tot_correctly_sub_classified':0,
                                         'tot_incorrect_sub_classified':0,
                                         'tot_correctly_final_classified':0,
                                         'tot_incorrect_final_classified':0,
                                         'n_other_srcs_incorrectly_final_classified':0,
                                         'top_feats':[]}

        """
        #n_sources  # number of sources of a science class
        #tot_correctly_sub_classified    # total correct subclassifications for all sources
            -> Insightful:   tot_correctly_sub_classified / (n_sources * len(pairwise_schema_dict))
        !!! tot_incorrect_sub_classified    # total incorrect subclassifications for all sources
            -> This is just (n_sources * len(pairwise_schema_dict)) - tot_correctly_sub_classified
        #tot_correctly_final_classified  # total correct final classifications for all sources
        !!! tot_incorrect_final_classified  # total incorrect final classifications for all sources
            -> this is just:     (n_sources - tot_correctly_final_classified)
        n_other_srcs_incorrectly_final_classified # n of other srcs incorrectly final classified as this science type (eg: [rrlya] = N of other class sources final-classified as rrlyra
            -> this shows how confusing this class may be to classifiers
        """


        ### NOTE: this could be somewhere else during __init__ or even stored in a .pkl:
        ### This constructs a dict which contains the top features (and significance)
        ###     used when vote-combined classifing some scienceclass:
        ###     some_dict[sciclass]['top_feats'][0]{'feat_name]:, 'top_feats'}
        tally_feat_dict = {}
        for pairname, pair_dict in pairwise_schema_dict.iteritems():

            pprint.pprint((pairname, pair_dict['top_feats'])) # DEBUG USE ONLY

            for a_class in pairname.split(';'):
                if a_class not in tally_feat_dict:
                    tally_feat_dict[a_class] = {}
                for top_feat_dict in pairwise_schema_dict[pairname]['top_feats']:
                    feat_name = top_feat_dict['feat_name']
                    tot_alpha = top_feat_dict['tot_alpha']
                    if tot_alpha == numpy.inf:
                        tot_alpha = 0.0 #KLUDGE (I'm guessing this is a terminating node), for rrlyra__nov only
                    if feat_name not in tally_feat_dict[a_class]:
                        tally_feat_dict[a_class][feat_name] = 0.0
                    tally_feat_dict[a_class][feat_name] += tot_alpha

        # Now we want to sort the [(tot_alpha, feat_name)]
        #     and order a list of reverse ranked, which is dict[class_name]
        #   this dict can then be used with[scilacc] at L316
        for class_name, class_dict in tally_feat_dict.iteritems():
            tup_sort_list = []
            for feat_name, total_alpha in class_dict.iteritems():
                tup_sort_list.append((total_alpha, feat_name))
            tup_sort_list.sort(reverse=True)
            class_summary[class_name]['top_feats'] = copy.copy(tup_sort_list[:3])
        ###

        fpath = "/tmp/%s" % (self.pars['cyto_network_fname'])
        if os.path.exists(fpath):
            os.system('rm ' + fpath)
        fp_cyto_network = open(fpath, 'w')

        fpath = "/tmp/%s" % (self.pars['cyto_nodeattrib_fname'])
        if os.path.exists(fpath):
            os.system('rm ' + fpath)
        fp_cyto_nodeattrib = open(fpath, 'w')
        

        tally_dict_empty = {}
        for classifier_name in self.pars['taxonomy_prune_defs']['terminating_classes']:
            tally_dict_empty[classifier_name] = {'classif_count':0,
                                                 'notclassif_count':0,
                                                 'classif_conf_total':0.,
                                                 'notclassif_conf_total':0.}
        i_inputrow = 0

        for orig_class, orig_class_dict in pairwise_pruned_dict.iteritems():
            #if orig_class == 'nov':
            #    print 'yo'
            print(orig_class)
            fp_cyto_nodeattrib.write("%s\t%s\t0\t0\n" % (orig_class, orig_class))
            class_summary[orig_class]['n_sources'] = orig_class_dict['count']
            for i_src, arff_row in enumerate(orig_class_dict['arffrow_wo_classnames']):
                #fp_cyto_nodeattrib.write("%s_%d\t%s\t1\thttp://dotastro.org/lightcurves/source.php?Source_ID=%d\n" % (orig_class, i_src, orig_class, orig_class_dict['srcid_list'][i_src]))
                fp_cyto_nodeattrib.write("%s_%d\t%s\t1\thttp://lyra.berkeley.edu/tcp/dotastro_periodfold_plot.php?srcid=%d\n" % (orig_class, i_src, orig_class, orig_class_dict['srcid_list'][i_src] + 100000000))
                feat_values = arff_row.split(',')
                num_list = []
                for elem in feat_values:
                    if elem == 't':
                        num_list.append([1])
                    elif elem == 'f':
                        num_list.append([0])
                    elif elem == '?':
                        num_list.append([numpy.NaN])
                    else:
                        num_list.append([float(elem)])
                train_data = numpy.array(num_list)
                #train_data = train_data.T # want: (29, 574) similar shape

                tally_dict = copy.deepcopy(tally_dict_empty)
                for classifier_name in pairwise_schema_dict.keys():
                    classifier_dict = pairwise_schema_dict[classifier_name]

                    normalized_preds = AdaboostWrapper.apply_classifier(toclassify_data=train_data,
                                                                    classifier_dict=classifier_dict)
                    if normalized_preds[0] < 0:
                        sciclass_pred = classifier_dict['classname_tup'][0]
                        notpred_sciclass = classifier_dict['classname_tup'][1]
                    else:
                        sciclass_pred = classifier_dict['classname_tup'][1]
                        notpred_sciclass = classifier_dict['classname_tup'][0]

                    if sciclass_pred == orig_class:
                        class_summary[orig_class]['tot_correctly_sub_classified'] += 1
                    #else:
                    #    class_summary[sciclass_pred]['tot_incorrect_sub_classified'] += 1

                    # # # #
                    # TODO: need to still tally the subclassifications to find the overall class


                    confidence = numpy.abs(normalized_preds[0])
                    #print "%s;%s;%lf;%s" % (src_id, sciclass_pred, confidence, classifier_dict['fname_root'])
                    #tally_dict[sciclass_pred]['classif_count'] += 1
                    #tally_dict[notpred_sciclass]['notclassif_count'] += 1
                    tally_dict[sciclass_pred]['classif_count'] += abs(normalized_preds[0])
                    tally_dict[notpred_sciclass]['notclassif_count'] += abs(normalized_preds[0])
                sort_list = []
                for sciclass, class_dict in tally_dict.iteritems():
                    sort_list.append((class_dict['classif_count'], sciclass))
                sort_list.sort(reverse=True)

                # # # # KLUDGE: running this classifier twice, could be avoided if this info was cached in some data structure:
                # TODO: if we are doing ++1 counting, then we need to account for more than 2 equal counts in the sort_list (and somehow go through them and choose a winner).  Maybe using confidences at theis stage would be smart
                if sort_list[0][0] == sort_list[1][0]:
                    print("!!!, sort_list[0][0] == sort_list[1][0]")
                    classifier_name = "%s;%s" % (sort_list[0][1], sort_list[1][1])
                    if classifier_name not in pairwise_schema_dict:
                        classifier_name = "%s;%s" % (sort_list[1][1], sort_list[0][1])
                    try:
                        classifier_dict = pairwise_schema_dict[classifier_name]
                    except:
                        print('ERROR: unknown classifier_name:', classifier_name)
                        raise
                        
                    normalized_preds = AdaboostWrapper.apply_classifier(toclassify_data=train_data,
                                                                    classifier_dict=classifier_dict)

                    if normalized_preds[0] < 0:
                        sciclass_pred = classifier_dict['classname_tup'][0]
                    else:
                        sciclass_pred = classifier_dict['classname_tup'][1]
                    tally_dict[sciclass_pred]['classif_count'] += 1

                    sort_list = []
                    for sciclass, class_dict in tally_dict.iteritems():
                        sort_list.append((class_dict['classif_count'], sciclass))
                    sort_list.sort(reverse=True)
                # # # #
                
                #for count, sciclass in sort_list[:3]:
                for count, sciclass in sort_list[:2]:
                    ### I want the 3rd weight to be 1, and the others to be (count_n - count_3rd)**3
                    #weight = (count - sort_list[2][0] + 1)**3
                    weight = (count - sort_list[1][0] + 1)**3

                    # TODO: I want to use: pairwise_schema_dict[classifier_name]
                    #    - but I am not sure what order the classifer name is...
                    ### This algo taken from L438:
                    #pair_list = [sciclass, ]
                    #pair_list.sort()
                    #pair_name = pair_list[0] + ';' + pair_list[1]
                    # # # NOTE: now that I am filling 

                    fp_cyto_network.write("%s_%d\t%s\t%lf\t%s\t%s\t%s_%lf\t%s_%lf\n" % (orig_class, i_src, sciclass, weight, orig_class, sciclass, class_summary[sciclass]['top_feats'][0][1], class_summary[sciclass]['top_feats'][0][0], class_summary[sciclass]['top_feats'][1][1], class_summary[sciclass]['top_feats'][1][0]))

                if sort_list[0][1] == orig_class:
                    class_summary[orig_class]['tot_correctly_final_classified'] += 1
                else:
                    class_summary[sort_list[0][1]]['n_other_srcs_incorrectly_final_classified'] += 1
            #pprint.pprint((orig_class, orig_class_dict['count'], class_summary[orig_class]))
            #print
        if os.path.exists(self.pars['pruned_classif_summary_stats_pkl_fpath']):
            os.system('rm ' + self.pars['pruned_classif_summary_stats_pkl_fpath'])
        fp = open(self.pars['pruned_classif_summary_stats_pkl_fpath'],'w')
        cPickle.dump(class_summary, fp)
        fp.close()

        fp_cyto_network.close()
        fp_cyto_nodeattrib.close()

        ### Finally, I copy the finished files to the DropBox directory, to play nice.
        cp_str = "cp /tmp/%s %s/%s" % (self.pars['cyto_network_fname'],
                                       self.pars['cyto_work_final_fpath'],
                                       self.pars['cyto_network_fname'])
        os.system(cp_str)


        cp_str = "cp /tmp/%s %s/%s" % (self.pars['cyto_nodeattrib_fname'],
                                       self.pars['cyto_work_final_fpath'],
                                       self.pars['cyto_nodeattrib_fname'])
        os.system(cp_str)
        return



    def main(self):
        """ Do tests / metrics
        """
        #self.get_classifications_for_test_case()
        self.get_classifications_for_pruned_trainset_rows()


class Pairwise_Classification:
    """
    """
    def __init__(self, pars):
        self.pars = pars
        self.DotastroSciclassTools = dotastro_sciclass_tools.Dotastro_Sciclass_Tools()
        if 'sciclass_lookup' in pars:
            self.sciclass_lookup = pars['sciclass_lookup'] # This occurs when on citriss33 and no MySQL is used.
        else:
            self.sciclass_lookup = self.DotastroSciclassTools.get_sciclass_lookup_dict()


    def parse_arff(self, arff_has_ids=False, arff_has_classes=True, has_srcid=False, get_features=False, arff_str='', write_pkl=True):
        """ Parse a given .arff file and generate dict of form:

        <science class>:{<arff linenumber>:arff row}

        This assumes the input .arff file is of form:

        <no id> ... <features>... 66666666667,4.45346931148,?,'Microlensing Event'
        """
        ##### NOTE: I disable this so that self.feat_id_names{} can be filled and since it
        #####    takes a couple secounds during classifier creation:
        
        #if os.path.exists(self.pars['arff_sciclass_dict_pkl_fpath']):
        #    arff_sciclass_dict = cPickle.load(open(self.pars['arff_sciclass_dict_pkl_fpath']))
        #    return arff_sciclass_dict

        if len(arff_str) > 0:
            lines = arff_str.split('\n')
        else:
            lines = open(self.pars['dotastro_arff_fpath']).readlines()

        #if get_features:
        #    feature_line_list = []
        #    for line in lines:
        #        if line[:10].lower() == '@attribute':
        #            feature_line_list.append(line)
        #        elif line[:5].lower() == '@data':
        #            break # no more features/classes to read
        #    feature_name_list = []
        #    for line in feature_line_list[:-1]:
        #        feature_name = line.split()[1]
        #        feature_name_list.append(feature_name)

        arff_sciclass_dict = {}
        self.feat_id_names = {}
        i_attrib = 0
        for line in lines:
            # eclisping EB: if '13231,0.654' in line:
            #if '13247,0.01965' in line:
            #    # Chemically Peculiar Stars
            #    print 'yo' # DEBUG
            if len(line.strip()) == 0:
                continue
            if line[0] == '%':
                continue
            if line[0] == '@':
                if '@ATTRIBUTE' in line.upper():
                    line_split = line.split()
                    feat_name = line_split[1]
                    if has_srcid:
                        if feat_name == 'source_id':
                            continue
                    self.feat_id_names[i_attrib] = feat_name
                    i_attrib += 1
                continue
            if line.count("'") > 0:
                # assuming all classes are surrounded by single quotes and no attribs have quotes
                i_sciclass = line.rfind("'",0,line.rfind("'")) + 1
                class_name = line[i_sciclass:].replace("'",'').strip()#.replace(",",'')
            else:
                # This is when weka write .arff and classes without spaces are not contained in quotes
                i_sciclass = line.rfind(",") + 1
                class_name = line[i_sciclass:].strip()#.replace(",",'')                
                i_sciclass = line.rfind(",") + 2
            ###KLUDGE: the .arff file may have some long-science-class names from the
            ###     tutor dataset, or ?(maybe with ',' and '-' string replacement)?
            if class_name not in self.sciclass_lookup['longname_shortname']:
                #print '!!!', class_name
                temp_classname = class_name.replace(',','-')
                if '-' in temp_classname:
                    class_elems_unstripped = temp_classname.split('-')
                else:
                    class_elems_unstripped = temp_classname.split(' ')
                class_elems = []
                for elem in class_elems_unstripped:
                    class_elems.append(elem.strip())
                replacement_classname = None
                for a_longclassname in self.sciclass_lookup['longname_shortname'].keys():
                    a_match = True
                    for elem in class_elems:
                        if not elem in a_longclassname:
                            a_match = False
                            break
                    if a_match:
                        replacement_classname = a_longclassname
                        #print 'MATCH:', replacement_classname
                        break
                if replacement_classname is None:
                    print('pairwise_classifications.parse_arff(): No match found:', class_name, class_elems)
                class_name = replacement_classname
            ### Now we use this known longclassname to get the equivalent shortname,
            #   which we will use in the .arff file
            shortname = self.sciclass_lookup['longname_shortname'][class_name]
            if shortname in self.DotastroSciclassTools.pars['canonical_shortnames']:
                shortname = self.DotastroSciclassTools.pars['canonical_shortnames'][shortname]


            if shortname not in arff_sciclass_dict:
                arff_sciclass_dict[shortname] = {'count':0,
                                                 'srcid_list':[],
                                                 'arffrow_with_classnames':[],
                                                 'arffrow_wo_classnames':[],
                                                 'feat_lists':[]}
            #arff_sciclass_dict[class_name]['arffrow_with_classnames'].append(line)
            if has_srcid:
                line_subsection = line[line.find(',') + 1:i_sciclass - 2]
                ##### 20100810: dstarr removes the int() constraint:
                #srcid = int(line[:line.find(',')])
                srcid = line[:line.find(',')]
                arff_sciclass_dict[shortname]['srcid_list'].append(srcid)
            else:
                line_subsection = line[:i_sciclass - 2]

            if get_features:
                feat_str_list = line_subsection.split(',')
                feat_list = []
                for feat_str in feat_str_list:
                    try:
                        feat_list.append(float(feat_str))
                    except:
                        if feat_str == '?':
                            feat_list.append(None)
                        else:
                            feat_list.append(feat_str)
                arff_sciclass_dict[shortname]['feat_lists'].append(feat_list)

            line_with_shortname = "%s,'%s'" % (line_subsection, shortname)
            arff_sciclass_dict[shortname]['arffrow_with_classnames'].append(line_with_shortname)
            arff_sciclass_dict[shortname]['arffrow_wo_classnames'].append(line_subsection)
            arff_sciclass_dict[shortname]['count'] += 1
            #if shortname == 'sne':
            #    print 'yo'
            #if line[:i_sciclass - 2][-1] == '?':
            #    print 'with   ', shortname
            #else:
            #    print 'without', shortname

        if write_pkl:
            fp = open(self.pars['arff_sciclass_dict_pkl_fpath'],'w')
            cPickle.dump(arff_sciclass_dict, fp)
            fp.close()


        return arff_sciclass_dict


    # More obsolete:
    def generate_pairwise_trainingset_row_dict__using_every_pair(self, arff_sciclass_dict):
        """ Generate a dict of the form:
        {(<sciclass_name1>,<sciclass_name2>):{'arff_rows_with_classnames':[], 'arff_rows_wo_classnames':[], ...}

        NOTE: will probably want some limiting number of sources for a science-class to be
              included for pairwise classification
        """
        pairwise_sciclass_list = []
        for sciclass_name, sciclass_dict in arff_sciclass_dict.iteritems():
            if sciclass_dict['count'] >= self.pars['min_num_sources_for_pairwise_class_inclusion']:
                pairwise_sciclass_list.append(sciclass_name)

        if ((len(self.pars['pairwise_trainingset_dirpath']) > 10) and
            (os.path.exists(self.pars['pairwise_trainingset_dirpath']))):
            os.system('rm -Rf ' + self.pars['pairwise_trainingset_dirpath'])
        os.system('mkdir ' + self.pars['pairwise_trainingset_dirpath'])

        pairwise_trainingset_row_dict = {}
        pairwise_dict = {}
        for classname_1 in pairwise_sciclass_list:
            for classname_2 in pairwise_sciclass_list:
                pair_list = [classname_1, classname_2]
                pair_list.sort()
                pair_name = pair_list[0] + ';' + pair_list[1]
                if ((classname_1 == classname_2) or \
                    (pair_name in pairwise_trainingset_row_dict.keys())):
                    continue # skip this combo since redundant
                if 1:
                    fname_root = pair_name.replace(';','___').replace(' ','_').replace(',','_')
                    fpath = "%s/%s.arffbody" % (self.pars['pairwise_trainingset_dirpath'],
                                                fname_root)
                    pairwise_dict[pair_name]={'arff_fpath':fpath,
                                            'fname_root':fname_root,
                                            'classname_tup':(pair_list[0], pair_list[1]),
                                            'src_count_tup':(arff_sciclass_dict[pair_list[0]]['count'],
                                                             arff_sciclass_dict[pair_list[1]]['count'])}
                    fp = open(fpath,'w')
                    for row in arff_sciclass_dict[classname_1]['arffrow_with_classnames']:
                        fp.write(row)
                    for row in arff_sciclass_dict[classname_2]['arffrow_with_classnames']:
                        fp.write(row)
                    fp.close()
                else:
                    pairwise_trainingset_row_dict[pair_name] = {'arffrow_with_classnames':[],
                                                                'arffrow_wo_classnames':[]}
                    pairwise_trainingset_row_dict[pair_name]['arffrow_with_classnames'].extend( \
                         arff_sciclass_dict[classname_1]['arffrow_with_classnames'])
                    pairwise_trainingset_row_dict[pair_name]['arffrow_with_classnames'].extend( \
                         arff_sciclass_dict[classname_2]['arffrow_with_classnames'])
            
                    pairwise_trainingset_row_dict[pair_name]['arffrow_wo_classnames'].extend( \
                         arff_sciclass_dict[classname_1]['arffrow_wo_classnames'])
                    pairwise_trainingset_row_dict[pair_name]['arffrow_wo_classnames'].extend( \
                         arff_sciclass_dict[classname_2]['arffrow_wo_classnames'])
        #print len(pairwise_trainingset_row_dict.keys())
        #return pairwise_trainingset_row_dict
        return pairwise_dict


    def condense_taxonomy_of_sciclassdict(self, arff_sciclass_dict):
        """ Given a dictionary of {<sciclassname>:<arff row information>},
        combine the science classes depending on some taxonomy pruning information.
        """
        if len(self.pars['taxonomy_prune_defs']['terminating_classes']) == 0:
            ### This is probably the Debosscher case, where we want to use all of the classes in the data
            return arff_sciclass_dict

        pruned_sciclass_dict = {}
        ### First add for all elements in the arff_sciclass_dict for <terminating classes of interest>.
        for shortname in self.pars['taxonomy_prune_defs']['terminating_classes']:
            #longname = self.sciclass_lookup['shortname_longname'][shortname]
            if shortname in arff_sciclass_dict:
                pruned_sciclass_dict[shortname] = copy.deepcopy(arff_sciclass_dict[shortname])
            else:
                # We have no data for this itself, but we still want to have a structure
                #    which we can add decendent class data to.
                pruned_sciclass_dict[shortname] = {'count':0,
                                                   'srcid_list':[],
                                                   'arffrow_with_classnames':[],
                                                   'arffrow_wo_classnames':[]}
        ### Next add all classes which are decendents of <terminating classes of interest>
        for shortname, class_dict in arff_sciclass_dict.iteritems():
            #shortname = self.sciclass_lookup['longname_shortname'][longname]
            if shortname in self.DotastroSciclassTools.pars['canonical_shortnames']:
                shortname = self.DotastroSciclassTools.pars['canonical_shortnames'][shortname]

            cur_shortname = shortname
            is_traversing_lineage = True
            while is_traversing_lineage:
                parent_shortname = self.sciclass_lookup['shortname_parentshortname'][cur_shortname]
                if parent_shortname == "_varstar_":
                    # Then we are at the top-most science class, meaning that none of the ancestors
                    # of the original science_class are within a <terminating class of interest>
                    #  - so for now we skip this class).
                    #  - in the future we may add these classes (but would need to be careful to add
                    #           the bottom-most class, not the highest ancestor)
                    is_traversing_lineage = False
                    break
                if parent_shortname in self.pars['taxonomy_prune_defs']['terminating_classes']:
                    pruned_sciclass_dict[parent_shortname]['count'] += class_dict['count']
                    #pruned_sciclass_dict[parent_shortname]['arffrow_with_classnames'].extend( \
                    #                                        class_dict['arffrow_with_classnames'])
                    for i, line in enumerate(class_dict['arffrow_with_classnames']):
                        i_sciclass = line.rfind("'",0,line.rfind("'")) + 1
                        line_with_shortname = "%s,'%s'" % (line[:i_sciclass - 2], parent_shortname)
                        pruned_sciclass_dict[parent_shortname]['arffrow_with_classnames'].append( \
                                                            line_with_shortname)
                        pruned_sciclass_dict[parent_shortname]['srcid_list'].append(class_dict['srcid_list'][i])
                    pruned_sciclass_dict[parent_shortname]['arffrow_wo_classnames'].extend( \
                                                            class_dict['arffrow_wo_classnames'])
                    is_traversing_lineage = False
                    break
                else:
                    cur_shortname = parent_shortname

        return pruned_sciclass_dict


    def generate_pairwise_trainingset_row_dict__using_pruned_taxonomy_tree(self, arff_sciclass_dict):
        """ Generate a dict of the form:
        {(<sciclass_name1>,<sciclass_name2>):{'arff_rows_with_classnames':[], 'arff_rows_wo_classnames':[], ...}

        NOTE: will probably want some limiting number of sources for a science-class to be
              included for pairwise classification
        """
        pairwise_sciclass_list = []
        for sciclass_name, sciclass_dict in arff_sciclass_dict.iteritems():
            print(sciclass_name, sciclass_dict['count'], self.pars['min_num_sources_for_pairwise_class_inclusion'])
            if sciclass_dict['count'] >= self.pars['min_num_sources_for_pairwise_class_inclusion']:
                pairwise_sciclass_list.append(sciclass_name)

        if ((len(self.pars['pairwise_trainingset_dirpath']) > 10) and
            (os.path.exists(self.pars['pairwise_trainingset_dirpath']))):
            os.system('rm -Rf ' + self.pars['pairwise_trainingset_dirpath'])
        os.system('mkdir ' + self.pars['pairwise_trainingset_dirpath'])

        pairwise_trainingset_row_dict = {}
        pairwise_dict = {}
        for classname_1 in pairwise_sciclass_list:
            for classname_2 in pairwise_sciclass_list:
                pair_list = [classname_1, classname_2]
                pair_list.sort()
                pair_name = pair_list[0] + ';' + pair_list[1]
                if ((classname_1 == classname_2) or \
                    (pair_name in pairwise_trainingset_row_dict.keys())):
                    continue # skip this combo since redundant
                if 1:
                    fname_root = pair_name.replace(';','___').replace(' ','_').replace(',','_')
                    fpath = "%s/%s.arffbody" % (self.pars['pairwise_trainingset_dirpath'],
                                                fname_root)
                    pairwise_dict[pair_name]={'arff_fpath':fpath,
                                            'fname_root':fname_root,
                                            'classname_tup':(pair_list[0], pair_list[1]),
                                            'src_count_tup':(arff_sciclass_dict[pair_list[0]]['count'],
                                                             arff_sciclass_dict[pair_list[1]]['count'])}
                    fp = open(fpath,'w')
                    for row in arff_sciclass_dict[classname_1]['arffrow_with_classnames']:
                        fp.write(row + '\n')
                    for row in arff_sciclass_dict[classname_2]['arffrow_with_classnames']:
                        fp.write(row + '\n')
                    fp.close()
                else:
                    pairwise_trainingset_row_dict[pair_name] = {'arffrow_with_classnames':[],
                                                                'arffrow_wo_classnames':[]}
                    pairwise_trainingset_row_dict[pair_name]['arffrow_with_classnames'].extend( \
                         arff_sciclass_dict[classname_1]['arffrow_with_classnames'])
                    pairwise_trainingset_row_dict[pair_name]['arffrow_with_classnames'].extend( \
                         arff_sciclass_dict[classname_2]['arffrow_with_classnames'])
            
                    pairwise_trainingset_row_dict[pair_name]['arffrow_wo_classnames'].extend( \
                         arff_sciclass_dict[classname_1]['arffrow_wo_classnames'])
                    pairwise_trainingset_row_dict[pair_name]['arffrow_wo_classnames'].extend( \
                         arff_sciclass_dict[classname_2]['arffrow_wo_classnames'])
        #print len(pairwise_trainingset_row_dict.keys())
        #return pairwise_trainingset_row_dict
        return pairwise_dict


    def write_sciclass_dict_pkl(self, pkl_fpath='', sciclass_dict={}):
        """ Write the sciclass_dict to a pkl file.
        This dict could contain pruned or normal science classes.

        This dict contains arff rows in dict like:
        dict[<classname>] = {'arffrow_wo_classnames':[],
                                              'srcid_list':[],
                                              'count':123}
        """
        os.system("rm " + pkl_fpath)
        fp=gzip.open(pkl_fpath,'wb')
        cPickle.dump(sciclass_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()


    def generate_pairwise_arffbody_trainingsets(self, arff_has_ids=False, arff_has_classes=True,
                                                has_srcid=False):
        """ Given the original dotastro trainingset with many science classes,
        generate arff-body files with all pairwise science-class combinations, although
        science classes are constrained by a number-of-source cut.
        """
        arff_sciclass_dict=self.parse_arff(arff_has_ids=arff_has_ids, arff_has_classes=arff_has_classes, \
                                           has_srcid=has_srcid)

        pruned_sciclass_dict = self.condense_taxonomy_of_sciclassdict(arff_sciclass_dict)

        ### For Test_Example() use only:
        self.write_sciclass_dict_pkl(pkl_fpath=self.pars['trainset_pruned_pklgz_fpath'],
                                     sciclass_dict=pruned_sciclass_dict)

        #pairwise_dict = self.generate_pairwise_trainingset_row_dict(arff_sciclass_dict)
        pairwise_dict = self.generate_pairwise_trainingset_row_dict__using_pruned_taxonomy_tree(\
                                                                               pruned_sciclass_dict)
        return {'pruned_sciclass_dict':pruned_sciclass_dict,
                'pairwise_dict':pairwise_dict}


    def generate_confidence_dict_given_pairwise_arff_fpath(self, arffbody_fpath):
        """ Given an arff fpath which has only 2 science classifications, 
        Convert these classes into realnumber confidences [-1,1] which can be
        used by confidence rated AdaBoost.

        Initially, this will just be: -1 is one class, +1 is another.
        """
        confidence_class_summary = {}
        confid_dict = {}
        lines = open(arffbody_fpath).readlines()
        low_confid_val = -1
        for j, line in enumerate(lines):
            if (line[0] == '%') or (line[0] == '@') or (len(line.strip()) == 0):
                continue
            i_sciclass = line.rfind("'",0,line.rfind("'")) + 1
            class_name = line[i_sciclass:].replace("'",'').strip()
            if not class_name in confidence_class_summary.keys():
                confidence_class_summary[class_name] = {'count':0,
                                                        'conf_val':low_confid_val}
                low_confid_val += 2
            confidence_class_summary[class_name]['count'] += 1
            confid_dict[j] = confidence_class_summary[class_name]['conf_val']

        if len(confidence_class_summary.keys()) != 2:
            print('ERROR, not a pairwise, 2 class arff', arffbody_fpath, confidence_class_summary)
        return (confid_dict, confidence_class_summary)


    def generate_weka_model(self, arff_fpath='', model_fpath='', result_fpath=''):
        """

         - generate a .model (J48)
            -> See: ingest_tools/generate_weka_classifiers.py:L529 generate model and save decision-tree results

        """
        ### These imports are needed when generating the .model files from command line.
        import stat
        import datetime
        import time

        model_fpath = "%s.model" % (arff_fpath[:arff_fpath.rfind('.arff')])
        results_fpath = "%s.results" % (arff_fpath[:arff_fpath.rfind('.arff')])

        if os.path.exists(model_fpath):
            os.system('rm ' + model_fpath)
        if os.path.exists(results_fpath):
            os.system('rm ' + results_fpath)
        
        t_start = datetime.datetime.now()
        exec_str = "/usr/lib/jvm/java-6-sun-1.6.0.03/bin/java weka.classifiers.trees.J48 -t %s -d %s -C 0.25 -M 2" % (arff_fpath, model_fpath)
        (a,b,c) = os.popen3(exec_str)

        file_is_written = False
        while not file_is_written:
            t_now = datetime.datetime.now()
            if t_now > (t_start + datetime.timedelta(seconds=10)):
                print('ERROR: unable to generate .model:', exec_str)
                #file_is_written = True # NOTE: file is not really written
                break
            if not os.path.exists(model_fpath):
                time.sleep(1)
                continue
            model_stat = os.stat(model_fpath)
            if (datetime.datetime.fromtimestamp(model_stat[stat.ST_MTIME]) + datetime.timedelta(seconds=1) < t_now):
                #file_is_written = True # some time has passed.  We are done writing.
                break
            time.sleep(1)
        
        a.close()
        c.close()
        lines = b.read()
        b.close()
        fp = open(results_fpath, 'w')
        fp.write(lines)
        fp.close()

        if len(lines) < 10:
            print(exec_str)

        return {'model_fpath':model_fpath,
                'results_fpath':results_fpath,
                'arff_fpath':arff_fpath} # NOTE: This will overwrite the existing arff_fpath in the stack above dictionary


    def write_full_arff_fpath(self, pairclass_dict={}, orig_arff_header_lines=[]):
        """ Add arff header to the existing pairwise-trainingset arff rows.
        """
        full_lines = copy.copy(orig_arff_header_lines)
        full_lines.insert(0,'@relation ts\n\n') # a weka .arff needs to begin with: @relation
        class_attrib_line = "@attribute class {'%s','%s'}\n\n@data\n" % (pairclass_dict['classname_tup'][0],
                                                              pairclass_dict['classname_tup'][1])
        full_lines.append(class_attrib_line)
        full_lines.extend(open(pairclass_dict['arff_fpath']).readlines())

        full_arff_fpath = "%s.arff" % (pairclass_dict['arff_fpath'][:pairclass_dict['arff_fpath'].rfind('.arff')])
        fp = open(full_arff_fpath, 'w')
        fp.writelines(full_lines)
        fp.close()
        return full_arff_fpath


    def parse_orig_arff_header_lines(self):
        """ Parse weka/arff header lines from the original dotastro arff file with all sciclasses
            - exclude the class attribute line since we will fill with classes customized to a class-pair.
        """
        orig_arff_lines = open(self.pars['dotastro_arff_fpath']).readlines()
        orig_arff_header_lines = []
        for line in orig_arff_lines:
            if '@attribute class' in line.lower():
                continue # skip this since we will fill with classes customized to a class-pair
            elif '@attribute source_id' in line.lower():
                continue # skip the source_id since not in the headerless pairwise arff row file
            elif '@attribute' in line.lower():
                orig_arff_header_lines.append(line)
            elif '@data' in line.lower():
                break # just parsing the header
        return orig_arff_header_lines


    def generate_weka_classifiers(self, pairwise_dict={}, arff_has_ids=False, arff_has_classes=True):
        """ Main function for generating pairwise WEKA classifiers.

        TODO:
         - parse each pairwise .arffbody trainingset
         - add arff / weka header from the original .arff
         - generate a .model (J48)
            -> See: ingest_tools/generate_weka_classifiers.py:L529 generate model and save decision-tree results
         - store the model in some .pkl or reference fpath for later weka classification
         - (Then in classifier)
            - similar to adaboost classifier structure, but parse the weka .model
            - See: 

pprint.pprint(pairwise_dict['c;sne'])
{'arff_fpath': '/home/pteluser/scratch/pairwise_trainingsets/c___sne.arffbody',
 'classname_tup': ('c', 'sne'),
 'fname_root': 'c___sne',
 'src_count_tup': (679, 373)}
        
        """
        orig_arff_header_lines = self.parse_orig_arff_header_lines()
            
        for pairclass_name, pairclass_dict in pairwise_dict.iteritems():
            full_arff_fpath = self.write_full_arff_fpath(pairclass_dict=pairclass_dict, \
                                                         orig_arff_header_lines=orig_arff_header_lines)
            path_dict = self.generate_weka_model(arff_fpath=full_arff_fpath, model_fpath='', result_fpath='')
            pairclass_dict.update(path_dict)

        ### Now write the pairclass_dict into a Pickle file for later classification reference:
        if os.path.exists(self.pars['weka_pairwise_classifiers_pkl_fpath']):
            os.system('rm ' + self.pars['weka_pairwise_classifiers_pkl_fpath'])
        fp=open(self.pars['weka_pairwise_classifiers_pkl_fpath'],'wb')
        cPickle.dump(pairwise_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()
        

    def generate_classifiers(self, pairwise_dict={}, arff_has_ids=False, arff_has_classes=True):
        """ Main function for generating pairwise AdaBoost classifiers.
        """
        if os.path.exists(pars['pairwise_classifier_dirpath']):
            os.system('rm -Rf ' + pars['pairwise_classifier_dirpath'])
        os.system('mkdir ' + pars['pairwise_classifier_dirpath'])
        os.system('cp %s %s/' % (pars['dotastro_arff_fpath'], pars['pairwise_classifier_dirpath']))

        #pairwise_dict = self.generate_pairwise_arffbody_trainingsets(arff_has_ids=arff_has_ids,
        #                                                             arff_has_classes=arff_has_classes)
        
        ### Generate the classifiers:
        AdaboostWrapper = classifier_adaboost_wrapper.Adaboost_Wrapper(pars)
        pkl_out_dict = {}
        for pair_name, apair_dict in pairwise_dict.iteritems():
            #print pair_name
            arffbody_fpath = apair_dict['arff_fpath']

            (confid_dict, confidence_class_summary) = \
                   PairwiseClassification.generate_confidence_dict_given_pairwise_arff_fpath(arffbody_fpath)

            #print
            ### TODO: want to pass in a dict of {<some id>:<-1 to 1 confidence>}
            ###   -> this is then used by:
            (train_data, ordered_classifs_arr, cand_id_list) = \
                       AdaboostWrapper.parse_arff_add_confidences(trainingset_arff_fpath=arffbody_fpath,
                                                                  confid_dict=confid_dict,
                                                                  arff_has_ids=arff_has_ids,
                                                                  arff_has_classes=arff_has_classes)
            

            try:
                classifier_dict = AdaboostWrapper.generate_classifier(train_data=train_data,
                                                                  ordered_classifs=ordered_classifs_arr)
            except:
                print("EXCEPT: Wrapper.generate_classifier(), probably unable to find 'edge' for:", pair_name)
                continue
            classifier_dict.update(apair_dict)
            #print pair_name, classifier_dict['alphas'][:3], classifier_dict['thresholds'][:3]

            if 0:
                # # # Do a count of the most weighted/significant features use in
                #     the Adaboost classifier:
                feat_weight_dict = {}
                for i, alpha in enumerate(classifier_dict['alphas']):
                    feat_id = classifier_dict['k'][i]
                    if feat_id not in feat_weight_dict:
                        feat_weight_dict[feat_id] = 0.0
                    feat_weight_dict[feat_id] += alpha
                sort_tups = []
                for feat_id, tot_alpha in feat_weight_dict.iteritems():
                    sort_tups.append((tot_alpha, feat_id))
                sort_tups.sort(reverse=True)
                classifier_dict['top_feats'] = []
                for tot_alpha, feat_id in sort_tups[:2]:
                    classifier_dict['top_feats'].append({'tot_alpha':tot_alpha,
                                                         'feat_name':self.feat_id_names[feat_id]})

            if 1:
                # # # Determine the features with the most significant alpha (decision weight)
                #     in the Adaboost classifier:
                feat_weight_dict = {}
                for i, alpha in enumerate(classifier_dict['alphas']):
                    feat_id = classifier_dict['k'][i]
                    if feat_id not in feat_weight_dict:
                        feat_weight_dict[feat_id] = alpha
                    if alpha > feat_weight_dict[feat_id]:
                        feat_weight_dict[feat_id] = alpha
                sort_tups = []
                for feat_id, max_alpha in feat_weight_dict.iteritems():
                    sort_tups.append((max_alpha, feat_id))
                sort_tups.sort(reverse=True)
                classifier_dict['top_feats'] = []
                for tot_alpha, feat_id in sort_tups[:2]:
                    classifier_dict['top_feats'].append({'tot_alpha':tot_alpha,
                                                        'feat_name':self.feat_id_names[feat_id]})

            pkl_out_dict[pair_name] = copy.deepcopy(classifier_dict)
            #### TODO: incorperate the row's attribute ordering into the pickle, for an sanity check

            #pkl_fpath = "%s/%s.pkl" % (pars['pairwise_classifier_dirpath'], apair_dict['fname_root'])
            #AdaboostWrapper.pickle_classifier_dict(classifier_dict=classifier_dict,
            #                                       pkl_fpath=pkl_fpath)


            if 0:
                ### Try the new classifier out:
                #print pair_name, 'train_data.shape', train_data.shape, train_data[:,10] #list(train_data[4])
                normalized_preds = AdaboostWrapper.apply_classifier( \
                                                            toclassify_data=train_data,
                                                            classifier_dict=classifier_dict)
                #realbogus_list = AdaboostWrapper.convert_adaboost_preds_into_RealBogus( \
                #                                      ordered_classifs=ordered_classifs,
                #                                      normalized_preds=normalized_preds,
                #                                      cand_id_list=cand_id_list)
                #pprint.pprint(normalized_preds)
                #print

        


        pklgz_fpath = "%s/%s.pkl.gz" % (self.pars['pairwise_classifier_pklgz_dirpath'], 
                                        self.pars['pairwise_schema_name'])
        fp=gzip.open(pklgz_fpath,'wb')
        cPickle.dump(pkl_out_dict,fp,1) # ,1) means a binary pkl is used.
        fp.close()


class Pairwise_Cross_Validation_Parallel_Worker:
    """ A class which is to be used on IPython clients, do perform
    the training and classification components of 10-fold cross validation.
    
    """
    def __init__(self, pars={}):
        self.pars = pars


    def generate_node_pars(self, scratch_dirpath=''):
        """ Generate pars which are unique to a crossvalidation node.
        """
        if os.path.exists(scratch_dirpath):
            os.system("rm -Rf " + scratch_dirpath)
        train_dirpath = "%s/train" % (scratch_dirpath)
        #classifier_dirpath = "%s/class" % (scratch_dirpath)
        os.system('mkdir ' + scratch_dirpath)
        os.system('mkdir ' + train_dirpath)
        #os.system('mkdir ' + classifier_dirpath)

        pars = {}
        pars['trainset_pruned_pklgz_fpath'] = "%s/pairwise_trainset.pkl.gz" % (scratch_dirpath)
        pars['pairwise_trainingset_dirpath'] = train_dirpath
        pars['weka_pairwise_classifiers_pkl_fpath'] = "%s/pairwise_classifier.pkl.gz" % (scratch_dirpath) #classifier_dirpath
        return pars


    def do_cross_validation_element(self, cross_valid_dataset={}, i_fold=0):
        """ Do one of the cross correlation fold tasks.
        """

        PairwiseClassification = Pairwise_Classification(self.pars)
        WekaPairwiseClassification = Weka_Pairwise_Classification(pars=self.pars)
        PairwiseClassification.write_sciclass_dict_pkl(pkl_fpath=self.pars['trainset_pruned_pklgz_fpath'],
                                     sciclass_dict=cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        pairwise_dict= PairwiseClassification.generate_pairwise_trainingset_row_dict__using_pruned_taxonomy_tree(\
                                                       cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        PairwiseClassification.generate_weka_classifiers(pairwise_dict=pairwise_dict,
                                                      arff_has_ids=self.pars['arff_has_ids'],
                                                      arff_has_classes=self.pars['arff_has_classes'])
        WekaPairwiseClassification.load_weka_classifiers(classifier_dict=pairwise_dict)
        WekaPairwiseClassification.fp_cyto_nodeattrib = None
        WekaPairwiseClassification.fp_cyto_network = None
        classif_summary_dict = WekaPairwiseClassification.do_pairwise_classification( \
                                       classifier_dict=pairwise_dict,
                                  pairwise_pruned_dict=cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        return classif_summary_dict
    

    # This works for single mode:
    def do_cross_validation_element__backup(self, cross_valid_dataset={}, i_fold=0):
        """ Do one of the cross correlation fold tasks.
        """

        PairwiseClassification = Pairwise_Classification(self.pars)
        WekaPairwiseClassification = Weka_Pairwise_Classification(pars=self.pars)

        PairwiseClassification.write_sciclass_dict_pkl(pkl_fpath=self.pars['trainset_pruned_pklgz_fpath'],
                                     sciclass_dict=cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        # # # pruned_sciclass_dict = cross_valid_dataset['crossval_data_dict'][0]['train']


        #pairwise_dict = self.generate_pairwise_trainingset_row_dict(arff_sciclass_dict)
        pairwise_dict= PairwiseClassification.generate_pairwise_trainingset_row_dict__using_pruned_taxonomy_tree(\
                                                       cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        #return {'pruned_sciclass_dict':pruned_sciclass_dict, # This is the reference, pruned, arff sciclass dict
        #        'pairwise_dict':pairwise_dict}  # this is a pairwise trainingset row_dict

        PairwiseClassification.generate_weka_classifiers(pairwise_dict=pairwise_dict,
                                                        arff_has_ids=arff_has_ids,
                                                        arff_has_classes=arff_has_classes)
        WekaPairwiseClassification.load_weka_classifiers(classifier_dict=pairwise_dict)
        WekaPairwiseClassification.fp_cyto_nodeattrib = None
        WekaPairwiseClassification.fp_cyto_network = None
        classif_summary_dict = WekaPairwiseClassification.do_pairwise_classification( \
                                       classifier_dict=pairwise_dict,
                                  pairwise_pruned_dict=cross_valid_dataset['crossval_data_dict'][i_fold]['train'])
        #self.write_confusionmatrix_heatmap_html(classif_summary_dict,
        #                                        html_fpath=self.pars['confusion_stats_html_fpath'],
        #                                        debosscher_confusion_data=debosscher_confusion_data)


        # # # # TODO: might want to Ipython push / pull this dictionary out:
        return classif_summary_dict


if __name__ == '__main__':
    options = parse_options()
    #'dotastro_arff_fpath':os.path.expandvars('$HOME/scratch/dotastro_sources_3src_or_more_20091123.arff'),
    #'dotastro_arff_fpath':os.path.expandvars('$HOME/Dropbox/work/20100524_xmlarffs_4312_includes_nonfold_3src_nocomboband_added_2percentile/train_output_20100517_dotastro_xml_with_features_removed_sdss.arff'),
    pars = {'num_percent_epoch_error_iterations':2, # !!! NOTE: This must be the same in analysis_deboss_tcp_source_compare.py:pars[]
            'crossvalid_nfolds':10, # None == use n_folds equal to the minimum number of sources for a science class.  If this number is > 10, then n_folds is set to 10
            'crossvalid_do_stratified':False, # False: randomly sample sources for each fold, True: exclude a fold group of sources which is not excluded in the other folds.
            'crossvalid_fold_percent':40., #NOTE: only valid if do_stratified=False  #float x in x/y OR None==just use the percent 1/nfolds
            'tcp_hostname':'192.168.1.25',
            'tcp_username':'pteluser',
            'tcp_port':     3306, 
            'tcp_database':'source_test_db',
            'dotastro_arff_fpath':os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features__default.arff'),#os.path.expandvars('$HOME/scratch/train_output_20100517_dotastro_xml_with_features.arff'),
            'arff_sciclass_dict_pkl_fpath':os.path.expandvars('$HOME/scratch/arff_sciclass_dict.pkl'),
            'trainset_pruned_pklgz_fpath':os.path.expandvars('$HOME/scratch/trainset_pruned.pkl.gz'),
            'pruned_classif_summary_stats_pkl_fpath': \
                                 os.path.expandvars('$HOME/scratch/pruned_classif_summary_stats.pkl'),
            'weka_pairwise_classifiers_pkl_fpath': \
                                  os.path.expandvars('$HOME/scratch/weka_pairwise_classifiers_pkl_fpath.pkl'),
            'pairwise_trainingset_dirpath':os.path.expandvars('$HOME/scratch/pairwise_trainingsets'),
            'pairwise_classifier_dirpath':os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'pairwise_classifier_pklgz_dirpath':os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'pairwise_scratch_dirpath':'/media/raid_0/pairwise_scratch',
            'classification_summary_pklgz_fpath':'',#os.path.expandvars('$HOME/scratch/pairwise_classifiers'),
            'confusion_stats_html_fpath':os.path.expandvars('$HOME/Dropbox/Public/work/pairwise_confusion_matrix.html'),
            'cyto_work_final_fpath':'/home/pteluser/Dropbox/work/',
            'cyto_network_fname':'pairwise_class.cyto.network',
            'cyto_nodeattrib_fname':'pairwise_class.cyto.nodeattrib',
            'pairwise_schema_name':'noprune', # represents how the class heirarchy pruning was done.
            't_sleep':0.2,
            'number_threads':13, # on transx : 10
            'min_num_sources_for_pairwise_class_inclusion':6,
            #'feat_dist_image_fpath':"/home/pteluser/Dropbox/Public/work/feat_distribution.png",#OBSOLETE
            #'feat_dist_image_url':"http://dl.dropbox.com/u/4221040/work/feat_distribution.png",#OBSOLETE
            'feat_dist_image_local_dirpath':'/media/raid_0/pairwise_scratch/pairwise_scp_data',#"/home/pteluser/scratch/pairwise_scp_data",
            'feat_dist_image_remote_scp_str':"pteluser@192.168.1.103:Sites/pairwise_images/",
            'feat_dist_image_rooturl':"http://lyra.berkeley.edu/~jbloom/dstarr/pairwise_images",
            'feat_distrib_classes':{'target_class':'lboo',#adding anything here is OBSOLETE
                                    'comparison_classes':['pvsg', 'gd', 'ds']},#adding anything here is OBSOLETE
            'plot_symb':['o','s','v','d','<'], # ,'+','x','.', ,'>','^'
            'feat_distrib_colors':['#000000',
                                   '#ff3366',
                                   '#660000',
                                   '#aa0000',
                                   '#ff0000',
                                   '#ff6600',
                                   '#996600',
                                   '#cc9900',
                                   '#ffff00',
                                   '#ffcc33',
                                   '#ffff99',
                                   '#99ff99',
                                   '#666600',
                                   '#99cc00',
                                   '#00cc00',
                                   '#006600',
                                   '#339966',
                                   '#33ff99',
                                   '#006666',
                                   '#66ffff',
                                   '#0066ff',
                                   '#0000cc',
                                   '#660099',
                                   '#993366',
                                   '#ff99ff',
                                   '#440044'],
            #'feat_distrib_colors':['b','g','r','c','m','y','k','0.25','0.5','0.75', (0.5,0,0), (0,0.5,0), (0,0,0.5), (0.75,0,0), (0,0.75,0), (0,0,0.75), (0.25,0,0), (0,0.25,0), (0,0,0.25), '#eeefff', '#bbbfff', '#888fff', '#555fff', '#000fff', '#000aaa', '#fffaaa'],
            'taxonomy_prune_defs':{
                     'terminating_classes':['be', 'bc', 'sreg', 'rr-lyr', 'c', 'bly', 'sne','nov']},
            'debosscher_confusion_table3_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/debosscher_table3.html'),
            'debosscher_confusion_table4_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/debosscher_table4.html'),
            'debosscher_class_lookup':{ \
                'BCEP':'bc',    
                'BE':'be', #NO LCs   # Pulsating Be-stars  (57) : HIP, GENEVA
                'CLCEP':'dc',
                'CP':'CP',
                'CV':'cv', #NO LCs   # Cataclysmic variables (3) : ULTRACAM
                'DAV':'pwd', #NO LCs # Pulsating DA white dwarfs (2) : WET
                'DBV':'pwd', #NO LCs # Pulsating DB white dwarfs (1) : WET / CFHT
                'DMCEP':'cm',
                'DSCUT':'ds',
                'EA':'alg',
                'EB':'bly',
                'ELL':'ell',
                'EW':'wu',
                'FUORI':'fuor', #NO LCs # FU-Ori stars (3) : ROTOR
                'GDOR':'gd',
                'GWVIR':'gw', #NO LCs # GW-Virginis stars (2) : CFHT
                'HAEBE':'haebe',
                'LBOO':'lboo',
                'LBV':'sdorad',
                'MIRA':'mira',
                'PTCEP':'piic',
                'PVSG':'pvsg', # Periodically variable supergiants (76) : HIP, GENEVA, ESO
                'ROAP':'rot', #NO LCs # Rapidly oscillationg Ap stars (4) : WET/ESO # 13587 is given class_id='rot' in Dotastro, but the dotastro projectclass is 'Rapidly Osc Ap stars'.
                'RRAB':'rr-ab',
                'RRC':'rr-c',
                'RRD':'rr-d',
                'RVTAU':'rv',
                'SDBV':'sdbv', #NO LCs # Pulsating subdwarf B stars (16) : ULTRACAM
                'SLR':'NOTMATCHED',  # NOT in projid=122 # NOT MATCHED  Solar-like oscillations in red giants (1) : MOST
                'SPB':'spb',   # Slowly-pulsating B stars (47) : HIP / GENEVA, MOST
                'SR':'sreg',
                'SXPHE':'sx',        ### NOT in current Debosscher confusion matrix
                'TTAU':'tt',
                'WR':'wr',
                'XB':'xrbin',        ### NOT in current Debosscher confusion matrix
                },
            }
            # Pre 20100501:         'terminating_classes':['ev', 'wr', 'be', 'puls', 'mira', 'gd', 'bc', 'ds', 'sreg', 'piic', 'rr-lyr', 'c', 'alg', 'bly', 'sne','nov']},

    pars['feat_dist_plots'] = options.feat_dist_plots
    if len(options.arff_fpath) > 0:
        pars['dotastro_arff_fpath'] = os.path.expandvars(os.path.expanduser(options.arff_fpath))
    if len(options.classifier_dir) > 0:
        classifier_dir = os.path.expandvars(os.path.expanduser(options.classifier_dir))
        if not os.path.exists(classifier_dir):
            os.system("mkdir -p " + classifier_dir)
        pars['weka_pairwise_classifiers_pkl_fpath'] = "%s/weka_pairwise_classifier.pkl" % (classifier_dir)
        pars['cyto_work_final_fpath'] = classifier_dir
    if (len(options.result_name) > 0) and (len(options.classifier_dir) > 0):
        pars['trainset_pruned_pklgz_fpath'] = "%s/%s.pkl.gz" % (classifier_dir, options.result_name)
        pars['crossvalid_pklgz_fpath'] = "%s/%s__crossvalid_data.pkl.gz" % (classifier_dir, options.result_name)
        pars['confusion_stats_html_fpath'] = "%s/%s_classif_stats.html" % (classifier_dir, options.result_name)
        pars['classification_summary_pklgz_fpath'] = "%s/%s_classification_summary.pkl.gz" % (classifier_dir, options.result_name)

    arff_has_ids=False
    pars['arff_has_ids']=False
    if options.arffrow_has_ids:
        arff_has_ids=True
        pars['arff_has_ids']=True

    arff_has_classes=True
    pars['arff_has_classes']=True
    if options.arffrow_has_no_classes:
        arff_has_classes=False
        pars['arff_has_classes']=False

    #if len(sys.argv) == 2:
    if 1:
        pars['debosscher_classes'] = options.debosscher_classes
        #if options.debosscher_classes:
        #    ### Debosscher Classes case
        #    pars['taxonomy_prune_defs']['terminating_classes'] = [] # So we keep all of the original classes

        if options.generate_weka:
            PairwiseClassification = Pairwise_Classification(pars)
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            pairwise_dict = a_dict['pairwise_dict']
            PairwiseClassification.generate_weka_classifiers(pairwise_dict=pairwise_dict,
                                                        arff_has_ids=arff_has_ids,
                                                        arff_has_classes=arff_has_classes)            
        elif options.deboss_percentage_exclude_analysis:
            WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)
            #WekaPairwiseClassification.main_deboss_percentage_exclude_analysis()
            WekaPairwiseClassification.ipython_master__deboss_percentage_exclude_analysis()
        elif options.test_weka:
            WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)
            WekaPairwiseClassification.main()
        elif options.debosscher_classes:
            WekaPairwiseClassification = Weka_Pairwise_Classification(pars=pars)
            WekaPairwiseClassification.debosscher_main()

        elif options.make_scidict_pkl_using_arff:
            PairwiseClassification = Pairwise_Classification(pars)
            arff_sciclass_dict = PairwiseClassification.parse_arff( \
                                   arff_has_ids=arff_has_ids, arff_has_classes=arff_has_classes, \
                                   has_srcid=True)
            pruned_sciclass_dict = PairwiseClassification.condense_taxonomy_of_sciclassdict(arff_sciclass_dict)
            PairwiseClassification.write_sciclass_dict_pkl(pkl_fpath=pars['trainset_pruned_pklgz_fpath'],
                                                           sciclass_dict=pruned_sciclass_dict)
            
        elif options.generate:
            PairwiseClassification = Pairwise_Classification(pars)
            a_dict = PairwiseClassification.generate_pairwise_arffbody_trainingsets( \
                                         arff_has_ids=arff_has_ids,
                                         arff_has_classes=arff_has_classes,
                                         has_srcid=True)
            pruned_sciclass_dict = a_dict['pruned_sciclass_dict']
            pairwise_dict = a_dict['pairwise_dict']
            PairwiseClassification.generate_classifiers(pairwise_dict=pairwise_dict,
                                                        arff_has_ids=arff_has_ids,
                                                        arff_has_classes=arff_has_classes)
        elif options.test:
            TestExample = Test_Example(pars=pars)
            TestExample.main()

    else:
        #elif len(sys.argv) < 2:
        ### MORE OBSOLETE:

        AdaboostWrapper = classifier_adaboost_wrapper.Adaboost_Wrapper(pars)

        #####
        pklgz_fpath = "%s/%s.pkl.gz" % (pars['pairwise_classifier_pklgz_dirpath'], 
                                        pars['pairwise_schema_name'])
        fp=gzip.open(pklgz_fpath,'rb')
        pairwise_schema_dict=cPickle.load(fp)
        fp.close()
        #####

        lines = sys.stdin
        for line in lines:
            #elems = line.strip().split(';')
            elems = line.strip().split()
            if len(elems) == 0:
                continue
            line_id = elems[0]
            pkl_fname = elems[1]
            src_id = elems[2]
            arff_row = elems[3]

            pair_name = pkl_fname[:pkl_fname.rfind('.')]
            classifier_dict = pairwise_schema_dict[pair_name]

            feat_values = arff_row.split(',')
            num_list = []

            for elem in feat_values:
                if elem == 't':
                    num_list.append([1])
                elif elem == 'f':
                    num_list.append([0])
                elif elem == '?':
                    num_list.append([numpy.NaN])
                else:
                    num_list.append([float(elem)])

            train_data = numpy.array(num_list)
            #train_data = train_data.T # want: (29, 574) similar shape

            normalized_preds = AdaboostWrapper.apply_classifier( \
                                                            toclassify_data=train_data,
                                                            classifier_dict=classifier_dict)
            
            if normalized_preds[0] < 0:
                sciclass_pred = classifier_dict['classname_tup'][0]
            else:
                sciclass_pred = classifier_dict['classname_tup'][1]

            confidence = numpy.abs(normalized_preds[0])
            print("%s;%s;%lf;%s" % (src_id, sciclass_pred, confidence, classifier_dict['fname_root']))

        ### echo "Microlensing_Event___Type_Ia_Supernovae.pkl;1234567;2.162,2.0,0.0053282182438,2.55090195635,0.702928248516,0.188299399184,0.0853351581732,0.306187780088,0.205958893895,0.216289555174,0.0053282182438,-0.124394776891,23.3580520327,0.00367702648004,-0.904973211272,6.05564055936,0.0350294994587,2.80813223337,5.27392523503,-2.23428210218,-2.86580747521,0.349652335223,2.69069983158,0.31463106821,1.69707408596,3.48520407775,7.83568496402,2.75038673891,0.0053282182438,0.39160330964,0.0665352511945,0.0607257947202,0.0406020944045,0.0053282182438,0.439950111808,37.7034063201,-0.22184590449,-0.515693283073,7.97774524672,0.447686493506,1.7921955914,1.34471480133,0.180273221282,1.39787119835,1.48542920427,-1.54289099897,1.41100587329,0.17488709034,0.169280134169,0.32265377148,2.01871518912,0.0539946935208,0.0184983669692,0.00152904572163,0.00246177414402,0.00351218024472,0.0539946935208,0.65646684733,3.3519012806,0.38221127332,-2.09925632409,17.6179404532,14.6861040649,57.6000889149,0.127980248486,0.181313917301,1.67435402877,1.58195296201,2.01890019525,1.20891221146,9.28586368803,4.47649040333,3.14714961224,0.315492615375,0.0053282182438,0.0,25.0,0.333333333333,-0.402873531426,57697.7027284" | ./pairwise_classification.py 

