# docker_featurize.py

# to be run from INSIDE a docker container

import subprocess
import sys
import os
sys.path.append("/home/mltp")
import build_rf_model
from subprocess import Popen, PIPE, call
import cPickle


def disco_test():
    '''See if Disco runs correctly inside Docker container.
    
    To be run inside Docker container.
    '''
    process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "stdout and stderr for 'disco status' command: \n", \
          stdout,"\n\n",stderr
    if "stopped" in str(stdout):
        print "Calling 'disco start':"
        status_code = call(["disco", "start"])#, stdout=PIPE, stderr=PIPE)
        #process = Popen(["/start_disco"], stdout=PIPE, stderr=PIPE)
        #stdout, stderr = process.communicate()
        #print stdout,"\n\n\n",stderr
        
        process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print ("stdout and stderr for 'disco status' command after "
               "calling '/start_disco': \n"), stdout,"\n\n",stderr
        
        if "stopped" in str(stdout):
            print "Calling '/disco/bin/disco debug':"
            status_code = call(["/disco/bin/disco", "nodaemon"])
            #process = Popen(["/start_disco"], stdout=PIPE, stderr=PIPE)
            #stdout, stderr = process.communicate()
            #print stdout,"\n\n\n",stderr
            
            process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print ("stdout and stderr for 'disco status' command after "
                   "calling '/start_disco': \n"), stdout,"\n\n",stderr
        
    return ""


if __name__=="__main__":
    results_str = disco_test()
    print results_str
