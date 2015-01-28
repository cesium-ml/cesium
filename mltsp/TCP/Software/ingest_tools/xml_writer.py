#!/usr/bin/env python
""" Tools which enable feature generation
for sources in the StarVars project.

*** TODO parse the LINEAR file into a string for below
*** parse raw LINEAR ts files (as string):
              tutor_database_project_insert.py:parse_asas_ts_data_str(ts_str)
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
import cPickle

#sys.path.append("/global/u1/d/dchesny/BUILD/MySQL-python-1.2.3/build/lib.linux-x86_64-2.7")
sys.path.insert(0,os.path.expandvars("/global/u1/d/dchesny/BUILD/MySQL-python-1.2.3/build/lib.linux-x86_64-2.7"))
import MySQLdb


import time, matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.pylab import *

"""FUNCTION Index #####################################
#+
# PURPOSE: given a directory, returns a list of the names of all files with full path
#
# CALLING SEQUENCE: files = index( directory )
#
# INPUTS:
#	indir   - a directory path
#
# OUTPUTS:
#	files = a list containing the full path names of all files in the directory
#-
"""
def index( directory ):
#    import os, sys

    stack = [directory]
    files = []
    while stack:
        directory = stack.pop()

        for file in os.listdir(directory):

            if file.endswith('.dat'):  # only get files that end in .dat [change for other purposes]

                fullname = os.path.join(directory, file)
                files.append(fullname)
                if os.path.isdir(fullname) and not os.path.islink(fullname):
                    stack.append(fullname)

    return files

"""FUNCTION readLC #####################################
    #+
    # PURPOSE: given a phased light curve file, returns num.array objects phase, mag, dmag
    #
    # CALLING SEQUENCE: readLC( infile )
    #
    # INPUTS:
    #       infile   - a 3-column light curve date[], mag[], dmag[] as text file
    #
    # OUTPUTS:
    #       A file containing three numpy arrays: date, mag, dmag
    #-
"""
    
#    def readLC(infile):  # reads in 3-column data and returns phase[], mag[], dmag[]
def readLC(infile):
    import numpy as np

    date = []
    mag  = []
    dmag = []
    mag_data_dict = {}

    ID      = infile[infile.rfind('/')+1:infile.rfind('.dat')]
    lines   = open(infile).readlines()

    for line in lines:
        fields = map( float, line.split() )
        date.append( fields[0] )
        mag.append( fields[1] )
        dmag.append( fields[2] )

    date = np.array( date )
    mag  = np.array( mag )
    dmag = np.array( dmag )

    mag_data_dict['srcid'] = ID
    mag_data_dict['t']     = date
    mag_data_dict['m']     = mag
    mag_data_dict['merr']  = dmag

    return mag_data_dict



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

    def example_dat_parse(self):
        """
        """
        import tutor_database_project_insert
        adt = tutor_database_project_insert.ASAS_Data_Tools(pars=pars)
        if 0:
            ### requires mysql connection to TUTOR:
            adt.retrieve_fullcat_frame_limitmags() 
            self.write_limitmags_into_pkl(adt.frame_limitmags)

        ### This is done when we don't have a connection to the mysql database.
        adt.frame_limitmags = self.retrieve_limitmags_from_pkl()

        dat_fpath = '/project/projectdirs/m1583/linear/allLINEARfinal_lc_dat/10003298.dat'
        ts_str = open(dat_fpath).read()
        source_intermed_dict = adt.parse_asas_ts_data_str(ts_str)
        """mag_data_dict = adt.filter_best_ts_aperture(source_intermed_dict)
        """
        xml_str = self.form_xml_string(mag_data_dict)
        
        
        ### TODO Generate the features for this xml string

        import pdb; pdb.set_trace()
        print


    def generate_arff_using_asasdat(self, data_fpaths=[], include_arff_header=False, arff_output_fp=None):
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
        adt.frame_limitmags = self.retrieve_limitmags_from_pkl()


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

        for dat_fpath in data_fpaths:
            new_srcid = dat_fpath[dat_fpath.rfind('/')+1:dat_fpath.rfind('.dat')]
            ts_str = open(dat_fpath).read()
            source_intermed_dict = adt.parse_asas_ts_data_str(ts_str)
            """mag_data_dict = adt.filter_best_ts_aperture(source_intermed_dict)
            """
            # Need to have a function like this for LINEAR data:
            
            xml_str = self.form_xml_string(mag_data_dict)
            
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


if __name__ == '__main__':

    startTime = time.time()
    indir = '/project/projectdirs/m1583/linear/allLINEARfinal_lc_dat'
#    print '\n indir =', indir
    files = index( indir )
#    print '\n files =', files[0:5]

    pars = { \
        #'tcp_hostname':'192.168.1.25',
        #'tcp_username':'pteluser',
        #'tcp_port':     3306, #23306,
        #'tcp_database':'source_test_db',
        #'limitmags_pkl_gz_fpath':'/home/dstarr/scratch/asas_limitmags.pkl.gz',
        'limitmags_pkl_gz_fpath':'/project/projectdirs/m1583/ASAS_scratch/asas_limitmags.pkl.gz',
        }

    sv_asas = StarVars_LINEAR_Feature_Generation( pars=pars )

    LC  = {}
    xml = {}
    for i in range( 0, len(files) ):
	try:
            LC[i]  = readLC( files[i] )
	except:
            print 'ERROR: File', i, 'in LC dictionary is not a light curve!'
            continue
        try:
            xml[i] = sv_asas.form_xml_string( LC[i] )
        except:
            print 'ERROR: Unable to form xml string for LC['+str(i)+']'
    
    buff = open( '/project/projectdirs/m1583/linear/allLINEARfinal_lc_dat/xml.pickle', 'wb' )
    cPickle.dump(xml, buff )
    buff.close()

    endTime = time.time()
    totalTime = endTime - startTime
    print '\nTotal time:', totalTime, 's'
