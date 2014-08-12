#!/usr/bin/env python 

import os,sys
import xmlrpclib

if (len(sys.argv) != 2):
    print "invalid input"
    sys.exit()
try:
    src_id = int(sys.argv[1])
except:
    print "invalid src_id"
    sys.exit()

#server = xmlrpclib.ServerProxy("http://lyra.berkeley.edu:34583")
server = xmlrpclib.ServerProxy("http://192.168.1.65:34583")
print server.get_vosource_url_for_srcid(src_id)
