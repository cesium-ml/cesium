# docker_featurize.py

# to be run from INSIDE a docker container

import subprocess
import sys
import os
sys.path.append("/home/mltp")
import build_rf_model
from subprocess import Popen, PIPE, call
import cPickle
import time


def disco_test():
    """Try to start Disco from inside Docker container."""
    
    
    '''
    process = Popen(["/usr/bin/supervisord"])
    time.sleep(2)
    
    process = Popen(["ps", "aux"], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print "beam", ("IS" if "beam" in str(stdout) else "is NOT"),\
          "in 'ps aux' output"
    print "epmd", ("IS" if "epmd" in str(stdout) else "is NOT"),\
          "in 'ps aux' output"
    print "\n\n\n", stdout, "\n\n\n"
    '''
    
    status_code = call(["/disco/bin/disco", "nodaemon"])
    time.sleep(2)
    
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
        
        #print "Calling '/disco/bin/disco nodaemon -v':"
        #status_code = Popen(["/disco/bin/disco", "nodaemon", "-v"])
        #process = Popen(["/start_disco"], stdout=PIPE, stderr=PIPE)
        #stdout, stderr = process.communicate()
        #print stdout,"\n\n\n",stderr
        
        process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print ("stdout and stderr for 'disco status' command after "
               "calling '/start_disco': \n"), stdout,"\n\n",stderr
        if "stopped" in str(stdout):
            print "Calling '/disco/bin/disco nodaemon':"
            status_code = call(["/disco/bin/disco", "nodaemon"])
            #process = Popen(["/start_disco"], stdout=PIPE, stderr=PIPE)
            #stdout, stderr = process.communicate()
            #print stdout,"\n\n\n",stderr
            process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print ("stdout and stderr for 'disco status' command after "
                   "calling '/disco/bin/disco nodaemon': \n"), stdout,"\n\n",stderr
            
            time.sleep(1)
            
            process = Popen(["disco", "status"], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print ("stdout and stderr for 'disco status' command after "
                   "calling '/disco/bin/disco nodaemon': \n"), stdout,"\n\n",stderr
            
    return ""


if __name__=="__main__":
    results_str = disco_test()
    print results_str
