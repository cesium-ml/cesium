#!/usr/bin/env python
""" scps noise trained weka .model files neede for classification
"""
from __future__ import print_function

import sys, os
import glob

client_defs = [ \
   {'name':'__local__',
    'hostname':'127.0.0.1',
    'furl_dirpath':'/home/pteluser/.ipython/security',
    'username':'pteluser',
    'ssh_port':22,
    'n_engines':10},
   {'name':'__worms2__',
    'hostname':'localhost',
    'furl_dirpath':'/home/starr/.ipython/security',
    'username':'starr',
    'ssh_port':32151,
    'n_engines':0},
   {'name':'__cch1__',
    'hostname':'localhost',
    'furl_dirpath':'/home/dstarr/.ipython/security',
    'username':'dstarr',
    'nice':19,
    'ssh_port':32161,
    'n_engines':1},
   ]

"""
   {'name':'__trans1__',
    'hostname':'192.168.1.45',
    'furl_dirpath':'/home/pteluser/.ipython/security',
    'username':'pteluser',
    'ssh_port':22,
    'n_engines':0},
   {'name':'__trans2__',
    'hostname':'192.168.1.55',
    'furl_dirpath':'/home/pteluser/.ipython/security',
    'username':'pteluser',
    'ssh_port':22,
    'n_engines':0},
   {'name':'__trans3__',
    'hostname':'192.168.1.65',
    'furl_dirpath':'/home/pteluser/.ipython/security',
    'username':'pteluser',
    'ssh_port':22,
    'n_engines':0},
   {'name':'__sgn02__',
    'hostname':'sgn02.nersc.gov',
    'furl_dirpath':'/global/homes/d/dstarr/datatran/.ipython/security',
    'username':'dstarr',
    'ssh_port':22,
    'n_engines':0},
"""

def send_to_other_nodes(glob_mask, dirnames, client_defs):
    """ send files on this computer to other node computers.
    """

    for client_def in client_defs:
        if client_def['name'] == '__local__':
            continue
        for dirname in dirnames:
            exec_str = "ssh -tp %d %s@%s mkdir scratch/Noisification/%s" % ( \
                client_def['ssh_port'],
                client_def['username'],
                client_def['hostname'],
                dirname)
            os.system(exec_str)

            exec_str = "scp -CP %d ~/scratch/Noisification/%s/*arff %s@%s:scratch/Noisification/%s/" % ( \
                client_def['ssh_port'],
                dirname,
                client_def['username'],
                client_def['hostname'],
                dirname)
            os.system(exec_str)

            exec_str = "scp -CP %d ~/scratch/Noisification/%s/*model %s@%s:scratch/Noisification/%s/" % ( \
                client_def['ssh_port'],
                dirname,
                client_def['username'],
                client_def['hostname'],
                dirname)
            os.system(exec_str)


def retrieve_from_other_node(glob_mask, dirnames, retrieve_host_dict):
    """ copy files to this node from other nodes.
    """
    # will do an scp to ~/scratch/Noisification/ files: scratch/Noisification/*glob_mask*/*arff  *model

    for dirname in dirnames:
        exec_str = "mkdir -p ~/scratch/Noisification/%s" % (dirname)
        os.system(exec_str)
        
        exec_str = "scp -CP %d %s@%s:scratch/Noisification/%s/{*arff,*model} ~/scratch/Noisification/%s/" % ( \
            retrieve_host_dict['ssh_port'],
            retrieve_host_dict['username'],
            retrieve_host_dict['hostname'],
            dirname,
            dirname)
        print(exec_str)
        os.system(exec_str)
    


if __name__ == '__main__':

    #glob_mask = sys.argv[1]  # eg: 50nois_*short1
    glob_mask = "50nois_*qk17.9"
    dirnames = glob.glob(glob_mask)

    #send_to_other_nodes(glob_mask, dirnames, client_defs)

    retrieve_host_dict =  \
                       {'name':'__cch1__',
                        'hostname':'localhost',
                        'furl_dirpath':'/home/dstarr/.ipython/security',
                        'username':'dstarr',
                        'nice':19,
                        'ssh_port':32161,
                        'n_engines':1}

    dirnames = ['20nois_19epch_040need_0.050mtrc_j48_17.9',
                '20nois_15epch_040need_0.050mtrc_j48_17.9',
                '20nois_11epch_040need_0.050mtrc_j48_17.9',
                '20nois_21epch_040need_0.050mtrc_j48_17.9',
                '20nois_25epch_040need_0.050mtrc_j48_17.9',
                '20nois_29epch_040need_0.050mtrc_j48_17.9',
                '20nois_17epch_040need_0.050mtrc_j48_17.9',
                '20nois_13epch_040need_0.050mtrc_j48_17.9',
                '20nois_20epch_040need_0.050mtrc_j48_17.9',
                '20nois_27epch_040need_0.050mtrc_j48_17.9',
                '20nois_23epch_040need_0.050mtrc_j48_17.9',
                '20nois_09epch_040need_0.050mtrc_j48_17.9',
                '20nois_10epch_040need_0.050mtrc_j48_17.9',
                '20nois_33epch_040need_0.050mtrc_j48_17.9']
    
    retrieve_from_other_node(glob_mask, dirnames, retrieve_host_dict)
