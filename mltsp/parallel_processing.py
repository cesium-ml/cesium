from __future__ import print_function
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
import ntpath

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


def currently_running_in_docker_container():
    import subprocess
    proc = subprocess.Popen(["cat","/proc/1/cgroup"],stdout=subprocess.PIPE)
    output = proc.stdout.read()
    if "/docker/" in str(output):
        in_docker_container=True
    else:
        in_docker_container=False
    return in_docker_container


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
    # This should not be necessary when mltsp is installed on the system
    # as a proper package:
    sys.path.append("/home/arien/projects/mltsp")# #TEMP#
    from mltsp import cfg
    from mltsp import predict_class as pred
    from mltsp import custom_exceptions
    import mltsp

    if mltsp.parallel_processing.currently_running_in_docker_container():
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER

    for fname, junk in kvgroup(sorted(iter)):
        if os.path.isfile(fname):
            fpath = fname
        elif os.path.isfile(os.path.join(params["tmp_dir_path"], fname)):
            fpath = os.path.join(params["tmp_dir_path"], fname)
        elif os.path.isfile(
                os.path.join(os.path.join(uploads_folder, "unzipped"), fname)):
            fpath = os.path.join(
                os.path.join(uploads_folder, "unzipped"), fname)
        else:
            print((fname if uploads_folder in fname else
                os.path.join(uploads_folder, fname)) + " is not a file...")
            if (os.path.exists(os.path.join(uploads_folder, fname)) or
                    os.path.exists(fname)):
                print("But it does exist on the disk.")
            else:
                print("and in fact it doesn't even exist.")
            continue

        features_to_use = pred.determine_feats_used(featset_key,
                                                    features_folder)
        big_feats_and_tsdata_dict = pred.featurize_single(
            fpath, features_to_use, uploads_folder, custom_features_script,
            meta_features)

        os.remove(fpath)
        short_fname = ntpath.basename(fpath)
        all_features = big_feats_and_tsdata_dict[short_fname]["features_dict"]
        ts_data = big_feats_and_tsdata_dict[short_fname]["ts_data"]
        yield short_fname, [all_features, ts_data]


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
        tmp_dir_path="/tmp"):
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

    the_tarfile = tarfile.open(newpred_file_path)
    the_tarfile.extractall(path=tmp_dir_path)
    all_fnames = the_tarfile.getnames()

    big_features_and_tsdata_dict = {}

    params = {"featset_key": featset_key, "sep": sep,
            "custom_features_script": custom_features_script,
            "meta_features": meta_features,
            "tmp_dir_path": tmp_dir_path}

    with open("/tmp/%s_disco_tmp.txt" % str(uuid.uuid4()), "w") as f:
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

    for fname, class_name in kvgroup(sorted(iter)):
        class_names = []
        for classname in class_name:
            class_names.append(classname)
        if len(class_names) == 1:
            class_name = str(class_names[0])
        elif len(class_names) == 0:
            print(("CLASS_NAMES: " + str(class_names) + "\n" +
                   "CLASS_NAME: " + str(class_name)))
            yield "", ""
        else:
            print(("CLASS_NAMES: " + str(class_names) + "\n" +
                   "CLASS_NAME: " + str(class_name) +
                   "  - Choosing first class name in list."))
            class_name = str(class_names[0])

        print("fname: " + fname + ", class_name: " + class_name)
        import os
        import sys
        # This should not be necessary when mltsp is installed on the system
        # as a proper package:
        sys.path.append("/home/arien/projects/mltsp")# #TEMP#
        from mltsp import cfg
        from mltsp import featurize
        import mltsp

        if mltsp.parallel_processing.currently_running_in_docker_container():
            features_folder = "/Data/features/"
            models_folder = "/Data/models/"
            uploads_folder = "/Data/flask_uploads/"
        else:
            features_folder = cfg.FEATURES_FOLDER
            models_folder = cfg.MODELS_FOLDER
            uploads_folder = cfg.UPLOAD_FOLDER

        short_fname = os.path.splitext(ntpath.basename(fname))[0]
        path_to_csv = os.path.join(
            uploads_folder, os.path.join("unzipped", fname))
        if os.path.isfile(path_to_csv):
            print("Extracting features for " + fname)
            all_features = featurize.featurize_tsdata_object(
                path_to_csv, short_fname, params['custom_script_path'],
                params['fname_class_dict'], params['features_to_use'])
        else:
            print(fname + " is not a file.")
            yield "", ""
        all_features["class"] = class_name

        yield short_fname, all_features


def process_featurization_with_disco(input_list, params, partitions=4):
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

    if currently_running_in_docker_container():
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER

    if len(features_to_use) == 0:
        features_to_use = all_features_list

    fname_class_dict = {}
    objects = []
    line_no = 0
    with open(headerfile_path) as headerfile:
        for line in headerfile:
            if (len(line) > 1 and line[0] not in ["#", "\n"] and
                line_no > 0 and not line.isspace()):
                if len(line.split(',')) >= 2:
                    fname, class_name = line.strip('\n').split(',')[:2]
                    fname_class_dict[fname] = class_name
            line_no += 1

    zipfile = tarfile.open(zipfile_path)
    zipfile.extractall(path=os.path.join(uploads_folder, "unzipped"))
    all_fnames = zipfile.getnames()
    num_objs = len(fname_class_dict)
    zipfile_name = ntpath.basename(zipfile_path)

    count=0
    print("Generating science features...")

    fname_class_list = list(fname_class_dict.items())
    input_fname_list = all_fnames
    longfname_class_list = []
    if is_test:
        all_fnames = all_fnames[:4]
    for i in range(len(all_fnames)):
        short_fname = os.path.splitext(ntpath.basename(all_fnames[i]))[0]
        if short_fname in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i], fname_class_dict[short_fname]])
        elif all_fnames[i] in fname_class_dict:
            longfname_class_list.append([
                all_fnames[i], fname_class_dict[all_fnames[i]]])
    with open("/tmp/%s_disco_tmp.txt" % str(uuid.uuid4()), "w") as f:
        for fname_classname in longfname_class_list:
            f.write(",".join(fname_classname) + "\n")

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
    print("Done generating features.")

    return fname_features_dict
