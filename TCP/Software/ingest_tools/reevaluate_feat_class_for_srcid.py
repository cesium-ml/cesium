#!/usr/bin/env python 
"""
   v0.1 Go through various "interesting" source resources and re-evaluate epochs, features. classes

   Source resources include:
     - ptf_09xxx associated sources in source_test_db.caltech_classif_summary
     - list of high nobjs sources, which actually have < 2 epochs associated with them.
"""
import os, sys
import reevaluate_feat_class


if __name__ == '__main__':

    src_id = int(sys.argv[1])

    reeval_fc = reevaluate_feat_class.Reevaluate_Feat_Class()
    reeval_fc.reevaluate_for_srcid(src_id=src_id)
