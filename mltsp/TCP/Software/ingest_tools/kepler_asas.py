#!/usr/bin/env python
"""

/usr/lib/python2.7/pdb.py kepler_asas.py

wget http://www.astro.uni.wroc.pl/ldb/asas/Table_1.txt

"""
from __future__ import print_function
from __future__ import absolute_import

import os, sys
import urllib2
from BeautifulSoup import BeautifulSoup
import subprocess
import urllib
import numpy

def load_csv_into_data_dict(fpath='', delimiter=',', comments='#'):
    """
    NOTE: we make assumption that the first commented out line contains column names

    """
    column_names = []
    column_types = []
    data_lists = []
    i_first_data_row = 0 # This will be updated

    column_names = ['No', 'ID', 'ASAS_ID_V', 'ASAS_ID_I', '2MASS_ID', 'RAd', 'DEC', 'V', 'I', 'V-I', 'J', 'J-H', 'H-K', 'Type', 'Period', 'V_amp', 'I_amp', 'Crossid']
    column_types = [int, str, str, str, str, float, float, float, float, float, float, float, float, str, float, float, float, str]
    data_dict = {}
    for i, column_name in enumerate(column_names):
        data_dict[column_name] = []

    with open(fpath, 'rb') as csvfile:
        for i, row in enumerate(csvfile.readlines()):
            if i == 0:
                continue
            #if i == 6:
            #    import pdb; pdb.set_trace()
            #    print
                
            elems = row.split()
            #for j, val in enumerate(elems):
            for j, val in enumerate(column_names):
                if len(elems) == j:
                    data_dict['Crossid'].append('')
                    continue # no comments
                elif j == (len(column_names) - 1):
                    #elif j > len(column_names):
                    # comments column
                    #import pdb; pdb.set_trace()
                    #print
                    val = ' '.join(elems[j:])
                else:
                    val = elems[j]
                if val == "N/A":
                    data_dict[column_names[j]].append(None)
                else:
                    data_dict[column_names[j]].append(column_types[j](val))
    #import pprint
    #pprint.pprint(data_dict)

    asasid_to_index = {}
    for i, id_name in enumerate(data_dict['ID']):
        asasid_to_index[id_name] = i

    out_dict = {'data_dict':data_dict,
                'types':column_types,
                'names':column_names,
                'asasid_to_index':asasid_to_index}
    return out_dict


def get_file_from_url(dirpath, url_modifier, asas_id):
    fpath = "{dir}/{asas_id}".format(
        asas_id=asas_id,
        dir=dirpath)
    f_size = 0
    if os.path.exists(fpath):
        f_size = os.stat(fpath).st_size
    while f_size < 10:
        
        url = "http://www.astro.uni.wroc.pl/ldb/asas/{url_modifier}/{asas_id}".format(
            asas_id=asas_id,
            dir=dirpath,
            url_modifier=url_modifier)
        data_str = urllib.urlopen(url).read()
        fp = open(fpath, 'w')
        fp.write(data_str)
        fp.close()
        f_size = os.stat(fpath).st_size
        print("Got:", asas_id)
    

def retrieve_ts_data(out_dict, asas_v_dirpath='', asas_i_dirpath=''):
    """ Retrieve the timeseries data from the kepler asas website.

    http://www.astro.uni.wroc.pl/ldb/asas/183952+4323.1.html
    http://www.astro.uni.wroc.pl/ldb/asas/lcv/183952+4323.1
    http://www.astro.uni.wroc.pl/ldb/asas/lci/183953+4323.2
    """
    if not os.path.exists(asas_v_dirpath):
        os.mkdir(asas_v_dirpath)
    if not os.path.exists(asas_i_dirpath):
        os.mkdir(asas_i_dirpath)

    for i, asas_id in enumerate(out_dict['data_dict']['ID']):
        ### V:
        try:
            get_file_from_url(asas_v_dirpath, 'lcv',
                          out_dict['data_dict']['ASAS_ID_V'][i])
        except:
            print("EXCEPT: V", asas_id)

        ### I:
        try:
            get_file_from_url(asas_i_dirpath, 'lci',
                          out_dict['data_dict']['ASAS_ID_I'][i])
        except:
            print("EXCEPT: I", asas_id)

    import pdb; pdb.set_trace()
    print()


def retrieve_nomad_color_files(data_dict={}, pars={}):
    """
    """
    all_source_dict = {'srcid_list':data_dict['data_dict']['ASAS_ID_V'],
                       'ra_list':data_dict['data_dict']['RAd'],
                       'dec_list':data_dict['data_dict']['DEC'],
                       'objids':data_dict['data_dict']['No']}

    from . import nomad_colors_assoc_activelearn
    nomad_data_cache_dirpath = '/home/dstarr/scratch/nomad_cache_asas_kepler'

    pars = {}
    anf = nomad_colors_assoc_activelearn.Analyze_Nomad_Features(pars=pars)
    sources_dict = anf.retrieve_nomad_for_asas_kepler_sources( \
                          all_source_dict=all_source_dict,
                          nomad_data_cache_dirpath=nomad_data_cache_dirpath,
                          nomad_radius=60, # 60
                          nomad_n_results=20,
                          return_outdict=True,
        pars=pars)
    return sources_dict
    
    # todo: need to fill the srcid list for kepler asas sources., then make a new function for kepler asas in starvars_feature_generation.py and revert the older function: generate_arff_using_asasdat()


def classify_best_nomad_sources(nomad_sources={}, asas_data_dict={}, pars={}):
    """ Adapted from get_colors_for_tutor_sources.py:generate_nomad_tutor_source_associations()
    """
    from . import get_colors_for_tutor_sources
    gc = get_colors_for_tutor_sources.Get_Colors_Using_Nomad(pars=pars)
    best_nomad_sources = gc.generate_nomad_source_associations_without_tutor(nomad_sources=nomad_sources, asas_data_dict=asas_data_dict)
    gc.update_bestnomad_list_file(best_nomad_lists=best_nomad_sources, projid=0)
    ### Now has been updated: /home/dstarr/src/TCP/Data/best_nomad_src_for_asas_kepler


def remove_sources_with_many_missing_attribs(data_dict, exclude_feats=['freq_signif']):
    """ Excludes sources which have many missing feature values.

    Intended to be used for datasets which may have sparse sources and
    thus no frequency based features found.  These sources need to be
    excluded before missing feature imputation is done (primarily for
    color features).
    """
    import numpy
    exclude_src_i_list = []
    for exclude_feat in exclude_feats:
        for i, val in enumerate(data_dict['featname_longfeatval_dict'][exclude_feat]):
            if ((val is None) or (val == numpy.nan)):
                exclude_src_i_list.append(i)
    exclude_src_i_set = set(exclude_src_i_list)

    new_featname_longfeatval_dict = {}
    for feat_name, feat_longlist in data_dict['featname_longfeatval_dict'].iteritems():
        new_list = []
        for i,val in enumerate(feat_longlist):
            if i in exclude_src_i_set:
                continue # skip this source
            else:
                new_list.append(val)
        new_featname_longfeatval_dict[feat_name] = new_list
    data_dict['featname_longfeatval_dict'] = new_featname_longfeatval_dict

    new_list = []
    for i, srcid in enumerate(data_dict['srcid_list']):
        if i in exclude_src_i_set:
            continue # skip this source
        else:
            new_list.append(srcid)
    data_dict['srcid_list'] = new_list
    print("Removed %d sources with few useful features" % (len(exclude_src_i_set)))

        
    



if __name__ == '__main__':



    #asas_v_dirpath = "/home/dstarr/armitage/src/kepler_asas/asas_v_data"
    #asas_i_dirpath = "/home/dstarr/armitage/src/kepler_asas/asas_i_data"
    #fpath = "/home/dstarr/armitage/src/kepler_asas/Table_1.txt"
    asas_v_dirpath = "/home/dstarr/Data/kepler_asas_947/asas_v_data"
    asas_i_dirpath = "/home/dstarr/Data/kepler_asas_947/asas_i_data"
    fpath = "/home/dstarr/Data/kepler_asas_947/Table_1.txt"
    asas_data_dict = load_csv_into_data_dict(fpath=fpath, delimiter=" ", comments="#")

    pars={'fpath_train_withsrcid':'/home/dstarr/scratch/kepler_asas_scratch/train_withsrcid',
          'fpath_train_no_srcid':'/home/dstarr/scratch/kepler_asas_scratch/train_no_srcid',
          'fpath_test_withsrcid':'/home/dstarr/scratch/kepler_asas_scratch/test_withsrcid',
          'fpath_test_no_srcid':'/home/dstarr/scratch/kepler_asas_scratch/no_srcid',
          'best_nomad_src_list_fpath':'/home/dstarr/src/TCP/Data/best_nomad_src_for_asas_kepler',
          'best_nomad_src_pickle_fpath':'/home/dstarr/src/TCP/Data/best_nomad_src_for_asas_kepler.pkl',
          }


    if 0:
        ### Initial retrieval of Kepler / ASAS timeseries data files:
        retrieve_ts_data(out_dict,
                         asas_v_dirpath=asas_v_dirpath,
                         asas_i_dirpath=asas_i_dirpath)

    if 0:
        ### Now for the retrieval of NOMAD colors and generation of features / .arff

        try:
            os.remove(pars['best_nomad_src_list_fpath'])
        except:
            pass

        nomad_sources = retrieve_nomad_color_files(data_dict=asas_data_dict, pars=pars)

        ### This updates NOMAD file: /home/dstarr/src/TCP/Data/best_nomad_src_for_asas_kepler
        classify_best_nomad_sources(nomad_sources=nomad_sources, asas_data_dict=asas_data_dict, pars=pars)

        import pdb; pdb.set_trace()
        print()

    ### NEXT step is to use
    ### starvars_feature_generation.py::ipp.main_ipython13() to
    ### generate a .arff which uses these nomad colors.
    ###
    ### NOTE: Make sure to *RESTART* the ipython server after code
    ###       changes, to ensure generated .arff is unique.
    ###
    ### Specify the nomad color file, referenced in
    ###     starvars_feature_generation.py, in function:
    ###   Parse_Nomad_Colors_List(fpath='/home/dstarr/src/TCP/Data/best_nomad_src_for_asas_kepler')
        

    if 1:
        ### Do imputation of missing-value colors:
        #  - some of this is adapted from lcs_classif.py
        #    TODO use a larger ASAS 50K dataset so that imputation has more classes to draw from

        ### features to ignore in the testing data:
        # NOTE: it doesnt seem that excluding these affects the MACC classifier classification
        ignore_feats_list = ["ar_is_theta",
                             "ar_is_sigma",
                             "delta_phase_2minima",
                             "gskew",
                             "lcmodel_median_n_per_day",
                             "lcmodel_neg_n_per_day",
                             "lcmodel_pos_area_ratio",
                             "lcmodel_pos_mag_ratio",
                             "lcmodel_pos_n_per_day",
                             "lcmodel_pos_n_ratio",
                             "phase_dispersion_freq0",
                             "freq1_harmonics_rel_phase_0",
                             "freq2_harmonics_rel_phase_0",
                             "freq3_harmonics_rel_phase_0",
                             "ratio_PDM_LS_freq0",
                             "n_points",
                             #"color_bv_extinction",
                             #"color_diff_bj",
                             #"color_diff_hk",
                             #"color_diff_jh",
                             #"color_diff_rj",
                             #"color_diff_vj",
                             ]



        pars['arff_fpath'] = '/home/dstarr/Data/starvars/combined_acvs.arff'
        skip_missingval_lines = False # this is False in lcs_classify # we skip sources which have missing values
        mtry = 5
        ntree = 10 # 100 has little difference from 10

        test_arff_str = open(pars['arff_fpath']).read()

        algo_code_dirpath = os.path.abspath(os.environ.get("TCP_DIR")+'Algorithms')
        sys.path.append(algo_code_dirpath)
        import rpy2_classifiers
        
        tmp_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

        rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algo_code_dirpath)
        sys.stdout.close()
        sys.stdout = tmp_stdout

        testdata_dict = rc.parse_full_arff(arff_str=test_arff_str, skip_missingval_lines=skip_missingval_lines)
        remove_sources_with_many_missing_attribs(testdata_dict, exclude_feats=['freq_signif'])

        # KLUDGEY conversion of missing-value features None into numpy.nan:
        new_featname_longfeatval_dict = {}
        for feat_name, feat_longlist in testdata_dict['featname_longfeatval_dict'].iteritems():
            new_list = []
            if feat_name in ignore_feats_list:
                continue # skip the features in the Ignore_feats_list for use in imputation and classification
            for val in feat_longlist:
                if val is None:
                    new_list.append(numpy.nan)
                else:
                    new_list.append(val)
            new_featname_longfeatval_dict[feat_name] = new_list
        testdata_dict['featname_longfeatval_dict'] = new_featname_longfeatval_dict
        new_features_r_data = rc.imputation_using_missForest(testdata_dict['featname_longfeatval_dict'],
                                                             mtry=mtry, ntree=ntree)
        testdata_dict['featname_longfeatval_dict'] = new_features_r_data
                             
        classifier_dict = rc.read_randomForest_classifier_into_dict(r_name='rf.tr',
                                                         r_classifier_fpath="/home/dstarr/scratch/macc_wrapper_rfclfr.rdat")
        #                                                 r_classifier_fpath="/Data/dstarr/src/ASASCatalog/data/asas_randomForest.Rdat")

        classif_results = rc.apply_randomforest__simple_output(classifier_dict=classifier_dict,
                                                data_dict=testdata_dict,
                                                #do_ignore_NA_features=do_ignore_NA_features,
                                                return_prediction_probs=True,
                                                ignore_feats=ignore_feats_list)
        #final_dict = {}
        #  form:     [(236518, 0, 0.36299999999999999, 'b. Semireg PV'), ...
        for tup in classif_results['predictions']['tups']:
            #final_dict[tup[3]] = tup[2]
            if ((tup[1] == 0) or (tup[1] == 1)):
                print(tup[0], tup[1], tup[3], '\t', tup[2])
        import pdb; pdb.set_trace()
        print()


