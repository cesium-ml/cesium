#!/usr/bin/env python
""" Generate a summary of metacost.results Weka output in Noisification/* dirs
"""

import sys, os
import glob


if __name__ == '__main__':


    os.chdir('/home/pteluser/scratch/Noisification')
    
    glob_paths = glob.glob("/home/pteluser/scratch/Noisification/*/metacost.results")
    for fpath in glob_paths:
        lines = open(fpath).readlines()
        i_1st_slash = fpath.rfind('/')
        i_2nd_slash = fpath.rfind('/',0,i_1st_slash)
        case_name = fpath[i_2nd_slash+1:i_1st_slash]
        passed_stratified = False
        percent = 0.
        for line in lines:
            if "=== Stratified cross-validation ===" in line:
                passed_stratified = True
            elif (passed_stratified and \
                  "Correctly Classified Instances" in line):
                percent = float(line[52:line.rfind('%')-1])
                break
        print "%0.2f %s" % (percent, case_name)
