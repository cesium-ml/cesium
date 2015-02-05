#!/usr/bin/env python
"""

This is intended to retrieve and parse simbad colors for ASAS and debosscher sources,
 - these sources are contained in the TUTOR database
 - May also retrieve colors from ASAS tables

The retrieval of simbad votable information will be alternated between harvard and strausberg to
have less chance of IP banning, which seems to have happened before in the past.

This task is related to the Active Learning project.

This code is partially adapted from kepler_find_simbd_public_sources.py

And may use some elements of activelearn_utils.py

"""
from __future__ import print_function
from __future__ import absolute_import
import sys, os
import socket
socket.setdefaulttimeout(20) # for urllib2 timeout of urlopen()
import urllib
import urllib2
import cPickle
import gzip
import time
import copy
import pprint
from math import sqrt
from scipy.stats import norm  # for debug plotting
import numpy
import matplotlib.pyplot as pyplot
from numpy import loadtxt


class Database_Utils:
    """ Establish database connections, contains methods related to database tables.
    """
    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def connect_to_db(self):
        import MySQLdb
        if 'tcp_hostname' in self.pars:
            self.tcp_db = MySQLdb.connect(host=self.pars['tcp_hostname'], \
                                          user=self.pars['tcp_username'], \
                                          db=self.pars['tcp_database'],\
                                          port=self.pars['tcp_port'])
            self.tcp_cursor = self.tcp_db.cursor()

        if 'tutor_hostname' in self.pars:
            self.tutor_db = MySQLdb.connect(host=self.pars['tutor_hostname'], \
                                            user=self.pars['tutor_username'], \
                                            db=self.pars['tutor_database'], \
                                            passwd=self.pars['tutor_password'], \
                                            port=self.pars['tutor_port'])
            self.tutor_cursor = self.tutor_db.cursor()


class VOTable_Parse:
    """
    A Class for parsing VOTable xmls

    Intended to have methods inherited by another class.
    """

    # NOTE: no need for a def __init__() since inheriting class will override.


    def load_votable_str(self, votable_str):
        """ Load VOTable string into xml.etree.ElementTree object

        NOTE: should have a seperate function which takes take a stringIO fp or normal file-poiner

        """
        from xml.etree import ElementTree # use the original implementation for ._namespace_map (although some documents say cElementTree is now an earlier implementation
        
        sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                        'Software/feature_extract/Code/extractors'))
        import xmldict

        #ElementTree._namespace_map["http://www.ivoa.net/xml/VOTable/v1.1"] = ''
        # KLUDGE: (as of 20110725 it seems simbad votables now have the following namespace,  which fouls up the xmldict dictionary dependent code.  Tried a couple other ways of removing the namespace reference via xml.etree configs, but with no success.
        votable_str = votable_str.replace("""<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1" ID="http://www.ivoa.net/xml/VOTable/v1.1 http://www.ivoa.net/xml/VOTable/v1.1">""","<VOTABLE>")
        
        elemtree = ElementTree.fromstring(votable_str)
        ###only available in v2.7: ElementTree.register_namespace('{http://www.ivoa.net/xml/VOTable/v1.1}')  
        #blah = ElementTree.QName('{http://www.ivoa.net/xml/VOTable/v1.1}')
        #elemtree = blah.fromstring(votable_str)

        d = xmldict.ConvertXmlToDict(elemtree)
        return d


    # TODO: have some general parsing attribute


    def parse_attrib(self, xml_dict, attrib_name='blah', i_row=None):
        """ Adapted from simbad_id_lookup.py
        v2: taken from kepler_find_simbad_public_sources.py
        v3: using xml.etree.ElementTree and xmldict (from vosource_parse.py)

        NOTE / KLUDGE: if there are more than 1 rows in the table, the first row is used.
           - this seems to be the closest distance source when viewing Simbad webpage.
        """
        b = xml_dict['VOTABLE']['RESOURCE']['TABLE']['FIELD']
        i_col_otype = -1
        for i, elem in enumerate(b):
            if elem['name'] == attrib_name:
                i_col_otype = i
                break
        if i_row != None:
            b = xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR'][i_row]['TD']
        else:
            if type([]) == type(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']):
                #NOTE / KLUDGE: if there are more than 1 rows in the table, the first row is used.
                #   - this seems to be the closest distance source when viewing Simbad webpage.
                b = xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR'][0]['TD']
            else:
                b = xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']['TD']
        return str(b[i_col_otype])


class Get_Colors(Database_Utils, VOTable_Parse):
    """

    Retrieve colors from simbad and possiby ASAS GCVS dataset


    """

    def __init__(self, pars={}):
        self.pars = pars
        self.connect_to_db()


    def query_votable_radec(self, ra=0.0, dec=0.0, rad=2.0, html_prefix=""):
        """ Adapted from simbad_id_lookup.py and simbad.py
        v2: taken from kepler_find_simbad_public_sources.py
        """
        #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"
        #html = "http://simbad.harvard.edu/simbad/sim-coo?"

        params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
                                       'Radius': rad, 'Radius.unit': "arcsec"})
        
        #html = "http://simbad.harvard.edu/simbad/sim-id?"
        #params = urllib.urlencode({'output.format':"VOTABLE","Ident":"HD 27290","NbIdent":1,\
        #                           'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
        f = urllib.urlopen("%s%s" % (html_prefix,params))
        s = f.read()
        f.close()
        #print s
        ### so this works if there is a matching obect (full xml is returned
        #import pdb; pdb.set_trace()
        return s


    def query_votable_srcname(self, rad=2.0, source_name=None, html_prefix=""):
        """ Adapted from simbad_id_lookup.py and simbad.py
        v2: taken from kepler_find_simbad_public_sources.py
        """
        #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"
        #html = "http://simbad.harvard.edu/simbad/sim-coo?"

        #params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
        #                               'Radius': rad, 'Radius.unit': "arcsec"})
        params = urllib.urlencode({'output.format': "VOTABLE", "Ident": source_name})

        #html = "http://simbad.harvard.edu/simbad/sim-id?"
        #params = urllib.urlencode({'output.format':"VOTABLE","Ident":"HD 27290","NbIdent":1,\
        #                           'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
        f = urllib.urlopen("%s%s" % (html_prefix,params))
        s = f.read()
        f.close()
        #print s
        ### so this works if there is a matching obect (full xml is returned
        #import pdb; pdb.set_trace()
        return s



    def query_tutor_sources(self):
        """
        Query sources from the TUTOR mysql database.
          - get source_id, project_id, ra, dec...

        Do this for ASAS and Debosscher projects
    
        """
        source_dict = {'deboss':{'proj_id':123,
                                 'srcid_list':[],
                                 'ra_list':[],
                                 'dec_list':[],
                                 'source_name_list':[],
                                 'class_id':[],
                                 'J':[],
                                 'H':[],
                                 'K':[],
                                 'B':[],
                                 'V':[],
                                 'R':[],
                                 'ref':[],
                                 },
                       'asas':{'proj_id':126,
                               'srcid_list':[],
                               'ra_list':[],
                               'dec_list':[],
                               'source_name_list':[],
                               'class_id':[],
                                 'J':[],
                                 'H':[],
                                 'K':[],
                                 'B':[],
                                 'V':[],
                                 'R':[],
                                 'ref':[],
                                 },
                       }

        
        for proj, proj_dict in source_dict.iteritems():
            select_str = "SELECT source_id, source_ra, source_dec, source_name, class_id FROM sources WHERE project_id=%d" % (proj_dict['proj_id'])
            self.tutor_cursor.execute(select_str)
            results = self.tutor_cursor.fetchall()
            if len(results) == 0:
                raise "ERROR"

            for (source_id, source_ra, source_dec, source_name, class_id) in results:
                proj_dict['srcid_list'].append(int(source_id))
                proj_dict['ra_list'].append(float(source_ra))
                proj_dict['dec_list'].append(float(source_dec))
                proj_dict['source_name_list'].append(source_name)
                proj_dict['class_id'].append(class_id)
              
        return source_dict


    def append_acvs_jhk(self, proj_dict={}, asas_ndarray=None, i_ndarray=None):
        """
        """
        proj_dict['J'].append(asas_ndarray['J'][i_ndarray])
        proj_dict['H'].append(asas_ndarray['H'][i_ndarray])
        proj_dict['K'].append(asas_ndarray['K'][i_ndarray])
        proj_dict['B'].append('NULL')
        proj_dict['V'].append('NULL')
        proj_dict['R'].append('NULL')
        proj_dict['ref'].append('asas_acvs')


    def append_none_jhk(self, proj_dict={}):
        """
        """
        proj_dict['J'].append('NULL')
        proj_dict['H'].append('NULL')
        proj_dict['K'].append('NULL')
        proj_dict['B'].append('NULL')
        proj_dict['V'].append('NULL')
        proj_dict['R'].append('NULL')
        proj_dict['ref'].append('none_simbad')


    def download_votable(self, i=None, ra=None, dec=None, proj_name=None,
                         len_srcid_list=None, src_id=None, fpath=None,
                         do_remove_file=False):
        """
        """
        if do_remove_file:
            os.system("rm " + fpath)
        html_prefix = self.pars['html_prefix_list'][i%2]
        
        votable_str = self.query_votable_radec(ra=ra,
                                               dec=dec,
                                               rad=60.0,   # arcseconds
                                               html_prefix=html_prefix)
        print("%s %d/%d srcid=%d len=%d %s" % (proj_name, i, len_srcid_list, src_id, len(votable_str), html_prefix))
        fp = open(fpath, 'w')
        fp.write(votable_str)
        fp.close()
        time.sleep(1)
        return votable_str


    def download_votable_srcname(self, source_name=None, fpath=None,
                                 do_remove_file=False):
        """
        """
        if do_remove_file:
            os.system("rm " + fpath)
        html_prefix = self.pars['html_srcname_prefix_list'][i%2]
        
        votable_str = self.query_votable_srcname(rad=60.0,   # arcseconds
                                                 source_name=source_name,
                                                 html_prefix=html_prefix)

        #print "%s %d/%d srcid=%d len=%d %s" % (proj_name, i, len_srcid_list, src_id, len(votable_str), html_prefix)
        fp = open(fpath, 'w')
        fp.write(votable_str)
        fp.close()
        time.sleep(0.5) # sleep so that a server is queried one time a second
        return votable_str


    def add_debosscher_SIMBAD_or_ACVS_mags(self, asas_ndarray=None, tutor_source_dict={}):
        """
        Get colors from simbad for ASAS sources

        Get colors from simbad for Debosscher sources

        Get colors from tranx:~/scratch/asas_data/ACVS.1.1 for ASAS

        Determine whether these ASAS ACVS V,J,H,K colors are the same as simbad's 2MASS colors

        Adapted from add_SIMBAD_or_ACVS_mags() for debosscher case rather than ASAS case

        """
        id_list = list(asas_ndarray['ID'])

        for proj_name, proj_dict in tutor_source_dict.iteritems():
            if proj_name == 'asas':
                continue # DEBUG / TESTING ONLY
            for i, src_id in enumerate(proj_dict['srcid_list']):

                fpath = "%s/%d.votable" % (self.pars['votable_cache_dirpath'],
                                           src_id)
                ra =  proj_dict['ra_list'][i]
                dec = proj_dict['dec_list'][i]
                if os.path.exists(fpath):
                    votable_str = open(fpath).read()
                else:
                    votable_str = self.download_votable(i=i, ra=ra, dec=dec, proj_name=proj_name,
                                                        len_srcid_list=len(proj_dict['srcid_list']),
                                                        src_id=src_id, fpath=fpath)
                #i_ndarray = id_list.index(proj_dict['source_name_list'][i])

                if len(votable_str) < 310:
                    #print "NO SIMBAD srcid=%d len=%d" % (src_id, len(votable_str))
                    ### if no simbad match, then we can't do much with Debosscher sources
                    self.append_none_jhk(proj_dict=proj_dict)
                    continue
                if len(votable_str) < 800:
                    if 'Service Temporarily Unavailable' in votable_str:
                        # TODO: need to attempt download of VOTable again.
                        votable_str = self.download_votable(i=i, ra=ra, dec=dec, proj_name=proj_name,
                                                            len_srcid_list=len(proj_dict['srcid_list']),
                                                            src_id=src_id, fpath=fpath, do_remove_file=True)
                        if 'Service Temporarily Unavailable' in votable_str:
                            raise

                        if len(votable_str) < 310:
                            #print "NO SIMBAD srcid=%d len=%d" % (src_id, len(votable_str))
                            ### if no simbad match, then we can't do much with Debosscher sources
                            self.append_none_jhk(proj_dict=proj_dict)
                            continue
                    else:
                        raise

                xml_dict = self.load_votable_str(votable_str)

                votable_i_row = None # Default value which means we use the [0] or only row in VOTable

                if type([]) == type(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']):
                    for j_row in range(len(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR'])):
                        ### Then we have more than more than one source in VOTable
                        #import pdb; pdb.set_trace()
                        #print

                        try:
                            dist =  float(self.parse_attrib(xml_dict, attrib_name="DISTANCE", i_row=j_row))
                        except:
                            ### This is not a useful row, since there is no J, K info
                            print('           %d This is not a useful row, since there is no J, K info' % (j_row))
                            continue

                        if (dist < 70):
                            ### I chose these mag cuts due to a couple sources which have <0.25 mag differences between ACVS table and matching simbad source (225975, 227503)
                            votable_i_row = j_row
                            print("  JK MATCH: %d dist=%f" % (j_row, dist))
                            break # we found the matching source.  get out of loop
                        else:
                            print("- NO MATCH: %d dist=%f" % (j_row, dist))

                    if votable_i_row is None:
                        #print "  JK None", src_id
                        ### if no simbad match, then we can't do much with Debosscher sources
                        self.append_none_jhk(proj_dict=proj_dict)
                        continue # We cannot get any useful info from Simbad since no sources match/have J,K, so only use ASAS ACVS info
                        
                try:
                    dist =  float(self.parse_attrib(xml_dict, attrib_name="DISTANCE", i_row=votable_i_row))
                except:
                    # We get here when no J info can be retrieved from Simbad VOTable.
                    #    - this means we have to use whatever existed in the ACVS table for JHK
                    #       - since we require a close J-band match of simbad source and ACVS source 
                    ### if no simbad match, then we can't do much with Debosscher sources
                    self.append_none_jhk(proj_dict=proj_dict)
                    continue # We cannot get any useful info from Simbad since no sources match/have J, so only use ASAS ACVS info

                if ((dist <= 0.33) and ('HIP' in proj_dict['source_name_list'][i])):
                    # NOTE: the JK_diff cut doesnt seem to cut out anything in first 20% of ASAS
                    #prefix = "<0.33   "
                    pass
                else:
                    #prefix = "!!!MISS"
                    ### if no simbad match, then we can't do much with Debosscher sources
                    self.append_none_jhk(proj_dict=proj_dict)
                    continue
                """
                print "%s %d dist=%6.3f J=%5.5s B=%5.5s V=%5.5s R=%5.5s I=%5.5s u=%5.5s %s" % ( \
                                      prefix,
                                      src_id,
                                      dist,
                                      self.parse_attrib(xml_dict, attrib_name="J", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="B", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="V", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="R", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="I", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="u", i_row=votable_i_row),
                                      proj_dict['source_name_list'][i],
                                      )
                """
                # Now we append the SIMBAD JHK, B, V
                for filt in ['J', 'H', 'K', 'B', 'V', 'R']:
                    try:
                        val = float(self.parse_attrib(xml_dict, attrib_name=filt, i_row=votable_i_row))
                    except:
                        val = 'NULL'
                    proj_dict[filt].append(val)

                proj_dict['ref'].append('debos_simbad')

                #print "%d i=%d J=%d B=%d" % (src_id, i, len(proj_dict['J']), len(proj_dict['B']))
                #import pdb; pdb.set_trace()
                #print
                    

        

    def add_SIMBAD_or_ACVS_mags(self, asas_ndarray=None, tutor_source_dict={}):
        """
        Get colors from simbad for ASAS sources

        Get colors from simbad for Debosscher sources

        Get colors from tranx:~/scratch/asas_data/ACVS.1.1 for ASAS

        Datermine whether these ASAS ACVS V,J,H,K colors are the same as simbad's 2MASS colors

        """
        id_list = list(asas_ndarray['ID'])

        for proj_name, proj_dict in tutor_source_dict.iteritems():
            if proj_name == 'deboss':
                continue # DEBUG / TESTING ONLY
            for i, src_id in enumerate(proj_dict['srcid_list']):

                fpath = "%s/%d.votable" % (self.pars['votable_cache_dirpath'],
                                           src_id)
                ra =  proj_dict['ra_list'][i]
                dec = proj_dict['dec_list'][i]
                if os.path.exists(fpath):
                    votable_str = open(fpath).read()
                else:
                    votable_str = self.download_votable(i=i, ra=ra, dec=dec, proj_name=proj_name,
                                                        len_srcid_list=len(proj_dict['srcid_list']),
                                                        src_id=src_id, fpath=fpath)
                i_ndarray = id_list.index(proj_dict['source_name_list'][i])

                if len(votable_str) < 310:
                    #print "NO SIMBAD srcid=%d len=%d" % (src_id, len(votable_str))
                    self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                    continue
                if len(votable_str) < 800:
                    if 'Service Temporarily Unavailable' in votable_str:
                        # TODO: need to attempt download of VOTable again.
                        votable_str = self.download_votable(i=i, ra=ra, dec=dec, proj_name=proj_name,
                                                            len_srcid_list=len(proj_dict['srcid_list']),
                                                            src_id=src_id, fpath=fpath, do_remove_file=True)
                        if 'Service Temporarily Unavailable' in votable_str:
                            raise

                        if len(votable_str) < 310:
                            #print "NO SIMBAD srcid=%d len=%d" % (src_id, len(votable_str))
                            self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                            continue
                    else:
                        raise

                xml_dict = self.load_votable_str(votable_str)

                votable_i_row = None # Default value which means we use the [0] or only row in VOTable

                if type([]) == type(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']):
                    for j_row in range(len(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR'])):
                        ### Then we have more than more than one source in VOTable
                        try:
                            # ??? why is j_diff and k_diff not abs()?
                            j_diff = float(self.parse_attrib(xml_dict, attrib_name="J", i_row=j_row)) - asas_ndarray['J'][i_ndarray]
                            k_diff = float(self.parse_attrib(xml_dict, attrib_name="K", i_row=j_row)) - asas_ndarray['K'][i_ndarray]
                            JK_diff = abs((float(self.parse_attrib(xml_dict, attrib_name="J", i_row=j_row)) -
                                           float(self.parse_attrib(xml_dict, attrib_name="K", i_row=j_row))) -
                                          (asas_ndarray['J'][i_ndarray] - asas_ndarray['K'][i_ndarray]))
                            dist =  float(self.parse_attrib(xml_dict, attrib_name="DISTANCE", i_row=j_row))
                        except:
                            ### This is not a useful row, since there is no J, K info
                            print('           %d This is not a useful row, since there is no J, K info' % (j_row))
                            continue

                        #if ((abs(j_diff) <= 0.25) and (abs(k_diff) <= 0.25)):
                        if ((abs(j_diff) <= 0.24) and (JK_diff <= 0.34)):
                            ### I chose these mag cuts due to a couple sources which have <0.25 mag differences between ACVS table and matching simbad source (225975, 227503)
                            votable_i_row = j_row
                            print("  JK MATCH: %d dJ=%f  dK=%f  dJK=%f  dist=%f" % (j_row, j_diff, k_diff, JK_diff, dist))
                            break # we found the matching source.  get out of loop
                        else:
                            print("- NO MATCH: %d dJ=%f  dK=%f  dJK=%f  dist=%f" % (j_row, j_diff, k_diff, JK_diff, dist))

                    if votable_i_row is None:
                        #print "  JK None", src_id
                        self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                        continue # We cannot get any useful info from Simbad since no sources match/have J,K, so only use ASAS ACVS info
                        
                try:
                    j_diff = float(self.parse_attrib(xml_dict, attrib_name="J", i_row=votable_i_row)) - asas_ndarray['J'][i_ndarray]
                    k_diff = float(self.parse_attrib(xml_dict, attrib_name="K", i_row=votable_i_row)) - asas_ndarray['K'][i_ndarray]
                    JK_diff = abs((float(self.parse_attrib(xml_dict, attrib_name="J", i_row=votable_i_row)) -
                                   float(self.parse_attrib(xml_dict, attrib_name="K", i_row=votable_i_row))) -
                                  (asas_ndarray['J'][i_ndarray] - asas_ndarray['K'][i_ndarray]))

                    dist =  float(self.parse_attrib(xml_dict, attrib_name="DISTANCE", i_row=votable_i_row))
                except:
                    # We get here when no J info can be retrieved from Simbad VOTable.
                    #    - this means we have to use whatever existed in the ACVS table for JHK
                    #       - since we require a close J-band match of simbad source and ACVS source 
                    self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                    continue # We cannot get any useful info from Simbad since no sources match/have J, so only use ASAS ACVS info

                if (JK_diff > 0.34):
                    self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                    continue

                if dist <= 6:
                    # NOTE: the JK_diff cut doesnt seem to cut out anything in first 20% of ASAS
                    #prefix = "ok     " #"<6 DIST"
                    pass
                elif abs(j_diff) <= 0.24:
                    #prefix = "ok     " #"sim MAG" # These are OK associations
                    pass
                elif ((abs(j_diff) <= 3.54) and (dist <= 34.3)):
                    #prefix = "ok" #"BAD <34"
                    pass
                else:
                    #prefix = "!!!MISS"
                    self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                    continue
                """
                print "%s %d dJ=%6.3f dist=%6.3f dJK=%6.3f J=%5.5s B=%5.5s V=%5.5s R=%5.5s I=%5.5s u=%5.5s %s" % ( \
                                      prefix,
                                      src_id,
                                      j_diff,
                                      dist,
                                      JK_diff,
                                      self.parse_attrib(xml_dict, attrib_name="J", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="B", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="V", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="R", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="I", i_row=votable_i_row),
                                      self.parse_attrib(xml_dict, attrib_name="u", i_row=votable_i_row),
                                      proj_dict['source_name_list'][i],
                                      )
                """
                # Now we append the SIMBAD JHK, B, V
                for filt in ['J', 'H', 'K', 'B', 'V', 'R']:
                    try:
                        val = float(self.parse_attrib(xml_dict, attrib_name=filt, i_row=votable_i_row))
                    except:
                        val = 'NULL'
                    proj_dict[filt].append(val)

                proj_dict['ref'].append('asas_simbad')

                print("%d i=%d J=%d B=%d" % (src_id, i, len(proj_dict['J']), len(proj_dict['B'])))
                #import pdb; pdb.set_trace()
                #print


    def get_SIMBAD_mags_for_srcname(self, source_name='', query_source_name = ''):
        """  This queries SIMBAD for a source_name
        - stores the result xml in a special directory source_name dir
        - then parses the (ra, dec)
           - the (ra, dec) will be used for for nomad query,
        ??? maybe parse BVRJHK for nomad match?

        Adapted from add_SIMBAD_or_ACVS_mags()
        """
        if len(query_source_name) == 0:
            query_source_name = source_name

        fpath = "%s/%s.votable" % (self.pars['votable_srcname_cache_dirpath'],
                                   source_name)

        if os.path.exists(fpath):
            votable_str = open(fpath).read()
        else:
            votable_str = self.download_votable_srcname(source_name=query_source_name,
                                                        fpath=fpath)
        #i_ndarray = id_list.index(proj_dict['source_name_list'][i])

        if len(votable_str) < 310:
            print("NO SIMBAD srcname=%s len=%d" % (query_source_name, len(votable_str)))
            #self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
            # ?????   continue
            return {}
        if len(votable_str) < 800:
            if 'Service Temporarily Unavailable' in votable_str:
                # TODO: need to attempt download of VOTable again.
                votable_str = self.download_votable_srcname(source_name=query_source_name,
                                                        fpath=fpath)
                if 'Service Temporarily Unavailable' in votable_str:
                    raise

                if len(votable_str) < 310:
                    print("NO SIMBAD srcname=%s len=%d" % (query_source_name, len(votable_str)))
                    #self.append_acvs_jhk(proj_dict=proj_dict, asas_ndarray=asas_ndarray, i_ndarray=i_ndarray)
                    # ???? continue
                    return {}
            if 'dentifier has an incorrect format' in votable_str:
                print("NO SIMBAD (INCORRECT FORMAT) srcname=%s len=%d" % (query_source_name, len(votable_str)))
                return {}
            elif 'dentifier not found in the database' in votable_str:
                print("NO SIMBAD (not in database) srcname=%s len=%d" % (query_source_name, len(votable_str)))
                return {}
            else:
                print("NO SIMBAD (raise) srcname=%s len=%d" % (query_source_name, len(votable_str)))
                raise

        xml_dict = self.load_votable_str(votable_str)

        if type([]) == type(xml_dict['VOTABLE']['RESOURCE']['TABLE']['DATA']['TABLEDATA']['TR']):
            print("TABLEDATA is a list, not expected. source_name=", source_name)
            raise 
        out_dict = {'ra':float(self.parse_attrib(xml_dict, attrib_name="RA", i_row=None)),
                    'dec':float(self.parse_attrib(xml_dict, attrib_name="DEC", i_row=None)),
                    }
        #try:
        if 1:

            for filt in ['J', 'H', 'K', 'B', 'V', 'R']:
                try:
                    val = float(self.parse_attrib(xml_dict, attrib_name=filt, i_row=None))
                    out_dict[filt] = val
                except:
                    pass
                #    val = 'NULL'
                #out_dict[filt] = val
        #except:
        #    pass

        return out_dict
 

    def insert_mags_into_db(self, tutor_source_dict={}):
        """
        Table: (to be created in tranx:source_test_db)

        ENUM('asas_simbad', 'asas_acvs', 'debos_simbad', 'none_simbad')
        
        CREATE TABLE activelearn_filter_mags (source_id INTEGER, ref VARCHAR(12), class_id INTEGER, b FLOAT, v FLOAT, r FLOAT, j FLOAT, h FLOAT, k FLOAT, jh FLOAT, hk FLOAT, jk FLOAT, vj FLOAT, bj FLOAT, bv FLOAT, vr FLOAT, extinct_bv FLOAT, PRIMARY KEY (source_id));

        # TODO: maybe make sure that only sources with enough color information are added
        #   - initially add everything
        
        """
        sources_insert_list = ["INSERT INTO activelearn_filter_mags (source_id, ref, class_id, b, v, r, j, h, k, jh, hk, jk, vj, bj, bv, vr, extinct_bv) VALUES "]

        #for proj_name, proj_dict in tutor_source_dict.iteritems():
        if 1:
            proj_dict = tutor_source_dict
            for i, src_id in enumerate(proj_dict['srcid_list']):

                if proj_dict['class_id'][i] is None:
                    class_id = 'NULL'
                else:
                    class_id = str(proj_dict['class_id'][i])

                try:
                    JH = proj_dict['J'][i] - proj_dict['H'][i]
                except:
                    JH = 'NULL'

                try:
                    HK = proj_dict['H'][i] - proj_dict['K'][i]
                except:
                    HK = 'NULL'
                    
                try:
                    JK = proj_dict['J'][i] - proj_dict['K'][i]
                except:
                    JK = 'NULL'

                try:
                    VJ = proj_dict['V'][i] - proj_dict['J'][i]
                except:
                    VJ = 'NULL'

                try:
                    BJ = proj_dict['B'][i] - proj_dict['J'][i]
                except:
                    BJ = 'NULL'

                try:
                    BV = proj_dict['B'][i] - proj_dict['V'][i]
                except:
                    BV = 'NULL'
                
                try:
                    VR = proj_dict['V'][i] - proj_dict['R'][i]
                except:
                    VR = 'NULL'

                
                insert_tup = (proj_dict['srcid_list'][i],
                              proj_dict['ref'][i],
                              class_id,
                              str(proj_dict['B'][i]),
                              str(proj_dict['V'][i]),
                              str(proj_dict['R'][i]),
                              str(proj_dict['J'][i]),
                              str(proj_dict['H'][i]),
                              str(proj_dict['K'][i]),
                              str(JH),
                              str(HK),
                              str(JK), 
                              str(VJ),
                              str(BJ),
                              str(BV),
                              str(VR),
                              proj_dict['extinct_bv'][i],
                    )

                #sources_insert_list.append("""(%d, '%s', %d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f), """ %  insert_tup)
                sources_insert_list.append("""(%d, '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %f), """ %  insert_tup)
        import pdb; pdb.set_trace()
        print()


        sources_insert_str = ''.join(sources_insert_list)[:-2]
        self.tcp_cursor.execute(sources_insert_str)

        import pdb; pdb.set_trace()
        print()


    def fill_webplot_data_files(self):
        """ Fill data files of Rows:(class_id, J, J-K) form.
        Which will be read by the ALLStars web-tool for FLOT plotting.
        """
        ##########################
        select_str = 'SELECT class_id, k, j - h FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/k_jh.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()

        ##########################
        select_str = 'SELECT class_id, j-h, h-k FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/jh_hk.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()

        ##########################
        select_str = 'SELECT class_id, b-j, j-k FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/bj_jk.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()

        ##########################
        select_str = 'SELECT class_id, b-j, h-k FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/bj_hk.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()

        ##########################
        select_str = 'SELECT class_id, b-v, j-k FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/bv_jk.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()

        ##########################
        select_str = 'SELECT class_id, b-v, v-j FROM activelearn_filter_mags WHERE ref="nomad"'
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        fpath = "%s/bv_vj.dat" % (self.pars['filtmag_dirpath'])
        if os.path.exists(fpath):
            os.system("rm " + fpath)
        fp = open(fpath, 'w')
        for row in results:
            try:
                fp.write("%d %f %f\n" % row)
            except:
                pass # we skip writing sources where the mags and mag_diffs are None
        fp.close()



    def fill_per_amp_webdat_file(self, all_srcid_classid={}):
        """ Fill per_amp_debosscher.dat file which is used in ALLStars plot.
        """
        if os.path.exists(self.pars['peramp_fpath']):
            os.system("rm " + self.pars['peramp_fpath'])

        fp = open(self.pars['peramp_fpath'], 'w')

        for src_id, class_id in all_srcid_classid.iteritems():
            select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_freq_0' AND src_id=%d" % (src_id + 100000000)
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            period = 1. / results[0][0]

            select_str = "SELECT feat_val FROM source_test_db.feat_values JOIN feat_lookup USING (feat_id) WHERE filter_id=8 AND feat_name='freq1_harmonics_amplitude_0' AND src_id=%d" % (src_id + 100000000)
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            amplitude = results[0][0]

            fp.write("%d %f %f\n" % (class_id, amplitude, period))
        fp.close()

        import pdb; pdb.set_trace()
        print()


    def add_tutor_classids(self, tutor_source_dict={}, proj_id=None, srcid_index={}):
        """ Add class_ids for all sources in TUTOR database, for a proj_id
        """
        select_str = "SELECT source_id, class_id FROM sources WHERE project_id=%d" % (proj_id)
        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        all_srcid_classid = {}
        for (src_id, class_id) in results:
            all_srcid_classid[src_id] = class_id
            if src_id in srcid_index:
                ### Only a subset of the sources have NOMAD source matches
                tutor_source_dict['class_id'][srcid_index[src_id]] = class_id
        return all_srcid_classid


    def add_AL_addToTrain_classids(self, tutor_source_dict={}, srcid_index={}):
        """
        """

        ### From activelearn_utils.py::pars{}
        user_classifs_fpaths = { \
            1:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_1.dat'),
            2:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_2.dat'),
            3:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_3.dat'),
            4:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_4.dat'),
            5:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_5.dat'),
            6:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_6.dat'),
            7:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_7.dat'),
            8:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_8.dat'),
            9:os.path.expandvars('$TCP_DIR/Data/allstars/AL_addToTrain_9.dat'),
            #10:os.path.expandvars('$TCP_DIR/Data/allstars/AL_SIMBAD_confirmed.dat'), # SIMBAD confirmed sources
        }

        all_srcid_classid = {}
        for n, fpath in user_classifs_fpaths.iteritems():
            data = loadtxt(fpath, dtype={'names': ('src_id', 'class_id'),
                                         'formats': ('i4', 'i4')})
            for i, src_id in enumerate(data['src_id']):
                all_srcid_classid[src_id] = data['class_id'][i]
                if src_id in srcid_index:
                    ### Only a subset of the sources have NOMAD source matches
                    tutor_source_dict['class_id'][srcid_index[src_id]] = data['class_id'][i]
        return all_srcid_classid


    def parse_dict_from_bestnomadsrclist(self):
        """ Parse best_nomad_src_list files and fill dict
        in order to later fil activelearn_filter_mags table
        """

        data = loadtxt(self.pars['best_nomad_src_list_fpath'],
                                           dtype={'names': ('srcid_list', 'B', 'V', 'R', 'J', 'H', 'K', 'extinct_bv'),
                                                  'formats': ('i4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')})


        tutor_source_dict = {'srcid_list':data['srcid_list'],
                             'B':data['B'],
                             'V':data['V'],
                             'R':data['R'],
                             'J':data['J'],
                             'H':data['H'],
                             'K':data['K'],
                             'extinct_bv':data['extinct_bv'],
                             'ref':['nomad']*len(data['srcid_list']),
                             'class_id':[None]*len(data['srcid_list'])}

        srcid_index = {}
        for i, srcid in enumerate(tutor_source_dict['srcid_list']):
            srcid_index[srcid] = i

        ### Add all Debosscher sources which we have NOMAD source matches for:
        all_srcid_classid = self.add_tutor_classids(tutor_source_dict=tutor_source_dict,
                                                    srcid_index=srcid_index,
                                                    proj_id=123)

        all_srcid_classid_2 = self.add_AL_addToTrain_classids(tutor_source_dict=tutor_source_dict,
                                        srcid_index=srcid_index)                                    
        all_srcid_classid.update(all_srcid_classid_2)
        return {'tutor_source_dict':tutor_source_dict,
                'all_srcid_classid':all_srcid_classid}
                


class Get_Colors_Using_Nomad(Database_Utils):
    """
    Retrieve colors from NOMAD for TUTOR sources.

    NOTE: to be run on betsy, for now (where NOMAD / cdsclient resides)

    """

    def __init__(self, pars={}):
        self.pars = pars
        try:
            self.connect_to_db()
        except:
            pass # for kepler_asas.py use

        ### This is for applying a trained RandomForest Active Learned classifier:
        algorithms_dirpath = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')
        sys.path.append(algorithms_dirpath)

        import rpy2_classifiers
        self.rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algorithms_dirpath)
        from rpy2.robjects.packages import importr
        from rpy2 import robjects
        self.robjects = robjects
        
        if 'classifier_filepath' in self.pars:
            r_classifier = self.pars['classifier_filepath']
        else:
            r_classifier = '/home/dstarr/scratch/nomad_asas_acvs_classifier/rf_trained_classifier.robj' # from citris33
        r_str = '''
        load(file="%s")
        ''' % (r_classifier)
        robjects.r(r_str)


    def get_source_dict(self, projid_list=[]):
        """
        """
        source_dict = {'projid_list':[],
                       'srcid_list':[],
                       'ra_list':[],
                       'dec_list':[],}
        
        for proj_id in projid_list:
            #select_str = "SELECT source_id, source_ra, source_dec, source_name, class_id FROM sources WHERE project_id=%d" % (proj_dict['proj_id'])
            select_str = "SELECT source_id, source_ra, source_dec FROM sources WHERE project_id=%d ORDER BY source_id" % (proj_id)
            self.tutor_cursor.execute(select_str)
            results = self.tutor_cursor.fetchall()
            if len(results) == 0:
                raise "ERROR"

            for (source_id, source_ra, source_dec) in results:
                source_dict['srcid_list'].append(int(source_id))
                source_dict['ra_list'].append(float(source_ra))
                source_dict['dec_list'].append(float(source_dec))

        return source_dict


    def get_linear_source_dict_from_tcpdb(self, projid_list=[]):
        """ Initialize tables on tranx:mysqldb:database=source_test_db:
        
CREATE TABLE linear_objects (id INT UNSIGNED, ra DOUBLE, decl DOUBLE, n_good_obj SMALLINT UNSIGNED, mag FLOAT, retrieved BOOLEAN DEFAULT FALSE, PRIMARY KEY (id), INDEX(n_good_obj, retrieved));

LOAD DATA INFILE '/media/raid_0/object_pg_copy.dat__5cols' INTO TABLE linear_objects FIELDS TERMINATED BY ' ';

        """
        source_dict = {'srcid_list':[],
                       'ra_list':[],
                       'dec_list':[],
                       'nobj_list':[],
                       'mag_list':[],}

        # TODO: want to include some is_retrieved == False index
        select_str = "SELECT id, ra, decl, n_good_obj, mag FROM linear_objects WHERE retrieved=FALSE ORDER BY n_good_obj DESC LIMIT 100"
        self.tcp_cursor.execute(select_str)
        results = self.tcp_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        for (source_id, source_ra, source_dec, nobj, mag) in results:
            source_dict['srcid_list'].append(int(source_id))
            source_dict['ra_list'].append(float(source_ra))
            source_dict['dec_list'].append(float(source_dec))
            source_dict['nobj_list'].append(int(nobj))
            source_dict['mag_list'].append(float(mag))
        return source_dict


    def get_uningested_source_dict_from_tcp(self, id_list=[]):
        """ Adapted from get_linear_source_dict_from_tcpdb()

        """
        source_dict = {'srcid_list':[],
                       'ra_list':[],
                       'dec_list':[],
                       'nobj_list':[],
                       'mag_list':[],}

        for objid in id_list:
            select_str = "SELECT id, ra, decl, n_good_obj, mag FROM linear_objects WHERE retrieved=FALSE AND id=%d" % (objid)
            self.tcp_cursor.execute(select_str)
            results = self.tcp_cursor.fetchall()
            if len(results) == 0:
                continue
            for (source_id, source_ra, source_dec, nobj, mag) in results:
                source_dict['srcid_list'].append(int(source_id))
                source_dict['ra_list'].append(float(source_ra))
                source_dict['dec_list'].append(float(source_dec))
                source_dict['nobj_list'].append(int(nobj))
                source_dict['mag_list'].append(float(mag))
        print('USED:', len(source_dict['srcid_list']))
        return source_dict


    def update_table_retrieved(self, sourcename_list=[]):
        """ Update the RDB table that sources have been retrieved. 
        """
        insert_list = ["INSERT INTO linear_objects (id, retrieved) VALUES "]

        for src_name in sourcename_list:
            insert_list.append('(%d, TRUE), ' % (src_name))

            if len(insert_list) > 10000:
                insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE retrieved=VALUES(retrieved)"
                self.tcp_cursor.execute(insert_str)
                insert_list = ["INSERT INTO linear_objects (id, retrieved) VALUES "]

        if len(insert_list) > 1:
            insert_str = ''.join(insert_list)[:-2] + " ON DUPLICATE KEY UPDATE retrieved=VALUES(retrieved)"
            self.tcp_cursor.execute(insert_str)


    def get_nomad_sources_for_ra_dec(self, ra=None, dec=None,
                                     avg_epoch=None,
                                     require_jhk=True):
        """
        Example query:
           findnomad1 304.1868910 -0.7529220 -E 1998.1 -rs 60 -m 30 -lmJ 15.-16.
           -m num results to retrieve
           -rs arcsec radius query
           
        """
        self.pars.update({'nomad_radius':120, # 60
                          'nomad_n_results':30})
        
        flags  =[]
        if avg_epoch != None:
            flags.append("-E %d" % (avg_epoch))

        if dec < 0:
            dec_str = str(dec)
        else:
            dec_str = '+' + str(dec)

        exec_str = "findnomad1 %lf %s -rs %d -m %d %s" % (ra, dec_str, self.pars['nomad_radius'],
                                                           self.pars['nomad_n_results'],
                                                           ' '.join(flags))
        (a,b,c) = os.popen3(exec_str)
        a.close()
        c.close()
        lines_str = b.read()
        b.close()

        out_dict = {'dist':[],
                    'B':[],
                    'V':[],
                    'R':[],
                    'J':[],
                    'H':[],
                    'K':[],
                    'ra':[],
                    'dec':[],
                    }

        lines = lines_str.split('\n')
        for line in lines:
            if len(line) == 0:
                continue
            if line[0] == '#':
                continue
            elems = line.split('|')

            radec_tup_long = elems[2].split()
            if '-' in radec_tup_long[0]:
                radec_tup = radec_tup_long[0].split('-')
                ra_nomad_src = float(radec_tup[0])
                dec_nomad_src = -1. * float(radec_tup[1])
            elif '+' in radec_tup_long[0]:
                radec_tup = radec_tup_long[0].split('+')
                ra_nomad_src = float(radec_tup[0])
                dec_nomad_src = float(radec_tup[1])
            else:
                raise # there should be a ra, dec in the nomad string
            
            color_str_list = []
            corr_str = elems[5].replace(' T ', '  ').replace(' Y ', '  ')
            for m_str in corr_str.split():
                color_str_list.append(m_str[:-1])
            color_str_list.extend(elems[6].split())
            #print line
            if len(color_str_list) != 6:
                import pdb; pdb.set_trace()
                print() # DEBUG ONLY
                continue

            mag_dict = {}
            for i_band, band_name in enumerate(['B', 'V', 'R', 'J', 'H', 'K']):
                if '--' in color_str_list[i_band]:
                    mag_dict[band_name] = None
                else:
                    mag_dict[band_name] = float(color_str_list[i_band])
    
            dist_str = elems[8][elems[8].find(';')+1:]
            dist = float(dist_str.strip())


            if require_jhk:
                if ((mag_dict['J'] is None) or (mag_dict['H'] is None) or (mag_dict['K'] is None)):
                    continue # skip this source
                
            
            out_dict['ra'].append(ra_nomad_src)
            out_dict['dec'].append(dec_nomad_src)
            out_dict['dist'].append(dist)
            out_dict['B'].append(mag_dict['B'])
            out_dict['V'].append(mag_dict['V'])
            out_dict['R'].append(mag_dict['R'])
            out_dict['J'].append(mag_dict['J'])
            out_dict['H'].append(mag_dict['H'])
            out_dict['K'].append(mag_dict['K'])
                        
        return out_dict  # NOTE: the order should be by distance from given source


    ##OLD / OBSOLETE:
    def get_match_source_index(self, nomad_sources={},
                               tutor_mags={},
                               other_mags={},
                               set_nomad_sources=None,
                               set_tutor_mags=None,
                               set_other_mags=None):
        """
Constraints:
  - (for all nomad sources) #I think we should consider several sources if within the radius
     - if within 10''
        - if 2 TUTOR filters match NOMAD filters (no ASAS), get color differes & compare
        - elif 3 ACVS (JHK) filters match NOMAD (yes ASAS), get color differes & compare
        - elif 1 TUTOR filter matches NOMAD: compare avg mags within ~2mag leeway
        - else continue
 - (for closest radius match)
     - if within 2''
        - then match
  - (for all nomad sources) #I think we should consider several sources if within the radius
     - if within 30''
        - if 2 TUTOR filters match NOMAD filters (no ASAS), get color differes & compare
        - elif 3 ACVS (JHK) filters match NOMAD (yes ASAS), get color differes & compare
        - elif 1 TUTOR filter matches NOMAD: compare avg mags within ~2mag leeway
        - else continue
  - NO MATCH, otherwise
        """
        i_chosen = None
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 10.0:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_tutor = tutor_mags['J'] - tutor_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_tutor - color_diff_nomad) < 0.34:
                        i_chosen = i
                        print("match: %d dist <= 10.0 & abs(color_diff_tutor(%f) - color_diff_nomad(%f)) < 0.34 dist=%f tutor_J=%f nomad_J=%f" % (i, color_diff_tutor, color_diff_nomad, dist, tutor_mags['J'], nomad_sources['J'][i]))
                        return i_chosen # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 10.0:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_other = other_mags['J'] - other_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_other - color_diff_nomad) < 0.34:
                        i_chosen = i
                        print("match: %d dist <= 10.0 & abs(color_diff_other(%f) - color_diff_nomad(%f)) < 0.34 dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        return i_chosen # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 10.0:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (len(color_intersection) >= 1):
                    band_match_count = 0
                    for band in list(color_intersection):
                        if nomad_sources[band][i] is None:
                            continue
                        # KLUDGE:  untested number 0.5:
                        if abs(tutor_mags[band] - nomad_sources[band][i]) <= 0.5:
                            band_match_count += 1
                    if len(color_intersection) == band_match_count:
                        i_chosen = i
                        print("match: %d dist <= 10.0 & abs(tutor_mags[band] - nomad_sources[band]) <= 0.5; dist=%f nomad_V=%s tutor_V=%s %s %s" % (i, dist, str(nomad_sources['V'][i]), str(tutor_mags['V']), str(tutor_mags),  pprint.pformat([(k, nomad_sources[k][i]) for k in nomad_sources.keys()])))
                        return i_chosen # Found matching source
                        
        if nomad_sources['dist'][0] <= 2.0:
            print("match: nomad_sources['dist'][0] <= 2.0", nomad_sources['dist'][0], str(tutor_mags), '\n', pprint.pformat([(k, nomad_sources[k][0]) for k in nomad_sources.keys()]))
            return 0 # Found matching source

        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 30.0:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_tutor = tutor_mags['J'] - tutor_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_tutor - color_diff_nomad) < 0.34:
                        i_chosen = i
                        print("match: %d dist <= 30.0 & abs(color_diff_tutor(%f) - color_diff_nomad(%f)) < 0.34 dist=%f tutor_J=%f nomad_J=%f" % (i, color_diff_tutor, color_diff_nomad, dist, tutor_mags['J'], nomad_sources['J'][i]))
                        return i_chosen # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 30.0:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_other = other_mags['J'] - other_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_other - color_diff_nomad) < 0.34:
                        i_chosen = i
                        print("match: %d dist <= 30.0 & abs(color_diff_other(%f) - color_diff_nomad(%f)) < 0.34 dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        return i_chosen # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= 30.0:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (len(color_intersection) >= 1):
                    band_match_count = 0
                    for band in list(color_intersection):
                        if nomad_sources[band][i] is None:
                            continue
                        # KLUDGE:  untested number 0.5:
                        if abs(tutor_mags[band] - nomad_sources[band][i]) <= 0.5:
                            band_match_count += 1
                    if len(color_intersection) == band_match_count:
                        i_chosen = i
                        print("match: %d dist <= 30.0 & abs(tutor_mags[band] - nomad_sources[band]) <= 0.5; dist=%f nomad_V=%s tutor_V=%s %s %s" % (i, dist, str(nomad_sources['V'][i]), str(tutor_mags['V']), str(tutor_mags), pprint.pformat([(k, nomad_sources[k][i]) for k in nomad_sources.keys()])))
                        return i_chosen # Found matching source
        return i_chosen
    



    def get_match_source_index__ActLearn_RandomForest(self, nomad_sources={},
                                             tutor_mags={},
                                             other_mags={},
                                             set_nomad_sources=None,
                                             set_tutor_mags=None,
                                             set_other_mags=None,
                                             cuts={},
                                             debug=False):
        """ This is the newest Nomad / simbad classifier (2012-03-26).
        Uses Active-learned trained RandomForest (R) classifier
             which is trained by nomad_colors_assoc_activelearn.py

        Some of this is adapted from nomad_colors_assoc_activelearn.py
            -> actlearn_randomforest__load_test_train_data_into_R()
        
        """
        i_chosen = None
        ### Not applicable to current ASAS sources (no tutor J, K)

        # ? how to get the needed features?
        # ? where is the best_nomad_src_list filled? This is done later:
        #   - update_bestnomad_list_file(best_nomad_lists=best_nomad_sources)

        # TODO: if I store the data into a arff file, then can just use nomad_colors_assoc_activelearn.py:parse_arff_files()
        #    to fill the train dictionaries.

        ####### test: ( TODO: want some arff strings outputted for parse_arff_files()):
        str_list = self.store_nomad_sources_for_classifier(srcid=1, # just bogus
                                                i_chosen=0, # this is bogus and is not used in making predictions
                                                nomad_dict=nomad_sources,
                                                tutor_mags=tutor_mags,
                                                acvs_mags=other_mags,
                                                add_to_filepointers=False)
        


        header_str = """@RELATION ts
@ATTRIBUTE source_id NUMERIC
@ATTRIBUTE dist NUMERIC
@ATTRIBUTE nn_rank NUMERIC
@ATTRIBUTE j_acvs_nomad NUMERIC
@ATTRIBUTE h_acvs_nomad NUMERIC
@ATTRIBUTE k_acvs_nomad NUMERIC
@ATTRIBUTE jk_acvs_nomad NUMERIC
@ATTRIBUTE v_tutor_nomad NUMERIC
@ATTRIBUTE class {'match','not'}
@data"""
        str_list.insert(0,header_str)
        testdata_dict = self.rc.parse_full_arff(arff_str='\n'.join(str_list), skip_missingval_lines=True, fill_arff_rows=True)

        if len(testdata_dict['srcid_list']) == 0:
            return None

        test_featname_longfeatval_dict = testdata_dict['featname_longfeatval_dict']
        for feat_name, feat_longlist in test_featname_longfeatval_dict.iteritems():
            test_featname_longfeatval_dict[feat_name] = self.robjects.FloatVector(feat_longlist)
        testdata_dict['features'] = self.robjects.r['data.frame'](**test_featname_longfeatval_dict)
        testdata_dict['classes'] = self.robjects.StrVector(testdata_dict['class_list'])

        self.robjects.globalenv['xte'] = testdata_dict['features']
        self.robjects.globalenv['yte'] = testdata_dict['classes']

        #pr = predict(rf_clfr, newdata=xte, proximity=TRUE, norm.votes=FALSE, type='vote', predict.all=TRUE)
        r_str  = '''
    pr = predict(rf_clfr, newdata=xte, norm.votes=FALSE, type='prob')
        '''
        classifier_out = self.robjects.r(r_str)
        #print numpy.array(self.robjects.r("pr"))

        ### I choose a nomad_source if one has a prob > 0.501, choosing the source with the max prob
        match_probs = numpy.array(self.robjects.r("pr"))[:,0]
        if len(numpy.where(match_probs >= 0.501)[0]):
            #i_chosen = match_probs.argsort()[-1] # this is the index of nomad source with the maximum 'match' prob
            ### I actually want to sort the array so that when there are duplicate probs, we choose the nomad source
            ###   which is closest in distance.
            reverse_match_probs = match_probs[::-1]
            i_chosen = (len(reverse_match_probs) -1 - reverse_match_probs.argsort())[-1]

        #import pdb; pdb.set_trace()
        #print # DEBUG ONLY
        return i_chosen




    def get_match_source_index__conservative(self, nomad_sources={},
                                             tutor_mags={},
                                             other_mags={},
                                             set_nomad_sources=None,
                                             set_tutor_mags=None,
                                             set_other_mags=None,
                                             cuts={},
                                             debug=False):
        """
### Constraints:
ASAS:
dist <= 5.0
  J - J        < 0.1
  J-K - J-K    < 0.1
  V(tut-nomad) <= 1.2  (for all other overlap filters)
dist <= 0.75
  V(tut-nomad) <= 3.0  (for all other overlap filters)
# the following match >= 2:
dist <= 30.0
  J-K - J-K    < 0.1
  J - J        < 0.1
  V(tut-nomad) <= 1.2  (for all other overlap filters)

        """
        i_chosen = None
        ### Not applicable to current ASAS sources (no tutor J, K)
        #import pdb; pdb.set_trace()
        #print
        if len(cuts) == 0:
            cuts = self.pars['nomad_assoc_cuts']['LIBERAL']

        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['1st_dist']:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    if abs(other_mags['J'] - nomad_sources['J'][i]) < cuts['1st_dJ']:
                        i_chosen = i
                        if debug and (set(['J', 'K']) <= color_intersection):
                            color_diff_other = other_mags['J'] - other_mags['K']
                            color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                            print("match: %d dist <= 5.0 & Jother-Jnomad < 0.1 : JK_color_diff_other(%f) JK_color_diff_nomad(%f)) dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        return i_chosen # Found matching source
        ### JK diff of other and Nomad is not useful, as seen in T/F overlapping histograms:
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['1st_dist']:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_other = other_mags['J'] - other_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_other - color_diff_nomad) < cuts['1st_dJK']:
                        i_chosen = i
                        if debug:
                            print("match: %d dist <= 5.0 & abs(JK_color_diff_other(%f) - JK_color_diff_nomad(%f)) < 0.1 dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        return i_chosen # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['1st_dist']:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (len(color_intersection) >= 1):
                    band_match_count = 0
                    for band in list(color_intersection):
                        if nomad_sources[band][i] is None:
                            continue
                        # KLUDGE:  originally tried <= 0.5, after looking at histogram: choose 1.0
                        if abs(tutor_mags[band] - nomad_sources[band][i]) <= cuts['1st_tut-nom']:
                            band_match_count += 1
                    if len(color_intersection) == band_match_count:
                        i_chosen = i
                        if debug:
                            print("match: %d dist <= 5.0 & abs(tutor_mags[band] - nomad_sources[band]) <= 1.2; dist=%f nomad_V=%s tutor_V=%s %s" % (i, dist, str(nomad_sources['V'][i]), str(tutor_mags['V']), str(tutor_mags)))#,  pprint.pformat([(k, nomad_sources[k][i]) for k in nomad_sources.keys()]))
                        return i_chosen # Found matching source
                        
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['2nd_dist']:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (len(color_intersection) >= 1):
                    band_match_count = 0
                    for band in list(color_intersection):
                        if nomad_sources[band][i] is None:
                            continue
                        # KLUDGE:  originally tried <= 0.5, after looking at histogram: choose 1.0
                        if abs(tutor_mags[band] - nomad_sources[band][i]) <= cuts['2nd_tut-nom']:
                            band_match_count += 1
                    if len(color_intersection) == band_match_count:
                        i_chosen = i
                        if debug:
                            print("match: %d dist <= 0.75 & abs(tutor_mags[band] - nomad_sources[band]) <= 3.0; dist=%f nomad_V=%s tutor_V=%s %s %s" % (i, dist, str(nomad_sources['V'][i]), str(tutor_mags['V']), str(tutor_mags),  pprint.pformat([(k, nomad_sources[k][i]) for k in nomad_sources.keys()])))
                        return i_chosen # Found matching source

        finalcase_i_matches = {} # {i:count}, we require >= 2 cases to match for the larger distance radius

        for i, dist in enumerate(nomad_sources['dist']):
            finalcase_i_matches[i] = 0 # initialize
            if dist <= cuts['3rd_dist']:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J', 'K']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    color_diff_other = other_mags['J'] - other_mags['K']
                    color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                    if abs(color_diff_other - color_diff_nomad) < cuts['3rd_dJK']:
                        i_chosen = i
                        if debug:
                            print("match: %d dist <= 30.0 & abs(color_diff_other(%f) - color_diff_nomad(%f)) < 0.1 dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        finalcase_i_matches[i_chosen] += 1 # Found matching source
        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['3rd_dist']:
                color_intersection = set_other_mags & set_nomad_sources # intersection
                if (set(['J']) <= color_intersection):
                    ### KLUDGE: for now we assume that the common colors are J, K
                    if abs(other_mags['J'] - nomad_sources['J'][i]) < cuts['3rd_dJ']:
                        i_chosen = i
                        if debug and (set(['J', 'K']) <= color_intersection):
                            color_diff_other = other_mags['J'] - other_mags['K']
                            color_diff_nomad = nomad_sources['J'][i] - nomad_sources['K'][i]
                            print("match: %d dist <= 30.0 & Jother-Jnomad < 0.1 : JK_color_diff_other(%f) JK_color_diff_nomad(%f)) dist=%f other_J=%f nomad_J=%f nomad_V=%s tutor_V=%s" % (i, color_diff_other, color_diff_nomad, dist, other_mags['J'], nomad_sources['J'][i], str(nomad_sources['V'][i]), str(tutor_mags['V'])))
                        finalcase_i_matches[i_chosen] += 1 # Found matching source

        for i, dist in enumerate(nomad_sources['dist']):
            if dist <= cuts['3rd_dist']:
                color_intersection = set_tutor_mags & set_nomad_sources # intersection
                if (len(color_intersection) >= 1):
                    band_match_count = 0
                    for band in list(color_intersection):
                        if nomad_sources[band][i] is None:
                            continue
                        # KLUDGE:  originally tried <= 0.5, after looking at histogram: choose 1.0
                        if abs(tutor_mags[band] - nomad_sources[band][i]) <= cuts['3rd_tut-nom']:
                            band_match_count += 1
                    if len(color_intersection) == band_match_count:
                        i_chosen = i
                        print("match: %d dist <= 30.0 & abs(tutor_mags[band] - nomad_sources[band]) <= 1.2; dist=%f nomad_V=%s tutor_V=%s %s" % (i, dist, str(nomad_sources['V'][i]), str(tutor_mags['V']), str(tutor_mags)))#,  pprint.pformat([(k, nomad_sources[k][i]) for k in nomad_sources.keys()]))
                        finalcase_i_matches[i_chosen] += 1 # Found matching source

        ### we require >= 2 cases to match for the larger distance radius, start at the closest distance:
        for i, dist in enumerate(nomad_sources['dist']):
            if finalcase_i_matches[i] >= 2:
                if debug:
                    print("        >= 2 matches, so matching source i=", i)
                return i # Found matching source
        if debug:
            print("         < 2 matches, so NO MATCH, possib dists:", nomad_sources['dist'])
        return i_chosen


    def choose_nomad_source(self, nomad_sources={}, tutor_mags={}, other_mags={},
                            conservative_cuts=False, cuts={}):
        """ Given a list of nomad retrieved sources with BVRJHK and distance information,

        Determine the most likely matching source, and return that source's info.

        # TODO: constraints:
         - if given mag dict, get color differences.


if ((abs(j_diff) <= 0.24) and (JK_diff <= 0.34)):
                            ### I chose these mag cuts due to a couple sources which have <0.25 mag differences between ACVS table and matching simbad source (225975, 227503)
         -> then use
if (JK_diff > 0.34):
         -> then skip
if dist <= 6:
                         # NOTE: the JK_diff cut doesnt seem to cut out anything in first 20% of ASAS
         -> then use
elif abs(j_diff) <= 0.24:
                         #prefix = "ok     " #"sim MAG" # These are OK associations
         -> then use
elif ((abs(j_diff) <= 3.54) and (dist <= 34.3)):
                         #prefix = "ok" #"BAD <34"
         -> then use
else: 
         -> then skip

##### Debosscher case:

                        if (dist < 70):
         -> then use
                if ((dist <= 0.33) and ('HIP' in proj_dict['source_name_list'][i])):
         -> then use


(Pdb) pprint.pprint(nomad_sources)
{'B': [11.144, None],
 'H': [1.3169999999999999, 12.348000000000001],
 'J': [2.2250000000000001, 14.382],
 'K': [0.91500000000000004, 11.766],
 'R': [10.07, None],
 'V': [10.497999999999999, None],
 'dist': [0.11, 51.659999999999997]}

??? How about if we have the ACVS JHK?
     - could have this JHK added to TUTOR dict, if no JHK exists in TUTOR dict already
     - then could use this to see if NOMAD source matches

TODO: Eventually want to store all avg mags possible, including TUTOR (no ACVS JHK) and NOMAD
     - maybe only TUTOR B V R J H K
     - although for now I think only J H K color difference features will be used

        """
        if 0:
            # DEBUG
            print('other_mags')
            pprint.pprint(other_mags)

            print('nomad_sources')
            pprint.pprint(nomad_sources)

            print('tutor_mags')
            pprint.pprint(tutor_mags)

            import pdb; pdb.set_trace()
            print()

        set_nomad_sources = set(nomad_sources.keys()) - set(('ra', 'dec', 'dist'))
        set_tutor_mags = set(tutor_mags.keys()) - set(('ra', 'dec', 'dist'))
        set_other_mags = set(other_mags.keys()) - set(('ra', 'dec', 'dist'))


        # Using new R, Active Learned RandomForest classifier:
        i_chosen = self.get_match_source_index__ActLearn_RandomForest(nomad_sources=nomad_sources,
                                               tutor_mags=tutor_mags,
                                               other_mags=other_mags,
                                               set_nomad_sources=set_nomad_sources,
                                               set_tutor_mags=set_tutor_mags,
                                               set_other_mags=set_other_mags,
                                                             cuts=cuts)

        if 0:
            #if conservative_cuts: (using hardcoded conditional classifier)
            i_chosen = self.get_match_source_index__conservative(nomad_sources=nomad_sources,
                                               tutor_mags=tutor_mags,
                                               other_mags=other_mags,
                                               set_nomad_sources=set_nomad_sources,
                                               set_tutor_mags=set_tutor_mags,
                                               set_other_mags=set_other_mags,
                                                             cuts=cuts)

        #else:
        #### VERY OLD / OBSOLETE:
        if 0:
            i_chosen = self.get_match_source_index(nomad_sources=nomad_sources,
                                               tutor_mags=tutor_mags,
                                               other_mags=other_mags,
                                               set_nomad_sources=set_nomad_sources,
                                               set_tutor_mags=set_tutor_mags,
                                               set_other_mags=set_other_mags)
            
        if i_chosen is None:
            print("No Match", end=' ')
            out_dict = {}
        else:
            out_dict = {}
            for k,vlist in nomad_sources.iteritems():
                if type(vlist) == type([]):
                    out_dict[k] = vlist[i_chosen]
                else:
                    out_dict[k] = vlist

        #print tutor_mags
        #pprint.pprint(nomad_sources)
        #pprint.pprint(out_dict)
        #import pdb; pdb.set_trace()
        #print

        return (out_dict, i_chosen)
        

    def get_tutor_avg_mags_for_srcid(self, srcid=None):
        """ Retrieve average color mags from TUTOR database for a source_id.
        """

        select_str = """select sources.source_name, filter_name, min(obsdata_val), avg(obsdata_val), max(obsdata_val), count(obsdata_val) FROM observations
join filters ON (observations.filter_id=filters.filter_id)
join obs_data ON (obs_data.observation_id=observations.observation_id)
join sources ON (sources.source_id=observations.source_id)
where observations.source_id=%d
GROUP BY filter_name""" % (srcid)

        self.tutor_cursor.execute(select_str)
        results = self.tutor_cursor.fetchall()
        if len(results) == 0:
            raise "ERROR"

        out_dict = {'tutor_mags':{},
                    'source_name':None}
        for (source_name, filt, m_min, m_avg, m_max, count) in results:

            filt_caps = filt.upper()
            out_dict['tutor_mags'][filt_caps] = m_avg # we only return the avg_mag for now. 
            out_dict['source_name'] = source_name
        return out_dict


    def get_ACVS_mags(self, source_name='', asas_ndarray=None):
        """ Using the numpy ndarray of ASAS source mags, parsed from ACVS.1.1,
        and referencing using the dotastro source_name, get the corresponding source color mags.
        """
        id_list = list(asas_ndarray['ID'])
        i_ndarray = id_list.index(source_name)

        
        try:
            acvs_mags = {'J':asas_ndarray['J'][i_ndarray],
                     'H':asas_ndarray['H'][i_ndarray],
                     'K':asas_ndarray['K'][i_ndarray]}
        except:
            acvs_mags = {}



        """
                    dtype={'names':('ID','PER','HJD0','VMAX','VAMP','TYPE','GCVS_ID','GCVS_TYPE',
                                    'IR12','IR25','IR60','IR100','J','H','K',
                                    'V_IR12','V_J','V_H','V_K','J_H','H_K'), \
                         'formats':('S13','f8','f8','f8','f8','S20','S20','S20',
                                    'f8','f8','f8','f8','f8','f8','f8',
                                    'f8','f8','f8','f8','f8','f8')})

        """

        return acvs_mags


    def query_store_nomad_sources(self, all_source_dict={}, projid_list=[], asas_ndarray=None,
                                  pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl'):
        """ Using the source_dict (source_id, ra, dec),
        This retrieves the most likely NOMAD matching source and stores associate color mags.
        """
        nomad_sources_dict = {}
        #for i in range(5464, 5470):
        for i, srcid in enumerate(all_source_dict['srcid_list']):
            srcid = all_source_dict['srcid_list'][i]
            ra = all_source_dict['ra_list'][i]
            dec = all_source_dict['dec_list'][i]

            nomad_sources = self.get_nomad_sources_for_ra_dec(ra=ra, dec=dec,
                                                              avg_epoch=None,
                                                              require_jhk=True)
            print(i, len(all_source_dict['srcid_list']), srcid)
            if len(nomad_sources['dist']) == 0:
                continue # skip this source since no NOMAD sources
            nomad_sources_dict[srcid] = nomad_sources

        fp = open(pkl_fpath, 'w')
        cPickle.dump(nomad_sources_dict, fp, 1)
        fp.close()
        #import pdb; pdb.set_trace()
        #print

        return nomad_sources_dict


    def lookup_nomad_colors_for_sources(self, all_source_dict={}, projid_list=[], asas_ndarray=None):
        """ Using the source_dict (source_id, ra, dec),
        This retrieves the most likely NOMAD matching source and stores associate color mags.
        """
        out_dict = {}
        for i, srcid in enumerate(all_source_dict['srcid_list']):
            ra = all_source_dict['ra_list'][i]
            dec = all_source_dict['dec_list'][i]

            nomad_sources = self.get_nomad_sources_for_ra_dec(ra=ra, dec=dec,
                                                              avg_epoch=None,
                                                              require_jhk=True)
            import pdb; pdb.set_trace()
            print()

            if len(nomad_sources['dist']) == 0:
                continue # skip this source since no NOMAD sources

            tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)

            
            if 126 in projid_list:
                # Only for project_id=126:
                acvs_mags = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
                cuts = self.pars['nomad_assoc_cuts']['ASAS']
            else:
                acvs_mags = {}

            print(srcid, end=' ')
            final_source_dict, i_chosen = self.choose_nomad_source(nomad_sources=nomad_sources,
                                                         tutor_mags=tutor_source_dict['tutor_mags'],
                                                         other_mags=acvs_mags,
                                                         cuts=cuts)
            out_dict[srcid] = final_source_dict



            # TODO: we want to ensure that these source JHK match the existing know ASAS ACV JHK we chose using simbad (of delta color mags)
            
        import pdb; pdb.set_trace()
        print()

        # TODO: we want to write these mags & srcid to some simple file which will be used by features
        # TODO: we want to store these mags & srcid to some MySQL table.

        return out_dict


    def get_best_nomad_lists_for_color_features(self, pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                                 projid_list=[],
                                                 asas_ndarray=None):
        """
        Determine the best parametes for the paraeter cuts to determine NOMAD/TUTOR source matches.

        instead of different aperture classes
          - have true source match, or source mismatch
          - true sources would be: close match of 2 / 3 params?
                  - wich have very tight abs(difference) matches for 2 
              - cant do 3/3 match since this will constrain the parameters to
                the small constraints
              - this will give a good idea of what the cut for each param
                should be, so I can widen the constraint
          - false sources would be 2/3 mismatch?


        ??? TODO: It will be interesting to look at these distributions seperately for:
            - ASAS
            - Debosscher HIP, OGLE

        Parameters:
            abs(V_other - V_nomad)   # trust less
            abs(J_other - J_nomad)   # trust less
            abs(V_tutor - V_nomad)   # trust more
            abs(JK_tutor - JK_nomad) # trust more
            abs(JH_tutor - JH_nomad) # trust more
            dist
        """
        fp = open(pkl_fpath,'rb')
        nomad_sources = cPickle.load(fp)
        fp.close()

        """
        srcid_list = []
        dist = []
        Jother_Jnomad = []
        Hother_Hnomad = []
        Vtutor_Vnomad = []
        JKother_JKnomad = []
        JHother_JHnomad = []
        other = { \
                'srcid_list':[],
                'dist':[],
                'Jother_Jnomad':[],
                'Hother_Hnomad':[],
                'Vtutor_Vnomad':[],
                'JKother_JKnomad':[],
                'JHother_JHnomad':[]}
        """
        out_dict = {'srcid':[],
                    'dist':[],
                    'B':[],
                    'H':[],
                    'K':[],
                    'J':[],
                    'R':[],
                    'V':[]}
        # [:100]
        for srcid in nomad_sources.keys():
            print(srcid, end=' ')
            nomad_dict = nomad_sources[srcid]
            tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)

            if 126 in projid_list:
                # Only for project_id=126:
                acvs_mags = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
                cuts = self.pars['nomad_assoc_cuts']['ASAS']
            else:
                acvs_mags = {}

            #TODO: we do the following only when we are sure that there is a NOMAD source match:
            nomad_match, i_chosen = self.choose_nomad_source(nomad_sources=nomad_dict,
                                                   tutor_mags=tutor_source_dict['tutor_mags'],
                                                   other_mags=acvs_mags,
                                                   conservative_cuts=True,
                                                   cuts=cuts)

            if len(nomad_match) == 0:
                print()
                continue # skip this source from being used in the analysis
            out_dict['srcid'].append(srcid)
            out_dict['dist'].append(nomad_match['dist'])
            out_dict['B'].append(nomad_match['B'])
            out_dict['H'].append(nomad_match['H'])
            out_dict['K'].append(nomad_match['K'])
            out_dict['J'].append(nomad_match['J'])
            out_dict['R'].append(nomad_match['R'])
            out_dict['V'].append(nomad_match['V'])
        return out_dict

        
    def get_best_nomad_lists_for_histogram_plots(self, pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                          projid_list=[],
                                          asas_ndarray=None):
        """
        (For ASAS, this was written pre-Debosscher (HIPP, OGLE))

        Determine the best parametes for the paraeter cuts to determine NOMAD/TUTOR source matches.

        instead of different aperture classes
          - have true source match, or source mismatch
          - true sources would be: close match of 2 / 3 params?
                  - wich have very tight abs(difference) matches for 2 
              - cant do 3/3 match since this will constrain the parameters to
                the small constraints
              - this will give a good idea of what the cut for each param
                should be, so I can widen the constraint
          - false sources would be 2/3 mismatch?


        ??? TODO: It will be interesting to look at these distributions seperately for:
            - ASAS
            - Debosscher HIP, OGLE

        Parameters:
            abs(V_other - V_nomad)   # trust less
            abs(J_other - J_nomad)   # trust less
            abs(V_tutor - V_nomad)   # trust more
            abs(JK_tutor - JK_nomad) # trust more
            abs(JH_tutor - JH_nomad) # trust more
            dist
        """
        fp = open(pkl_fpath,'rb')
        nomad_sources = cPickle.load(fp)
        fp.close()

        srcid_list = []
        dist = []
        Jother_Jnomad = []
        Hother_Hnomad = []
        Vtutor_Vnomad = []
        JKother_JKnomad = []
        JHother_JHnomad = []
        other = { \
                'srcid_list':[],
                'dist':[],
                'Jother_Jnomad':[],
                'Hother_Hnomad':[],
                'Vtutor_Vnomad':[],
                'JKother_JKnomad':[],
                'JHother_JHnomad':[]}

        #import pdb; pdb.set_trace()
        #print

        # [:100]
        for srcid in nomad_sources.keys():
            nomad_dict = nomad_sources[srcid]
            tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)

            if 126 in projid_list:
                # Only for project_id=126:
                acvs_mags = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
                cuts = self.pars['nomad_assoc_cuts']['ASAS']
            else:
                acvs_mags = {}


            #TODO: we do the following only when we are sure that there is a NOMAD source match:
            nomad_match, i_chosen = self.choose_nomad_source(nomad_sources=nomad_dict,
                                                   tutor_mags=tutor_source_dict['tutor_mags'],
                                                   other_mags=acvs_mags,
                                                   conservative_cuts=True,
                                                   cuts=cuts)

            if len(nomad_match) == 0:
                continue # skip this source from being used in the analysis
            #import pdb; pdb.set_trace()
            #print
            ### For histogram plotting, want to get another source which is not the target source, start from the last index:

            for i in range(len(nomad_dict['dist']) -1, -1, -1):
                d = nomad_dict['dist'][i]
                if d != nomad_match['dist']:
                    ### Then add this source to an unrelated comparison source list
                    other['dist'].append(d)
                    try:
                        other['Jother_Jnomad'].append(abs(acvs_mags['J'] - nomad_dict['J'][i]))
                    except:
                        other['Jother_Jnomad'].append(None)
                    try:
                        other['Hother_Hnomad'].append(abs(acvs_mags['H'] - nomad_dict['H'][i]))
                    except:
                        other['Hother_Hnomad'].append(None)
                    try:
                        other['Vtutor_Vnomad'].append(abs(tutor_source_dict['tutor_mags']['V'] - nomad_dict['V'][i]))
                    except:
                        other['Vtutor_Vnomad'].append(None)
                    try:
                        other['JKother_JKnomad'].append(abs((acvs_mags['J'] - acvs_mags['K']) - (nomad_dict['J'][i] - nomad_dict['K'][i]))) # no abs()?
                    except:
                        other['JKother_JKnomad'].append(None) # no abs()?
                    try:
                        other['JHother_JHnomad'].append(abs((acvs_mags['J'] - acvs_mags['H']) - (nomad_dict['J'][i] - nomad_dict['H'][i]))) # no abs()?
                    except:
                        other['JHother_JHnomad'].append(None) # no abs()?
                    break

            #other_dicts.append(other)
            srcid_list.append(srcid)
            dist.append(nomad_match['dist'])
            try:
                Jother_Jnomad.append(abs(acvs_mags['J'] - nomad_match['J']))
            except:
                Jother_Jnomad.append(None)
            try:
                Hother_Hnomad.append(abs(acvs_mags['H'] - nomad_match['H']))
            except:
                Hother_Hnomad.append(None)
            try:
                Vtutor_Vnomad.append(abs(tutor_source_dict['tutor_mags']['V'] - nomad_match['V']))
            except:
                Vtutor_Vnomad.append(None)
            try:
                JKother_JKnomad.append(abs((acvs_mags['J'] - acvs_mags['K']) - (nomad_match['J'] - nomad_match['K']))) # no abs()?
            except:
                JKother_JKnomad.append(None) # no abs()?
            try:
                JHother_JHnomad.append(abs((acvs_mags['J'] - acvs_mags['H']) - (nomad_match['J'] - nomad_match['H']))) # no abs()?
            except:
                JHother_JHnomad.append(None) # no abs()?


        out_dict = { \
            'srcid_list':srcid_list,
            'dist':dist,
            'Jother_Jnomad':Jother_Jnomad,
            'Hother_Hnomad':Hother_Hnomad,
            'Vtutor_Vnomad':Vtutor_Vnomad,
            'JKother_JKnomad':JKother_JKnomad,
            'JHother_JHnomad':JHother_JHnomad,
            'other_dicts':other}
        #pprint.pprint(out_dict['other_dicts'])
        #import pdb; pdb.set_trace()
        #print
        return out_dict


    def determine_color_param_likelyhoods(self, best_nomad_lists={}):
        """ Analyze likelyhoods using param lists.  Generate plots

        Following some of the likelyhood ratio tests of
                tutor_database_project_insert.py:plot_aperture_mag_relation()

        """
        param_name_list = best_nomad_lists.keys()
        try:
            param_name_list.remove('other_dicts') # KLUDGEY: not a parameter
        except:
            pass
        try:
            param_name_list.remove('srcid_list') # KLUDGEY: not a parameter
        except:
            pass
        if 0:
            ### ASAS:
            xlim_dict = {'Jother_Jnomad':[0.05, 5],
                         'Vtutor_Vnomad':[0.2, 4],
                         'Hother_Hnomad':[0.05, 5],
                         'JKother_JKnomad':[0.1, 2],
                         'JHother_JHnomad':[0.1, 2],
                         'dist':[0, 30]}
        if 0:
            ### OGLE:
            xlim_dict = {'Jother_Jnomad':[0.0, 0.5],
                         'Vtutor_Vnomad':[0.0, 4],
                         'Hother_Hnomad':[0.0, 0.5],
                         'JKother_JKnomad':[0.0, 0.1],
                         'JHother_JHnomad':[0.0, 0.2],
                         'dist':[0, 30]}
        if 1:
            ### HIPPARCOS:
            xlim_dict = {'Jother_Jnomad':[0.0, 5],
                         'Vtutor_Vnomad':[0.2, 4],
                         'Hother_Hnomad':[0.1, 4],
                         'JKother_JKnomad':[0.1, 5],
                         'JHother_JHnomad':[0.1, 5],
                         'dist':[0, 10]}
        if 0:
            ### DEBUG / LIBERAL:
            xlim_dict = {'Jother_Jnomad':[0.0, 5],
                         'Vtutor_Vnomad':[0.0, 5],
                         'Hother_Hnomad':[0.0, 5],
                         'JKother_JKnomad':[0.0, 5],
                         'JHother_JHnomad':[0.0, 5],
                         'dist':[0, 30]}
        for param_name in param_name_list:
            param_list = best_nomad_lists[param_name]
            ### Match source:
            vals_no_none = []
            for v in param_list:
                if v != None:
                    vals_no_none.append(v)
            mags = vals_no_none # mag[aper_inds]
            fits = norm.fit(mags)
            dist = norm(fits)
            probs = []

            for m in mags:
                probs.append(dist.pdf(m)[0]) # * len(param_list)/float(len(mag)))

            if len(xlim_dict[param_name]) == 0:
                x_range = (min(mags), max(mags))
            else:
                x_range = (xlim_dict[param_name][0], xlim_dict[param_name][1])

            pyplot.hist(mags, bins=50, normed=True, facecolor='r', alpha=0.3, range=x_range)
            #pyplot.plot(mags, probs, 'ro', ms=3)

            ### other sources unrelated to match source:
            vals_no_none = []
            for v in best_nomad_lists['other_dicts'][param_name]:
                if v != None:
                    vals_no_none.append(v)
            mags = vals_no_none # mag[aper_inds]
            fits = norm.fit(mags)
            dist = norm(fits)
            probs = []
            for m in mags:
                probs.append(dist.pdf(m)[0]) # * len(param_list)/float(len(mag)))
            pyplot.hist(mags, bins=50, normed=True, facecolor='b', alpha=0.3, range=x_range)
            #pyplot.plot(mags, probs, 'bo', ms=3)
            
            #pyplot.xlim(-1, 5)
            #pyplot.ylim(9, 14)
            title_str = '%s' % (param_name)
            pyplot.title(title_str)
            fpath = "/tmp/tutor_nomad_colors_%s.png" % (title_str.replace(' ','_'))
            pyplot.savefig(fpath)
            #os.system('eog %s &' % (fpath))
            #pyplot.show()

            print(param_name)
            pyplot.clf()

        os.system('eog /tmp/tutor_nomad*png &')

        # # # TODO: I need to have the params of mismatch sourcs, as well
        #   - maybe if the matching source is not index==1, return it as the unmatched source

        # # # TODO: tighten up the conservative constraints so there are no ambiguous sources matched and printed out.


    def recalculate_nomad_dists_using_simbad_source(self, simbad_mags_dict={}, nomad_sources={}):
        """ Here I re-evaluate the nomad distances using the source_name matched SIMBAD source.

        The re-calculated distances are updated int the nomad_sources{}.

        """
        dist_tups = []
        for i in range(len(nomad_sources['ra'])):
            nomad_sources['ra'][i]
            nomad_sources['dec'][i]
            simbad_mags_dict['ra']
            simbad_mags_dict['dec']
            #print 'old:', i, nomad_sources['dist'][i]
            nomad_sources['dist'][i] = numpy.sqrt( \
                      ((nomad_sources['ra'][i] - simbad_mags_dict['ra'])*numpy.cos(simbad_mags_dict['dec']))**2. +
                      (nomad_sources['dec'][i] - simbad_mags_dict['dec'])**2.) * 3600.
            dist_tups.append((nomad_sources['dist'][i], i))
            #print 'new:', i, nomad_sources['dist'][i]

        ### Now re-sort the nomad_sources lists by nomad_sources['dist']:
        dist_tups.sort()
        new_nomad = {'dist':[],
                     'B':[],
                     'V':[],
                     'R':[],
                     'J':[],
                     'H':[],
                     'K':[],
                     'ra':[],
                     'dec':[],
                     }
        for dist, i in dist_tups:
            #print dist, i
            new_nomad['dist'].append(nomad_sources['dist'][i])
            new_nomad['B'].append(nomad_sources['B'][i])
            new_nomad['V'].append(nomad_sources['V'][i])
            new_nomad['R'].append(nomad_sources['R'][i])
            new_nomad['J'].append(nomad_sources['J'][i])
            new_nomad['H'].append(nomad_sources['H'][i])
            new_nomad['K'].append(nomad_sources['K'][i])
            new_nomad['ra'].append(nomad_sources['ra'][i])
            new_nomad['dec'].append(nomad_sources['dec'][i])
        #import pdb; pdb.set_trace()
        #print
        return new_nomad


    def DEBOSS_determine_hip_or_ogle_sourcename(self, tutor_source_dict={}):
        """  Determine ogle or hip in source name
        """
        if ('OGLE_SMC' in tutor_source_dict['source_name']):
            query_source_name = tutor_source_dict['source_name'].replace('_',' ')

            #query_source_name = "OGLE+SMC-SC4+182752";
        elif ('OGLE' in tutor_source_dict['source_name']):
            query_source_name = tutor_source_dict['source_name'].replace('OGLE','OGLE J')
        elif ('HIP' in tutor_source_dict['source_name']):
            query_source_name = tutor_source_dict['source_name'].replace('HIP','HIP ')
        elif ('HD' in tutor_source_dict['source_name']):
            query_source_name = tutor_source_dict['source_name'].replace('HD','HD ')
        else:
            query_source_name = tutor_source_dict['source_name']
        ### For debugging that the normal OGLE* case works:
        #query_source_name = "OGLE J003716.81-731602.1"  # This does retrieve a fill votable
        #import pdb; pdb.set_trace()
        #print

        return query_source_name




        
    def analyze_nomad_tutor_source_param_relations(self, projid=None,
                                                 pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl'):
        """ Analyze likelyhoods using param lists.  Generate plots

        Following some of the likelyhood ratio tests of
                tutor_database_project_insert.py:plot_aperture_mag_relation()


        # NOTE: sort of like the older:
            best_nomad_lists = self.get_best_nomad_lists_for_histogram_plots(pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                                   projid_list=projid_list,
                                                   asas_ndarray=asas_ndarray)

            self.determine_color_param_likelyhoods(best_nomad_lists=best_nomad_lists)
        
        
        """
        all_source_dict = self.get_source_dict(projid_list=[projid])

        GetColors = Get_Colors(pars=self.pars) # This contains SIMBAD XML parsing code.

        if not os.path.exists(pkl_fpath):
            nomad_sources = self.query_store_nomad_sources(all_source_dict=all_source_dict, pkl_fpath=pkl_fpath)
        else:
            fp = open(pkl_fpath,'rb')
            nomad_sources = cPickle.load(fp)
            fp.close()

        # # # For analysis:
        srcid_list = []
        dist = []
        Jother_Jnomad = []
        Hother_Hnomad = []
        Vtutor_Vnomad = []
        JKother_JKnomad = []
        JHother_JHnomad = []
        other = { \
                'srcid_list':[],
                'dist':[],
                'Jother_Jnomad':[],
                'Hother_Hnomad':[],
                'Vtutor_Vnomad':[],
                'JKother_JKnomad':[],
                'JHother_JHnomad':[]}
        # # # ^^^^^^^^^^^^^^^^^

        for i, srcid in enumerate(nomad_sources.keys()):
            print(srcid)
            nomad_dict = nomad_sources[srcid]
            tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)
    
            if projid == 126:
                # ASAS ACVS
                mags_dict = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
                cuts = self.pars['nomad_assoc_cuts']['ASAS']
            if projid == 123:
                # Debosscher OGLE and HIPPARCOS
                ### KLUDGE: Debosscher sources are stored in TUTOR database with 'CLEAR' filter, here we rename this as 'V' filter:
                tutor_source_dict['tutor_mags']['V'] = tutor_source_dict['tutor_mags'].pop('CLEAR')
                query_source_name = self.DEBOSS_determine_hip_or_ogle_sourcename(tutor_source_dict)
                if 'OGLE' in query_source_name:
                    cuts = self.pars['nomad_assoc_cuts']['OGLE']
                    continue # skip when generating current analysis plots
                else:
                    # HIPPARCOS:
                    cuts = self.pars['nomad_assoc_cuts']['HIPPARCOS']
                
                mags_dict = GetColors.get_SIMBAD_mags_for_srcname(source_name=tutor_source_dict['source_name'],
                                                                  query_source_name=query_source_name, i=i)
                if len(mags_dict) > 0:
                    ### re-evaluate the nomad distances using the source_name matched SIMBAD source
                    nomad_dict = self.recalculate_nomad_dists_using_simbad_source(simbad_mags_dict=mags_dict,
                                                                                  nomad_sources=nomad_dict)
            else:
                mags_dict = {}

            if 0:
                # DEBUG / LIBERAL:
                cuts = self.pars['nomad_assoc_cuts']['LIBERAL']

            nomad_match, i_chosen = self.choose_nomad_source(nomad_sources=nomad_dict,
                                                   tutor_mags=tutor_source_dict['tutor_mags'],
                                                   other_mags=mags_dict,
                                                   conservative_cuts=True,
                                                   cuts=cuts)

            ############################################
            if len(nomad_match) == 0:
                continue # skip this source from being used in the analysis

            #import pdb; pdb.set_trace()
            #print
            ### For histogram plotting, want to get another source which is not the target source, start from the last index:

            for j in range(len(nomad_dict['dist']) -1, -1, -1):
                d = nomad_dict['dist'][j]
                if d != nomad_match['dist']:
                    ### Then add this source to an unrelated comparison source list
                    other['dist'].append(d)
                    try:
                        other['Jother_Jnomad'].append(abs(mags_dict['J'] - nomad_dict['J'][j]))
                    except:
                        other['Jother_Jnomad'].append(None)
                    try:
                        other['Hother_Hnomad'].append(abs(mags_dict['H'] - nomad_dict['H'][j]))
                    except:
                        other['Hother_Hnomad'].append(None)
                    try:
                        other['Vtutor_Vnomad'].append(abs(tutor_source_dict['tutor_mags']['V'] - nomad_dict['V'][j]))
                    except:
                        other['Vtutor_Vnomad'].append(None)
                    try:
                        other['JKother_JKnomad'].append(abs((mags_dict['J'] - mags_dict['K']) - (nomad_dict['J'][j] - nomad_dict['K'][i]))) # no abs()?
                    except:
                        other['JKother_JKnomad'].append(None) # no abs()?
                    try:
                        other['JHother_JHnomad'].append(abs((mags_dict['J'] - mags_dict['H']) - (nomad_dict['J'][j] - nomad_dict['H'][i]))) # no abs()?
                    except:
                        other['JHother_JHnomad'].append(None) # no abs()?
                    break

            #other_dicts.append(other)
            srcid_list.append(srcid)
            dist.append(nomad_match['dist'])
            try:
                Jother_Jnomad.append(abs(mags_dict['J'] - nomad_match['J']))
            except:
                Jother_Jnomad.append(None)
            try:
                Hother_Hnomad.append(abs(mags_dict['H'] - nomad_match['H']))
            except:
                Hother_Hnomad.append(None)
            try:
                Vtutor_Vnomad.append(abs(tutor_source_dict['tutor_mags']['V'] - nomad_match['V']))
            except:
                Vtutor_Vnomad.append(None)
            try:
                JKother_JKnomad.append(abs((mags_dict['J'] - mags_dict['K']) - (nomad_match['J'] - nomad_match['K']))) # no abs()?
            except:
                JKother_JKnomad.append(None) # no abs()?
            try:
                JHother_JHnomad.append(abs((mags_dict['J'] - mags_dict['H']) - (nomad_match['J'] - nomad_match['H']))) # no abs()?
            except:
                JHother_JHnomad.append(None) # no abs()?


        out_dict = { \
            'srcid_list':srcid_list,
            'dist':dist,
            'Jother_Jnomad':Jother_Jnomad,
            'Hother_Hnomad':Hother_Hnomad,
            'Vtutor_Vnomad':Vtutor_Vnomad,
            'JKother_JKnomad':JKother_JKnomad,
            'JHother_JHnomad':JHother_JHnomad,
            'other_dicts':other}
        #pprint.pprint(out_dict['other_dicts'])
        #import pdb; pdb.set_trace()
        #print

        #return out_dict
        self.determine_color_param_likelyhoods(best_nomad_lists=out_dict)
        import pdb; pdb.set_trace()
        print()
        # # # # NOTE: the above is just like generate_nomad_tutor_source_associations()
        
        # # # # The rest should look like get_best_nomad_lists_for_histogram_plots()
        # # # #                           determine_color_param_likelyhoods(best_nomad_lists=best_nomad_lists)


    def add_ned_extinction_for_nomad_match(self, nomad_match={}):
        """ Given the NOMAD matchign source's ra, dec, retrieve the Galactic extinction
        from the NED Coordinate & extinction calcularor.

        Example URL:
        http://ned.ipac.caltech.edu/cgi-bin/nph-calc?in_csys=Equatorial&in_equinox=J2000.0&obs_epoch=2000.0&lon=123.267567d&lat=-34.578527d&pa=0.0&out_csys=Equatorial&out_equinox=J2000.0
        
        """
        if  nomad_match['dec'] >= 0.0:
            dec_str = '+' + str(nomad_match['dec'])
        else:
            dec_str = str(nomad_match['dec'])
        url_str = "http://ned.ipac.caltech.edu/cgi-bin/nph-calc?in_csys=Equatorial&in_equinox=J2000.0&obs_epoch=2000.0&lon=%lfd&lat=%sd&pa=0.0&out_csys=Equatorial&out_equinox=J2000.0" % (nomad_match['ra'], dec_str)

        html_str = urllib.urlopen(url_str).read()

        i_begin = html_str.rfind("Landolt B")
        sub_str = html_str[i_begin:i_begin+25]
        i_begin = sub_str.find(")") + 1
        i_end = i_begin + 8
        extinct_b = float(sub_str[i_begin:i_end].strip())

        i_begin = html_str.rfind("Landolt V")
        sub_str = html_str[i_begin:i_begin+25]
        i_begin = sub_str.find(")") + 1
        i_end = i_begin + 8
        extinct_v = float(sub_str[i_begin:i_end].strip())

        extinct_bv = extinct_b - extinct_v
        nomad_match['extinct_bv'] = extinct_bv


    def add_ned_extinction_for_nomad_match__pre20121122(self, nomad_match={}):
        """ Given the NOMAD matchign source's ra, dec, retrieve the Galactic extinction
        from the NED Coordinate & extinction calcularor.

        NOTE: it seems some time prior to 20121122 the format of the ned.ipac extragalactic extinction DB changed, so now
        b-v extinction is calcuated

        Example URL:
        http://ned.ipac.caltech.edu/cgi-bin/nph-calc?in_csys=Equatorial&in_equinox=J2000.0&obs_epoch=2000.0&lon=123.267567d&lat=-34.578527d&pa=0.0&out_csys=Equatorial&out_equinox=J2000.0
        
        """
        if  nomad_match['dec'] >= 0.0:
            dec_str = '+' + str(nomad_match['dec'])
        else:
            dec_str = str(nomad_match['dec'])
        url_str = "http://ned.ipac.caltech.edu/cgi-bin/nph-calc?in_csys=Equatorial&in_equinox=J2000.0&obs_epoch=2000.0&lon=%lfd&lat=%sd&pa=0.0&out_csys=Equatorial&out_equinox=J2000.0" % (nomad_match['ra'], dec_str)

        html_str = urllib.urlopen(url_str).read()
        i_begin = html_str.find("E(B-V)") + 8
        i_end = html_str.find("mag.", i_begin, len(html_str)-1)

        extinct_bv = float(html_str[i_begin:i_end].strip())
        nomad_match['extinct_bv'] = extinct_bv


    def nomad_sources_for_classifier__addheader(self):


        header = """@ATTRIBUTE dist NUMERIC
@ATTRIBUTE nn_rank NUMERIC
@ATTRIBUTE j_acvs_nomad NUMERIC
@ATTRIBUTE h_acvs_nomad NUMERIC
@ATTRIBUTE k_acvs_nomad NUMERIC
@ATTRIBUTE jk_acvs_nomad NUMERIC
@ATTRIBUTE v_tutor_nomad NUMERIC
"""
        self.fp_test_withsrcid.write("@RELATION ts\n@ATTRIBUTE source_id NUMERIC\n" + header + "@ATTRIBUTE class {'match','not'}\n@data\n")
        self.fp_train_withsrcid.write("@RELATION ts\n@ATTRIBUTE source_id NUMERIC\n" + header + "@ATTRIBUTE class {'match','not'}\n@data\n")
        self.fp_test_no_srcid.write("@RELATION ts\n" + header + "@ATTRIBUTE class {'match','not'}\n@data\n")
        self.fp_train_no_srcid.write("@RELATION ts\n" + header + "@ATTRIBUTE class {'match','not'}\n@data\n")



    def store_nomad_sources_for_classifier(self, srcid=None,
                                           i_chosen=None,
                                           nomad_dict={},
                                           tutor_mags={},
                                           acvs_mags={},
                                           add_to_filepointers=True):
        """ Store all information about source so that it can be used
        to train a single NOMAD association classifier.

        - This function was written 2012-03-12 in order to explore how
          much more effective a single RandomForest classifier would be
          for determining NOMAD source associations.
        """
        out_list = []

        # TODO: write to a file for classification
        #   - want to write missing attribute values
        if 0:
            print('acvs_mags (SIMBAD BVRJHK which is found in ACVS catalog)')
            pprint.pprint(acvs_mags)

            print('nomad_dict')
            pprint.pprint(nomad_dict)

            print('tutor_mags')
            pprint.pprint(tutor_mags)

            print('srcid', srcid)
        print('i_chosen', i_chosen)

        for i in range(len(nomad_dict['J'])):

            if i_chosen is None:
                class_str = "?"
            elif i == i_chosen:
                class_str = "'match'"
            else:
                class_str = "'not'"
                

            dist = nomad_dict['dist'][i]

            try:
                j_acvs_nomad = str(acvs_mags['J'] - nomad_dict['J'][i])
            except:
                j_acvs_nomad = '?'

            try:
                h_acvs_nomad = str(acvs_mags['H'] - nomad_dict['H'][i])
            except:
                h_acvs_nomad = '?'

            try:
                k_acvs_nomad = str(acvs_mags['K'] - nomad_dict['K'][i])
            except:
                k_acvs_nomad = '?'

            ##### We don't parse V from ACVS file since the ACVS V seems to behave oddly, and assuming it is taken from ACVS lightcurve average or median:
            #try:
            #    v_acvs_nomad = str(acvs_mags['V'] - nomad_dict['V'][i])
            #except:
            #    v_acvs_nomad = '?'


            try:
                jk_acvs_nomad = str((acvs_mags['J'] - acvs_mags['K']) - (nomad_dict['J'][i] - nomad_dict['K'][i]))
            except:
                jk_acvs_nomad = '?'



            ##### We don't parse V from ACVS file since the ACVS V seems to behave oddly, and assuming it is taken from ACVS lightcurve average or median:
            #try:
            #    vj_acvs_nomad = str((acvs_mags['V'] - acvs_mags['J']) - (nomad_dict['V'][i] - nomad_dict['J'][i]))
            #except:
            #    vj_acvs_nomad = '?'


            try:
                v_tutor_nomad = str(tutor_mags['V'] - nomad_dict['V'][i])
            except:
                v_tutor_nomad = '?'


            root_str = "%f,%d,%s,%s,%s,%s,%s" % ( \
                dist,
                i,
                j_acvs_nomad,
                h_acvs_nomad,
                k_acvs_nomad,
                jk_acvs_nomad,
                v_tutor_nomad)
            #print root_str
            try:
                out_list.append("%d,%s,%s\n" % (srcid, root_str, class_str))
            except:
                out_list.append("%s,%s,%s\n" % (srcid, root_str, class_str))
                

            if add_to_filepointers:
                if class_str == "?":
                    try:
                        self.fp_test_withsrcid.write("%d,%s,%s\n" % (srcid, root_str, class_str))
                    except:
                        self.fp_test_withsrcid.write("%s,%s,%s\n" % (srcid, root_str, class_str))                        
                    self.fp_test_no_srcid.write("%s,%s\n" % (root_str, class_str))
                else:
                    try:
                        self.fp_train_withsrcid.write("%d,%s,%s\n" % (srcid, root_str, class_str))
                    except:
                        self.fp_train_withsrcid.write("%s,%s,%s\n" % (srcid, root_str, class_str))
                    self.fp_train_no_srcid.write("%s,%s\n" % (root_str, class_str))

        return out_list
        #import pdb; pdb.set_trace()
        #print


        



    def generate_nomad_tutor_source_associations(self, projid=None,
                                                 pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                                 do_store_nomad_sources_for_classifier=True,
                                                 add_extinction=False,
                                                 asas_ndarray=None):
        """ A more general for of Get_Colors_Using_Nomad.main() (which was ASAS specific).

        This version should allow any TUTOR project_id to have NOMAD source associations.
        
        """
        all_source_dict = self.get_source_dict(projid_list=[projid])

        if not os.path.exists(pkl_fpath):
            nomad_sources = self.query_store_nomad_sources(all_source_dict=all_source_dict, pkl_fpath=pkl_fpath)
        else:
            fp = open(pkl_fpath,'rb')
            nomad_sources = cPickle.load(fp)
            fp.close()

        out_dict = {'srcid':[],
                    'dist':[],
                    'B':[],
                    'H':[],
                    'K':[],
                    'J':[],
                    'R':[],
                    'V':[],
                    'extinct_bv':[]}
        GetColors = Get_Colors(pars=self.pars) # This contains SIMBAD XML parsing code.

        if do_store_nomad_sources_for_classifier:
            self.fp_train_withsrcid = open(self.pars['fpath_train_withsrcid'], 'w')
            self.fp_train_no_srcid = open(self.pars['fpath_train_no_srcid'], 'w')
            self.fp_test_withsrcid = open(self.pars['fpath_test_withsrcid'], 'w')
            self.fp_test_no_srcid = open(self.pars['fpath_test_no_srcid'], 'w')
            self.nomad_sources_for_classifier__addheader()

        # [:100]
        for srcid in nomad_sources.keys():
            print(srcid, end=' ')
            nomad_dict = nomad_sources[srcid]
            tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)

            if projid == 126:
                # ASAS ACVS
                mags_dict = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
                cuts = self.pars['nomad_assoc_cuts']['ASAS']
            elif projid == 123:
                # Debosscher OGLE and HIPPARCOS
                ### Code below is taken from analyze_nomad_tutor_source_param_relations():
                tutor_source_dict['tutor_mags']['V'] = tutor_source_dict['tutor_mags'].pop('CLEAR')
                query_source_name = self.DEBOSS_determine_hip_or_ogle_sourcename(tutor_source_dict)
                if 'OGLE' in query_source_name:
                    cuts = self.pars['nomad_assoc_cuts']['OGLE']
                else:
                    # HIPPARCOS:
                    cuts = self.pars['nomad_assoc_cuts']['HIPPARCOS']
                ### Returns SIMBAD mags for a source which has matching source_name:
                mags_dict = GetColors.get_SIMBAD_mags_for_srcname(source_name=tutor_source_dict['source_name'],
                                                                  query_source_name=query_source_name)
                if len(mags_dict) > 0:
                    ### re-evaluate the nomad distances using the source_name matched SIMBAD source
                    nomad_dict = self.recalculate_nomad_dists_using_simbad_source(simbad_mags_dict=mags_dict,
                                                                                  nomad_sources=nomad_dict)
            else:
                mags_dict = {}

            #TODO: we do the following only when we are sure that there is a NOMAD source match:
            nomad_match, i_chosen = self.choose_nomad_source(nomad_sources=nomad_dict,
                                                   tutor_mags=tutor_source_dict['tutor_mags'],
                                                   other_mags=mags_dict,
                                                   conservative_cuts=True,
                                                   cuts=cuts)
            print("SIMBAD: B:%2.3f V:%2.3f R:%2.3f J:%2.3f H:%2.3f K:%2.3f" % (mags_dict.get('B',0),
                                                                                         mags_dict.get('V',0),
                                                                                         mags_dict.get('R',0),
                                                                                         mags_dict.get('J',0),
                                                                                         mags_dict.get('H',0),
                                                                                         mags_dict.get('K',0)))
            try:
                print("       NOMAD:  B:%2.3f V:%2.3f R:%2.3f J:%2.3f H:%2.3f K:%2.3f dist:%2.3f" % (nomad_match.get('B',0),
                                                                                        nomad_match.get('V',0),
                                                                                        nomad_match.get('R',0),
                                                                                        nomad_match.get('J',0),
                                                                                        nomad_match.get('H',0),
                                                                                        nomad_match.get('K',0),
                                                                                        nomad_match.get('dist',0)))
            except:
                print("  !    NOMAD:  B:%6s V:%2.3s R:%6s J:%6s H:%2.3f K:%2.3f dist:%2.3f" % (str(nomad_match.get('B',0)),
                                                                                        str(nomad_match.get('V',0)),
                                                                                        str(nomad_match.get('R',0)),
                                                                                        nomad_match.get('J',0),
                                                                                        nomad_match.get('H',0),
                                                                                        nomad_match.get('K',0),
                                                                                        nomad_match.get('dist',0)))

            if do_store_nomad_sources_for_classifier:
                self.store_nomad_sources_for_classifier(srcid=srcid,
                                                        i_chosen=i_chosen,
                                                        nomad_dict=nomad_dict,
                                                        tutor_mags=tutor_source_dict['tutor_mags'],
                                                        acvs_mags=mags_dict,
                                                        )
                

            if len(nomad_match) == 0:
                print()
                continue # skip this source from being used in the analysis

            # # # # #
            # # # # #
            # # # # #
            # # # # #
            if (not do_store_nomad_sources_for_classifier) or add_extinction:
                #   NOTE: this just takes additional time for do_store_nomad_sources_for_classifier case
                ##### Need to add NED extinction info to nomad_match{}
                self.add_ned_extinction_for_nomad_match(nomad_match=nomad_match)
                out_dict['extinct_bv'].append(nomad_match['extinct_bv'])


            out_dict['srcid'].append(srcid)
            out_dict['dist'].append(nomad_match['dist'])
            out_dict['B'].append(nomad_match['B'])
            out_dict['H'].append(nomad_match['H'])
            out_dict['K'].append(nomad_match['K'])
            out_dict['J'].append(nomad_match['J'])
            out_dict['R'].append(nomad_match['R'])
            out_dict['V'].append(nomad_match['V'])

        if do_store_nomad_sources_for_classifier:
            self.fp_train_withsrcid.close()
            self.fp_train_no_srcid.close()
            self.fp_test_withsrcid.close()
            self.fp_test_no_srcid.close()
            import pdb; pdb.set_trace()
            print()

        return out_dict



    def generate_nomad_source_associations_without_tutor(self,
                                                         nomad_sources={},
                                                         asas_data_dict={},
                                                         projid=None,
                                                 pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                                 do_store_nomad_sources_for_classifier=True,
                                                 add_extinction=True,
                                                 asas_ndarray=None):
        """ Adapted from generate_nomad_tutor_source_associations()

        This should not require TUTOR information

        A more general for of Get_Colors_Using_Nomad.main() (which was ASAS specific).

        
        """
        #all_source_dict = self.get_source_dict(projid_list=[projid])
        #if not os.path.exists(pkl_fpath):
        #    nomad_sources = self.query_store_nomad_sources(all_source_dict=all_source_dict, pkl_fpath=pkl_fpath)
        #else:
        #    fp = open(pkl_fpath,'rb')
        #    nomad_sources = cPickle.load(fp)
        #    fp.close()

        out_dict = {'srcid':[],
                    'dist':[],
                    'B':[],
                    'H':[],
                    'K':[],
                    'J':[],
                    'R':[],
                    'V':[],
                    'extinct_bv':[]}
        GetColors = Get_Colors(pars=self.pars) # This contains SIMBAD XML parsing code.

        if do_store_nomad_sources_for_classifier:
            self.fp_train_withsrcid = open(self.pars['fpath_train_withsrcid'], 'w')
            self.fp_train_no_srcid = open(self.pars['fpath_train_no_srcid'], 'w')
            self.fp_test_withsrcid = open(self.pars['fpath_test_withsrcid'], 'w')
            self.fp_test_no_srcid = open(self.pars['fpath_test_no_srcid'], 'w')
            self.nomad_sources_for_classifier__addheader()

        # [:100]
        for srcid in nomad_sources.keys():
            #if ((srcid == '191956+4052.6') or (srcid == '191955+4052.6')):
            #    import pdb; pdb.set_trace()
            #    print

            print(srcid, end=' ')
            nomad_dict = nomad_sources[srcid]
            #tutor_source_dict = self.get_tutor_avg_mags_for_srcid(srcid=srcid)
            try:
                ind = asas_data_dict['asasid_to_index'][srcid]
            except:
                continue
            tutor_mags = {'V':asas_data_dict['data_dict']['V'][ind]}
            mags_dict = {'J':asas_data_dict['data_dict']['J'][ind],
                         'H':asas_data_dict['data_dict']['J'][ind] - asas_data_dict['data_dict']['J-H'][ind],
                         'K':asas_data_dict['data_dict']['J'][ind] - asas_data_dict['data_dict']['J-H'][ind] - asas_data_dict['data_dict']['H-K'][ind],
                } # acvs_mags, etc (see get_colors_for_tutor_sourcs.py: L2509 or L2775

            #if projid == 126:
            #    # ASAS ACVS
            #    mags_dict = self.get_ACVS_mags(source_name=tutor_source_dict['source_name'], asas_ndarray=asas_ndarray)
            #    cuts = self.pars['nomad_assoc_cuts']['ASAS']
            #elif projid == 123:
            #    # Debosscher OGLE and HIPPARCOS
            #    ### Code below is taken from analyze_nomad_tutor_source_param_relations():
            #    tutor_source_dict['tutor_mags']['V'] = tutor_source_dict['tutor_mags'].pop('CLEAR')
            #    query_source_name = self.DEBOSS_determine_hip_or_ogle_sourcename(tutor_source_dict)
            #    if 'OGLE' in query_source_name:
            #        cuts = self.pars['nomad_assoc_cuts']['OGLE']
            #    else:
            #        # HIPPARCOS:
            #        cuts = self.pars['nomad_assoc_cuts']['HIPPARCOS']
            #    ### Returns SIMBAD mags for a source which has matching source_name:
            #    mags_dict = GetColors.get_SIMBAD_mags_for_srcname(source_name=tutor_source_dict['source_name'],
            #                                                      query_source_name=query_source_name)
            #    if len(mags_dict) > 0:
            #        ### re-evaluate the nomad distances using the source_name matched SIMBAD source
            #        nomad_dict = self.recalculate_nomad_dists_using_simbad_source(simbad_mags_dict=mags_dict,
            #                                                                      nomad_sources=nomad_dict)
            #else:
            #    mags_dict = {}

            #TODO: we do the following only when we are sure that there is a NOMAD source match:
            nomad_match, i_chosen = self.choose_nomad_source(nomad_sources=nomad_dict,
                                                   tutor_mags=tutor_mags, #tutor_source_dict['tutor_mags'],
                                                   other_mags=mags_dict,
                                                   conservative_cuts=True,
                                                   cuts={})
            print("SIMBAD: B:%2.3f V:%2.3f R:%2.3f J:%2.3f H:%2.3f K:%2.3f" % (mags_dict.get('B',0),
                                                                                         mags_dict.get('V',0),
                                                                                         mags_dict.get('R',0),
                                                                                         mags_dict.get('J',0),
                                                                                         mags_dict.get('H',0),
                                                                                         mags_dict.get('K',0)))
            try:
                print("       NOMAD:  B:%2.3f V:%2.3f R:%2.3f J:%2.3f H:%2.3f K:%2.3f dist:%2.3f" % (nomad_match.get('B',0),
                                                                                        nomad_match.get('V',0),
                                                                                        nomad_match.get('R',0),
                                                                                        nomad_match.get('J',0),
                                                                                        nomad_match.get('H',0),
                                                                                        nomad_match.get('K',0),
                                                                                        nomad_match.get('dist',0)))
            except:
                print("  !    NOMAD:  B:%6s V:%2.3s R:%6s J:%6s H:%2.3f K:%2.3f dist:%2.3f" % (str(nomad_match.get('B',0)),
                                                                                        str(nomad_match.get('V',0)),
                                                                                        str(nomad_match.get('R',0)),
                                                                                        nomad_match.get('J',0),
                                                                                        nomad_match.get('H',0),
                                                                                        nomad_match.get('K',0),
                                                                                        nomad_match.get('dist',0)))

            if do_store_nomad_sources_for_classifier:
                self.store_nomad_sources_for_classifier(srcid=srcid,
                                                        i_chosen=i_chosen,
                                                        nomad_dict=nomad_dict,
                                                        tutor_mags=tutor_mags, #tutor_source_dict['tutor_mags'],
                                                        acvs_mags=mags_dict,
                                                        )
                

            if len(nomad_match) == 0:
                print()
                continue # skip this source from being used in the analysis

            # # # # #
            # # # # #
            # # # # #
            # # # # #
            if (not do_store_nomad_sources_for_classifier) or add_extinction:
                #   NOTE: this just takes additional time for do_store_nomad_sources_for_classifier case
                ##### Need to add NED extinction info to nomad_match{}
                self.add_ned_extinction_for_nomad_match(nomad_match=nomad_match)
                out_dict['extinct_bv'].append(nomad_match['extinct_bv'])


            out_dict['srcid'].append(srcid)
            out_dict['dist'].append(nomad_match['dist'])
            out_dict['B'].append(nomad_match['B'])
            out_dict['H'].append(nomad_match['H'])
            out_dict['K'].append(nomad_match['K'])
            out_dict['J'].append(nomad_match['J'])
            out_dict['R'].append(nomad_match['R'])
            out_dict['V'].append(nomad_match['V'])

        if do_store_nomad_sources_for_classifier:
            self.fp_train_withsrcid.close()
            self.fp_train_no_srcid.close()
            self.fp_test_withsrcid.close()
            self.fp_test_no_srcid.close()

        return out_dict


    def update_bestnomad_list_file(self, best_nomad_lists={}, projid=0):
        """ update the lsit file which is used for retrieving NOMAD color features
        for a TUTOR source_id.
        """
        # TODO: open the existing .pkl file and add to it
        # TODO: open the existing list file and add to it

        if os.path.exists(self.pars['best_nomad_src_list_fpath']):
            data = loadtxt(self.pars['best_nomad_src_list_fpath'],
                                           dtype={'names': ('src_id', 'B', 'V', 'R', 'J', 'H', 'K'),
                                                  'formats': ('i4', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')})
            existing_srcids = data['src_id']
            fp = open(self.pars['best_nomad_src_list_fpath'], 'a')
        else:
            existing_srcids = []
            fp = open(self.pars['best_nomad_src_list_fpath'], 'w')
            

        #fp = open(self.pars['best_nomad_src_list_fpath'], 'w')
        pkl_source_dict = {}
        for i in range(len(best_nomad_lists['srcid'])):
            srcid = best_nomad_lists['srcid'][i]
            #if srcid in existing_srcids:
            #    continue # TODO: maybe update if the NOMAD color algorithms change
            B = str(best_nomad_lists['B'][i]) if (best_nomad_lists['B'][i] != None) else str(-99)
            V = str(best_nomad_lists['V'][i]) if (best_nomad_lists['V'][i] != None) else str(-99)
            R = str(best_nomad_lists['R'][i]) if (best_nomad_lists['R'][i] != None) else str(-99)
            J = str(best_nomad_lists['J'][i]) if (best_nomad_lists['J'][i] != None) else str(-99)
            H = str(best_nomad_lists['H'][i]) if (best_nomad_lists['H'][i] != None) else str(-99)
            K = str(best_nomad_lists['K'][i]) if (best_nomad_lists['K'][i] != None) else str(-99)
            #import pdb; pdb.set_trace()
            #print
            extinct_bv = str(best_nomad_lists['extinct_bv'][i]) if (best_nomad_lists['extinct_bv'][i] != None) else str(-99)

            if type(srcid) == str:
                src_str = "%s" % (srcid)
            else:
                src_str = "%d" % (srcid)
            fp.write("%s %s %s %s %s %s %s %s\n" % ( \
                src_str,
                B,
                V,
                R,
                J,
                H,
                K,
                extinct_bv))
                #str(best_nomad_lists['dist'][i]),

            pkl_source_dict[best_nomad_lists['srcid'][i]] = {'B':B,
                                                             'V':V,
                                                             'R':R,
                                                             'J':J,
                                                             'H':H,
                                                             'K':K,
                                                             'dist':best_nomad_lists['dist'][i],
                                                             'extinct_bv':''}#best_nomad_lists['extinct_bv'][i]}


            
        fp.close()

        fp_pkl = open(self.pars['best_nomad_src_pickle_fpath'] + str(projid), 'w')
        cPickle.dump(pkl_source_dict, fp_pkl, 1)
        fp_pkl.close()




    # More Obsolete: (ASAS project only):
    def main(self, projid_list=[], asas_ndarray=None):
        """
        """
        all_source_dict = self.get_source_dict(projid_list=projid_list)

        if 0:
            ### Only do this *once* to generate a Pickle file:
            self.query_store_nomad_sources(all_source_dict=all_source_dict, projid_list=projid_list,
                                             asas_ndarray=asas_ndarray)
            import pdb; pdb.set_trace()
            print()


        if 1:
            ### For generating a nomad best match color list which will be used as color features.
            best_nomad_lists = self.get_best_nomad_lists_for_color_features( \
                                          pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                          projid_list=projid_list,
                                          asas_ndarray=asas_ndarray)
            fp = open(self.pars['best_nomad_src_list_fpath'], 'w')
            pkl_source_dict = {}
            for i in range(len(best_nomad_lists['srcid'])):

                B = str(best_nomad_lists['B'][i]) if (best_nomad_lists['B'][i] != None) else str(-99)
                V = str(best_nomad_lists['V'][i]) if (best_nomad_lists['V'][i] != None) else str(-99)
                R = str(best_nomad_lists['R'][i]) if (best_nomad_lists['R'][i] != None) else str(-99)
                J = str(best_nomad_lists['J'][i]) if (best_nomad_lists['J'][i] != None) else str(-99)
                H = str(best_nomad_lists['H'][i]) if (best_nomad_lists['H'][i] != None) else str(-99)
                K = str(best_nomad_lists['K'][i]) if (best_nomad_lists['K'][i] != None) else str(-99)

                fp.write("%d %s %s %s %s %s %s\n" % ( \
                    best_nomad_lists['srcid'][i],
                    B,
                    V,
                    R,
                    J,
                    H,
                    K))
                    #str(best_nomad_lists['dist'][i]),

                pkl_source_dict[best_nomad_lists['srcid'][i]] = {'B':B,
                                                                 'V':V,
                                                                 'R':R,
                                                                 'J':J,
                                                                 'H':H,
                                                                 'K':K,
                                                                 'dist':best_nomad_lists['dist'][i]}


                
            fp.close()

            fp_pkl = open(self.pars['best_nomad_src_pickle_fpath'], 'w')
            cPickle.dump(pkl_source_dict, fp_pkl, 1)
            fp_pkl.close()

            import pdb; pdb.set_trace()
            print()

        if 0:
            ### For analysis of liklihood of various color parameters (for ASAS):
            ###  - This generates png histograms of liklihoods of color, dist param values for matches and mismatch sources

            #pkl_fpath_100src='/home/pteluser/scratch/get_colors_for_tutor_sources_temp.pkl',
                        
            best_nomad_lists = self.get_best_nomad_lists_for_histogram_plots(pkl_fpath='/home/pteluser/scratch/get_colors_for_tutor_sources.pkl',
                                                   projid_list=projid_list,
                                                   asas_ndarray=asas_ndarray)

            self.determine_color_param_likelyhoods(best_nomad_lists=best_nomad_lists)
            

        # OBSOLETE ???:
        self.lookup_nomad_colors_for_sources(all_source_dict=all_source_dict, projid_list=projid_list,
                                             asas_ndarray=asas_ndarray)

        # TODO: need to query NOMAD for each source & parse the results


        # FOR TESTING ONLY: get the xml filepaths for each srcid
        #  - dont need to do since we are just filling a file with this info, which will later be used
        

        import pdb; pdb.set_trace()
        print()


class Parse_Nomad_Colors_List:
    """ Using a list of (tutor_srcid, jhkbvr_colors)
    which was retrieved from nomad for each source using
    get_colors_for_tutor_sources.py: Get_Colors_Using_Nomad.main()

    NOTE: the columns contained in the source_color_list file are defined in:
          get_colors_for_tutor_sources.py: Get_Colors_Using_Nomad.main()
    """
    def __init__(self, fpath=""):
        self.load_data_list(fpath=fpath)


    def load_data_list(self, fpath=""):
        """ Load the sourceid_color list into memory for repeated use.
        """
        #if len(fpath) == 0:
        #    fpath = self.pars['nomad_color_list_fpath']

        try:
            self.data = loadtxt(fpath, dtype={'names': ('srcid', 'B', 'V', 'R', 'J', 'H', 'K', 'extinct_bv'),
                                              'formats': ('i4',  'f4','f4','f4','f4','f4','f4', 'f4')})
        except:
            # Case when srcid is an ASAS source name with quotes:   '195853+4054.2'
            self.data = loadtxt(fpath, dtype={'names': ('srcid', 'B', 'V', 'R', 'J', 'H', 'K', 'extinct_bv'),
                                              'formats': ('S15',  'f4','f4','f4','f4','f4','f4', 'f4')})
            
        self.srcid_list = list(self.data['srcid'])


    def get_colors_for_srcid(self, xml_str='', srcid=None):
        """ Given an XML string and a TUTOR/Dotastro source_id
         - This parses list/file for corresponding source-matched JHKBVR colors,
           if they exist for this source.
        """

        try:
            i = self.srcid_list.index(srcid)
        except:
            return xml_str

        table_xml_index = xml_str.index("<TABLE ")

        xml_str_list = [xml_str[:table_xml_index]]

        #import pdb; pdb.set_trace()
        #print

        for band in ['B', 'V', 'R', 'J', 'H', 'K', 'extinct_bv']:

            mag_val = self.data[band][i]
            ### 20110620: It seems some db_importer.py xml parsing code has problems with None being in the data-epochs table in the vosource (without encapsulating '"'), so I will keep using the -99 value to represent no/missing value (and comment out the condition below):
            #if mag_val == -99:
            #    mag_str = 'None'
            #else:
            mag_str = str(mag_val)
            if band == 'extinct_bv':
                band_str = band
            else:
                band_str = "%s:NOMAD" % (band)

            xml_str_list.append("""      <TABLE name="%s">
        <FIELD name="t" ID="col1" system="TIMESYS" datatype="float" unit="day"/>
        <FIELD name="m" ID="col2" ucd="phot.mag;em.opt.%s" datatype="float" unit="mag"/>
        <FIELD name="m_err" ID="col3" ucd="stat.error;phot.mag;em.opt.%s" datatype="float" unit="mag"/>
        <DATA>
          <TABLEDATA>
            <TR row="1"><TD>0.0</TD><TD>%s</TD><TD>0.0000</TD></TR>
            </TABLEDATA>
          </DATA>
        </TABLE>
""" % (band_str, band_str, band_str, mag_str))

        xml_str_list.append(xml_str[table_xml_index:])
        return ''.join(xml_str_list)



if __name__ == '__main__':

    pars = { \
    'tutor_hostname':'192.168.1.103', #'lyra.berkeley.edu',
    'tutor_username':'dstarr', #'tutor', # guest
    'tutor_password':'ilove2mass', #'iamaguest',
    'tutor_database':'tutor',
    'tutor_port':3306,
    'tcp_hostname':'192.168.1.25',
    'tcp_username':'pteluser',
    'tcp_port':     3306, 
    'tcp_database':'source_test_db',
    'best_nomad_src_list_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/best_nomad_src_list'),
    'best_nomad_src_pickle_fpath':os.path.abspath(os.environ.get("TCP_DIR") + '/Data/best_nomad_src.pkl'),
    'filtmag_dirpath':'/home/pteluser/src/classify/filtmag_data',
    'peramp_fpath':'/home/pteluser/src/classify/per_amp_debosscher.dat',
    'votable_cache_dirpath':'/home/dstarr/scratch/simbad_votables',
    'votable_srcname_cache_dirpath':'/home/dstarr/scratch/simbad_srcname_votables',
    'html_prefix_list':["http://simbad.u-strasbg.fr/simbad/sim-coo?",
                        "http://simbad.harvard.edu/simbad/sim-coo?"],
    'html_srcname_prefix_list':["http://simbad.u-strasbg.fr/simbad/sim-id?",
                                "http://simbad.harvard.edu/simbad/sim-id?"],
    'votable_attrib_names': [
        "GEN:U_B",  # color index U-B
        "GEN:V_B",  # color index V-B
        "GEN:B1_B", # color index B1-B
        "GEN:B2_B", # color index B2-B
        "GEN:V1_B", # color index V1-B
        "GEN:G_B",  # color index G-B
        "UBV:B_V",  # B-V color index
        "UBV:U_B",  # U-B color index
        "uvby:b_y", # b-y color index
        "uvby:m1",  # m1 index (Balmer discontinuity)
        "uvby:c1",  # c1 index (line blocking)
        "U",        # Magnitude U
        "B",        # Magnitude B
        "V",        # Magnitude V
        "R",        # Magnitude R
        "I",        # Magnitude I
        "J",        # Magnitude J
        "H",        # Magnitude H
        "K",        # Magnitude K
        "u",        # Magnitude u  sdss
        "g",        # Magnitude g  sdss
        "r",        # Magnitude r  sdss
        "i",        # Magnitude i  sdss
        "z",        # Magnitude z  sdss
        ],
    'nomad_assoc_cuts':{'LIBERAL':{'1st_dist':   30,
                                   '1st_dJ':     3.0,
                                   '1st_dJK':    3.0,
                                   '1st_tut-nom':3.0,
                                   '2nd_dist':   -1,
                                   '2nd_tut-nom':0.1,
                                   '3rd_dist':   -1,
                                   '3rd_dJ':     0.1,
                                   '3rd_dJK':    0.1,
                                   '3rd_tut-nom':0.1},
                        'HIPPARCOS':{'1st_dist':   1.0,
                                     '1st_dJ':     0.1,
                                     '1st_dJK':    0.3,
                                     '1st_tut-nom':0.3,
                                     '2nd_dist':   0.1,
                                     '2nd_tut-nom':1.6,
                                     '3rd_dist':   4.25, #2.0,
                                     '3rd_dJ':     0.1,
                                     '3rd_dJK':    0.3,
                                     '3rd_tut-nom':1.6},
                        'OGLE':{'1st_dist':   -1, #25,
                                '1st_dJ':     0.1,
                                '1st_dJK':    0.02,
                                '1st_tut-nom':-1,
                                '2nd_dist':   0.2, # only couple OGLE pass this cut and their tut-nom <1.45 when <3 tried
                                '2nd_tut-nom':1.45,
                                '3rd_dist':   3,   # < 13 has a large peak around 12, which is probably unrelated sources with similar J
                                '3rd_dJ':     0.02,
                                '3rd_dJK':    0.02,
                                '3rd_tut-nom':1.45},#0.75}
                        'ASAS':{'1st_dist':   5.0, # -1 dist disables a group of cuts
                                '1st_dJ':     0.1,
                                '1st_dJK':    0.1,
                                '1st_tut-nom':1.2,
                                '2nd_dist':   0.75,
                                '2nd_tut-nom':3.0,
                                '3rd_dist':  30.0,
                                '3rd_dJ':     0.1,
                                '3rd_dJK':    0.1,
                                '3rd_tut-nom':1.2},
                        },
        'fpath_train_withsrcid':os.path.expandvars("$HOME/scratch/nomad_asas_acvs_classifier/ALclassified_arff/train_withsrcid.arff"),
        'fpath_train_no_srcid':os.path.expandvars("$HOME/scratch/nomad_asas_acvs_classifier/ALclassified_arff/train_no_srcid.arff"),
        'fpath_test_withsrcid':os.path.expandvars("$HOME/scratch/nomad_asas_acvs_classifier/ALclassified_arff/test_withsrcid.arff"),
        'fpath_test_no_srcid':os.path.expandvars("$HOME/scratch/nomad_asas_acvs_classifier/ALclassified_arff/test_no_srcid.arff"),
    }

    from .tutor_database_project_insert import ASAS_Data_Tools

    ASASDataTools = ASAS_Data_Tools(pars={'source_data_fpath':os.path.abspath(os.environ.get("TCP_DIR") + \
                                        'Data/allstars/ACVS.1.1')})
    asas_ndarray = ASASDataTools.retrieve_parse_asas_acvs_source_data()

    GetColorsUsingNomad = Get_Colors_Using_Nomad(pars=pars)

    if 1:
        ### For plotting an existing  best_nomad_src.pkl file:
        pkl_fpath = '/home/dstarr/src/TCP/Data/best_nomad_src.pkl126' # contains final classified srcs
        color_arff_fpath = '/home/dstarr/scratch/nomad_asas_acvs_classifier/notchosen_withclass_withsrcid.arff'
        import cPickle
        fp = open(pkl_fpath)
        best_nomad_src = cPickle.load(fp)

        #print best_nomad_src[262144]
        #{'B': '12.722', 'dist': 1.85, 'H': '6.146', 'K': '5.816', 'J': '7.041', 'extinct_bv': '', 'R': '10.31', 'V': '11.189'}

        from . import nomad_colors_assoc_activelearn
        ### This is for applying a trained RandomForest Active Learned classifier:
        algorithms_dirpath = os.path.abspath(os.environ.get("TCP_DIR") + 'Algorithms/')
        sys.path.append(algorithms_dirpath)
        import rpy2_classifiers
        rc = rpy2_classifiers.Rpy2Classifier(algorithms_dirpath=algorithms_dirpath)

        arff_str = open(color_arff_fpath).read()
        data_dict = rc.parse_full_arff(arff_str=arff_str, skip_missingval_lines=True, fill_arff_rows=True)

        
        #ncaa = Nomad_Colors_Assoc_AL()
        #ncaa.parse_arff_files()
        import pdb; pdb.set_trace()
        print()



    projid = 126 # 123
    pkl_fpath = '/home/dstarr/scratch/get_colors_for_tutor_sources_%d.pkl' % (projid)
    if 1:
        if 0:
            ### (for Analysis of NOMAD associations: Deboss HIPP and OGLE, and probably works with ASAS):
            GetColorsUsingNomad.analyze_nomad_tutor_source_param_relations(projid=projid,
                                                                           pkl_fpath=pkl_fpath)

            sys.exit()
        ### Generate associations of NOMAD sources with tutor sources for a project_id.
        #   Store in list file and .pkl
        ### NOTE: the do_store_nomad_sources_for_classifier=True flag is only needed to generate .arff
        #         for seperate WEKA classifier training with existing hardcoded decision tree.
        
        best_nomad_sources = GetColorsUsingNomad.generate_nomad_tutor_source_associations(projid=projid,
                                                                                          pkl_fpath=pkl_fpath,
                                                                                          do_store_nomad_sources_for_classifier=True,
                                                                                          add_extinction=False)
        GetColorsUsingNomad.update_bestnomad_list_file(best_nomad_lists=best_nomad_sources, projid=projid)

    if 0:
        # as of 20110623 this is more obsolete and succeeded by:
        #        GetColorsUsingNomad.generate_nomad_tutor_source_associations()
        ### This retrieves NOMAD colors for all tutor sources and stores in a file which will be used
        ###      by feature extractors, eg on citris33

        GetColorsUsingNomad.main(projid_list=[126], asas_ndarray=asas_ndarray)

    if 0:
        ### This is to fill the source_test_db.activelearn_filter_mags TABLE:
        #tutor_source_dict = GetColors.query_tutor_sources() # this gets Deboss and ASAS project source_ids, ra, dec

        ### This is more obsolete since this information is now in a filled best_nomad_src_list:
        #GetColors.add_debosscher_SIMBAD_or_ACVS_mags(asas_ndarray=asas_ndarray, tutor_source_dict=tutor_source_dict)
        #GetColors.add_SIMBAD_or_ACVS_mags(asas_ndarray=asas_ndarray, tutor_source_dict=tutor_source_dict)

        GetColors = Get_Colors(pars=pars)
        adict = GetColors.parse_dict_from_bestnomadsrclist()
        tutor_source_dict = adict['tutor_source_dict']
        all_srcid_classid = adict['all_srcid_classid']

        GetColors.fill_per_amp_webdat_file(all_srcid_classid=all_srcid_classid)
        
        GetColors.insert_mags_into_db(tutor_source_dict=tutor_source_dict)
        
        ### This is for filling the file referenced by ALLStars for tutor source colors:
        GetColors.fill_webplot_data_files() # Assuming activelearn_filter_mags TABLE is already populated

