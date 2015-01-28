#!/usr/bin/env python
"""
This is to be called by flask script using subprocess.Popen()

###Calling Flask code should use syntax like:
import subprocess
p = subprocess.Popen("/home/dstarr/src/TCP/Software/ingest_tools/lcs_classif.py http://lyra.berkeley.edu:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
sts = os.waitpid(p.pid, 0)
script_output = p.stdout.readlines()

### This script can be tested using:
/home/dstarr/src/TCP/Software/ingest_tools/lcs_classif.py http://lyra.berkeley.edu:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,

"""
import sys, os
import urllib
import cStringIO

os.environ["TCP_DIR"] = "/Data/dstarr/src/TCP/"
from rpy2.robjects.packages import importr
from rpy2 import robjects
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from Code import *
import db_importer

sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
import arffify

algo_code_dirpath = os.path.abspath(os.environ.get("TCP_DIR")+'Algorithms')
sys.path.append(algo_code_dirpath)
import rpy2_classifiers

head_str = """<?xml version="1.0"?>
<VOSOURCE version="0.04">
	<COOSYS ID="J2000" equinox="J2000." epoch="J2000." system="eq_FK5"/>
  <history>
    <created datetime="2009-12-02 20:56:18.880560" codebase="db_importer.pyc" codebase_version="9-Aug-2007"/>
  </history>
  <ID>6930531</ID>
  <WhereWhen>
    <Description>Best positional information of the source</Description>
    <Position2D unit="deg">
      <Value2>
        <c1>323.47114731</c1>
        <c2>-0.79916734036</c2>
      </Value2>
      <Error2>
        <c1>0.000277777777778</c1>
        <c2>0.000277777777778</c2>
      </Error2>
    </Position2D>
  </WhereWhen>
  <VOTimeseries version="0.04">
    <TIMESYS>
			<TimeType ucd="frame.time.system?">MJD</TimeType> 
			<TimeZero ucd="frame.time.zero">0.0 </TimeZero>
			<TimeSystem ucd="frame.time.scale">UTC</TimeSystem> 
			<TimeRefPos ucd="pos;frame.time">TOPOCENTER</TimeRefPos>
		</TIMESYS>

    <Resource name="db photometry">
        <TABLE name="v">
          <FIELD name="t" ID="col1" system="TIMESYS" datatype="float" unit="day"/>
          <FIELD name="m" ID="col2" ucd="phot.mag;em.opt.v" datatype="float" unit="mag"/>
          <FIELD name="m_err" ID="col3" ucd="stat.error;phot.mag;em.opt.v" datatype="float" unit="mag"/>
          <DATA>
            <TABLEDATA>
"""

tail_str = """              </TABLEDATA>
            </DATA>
          </TABLE>
        </Resource>
      </VOTimeseries>
</VOSOURCE>"""


def generate_feature_xml_using_raw_xml(raw_xml_str):
    """ Generate an xml string which has features in it.
    ####### This part was taken from file: test_feature_algorithms.py:
    """
    tmp_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=raw_xml_str)
    gen.sig.add_features_to_xml_string(gen.signals_list)

    fp_out = cStringIO.StringIO()
    gen.sig.write_xml(out_xml_fpath=fp_out)
    xml_str = fp_out.getvalue()
    sys.stdout.close()
    sys.stdout = tmp_stdout
    return xml_str


def generate_arff_using_raw_xml(xml_str):
    """ This generates an arff, which contains features
    """
    master_list = []
    master_features_dict = {}
    all_class_list = []
    master_classes_dict = {}

    new_srcid = 1
    include_arff_header = True

    ### Generate the features:
    tmp_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=xml_str)
    gen.sig.add_features_to_xml_string(signals_list)                
    gen.sig.x_sdict['src_id'] = new_srcid
    dbi_src = db_importer.Source(make_dict_if_given_xml=False)
    dbi_src.source_dict_to_xml(gen.sig.x_sdict)
    sys.stdout.close()
    sys.stdout = tmp_stdout

    xml_fpath = dbi_src.xml_string

    a = arffify.Maker(search=[], skip_class=False, local_xmls=True, convert_class_abrvs_to_names=False, flag_retrieve_class_abrvs_from_TUTOR=False, dorun=False)
    out_dict = a.generate_arff_line_for_vosourcexml(num=new_srcid, xml_fpath=xml_fpath)

    master_list.append(out_dict)
    all_class_list.append(out_dict['class'])
    master_classes_dict[out_dict['class']] = 0
    for feat_tup in out_dict['features']:
        master_features_dict[feat_tup] = 0 # just make sure there is this key in the dict.  0 is filler


    master_features = master_features_dict.keys()
    master_classes = master_classes_dict.keys()
    a = arffify.Maker(search=[], skip_class=True, local_xmls=True, 
                      convert_class_abrvs_to_names=False,
                      flag_retrieve_class_abrvs_from_TUTOR=False,
                      dorun=False, add_srcid_to_arff=True)
    a.master_features = master_features
    a.all_class_list = all_class_list
    a.master_classes = master_classes
    a.master_list = master_list


    fp_out = cStringIO.StringIO()
    a.write_arff(outfile=fp_out, \
                 remove_sparse_classes=True, \
                 n_sources_needed_for_class_inclusion=1,
                 include_header=include_arff_header,
                 use_str_srcid=True)#, classes_arff_str='', remove_sparse_classes=False)
    arff_str = fp_out.getvalue()
    return arff_str


def main():
    """ Main function
    """
    if len(sys.argv) < 2:
        return {}
    timeseries_url = sys.argv[1]

    t_list = []
    m_list = []
    merr_list = []
    try:
        f = urllib.urlopen(timeseries_url)
        ts_str = f.read()
        f.close()
        ts_list = eval(ts_str)
        for tup in ts_list:
            t_list.append(float(tup[0]))
            m_list.append(float(tup[1]))
            merr_list.append(float(tup[2]))
    except:
        return {}
    if len(t_list) == 0:
        return {}

    data_str_list = []
    for i, t in enumerate(t_list):
        data_str = '              <TR row="%d"><TD>%lf</TD><TD>%lf</TD><TD>%lf</TD></TR>' % \
                                  (i, t, m_list[i], merr_list[i])
        data_str_list.append(data_str)
    all_data_str = '\n'.join(data_str_list)
    out_xml = head_str + all_data_str + tail_str
    ### This generates a xml which contains features:
    #feat_xml_str = generate_feature_xml_using_raw_xml(out_xml)
    #print feat_xml_str

    ### This generates an arff, which contains features:
    test_arff_str = generate_arff_using_raw_xml(out_xml)


    algo_code_dirpath = os.path.abspath(os.environ.get("TCP_DIR")+'Algorithms')
    tmp_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algo_code_dirpath)
    sys.stdout.close()
    sys.stdout = tmp_stdout


    classifier_dict = rc.read_randomForest_classifier_into_dict(r_name='rf.tr',
                                                     r_classifier_fpath="/home/dstarr/scratch/macc_wrapper_rfclfr.rdat")
    #                                                 r_classifier_fpath="/Data/dstarr/src/ASASCatalog/data/asas_randomForest.Rdat")
    # NOTE: see activelearn_utils.py:L696
    # TODO: will want to ensure that the classifier applies to the same features as in the arff_str

    #do_ignore_NA_features = False # This is a strange option to set True, which would essentially skip a featrue from being used.  The hardcoded-exclusion features are sdss and ws_ related.
    skip_missingval_lines = False # we skip sources which have missing values

    if 0:
        #train_arff_str = open(os.path.expandvars("/media/raid_0/historical_archive_featurexmls_arffs/tutor_123/2011-02-05_23:43:21.830763/source_feats.arff")).read()
        traindata_dict = rc.parse_full_arff(arff_str=train_arff_str, skip_missingval_lines=skip_missingval_lines)
        #import pdb; pdb.set_trace()
        classifier_dict = rc.train_randomforest(traindata_dict,
                                                do_ignore_NA_features=do_ignore_NA_features,
                                                mtry=15, ntrees=1000, nodesize=1)

        r_name='rf_clfr'
        classifier_dict = {'class_name':r_name}

    #test_arff_str = open(os.path.expandvars("/media/raid_0/historical_archive_featurexmls_arffs/tutor_126/2011-02-06_00:03:02.699641/source_feats.arff")).read()
    testdata_dict = rc.parse_full_arff(arff_str=test_arff_str, skip_missingval_lines=skip_missingval_lines)


    # features to ignore in the testing data:
    ignore_feats_list = ["color_bv_extinction",
                         "color_diff_bj",
                         "color_diff_hk",
                         "color_diff_jh",
                         "color_diff_rj",
                         "color_diff_vj",
                         "ar_is_theta",
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
                         "n_points"]

    classif_results = rc.apply_randomforest(classifier_dict=classifier_dict,
                                            data_dict=testdata_dict,
                                            #do_ignore_NA_features=do_ignore_NA_features,
                                            return_prediction_probs=True,
                                            ignore_feats=ignore_feats_list)
    # classif_results['predictions']['tups']
    # srcid, rank, prob, class_name
    #import pdb; pdb.set_trace()
    #print
    
    #out = self.retrieve_tutor_class_ids()
    #rclass_tutorid_lookup = out['rclass_tutorid_lookup']

    final_dict = {}
    #  form:     [(236518, 0, 0.36299999999999999, 'b. Semireg PV'), ...
    for tup in classif_results['predictions']['tups']:
        final_dict[tup[3]] = tup[2]

    return final_dict


if __name__ == '__main__':

    #print '''{"rrlyra":0.912,"cepheid":0.02}'''
    #print "blahblah"
    out_dict = main()
    #print "yoyoyo"
    print out_dict

