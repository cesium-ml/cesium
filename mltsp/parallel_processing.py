from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import open
from builtins import str
from builtins import dict
from builtins import *
from future import standard_library
standard_library.install_aliases()
# disco_test.py

from operator import itemgetter
#from rpy2.robjects.packages import importr
#from rpy2 import robjects
import shutil
import sklearn as skl
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib

import pickle
import sys
import os

import numpy as np
import datetime
import pytz
import tarfile
import glob
import tarfile
import uuid
import shutil

from . import cfg
from . import lc_tools
from . import disco_tools
from . import custom_exceptions

try:
    from disco.core import Job, result_iterator
    from disco.util import kvgroup
    DISCO_INSTALLED = True
except Exception as theError:
    DISCO_INSTALLED = False

from .TCP.Software.ingest_tools import generate_science_features


def map(fname_and_class, params):
    """Map procedure for use in Disco's map-reduce implementation.

    Generator used for feature generation process. Yields a 
    (file name, class name) tuple.

    This function is never directly called, but rather passed as a 
    parameter to the Disco `Job()` object's `run()` method.

    Parameters
    ----------
    fname_and_class : str
        Single line from a file containing file name and class name 
        separated by a comma.
    params : dict
        Dictionary of parameters for use in map-reduce process.

    Yields
    ------
    tuple of str
        Two-element tuple containing file name (str) and class name 
        (str).

    """
    fname, class_name = fname_and_class.strip("\n").strip().split(",")
    yield fname, class_name


def pred_map(fname, params):
    """Map procedure for use in Disco's map-reduce implementation.

    Generator used for featurizing prediction data. Yields a 
    (file name, empty string) tuple.

    This function is never directly called, but rather passed as a 
    parameter to the Disco `Job()` object's `run()` method.

    Parameters
    ----------
    fname : str
        Single line from a file containing file name and a placeholder  
        separated by a comma.
    params : dict
        Dictionary of parameters for use in map-reduce process.

    Yields
    ------
    tuple of str
        Two-element tuple containing file name (str) and class name 
        (str).

    """
    fname, junk = fname.strip("\n").strip().split(",")
    yield fname, junk


def pred_featurize_reduce(iter, params):
    """Generate features as reduce step in Disco's map-reduce.

    Generator. Implementation of reduce stage in map-reduce process, 
    for model prediction feature generation of time series data. 

    This function is never directly called, but rather passed as a 
    parameter to the Disco `Job()` object's `run()` method.

    Parameters
    ----------
    iter : iterable
        Iterable of tuples each containing the file name of a time 
        series data file to be used for featurization and an unused 
        placeholder string. 
    params : dict
        Dictionary of parameters for use in map-reduce process.

    Yields
    ------
    tuple
        A two-element tuple containing the file name of the 
        time series data set as its first element, and a two-element 
        list containing the extracted features (dict) and the original 
        time series data (list of lists) as its the second element. 

    """
    from copy import deepcopy
    featset_key = params['featset_key']
    sep = params['sep']
    custom_features_script = params['custom_features_script']
    meta_features = params['meta_features']
    
    import sys, os
    from disco.util import kvgroup
    import uuid
    import os
    import sys
    from . import cfg
    from . import custom_exceptions
    from .TCP.Software.ingest_tools import generate_science_features
    from . import lc_tools
    from . import custom_feature_tools as cft
    
    if generate_science_features.currently_running_in_docker_container():
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
        tcp_ingest_tools_path = "/home/mltsp/mltsp/TCP/Software/ingest_tools/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER
        tcp_ingest_tools_path = cfg.TCP_INGEST_TOOLS_PATH
    
    for fname,junk in kvgroup(sorted(iter)):
        if os.path.isfile(fname):
            f = open(fname)
            fpath = fname
        elif os.path.isfile(os.path.join(params["tmp_dir_path"], fname)):
            f = open(os.path.join(params["tmp_dir_path"], fname))
            fpath = os.path.join(params["tmp_dir_path"], fname)
        elif os.path.isfile(
                os.path.join(os.path.join(uploads_folder, "unzipped"), fname)):
            f = open(os.path.join(
                os.path.join(uploads_folder, "unzipped"), fname))
            fpath = os.path.join(
                os.path.join(uploads_folder, "unzipped"), fname)
        else:
            print((fname if uploads_folder in fname else 
                os.path.join(uploads_folder,fname)) + " is not a file...")
            if (os.path.exists(os.path.join(uploads_folder, fname)) or
                    os.path.exists(fname)):
                print("But it does exist on the disk.")
            else:
                print("and in fact it doesn't even exist.")
            continue
        
        lines=f.readlines()
        f.close()
        ts_data = []
        for i in range(len(lines)):
            ts_data.append(lines[i].strip("\n").strip().split(sep))
            if len(ts_data[i]) < len(lines[i].strip("\n").strip().split(",")):
                ts_data[i] = lines[i].strip("\n").strip().split(",")
            if len(ts_data[i]) < len(lines[i].strip("\n").strip().split(" ")):
                ts_data[i] = lines[i].strip("\n").strip().split(" ")
            if len(ts_data[i]) < len(lines[i].strip("\n").strip().split("\t")):
                ts_data[i] = lines[i].strip("\n").strip().split("\t")
            
            for j in range(len(ts_data[i])):
                ts_data[i][j] = float(ts_data[i][j])
                
            if len(ts_data[i]) == 2: # no error column
                ts_data[i].append(1.0) # make all errors 1.0
            elif len(ts_data[i]) in (0, 1):
                raise custom_exceptions.DataFormatError(
                    "Incomplete or improperly formatted time series "
                    "data file provided.")
            elif len(ts_data[i]) > 3:
                ts_data[i] = ts_data[i][:3] 
            
        del lines
        f = open(os.path.join(features_folder,"%s_features.csv" % featset_key))
        features_in_model = f.readline().strip().split(',')
        f.close()
        
        features_to_use = features_in_model
        
        ## generate features:
        if len(list(set(features_to_use) & set(cfg.features_list))) > 0:
            timeseries_features = lc_tools.generate_timeseries_features(
                deepcopy(ts_data), sep=sep, ts_data_passed_directly=True)
        else:
            timeseries_features = {}
        if (len(list(set(features_to_use) &
                set(cfg.features_list_science))) > 0):
            science_features = generate_science_features.generate(
                ts_data=deepcopy(ts_data))
        else:
            science_features = {}
        if custom_features_script not in ("None", None, False, "False"):
            custom_features = cft.generate_custom_features(
                custom_script_path=custom_features_script,
                path_to_csv=None, 
                features_already_known=dict(
                    list(timeseries_features.items()) + list(science_features.items()) + 
                    list(meta_features.items())),
                ts_data=deepcopy(ts_data))
            if (type(custom_features) == list and 
                len(custom_features) == 1):
                    custom_features = custom_features[0]
        else:
            custom_features = {}
        
        all_features = dict(
            list(timeseries_features.items()) + list(science_features.items()) + 
            list(custom_features.items()) + list(meta_features.items()))
        
        os.remove(fpath)
        
        yield fname, [all_features, ts_data]


def featurize_reduce(iter, params):
    """Generate features as reduce step in Disco's map-reduce.
    
    Generator. Implementation of reduce stage in map-reduce process, 
    for model prediction feature generation of time series data. 
    
    This function is never directly called, but rather passed as a 
    parameter to the Disco `Job()` object's `run()` method.
    
    Parameters
    ----------
    iter : iterable
        Iterable of tuples each containing the file name of a time 
        series data file to be used for featurization, and the 
        associated class or type name. 
    params : dict
        Dictionary of parameters for use in map-reduce process.
    
    Yields
    ------
    tuple
        A two-element tuple containing the file name of the time 
        series data set, and dict of the extracted features.
    
    """
    from disco.util import kvgroup
    
    for fname,class_name in kvgroup(sorted(iter)):
        class_names = []
        for classname in class_name:
            class_names.append(classname)
        if len(class_names) == 1:
            class_name = str(class_names[0])
        elif len(class_names) == 0:
            print(("CLASS_NAMES: " + str(class_names) + "\n" + 
                   "CLASS_NAME: " + str(class_name)))
            yield "",""
        else:
            print(("CLASS_NAMES: " + str(class_names) + "\n" + 
                   "CLASS_NAME: " + str(class_name) + 
                   "  - Choosing first class name in list."))
            class_name = str(class_names[0])
        
        print("fname: " + fname + ", class_name: " + class_name)
        import os
        import sys
        from . import cfg
        from .TCP.Software.ingest_tools import generate_science_features

        if generate_science_features.currently_running_in_docker_container():
            features_folder = "/Data/features/"
            models_folder = "/Data/models/"
            uploads_folder = "/Data/flask_uploads/"
            tcp_ingest_tools_path = "/home/mltsp/mltsp/TCP/Software/ingest_tools/"
        else:
            features_folder = cfg.FEATURES_FOLDER
            models_folder = cfg.MODELS_FOLDER
            uploads_folder = cfg.UPLOAD_FOLDER
            tcp_ingest_tools_path = cfg.TCP_INGEST_TOOLS_PATH

        from . import lc_tools
        from . import custom_feature_tools as cft

        short_fname = fname.split("/")[-1].replace(
            ("."+fname.split(".")[-1] if "." in fname.split("/")[-1] else ""),
            "")
        path_to_csv = os.path.join(
            uploads_folder, os.path.join("unzipped",fname))
        all_features = {}
        print("path_to_csv: " + path_to_csv)
        if os.path.isfile(path_to_csv):
            print("Extracting features for " + fname)

            ## generate features:
            if (len(list(set(params['features_to_use']) & 
                    set(cfg.features_list))) > 0):
                timeseries_features = lc_tools.generate_timeseries_features(
                    path_to_csv,classname=class_name,sep=',')
            else:
                timeseries_features = {}
            if len(list(set(params['features_to_use']) &
                        set(cfg.features_list_science))) > 0:
                science_features = generate_science_features.generate(
                    path_to_csv=path_to_csv)
            else:
                science_features = {}
            if params['custom_script_path']:
                custom_features = cft.generate_custom_features(
                    custom_script_path=params['custom_script_path'],
                    path_to_csv=path_to_csv,
                    features_already_known=dict(
                        list(timeseries_features.items()) +
                        list(science_features.items()) +
                        (list(params['meta_features'][fname].items()) if
                         fname in params['meta_features'] else list({}.items()))))
                if (type(custom_features) == list and 
                    len(custom_features) == 1):
                        custom_features = custom_features[0]
            else:
                custom_features = {}
            
            all_features = dict(
                list(timeseries_features.items()) + list(science_features.items()) +
                list(custom_features.items()) + [("class",class_name)])
        
        else:
            print(fname + " is not a file.")
            yield "", ""
        
        yield short_fname, all_features


def process_featurization_with_disco(input_list,params,partitions=4):
    """Featurize time-series data in parallel as a Disco job. 
    
    Called from within the `featurize_in_parallel` function.
    
    Parameters
    ----------
    input_list : str
        Path to file listing the file name and class name 
        (comma-separated) for each individual time series data file, 
        one per line.
    params : dict
        Dictionary of parameters to be passed to each map & reduce 
        function.
    partitions : int, optional
        Number of nodes/partitions in system. Defaults to 4.
    
    Returns
    -------
    iterator
        disco.core.result_iterator(), an interator of two-element 
        tuples, each containing the file name of the original time 
        series data file, and a dictionary of the associated features 
        generated.
    
    """
    from disco.core import Job, result_iterator
    job = Job().run(input=input_list,
                    map=map,
                    partitions=partitions,
                    reduce=featurize_reduce,
                    params=params)
    
    result = result_iterator(job.wait(show=True))
    return result


def process_prediction_data_featurization_with_disco(
    input_list, params, partitions=4):
    """Featurize time-series data in parallel as a Disco job.
    
    Called from within the `featurize_prediction_data_in_parallel` 
    function.
    
    Parameters
    ----------
    input_list : str
        Path to two-column CSV file listing the file name and an unused 
        placeholder string (comma-separated) for each individual time 
        series data file, one per line.
    params : dict
        Dictionary of parameters to be passed to each map & reduce 
        function.
    partitions : int, optional
        Number of nodes/partitions in system. Defaults to 4.
    
    Returns
    -------
    iterator
        disco.core.result_iterator(), an interator of two-element 
        tuples, each containing the file name of the original time 
        series data file, and a dictionary of the associated features 
        generated.
    
    """
    from disco.core import Job, result_iterator
    job = Job().run(input=input_list,
                    map=pred_map,
                    partitions=partitions,
                    reduce=pred_featurize_reduce,
                    params=params)
    
    result = result_iterator(job.wait(show=True))
    return result


def featurize_prediction_data_in_parallel(
    newpred_file_path, featset_key, sep=',', 
    custom_features_script=None, meta_features={}, 
    tmp_dir_path=None):
    """Generate features using Disco's map-reduce framework.
    
    Utilizes Disco's map-reduce framework to generate features on 
    multiple time series data files in parallel. The generated 
    features are returned, along with the time series data, in a 
    dict (with file names as keys). 
    
    Parameters
    ----------
    newpred_file_path : str
        Path to the zip file containing time series data files to be 
        featurized.
    featset_key : str
        RethinkDB key of the feature set associated with the model to 
        be used in prediction.
    sep : str, optional
        Delimiting character in time series data files. Defaults to ",".
    custom_features_script : str, optional
        Path to custom features script to be used in feature 
        generation. Defaults to None.
    meta_features : dict
        Dictionary of associated meta features. Defaults to an empty 
        dict.
    tmp_dir_path : str, optional
        Path to temporary files directory, in which any temporary files 
        will be created. Defaults to None, in which case temporary 
        files are created in working directory, though they are later 
        removed.
    
    Returns
    -------
    dict
        Dictionary whose keys are the file names of the original time-
        series data and keys are dictionaries containing a dictionary 
        of the features generated and a list of the time-series data.
    
    """
    #print "FEATURIZE_PRED_DATA_IN_PARALLEL: newpred_file_path =", \
    #      newpred_file_path
    the_tarfile = tarfile.open(newpred_file_path)
    the_tarfile.extractall(path=tmp_dir_path)
    all_fnames = the_tarfile.getnames()
    #print "ALL_FNAMES:", all_fnames
    
    big_features_and_tsdata_dict = {}
    
    params={"featset_key": featset_key, "sep": sep, 
            "custom_features_script": custom_features_script,
            "meta_features": meta_features,
            "tmp_dir_path": tmp_dir_path}
    
    with open("/tmp/%s_disco_tmp.txt"%str(uuid.uuid4()),"w") as f:
        for fname in all_fnames:
            f.write(fname+",unknown\n")
    
    disco_iterator = process_prediction_data_featurization_with_disco(
        input_list=[f.name],params=params,partitions=4)
    
    for k,v in disco_iterator:
        fname = k
        features_dict, ts_data = v
        if fname != "":
            big_features_and_tsdata_dict[fname] = {
                "features_dict": features_dict, "ts_data": ts_data}
    
    print("Feature generation complete.")
    os.remove(f.name)
    return big_features_and_tsdata_dict


def featurize_in_parallel(
    headerfile_path, zipfile_path, features_to_use=[], 
    is_test=False, custom_script_path=None, meta_features={}):
    """Generate features using Disco's map-reduce framework.
    
    Utilizes Disco's map-reduce framework to generate features on 
    multiple time series data files in parallel. The generated 
    features are returned, along with the time series data, in a 
    dict (with file names as keys). 
    
    Parameters
    ----------
    headerfile_path : str
        Path to header file containing file names, class names, and 
        metadata.
    zipfile_path : str
        Path to the tarball of individual time series files to be used 
        for feature generation.
    features_to_use : list, optional
        List of feature names to be generated. Default is an empty list,
        which results in all available features being used.
    is_test : bool, optional
        Boolean indicating whether to do a test run of only the first 
        five time-series files. Defaults to False.
    custom_script_path : str, optional
        Path to Python script containing methods for the generation of 
        any custom features.
    meta_features : dict, optional
        Dictionary of associated meta features, defaults to an empty 
        dict.
    
    Returns
    -------
    dict
        Dictionary whose keys are the file names of the original time-
        series data and keys are dictionaries containing a dictionary 
        of the features generated and a list of the time-series data.
    
    """
    all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
    
    if generate_science_features.currently_running_in_docker_container():
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
        tcp_ingest_tools_path = "/home/mltsp/mltsp/TCP/Software/ingest_tools/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER
        tcp_ingest_tools_path = cfg.TCP_INGEST_TOOLS_PATH
    
    if len(features_to_use) == 0:
        features_to_use = all_features_list
    
    headerfile = open(headerfile_path,'r')
    fname_class_dict = {}
    objects = []
    line_no = 0
    for line in headerfile:
        if (len(line)>1 and line[0] not in ["#","\n"] and 
                line_no > 0 and not line.isspace()):
            if len(line.split(',')) >= 2:
                fname,class_name = line.strip('\n').split(',')[:2]
                fname_class_dict[fname] = class_name
        line_no += 1
    headerfile.close()
    
    zipfile = tarfile.open(zipfile_path)
    zipfile.extractall(path=os.path.join(uploads_folder,"unzipped"))
    all_fnames = zipfile.getnames()
    num_objs = len(fname_class_dict)
    zipfile_name = zipfile_path.split("/")[-1]
    
    count=0
    print("Generating science features...")
    
    fname_class_list = list(fname_class_dict.items())
    input_fname_list = all_fnames
    longfname_class_list = []
    if is_test:
        all_fnames = all_fnames[:4]
    for i in range(len(all_fnames)):
        short_fname = all_fnames[i].\
            replace("."+all_fnames[i].split(".")[-1],"").split("/")[-1].\
            replace("."+all_fnames[i].split(".")[-1],"").strip()
        if short_fname in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i],fname_class_dict[short_fname]])
        elif all_fnames[i] in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i],fname_class_dict[all_fnames[i]]])
    with open("/tmp/%s_disco_tmp.txt"%str(uuid.uuid4()),"w") as f:
        for fname_classname in longfname_class_list:
            f.write(",".join(fname_classname)+"\n")
    
    params = {}
    params['fname_class_dict'] = fname_class_dict
    params['features_to_use'] = features_to_use
    params['meta_features'] = meta_features
    params['custom_script_path'] = custom_script_path
    
    disco_results = process_featurization_with_disco(
        input_list=[f.name],params=params)
    
    fname_features_dict = {}
    for k,v in disco_results:
        fname_features_dict[k] = v
    
    os.remove(f.name)
    print("Done generating features.")
    
    return fname_features_dict


## the test version:
def featurize_in_parallel_newtest(
    headerfile_path, zipfile_path, features_to_use=[], is_test=False, 
    custom_script_path=None, meta_features={}):
    """Generate features using Disco's map-reduce framework.
    
    Utilizes Disco's map-reduce framework to generate features on 
    multiple time series data files in parallel. The generated 
    features are returned, along with the time series data, in a 
    dict (with file names as keys). 
    
    Test function.
    
    Parameters
    ----------
    headerfile_path : str
        Path to header file containing file names, class names, and 
        metadata.
    zipfile_path : str
        Path to the tarball of individual time series files to be used 
        for feature generation.
    features_to_use : list, optional
        List of feature names to be generated. Default is an empty list,
        which results in all available features being used.
    is_test : bool, optional
        Boolean indicating whether to do a test run of only the first 
        five time-series files. Defaults to False.
    custom_script_path : str, optional
        Path to Python script containing methods for the generation of 
        any custom features.
    meta_features : dict, optional
        Dictionary of associated meta features, defaults to an empty 
        dict.
    
    Returns
    -------
    dict
        Dictionary whose keys are the file names of the original time-
        series data and keys are dictionaries containing a dictionary 
        of the features generated and a list of the time-series data.
    
    """
    all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
    
    if generate_science_features.currently_running_in_docker_container():
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
        tcp_ingest_tools_path = "/home/mltsp/mltsp/TCP/Software/ingest_tools/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER
        tcp_ingest_tools_path = cfg.TCP_INGEST_TOOLS_PATH
    
    if len(features_to_use) == 0:
        features_to_use = all_features_list
    
    headerfile = open(headerfile_path,'r')
    fname_class_dict = {}
    objects = []
    line_no = 0
    for line in headerfile:
        if (len(line)>1 and line[0] not in ["#","\n"] and 
                line_no > 0 and not line.isspace()):
            if len(line.split(',')) >= 2:
                fname,class_name = line.strip('\n').split(',')[:2]
                fname_class_dict[fname] = class_name
        line_no += 1
    headerfile.close()
    
    zipfile = tarfile.open(zipfile_path)
    zipfile.extractall(path=os.path.join(uploads_folder,"unzipped"))
    all_fnames = zipfile.getnames()
    num_objs = len(fname_class_dict)
    zipfile_name = zipfile_path.split("/")[-1]
    
    count=0
    print("Generating science features...")
    
    
    from disco.core import DDFS
    # push to ddfs
    print("Pushing all files to DDFS...")
    
    
    
    
    print("Done pushing files to DDFS.")
    
    # pass tags (or urls?) as input_list
    
    
    """
    fname_class_list = list(fname_class_dict.iteritems())
    input_fname_list = all_fnames
    longfname_class_list = []
    if is_test:
        all_fnames = all_fnames[:4]
    for i in range(len(all_fnames)):
        short_fname = all_fnames[i].replace("."+all_fnames[i].\
            split(".")[-1],"").split("/")[-1].replace("."+all_fnames[i].\
            split(".")[-1],"").strip()
        if short_fname in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i],fname_class_dict[short_fname]])
        elif all_fnames[i] in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i],fname_class_dict[all_fnames[i]]])
    with open("/tmp/disco_inputfile.txt","w") as f:
        for fname_classname in longfname_class_list:
            f.write(",".join(fname_classname)+"\n")
    """
    
    params = {}
    params['fname_class_dict'] = fname_class_dict
    params['features_to_use'] = features_to_use
    params['meta_features'] = meta_features
    params['custom_script_path'] = custom_script_path
    
    disco_results = process_featurization_with_disco(
        input_list=[f.name], params=params)
    
    fname_features_dict = {}
    for k,v in disco_results:
        fname_features_dict[k] = v
    
    os.remove(f.name)
    print("Done.")
    
    return fname_features_dict
    
