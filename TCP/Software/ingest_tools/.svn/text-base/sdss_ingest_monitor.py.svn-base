#!/usr/bin/env python
"""
   v0.1 Initial version: thread off ingest_tools.py instances to muli nodes.
"""

#TODO: Test before threading, that the ssh method exists until finished
#       (wait for bug to occur)
#TODO: I should have a thread list, which the main while()
#      tests whether each thread is no longer alive.
#      - if not alive, then removes thread;
#           - records that another thread can be initiated on this node

import sys, os
import threading
import time
import random

"""
        '192.168.0.123':{\
            'hostname':'192.168.0.123',
            'exec_fpath':'/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py',
            'n_instances':2,
            'nice':1},
        },
        '192.168.0.106':{\
            'hostname':'192.168.0.106',
            'exec_fpath':'/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py',
            'n_instances':8,
            'nice':19},
"""
pars = {\
    'host_defs':{\
        'localhost':{\
            'hostname':'localhost',
            'exec_fpath':'/home/dstarr/src/TCP/Software/ingest_tools/ingest_tools.py',
            'n_instances':6,
            'nice':0},
        },
    }

class Sdss_Ingest_Monitor:
    """ Threads off multiple ingest_tools.py instances to various nodes.
    """
    def __init__(self, pars):
        self.pars = pars
        self.running_tasks = {}
        for hostname in self.pars['host_defs'].keys():
            self.running_tasks.update({hostname:{'running_threads':[]}})

    def ingest_thread(self, node_dict):
        """ Method which is threaded off, and executes ssh connection.
        """
        #for i in range(10):
        #    print i, node_dict['hostname']
        #    time.sleep(random.random()*5)

        # TODO/DEBUG: Do I want to '&' this task?  I don't think so...
        #ssh_str = """ssh -x -n %s nice -%d %s >& /dev/null""" % (\
        #ssh_str = """ssh -n %s nice -%d %s""" % (\
        #    node_dict['hostname'], node_dict['nice'], node_dict['exec_fpath'])
        ssh_str = """nice -%d %s do_populate_sdss=1""" % (node_dict['nice'], \
                                                       node_dict['exec_fpath'])
        # 20070913 Commented out:
        #ssh_str = """%s do_populate_sdss=1""" % (node_dict['exec_fpath'])
        #print ssh_str
        os.system(ssh_str)
        #print 'os.system(ssh) DONE!'
        #sys.exit()

        
    def check_finished_threads(self):
        """ Check whether any of the threads are done.
        Remove them from the threads[]
        """
        for hostname,run_dict in self.running_tasks.iteritems():
            for t in run_dict['running_threads']:
                if not t.isAlive():
                    run_dict['running_threads'].remove(t)
                    print 'removed from:', hostname


    def start_new_threads(self):
        """ Start new tasks on available nodes.
        """
        for hostname,run_dict in self.running_tasks.iteritems():
            n_tasks_to_spawn = self.pars['host_defs'][hostname]['n_instances'] - len(run_dict['running_threads'])
            while (n_tasks_to_spawn > 0):
                #self.ingest_thread(self.pars['host_defs'][hostname])
                t = threading.Thread(target=self.ingest_thread, \
                                     args=[self.pars['host_defs'][hostname]])
                t.start()
                run_dict['running_threads'].append(t)
                n_tasks_to_spawn = self.pars['host_defs'][hostname]['n_instances'] - len(run_dict['running_threads'])


    def monitor_loop(self):
        """ Main loop which spawns threads and monitors them.
        """
        i = 0
        while 1:
            self.check_finished_threads()
            self.start_new_threads()
            #print '...sleep'
            time.sleep(3)
            #i += 1



if __name__ == '__main__':

    sim = Sdss_Ingest_Monitor(pars)
    sim.monitor_loop()
