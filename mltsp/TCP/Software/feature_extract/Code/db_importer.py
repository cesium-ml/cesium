#!/usr/bin/env python

"""
main remote interaction client to the transients source database

NOTE: I've added the "svn propset" characteristic to this file, for $Id: db_importer.py 1573 2010-07-12 18:14:15Z pteluser $ using:
     svn propset svn:keywords Id *.py

To run this locally, you'll want to set up a tunnel from here->lyra->linux

  ssh  -L 8000:192.168.1.45:8000 lyra.berkeley.edu

Leave that window open.

you'll want to have Amara (XML toolkit installed)
   wget http://peak.telecommunity.com/dist/ez_setup.py
   sudo python ez_setup.py
   sudo /scisoft/i386/Packages/Python/Python.framework/Versions/Current/bin/easy_install amara
    (or /sw/bin/easy_install amara)

Open up a new UNIX window.Typical usage might be:
bash> ipython -pylab
py> import db_importer
py> pe =db_importer.PositionExtractor(pos=(49.599497, -1.0050998),radius=0.001,prefer_only_source_search=True, host="192.168.1.45")
py> pe.search_pos(out_xml_fpath='')  # this populates the pe.sources list
py> # to view the dictionary associated with the first source returned
py> import pprint
py> pprint.pprint(pe.sources[0].d)

If you have an xml that you want to be put in to an internal representation (py dictionary), then do something like this:
bash> ipython -pylab
py> import db_importer
py> s = db_importer.Source(xml_handle="source_5.xml")

Now s.x_sdict will have a dictionary representation of the xml.
that dictionary (and the one coerced from Dan's db) will look like:
py> pprint.pprint(s.x_sdict)

{'dec': -1.0142709999999999,
 'dec_rms': 0.000118,
 'ra': 49.591202000000003,
 'ra_rms': 0.00012300000000000001,
 'src_id': 26,
 'ts': {'g': {'m': [24.215399999999999],
              'm_err': [3.4363600000000001],
              't': [53666.468710000001]},
        'i': {'m': [23.313300000000002],
              'm_err': [1.5199199999999999],
              't': [53666.466222000003]},
        'r': {'m': [22.273800000000001],
              'm_err': [0.47815600000000003],
              't': [53666.465392999999]},
        'z': {'m': [22.619199999999999],
              'm_err': [2.7249099999999999],
              't': [53666.467880999997]}}}

if the source was made from Dan's codes then use s.d for the dictionary.
"""
from __future__ import print_function
from __future__ import absolute_import

__author__ = "JSB"
__version__ = "9-Aug-2007"
__svn_id__ = "$Id: db_importer.py 1573 2010-07-12 18:14:15Z pteluser $".replace('$','').replace('Id:','').strip()

__tab__ = "  "

import time, datetime
import os, sys
from logging import *
import copy

MAX_SEARCH_RADIUS = 0.5 # degrees
#20080225# MAX_SEARCH_RADIUS = 0.125 # degrees
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR","") + \
              '/Software/feature_extract/Code')) # 20090309 dstarr adds this for nosetests use only
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR","") + \
              '/Software/feature_extract/Code/extractors')) # 20090309 dstarr adds this for xmldict load only
from .extractors import xmldict
from . import vo_timeseries
import numpy
try:
    import numarray
except:
    import numpy as numarray
#import matplotlib
#try:
#    from matplotlib import pylab
#except:
#    pass
try:
    from xml.etree import cElementTree as ElementTree # this is a nicer implementation
except:
    # This is caught in M45's python 2.4.3 distro where the elementtree module was installed instead
    from elementtree import ElementTree


sdss_filters        = {'u': 0, 'g':    1, 'r':   2, 'i':    3, 'z':   4, 'V': 5}
sdss_plotting_codes = {'u': 'kd', 'g': 'bo', 'r': 'gs','i': 'rD', 'z': 'md', 'V': 'bo',
               'ptf_g':'go', 'ptf_r':'ro'}


def setup_logging(file_level=DEBUG, screen_level=INFO,fname="./db_importer.log"):

    basicConfig(level=file_level,format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename=fname,filemode='w')
    console = StreamHandler()
    console.setLevel(screen_level)
    getLogger('').addHandler(console)
    return

#try:
#   import amara
#   use_amara = True
#except:
#   warning("cannot use Amara for xml fun")
#   use_amara = False

def add_pretty_indents_to_elemtree(elem, level=0):
    """ in-place prettyprint formatter
    """
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            if (elem.tag == "MAG") or (elem.tag == "TIME"):
                elem.tail = "\n" + (level+1)*"  "
                continue
            add_pretty_indents_to_elemtree(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i



class vosource_classification_obj:
    """ This deals with forming the <CLASSIFICATION> </..> part
    of the vosource XML.
    """
    def __init__(self):
        # Internal representation of class:probabilities is:
        #self._classes[source_name][class_schema_name][class_name] = prob
        self._classes = {}


    def add_classif_prob(self, class_name="", prob=-1.0,
                         src_name='None', class_schema_name='None',
                         human_algo="algorithm",
                         catalog_tcp="tcp"):
        """ This adds a classification to the internal class structure.

        NOTE: human_algo == ["algorithm" OR "human"]
        NOTE: catalog_tcp == ["catalog" OR "tcp"]
        """
        if human_algo not in self._classes:
            self._classes[human_algo] = {}
        if catalog_tcp not in self._classes[human_algo]:
            self._classes[human_algo][catalog_tcp] = {}
        if src_name not in self._classes[human_algo][catalog_tcp]:
            self._classes[human_algo][catalog_tcp][src_name] = {}
        if class_schema_name not in self._classes[human_algo][catalog_tcp][src_name]:
            self._classes[human_algo][catalog_tcp][src_name][class_schema_name] = {}
        if class_name not in self._classes[human_algo][catalog_tcp][src_name][class_schema_name]:
            self._classes[human_algo][catalog_tcp][src_name][class_schema_name][class_name] = {}
        if class_name not in self._classes[human_algo][catalog_tcp][src_name][class_schema_name]:
            self._classes[human_algo][catalog_tcp][src_name][class_schema_name][class_name] = {}
        self._classes[human_algo][catalog_tcp][src_name][class_schema_name][class_name]['prob'] = prob


    def get_class_xml_string(self):
        """ This forms the (<Classifications> </..>) string
        and returns this string.
        """
        __tab__ = "  " # This is a global variable in db_importer.py

        self.class_xml_string = "  <Classifications>\n"
        for human_algo in self._classes.keys():
            self.class_xml_string += '    <Classification type="%s">\n' % (human_algo)
            for catalog_tcp in self._classes[human_algo].keys():
                for src_name in self._classes[human_algo][catalog_tcp].keys():
                    self.class_xml_string += """      <source type="%s">
        <link></link>
        <name>%s</name>
        <version>1.0</version>
        <comments></comments>
      </source>\n""" % (catalog_tcp, src_name)
                    for class_schema_name in self._classes[human_algo][catalog_tcp][src_name].keys():
                        #self.class_xml_string += '        <CLASS_SCHEMA type="%s">\n' % (class_schema_name)
                        for class_name in self._classes[human_algo][catalog_tcp][src_name][class_schema_name].keys():
                            #self.class_xml_string += '      <class dbname="%s" prob="%lf">\n' % (class_name, \
                            #20090420 comment out# self.class_xml_string += '      <class name="%s" dbname="%s" prob="%lf">\n' % (class_name, class_name, self._classes[human_algo][catalog_tcp][src_name][class_schema_name][class_name]['prob'])
                            self.class_xml_string += '      <class name="%s" dbname="%s" prob="%lf">\n' % (class_name, class_schema_name, self._classes[human_algo][catalog_tcp][src_name][class_schema_name][class_name]['prob'])
                            self.class_xml_string += "      </class>\n"
                        #self.class_xml_string += "        </CLASS_SCHEMA>\n"
            self.class_xml_string += "    </Classification>\n"
        self.class_xml_string += "  </Classifications>\n"
        return self.class_xml_string


    def add_class_xml_to_existing_vosource_xml(self, old_vosource_str):
        """ Given a vosource XML string, this forms and inserts the
        <CLASSIFICATION> contents and returns a new vosource string.

        Uses get_class_xml_string()
        Returns a new vosource_str.
        """
        class_xml_string = self.get_class_xml_string()

        # This is KLUDGEY: I'm not sure the re module would be efficient since
        #    it might search over the enormous string.  So I try 3 cases:
        r_buffer_size = 1000
        vosource_end_str = old_vosource_str[-r_buffer_size:]
        ind = vosource_end_str.rfind('</VOSOURCE')
        if ind == -1:
            ind = vosource_end_str.rfind('</vosource')
            if ind == -1:
                ind = vosource_end_str.rfind('</Vosource')
                if ind == -1:
                    print("Unable to find </VOSOURCE> at end of string!")
                    return old_vosource_str

        # get the true index of the beginning of </VOSOURCE>:
        i_begin_of_vosource = ind + len(old_vosource_str) - r_buffer_size
        new_vosource_str = "%s\n%s\n%s" % (\
                                        old_vosource_str[:i_begin_of_vosource], \
                                        class_xml_string, \
                                        old_vosource_str[i_begin_of_vosource:])
        return new_vosource_str


class Source:

    def __init__(self,verbose=True, sdict=None, xml_handle=None,\
              make_xml_if_given_dict=True, interactive=False,\
              make_dict_if_given_xml=True, doplot=False,xml_validate=False,\
          out_xml_fpath='', use_source_id_in_xml_fpath=False, \
          write_xml=True, read_simpletimeseries=False):
        """
        sdict - the dictionary with the data of the source
                as it comes from the database
        xml_handle - the string representation, file name, or file h
        """
        self.sdict   = sdict
        self.verbose = verbose
        self.xml_handle = xml_handle
        self.marshalled_to_xml = False
        self.coerced_to_dict = False
        self.xml_validate = xml_validate
        self.id = "unk"
        self.use_source_id = use_source_id_in_xml_fpath
        self._handle_start()

        if read_simpletimeseries and make_dict_if_given_xml:
            self.simpletimeseriesxml_to_source_dict(self.xml_handle)
            return

        if make_xml_if_given_dict and self.coerced_to_dict:
            self.source_dict_to_xml(self.d)
            if write_xml == True:
                self.write_xml(out_xml_fpath=out_xml_fpath)
            if doplot:
                self.plot_from_dict(self.d,interactive= \
                                           interactive)

        elif make_dict_if_given_xml and not self.coerced_to_dict:
            self.xml_to_source_dict(self.xml_handle)
            if doplot:
                self.plot_from_dict(self.x_sdict,interactive= \
                            interactive,bands=self.x_sdict['ts'].keys())

    def write_xml(self, out_xml_fpath=''):
        if not self.marshalled_to_xml:
            return
        if type(out_xml_fpath) != type(""):
            # This catches filepointers and StringIO
            f = out_xml_fpath
        else:
            if len(out_xml_fpath) != 0:
                if not self.use_source_id:
                    fname = out_xml_fpath
                else:
                    bb = os.path.dirname(out_xml_fpath)
                    if bb == "":
                        bb = "./"
                    if out_xml_fpath.endswith(".xml"):
                        ttt = ""
                    else:
                        ttt = ".xml"
                    fname = os.path.normpath(bb + "/source" + \
                        str(self.id) + "." + os.path.basename(out_xml_fpath) + ttt)
            else:
                fname = "source_" + str(self.id) + ".xml"

            f = open(fname,"w")

        f.write(self.xml_string)

        if type(out_xml_fpath) == type(""):
            f.close()
        print("wrote %s " % fname)

    def _handle_start(self):
        """
        decides what do to with the initial instantiation
        """
        if self.sdict is None and self.xml_handle is None:
            # this is a blank instance
            if self.verbose:
                info("blank instance of Source created")
        if self.sdict is not None:
            self.coerce_sdict()


    def coerce_sdict(self,metakeys=["src_id",'ra_rms',"dec_rms","ra",\
                    "dec", 'feat_gen_date']):
        """
        this makes a reasonable dictionary out of the primitive currently being returned from Dan's codes
        """
        self.d = {}

        all_entries = self.sdict.keys()
        # TODO: rather than select the first entry, I want to select the entry which has the mst amount of info.
        best_represent_entry = all_entries[0]
        # NOTE: I want to choose the self.sdict entry which has all of the source info.
        #       - this is needed because some filters just contain limiting mags and not much source info.
        for entry in all_entries:
            if 'm' in self.sdict[entry]:
                best_represent_entry = entry
                break
        for m in metakeys:
            if m in self.sdict[best_represent_entry]:
                self.d.update({m: self.sdict[best_represent_entry][m]})
            for b in all_entries:
                if m in self.sdict[b]:
                    self.sdict[b].pop(m)
        self.d.update({'ts': self.sdict})
        if "src_id" in self.d:
            self.id = self.d['src_id']
        self.coerced_to_dict = True
        return


    def plot_from_dict(self,dic,bands=['u','g','r','i','z'],plot_title="",interactive=False,save_plot_name=None):
        if not self.coerced_to_dict:
            return

        if "ts" not in dic:
            warning("no timeseries to plot")
            return

        import matplotlib

        matplotlib.pylab.hold(False)
        matplotlib.pylab.plot([120,111])
        matplotlib.pylab.hold(True)
        xxtrema = [[],[]]
        yytrema = [[],[]]
        #print bands
        for i in range(len(bands)):
            filt = bands[i]
            if filt not in dic['ts']:
                continue
            #g = [ numpy.array(dic['ts'][filt]['t']),numpy.array(dic['ts'][filt]['m']),numpy.array(dic['ts'][filt]['m_err']) ]

            g = [ numarray.array(dic['ts'][filt]['t']),numarray.array(dic['ts'][filt]['m']),numarray.array(dic['ts'][filt]['m_err']) ]
            #print g
            matplotlib.pylab.errorbar(g[0],g[1],g[2],fmt=sdss_plotting_codes[filt])
            xxtrema[0].append(min(g[0]))
            xxtrema[1].append(max(g[0]))
            yytrema[0].append(max(g[1]))
            yytrema[1].append(min(g[1]))

        matplotlib.pylab.ylim( (max(yytrema[0]) + 1,min(yytrema[1]) - 0.3) )
        matplotlib.pylab.xlim( (min(xxtrema[0]) - 10,max(xxtrema[1]) + 10) )
        #print (max(yytrema[1]) + 1,min(yytrema[0]))
        #print (min(xxtrema[0]) - 10,max(xxtrema[1]) + 10)
        #print yytrema
        matplotlib.pylab.xlabel("%s - %5.2f [%s]" % (self.timesys, self.timezero, "day"))
        matplotlib.pylab.ylabel('magnitude')

        if plot_title=='':
            plot_title = "ID: " + repr(dic['src_id'])
        matplotlib.pylab.title(plot_title)

        if interactive:
            matplotlib.pylab.show()
        else:
             if save_plot_name is None:
                     save_plot_name = "source_plot_" + repr(dic['src_id']) + ".png"
             matplotlib.pylab.savefig(save_plot_name)
             f = open(save_plot_name,'r')
             if f.readline().find("PS-Adobe")  != -1:
                     # this is a postscript file
                     os.rename(save_plot_name,save_plot_name.replace(".png",".ps"))
                     save_plot_name = save_plot_name.replace(".png",".ps")
             f.close()
             if self.verbose:
                     print("+ save light curve %s" % save_plot_name)


    def normalize_vosource_tags(self, xml_str):
        """ Convert specific VOSource tags to expected case
        so that it is easier to xpath query, traverse.
        """
        xs = xml_str.replace('CLASSIFICATIONS','Classifications')\
                    .replace('CLASSIFICATION','Classification')\
                    .replace('classification','Classification')\
                    .replace('<SOURCE','<source')\
                    .replace('</SOURCE','</source')\
                    .replace('RESOURCE','Resource')\
                    .replace('VOTIMESERIES','VOTimeseries')\
                    .replace('CLASS','class')
        return xs


    def xml_to_source_dict(self,xml_handle):
        """
        takes the XML string and makes a dict
        """
        #if not use_amara:
        #   print "sorry. no amara"
        #   return

        self.x_sdict = {}
        # # # # # # #
        # # # # # # #
        # TODO: eventually get rid of this amara reference and self.doc:
        #self.doc = amara.parse(xml_handle,validate=self.xml_validate)
        # # # # # # #
        # # # # # # #

        # KLUDGE: need to do test as to whether xml_handle is filepath
        #      or an xml_string (this was previously done in amara.parse())
        if len(xml_handle) < 200:
            # assume filepath case
            xml_str = open(xml_handle).read()
        else:
            xml_str = xml_handle

        # TODO: here I want to convert xml_string XML tags to lowercase.
        # TODO: here I should also check schema conformity
        new_xml_str = self.normalize_vosource_tags(xml_str)

        self.elemtree = ElementTree.fromstring(new_xml_str)

        xmld_data = xmldict.ConvertXmlToDict(self.elemtree)

        # xmldict form:
        #  data = vosource_parse.vosource_parser(_xmlfpath).d  = xmldict.ConvertXmlToDict(self.elemtree)
        #data.data['VOSOURCE']['Features']['feature'][0].keys()
        #['origin', 'name', 'err', 'filter', 'val', 'description']

        # so ideally, the code in db_importer.py would know how to deal with a xmldict{}

        srcid_uri = xmld_data['VOSOURCE']['ID'] # str
        if 'ivo' in srcid_uri:
            if srcid_uri.count('#') == 0:
                srcid_num = int(srcid_uri[srcid_uri.rfind(' ')+1:])
            else:
                srcid_num = int(srcid_uri[srcid_uri.rfind('#')+1:])
        else:
            try:
                srcid_num = int(srcid_uri)
            except:
                # if we can't make an INT of it, try just a str
                #    - this will break feature-RDB codes
                srcid_num = srcid_uri
        try:
            self.x_sdict.update({"src_id": srcid_num})
        except:
            self.x_sdict.update({"src_id": 'UNKNOWN'})

        ### Retrieve classified science classes, if exist:
        ###################### 20080707 dstarr modified:
        #classification_branches = self.doc.xml_xpath(u"//classification")
        #if len(classification_branches) == 0:

        # # # # # # #self.elemtree.findall('CLASSIFICATIONS/CLASSIFICATION')
                #classification_branches = self.doc.xml_xpath(u"//CLASSIFICATION")
        classification_branches = self.elemtree.findall('Classifications/Classification')

        #class_update_dict = {"class":''}
        class_update_dict = {"class":"UNKNOWN"}
        #20100709 comment out: #for classification_node_type_name in ['tcp','catalog','tutor-data-ingest']:
        for classification_node_type_name in ['tcp','tutor-data-ingest', 'catalog']:
            # 20100706: NOTE: I order the conditions, since for dotastro.org classifications,
            #      <source type="catalog"> seems more descriptive than <source type="tutor-data-ingest"> in some cases (9022)
            if class_update_dict["class"] != "UNKNOWN":
                break # This means we already found a valid classification from xml parsing
            for classfn_branch in classification_branches:
                correct_branch = False
                try:
                    for source_branch in classfn_branch.findall('source'):
                        if (source_branch.get('type') == classification_node_type_name):
                            correct_branch = True
                            break
                except:
                    pass
                if correct_branch:
                    # Then we get the innermost, longest class dbname & parse last ':' suffix
                    classes = classfn_branch.findall('.//class')
                    tmpclasses = []
                    dbname_to_name = {}
                    for c in classes:
                        class_name = c.get('dbname','')
                        if len(class_name) > 0:
                            tmpclasses.append(class_name)
                            if c.get('name') != None:
                                verbose_name = c.get('name')
                            else:
                                verbose_name = c.get('dbname','') # I'd perfer not having this case arise.
                            dbname_to_name[class_name] = verbose_name
                    tmpclasses.sort(key=len,reverse=True)
                    grandchild_classname = ''
                    if len(tmpclasses) > 0:
                        grandchild_classname = dbname_to_name[tmpclasses[0]]
                    class_update_dict = {"class":grandchild_classname}
                    break
                #else:
                #    class_update_dict = {"class":"UNKNOWN"}
        self.x_sdict.update(class_update_dict)
        ######################

        # self.elemtree.findall('WhereWhen/Position2D/Value2/c1')[0].text
        try:
            self.x_sdict.update({"ra": float(self.elemtree.\
                 findall('WhereWhen/Position2D/Value2/c1')[0].text)})
        except:
            self.x_sdict.update({"ra": ''})
        try:
            self.x_sdict.update({"dec": float(self.elemtree.\
                 findall('WhereWhen/Position2D/Value2/c2')[0].text)})
        except:
            self.x_sdict.update({"dec": ''})
        try:
            self.x_sdict.update({"dec_rms": float(self.elemtree.\
                 findall('WhereWhen/Position2D/Error2/c2')[0].text)})
        except:
            self.x_sdict.update({"dec_rms": ''})
        try:
            self.x_sdict.update({"ra_rms": float(self.elemtree.\
                 findall('WhereWhen/Position2D/Error2/c1')[0].text)})
        except:
            self.x_sdict.update({"ra_rms": ''})

        self.ts = {}
        ## now parse through to get all the timeseries data

        ## figure out what kind of timeseries it is
        try:
            self.timesys = self.elemtree.findall('VOTimeseries/TIMESYS/TimeType')[0].text.upper()
            self.timezero = float(self.elemtree.findall('VOTimeseries/TIMESYS/TimeZero')[0].text)
        except:
            #print "No TIMESYS ... assuming the defaults"
            self.timesys = "MJD"
            self.timezero = 0.0

        try:
            # 20090311: dstarr not sure if a-mara string case still applicable for etree.  Commenting out:
            #filt_nodes = [x for x in self.doc.VOSOURCE.VOTIMESERIES.RESOURCE.xml_children if type(x) != type(u"")]
            filt_nodes = self.elemtree.findall('VOTimeseries/Resource/TABLE')
        except:
            filt_nodes = []
        self.durga = filt_nodes
        for fn in filt_nodes:
            # Here we are iterating over <TABLE>...
            # get the band name
            band_split = fn.get('name').split("-")
            if len(band_split) == 2:
                band = band_split[1]
            else:
                band = band_split[0]

            units = []
            array_names = []
            ucds = []
            IDs  = []
            data = {}
            for f in fn.findall('FIELD'):
                ucds.append(f.get('ucd')) # appends None otherwise
                units.append(f.get('unit')) # appends None otherwise
                if f.get('name') != None:
                    array_names.append(f.get('name'))
                else:
                    array_names.append("unknown")
                data.update({array_names[-1]: []})
                if f.get('ID') != None:
                    IDs.append(f.get('ID'))
                else:
                    IDs.append("unknown")

            data.update({'units': units, 'ucds': ucds, 'IDs': IDs, 'ordered_column_names': array_names,
                     'limitmags':{'t':[], 'lmt_mg':[]}})
            ## now go through the timeseries part of the data line by line
            try:
                rows = fn.findall('DATA/TABLEDATA/TR')
            except:
                rows = []
            # needed for limit_mag use:
            col_name_dict = {}
            for i, col_name in enumerate(array_names):
                col_name_dict[col_name] = i

            for tr in rows:
                cols = tr.findall('TD')
                if 'limit' in tr.keys():
                    # KLUDGE: for limiting-magnitude XML TABLE row:
                    #   explicitly assume column names exist: XML.TABLE.FIELD.name = {'t','m'}
                    data['limitmags']['t'].append(float(cols[col_name_dict['t']].text))
                    data['limitmags']['lmt_mg'].append(float(cols[col_name_dict['m']].text))
                else:
                    for i,td in enumerate(cols):
                        data[array_names[i]].append(float(td.text))
            self.ts.update({band: copy.copy(data)})

        if 0:
            # # # 20100521: dstarr disables this due to complications with watt_per_m2_flux and just the general sloppiness of combining filters and their magnigueds.  Ideally there would be some soft of offset magnitude used for each band (like the watt_per_m2_flux, and specific features would act only on this internal combined flux(t) dataset
            ###############################
            ### KLUDGE: (20090616)
            # I'm generating a combined-band which due to a combined number of data points, should
            #    be used for band-invariant features.  This is useful for PTF since data is sparse and
            #    spread bi-monthly over 2 bands.  It is a kludge because astrophysical objects have
            #    different brightnesses in different bands.  Hopefully features which dominate
            #    effective classification prefer more samples than magnitude accuracy/offsets.
            ts_without_combo = {}
            for k,v in self.ts.items():
                if k != 'combo_band':
                    ts_without_combo[k] = v

            band_name_with_data = ts_without_combo.keys()[0]
            for band,data_dict in ts_without_combo.items():
                if len(data_dict.get('m',[])) > 0:
                    band_name_with_data = band
                    break
            combo_band_dict = copy.deepcopy(ts_without_combo[band_name_with_data])
            if 'limitmags' not in combo_band_dict:
                combo_band_dict['limitmags'] = {'lmt_mg':[], 't':[]}
            for band,data_dict in ts_without_combo.items():
                if band == band_name_with_data:
                    continue
                combo_band_dict['limitmags']['lmt_mg'].extend(data_dict.get('limitmags',{}).get('lmt_mg',[]))
                combo_band_dict['limitmags']['t'].extend(data_dict.get('limitmags',{}).get('t',[]))
                combo_band_dict['m'].extend(data_dict.get('m',[]))
                combo_band_dict['m_err'].extend(data_dict.get('m_err',[]))
                combo_band_dict['t'].extend(data_dict.get('t',[]))
            t_tup_list = []
            for i,t_val in enumerate(combo_band_dict.get('t',[])):
                t_tup_list.append((t_val,i))
            t_tup_list.sort()
            i_sorted_list = map(lambda a_b: a_b[1], t_tup_list)
            combo_band_dict['m'] = map(lambda i: combo_band_dict['m'][i], i_sorted_list)
            combo_band_dict['m_err'] = map(lambda i: combo_band_dict['m_err'][i], i_sorted_list)
            combo_band_dict['t'] = map(lambda i: combo_band_dict['t'][i], i_sorted_list)

            t_tup_list = []
            for i,t_val in enumerate(combo_band_dict['limitmags']['t']):
                t_tup_list.append((t_val,i))
            t_tup_list.sort()
            i_sorted_list = map(lambda a_b1: a_b1[1], t_tup_list)
            combo_band_dict['limitmags']['lmt_mg'] = map(lambda i: combo_band_dict['limitmags']['lmt_mg'][i], i_sorted_list)
            combo_band_dict['limitmags']['t'] = map(lambda i: combo_band_dict['limitmags']['t'][i], i_sorted_list)

            self.ts['combo_band'] = combo_band_dict
        ###############################
        self.x_sdict.update({'ts': self.ts})
        if self.verbose:
            info("converted xml to dict")

        self.coerced_to_dict = True



    # TODO(20100211): I may have the following function take a keyword which specifies xml version, and at some point allows the default of simpletimeseries xml (once all code can make use of this xml... assuming they all use db_importer and not mlens)
    def source_dict_to_xml(self,sdict):
        sss = vo_timeseries.vo_source_preamble
        xmllevel = 1

        #print sdict
        ## put in some versioning to start
        sss += """%s<history>\n%s<created datetime="%s" codebase="%s" codebase_version="%s"/>\n%s</history>\n""" % \
            (__tab__*xmllevel,__tab__*(xmllevel+1),str(datetime.datetime.utcnow()),os.path.basename(__file__),__version__,__tab__*xmllevel)
        if "src_id" in sdict:
            sss += "%s<ID>%s</ID>\n" % (__tab__*xmllevel,sdict['src_id'])

        ## get the positional info
        if "ra" in sdict and "dec" in sdict:
            sss += "%s<WhereWhen>\n" % (__tab__*xmllevel)
            sss += '%s<Description>Best positional information of the source</Description>\n' % (__tab__*(xmllevel + 1))
            sss += '%s<Position2D unit="deg">\n%s<Value2>\n' % (__tab__*(xmllevel + 1),__tab__*(xmllevel + 2))
            sss += "%s<c1>%s</c1>\n%s<c2>%s</c2>\n%s</Value2>\n" % \
                (__tab__*(xmllevel + 3),str(sdict['ra']),__tab__*(xmllevel + 3),str(sdict['dec']),__tab__*(xmllevel + 2))
            if "ra_rms" in sdict and "dec_rms" in sdict:
                xmllevel += 1
                sss += "%s<Error2>\n" % (__tab__*(xmllevel + 1))
                sss += "%s<c1>%s</c1>\n%s<c2>%s</c2>\n%s</Error2>\n" % \
                    (__tab__*(xmllevel + 2),str(sdict['ra_rms']),__tab__*(xmllevel + 2),str(sdict['dec_rms']),__tab__*(xmllevel + 1))
                xmllevel -= 1
            sss += "%s</Position2D>\n" % (__tab__*(xmllevel + 1))
            sss += "%s</WhereWhen>\n" % (__tab__*xmllevel)

        ## now do the timeseries
        if "ts" in sdict:
            sss +=  __tab__*xmllevel + vo_timeseries.vo_timeseries_preamble
            xmllevel += 1
            sss +=  __tab__*xmllevel + vo_timeseries.vo_timeseries_mjd
            filts = sdict['ts'].keys()
            if self.verbose:
                info(" there are %i band resources for the timeseries ... ")
            sss += '%s<Resource name="db photometry">\n' % (__tab__*xmllevel)
            for b in filts:
                bdata = copy.deepcopy(sdict['ts'][b]) #20090617 dstarr adds deepcopy due to sdict['ts'] being extended with limitmags while originally this sdict['ts'] structure is still accessible to later classes (which expect only regular magnitudes in sdict['ts']).

                # NOTE: KLUDGE: for now I clump both filters together for limiting magnitudes, since
                #    it will take more of a rework to seperate filters in all TCP code.
                if 't' in bdata:
                    # KLUDGE: I'm also assuming m, m_err exist.
                    bdata['is_limit'] = [False] * len(bdata['t'])
                    is_limit = bdata['is_limit'] # 20091102 dstarr adds this line
                elif 'limitmags' in bdata:
                    # This filter had no normal (t,m,m_err) data.  Just lim-mags
                    bdata['is_limit'] = []
                    bdata['t'] = []
                    bdata['m'] = []
                    bdata['m_err'] = []

                if 'limitmags' in bdata:
                    bdata['is_limit'].extend([True] * len(bdata['limitmags']['t']))
                    bdata['t'].extend(bdata['limitmags']['t'])
                    bdata['m'].extend(bdata['limitmags']['lmt_mg'])
                    bdata['m_err'].extend([0.0] * len(bdata['limitmags']['t']))

                xmllevel += 1
                sss += '%s<TABLE name="%s">\n' % (__tab__*xmllevel,b)
                xmllevel += 1
                col = 1
                has_m = has_m_err = has_t = False
                if 't' in bdata:
                    sss += '%s<FIELD name="t" ID="col%i" system="TIMESYS" datatype="float" unit="day"/>\n' \
                        % (__tab__*xmllevel,col)
                    t = numarray.array(bdata['t'])
                    tsort = t.argsort()
                    t = t[tsort]
                    has_t = True
                    col += 1
                else:
                    warning("no time array given for filter %s" % b)

                if 'limitmags' in bdata:
                    try:
                        is_limit = numarray.array(bdata['is_limit'])[tsort]
                    except:
                        is_limit = numarray.array(bdata['is_limit'])
                if "m" in bdata:
                    sss += '%s<FIELD name="m" ID="col%i" ucd="phot.mag;em.opt.%s" datatype="float" unit="mag"/>\n' \
                        % (__tab__*xmllevel,col,b)
                    has_m = True
                    try:
                        m = numarray.array(bdata['m'])[tsort]
                    except:
                        m = numarray.array(bdata['m'])
                    col += 1
                if "m_err" in bdata:
                    sss += '%s<FIELD name="m_err" ID="col%i" ucd="stat.error;phot.mag;em.opt.%s" datatype="float" unit="mag"/>\n' \
                        % (__tab__*xmllevel,col,b)
                    has_m_err = True
                    try:
                        m_err = numarray.array(bdata['m_err'])[tsort]
                    except:
                        m_err = numarray.array(bdata['m_err'])
                    col += 1

                if "objid_candid" in bdata:
                    ptf_charac_val_list = []
                    ptf_charac_name_list = ['a_elip_candid', 'b_elip_candid', 'chip_id', 'dec_candidate', 'dec_subtract', 'dtime_observe', 'dtime_reductn', 'field_id', 'filter_id', 'fourier_factor', 'fwhm_obj_candid', 'fwhm_obj_subtr', 'hp_il', 'hp_iu', 'hp_kern_radius', 'hp_newskybkg', 'hp_newskysig', 'hp_nsx', 'hp_nsy', 'hp_refskybkg', 'hp_refskysig', 'hp_rss', 'hp_tl', 'hp_tu', 'img_id_candid', 'img_id_refer', 'mag_refer', 'mag_sig_refer', 'mag_sig_subtr', 'mag_subtr', 'nn_a_elip', 'nn_b_elip', 'nn_dec', 'nn_distance', 'nn_mag', 'nn_mag_sig', 'nn_ra', 'nn_star_galaxy', 'nn_x', 'nn_y', 'objid_candid', 'objid_subtract', 'perc_cand_saved', 'percent_incres', 'positive_pix_ratio', 'quality_factor', 'ra_candidate', 'ra_subtract', 'signoise_subt_big_ap', 'signoise_subt_normap', 'surf_bright', 'x_candidate', 'x_subtref', 'y_candidate', 'y_subtref', 'zp_candidate', 'zp_reference']
                    for charac in ptf_charac_name_list:
                        #try:
                        #   ptf_charac_val_list[j] = bdata[charac][tsort]
                        #except:
                        #   ptf_charac_val_list[j] = bdata[charac]

                        #ptf_charac_val_list.append(bdata[charac])
                        ptf_charac_val_list.append(numarray.array(bdata[charac])[tsort])

                        sss += '%s<FIELD name="%s" ID="col%i" ucd="%s" datatype="float" unit=""/>\n' % (__tab__*xmllevel,charac,col,b)
                        col += 1

                sss += "%s<DATA>\n" % (__tab__*xmllevel)
                if has_t:
                    xmllevel += 1
                    sss += "%s<TABLEDATA>\n" % (__tab__*xmllevel)
                    xmllevel += 1
                    for i in range(len(t)):
                        # # # #
                        if is_limit[i]:
                            sss += '%s<TR row="%i" limit="upper" confidence="1">' % (__tab__*xmllevel,i + 1)
                        else:
                            sss += '%s<TR row="%i">' % (__tab__*xmllevel,i + 1)
                        sss += "<TD>%f</TD>" % t[i]
                        if has_m:
                            sss += "<TD>%f</TD>" % m[i]
                        if has_m_err:
                            sss += "<TD>%f</TD>" % m_err[i]
                        if "objid_candid" in bdata:
                            # TODO: I need to have ptf_charac_name_list[j][i] in array form, in case there are >1 ptf datapoint
                            for j in range(len(ptf_charac_name_list)):
                                sss += "<TD>%lf</TD>" % float(ptf_charac_val_list[j][i])
                        sss += "</TR>\n"
                    sss += "%s</TABLEDATA>\n" % (__tab__*xmllevel)
                    xmllevel -= 1
                sss += "%s</DATA>\n" % (__tab__*xmllevel)
                xmllevel -= 1
                sss += "%s</TABLE>\n" % (__tab__*xmllevel)
                xmllevel -= 1
            sss += "%s</Resource>\n" % (__tab__*xmllevel)
            xmllevel -= 1
            sss += __tab__*xmllevel  + "</VOTimeseries>\n"
        if "features" in sdict:
            sss += "%s<Features>\n" % (__tab__*xmllevel)
            xmllevel += 1
            for filt_name,filt_dict in sdict["features"].items():
                for feat_name,feat_str_val in filt_dict.items():
                    sss += "%s<Feature>\n" % (__tab__*xmllevel)
                    xmllevel += 1
                    sss += '%s<name class="timeseries">%s</name>\n' % (__tab__*xmllevel, feat_name) # or "class=context"
                    xmllevel += 1
                    sss += '%s<description>%s</description>\n' % (__tab__*xmllevel, feat_name)
                    xmllevel += 1
                    #TODO: WANT "unit" :: sss += "%s<val datatype="float" unit='arcmin' is_reliable="True">%s</val>\n" % (__tab__*xmllevel, feat_str_val)
                                        #if feat_name == 'flux_percentile_ratio_mid50':
                                        #    print 'yo'
                    if 'fail' in feat_str_val.lower():
                        sss += """%s<val datatype="string" is_reliable="False">%s</val>\n""" % (__tab__*xmllevel, feat_str_val)
                    else:
                        # 20090129 KLUDGE to discern strings vs floats:
                        try:
                            test = float(feat_str_val)
                            sss += """%s<val datatype="float" is_reliable="True">%s</val>\n""" % (__tab__*xmllevel, feat_str_val)
                        except:
                            sss += """%s<val datatype="string" is_reliable="True">%s</val>\n""" % (__tab__*xmllevel, feat_str_val)
                    # TODO: add errors here, if known:
                    sss += """%s<err datatype="string">unknown</err>\n""" % (__tab__*xmllevel)
                    ##### TODO: add features:
                    sss += """%s<filter datatype="string">%s</filter>\n""" % (__tab__*xmllevel, filt_name)
                    sss += """%s<origin description="%s">\n""" % (__tab__*xmllevel, sdict["feature_docs"][filt_name].get(feat_name,"").replace('\n','').replace('?','__qmark__').replace('&','__amper__'))
                    xmllevel += 1
                    sss += """%s<code_ver>%s</code_ver>\n""" % (__tab__*xmllevel, __svn_id__)
                    # TODO: not sure the best way to extract SVN version... (latest version under /feature_extract/Code/ ???)
                    sss += """%s<t_gen ucd="time.epoch">%s</t_gen>\n""" % (__tab__*xmllevel, sdict['feat_gen_date'].replace(' ','T'))
                    # TODO: Insert some feature-code generated comment here:
                    sss += """%s<code_output datatype="string">"%s"</code_output>\n""" % (__tab__*xmllevel, feat_str_val)
                    xmllevel -= 1
                    sss += """%s</origin>\n""" % (__tab__*xmllevel)
                    xmllevel -= 3
                    sss += "%s</Feature>\n" % (__tab__*xmllevel)
                xmllevel -= 1
            sss += "%s</Features>\n" % (__tab__*xmllevel)

                ####
        if "class" in sdict:
            vosource_class_obj = vosource_classification_obj()
            # 20081023: dstarr comments out:
            #vosource_class_obj.add_classif_prob(class_name="tutor",
            vosource_class_obj.add_classif_prob(class_name=sdict['class'],
                                                prob=1.0,
                                                class_schema_name="tutor",
                                                human_algo="human")
            sss += vosource_class_obj.get_class_xml_string()
        sss += "</VOSOURCE>\n"

        self.xml_string = sss
        self.marshalled_to_xml = True


    def add_features_to_xml_string(self, signals_list):
        """ Given a signals_list (aka parent <generator>.signals_list),
        Add features to self.x_sdict and self.xml_string (for XML file write).
        """
        # KLUDGE: Assume 1 source in signals_list
        self.x_sdict['features'] = {}
        self.x_sdict['feature_docs'] = {}

        #import datetime
        self.x_sdict['feat_gen_date'] = str(datetime.datetime.utcnow())

        for filter_name,filt_dict in signals_list[0].properties['data'].items():
            self.x_sdict['features'][filter_name] = {}
            self.x_sdict['feature_docs'][filter_name] = {}
            # KLUDGE: Since scalar values in ['features'] dict are actually
            #    of type: Code.FeatureExtractor.outputclass, I explicitly cast str:
            for feat_name,value_object in signals_list[0].properties['data']\
                                            [filter_name]['features'].items():
                self.x_sdict['features'][filter_name][feat_name] = str(value_object)
                self.x_sdict['feature_docs'][filter_name][feat_name] = \
                             str(value_object.__doc__).replace('&','__AMPERSAND__').replace("'",'__SINGLEQUOTE__').replace('"','__DOUBLEQUOTE__')[:500]
        self.source_dict_to_xml(self.x_sdict)


class PositionExtractor:
    def __init__(self, pos=(None,None), radius=0.001, verbose=True, \
             prefer_only_source_search=True, host="localhost", \
             port=8000, doplot=True, use_source_id_in_xml_name=True, \
             do_remote_connection=1, write_xml=True):
        """
        radius - search distance (box) in degrees
        use_source_id_in_xml_name - in the case where you've asked for an xml file name, setting
            this to True will mean that you get a unique xml file out.
        """
        self.verbose = verbose
        self.allow_search = False
        self.pos = pos
        self.radius = radius
        self.prefer_only_source_search = prefer_only_source_search
        self.doplot = doplot
        self.write_xml = write_xml
        self.use_source_id_in_xml_name=use_source_id_in_xml_name

        if self.radius > MAX_SEARCH_RADIUS:
            warning("search radius exceeded. Cutting down to %f deg" % MAX_SEARCH_RADIUS)
            self.radius = MAX_SEARCH_RADIUS
        self.pos_well_formed = False
        if type(self.pos) == type(()):
            if len(self.pos) == 2:
                if type(self.pos[0]) == type(1.0) and type(self.pos[1]) == type(1.0):
                        self.pos_well_formed = True

        if do_remote_connection == 1:
            self.setup_remote_connection(host=host, port=port)

    def setup_remote_connection(self,host="localhost",port=8000):
        import xmlrpclib
        info("connecting to the server")
        self.server = xmlrpclib.ServerProxy("http://%s:%i" % (host, port))
        self.remote_meth =  self.server.system.listMethods()
        if 'system.multicall' in self.remote_meth:
            self.multicall = True
        else:
            self.multicall = False

        if "get_sources_for_radec" in self.remote_meth:
            self.allow_search = True
            self.search_type  = "full"

        if self.prefer_only_source_search and ("get_sources_for_radec_assume_in_src_db" in self.remote_meth):
            self.allow_search = True
            self.search_type  = "src"

    def search_pos(self, out_xml_fpath='', summary_ps_fpath='', \
               get_sources_for_radec_method=None, \
               skip_construct_sources=False):
        if not self.allow_search:
            warning("No search allowed because the server does not have the appropriate method")
            return
        info("making the call to the server for position %s" % repr(self.pos))
        if get_sources_for_radec_method != None:
            info("this could take awhile")
            self.rez = get_sources_for_radec_method(self.pos[0],self.pos[1],self.radius, summary_ps_fpath)
        elif self.search_type == "full":
            info("this could take awhile")
            self.rez = self.server.get_sources_for_radec(self.pos[0],self.pos[1],self.radius, summary_ps_fpath)
        else:
            self.rez = self.server.get_sources_for_radec_assume_in_src_db(self.pos[0],self.pos[1],self.radius)

        if self.verbose:
            info("Got %i sources." % len(self.rez))

        #20080313 dstarr KLUDGE: I want to call this outside, but
        #  I believe others might call search_pos() in their own code
        #  so I leave this as the default action:
        if not skip_construct_sources:
            self.construct_sources(self.rez, out_xml_fpath=out_xml_fpath)

    def construct_sources(self,slist, out_xml_fpath=''):
        """ slist is a list of source dictionaries
        """
        if type(slist) != type([]):
            warning("slist is not a list")
            self.sources = []
            return
        if len(slist) == 0:
            warning("slist is empty list")
            self.sources = []
            return
        if type(slist[0]) != type({}):
            warning("first entry in slist is not a dictionary")
            self.sources = []
            return
        # 20080127: dstarr thinks this deepcopy() is unnecissary:
        #self.sources = [copy.deepcopy(Source(sdict=s, \
        #                out_xml_fpath=out_xml_fpath,doplot=self.doplot,\
        #           use_source_id_in_xml_fpath= \
        #           self.use_source_id_in_xml_name, \
        #           write_xml=self.write_xml)) for s in slist]
        self.sources = [Source(sdict=s, \
                        out_xml_fpath=out_xml_fpath,doplot=self.doplot,\
                    use_source_id_in_xml_fpath= \
                    self.use_source_id_in_xml_name, \
                    write_xml=self.write_xml) for s in slist]

    def summary_plot(self):
        import matplotlib

        matplotlib.pylab.hold(False)
        matplotlib.pylab.plot([120,111])
        matplotlib.pylab.hold(True)
        rr = []
        dd = []
        for s in self.sources:
            matplotlib.pylab.scatter([s.d['ra']],[s.d['dec']])
            rr.append(s.d['ra'])
            dd.append(s.d['dec'])
        #matplotlib.pylab.ylim( (max(yytrema[0]) + 1,min(yytrema[1]) - 0.3) )
        #matplotlib.pylab.xlim( (min(xxtrema[0]) - 10,max(xxtrema[1]) + 10) )
        #print (max(yytrema[1]) + 1,min(yytrema[0]))
        #print (min(xxtrema[0]) - 10,max(xxtrema[1]) + 10)
        matplotlib.pylab.ylim( (min(dd) - 0.01,max(dd) + 0.01) )
        matplotlib.pylab.xlim( (min(rr) - 0.01,max(rr) + 0.01) )

        matplotlib.pylab.xlabel('RA [deg]')
        matplotlib.pylab.ylabel('DEC [dec]')
        matplotlib.pylab.show()

    def ds9_summary(self,fname="tmp.reg"):
        """
        makes a ds9 region file from all the sources. Source number and the number of obs in each filter is given

        TODO: make error ellipses instead of points
        """
        pream = \
"""
# Region file format: DS9 version 4.0
global color=green font="helvetica 10 normal" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source
fk5
"""
        f = open(fname,"w")
        f.write(pream)
        for s in self.sources:
            (ra,dec) = (str(s.d['ra']),str(s.d['dec']))
            src_id = s.d['src_id']
            vv = s.d['ts'].values()
            ss = [band + "=" + str(len(val['t'])) for band, val in s.d['ts'].items()]
            label = "s" + str(src_id) + ":" + ";".join(ss)
            f.write("point(%s,%s) # point=circle text={%s}\n" % (ra,dec,label))
        f.close()
        print("wrote %s" % fname)

    def get_search_help(self):
        if self.allow_search:
            if self.search_type  == "full":
                print(self.server.system.methodHelp("get_sources_for_radec"))
            else:
                print(self.server.system.methodHelp("get_sources_for_radec_assume_in_src_db"))
        return

    def __del__(self):
        try:
            info("disconnecting from the server")
            del self.server
        except:
            pass

class TestClass:
    """ Testing class for python-nose tests.
    Useful for refactoring and adding new XML schema

        NOTE: Make sure that environment variable is set to:
               PYTHONOPTIMIZE=""
        NOTE: Make sure that no ".pyo" files exist in source directories.

    TO RUN python-nose test in SHELL:
            nosetests --tests=db_importer

        OR more verbosely:
            nosetests -s -vv --tests=db_importer

    TO RUN python-nose test in PDB:

            BREAK on any ERROR:
                nosetests --pdb --tests=db_importer

            BREAK on TEST FAILURE:
            nosetests --pdb-failures --tests=db_importer


    TODO TESTS:
     - read various things from an testing XML file.
     - write a feature & (brute force?) read from xmlfile?
     - write a mag,time epoch & (brute force?) read from xmlfile?
     - write a classification & (brute force?) read from xmlfile?
    """
    def setUp(self):
            """ Performed at the beginning of each test
            """
            self.temp_rw_vosource_fpath = '/tmp/db_importer_tests.vosource.xml'


    def tearDown(self):
            """ Performed at the end of each test
            """
            pass


    def make_assertions_for__vosource_1990af(self,dbi_src):
        """ For $TCP_DIR/Data/1990af.xml
        """
        from nose import tools as nt

        nt.assert_true( dbi_src.x_sdict['src_id'] == 14483)
        nt.assert_true( dbi_src.x_sdict['class'] =='Type Ia Supernovae')
        nt.assert_true( ((dbi_src.x_sdict['ra'] > 323.74216) and
                             (dbi_src.x_sdict['ra'] < 323.74217)))
        nt.assert_true( dbi_src.x_sdict['ts']['B:table4598']['m'][2] == 17.939)
        nt.assert_true( ((dbi_src.x_sdict['ts']['B:table4598']['m_err'][3] > 0.030) and
                             (dbi_src.x_sdict['ts']['B:table4598']['m_err'][3] < 0.032)))
        nt.assert_true( ((dbi_src.x_sdict['ts']['B:table4598']['t'][1] > 2448193.53) and
                             (dbi_src.x_sdict['ts']['B:table4598']['t'][1] < 2448193.55)))


    def make_assertions_for__vosource_tutor12881(self,dbi_src):
        """ For $TCP_DIR/Data/vosource_tutor12881.xml:
        """
        from nose import tools as nt

        nt.assert_true( dbi_src.x_sdict['src_id'] == 12881)
        nt.assert_true( dbi_src.x_sdict['class'] =='RR Lyrae, Fundamental Mode')
        nt.assert_true( ((dbi_src.x_sdict['ra'] > 30.47567) and
                             (dbi_src.x_sdict['ra'] < 30.47568)))
        nt.assert_true( dbi_src.x_sdict['ts']['H:table1384']['m'][2] == 11.5783)
        nt.assert_true( ((dbi_src.x_sdict['ts']['H:table1384']['m_err'][3] > 0.0429) and
                             (dbi_src.x_sdict['ts']['H:table1384']['m_err'][3] < 0.0431)))
        nt.assert_true( ((dbi_src.x_sdict['ts']['H:table1384']['t'][1] > 7904.22188) and
                             (dbi_src.x_sdict['ts']['H:table1384']['t'][1] < 7904.2219)))


    def test_case_parse_vosource_file(self):
        """ Tests related to the parsed vosource xml
        """
        # old TCP vosource:
        vosource_fpath = os.path.expandvars("$TCP_DIR/Data/vosource_tutor12881.xml")
        dbi_src = Source(make_dict_if_given_xml=True,
                             make_xml_if_given_dict=False,
                             doplot=False,
                             xml_handle=vosource_fpath)
        self.make_assertions_for__vosource_tutor12881(dbi_src)

        # TUTOR vosource:
        vosource_fpath = os.path.expandvars("$TCP_DIR/Data/1990af.xml")
        dbi_src = Source(make_dict_if_given_xml=True,
                             make_xml_if_given_dict=False,
                             doplot=False,
                             xml_handle=vosource_fpath)
        self.make_assertions_for__vosource_1990af(dbi_src)




    def test_case_generated_vosource_xml_string(self):
        """ Tests related to writing a internal sdict to VOSource XML string.
        """
            # TODO: test that I want to pickle the test_feature_algorithms's signals_list[0] and open it here
            # ( in the class) and then write out a vosource xml string & then test that all the expected <tags> are in place.
        vosource_fpath = os.path.expandvars("$TCP_DIR/Data/vosource_tutor12881.xml")#old TCP vosource

        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR","") + \
                                              'Software/feature_extract'))
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR","") + \
                      'Software/feature_extract/Code'))
        from Code import generators_importers
        from . import db_importer

        signals_list = []
        gen = generators_importers.from_xml(signals_list)

        gen.generate(xml_handle=vosource_fpath)
        gen.sig.add_features_to_xml_string(gen.signals_list)

        from nose import tools as nt
        nt.assert_true( ((float(str(signals_list[0].properties['data']['multiband']['features']['ecpl'])) > 25.2720) and
                (float(str(signals_list[0].properties['data']['multiband']['features']['ecpl'])) < 25.2721)))
        nt.assert_true( ((float(str(signals_list[0].properties['data']['H:table1384']['features']['median'])) > 11.9414) and
                (float(str(signals_list[0].properties['data']['H:table1384']['features']['median'])) < 11.9416)))

        # TODO: do schema / formatting tests on the xml string :
        #           gen.sig.xml_string

        ### Now write this new VOSource XML to file, read again, and test values/format are correct.
        gen.sig.write_xml(out_xml_fpath=self.temp_rw_vosource_fpath)

        dbi_src = Source(make_dict_if_given_xml=True,
                             make_xml_if_given_dict=False,
                             doplot=False,
                             xml_handle=self.temp_rw_vosource_fpath)

        # NOTE: This function uses new temp XML, but with original assertions:
        self.make_assertions_for__vosource_tutor12881(dbi_src)


if __name__ == "__main__":

    tc = TestClass()
    tc.setUp()
    #tc.test_case_parse_vosource_file()
    tc.test_case_generated_vosource_xml_string()
    tc.tearDown()

    sys.exit()
    setup_logging()
    info("started.")
    dotest1()
    info("finished.")

