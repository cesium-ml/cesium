# predict_class.py

import sklearn as skl
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib

import logging
from operator import itemgetter
import cfg

import cPickle
import lc_tools
import sys
import os
import uuid
import shutil
import numpy as np
import datetime
import pytz
import tarfile
import glob
from copy import deepcopy
import custom_exceptions
sys.path.append(cfg.TCP_INGEST_TOOLS_PATH)

import generate_science_features
import custom_feature_tools as cft

try:
    from disco.core import Job, result_iterator
    from disco.util import kvgroup
    DISCO_INSTALLED = True
except Exception as theError:
    DISCO_INSTALLED = False

if DISCO_INSTALLED:
    import parallel_processing

n_epochs_list = [20,40,70,100,150,250,500,1000,10000,100000]

#sorted_survey_list = sorted(survey_list)


def predict(
    newpred_file_path, model_name, model_type, featset_key,
    sepr=',', n_cols_html_table=5, features_already_extracted=False, 
    custom_features_script=None, metadata_file_path=None, 
    in_docker_container=False):
    """Generate features from new TS data and perform model prediction.
    
    Generates features for new time series file, loads saved 
    classifier model, calculates class predictions with extracted 
    features, and returns a dictionary containing a list of class 
    prediction probabilities, a string containing HTML markup for a 
    table containing a list of the results, the time-series data itself 
    used to generate features, and a dictionary of the features 
    extracted. The respective dict keys of the above-mentioned values 
    are: "pred_results_list", "results_str", "ts_data", "features_dict".
    
    Parameters
    ----------
    newpred_file_path : str
        Path to time series data file to be used in prediction.
    model_name : str
        Name of the model to be used.
    model_type : str
        Type (abbreviation, e.g. "RF") of the model to be used.
    featset_key : str
        RethinkDB ID of the feature set used to create the 
        above-specified model.
    sepr : str, optional
        Delimiting character in time series data file. Default is comma 
        (",").
    n_cols_html_table : int, optional
        The number of highest-probability classes to include (one per 
        column) in the generated HTML table.
    features_already_extracted : dict, optional
        Dictionary of any features already extracted associated with 
        the time series data pointed to by `newpred_file_path`. 
        Defaults to False.
    custom_features_script : str, optional
        Path to custom features script to be used in feature 
        generation, defaults to None.
    metadata_file_path : str, optional
        Path to meta data file associated with provided time series 
        data. Defaults to None.
    
    Returns
    -------
    dict
        Returns dictionary whose keys are the file names of the 
        individual time-series data files used in prediction and whose 
        corresponding values are dictionaries with the following 
        key-value pairs:
            "results_str": String containing table listing results in 
                HTML markup.
            "ts_data": The original time-series data provided.
            "features_dict": A dictionary containing the generated 
                features.
            "pred_results_list": A list of lists, each containing one 
                of the most-probable classes and its probability.
    
    """
    print "predict_class - predict() called."
    if in_docker_container:
        features_folder = "/Data/features/"
        models_folder = "/Data/models/"
        uploads_folder = "/Data/flask_uploads/"
        path_to_project_directory = "/home/mltp/"
    else:
        features_folder = cfg.FEATURES_FOLDER
        models_folder = cfg.MODELS_FOLDER
        uploads_folder = cfg.UPLOAD_FOLDER
        path_to_project_directory = cfg.PROJECT_PATH
    if metadata_file_path is not None:
        meta_features = {}
        with open(metadata_file_path) as f:
            meta_feat_names = f.readline().strip().split(",")[1:]
            for line in f:
                if line != "\n" and len(line.split(",")) > 1:
                    els = line.strip().split(",")
                    fname = els[0]
                    meta_feats = els[1:]
                    for i in range(len(meta_feats)):
                        try:
                            meta_feats[i] = float(meta_feats[i])
                        except ValueError:
                            pass
                    meta_features[fname] = dict(
                        zip(meta_feat_names,meta_feats))
    else:
        meta_features = {}
    sep=sepr
    featset_name = model_name
    model_name = model_name.strip()
    all_features_list = cfg.features_list[:] + cfg.features_list_science[:]
    with open(os.path.join(
            features_folder,"%s_features.csv" % featset_key)) as f:
        features_in_model = f.readline().strip().split(',')
    features_to_use = features_in_model
    is_tarfile = tarfile.is_tarfile(newpred_file_path)
    
    big_features_and_tsdata_dict = {}
    
    if is_tarfile:
        tmp_dir_path = os.path.join(os.path.join(
            uploads_folder, "unzipped"), str(uuid.uuid4()))
        os.mkdir(tmp_dir_path)
        # disco may be installed in docker container, 
        # but it is not working yet, thus the "and not in_docker_container":
        if DISCO_INSTALLED and not in_docker_container:
            big_features_and_tsdata_dict = (
                parallel_processing.featurize_prediction_data_in_parallel(
                    newpred_file_path=newpred_file_path, 
                    featset_key=featset_key, sep=sep, 
                    custom_features_script=custom_features_script,
                    meta_features=meta_features, tmp_dir_path=tmp_dir_path))
            for fname in big_features_and_tsdata_dict.keys():
                if fname in meta_features:
                    big_features_and_tsdata_dict[fname]['features_dict'] = (
                        dict(big_features_and_tsdata_dict[fname]
                             ['features_dict'].items() 
                             + meta_features[fname].items()))
        else:
            
            the_tarfile = tarfile.open(newpred_file_path)
            all_fnames = the_tarfile.getnames()
            the_tarfile.extractall(path=tmp_dir_path)
            
            with open(os.path.join(
                    features_folder,"%s_features.csv" % featset_key)) as f:
                features_in_model = f.readline().strip().split(',')
            features_to_use = features_in_model
            for fname in all_fnames:
                if os.path.isfile(fname):
                    f = open(fname)
                elif os.path.isfile(os.path.join(tmp_dir_path, fname)):
                    f = open(os.path.join(tmp_dir_path, fname))
                else:
                    print fname + " is not a file..."
                    continue
                short_fname = fname.split("/")[-1]
                lines=f.readlines()
                ts_data = []
                f.close()
                for i in range(len(lines)):
                    if lines[i].strip() != "":
                        ts_data.append(lines[i].strip().split(sep))
                        if len(ts_data[i]) < len(lines[i]
                                .strip("\n").strip().split(",")):
                            ts_data[i] = (lines[i].strip("\n")
                                .strip().split(","))
                        if len(ts_data[i]) < len(lines[i].strip("\n")
                                .strip().split(" ")):
                            ts_data[i] = (lines[i].strip("\n")
                                .strip().split(" "))
                        if len(ts_data[i]) < len(lines[i]
                                .strip("\n").strip().split("\t")):
                            ts_data[i] = (lines[i].strip("\n")
                                .strip().split("\t"))
                        
                        for j in range(len(ts_data[i])):
                            ts_data[i][j] = float(ts_data[i][j])
                        
                        if len(ts_data[i]) == 2: # no error column
                            ts_data[i].append(1.0) # make all errors 1.0
                        elif len(ts_data[i]) in [0,1]:
                            raise custom_exceptions.DataFormatError(
                                "Incomplete or improperly formatted time "
                                "series data file provided.")
                        elif len(ts_data[i]) > 3:
                            ts_data[i] = ts_data[i][:3]
                del lines
                
                ## generate features:
                if len(list(set(features_to_use) & 
                    set(cfg.features_list))) > 0:
                    timeseries_features = (lc_tools
                        .generate_timeseries_features(
                            deepcopy(ts_data), sep=sepr, 
                            ts_data_passed_directly=True))
                else:
                    timeseries_features = {}
                if len(list(set(features_to_use) & 
                            set(cfg.features_list_science))) > 0:
                    science_features = generate_science_features.generate(
                        ts_data=deepcopy(ts_data))
                else:
                    science_features = {}
                if custom_features_script not in [None,"None","none",False]:
                    custom_features = cft.generate_custom_features(
                        custom_script_path=custom_features_script,
                        path_to_csv=None,
                        features_already_known=dict(
                            timeseries_features.items() +
                            science_features.items() + 
                            (meta_features[short_fname].items() if 
                             short_fname in meta_features else 
                             {}.items())),ts_data=deepcopy(ts_data))
                else:
                    custom_features = {}
            
                features_dict = dict(
                    timeseries_features.items() + science_features.items() + 
                    custom_features.items() + 
                    (meta_features[short_fname].items() if 
                     short_fname in meta_features else {}.items()))
                
                big_features_and_tsdata_dict[fname] = {
                    "features_dict":features_dict, "ts_data":ts_data}
        shutil.rmtree(tmp_dir_path, ignore_errors=True) 
        
    else:
        fname = newpred_file_path
        short_fname = fname.split("/")[-1]
        if os.path.isfile(fname):
            f = open(fname)
        elif os.path.isfile(os.path.join(uploads_folder, fname)):
            f = open(os.path.join(uploads_folder, fname))
        else:
            print fname + " is not a file..."
            return
        
        lines=f.readlines()
        f.close()
        ts_data = []
        for i in range(len(lines)):
            if lines[i].strip() != "":
                ts_data.append(lines[i].strip("\n").strip().split(sep))
                if len(ts_data[i]) < len(
                        lines[i].strip("\n").strip().split(",")):
                    ts_data[i] = lines[i].strip("\n").strip().split(",")
                if len(ts_data[i]) < len(
                        lines[i].strip("\n").strip().split(" ")):
                    ts_data[i] = lines[i].strip("\n").strip().split(" ")
                if len(ts_data[i]) < len(
                        lines[i].strip("\n").strip().split("\t")):
                    ts_data[i] = lines[i].strip("\n").strip().split("\t")
                
                for j in range(len(ts_data[i])):
                    ts_data[i][j] = float(ts_data[i][j])
                    
                if len(ts_data[i]) == 2: # no error column
                    ts_data[i].append(1.0) # make all errors 1.0
                elif len(ts_data[i]) in [0,1]:
                    raise custom_exceptions.DataFormatError(
                        "Incomplete or improperly formatted "
                        "time series data file provided.")
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
                deepcopy(ts_data),sep=sepr,ts_data_passed_directly=True)
        else:
            timeseries_features = {}
        if len(list(set(features_to_use) & 
                set(cfg.features_list_science))) > 0:
            science_features = generate_science_features.generate(
                ts_data=deepcopy(ts_data))
        else:
            science_features = {}
        if custom_features_script not in [None,"None","none",False]:
            custom_features = cft.generate_custom_features(
                custom_script_path=custom_features_script, path_to_csv=None,
                features_already_known=dict(
                    timeseries_features.items() + science_features.items() + 
                    (
                        meta_features[short_fname].items() if short_fname in 
                        meta_features else {}.items())),ts_data=ts_data)
        else:
            custom_features = {}
        features_dict = dict(
            timeseries_features.items() + science_features.items() + 
            custom_features.items() + 
            (
                meta_features[short_fname].items() if short_fname 
                in meta_features else {}.items()))
        big_features_and_tsdata_dict[fname] = {
            "features_dict":features_dict, "ts_data":ts_data}
    features_extracted = big_features_and_tsdata_dict[
        big_features_and_tsdata_dict.keys()[0]]["features_dict"].keys()
    results_dict = {}
    for fname, features_and_tsdata_dict in \
            big_features_and_tsdata_dict.iteritems():
        ts_data = features_and_tsdata_dict['ts_data']
        new_obj = features_and_tsdata_dict['features_dict']
        data_dict = {}
        features_dict = {}
        newFeatures = []
        for feat in sorted(features_extracted):
            if feat != 'class' and feat in new_obj and feat in features_to_use:
                try:
                    if type(new_obj[feat]) != type(None):
                        try:
                            newFeatures.append(float(new_obj[feat]))
                        except ValueError:
                            newFeatures.append(0.0)
                    else:
                        newFeatures.append(0.0)
                    features_dict[feat] = newFeatures[-1]
                except KeyError as theError:
                    print theError
                    pass
            else:
                pass
        #tsdata = ts_data
        has_err_col = True  # 1/29/14 - skipping the noerrs thing for now
        n_epochs = len(ts_data)
        xNew = np.array(newFeatures)
        modelnum = -99
        if has_err_col:
            
            modelnum="standard"
            try: # load model object:
                rfc_model = joblib.load(os.path.join(
                    models_folder,"%s_%s.pkl" % (featset_key,model_type)))
            except Exception as theError:
                return [
                    str(theError) + (
                        "<br>It looks like a model has yet to be built for "
                        "this project - after uploading your data and "
                        "generating features, build the classifier model "
                        "using the form under the 'Build Model' tab."), 
                    "Using model %s_%s.pkl" % (featset_key,model_type), 
                    features_dict]
            # load classes list:
            all_objs_class_list = joblib.load(os.path.join(
                features_folder,"%s_classes.pkl" % featset_key))
            
        else:

            modelnum="noerrs"
            try: # load model object:
                rfc_model = joblib.load(os.path.join(
                    models_folder,"%s_%s.pkl" % (featset_key,model_type)))
            except Exception as theError:
                return [
                    str(theError) + (
                        "<br>It looks like a model has yet to be built for "
                        "this project - after uploading your data and "
                        "generating features, build the classifier model "
                        "using the form under the 'Build Model' tab."), 
                    "Using model %s_%s.pkl" % (featset_key,model_type), 
                    features_dict]
            # load classes list:
            all_objs_class_list = joblib.load(os.path.join(
            features_folder,"%s_classes.pkl" % featset_key))
        sorted_class_list = []
        for i in sorted(all_objs_class_list):
            if i not in sorted_class_list:
                sorted_class_list.append(i)
        try:
            classifier_preds = rfc_model.predict_proba(xNew)
        except ValueError as theError:
            results_str = str("ValueError:" + 
                str(theError).split("ValueError:")[-1])
            results_str += ("<BR><BR><i>Note: This is likely an indication "
                "that source metadata was provided in the header file during "
                "feature generation, but that no corresponding metadata was "
                "provided with this new unlabeled timeseries data. Please "
                "construct an appropriate metadata file (click above link for "
                "example) and try again.</i>")
            return results_str
        
        class_probs = classifier_preds[0]
        print "classifier_preds:", classifier_preds
        print "sorted_class_list:", sorted_class_list
        class_names = sorted_class_list
        
        results_str = ("<tr class='pred_results'>"
            "<td class='pred_results pred_results_fname_cell'>"
            "<a href='#'>%s</a></td>") % str(fname.split("/")[-1])
        results_arr = []
        
        if len(class_probs) != len(sorted_class_list):
            print "len(class_probs) != len(sorted_class_list)... Returning 0."
            print "len(class_probs) =", len(class_probs), \
                "len(sorted_class_list) =", len(sorted_class_list)
            return 0
        else:
            for i in range(len(class_probs)):
                results_arr.append(
                    [sorted_class_list[i], float(class_probs[i])])
            results_arr.sort(key=itemgetter(1),reverse=True)
            i=0
            for arr in results_arr:
                if i < n_cols_html_table:
                    results_str += """
                        <td class='pred_results'>%s</td>
                        <td class='pred_results'>%s</td>
                    """ % (arr[0], str(arr[1]))
                
                i += 1
        results_str += "</tr>"
        if modelnum == -99:
            modelnum = ""
        # print "predict_class.py() predict(): features_dict =", features_dict
        results_dict[str(fname.split("/")[-1])] = {
            "results_str":results_str, "ts_data":ts_data, 
            "features_dict":features_dict, "pred_results_list":results_arr}
        del rfc_model
        del all_objs_class_list
        del sorted_class_list
    #os.remove(newpred_file_path)
    return results_dict


if __name__ == "__main__":
    f = open('swasp.dat')
    lines = f.readlines()
    f.close()
    for i in range(len(lines)):
        lines[i] = lines[i].replace('\n','')
    lines = '\n'.join(lines)
    print predict(lines,',')
