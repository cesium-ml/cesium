#!/usr/bin/env python
"""

Given a list of older vosource.xmls, this re-generates
the vosource.xmls, adding new features.

This code saves XMLs into a seperate directory.

"""
from __future__ import print_function
import os, sys

sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from Code import *
import db_importer
import glob
import time

from IPython.kernel import client
from optparse import OptionParser


# # # # FOR DEBUGGING ONLY:
#import os,sys
#os.environ['TCP_SEX_BIN']=os.path.expandvars('$HOME/bin/sex')
#os.environ['TCP_WCSTOOLS_DIR']=os.path.expandvars('$HOME/src/install/wcstools-3.6.4/bin/')
#os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
#os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')
#os.environ['CLASSPATH']=os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar')
#sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
#sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
#from Code import *
#import db_importer
# # # # 

class Regenerate_Vosource_Xmls:
    """
Given a list of older vosource.xmls, this re-generates
the vosource.xmls, adding new features.

This code saves XMLs into a seperate directory.
    """
    def __init__(self, pars={}):
        self.pars = pars

    def main(self):
        """ main method
        
        This method runs linear tasks and thus is becoming obsolete.
        """
        if not os.path.exists(self.pars['new_xmls_dirpath']):
            os.system("mkdir -p %s" % (self.pars['new_xmls_dirpath']))

        old_xml_fpaths = glob.glob("%s/*xml" % (self.pars['old_xmls_dirpath']))
        
        for old_xml_fpath in old_xml_fpaths:
            signals_list = []
            gen = generators_importers.from_xml(signals_list)
            gen.generate(xml_handle=old_xml_fpath)
            gen.sig.add_features_to_xml_string(gen.signals_list)

            fname = old_xml_fpath[old_xml_fpath.rfind('/')+1:]
            new_xml_fpath = "%s/%s" % (self.pars['new_xmls_dirpath'], fname)

            gen.sig.write_xml(out_xml_fpath=new_xml_fpath)
            #print "Wrote: ", new_xml_fpath


    def initialize_ipengines(self):
        """ Initialize ipengines, load environ vars, etc.
        """
        self.mec = client.MultiEngineClient()
        #THE FOLLOWING LINE IS DANGEROUS WHEN OTHER TYPES OF TASKS MAY BE OCCURING:
        self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        self.tc = client.TaskClient()
        self.tc.clear() # This supposedly clears the list of finished task objects in the task-client
        self.mec.flush() # This doesnt seem to do much in our system.
        #self.mec.reset(targets=self.mec.get_ids()) # Reset the namespaces of all engines
        exec_str = """import os,sys
os.environ['TCP_SEX_BIN']=os.path.expandvars('$HOME/bin/sex')
os.environ['TCP_WCSTOOLS_DIR']=os.path.expandvars('$HOME/src/install/wcstools-3.6.4/bin/')
os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')
os.environ['CLASSPATH']=os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar')
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + 'Software/feature_extract/Code'))
from Code import *
import db_importer
        """
        self.mec.execute(exec_str)


    def spawn_tasks_using_beowulf_beorun(self):
        """ This spawns beowulf cluster tasks using beorun.

        using all vosource.xml in 'old_xmls_dirpath'

        NOTE: This is intended to be run on a single machine (transx)

        # TODO: now iterate over task_fpath_list and do:
        # beorun /home/dstarr/src/TCP/Software/ingest_tools/beowulf_task_regenerate_vosource_xmls.py __task_file___ ...
        # TODO 1: first try beorun with 10 taks
        # TODO 2: then try beorun with 80 tasks
        # TODO 3: then try beorun with 120 tasks (to see if it queues properly)

        """
        import time
        import random
        import copy
        import threading
        n_cpus_per_node = 8
        node_id_list = [1,2,3,4,5,6,7,8,9,10,0]

        feat_vsrc_dirpath = self.pars['new_xmls_dirpath'][:self.pars['new_xmls_dirpath'].rfind('/')] + '/featured_vosource'
        if not os.path.exists(feat_vsrc_dirpath):
            os.system("mkdir -p %s" % (feat_vsrc_dirpath))

        task_dirpath = self.pars['new_xmls_dirpath'][:self.pars['new_xmls_dirpath'].rfind('/')] + '/beorun_tasks'
        if os.path.exists(task_dirpath):
            if len(task_dirpath) > 20:
                # sanity check B4 doing
                os.system("rm -Rf %s" % task_dirpath)
        os.system("mkdir -p %s" % (task_dirpath))

        old_xml_fpaths = glob.glob("%s/*xml" % (self.pars['old_xmls_dirpath']))

        #n_rows_in_taskfile = 10
        n_rows_in_taskfile = len(old_xml_fpaths) / (len(node_id_list) * n_cpus_per_node)
        #extra_rows_in_taskfile = len(old_xml_fpaths) % (len(node_id_list) * n_cpus_per_node)

        task_fpath_list = []
        #for old_xml_fpath in old_xml_fpaths:
        for i in range(n_rows_in_taskfile, len(old_xml_fpaths), n_rows_in_taskfile):
            task_fpath = "%s/regen%lf_%d" % (task_dirpath, time.time(), 
                                             random.randint(0,100000000))
            fp = open(task_fpath, 'w')
            for xml_fpath in old_xml_fpaths[(i - n_rows_in_taskfile):i]:
                fp.write(xml_fpath + '\n')
            fp.close()
            task_fpath_list.append(task_fpath)
        # Catch the last bits:
        if i < len(old_xml_fpaths):
            task_fpath = "%s/regen%lf_%d" % (task_dirpath, time.time(), 
                                             random.randint(0,100000000))
            fp = open(task_fpath, 'w')
            for xml_fpath in old_xml_fpaths[i:len(old_xml_fpaths) - 1]:
                fp.write(xml_fpath + '\n')
            fp.close()
            task_fpath_list.append(task_fpath)
        
        #n_tasks_per_cpu = 10 # 80
        ### iterate over node number list
        ###   - iterate over the n_cpus_per_node
        #for i in range(n_tasks_per_cpu, len(task_fpath_list), n_tasks_per_cpu):
        #    #exec_str = "beorun --no-local /home/dstarr/src/TCP/Software/ingest_tools/beowulf_task_regenerate_vosource_xmls.py "
        threads = []
        for i_cpu in range(n_cpus_per_node):
            for i_node in range(len(node_id_list)):
                node_id = node_id_list[i_node]
                i_task = i_node * n_cpus_per_node + i_cpu
                #exec_str = "bpsh -M %d /home/dstarr/src/TCP/Software/ingest_tools/beowulf_task_regenerate_vosource_xmls.py %s " % (node_id, task_fpath_list[i_task])
                exec_str = "bpsh -m %d /home/dstarr/src/TCP/Software/ingest_tools/beowulf_task_regenerate_vosource_xmls.py %s >& /dev/null" % (node_id, task_fpath_list[i_task])
                t = threading.Thread(target=os.system, args=[copy.copy(exec_str)])
                threads.append(t)
                t.start()
                #time.sleep(1)
                print('i_cpu:', i_cpu, 'i_node:', i_node)

        while len(threads) > 0:
            for i,t in enumerate(threads):
                if not t.isAlive():
                    threads.remove(t)
                    break # need to do this since in threads[] based loop.
            if i == (len(threads) - 1):
                # went through list without removing
                print("threads left:", len(threads))
                time.sleep(5)

        print("Done: spawn_tasks_using_beowulf_beorun()")


    def spawn_tasks_for_xmlfile(self):
        """ This spawns ipython ipengine tasks for
        all vosource.xml in 'old_xmls_dirpath'

        NOTE: This is intended to be run on a single machine (transx)
        """
        if not os.path.exists(self.pars['new_xmls_dirpath']):
            os.system("mkdir -p %s" % (self.pars['new_xmls_dirpath']))

        old_xml_fpaths = glob.glob("%s/*xml" % (self.pars['old_xmls_dirpath']))
        
        for old_xml_fpath in old_xml_fpaths:
            #       gen.sig.write_xml(out_xml_fpath="%s/%s")
            #       os.system("bpcp %s/%s master:%s/%s")""" % (old_xml_fpath, 

            #exec_str = """signals_list = []
            #gen = generators_importers.from_xml(signals_list)
            #gen.generate(xml_handle="%s")
            #gen.sig.add_features_to_xml_string(gen.signals_list)
            #gen.sig.write_xml(out_xml_fpath="%s/%s")""" % (old_xml_fpath, 
            #                              self.pars['new_xmls_dirpath'],
            #                              old_xml_fpath[old_xml_fpath.rfind('/')+1:])

            ##### This version just saves feature generated sources which found periods:
            """
if period_found:
    gen.sig.write_xml(out_xml_fpath="%s/%s")""" #% (old_xml_fpath, 
            ##### This version just saves feature generated sources which have no found periods:
            """
if not period_found:
    gen.sig.write_xml(out_xml_fpath="%s/%s")""" #% (old_xml_fpath, 


            exec_str = """signals_list = []
gen = generators_importers.from_xml(signals_list)
gen.generate(xml_handle="%s")
gen.sig.add_features_to_xml_string(gen.signals_list)
period_found = False
for filt,filt_dict in gen.signals_list[0].properties['data'].iteritems():
    try:
        if str(filt_dict['features']['freq1_harmonics_freq_0']) == "False":
            pass
        elif float(str(filt_dict['features']['freq1_harmonics_freq_0'])) > 0.0001:
            period_found = True
            break
    except:
        pass
if 1:
    gen.sig.write_xml(out_xml_fpath="%s/%s")""" % (old_xml_fpath, 
                                          self.pars['new_xmls_dirpath'],
                                          old_xml_fpath[old_xml_fpath.rfind('/')+1:])
            taskid = self.tc.run(client.StringTask(exec_str))


    def wait_for_tasks_to_finish(self):
        """ Wait for task client / ipengine tasks to finish.
        """
	while ((self.tc.queue_status()['scheduled'] > 0) or
 	       (self.tc.queue_status()['pending'] > 0)):
            print(self.tc.queue_status())
            print('Sleep... 3 in regenerate_vosource_xmls.py')
            time.sleep(3)
        print('done with while loop')


    def run_debug_task(self):
        """ Just a debugging test case:
        """
        signals_list = []
        gen = generators_importers.from_xml(signals_list)
        gen.generate(xml_handle="/home/dstarr/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/generated_vosource/100018590_8.44635457907.xml")
        gen.sig.add_features_to_xml_string(gen.signals_list)
        gen.sig.write_xml(out_xml_fpath="/home/dstarr/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/featured_vosource/100018590_8.44635457907.xml")
        # bpcp /home/dstarr/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/featured_vosource/100018590_8.44635457907.xml master:/home/dstarr/scratch/Noisification/50nois_17epch_100need_0.050mtrc_qk17.9/featured_vosource/100018590_8.44635457907.xml

    def main_using_ipython_tasking(self):
        """ This is an IPython / parallel version.

        NOTE: This is intended to be run on a single machine (transx)
        """
        # # # # # For DEBUGGING:
        #self.run_debug_task()

        if self.pars['multiprocessing'] is None:
            self.initialize_ipengines()
            self.spawn_tasks_for_xmlfile()
            self.wait_for_tasks_to_finish()
        else:
            self.spawn_tasks_using_beowulf_beorun()

        # TODO: each spawned task should be a script which loads gen... is passed an(multiple?) XML,
        #       and crunches on a processor.
        # The execution command should be:
        #    



if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog cmd [options]")
    parser.add_option("-a","--old_xmls_dirpath",
                      dest="old_xmls_dirpath", 
                      action="store", default=os.path.expandvars('/home/pteluser/scratch/Noisification/10epoch_anyband_nospline_sifted/generated_vosource'),
                      help="")
    parser.add_option("-b","--new_xmls_dirpath",
                      dest="new_xmls_dirpath", 
                      action="store", default=os.path.expandvars('/home/pteluser/scratch/Noisification/10epoch_anyband_nospline_sifted/featured_vosource'),
                      help="")
    parser.add_option("-m","--multiprocessing",
                      dest="multiprocessing", 
                      action="store", default=None,
                      help="")

    (options, args) = parser.parse_args()
    print("For help use flag:  --help") # KLUDGE since always: len(args) == 0

    #pars = {'old_xmls_dirpath':os.path.expandvars('/home/pteluser/scratch/TUTOR_vosources/SNIa_from_20080707tutor'),
    #        'new_xmls_dirpath':os.path.expandvars('/home/pteluser/scratch/TUTOR_vosources/SNIa_from_20080707tutor_new')}
    pars = {'old_xmls_dirpath':options.old_xmls_dirpath,
            'new_xmls_dirpath':options.new_xmls_dirpath,
            'multiprocessing':options.multiprocessing}
    RegenVosXmls = Regenerate_Vosource_Xmls(pars=pars)
    RegenVosXmls.main_using_ipython_tasking()

    # This is older, non-parallel, non-ipython:
    #RegenVosXmls.main()
