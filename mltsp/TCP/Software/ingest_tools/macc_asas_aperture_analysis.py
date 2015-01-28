#!/usr/bin/env python
""" MACC catalog paper aperture analysis script
 - Analyze feature changes for all 50k ASAS ACVS sources, 
   when slightly larger and smaller apertures are used instead.

This parses arff files which have been generated from ASAS .dat files 
     using starvars_feature_generation.py:IPython_Parallel_processing.main()

"""
import sys, os
import numpy

class Macc_Asas_Aperture_Analysis:
    """
    """
    def __init__(self, pars={}):
        self.pars = pars


    def summarize_feats(self, orig_dict={}, orig_srcid_dict={}, perturb_srcid_dict={}, perturb_dict={}):
        """
        """
        orig_aper_dict = orig_dict
        small_srcid_dict = perturb_srcid_dict
        small_aper_dict = perturb_dict

        orig_small_delta = {}
        for feat_name in orig_aper_dict['featname_longfeatval_dict'].keys():
            if feat_name in self.pars['feature_skip_list']:
                continue
            orig_small_delta[feat_name] = []

        for feat_name in orig_small_delta.keys():
            for i, srcid in enumerate(orig_aper_dict['srcid_list']):
                #if orig_aper_dict['featname_longfeatval_dict'][feat_name][i] == None:
                #    print feat_name
                #    break
                delta = orig_aper_dict['featname_longfeatval_dict'][feat_name][i] - \
                            small_aper_dict['featname_longfeatval_dict'][feat_name][ \
                                                              small_srcid_dict[srcid]]

                orig_small_delta[feat_name].append(delta)
                #if delta == 0:
                #    orig_small_delta[feat_name].append(0.0)
                #elif orig_aper_dict['featname_longfeatval_dict'][feat_name][i] == 0:
                #    orig_small_delta[feat_name].append(1.0)
                #else:
                #    orig_small_delta[feat_name].append(delta/float(orig_aper_dict['featname_longfeatval_dict'][feat_name][i]))

        #sort_feat_names = orig_small_delta.keys()
        #sort_feat_names.sort()
        #for feat_name in sort_feat_names:
        #    print "ABS: mean=%0.3lf std=%0.3lf\tRAW: mean=%0.3lf std=%0.3lf\t%s" % ( \
        #                    numpy.mean(numpy.abs(numpy.array(orig_small_delta[feat_name]))),
        #                    numpy.std(numpy.abs(numpy.array(orig_small_delta[feat_name]))),
        #                    numpy.mean(numpy.array(orig_small_delta[feat_name])),
        #                    numpy.std(numpy.array(orig_small_delta[feat_name])),
        #                    feat_name)

        tups_list = []
        for feat_name in orig_small_delta.keys():
            tups_list.append((numpy.mean(numpy.abs(numpy.array(orig_small_delta[feat_name]))),
                              numpy.mean(numpy.abs(numpy.array(orig_small_delta[feat_name]))),
                              numpy.std(numpy.abs(numpy.array(orig_small_delta[feat_name]))),
                              feat_name))
        tups_list.sort(reverse=True)
        for (i_sort, a, b, name) in tups_list:
            print "ABS: mean=%0.3lf std=%0.3lf\t%s" % (a, b, name)

    def subselect_1000_sources(self):
        """ Just for taking aperture perturbed sources and subselecting 1000 random sources.
        
        """

        smalleraper_fpath = "/home/dstarr/scratch/macc_aperture_analysis/combined_acvs_smalleraper.arff"
        smalleraper_subset_fpath = "/home/dstarr/scratch/macc_aperture_analysis/combined_acvs_smalleraper_1000.arff"
        largeraper_fpath = "/home/dstarr/scratch/macc_aperture_analysis/combined_acvs_largeraper.arff"
        largeraper_subset_fpath = "/home/dstarr/scratch/macc_aperture_analysis/combined_acvs_largeraper_1000.arff"

        source_dict = {}
        lines = open(smalleraper_fpath).readlines()
        for i,l in enumerate(lines):
            if len(l) == 0:
                continue
            elif ((l[0] == '%') or (l[0] == '@')):
                if '@data' in l:
                    i_data = i+1
                continue
            source_name = l.split(',')[0]
            source_dict[source_name] = i

        import numpy
        src_shuff = numpy.array(source_dict.keys())
        numpy.random.shuffle(src_shuff)
        src_subset = src_shuff[:1000]

        new_lines = lines[0:i_data]
        for src_name in src_subset:
            new_lines.append(lines[source_dict[src_name]])
        out_str = ''.join(new_lines)
        fp = open(smalleraper_subset_fpath,'w')
        fp.write(out_str)
        fp.close()
        
        ###
        source_dict = {}
        lines = open(largeraper_fpath).readlines()
        for i,l in enumerate(lines):
            if len(l) == 0:
                continue
            elif ((l[0] == '%') or (l[0] == '@')):
                if '@data' in l:
                    i_data = i+1
                continue
            source_name = l.split(',')[0]
            source_dict[source_name] = i
        
        new_lines = lines[0:i_data]
        for src_name in src_subset:
            new_lines.append(lines[source_dict[src_name]])
        out_str = ''.join(new_lines)
        fp = open(largeraper_subset_fpath,'w')
        fp.write(out_str)
        fp.close()
        import pdb; pdb.set_trace()
        print
        

    def main(self):

        algo_code_dirpath = os.path.abspath(os.environ.get("TCP_DIR")+'Algorithms')
        sys.path.append(algo_code_dirpath)
        import rpy2_classifiers

        self.rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algo_code_dirpath)

        
        arff_str = open(self.pars['orig_aper_arff']).read()
        orig_aper_dict = self.rc.parse_full_arff(arff_str=arff_str,
                                                 skip_missingval_lines=False)
        orig_srcid_dict = {}
        for i, srcid in enumerate(orig_aper_dict['srcid_list']):
            orig_srcid_dict[srcid] = i

        arff_str = open(self.pars['small_aper_arff']).read()
        small_aper_dict = self.rc.parse_full_arff(arff_str=arff_str,
                                                 skip_missingval_lines=False)
        small_srcid_dict = {}
        for i, srcid in enumerate(small_aper_dict['srcid_list']):
            small_srcid_dict[srcid] = i

        arff_str = open(self.pars['large_aper_arff']).read()
        large_aper_dict = self.rc.parse_full_arff(arff_str=arff_str,
                                                 skip_missingval_lines=False)
        large_srcid_dict = {}
        for i, srcid in enumerate(large_aper_dict['srcid_list']):
            large_srcid_dict[srcid] = i

        #self.summarize_feats(orig_dict=orig_aper_dict,
        #                     orig_srcid_dict=orig_srcid_dict,
        #                     perturb_dict=small_aper_dict,
        #                     perturb_srcid_dict=small_srcid_dict)

        self.summarize_feats(orig_dict=orig_aper_dict,
                             orig_srcid_dict=orig_srcid_dict,
                             perturb_dict=large_aper_dict,
                             perturb_srcid_dict=large_srcid_dict)

        import pdb; pdb.set_trace()
        print
        # TODO: do for large aper
        # TODO: visualize deltas somehow for large and small delta apertures


if __name__ == '__main__':

    pars = { \
        'feature_skip_list':['color_diff_rj',
                             'color_bv_extinction',
                             'color_diff_bj',
                             'color_diff_jh',
                             'color_diff_hk',
                             'color_diff_vj'],
        'orig_aper_arff':'/global/home/users/dstarr/500GB/acvs_50k_raw/combined_acvs_orig.arff',
        'small_aper_arff':'/global/home/users/dstarr/500GB/acvs_50k_raw/combined_acvs_smalleraper.arff',
        'large_aper_arff':'/global/home/users/dstarr/500GB/acvs_50k_raw/combined_acvs_largeraper.arff',
        }

    maaa = Macc_Asas_Aperture_Analysis(pars=pars)

    maaa.subselect_1000_sources()
    maaa.main()
