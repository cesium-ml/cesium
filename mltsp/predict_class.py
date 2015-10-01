from __future__ import print_function
from sklearn.externals import joblib

from operator import itemgetter
import os
import shutil
import tempfile
import numpy as np
import tarfile
from copy import deepcopy
import uuid

from . import cfg
from . import custom_exceptions
from . import custom_feature_tools as cft
from .celery_tasks import pred_featurize_single


def parse_metadata_file(metadata_file_path):
    """
    """
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
                        list(zip(meta_feat_names, meta_feats)))
    else:
        meta_features = {}
    return meta_features


def determine_feats_used(featset_key):
    """
    """
    with open(os.path.join(
            cfg.FEATURES_FOLDER, "%s_features.csv" % featset_key)) as f:
        features_in_model = f.readline().strip().split(',')
    return features_in_model


def featurize_multiple_serially(newpred_file_path, tmp_dir_path,
                                features_to_use, custom_features_script,
                                all_meta_features, sep=","):
    """
    """
    the_tarfile = tarfile.open(newpred_file_path)
    all_fnames = the_tarfile.getnames()
    the_tarfile.extractall(path=tmp_dir_path)
    big_features_and_tsdata_dict = {}
    for fname in all_fnames:
        meta_features = all_meta_features.get(os.path.basename(fname), {})
        big_features_and_tsdata_dict.update(featurize_single(
            fname, features_to_use, custom_features_script, meta_features,
            tmp_dir_path=tmp_dir_path, sep=sep))
    return big_features_and_tsdata_dict


def featurize_single(newpred_file_path, features_to_use, custom_features_script,
                     meta_features, tmp_dir_path="/tmp", sep=","):
    """
    """
    fname = newpred_file_path
    if os.path.isfile(fname) and os.path.isabs(fname):
        filepath = fname
    elif os.path.isfile(os.path.join(tmp_dir_path, fname)) and \
         os.path.isabs(os.path.join(tmp_dir_path, fname)):
        filepath = os.path.join(tmp_dir_path, fname)
    elif os.path.isfile(os.path.join(os.path.join(cfg.UPLOAD_FOLDER,
                                                  "unzipped"),
                                     fname)) and \
         os.path.isabs(os.path.join(os.path.join(cfg.UPLOAD_FOLDER, "unzipped"),
                                    fname)):
        filepath = os.path.join(os.path.join(cfg.UPLOAD_FOLDER, "unzipped"),
                                fname)
    elif os.path.isfile(os.path.join(cfg.UPLOAD_FOLDER, fname)) and \
         os.path.isabs(os.path.join(cfg.UPLOAD_FOLDER, fname)):
        filepath = os.path.join(cfg.UPLOAD_FOLDER, fname)
    else:
        print(fname + " is not a file...")
        return {}

    res = pred_featurize_single.delay(
        filepath, features_to_use, custom_features_script,
        meta_features)
    big_features_and_tsdata_dict = res.get(timeout=30)

    return big_features_and_tsdata_dict


def generate_input_params_list(newpred_file_path, features_to_use,
                               custom_features_script, all_meta_features,
                               tmp_dir_path):
    """
    """
    params_list = []
    the_tarfile = tarfile.open(newpred_file_path)
    all_fnames = the_tarfile.getnames()
    the_tarfile.extractall(path=tmp_dir_path)
    for fname in all_fnames:
        if not os.path.isfile(fname):
            if os.path.isfile(os.path.join(tmp_dir_path, fname)):
                fname = os.path.join(tmp_dir_path, fname)
            elif os.path.isdir(os.path.join(tmp_dir_path, fname)):
                continue
            else:
                raise Exception("Specified TS data file not on disk - %s." %
                                fname)
        meta_features = all_meta_features.get(os.path.basename(fname), {})
        params_list.append([fname, features_to_use, custom_features_script,
                            meta_features])
    return params_list


def featurize_multiple(newpred_file_path, features_to_use,
                       custom_features_script, meta_features, tmp_dir_path):
    """
    """
    input_params_list = generate_input_params_list(
        newpred_file_path, features_to_use, custom_features_script,
        meta_features, tmp_dir_path)
    res = pred_featurize_single.chunks(input_params_list, cfg.N_CORES).delay()
    res_list = res.get(timeout=100)
    big_features_and_tsdata_dict = {}
    for line in res_list:
        for feats_and_tsdata_dict in line:
            big_features_and_tsdata_dict.update(feats_and_tsdata_dict)
    return big_features_and_tsdata_dict


def featurize_tsdata(newpred_file_path, featset_key, custom_features_script,
                     metadata_file_path, features_already_extracted,
                     features_to_use, in_docker_container):
    """
    """
    all_meta_features = parse_metadata_file(metadata_file_path)
    sep = sepr = ","

    all_features_list = cfg.features_list_obs[:] + cfg.features_list_science[:]
    tmp_dir_path = os.path.join("/tmp", str(uuid.uuid4())[:10])
    os.mkdir(tmp_dir_path)
    os.chmod(tmp_dir_path, 0777)
    if tarfile.is_tarfile(newpred_file_path):
        big_features_and_tsdata_dict = featurize_multiple(
            newpred_file_path, features_to_use,
            custom_features_script, all_meta_features, tmp_dir_path)
    else:
        meta_features = all_meta_features.get(os.path.basename(newpred_file_path), {})
        big_features_and_tsdata_dict = featurize_single(
            newpred_file_path, features_to_use, custom_features_script,
            meta_features)

    shutil.rmtree(tmp_dir_path, ignore_errors=True)
    return big_features_and_tsdata_dict


def create_feat_dict_and_list(new_obj, features_to_use, features_extracted):
    """
    """
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
                print(theError)
                pass
        else:
            pass
    return (newFeatures, features_dict)


def add_to_predict_results_dict(results_dict, classifier_preds, fname, ts_data,
                                features_dict, featset_key, n_cols_html_table):
    """
    """
    # Load model class list
    all_objs_class_list = list(np.load(
        os.path.join(cfg.FEATURES_FOLDER, "%s_classes.npy" % featset_key)))
    sorted_class_list = []
    for i in sorted(all_objs_class_list):
        if i not in sorted_class_list:
            sorted_class_list.append(i)
    class_probs = classifier_preds[0]
    class_names = sorted_class_list

    results_str = ("<tr class='pred_results'>"
                   "<td class='pred_results pred_results_fname_cell'>"
                   "<a href='#'>%s</a></td>") % os.path.basename(fname)
    results_arr = []

    for i in range(len(class_probs)):
        results_arr.append(
            [sorted_class_list[i], float(class_probs[i])])
    results_arr.sort(key=itemgetter(1), reverse=True)

    for i in range(len(results_arr)):
        if i < n_cols_html_table:
            results_str += """
                <td class='pred_results'>%s</td>
                <td class='pred_results'>%s</td>
            """ % (str(results_arr[i][0]), str(results_arr[i][1]))

    results_str += "</tr>"
    results_dict[os.path.splitext(os.path.basename(fname))[0]] = {
        "results_str": results_str, "ts_data": ts_data,
        "features_dict": features_dict, "pred_results_list": results_arr}
    return


def do_model_predictions(big_features_and_tsdata_dict, featset_key, model_type,
                         features_to_use, n_cols_html_table):
    """

    """
    features_extracted = list(big_features_and_tsdata_dict[
        list(big_features_and_tsdata_dict.keys())[0]]["features_dict"].keys())

    results_dict = {}
    for fname, features_and_tsdata_dict in \
            big_features_and_tsdata_dict.items():
        ts_data = features_and_tsdata_dict['ts_data']
        new_obj = features_and_tsdata_dict['features_dict']
        newFeatures, features_dict = create_feat_dict_and_list(
            new_obj, features_to_use, features_extracted)

        # Load model
        rfc_model = joblib.load(os.path.join(
            cfg.MODELS_FOLDER, "%s_%s.pkl" % (featset_key, model_type)))

        # Do probabilistic model prediction
        classifier_preds = rfc_model.predict_proba(np.array(newFeatures))
        add_to_predict_results_dict(
            results_dict, classifier_preds, fname, ts_data, features_dict,
            featset_key, n_cols_html_table)

    return results_dict


def predict(newpred_file_path, model_name, model_type, featset_key,
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
        the time series data provided. Defaults to False.
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
    print("predict_class - predict() called.")

    features_to_use = determine_feats_used(featset_key)

    big_features_and_tsdata_dict = featurize_tsdata(
        newpred_file_path, featset_key, custom_features_script,
        metadata_file_path, features_already_extracted,
        features_to_use, in_docker_container)

    pred_results_dict = do_model_predictions(
        big_features_and_tsdata_dict, featset_key, model_type, features_to_use,
        n_cols_html_table)

    return pred_results_dict
