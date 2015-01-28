#!/usr/bin/env python
"""
* asas_catalog.R in Python
** input parameters:
     - deboss arff fpath
     - asas arff fpath
     - features to exclude
** output: 
     - asas_randomForest.Rdat fpath
     - classifier effeciency metrics
** I want to call the full AL R script, but be able to 
    modify some bits.
*** wrapping the R code in a python string is less ideal
     - but it could just be for a specific version of the AL/MACC code
"""
import os, sys
from rpy2.robjects.packages import importr
from rpy2 import robjects



if __name__ == '__main__':
    # TODO: do some popen of the asas_catalog.R script
    # source a file which initializes variables
    # source asas_catalog.R

    pars = {'root_dirpath':"/Data/dstarr/src/ASASCatalog/",
        'deboss_srcids_arff_fpath':"/Data/dstarr/src/ASASCatalog/data/debosscher_feats_20120305.arff",
        'deboss_train_arff_fpath':"/Data/dstarr/src/ASASCatalog/data/train_20120327_10ntree_5mtry.arff",
        'asas_test_arff_fpath':"/Data/dstarr/src/ASASCatalog/data/test_20120327_10ntree_5mtry.arff",
        'rf_clfr_fpath':"/home/dstarr/scratch/macc_wrapper_rfclfr.rdat",
            }
    
    ### Initialize:
    r_str = '''
set.seed(1)
source("{root_dirpath}R/utils_classify.R")
source("{root_dirpath}R/class_cv.R")
source("{root_dirpath}R/missForest.R")
source("{root_dirpath}R/utils_PTF.R")
source("{root_dirpath}R/runJunkClass.R")
library(randomForest)
library(nnet)
library(foreign)
    '''.format(root_dirpath=pars['root_dirpath'])
    robjects.r(r_str)
    
    r_str = '''
path = "{root_dirpath}"
asas_test_arff_fpath = "{asas_test_arff_fpath}"
rf_clfr_fpath="{rf_clfr_fpath}"

# Load Debosscher data
debdat=read.arff(file="{deboss_srcids_arff_fpath}")
ID.use = debdat$source_id
debdat=read.arff(file="{deboss_train_arff_fpath}")
use = which(debdat$source_id {isin} ID.use)
debdat = debdat[use,]

ID = debdat$source_id
debdat$class = paste(debdat$class)
deb.reclassify = read.table(paste(path,"data/reclassified_debosscher_eclipsing.dat",sep=""))
debdat$class[which(ID {isin} deb.reclassify[,1])] = deb.reclassify[,2]

# straighten out T Tauri subclasses (AAM visual reclassifications)
ttau.cl = c(163375,163434,163445,163480,163585,163762,163907,164145,164355)
debdat$class[debdat$source_id {isin} ttau.cl] = 201
ttau.wl = c(163981,164277)
debdat$class[debdat$source_id {isin} ttau.wl] = 202

class.deb = class.debos(debdat$class)

# re-label the source that Nat found to be wrong
class.deb[ID==164154] = "y. W Ursae Maj." 

p = dim(debdat)[2]
feat.debos = data.frame(debdat)[,-c(1,p)] # Deb features
    '''.format(isin="%in%",
               root_dirpath=pars['root_dirpath'],
               rf_clfr_fpath=pars['rf_clfr_fpath'],
               deboss_srcids_arff_fpath=pars['deboss_srcids_arff_fpath'],
               deboss_train_arff_fpath=pars['deboss_train_arff_fpath'],
               asas_test_arff_fpath=pars['asas_test_arff_fpath'])
    robjects.r(r_str)

    ### Remove useless features from the training data:
    r_str = '''
rem = c(which(substr(names(feat.debos),1,7) == "eclpoly"))
rem = c(rem,which(names(feat.debos)=="color_bv_extinction"))
rem = c(rem,which(names(feat.debos)=="color_diff_bj"))
rem = c(rem,which(names(feat.debos)=="color_diff_hk"))
rem = c(rem,which(names(feat.debos)=="color_diff_jh"))
rem = c(rem,which(names(feat.debos)=="color_diff_rj"))
rem = c(rem,which(names(feat.debos)=="color_diff_vj"))
rem = c(rem,which(names(feat.debos)=="n_points"))
rem = c(rem,which(names(feat.debos)=="freq_rrd"))
rem = c(rem,which(substr(names(feat.debos),17,27)=="rel_phase_0"))
feat.debos = feat.debos[,-rem]
    '''.format()
    robjects.r(r_str)
    #import pdb; pdb.set_trace()
    #print

    ### NOTE: must use the local version of asas_catalog.R:
    r_str = 'source("asas_catalog.R")'
    #r_str = 'source("{root_dirpath}R/asas_catalog.R")'.format(root_dirpath=pars['root_dirpath'])
    robjects.r(r_str)
    #import pdb; pdb.set_trace()
    #print


    ### TODO: ensure .R files are coming from current path

    ### TODO: retrieve resulting metrics
