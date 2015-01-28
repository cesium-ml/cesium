#!/usr/bin/env python 
"""
This module is intended to:
 - Remotely retrieve a source for a given (ra,dec)
 - generate VOEvent'esque XML encapsulation of source
 - Apply feature extraction for this source.
 - (update?) XML encapsulation of source to include feature extaction info.
 - (?) Hook into an HTML/PHP interface for source query & Source XML return
"""
import sys, os

def check_dependencies():
    """ Check for various dependencies.
    """
    needed_envs_list = ["TCP_DIR"]
    for env_name in needed_envs_list:
        if not os.environ.has_key(env_name):
            print "ERROR: Environ Var: %s not defined!" % (env_name)
            sys.exit()
        elif len(os.environ[env_name]) == 0:
            print "ERROR: Environ Var: %s len()==0" % (env_name)
            sys.exit()



if __name__ == '__main__':
    check_dependencies()

    """ NOTE: No need to do this if run within Lyra LAN:
    To run this locally, you'll want to set up a tunnel from here->lyra->linux
    ssh  -L 8000:192.168.1.35:8000 lyra
    Leave that window open."""

    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                              'Software/feature_extract/Code'))
    import db_importer

    # 20071019: disable this for now:
    if 0:
        source_xml_fpath = '/tmp/source.xml'
        pe = PositionExtractor(pos=(49.599497, -1.0050998),radius=0.05, \
                           host="localhost",port=8000)
        pe.search_pos(out_xml_fpath=source_xml_fpath)

    ### TODO: Maybe interactivly try these out:
    #pe.summary_plot()
    #pe.ds9_summary()
    #print pe.sources[0].d['ts'][filt]['t']
    #####
    sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
    from Code import *
    #sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
    import generators_importers
    signals_list = []
    ###gen = generators_importers.uneven_sine_gen(signals_list)
    ###gen.generate() #GIVES: AttributeError: "'uneven_sine_gen' object has no attribute 'sig'"
    ###sig = signals_list[-1]
    ####### TODO: see whether sig contains classes / methods:
    ###sig.properties['data']['inter']['99pct significant power'].plots()
    ####
    gen = generators_importers.from_xml(signals_list) # see Software/feature_extract/Code/main.py
    source_xml_fpath = '/tmp/source.xml'
    gen.generate(xml_handle=source_xml_fpath, make_xml_if_given_dict=False)
    # I get the following lines from main.py.test() :
    sig = signals_list[-1]
    sig.properties['data']['inter']['99pct significant power'].plots()
    # # # # # #
    # TODO: I should figure where the feature extracted info is.
    #   - or whether I need to run multiple methods to get all possible
    #     extracted features.

    # I shold be able to get source dict using something like:
    import xmlrpclib
    server = xmlrpclib.ServerProxy("http://192.168.1.45:8000")
    print server.system.listMethods()
    print server.system.methodHelp("get_sources_for_radec")
    #src_list = server.get_sources_for_radec(ra, dec, box_range)
