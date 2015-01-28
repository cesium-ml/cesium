#!/usr/bin/env python
""" Adapted from josh's simbad.py
"""

import os, sys

import urllib


def query_votable(src_name="HD 27290"):

    #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"
    #html_pre = "http://simbad.harvard.edu/simbad/sim-coo?"
    html = "http://simbad.harvard.edu/simbad/sim-id?"


    #params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
    #                               'Radius': rad, 'Radius.unit': "arcsec"})
    
    params = urllib.urlencode({'output.format': "VOTABLE", "Ident":src_name, "NbIdent":1, \
                               'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
    f = urllib.urlopen("%s%s" % (html,params))
    s = f.read()
    f.close()
    return s


def parse_class(votable_str):
    import amara
    
    a = amara.parse(votable_str)
    #b = a.xml_select("/VOTABLE/RESOURCE/TABLE/FIELD")
    #b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/FIELD[@name='OTYPE']")
    b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/FIELD")
    i_col_otype = -1
    for i, elem in enumerate(b):
        if elem['name'] == 'OTYPE':
            i_col_otype = i
            break
    b = a.xml_xpath("/VOTABLE/RESOURCE/TABLE/DATA/TABLEDATA/TR/TD")
    #print len(b[i_col_otype])
    return str(b[i_col_otype])




def query_html(src_name = "HD 27290"):
    """ This returns the various associated ids that a source has, unlike in the votable case
    """
    #alt_html_pre = "http://simbad.u-strasbg.fr/simbad/sim-coo?"
    #html_pre = "http://simbad.harvard.edu/simbad/sim-coo?"
    html = "http://simbad.harvard.edu/simbad/sim-id?"


    #params = urllib.urlencode({'output.format': "VOTABLE", "Coord": "%fd%f" % (ra, dec),\
    #                               'Radius': rad, 'Radius.unit': "arcsec"})
    
    params = urllib.urlencode({'output.format': "html", "Ident":src_name, "NbIdent":1, \
                               'Radius': 2, 'Radius.unit': "arcsec", 'submit':'submit id'})
    f = urllib.urlopen("%s%s" % (html,params))
    s = f.read()
    f.close()
    #print s
    #a = amara.parse(s)
    #b = a.xml_select("/VOTABLE/RESOURCE/TABLE/FIELD")
    return s


def parse_html_for_ids(html_str, instr_identifier='HIP'):
    """
    """
    lines = html_str.split('\n')
    out_id_str_list = []
    for line in lines:
        if (('<A HREF="http://vizier.u-strasbg.fr/viz-bin/VizieR' in line) and
            (instr_identifier in line)):
            id_str = line[line.find('>') + 1:line.rfind('</A>')]
            #print id_str
            out_id_str_list.append(id_str)
    #import pdb; pdb.set_trace()
    return out_id_str_list

if __name__ == '__main__':


    #a_str = query_html(src_name = "HIP 8")
    a_str = query_votable(src_name = "HIP 8")
    sci_class = parse_class(a_str)
    print sci_class

    sys.exit()

    html_str = query_html(src_name = "HD 27290")

    hip_ids = parse_html_for_ids(html_str, instr_identifier='HIP')
    print hip_ids
