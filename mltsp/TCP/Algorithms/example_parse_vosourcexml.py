#!/usr/bin/env python
""" This example script parses VOSource style XML.
    These XML may be generated TUTOR/DotAstro.org,
    or XML generated / used by TCP related programs.

NOTE: This requires a couple Python packages:

      python-xml     # Allows: import xml.etree.cElementTree

NOTE: This also requires reference to a PATH which contains required Python modules.
      - If one svn checks-out TCP, then just add a .bashrc environment variable pointing to the TCP directory:

           export TCP_DIR=/home/pteluser/src/TCP/



"""
import os, sys
import pprint

sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/Code/extractors')
import mlens3

sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
import arffify

sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/Code/extractors')
import db_importer

if __name__ == '__main__':


    #xml_fpath = "/home/pteluser/scratch/vosource_xml_writedir/100015915.xml"
    xml_fpath = "/home/pteluser/Dropbox/work/403.47491.770.xml"
    dbi_src = db_importer.Source(xml_handle=xml_fpath)#make_dict_if_given_xml=False
    import pdb; pdb.set_trace()

    ##### NOTE:
    #print dbi_src.x_sdict.keys()
    #['src_id', 'ra', 'dec', 'dec_rms', 'class', 'ra_rms', 'ts']
    #print dbi_src.x_sdict['ts'].keys()
    #['B:table13168']
    #print dbi_src.x_sdict['ts']['B:table13168'].keys()
    #['ucds', 'm_err', 'ordered_column_names', 'm', 'IDs', 'units', 't', 'limitmags']
    #print dbi_src.x_sdict['ts']['B:table13168']['t']
    #[1165.7560000000001, 1166.7670000000001,  .... ]

    ############
    # OBSOLETE:
    ############

    a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
    a.pars['skip_sci_class_list'] = []
    class_features_dict = a.generate_arff_line_for_vosourcexml(xml_fpath=xml_fpath)


    pprint.pprint(class_features_dict)
    """ 
{'class': 'Variable Stars',
 'features': {('amplitude', 'float'): 0.025850000000000001,
              ('beyond1std', 'float'): 0.0,
              ('flux_percentile_ratio_mid20', 'float'): 0.23181637707700001,
              ('flux_percentile_ratio_mid35', 'float'): 0.43537035954600001,
              ('flux_percentile_ratio_mid50', 'float'): 0.60144542283299995,
              ('flux_percentile_ratio_mid65', 'float'): 0.72181559826399999,
              ('flux_percentile_ratio_mid80', 'float'): 0.88061936278599995,
              ('freq1_harmonics_amplitude_0', 'string'): None,
              ('freq1_harmonics_freq_0', 'string'): None,
              ('freq1_harmonics_moments_0', 'string'): None,
              ('freq1_harmonics_peak2peak_flux', 'string'): None,
              ('freq1_harmonics_rel_phase_0', 'string'): None,
              ('freq2_harmonics_amplitude_0', 'string'): None,
              ('freq2_harmonics_freq_0', 'string'): None,
              ('freq2_harmonics_moments_0', 'string'): None,
              ('freq2_harmonics_rel_phase_0', 'string'): None,
              ('freq3_harmonics_amplitude_0', 'string'): None,
              ('freq3_harmonics_freq_0', 'string'): None,
              ('freq3_harmonics_moments_0', 'string'): None,
              ('freq3_harmonics_rel_phase_0', 'string'): None,
              ('freq_harmonics_offset', 'string'): None,
              ('freq_nharm', 'string'): None,
              ('freq_signif', 'string'): None,
              ('freq_y_offset', 'string'): None,
              ('max_slope', 'float'): 4.0,
              ('median_buffer_range_percentage', 'float'): 0.25,
              ('pair_slope_trend', 'float'): 0.0666666666667,
              ('percent_amplitude', 'float'): 34.639465635699999,
              ('percent_difference_flux_percentile', 'float'): 0.0384360559729,
              ('sdss_petro_radius_g_err', 'string'): None,
              ('sdss_photo_z_pztype', 'string'): None,
              ('sdss_rosat_flux_in_mJy', 'string'): None,
              ('sdss_rosat_log_xray_luminosity', 'string'): None,
              ('skew', 'float'): -0.21906825572300001,
              ('std', 'float'): 0.0138923614089,
              ('ws_variability_bv', 'string'): None,
              ('ws_variability_gr', 'string'): None,
              ('ws_variability_iz', 'string'): None,
              ('ws_variability_ri', 'string'): None,
              ('ws_variability_ru', 'string'): None,
              ('ws_variability_self', 'float'): 994999.20798299997,
              ('ws_variability_ug', 'string'): None},
 'file': '/home/pteluser/scratch/vosource_xml_writedir/100015915.xml',
 'num': ''}
"""

    d = mlens3.EventData(xml_fpath)
    ### NOTE: "d" is an object which contains xmldict.XmlDictObject components among other things.


    ts_dict = {}
    for filter_name, elem_list in d.data['ts'].iteritems():
        ts_dict[filter_name] = {}
        for xml_elem in elem_list:
            ts_dict[filter_name][xml_elem['name']] = xml_elem['val']

    pprint.pprint(ts_dict)
    """
{'I:table6235': {'limit': array(['false', 'false', ...], dtype='|S5'),
                 'm': array([ 16.2127,  16.2109, ...]),
                 'm_err': array([ 0.0061,  0.0081, ...]),
                 't': array([ 49086.86378,  49087.78441, ...])},
 'V:table7886': {'limit': ....}}
    """




    if False:

        ##### The following just kicks us into a PDB prompt rather than exiting, which allows interactive work with variables.
        #####     Type "?" for a list of available commands, although print and most Python syntax works
        import pdb; pdb.set_trace()



        ##### This gives some examples of access to "d"'s XmlDictObject components:
        print d.data['ts'].keys()
        #['I:table6235', 'V:table7886']
        print d.data['ts']['I:table6235'][2]['name']
        #m_err

        print d.feat_dict.keys()
        #['I:table6235', 'multiband', 'V:table7886']

        print d.feat_dict['I:table6235'].keys()
        #['ratio32', 'ratio31', 'freq3_harmonics_amplitude_error_0', 'freq1_harmonics_peak2peak_flux', 'beyond1std', 'freq1_harmonics_rel_phase_0', 'max_slope',  .... ]

        import pprint
        pprint.pprint(d.feat_dict['I:table6235']['amplitude'])
        #{'description': 'amplitude',
        # 'err': {'_text': 'unknown', 'datatype': 'string'},
        # 'filter': {'_text': 'I:table6235', 'datatype': 'string'},
        # 'name': {'_text': 'amplitude', 'class': 'timeseries'},
        # 'origin': {'code_output': {'_text': '"0.02585"', 'datatype': 'string'},
        #            'code_ver': 'db_importer.py 1572 2010-07-06 11:40:46Z pteluser',
        #            'description': ' Returns the half the difference between the maximum magnitude and the minimum magnitude. Note this will also work for data that is given in terms of flux. So in a sense, it__SINGLEQUOTE__s a volitile feature across different datasets.  Suggestion: use the new percent_amplitude below instead. Turn this one off__qmark__  ',
        #            't_gen': {'_text': '2010-07-09T23:54:51.292070',
        #                      'ucd': 'time.epoch'}},
        # 'val': {'_text': '0.02585', 'datatype': 'float', 'is_reliable': 'True'}}





