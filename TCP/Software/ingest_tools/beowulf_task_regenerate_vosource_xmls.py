#!/usr/bin/env python
"""
This is a very KLUDGY beowulf beorun'able task which unfortunately loads a lot of modules, 
thus being inefficient when compared with the preferred parallel-IPython method.

Called using:

beorun /home/dstarr/src/TCP/Software/ingest_tools/beowulf_task_regenerate_vosource_xmls.py /home/dstarr/scratch/Noisification/50nois_20epch_100need_0.050mtrc_frq17.9/generated_vosource/100018609_11.6262227104.xml /home/dstarr/scratch/Noisification/50nois_20epch_100need_0.050mtrc_frq17.9/generated_vosource/100018609_11.6262227104.xml /home/dstarr/scratch/Noisification/50nois_20epch_100need_0.050mtrc_frq17.9/generated_vosource/100018609_11.6262227104.xml


"""
import os,sys
os.environ['TCP_SEX_BIN']=os.path.expandvars('$HOME/bin/sex')
os.environ['TCP_WCSTOOLS_DIR']=os.path.expandvars('$HOME/src/install/wcstools-3.6.4/bin/')
os.environ['TCP_DIR']=os.path.expandvars('$HOME/src/TCP/')
os.environ['TCP_DATA_DIR']=os.path.expandvars('$HOME/scratch/TCP_scratch/')
os.environ['CLASSPATH']=os.path.expandvars('$HOME/src/install/weka-3-5-7/weka.jar')
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
                                      'Software/feature_extract'))
sys.path.append(os.path.abspath(os.environ.get("TCP_DIR") + \
              'Software/feature_extract/Code'))
from Code import *
import db_importer

class QueueTasks:
    """ Queue the tasks.
    Called by regenerate_vosource_xmls.py instead of IPython parallel code.
    """

    def main(self, xml_fpath_list):
        """
        Input: list of xml_files for processing.
        """
        # TODO: for each set of (10) xmls, write to random-filepath 
        #    and store in a list for beorun


class ProcessTasks:
    """ Process the given xmls (task) described in given filepath.
    """
    def __init__(self, pars={}):
        self.pars = pars

    def thread_task(self, line):
        """ Task which is threaded
        """
        signals_list = []
        gen = generators_importers.from_xml(signals_list)
        #gen.generate(xml_handle="/home/dstarr/scratch/Noisification/50nois_20epch_100need_0.050mtrc_frq17.9/generated_vosource/100018609_11.6262227104.xml")
        gen.generate(xml_handle=line)
        gen.sig.add_features_to_xml_string(gen.signals_list)

        str_i_1 = line.rfind('/')
        str_i_2 = line.rfind('/', 0, str_i_1)
        out_fpath = "%s/featured_vosource/%s" % (line[:str_i_2], line[str_i_1+1:])
        #gen.sig.write_xml(out_xml_fpath="/home/dstarr/scratch/Noisification/50nois_20epch_100need_0.050mtrc_frq17.9/featured_vosource/100018609_11.6262227104.xml")
        gen.sig.write_xml(out_xml_fpath=out_fpath)


    def main(self):
        """
        """
        import time
        import datetime
        import threading
        import copy
        #import socket
        #print socket.gethostname()


        fp = open(self.pars['task_fpath'])
        lines = fp.readlines()
        fp.close()

        # TODO:
        # I start 10 threads
        # I want to have each thread with a start datetime.
        #  - I sleep(1)
        #  - I then check for sources with isalive()
        #      - False: I join()  & increment number of tasks_to_queue + 1
        #      - True:  I check that dtime.now < dtime + 1 minute.
        #              - if too old, I .join(0.1)
        #              - otherwise, pass.

        max_seconds_thread_lifetime = 180
        n_tasks_to_thread = 1
        running_threads = []

        while ((len(lines) > 0) or 
               ((len(lines) == 0) and (len(running_threads) > 0))):
            while (len(lines) > 0) and ((len(running_threads) < n_tasks_to_thread)):
                # add some running threads
                line_raw = lines.pop()
                line = line_raw.strip()
                t = threading.Thread(target=self.thread_task, args=[copy.copy(line)])
                t.start()
                now = datetime.datetime.utcnow()
                #print ">>>>>>>>>", now, "tasked:", line
                running_threads.append((now,t))
            time.sleep(3)
            i_remove_list = []
            for i,(dtime,t) in enumerate(running_threads):
                if not t.isAlive():
                    i_remove_list.append(i)
                    t.join(0.01)
                else:
                    if dtime < (datetime.datetime.utcnow() - \
                                 datetime.timedelta(seconds=max_seconds_thread_lifetime)):
                        i_remove_list.append(i)
                        #print "################", datetime.datetime.utcnow()
                        t.join(0.01) # I force a join in 0.1 seconds, regardless
            i_remove_list.sort(reverse=True)
            for i in i_remove_list:
                running_threads.pop(i)
        #print "DONE", datetime.datetime.utcnow()

if __name__ == '__main__':

    pars = {'task_fpath':sys.argv[1]}
    pt = ProcessTasks(pars=pars)
    pt.main()
