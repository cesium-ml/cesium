"""
This is to be called by flask script using subprocess.Popen()

###Calling Flask code should use syntax like:
import subprocess
p = subprocess.Popen(home_str+"/Dropbox/work_etc/mltp/TCP/Software/ingest_tools/generate_science_features.py http://lyra.berkeley.edu:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
sts = os.waitpid(p.pid, 0)
script_output = p.stdout.readlines()

### This script can be tested using:
home_str+/Dropbox/work_etc/mltp/TCP/Software/ingest_tools/generate_science_features.py http://lyra.berkeley.edu:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,

"""
from __future__ import print_function


def currently_running_in_docker_container():
    import subprocess
    proc = subprocess.Popen(["cat","/proc/1/cgroup"],stdout=subprocess.PIPE)
    output = proc.stdout.read()
    if "/docker/" in output:
        in_docker_container=True
    else:
        in_docker_container=False
    return in_docker_container


import sys, os
import urllib
import io

from ..feature_extract.Code import *
from ..feature_extract.Code import db_importer
from ..feature_extract.MLData import arffify


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

    fp_out = io.StringIO()
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
    #tmp_stdout = sys.stdout
    #sys.stdout = open(os.devnull, 'w')
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=xml_str)
    gen.sig.add_features_to_xml_string(signals_list)
    gen.sig.x_sdict['src_id'] = new_srcid
    dbi_src = db_importer.Source(make_dict_if_given_xml=False)
    dbi_src.source_dict_to_xml(gen.sig.x_sdict)
    #sys.stdout.close()
    #sys.stdout = tmp_stdout

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


    fp_out = io.StringIO()
    a.write_arff(outfile=fp_out, \
                 remove_sparse_classes=True, \
                 n_sources_needed_for_class_inclusion=1,
                 include_header=include_arff_header,
                 use_str_srcid=True)#, classes_arff_str='', remove_sparse_classes=False)
    arff_str = fp_out.getvalue()
    return arff_str




def arff_to_dict(arff_str):
    out_dict = {}
    attributes_list = []
    all_lines = arff_str.split('\n')
    line_num=0
    for line in all_lines:
        if "@ATTRIBUTE" in line and len(line.split())==3:
            attr_name,type_name = line.split()[1:]
            attributes_list.append(attr_name)
        elif "@ATTRIBUTE" in line and "class" in line:
            attributes_list.append("class")
        if "@data" in line:
            all_vals = all_lines[line_num+1].split(',')
            if len(all_vals) != len(attributes_list):
                print("ERROR: len(all_vals) != len(attributes_list) !!!!")
                print("len(all_vals) =", len(all_vals), " and len(attributes_list) =", len(attributes_list))
                print("attributes_list =", attributes_list)
                return out_dict
            for i in range(len(all_vals)):
                try:
                    out_dict[attributes_list[i]] = float(all_vals[i])
                except ValueError:
                    out_dict[attributes_list[i]] = str(all_vals[i])


        line_num += 1
    return out_dict


def generate(timeseries_url="",path_to_csv=False,ts_data=None):
    """ Main function
    """

    t_list = []
    m_list = []
    merr_list = []

    if path_to_csv: # read csv from local machine:
        try:
            with open(path_to_csv) as f:
                for line in f:
                    if line.strip() != "":
                        if len(line.split(",")) >= 3:
                            t,m,merr = line.strip().split(',')[:3]
                            t_list.append(float(t))
                            m_list.append(float(m))
                            merr_list.append(float(merr))
                        elif len(line.split(",")) == 2:
                            t,m = line.strip().split(',')
                            t_list.append(float(t))
                            m_list.append(float(m))
                            merr_list.append(1.0)

        except Exception as theError:
            print("generate_science_features::generate():", theError, "... Returning {}...")
            return {}
    elif timeseries_url != "": # a url is provided to return the ts data

        if timeseries_url not in ["","5125"]:
            print(timeseries_url)
        else:
            if len(sys.argv) < 2:
                print("lcs_classif.py - len(sys.argv) < 2. Returning...")
                return {}
            print("lcs_classif.py - sys.argv[1] =", sys.argv[1])
        timeseries_url = sys.argv[1]


        try:
            f = urllib.urlopen(timeseries_url)
            ts_str = f.read()
            f.close()
            ts_list = eval(ts_str)
            for tup in ts_list:
                t_list.append(float(tup[0]))
                m_list.append(float(tup[1]))
                merr_list.append(float(tup[2]))
        except Exception as theError:
            print("generate_science_features::generate():", theError, "... Returning {}...")
            return {}
    elif ts_data != None and type(ts_data)==list:
        t_list, m_list, merr_list = zip(*ts_data)
        t_list=list(t_list)
        m_list=list(m_list)
        merr_list=list(merr_list)
    if len(t_list) == 0:
        print("t_list = [] !!!!!!!!!!!\nReturning {}...")
        return {}
    #to see what's been read in:
    #print zip(t_list,m_list,merr_list)

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
    #print type(feat_xml_str)
    ### This generates an arff, which contains features:
    test_arff_str = generate_arff_using_raw_xml(out_xml)


    #print test_arff_str
    #print type(test_arff_str)

    out_dict = arff_to_dict(test_arff_str)

    return out_dict


if __name__ == '__main__':

    outdict = generate()

    print(outdict)
