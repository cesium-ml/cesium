#!/usr/bin/env python 
"""
   v0.1 Summarize all feature extractors.
   
"""
import os, sys
import copy

sys.path.append(os.environ.get("TCP_DIR") + '/Software/feature_extract/MLData')
import arffify

class Summarize_Available_Features:
    """ Finds all feature extractors, tries to summarize some info about them,
    whether they are currently used, and if they have doc-strings
    """
    def __init__(self, pars={}):
        self.pars = pars


    def extract_all_features_from_init(self):
        """ Parse __init__.py, get features that are known / avialble
        """
        out_feat_dict = {}

        lines = open(self.pars['init_fpath']).readlines()

        import_dict = {} # contains: {<py_filename>:[<extractor 1>, <extractor 2>, ...]
        for line in lines:
            if len(line) < 1:
                continue # skip this line
            if ((line[0] != '#') and ('from' in line)):
                sub_str = line[line.find('from') + 5:line.find('import')]
                py_filename = sub_str.strip()
                sub_str = line[line.find('import')+7:]
                a_list = sub_str.split(',')
                extractor_list = []
                for elem in a_list:
                    extractor_list.append(elem.strip())
                import_dict[py_filename] = {'extractor_list':extractor_list,
                                            'init_line':copy.copy(line)}

        ### Now parse arffify and see which features are actually used.
        skipped_features = arffify.skip_features
        for extr_dict in import_dict.values():
            for feat_name in extr_dict['extractor_list']:
                out_feat_dict[feat_name] = {'used_in_classifications':True,
                                            'is_extracted':False,
                                            'doc_str':""}
                if feat_name in skipped_features:
                    out_feat_dict[feat_name]['used_in_classifications'] = False


        ### Try to get the doc_strings for the feature extractors, if any where created.
        # This might be more easily done by genning signals_list ala db_importer.py:1048
        # test_feature_algorithms.py:22
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                              'Software/feature_extract'))
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                      'Software/feature_extract/Code'))
        from Code import *
        import db_importer

        signals_list = []
        gen = generators_importers.from_xml(signals_list)
        gen.generate(xml_handle="../../Data/vosource_9026.xml")
        gen.sig.add_features_to_xml_string(gen.signals_list)

	for filter_name,filt_dict in signals_list[0].properties['data'].iteritems():
		for feat_name,value_object in signals_list[0].properties['data']\
		                                [filter_name]['features'].iteritems():
                    # KLUDGE: some inconsistancy in feature naming for closest_in_light...
                    #    - these seem to be due to various users creating extractors with non conforming names / defintions
                    #        - if everyone named their extractors with a '_extractor' suffix, this would work!!!
                    if 'closest_light' in feat_name:
                        feat_name = feat_name.replace('closest_light','closest_in_light')
                    if not out_feat_dict.has_key(feat_name):
                        feat_name = feat_name + '_extractor'
                    if not out_feat_dict.has_key(feat_name):
                        feat_name = feat_name.replace('_extractor','extractor')

                    if feat_name in skipped_features:
                        out_feat_dict[feat_name]['used_in_classifications'] = False

                    out_feat_dict[feat_name]['is_extracted'] = True
                    out_feat_dict[feat_name]['doc_str'] = value_object.__doc__


        import pprint
        pprint.pprint(out_feat_dict)
        return out_feat_dict

        
if __name__ == '__main__':

    pars = {'init_fpath':'/home/pteluser/src/TCP/Software/feature_extract/Code/extractors/__init__.py'}

    SummarizeFeatures = Summarize_Available_Features(pars=pars)
    SummarizeFeatures.extract_all_features_from_init()

    # parse init file for non # lines

    """
        ### Try to get the doc_strings for the feature extractors, if any where created.
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code/extractors'))
        from Code import *

        for extractor_name,extr_dict in import_dict.iteritems():
            exec("sys.path.append(os.path.abspath(os.environ.get('TCP_DIR') + 'Software/feature_extract/Code/extractors'));" + extr_dict['init_line'])
            for extr_name in extr_dict['extractor_list']:
                print extr_name # TODO: see if __doc__ exists : do an eval()
    """
