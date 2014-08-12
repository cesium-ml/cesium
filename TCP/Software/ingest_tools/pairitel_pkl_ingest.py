#!/usr/bin/env python 
""" pairitel_pkl_ingest.py

Used to ingest all pairitel pkl files.
"""
import os, sys
import threading
import time

pars = {\
    't_sleep':0.2,
    'number_threads':20,
    'scratch_dirpath':'/home/pteluser/scratch/TCP_scratch',
    'pickle_fpath_list':[\
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2008a',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2007b',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2007a',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2006b',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2006a',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2005b',
        '/home/pteluser/scratch/TCP_tests/pkl_path_list.sem2005a'],
        }

class Pairitel_Pickle_ingest:
    def __init__(self, pars):
        self.pars = pars


    def pkl_ingest_task(self, pkl_fpath, scratch_dirpath):
        """
        # - scp pkl to local path: self.pars['scratch_dirpath']
        # - execute ingest_tools
        """
        if len(scratch_dirpath) < 10:
            return # sanity check before we mkdir/rmdir
        mkdir_str = "mkdir %s" % (scratch_dirpath)
        os.system(mkdir_str)
        scp_str = "scp -qc blowfish lyra.berkeley.edu:%s %s/" % \
                                                   (pkl_fpath, scratch_dirpath)
        os.system(scp_str)

        local_pkl_fpath = "%s/%s" % (scratch_dirpath, \
                                     pkl_fpath[pkl_fpath.rfind('/')+1:])
        exec_str = "/home/pteluser/src/TCP/Software/ingest_tools/ingest_tools.py do_pairitel_pkl_ingest=1 ptel_pkl_fpath=%s" % (local_pkl_fpath)
        #print exec_str
        os.system(exec_str)

        rmdir_str = "rm -Rf %s" % (scratch_dirpath)
        os.system(rmdir_str)


    def main(self):
        scratch_dir_count = 0
        running_threads = []
        for pkl_fpath_list_fpath in self.pars['pickle_fpath_list']:
            lines = open(pkl_fpath_list_fpath).readlines()
            for line in lines:
                line_elems = line.split()
                if len(line_elems) != 2:
                    continue
                pkl_fpath = line_elems[1]
                print pkl_fpath
                scratch_dirpath = "%s/pkl_ingest_%s" % (self.pars['scratch_dirpath'], scratch_dir_count)

                for thr in running_threads:
                    if not thr.isAlive():
                        running_threads.remove(thr)
                n_tasks_to_spawn = self.pars['number_threads'] - \
                                                           len(running_threads)
                #self.pkl_ingest_task(pkl_fpath, scratch_dirpath)
                while n_tasks_to_spawn < 1:
                    time.sleep(self.pars['t_sleep'])
                    for thr in running_threads:
                        if not thr.isAlive():
                            running_threads.remove(thr)
                    n_tasks_to_spawn = self.pars['number_threads'] - \
                                                           len(running_threads)
                t = threading.Thread(target=self.pkl_ingest_task,\
                                             args=[pkl_fpath, scratch_dirpath])
                t.start()
                running_threads.append(t)
                scratch_dir_count += 1
                

# TODO: write ingested pickle fpaths to log file.


if __name__ == '__main__':

    ppi = Pairitel_Pickle_ingest(pars)
    ppi.main()
