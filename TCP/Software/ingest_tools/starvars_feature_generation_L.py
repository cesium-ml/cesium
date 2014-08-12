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

    lines   = open(infile).readlines()

    for line in lines:
        fields = map( float, line.split() )
        date.append( fields[0] )
        mag.append( fields[1] )
        dmag.append( fields[2] )

    date = np.array( date )
    mag  = np.array( mag )
    dmag = np.array( dmag )

    mag_data_dict['t']    = date
    mag_data_dict['m']    = mag
    mag_data_dict['merr'] = dmag

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
    flist	  = sys.argv[1]
    print '\n flist =', flist
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
    #sv_asas.example_dat_parse()

    """
    BATCHES
    
    files1=files[0:1000]
    files2=files[1000:2000]
    files3=files[2000:3000]
    files4=files[3000:4000]
    files5=files[4000:5000]
    files6=files[5000:6000]
    files7=files[6000:7000]
    files8=files[7000:7011]
    
    """
    runfiles = []
    if flist == "1":
        runfiles = files[0:5]
    
    if flist == "2":
        runfiles = files[5:10]

    if flist == "3":
        runfiles = files[10:15]

    if flist == "4":
        runfiles = files[15:20]
	
    if flist == "5":
        runfiles = files[400:500]
	
    if flist == "6":
        runfiles = files[500:600]
	
    if flist == "7":
        runfiles = files[600:700]
	
    if flist == "8":
        runfiles = files[700:800]
	
    if flist == "9":
        runfiles = files[800:900]
	  
    if flist == "10":
        runfiles = files[900:1000]
	  
    if flist == "11":
        runfiles = files[1000:1100]
	  
    if flist == "12":
        runfiles = files[1100:1200]
	  
    if flist == "13":
        runfiles = files[1200:1300]
	  
    if flist == "14":
        runfiles = files[1300:1400]
	  
    if flist == "15":
        runfiles = files[1400:1500]
	  
    if flist == "16":
        runfiles = files[1500:1600]
	  
    if flist == "17":
        runfiles = files[1600:1700]
	  
    if flist == "18":
        runfiles = files[1700:1800]
	
    if flist == "19":
        runfiles = files[1800:1900]
	  
    if flist == "20":
        runfiles = files[1900:2000]
	  
    if flist == "21":
        runfiles = files[2000:2100]
	  
    if flist == "22":
        runfiles = files[2100:2200]
	  
    if flist == "23":
        runfiles = files[2200:2300]
	  
    if flist == "24":
        runfiles = files[2300:2400]
	  
    if flist == "25":
        runfiles = files[2400:2500]
	  
    if flist == "26":
        runfiles = files[2500:2600]
	  
    if flist == "27":
        runfiles = files[2600:2700]
	 
    if flist == "28":
        runfiles = files[2700:2800]
	  
    if flist == "29":
        runfiles = files[2800:2900]
	  
    if flist == "30":
        runfiles = files[2900:3000]
	  
    if flist == "31":
        runfiles = files[3000:3100]
	  
    if flist == "32":
        runfiles = files[3100:3200]
	  
    if flist == "33":
        runfiles = files[3200:3300]
	  
    if flist == "34":
        runfiles = files[3300:3400]
	  
    if flist == "35":
        runfiles = files[3400:3500]
	  
    if flist == "36":
        runfiles = files[3500:3600]
	  
    if flist == "37":
        runfiles = files[3600:3700]
	  
    if flist == "38":
        runfiles = files[3700:3800]
	  
    if flist == "39":
        runfiles = files[3800:3900]
	  
    if flist == "40":
        runfiles = files[3900:4000]
	  
    if flist == "41":
        runfiles = files[4000:4100]
	
    if flist == "42":
        runfiles = files[4100:4200]
	  
    if flist == "43":
        runfiles = files[4200:4300]
	  
    if flist == "44":
        runfiles = files[4300:4400]
	  
    if flist == "45":
        runfiles = files[4400:4500]
	  
    if flist == "46":
        runfiles = files[4500:4600]
	  
    if flist == "47":
        runfiles = files[4600:4700]
	  
    if flist == "48":
        runfiles = files[4700:4800]
	  
    if flist == "49":
        runfiles = files[4800:4900]
	  
    if flist == "50":
        runfiles = files[4900:5000]
	  
    if flist == "51":
        runfiles = files[5000:5100]
	  
    if flist == "52":
        runfiles = files[5100:5200]
	  
    if flist == "53":
        runfiles = files[5200:5300]
	  
    if flist == "54":
        runfiles = files[5300:5400]
	  
    if flist == "55":
        runfiles = files[5400:5500]
	  
    if flist == "56":
        runfiles = files[5500:5600]
	  
    if flist == "57":
        runfiles = files[5600:5700]
	  
    if flist == "58":
        runfiles = files[5700:5800]
	  
    if flist == "59":
        runfiles = files[5800:5900]
	  
    if flist == "60":
        runfiles = files[5900:6000]
	  
    if flist == "61":
        runfiles = files[6000:6100]
		  
    if flist == "62":
        runfiles = files[6100:6200]
	  
    if flist == "63":
        runfiles = files[6200:6300]
	  
    if flist == "64":
        runfiles = files[6300:6400]
	  
    if flist == "65":
        runfiles = files[6400:6500]
	  
    if flist == "66":
        runfiles = files[6500:6600]
	  
    if flist == "67":
        runfiles = files[6600:6700]
	  
    if flist == "68":
        runfiles = files[6700:6800]
	  
    if flist == "69":
        runfiles = files[6800:6900]
	  
    if flist == "70":
        runfiles = files[6900:7000]
		  
    if flist == "71":
        runfiles = files[7000:7010]



#--------------------------------------------------------------

#    print 'runfiles = ', runfiles

    j = 0
    for file in runfiles:
        j += 1
        print 'writing features for file', j, 'of', len(runfiles)
        mag_data_dict = readLC(file)
        print 'mag_data_dict generated for LC', j, 'of', len(runfiles)
        arff_output_fp = open( 'out' + str(flist) + '.arff', 'w' )
        sv_asas.generate_arff_using_asasdat(data_fpaths=runfiles,
                                            include_arff_header=False,
                                            arff_output_fp=arff_output_fp)

        sleep(20)

        print '\nCompleted writing features for LC', j, 'of', len(runfiles)
        arff_output_fp.close()
        print '\nClosed output file successfully'
#        arff_rows_str = arff_output_fp.getvalue()
#        print arff_rows_str




    
#     j = 0
#     for file in files1:
#         j += 1
#         print 'writing features for file', j, 'of', len(files1)
#         mag_data_dict = readLC(file)
# 
#         arff_output1_fp = open('out1.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files1,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output1_fp)
#         arff_output1_fp.close()
#
# 
#     for file in files2:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out2.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files2,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files3:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out3.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files3,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files4:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out4.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files4,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files5:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out5.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files5,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files6:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out6.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files6,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files7:
#         mag_data_dict = readLC(file)
# 
#         arff_output_fp = open('out7.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files7,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
# 
# 
#     for file in files8:
#         mag_data_dict = readLC(file)
# 
#         arff_output8_fp = open('out8.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=files8,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output8_fp)
#         arff_output8_fp.close()

    endTime = time.time()
    
    totalTime = endTime - startTime
    print '\nTotal time:', totalTime, 's'

#     if 1:
#         ### Example: generate arff feature string, do not write to file:
#         import cStringIO
#         arff_output_fp = cStringIO.StringIO()
# 
#         sv_asas.generate_arff_using_asasdat(data_fpaths=data_fpaths,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
# 
#         arff_rows_str = arff_output_fp.getvalue()
#         print arff_rows_str
# 
#     else:
#         ### Example: generate arff feature string, write to some file:
#         arff_output_fp = open('out.arff', 'w')
#         sv_asas.generate_arff_using_asasdat(data_fpaths=data_fpaths,
#                                             include_arff_header=False,
#                                             arff_output_fp=arff_output_fp)
#         arff_output_fp.close()
