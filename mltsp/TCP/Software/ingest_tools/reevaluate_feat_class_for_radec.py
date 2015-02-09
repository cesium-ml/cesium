#!/usr/bin/env python 
"""
   v0.1 given an ra,dec this will looking at all epochs in ptf_events table within
       that region and re-evaluate or add new sources using these.
     - then features will be generated and classifications are made
       and these are stored in the normal TABLES.

Call using:

./reevaluate_feat_class_for_radec.py 316.7523 -0.6646

"""
import os, sys
import reevaluate_feat_class


if __name__ == '__main__':

    ra = float(sys.argv[1])
    dec = float(sys.argv[2])

    reeval_fc = reevaluate_feat_class.Reevaluate_Feat_Class()
    reeval_fc.reevaluate_for_radec(ra=ra, dec=dec)
