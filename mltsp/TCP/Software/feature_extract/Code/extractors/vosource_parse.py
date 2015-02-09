"""
like dbimporter but more general.

try it like:

import vosource_parse, pprint

fname = "test_feature_algorithms.VOSource.xml"
v = vosource_parse.vosource_parser(fname)
pprint(v.d)

## note that v is of type xmldict.XmlDictObject

v['ts'] is the parsed timeseries as a list, usually with 4 entries (time, val, valerr, limit)

it's up to the user to decide how to use those columns...there's almost no reformating

"""
from scipy import *
import xmldict, os, sys
from xml.etree import cElementTree as ElementTree # this is a nicer implementation
from pprint import pprint

class vosource_parser:
    def __init__(self, fname, is_xmlstring=False):
        self.fname = fname
        self.d = {}

        if is_xmlstring:
            self._parse_xmlstring()
        elif os.path.exists(self.fname):
            self._parse()

        if self.d:
            self._make_timeseries()

    def _parse(self):
        try:
            # 20090225 dstarr adds:
            self.elemtree = ElementTree.parse(self.fname).getroot()
            self.d = xmldict.ConvertXmlToDict(self.elemtree)
        except Exception as e:
            print(e)
            self.d = {}
            return

    def _parse_xmlstring(self):
        try:
            self.elemtree = ElementTree.fromstring(self.fname)
            self.d = xmldict.ConvertXmlToDict(self.elemtree)
        except Exception as e:
            print("EXCEPTION:", e)
            self.d = {}
            return

    def _make_timeseries(self):
        self.d.update({"ts": {}})
        try:
            if isinstance(self.d['VOSOURCE']['VOTimeseries']['Resource']['TABLE'], xmldict.XmlDictObject):
                ts_dict = [self.d['VOSOURCE']['VOTimeseries']['Resource']['TABLE']]
            else:
                ts_dict = self.d['VOSOURCE']['VOTimeseries']['Resource']['TABLE']
        except:
            print("Error")
            return

        for filt in ts_dict:
            name = filt['name']
            if not isinstance(filt.get('FIELD',''),list):
                print("field is not a list")
                continue
            allcol = []
            ncols = len(filt['FIELD'])
            for col in filt['FIELD']:
                allcol.append(col)
                allcol[-1].update({"val": []})
            try:
                xml_obj = filt['DATA']['TABLEDATA']['TR']
            except:
                continue # sometimes there is a blank line and no data.  Skip this filter.
            #20090212: dstarr adds this first condition to catch n_epochs=1, when there was just the 2nd previously:
            if isinstance(xml_obj,xmldict.XmlDictObject):
                xml_obj = [filt['DATA']['TABLEDATA']['TR']]
            elif not isinstance(xml_obj,list):
                print("data is not a list")
                continue
            ndata = len(xml_obj)
            limit = empty(ndata,dtype="S5")
            limit[:] = "false"
            for d in xml_obj:
                if len(d['TD']) != ncols:
                    continue
                for c in enumerate(d['TD']):
                    if isinstance(c[1],str):
                        allcol[c[0]]['val'].append(float(c[1]))
                    elif isinstance(c[1],dict):
                        if "_text" in c[1]:
                            if isinstance(c[1]['_text'],str):
                                allcol[c[0]]['val'].append(float(c[1]['_text']))
                        if      "limit" in c[1]:
                            limit[c[0]] = c[1]['limit']
            #make the limits
            lim = {'ID': 'col%i' % (ncols + 1), 'datatype': 'string', 'name': "limit", \
                       "ucd": "stat.max;stat.min", "val": limit}
            for col in allcol:
                col.update({"val": array(col['val'])})

            allcol.append(lim)
            self.d['ts'].update({name: allcol})

        #print ts_dict

def test():
	
	fname = "test_feature_algorithms.VOSource.xml"
	v = vosource_parser(fname)
	pprint(v.d)
	
if __name__ == "__main__":
	test()
