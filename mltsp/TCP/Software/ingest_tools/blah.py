#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import os
import subprocess
p = subprocess.Popen("/home/dstarr/src/TCP/Software/ingest_tools/lcs_classif.py http://127.0.0.1:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
sts = os.waitpid(p.pid, 0)
script_output = p.stdout.readlines()
print(script_output[0])
