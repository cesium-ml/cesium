#!/usr/bin/env python
""" Tools which enable feature generation for sources in the StarVars project.

*** TODO parse the LINEAR file into a string for below
*** The aperture is chosen and the cooresp timeseries is decided in:
              tutor_database_project_insert.py:filter_best_ts_aperture()
*** TODO insert the resulting v_array int CSV parsing & freature generation code
*** TODO store the resulting features in an arff file / CSV format?

NOTE: I resolved library / python package dependencies by doing:
  1) editing my ~/.bashrc.ext:

export PATH=/global/homes/d/dstarr/local/bin:${PATH}
export TCP_DIR=/global/homes/d/dstarr/src/TCP/

  2) loading some modules:
module load python/2.7.1 numpy/1.6.1 scipy/0.10.1 ipython/0.12.1 R/2.12.1 mysql/5.1.63


"""
import sys, os
#sys.path.append("/global/u1/d/dchesny/BUILD/MySQL-python-1.2.3/build/lib.linux-x86_64-2.7")
sys.path.insert(0,os.path.expandvars("/global/u1/d/dchesny/BUILD/MySQL-python-1.2.3/build/lib.linux-x86_64-2.7"))
import MySQLdb

import time, matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.pylab import *


"""CLASS StarVars_LINEAR_Feature_Generation ############################################
    #+
    # PURPOSE: generates light curve features from input light curves as xml files
    #
    # METHODS: 
    #
    # FUNCTIONS:
    #
    #-
"""

class StarVars_LINEAR_Feature_Generation:
    """
    """
    def __init__(self, pars={}):
        self.head_str = """<?xml version="1.0"?>
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

        self.tail_str = """              </TABLEDATA>
            </DATA>
          </TABLE>
        </Resource>
      </VOTimeseries>
</VOSOURCE>"""

        self.pars=pars


    def write_limitmags_into_pkl(self, frame_limitmags):
        """ This parses the adt.frame_limitmags dictionary which is contained
        in a Pickle file and which was originally retrieved from
        mysql and from adt.retrieve_fullcat_frame_limitmags()
        """
        import cPickle
        import gzip
        ### This is just for writing the pickle file:
        fp = gzip.open(self.pars['limitmags_pkl_gz_fpath'],'w')
        cPickle.dump(frame_limitmags, fp, 1) # 1 means binary pkl used
        fp.close()


    def retrieve_limitmags_from_pkl(self):
        """ This parses the adt.frame_limitmags dictionary which is contained
        in a Pickle file and which was originally retrieved from
        mysql and from adt.retrieve_fullcat_frame_limitmags()
        """
        import cPickle
        import gzip
        fp = gzip.open(self.pars['limitmags_pkl_gz_fpath'],'rb')
        frame_limitmags = cPickle.load(fp)
        fp.close()
        return frame_limitmags

    
    def form_xml_string(self, mag_data_dict):
        """
    	Take timeseries dict data and place into VOSource XML format, 
        which TCP feature generation code expects.
       
        Adapted from: TCP/Software/feature_extract/format_csv_getfeats.py
        """
        
        data_str_list = []

        for i, t in enumerate(mag_data_dict['t']):
            m = mag_data_dict['m'][i]
            m_err = mag_data_dict['merr'][i]
            data_str = '              <TR row="%d"><TD>%lf</TD><TD>%lf</TD><TD>%lf</TD></TR>' % \
                (i, t, m, m_err)
            data_str_list.append(data_str)
            
        all_data_str = '\n'.join(data_str_list)
        out_xml = self.head_str + all_data_str + self.tail_str

        return out_xml


    def generate_arff_using_asasdat(self, xml_data=[], include_arff_header=False, arff_output_fp=None):
        """ Given a list of LINEAR data file filepaths, for each source/file:
        - choose the optimal aperture, depending upon median magnitude <---only for ASAS!!!
        - exclude bad/flagged epochs
        - generate features from timeseries (placing in intermediate XML-string format)
        - collect resulting features for all given sources, and place in ARFF style file
              which will later be read by ML training/classification code.
              
        Partially adapted from: TCP/Software/citris33/arff_generation_master_using_generic_ts_data.py:get_dat_arffstrs()
        """
        import tutor_database_project_insert
        adt = tutor_database_project_insert.ASAS_Data_Tools(pars=pars)
#         adt.frame_limitmags = self.retrieve_limitmags_from_pkl()


        sys.path.append(os.environ.get('TCP_DIR') + '/Software/feature_extract/MLData')
        #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + '/Software/feature_extract/Code/extractors'))
        #print os.environ.get("TCP_DIR")
        import arffify

        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                      'Software/feature_extract/Code'))
        import db_importer
        from data_cleaning import sigmaclip_sdict_ts
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                      'Software/feature_extract'))
        from Code import generators_importers

        master_list = []
        master_features_dict = {}
        all_class_list = []
        master_classes_dict = {}

        for xml_str in xml_data:
             new_srcid = xml_str['ID']
#             ts_str = open(dat_fpath).read()
#             source_intermed_dict = adt.parse_asas_ts_data_str(ts_str)
#             """mag_data_dict = adt.filter_best_ts_aperture(source_intermed_dict)
#             """
            # Need to have a function like this for LINEAR data:
            
#             xml_str = self.form_xml_string(mag_data_dict)
            
            ### Generate the features:
            signals_list = []
            gen = generators_importers.from_xml(signals_list)
            gen.generate(xml_handle=xml_str)
            gen.sig.add_features_to_xml_string(signals_list)                
            gen.sig.x_sdict['src_id'] = new_srcid
            dbi_src = db_importer.Source(make_dict_if_given_xml=False)
            dbi_src.source_dict_to_xml(gen.sig.x_sdict)

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
        a = arffify.Maker(search=[], skip_class=False, local_xmls=True, 
                          convert_class_abrvs_to_names=False,
                          flag_retrieve_class_abrvs_from_TUTOR=False,
                          dorun=False, add_srcid_to_arff=True)
        a.master_features = master_features
        a.all_class_list = all_class_list
        a.master_classes = master_classes
        a.master_list = master_list


        a.write_arff(outfile=arff_output_fp, \
                     remove_sparse_classes=True, \
                     n_sources_needed_for_class_inclusion=1,
                     include_header=include_arff_header,
                     use_str_srcid=True)#, classes_arff_str='', remove_sparse_classes=False)


"""MIAIN PROGRAM ###############################################################################
    #+
    # PURPOSE: Generate a set of predefined light curve features from a set of light curves.
    #          The light curves are in a predefined pickle file as a dictionary of xml strings.
    #
    # CALLING SEQUENCE: [ python ] starsvars_feature_generation_xml.py start finish
    #
    # INPUTS:
    #       start - an integer representing the index of the first light curve in the range of 
    #				light curves to be processed.
    #
    #		finish- an integer representing the index of the final light curve in the range of 
    #				light curves to be processed.
    #
    # OUTPUTS:
    #       A file containing the currently coded set of light curve features
    #-
"""

if __name__ == '__main__':

    pars = { \
        #'tcp_hostname':'192.168.1.25',
        #'tcp_username':'pteluser',
        #'tcp_port':     3306, #23306,
        #'tcp_database':'source_test_db',
        #'limitmags_pkl_gz_fpath':'/home/dstarr/scratch/asas_limitmags.pkl.gz',
        'limitmags_pkl_gz_fpath':'/project/projectdirs/m1583/ASAS_scratch/asas_limitmags.pkl.gz',
        }

	# initialize the class StarVars_LINEAR_Feature_Generation
    sv_asas = StarVars_LINEAR_Feature_Generation( pars=pars )
    
    startTime = time.time()

	# open the pickle file containing the xml string light curves an load them into memory as the list 'files'
    buff  = open('/project/projectdirs/m1583/linear/allLINEARfinal_lc_dat/xml.pickle', 'wb')
    files = cPickle.load( buff )
    buff.close()

    # select from the full set of light curves the range of light curves that you specify
    m = sys.argv[1]
    n = sys.argv[2]
    for i in range(m,n):
        runfiles.append( files[i] )

	# calculate features for the specified light curves and write the results into a file
    arff_output_fp = open( 'out' + '_' + str(m) + 'to' + str(n) + '.arff', 'w' )

    sv_asas.generate_arff_using_asasdat(xml_data=runfiles,
                                        include_arff_header=False,
                                        arff_output_fp=arff_output_fp)
                                            
    arff_output_fp.close()
    print '\n\nCompleted writing features for LC', j, 'of', len(runfiles), '\n\n'

    endTime = time.time()  
    totalTime = endTime - startTime
    print '\nDone! Total time =', totalTime, 's'
   	time.sleep(30)

	# need to add code that checks the output file for correctness using os.stat