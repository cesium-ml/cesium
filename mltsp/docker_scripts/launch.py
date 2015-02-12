#!/usr/bin/env python

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
