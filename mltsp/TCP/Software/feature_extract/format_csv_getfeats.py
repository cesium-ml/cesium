#!/usr/bin/env python
""" When given a csv lightcurve, generate features.
"""
from __future__ import print_function
from __future__ import absolute_import

import os, sys
import csv

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from .Code import *
import db_importer


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


if __name__ == '__main__':

    pars = {'csv_fpath':"/home/dstarr/scratch/PTFS1108o.dat",
            'final_vsrcxml_fpath':'/tmp/PTFS1108o.xml',
            }

    data_str_list = []

    rows = csv.reader(open(pars['csv_fpath']), delimiter=' ')

    t_list = []
    m_list = []
    merr_list = []
    for i,row in enumerate(rows):
        t = float(row[0])
        m = float(row[1])
        m_err = float(row[2])
        data_str = '              <TR row="%d"><TD>%lf</TD><TD>%lf</TD><TD>%lf</TD></TR>' % \
                                  (i, t, m, m_err)
        data_str_list.append(data_str)
        t_list.append(t)
        m_list.append(m)
        merr_list.append(m_err)

    all_data_str = '\n'.join(data_str_list)

    out_xml = head_str + all_data_str + tail_str

    ####### This part was taken from file: test_feature_algorithms.py:
    signals_list = []
    gen = generators_importers.from_xml(signals_list)
    gen.generate(xml_handle=out_xml)
    gen.sig.add_features_to_xml_string(gen.signals_list)

    feature_added_VOSource_XML_fpath = pars['final_vsrcxml_fpath']
    gen.sig.write_xml(out_xml_fpath=feature_added_VOSource_XML_fpath)
    import pprint
    pprint.pprint((signals_list[0].properties['data']['v']['features'].keys()).sort())
    print()
    print('freq1_harmonics_freq_0 =', signals_list[0].properties['data']['v']['features']['freq1_harmonics_freq_0'])
    print()

    #import pdb; pdb.set_trace()
