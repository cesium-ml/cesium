#!/usr/bin/env python

import os
import subprocess
p = subprocess.Popen("/home/dstarr/src/TCP/Software/ingest_tools/lcs_classif.py http://127.0.0.1:5123/get_lc_data/?filename=dotastro_215153.dat&sep=,", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
sts = os.waitpid(p.pid, 0)
script_output = p.stdout.readlines()
print script_output[0]

