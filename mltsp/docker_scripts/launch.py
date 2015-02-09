#!/usr/bin/env python


from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import subprocess
import sys
import os

if not len(sys.argv) > 1:
    print("usage: launch.py filename.py")
    sys.exit(-1)

file_to_launch = sys.argv[1]
if not os.path.exists(file_to_launch):
    print("Cannot find script to launch")
    sys.exit(-1)

args = ['python'] + sys.argv[1:]
print("Launching ", ' '.join(args))
err = subprocess.call(args)

if err == 0:
    print("Script completed successfully.  Stopping supervisord.")
    subprocess.call(["supervisorctl", "shutdown"])
else:
    sys.exit(err)
