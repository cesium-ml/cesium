#!/usr/bin/env python 
"""
   v0.1 Tool used for initating an Ipython (v0.9.1+) cluster using
        multiple nodes This actually uses ipcontroller and ipengine
        rather than the obsolete ipcluster.

NOTE: if installing ipython controller (and engines) on a new computer,
   - need to rm ~/.ipython/security/ipcontroller-engine.furl
        prior to running ipython_cluster_setup.py


NOTE: Requires prior setup of ssh tunneling for:
       - from controller computer to engine client computers
       - from engine client computers to controller computer

TO SETUP a remote, ssh tunneled ipengine node:
  - install OpenSSL for python

       apt-get install python-openssl

  - Make a passwordless ssh tunnel to the ipengine client
    so that you can scp (or you can let the script by uncommenting
    scp ~/.ipython/ipcontroller-engine.furl to the ipengine client.

  - SETUP an ssh tunnel on the ipengine client for controller/engine (worms2)

       ssh -L 23610:localhost:23611 pteluser@lyra.berkeley.edu

  - SETUP an ssh tunnel on the ipcontroller computer for controller/engine (transx)

       ssh -R 23611:localhost:23612 pteluser@lyra.berkeley.edu
  
  - EDIT the ipcontroller-engine.furl on the ipengine client computer
    so that the 2nd IP is 127.0.0.1 and the portforwared port.  Eg:

    e.g.: ipcontroller computer ipcontroller-engine.furl is:
       pb://3r___rcx@127.0.0.1:23612,192.168.1.25:23612/ec___yi

    and once edited on ipengine client computer, looks like:
       pb://3r___rcx@127.0.0.1:23612,127.0.0.1:23610/ec___yi

  - Also ensure that TCP environ var setting will work duing mec.execute():
os.environ['TCP_SEX_BIN']=os.path.expandvars('$HOME/bin/sex')
os.environ['TCP_WCSTOOLS_DIR']=os.path.expandvars('$HOME/src/install/wcstools-3.6.4/bin/')
os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')

  - NOW you are ready to run ipython_cluster_setup.py, which will
    kill and start the ipcontroller, start ipengines,
    and run a TaskClient test.

    

TODO: Eventually have this script run by testsuite.py?

TODO: Is ipcontroller doing some logging?
      - Is this essentially a memory leak/growth?

TODO: EC2 connection?

"""
import os, sys
import time
import threading # used for scp/ssh tasks.
from IPython.kernel import client

class Setup_System:
    """ Setup Ipython controller and engines.

    """
    def __init__(self, pars={}):
        self.pars = pars


    def kill_existing_controller(self):
        """
        """
        # Default is SIGTERM
        exec_str = "pkill -f .*ipcontroller.*"
        #KILLS SCREEN NOOOO! #exec_str = "pkill -f .*ipengine.*"
        os.system(exec_str)
        

    def initialize_controller(self):
        """ initialize controller on local machine.
        """
        # -y -x flags turn off engine and client security, which is ok since SSH tunnels are used.
        #exec_str = "ipcontroller -y -x --client-port=%d --engine-port=%d &" % \
        exec_str = "ipcontroller --client-port=%d --engine-port=%d &" % \
                             (self.pars['client_port'],
                              self.pars['engine_port'])
        os.system(exec_str)


    def scp_furls_to_clients(self):
        """ scp controller furl file to task client machines.

        Also modifies the generated_enginefurl to have the correct ports for port-forward use.
        """
        lines = open(self.pars['generated_engine_furl_fpath']).readlines()
        new_line = lines[0].replace('192.168.1.25:%d' % (self.pars['engine_port']),\
                         '127.0.0.1:%d' % (self.pars['tunneled_engine_client_port']))
        new_furl_fp = open(self.pars['modified_engine_furl_fpath'],'w')
        new_furl_fp.write(new_line)
        new_furl_fp.close()


        thread_list = []
        for client_dict in self.pars['client_defs']:
            if ('__local__' in client_dict['name']):
                continue # skip the scp since generated on same machine
            elif ('__trans' in client_dict['name']):
                exec_str = "scp -C -P %d %s %s@%s:%s/ipcontroller-engine.furl" % (client_dict['ssh_port'],
                                                      self.pars['generated_engine_furl_fpath'],
                                                      client_dict['username'],
                                                      client_dict['hostname'],
                                                      client_dict['furl_dirpath'])
                t = threading.Thread(target=os.system, args=[exec_str])
                t.start()
                thread_list.append(t)
            else:
                exec_str = "scp -C -P %d %s %s@%s:%s/ipcontroller-engine.furl" % (client_dict['ssh_port'],
                                                      self.pars['modified_engine_furl_fpath'],
                                                      client_dict['username'],
                                                      client_dict['hostname'],
                                                      client_dict['furl_dirpath'])
                t = threading.Thread(target=os.system, args=[exec_str])
                t.start()
                thread_list.append(t)

        for t in thread_list:
            print "scp/ssh thread (%s) waiting..." % (client_dict['hostname'])
            t.join(10.0) # wait 10 seconds for scp/ssh
            if t.isAlive():
                print "! Thread (%s) has not returned! (dead host?)" % (client_dict['hostname'])
                

    def kill_engines_on_taskclients(self):
        """ pkill any existing ipengines on local and remote
        ipengine client machines.
        """
        thread_list = []

        #DISABLED: try doing this 2x:
        for i in xrange(1):
            for client_dict in self.pars['client_defs']:
                # Comment this out if I want to KILL engines on trans[123]
                #if ('__trans' in client_dict['name']):
                #    continue # KLUDGE dont kill ipengines on trans[123] computers
                #exec_str = "ssh -fn -p %d %s@%s pkill -9 -f .*bin.ipengine" % ( \
                #                       client_dict['ssh_port'],
                #                       client_dict['username'],
                #                       client_dict['hostname'])
                home_dirpath = client_dict['furl_dirpath'][:client_dict['furl_dirpath'].find('.ipython')]
                exec_str = "ssh -fn -p %d %s@%s %ssrc/TCP/Algorithms/ipengine_kill.py" % ( \
                                       client_dict['ssh_port'],
                                       client_dict['username'],
                                       client_dict['hostname'],
                                       home_dirpath)
                print exec_str
                t = threading.Thread(target=os.system, args=[exec_str])
                t.start()
                thread_list.append(t)

        for t in thread_list:
            print "scp/ssh thread (%s) waiting..." % (client_dict['hostname'])
            t.join(10.0) # wait 10 seconds for scp/ssh
            if t.isAlive():
                print "! Thread (%s) has not returned! (dead host?)" % (client_dict['hostname'])


    def start_engines_on_taskclients(self):
        """ Start ipengine clients on local and remote machines
        """
        # IF CURRENT IMPLEMENTATION POSES PROBLEMS:
        # Maybe have a daemon on the remote machine which can be given
        #       a config file & restarted (which kills existing
        #       engines), and the daemon will spawn the engines
        #       without need of a continuous ssh session from
        #       ipython_clister_setup.py host.
        #   - This would allow for the ~dozen engines to be easily spawned

        thread_list = []
        for client_dict in self.pars['client_defs']:
            for i in xrange(client_dict['n_engines']):
                if ('__local__' in client_dict['name']):
                    exec_str = "ipengine &"
                    os.system(exec_str)
                else:
                    # here we spawn a remote ssh session.
                    ### NOTE: nice -19 works, but since I run on my onw machines, I dont do:
                    #exec_str = "ssh -fn -p %d %s@%s nice -19 ipengine &" % ( \
                    if client_dict.has_key('nice'):
                        exec_str = "ssh -fn -p %d %s@%s nice -%d ipengine &" % ( \
                                           client_dict['ssh_port'],
                                           client_dict['username'],
                                           client_dict['hostname'],
                                           client_dict['nice'])
                    else:
                        exec_str = "ssh -fn -p %d %s@%s ipengine &" % ( \
                                           client_dict['ssh_port'],
                                           client_dict['username'],
                                           client_dict['hostname'])
                    print exec_str
                    t = threading.Thread(target=os.system, args=[exec_str])
                    t.start()
                    thread_list.append(t)
        for t in thread_list:
            print "scp/ssh thread (%s) waiting..." % (client_dict['hostname'])
            t.join(20.0) # wait 10 seconds for scp/ssh
            if t.isAlive():
                print "! Thread (%s) has not returned! (dead host?)" % (client_dict['hostname'])


    def main(self):
        """ Main function.

        """
        flag_done = False
        while not flag_done:
            try:
                self.kill_existing_controller()
                time.sleep(5)
                self.initialize_controller()
                time.sleep(20) # we need to wait for the ipcontroller to generate new .furl files
                self.scp_furls_to_clients()
                self.kill_engines_on_taskclients()
                #sys.exit()
                time.sleep(5)
                self.start_engines_on_taskclients()
                flag_done = True
            except:
                print "Setup_System.main() Except.  sleeping(20)"
                time.sleep(20) # wait a couple seconds, probably an incomplete file scp or .mec() initialization failure.


class Test_System:
    """ Run a test case of Ipython parallelization.

    """
    def __init__(self, pars={}):
        self.pars = pars

    def main(self):
        """ Main function for Testing.
        """
        # This tests the Multi-engine interface:
        mec = client.MultiEngineClient()
        exec_str = """import os
os.environ['TCP_SEX_BIN']=os.path.expandvars('$HOME/bin/sex')
os.environ['TCP_WCSTOOLS_DIR']=os.path.expandvars('$HOME/src/install/wcstools-3.6.4/bin/')
os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')
os.environ['CLASSPATH']=os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar')

        """
        #if os.path.exists(os.path.expandvars("$HOME/.ipython/custom_configs")): execfile(os.path.expandvars("$HOME/.ipython/custom_configs"))
        mec.execute(exec_str)

        # This tests the task client interface:
        tc = client.TaskClient()
        task_list = []

        n_iters_total = 8
        n_iters_per_clear = 10
        for i in xrange(n_iters_total):
            task_str = """cat = os.getpid()""" # os.getpid() # os.environ
            taskid = tc.run(client.StringTask(task_str, pull="cat"))
            task_list.append(taskid)
            ### NOTE: This can be used to thin down the ipcontroller memory storage of
            ###       finished tasks, but afterwards you cannot retrieve values (below):
            #if (i % n_iters_per_clear == 0):
            #    tc.clear()
        print '!!! NUMBER OF TASKS STILL SCHEDULED: ', tc.queue_status()['scheduled']
        for i,taskid in enumerate(task_list):
            ### NOTE: The following retrieval doesnt work if 
            ###       tc.clear()      was called earlier:
            task_result = tc.get_task_result(taskid, block=True)
            print task_result['cat']
        print 'done'
        print tc.queue_status()
        #del tc
        #time.sleep(1)

if __name__ == '__main__':

    if len(sys.argv) > 1:
        # We can assume we were given a python file to exec() which contains a pars={} dict.
        # TODO: read pars from file.
        f = open(os.path.abspath(os.path.expandvars(sys.argv[1])))# Import the standard Parameter file
        exec f
        f.close()
    else:
        pars = { \
            'client_port':10113, # Controller listen port for python taskclient connections
            'engine_port':23612, # Controller listen port for engine connections
            'tunneled_engine_client_port':23610, # port used on the engine client to get back to ipcontroller
            'generated_engine_furl_fpath':'/home/pteluser/.ipython/security/ipcontroller-engine.furl',
            'modified_engine_furl_fpath':'/tmp/temp_engine_furl_fpath',
            'engine-cert-file':'',  # this is shared by all engines.  ?Maybe it is manually copied over once, initially? Although this .pem is not identical to the ipcontroller computer.
            'client_defs':[ \
                {'name':'__local__',
                 'hostname':'127.0.0.1',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                 'n_engines':10},
                ],
            }

    SetupSystem = Setup_System(pars=pars)
    SetupSystem.main()

    # FOR TESTING:
    time.sleep(20) # (70) # We give some time for controller to initialize (sgn02 requires > 30secs)
    TestSystem = Test_System()
    TestSystem.main()
    time.sleep(0.01) # This seems to fix a traceback where Ipython/Twisted trips on itself while shutting down
    
    """
                {'name':'__local__',
                 'hostname':'127.0.0.1',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                 'n_engines':8},
                {'name':'__trans_betsy__',
                 'hostname':'192.168.1.85',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                 'n_engines':8},
                {'name':'__trans1__',
                 'hostname':'192.168.1.45',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                'n_engines':2},
                {'name':'__trans2__',
                 'hostname':'192.168.1.55',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                 'n_engines':2},
                {'name':'__trans3__',
                 'hostname':'192.168.1.65',
                 'furl_dirpath':'/home/pteluser/.ipython/security',
                 'username':'pteluser',
                 'ssh_port':22,
                 'n_engines':2},
            {'name':'__worms2__',
             'hostname':'localhost',
             'furl_dirpath':'/home/starr/.ipython/security',
             'username':'starr',
             'ssh_port':32151,
             'n_engines':6},

                {'name':'__cch1__',
                 'hostname':'localhost',
                 'furl_dirpath':'/home/dstarr/.ipython/security',
                 'username':'dstarr',
                 'nice':19,
                 'ssh_port':32161,
                 'n_engines':1},

            {'name':'__sgn02__',
             'hostname':'localhost',
             'furl_dirpath':'/global/homes/d/dstarr/datatran/.ipython/security',
             'username':'dstarr',
             'ssh_port':32141,
             'n_engines':0},  # 6

    """
