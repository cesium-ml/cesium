#!/usr/bin/env python 
"""
   v0.1 This retrieves TCP related data files, weka .models, etc... which
        are required to run as a TCP task client / ipengine client.
"""

import os, sys
import ingest_tools
ingest_tools_pars = ingest_tools.pars



if __name__ == '__main__':

    local_scratch_dirpath = os.path.expandvars(\
                                   '$HOME/scratch/Noisification/')

    os.system("mkdir -p %s" % (local_scratch_dirpath))


    for class_schema_name, class_dict in ingest_tools_pars[\
                         'class_schema_definition_dicts'].iteritems():
        if class_dict.has_key('weka_training_model_fpath'):
            class_dirpath = class_dict['weka_training_model_fpath'][: \
                                class_dict['weka_training_model_fpath'].rfind('/')]
            if not os.path.exists(class_dirpath):
                os.system("mkdir -p " + class_dirpath)

            fpath = class_dict['weka_training_model_fpath']
            sysindep_fpath = fpath[fpath.find("scratch"):]
            if not os.path.exists(fpath):
                scp_str = "scp -C pteluser@192.168.1.25:%s %s/" % (sysindep_fpath, class_dirpath)
                os.system(scp_str)

            fpath = class_dict['weka_training_arff_fpath']
            sysindep_fpath = fpath[fpath.find("scratch"):]
            if not os.path.exists(fpath):
                scp_str = "scp -C pteluser@192.168.1.25:%s %s/" % (sysindep_fpath, class_dirpath)
                os.system(scp_str)
