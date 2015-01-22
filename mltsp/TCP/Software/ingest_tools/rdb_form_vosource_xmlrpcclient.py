from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import *
from future import standard_library
standard_library.install_aliases()
#!/usr/bin/env python

import os,sys
import xmlrpc.client

if (len(sys.argv) != 2):
    print("invalid input")
    sys.exit()
try:
    src_id = int(sys.argv[1])
except:
    print("invalid src_id")
    sys.exit()

#server = xmlrpclib.ServerProxy("http://lyra.berkeley.edu:34583")
server = xmlrpc.client.ServerProxy("http://192.168.1.65:34583")
print(server.get_vosource_url_for_srcid(src_id))
