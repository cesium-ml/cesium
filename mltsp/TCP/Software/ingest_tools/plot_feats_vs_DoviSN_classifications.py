#!/usr/bin/env python
"""
This code is derived from regenerate_vosource_xmls.py


Creates a collection of plots displaying SN relevant features vs.
class probabilities from Dovi/Nat SN classification algorithms.

This takes a set of vosource xmls in a directory.

This applies the SN classification code to each vosource.

Currently, this writes a .arff file which can be used to visualize the dependencies

NOTE: only context features are used by the SN classification code.
"""
import os, sys

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from Code import *
import db_importer
import glob
import pprint
import sn_classifier
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code/extractors'))
#import vosource_parse
import mlens3

class Plot_Feats_Vs_DoviSN_Classifications:
    """
Given a list of older vosource.xmls, this re-generates
the vosource.xmls, adding new features.

This code saves XMLs into a seperate directory.
    """
    def __init__(self, pars={}):
        self.pars = pars

    def main(self):
        """ main method
        (generating .arff file for WEKA plotting)
        """
        misval_chr = self.pars['missing_val_char']
        old_xml_fpaths = glob.glob("%s/*xml" % (self.pars['xmls_dirpath']))

        body_lines_list = []
        orig_sci_class_list = []
        for old_xml_fpath in old_xml_fpaths:
            ### I think this bit is only needed if sdss or closest_in
            #   features had not been calculated, but I think they have
            #   for all XMLs of current interest. :
            ### This object generates new features:
            if self.pars['re-generate_features_for_xmls']:
                signals_list = []
                gen = generators_importers.from_xml(signals_list)
                gen.generate(xml_handle=old_xml_fpath)
                gen.sig.add_features_to_xml_string(gen.signals_list)
                os.system("rm %s" % (old_xml_fpath))
                gen.sig.write_xml(out_xml_fpath=old_xml_fpath)
            # This objects gets a xmldict.XmlDictObject structure which will be used 
            #     by the SN classfication code:
            d = mlens3.EventData(os.path.abspath(old_xml_fpath))

            #v = vosource_parse.vosource_parser(old_xml_fpath)
            #datamodel = v.d
            #pprint.pprint(d.data)
            try:
                orig_sci_class = d.data['VOSOURCE']['CLASSIFICATIONS']['CLASSIFICATION']['SOURCE']['CLASS_SCHEMA']['CLASS']['dbname']
            except:
                #for xml_elem in d.data['VOSOURCE']['CLASSIFICATIONS']['classification']:
                #    if 'nova' in xml_elem['class']['name']:
                #        orig_sci_class = xml_elem['class']['name']
                #        break
                ### db_importer.py written variety:
                orig_sci_class = d.data['VOSOURCE']['Classifications']['Classification']['class'].name
            #if not 'nova' in orig_sci_class:
            #    continue # skip this VOSource
            if not orig_sci_class in orig_sci_class_list:
                orig_sci_class_list.append(orig_sci_class)

            sn =  sn_classifier.Dovi_SN(datamodel=d,doplot=False)
            #print old_xml_fpath
            #print 'orig_sci_class:    ', orig_sci_class
            #print "!!! sn.final_results:", sn.final_results.get('probabilities',{})
            #pprint.pprint(sn.final_results.get('probabilities',{}))
            (closest_in_light,closest_in_light_ttype,closest_in_light_dm,sdss_best_offset_in_petro_g,sdss_best_z,sdss_best_dz,sdss_nearest_obj_type,sdss_photo_rest_ug,sdss_photo_rest_gr,sdss_photo_rest_ri,sdss_photo_rest_iz) = sn.debug_feat_tup
            #print 'closest_in_light:',closest_in_light,'\nclosest_in_light_ttype:',closest_in_light_ttype,'\nclosest_in_light_dm:',closest_in_light_dm,'\nsdss_best_offset_in_petro_g:',sdss_best_offset_in_petro_g,'\nsdss_best_z:',sdss_best_z,'\nsdss_best_dz:',sdss_best_dz,'\nsdss_nearest_obj_type:',sdss_nearest_obj_type,'\nsdss_photo_rest_ug:',sdss_photo_rest_ug,'\nsdss_photo_rest_gr:',sdss_photo_rest_gr,'\nsdss_photo_rest_ri:',sdss_photo_rest_ri,'\nsdss_photo_rest_iz:',sdss_photo_rest_iz,
                
            id_num = str(d.data['VOSOURCE']['ID'])
            if '#' in id_num:
                id_num = id_num[id_num.rfind('#')+1:]
            weka_line_list = [id_num]
            if closest_in_light == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(closest_in_light))
            if closest_in_light_ttype == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(closest_in_light_ttype))
            if closest_in_light_dm == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(closest_in_light_dm))
            if sdss_best_offset_in_petro_g == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_best_offset_in_petro_g))
            if sdss_best_z == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_best_z))
            if sdss_best_dz == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_best_dz))
            if ('star' in sdss_nearest_obj_type) or \
                   (sdss_nearest_obj_type == 'galaxy'):
                weka_line_list.append("'" + str(sdss_nearest_obj_type) + "'")
            else:
                weka_line_list.append('?')
            if sdss_photo_rest_ug == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_photo_rest_ug))
            if sdss_photo_rest_gr == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_photo_rest_gr))
            if sdss_photo_rest_ri == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_photo_rest_ri))
            if sdss_photo_rest_iz == None:
                weka_line_list.append(misval_chr)
            else:
                weka_line_list.append(str(sdss_photo_rest_iz))


            #pprint.pprint(sn.final_results.get('probabilities',{}))
            for class_name in ['SN CC','SN IIP','SN IIn','SN Ia','SN Ibc']:
                prob_str = str(sn.final_results.get('probabilities',{}).get(class_name,{}).get('prob',misval_chr))
                weka_line_list.append(prob_str)
            
            weka_line_list.append("'" + str(orig_sci_class) + "'")

            weka_line = ','.join(weka_line_list)
            print '!', weka_line
            body_lines_list.append(weka_line)

        header_str = """% date = 2009-03-06 05:00:37.323219
%% 
@RELATION ts

@ATTRIBUTE id NUMERIC
@ATTRIBUTE closest_in_light NUMERIC
@ATTRIBUTE closest_in_light_ttype NUMERIC
@ATTRIBUTE closest_in_light_dm NUMERIC
@ATTRIBUTE sdss_best_offset_in_petro_g NUMERIC
@ATTRIBUTE sdss_best_z NUMERIC
@ATTRIBUTE sdss_best_dz NUMERIC
@ATTRIBUTE sdss_nearest_obj_type {'galaxy','star','star_late'}
@ATTRIBUTE sdss_photo_rest_ug NUMERIC
@ATTRIBUTE sdss_photo_rest_gr NUMERIC
@ATTRIBUTE sdss_photo_rest_ri NUMERIC
@ATTRIBUTE sdss_photo_rest_iz NUMERIC
@ATTRIBUTE prob_SN_CC NUMERIC
@ATTRIBUTE prob_SN_IIP NUMERIC
@ATTRIBUTE prob_SN_IIn NUMERIC
@ATTRIBUTE prob_SN_Ia NUMERIC
@ATTRIBUTE prob_SN_Ibc NUMERIC
"""
    
        end_of_header_str = """@ATTRIBUTE class {'%s'}

@data
""" % ("','".join(orig_sci_class_list))
        weka_file_str = header_str
        weka_file_str += end_of_header_str
        weka_file_str += '\n'.join(body_lines_list)

        fp = open(self.pars['output_arff_filepath'],'w')
        fp.write(weka_file_str)
        fp.close()
        # todo: write weka_file_str to disk.

if __name__ == '__main__':
    #'/home/pteluser/scratch/vosources_SN_from_TUTOR_and_jbloom'),
    ##### Too few SN sources in this dir: (probably just sources with >0 lightcurves):
    #pars = {'xmls_dirpath':os.path.expandvars(\
    #               '$TCP_DATA_DIR/vosource_SN_20090319'),

    pars = {'xmls_dirpath':os.path.expandvars(\
                   '$TCP_DATA_DIR/vosource_SN_nonTUTOR_collection_20090305'),
            'output_arff_filepath':'/tmp/test.arff',
            'missing_val_char':'?', # '?' :: WEKA will not plot/visualize the data if '?' is used (and thus inserted into .arff file).
            're-generate_features_for_xmls':True, # False == (just use the features existing in the vosurce.xml files)
            }
    pfvdsc = Plot_Feats_Vs_DoviSN_Classifications(pars=pars)
    pfvdsc.main()
