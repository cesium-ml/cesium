from sklearn.externals import joblib
from sklearn.base import ClassifierMixin, RegressorMixin
from operator import itemgetter
import os
import numpy as np
import pandas as pd
import xray
import tarfile
import zipfile
from . import build_model
from . import cfg
from . import featurize
from . import featurize_tools as ft
from . import util


def add_to_predict_results_dict_classification_proba(
        results_dict, estimator_preds, fname, ts_data, features_dict,
        featureset_key, n_cols_html_table):
    """
    """
    # Load model target list
    sorted_target_list = list(estimator_preds.index)
    target_probs = estimator_preds

    results_str = ("<tr target='pred_results'>"
                   "<td target='pred_results pred_results_fname_cell'>"
                   "<a href='#'>%s</a></td>") % os.path.basename(fname)

    results_arr = []
    for i in range(len(target_probs)):
        results_arr.append([sorted_target_list[i], float(target_probs[i])])
    results_arr.sort(key=itemgetter(1), reverse=True)

    for i in range(len(results_arr)):
        if i < n_cols_html_table:
            results_str += """
                <td target='pred_results'>%s</td>
                <td target='pred_results'>%s</td>
            """ % (str(results_arr[i][0]), str(results_arr[i][1]))

    results_str += "</tr>"
    results_dict[os.path.splitext(os.path.basename(fname))[0]] = {
        "results_str": results_str, "ts_data": ts_data,
        "features_dict": features_dict, "pred_results": results_arr}


def add_to_predict_results_dict_classification(
        results_dict, estimator_preds, fname, ts_data, features_dict,
        featureset_key, n_cols_html_table):
    """
    """
    results_str = ("<tr class='pred_results'>"
                   "<td class='pred_results pred_results_fname_cell'>"
                   "<a href='#'>%s</a></td>") % os.path.basename(fname)
    if isinstance(estimator_preds, (list, np.ndarray, pd.core.series.Series)):
        estimator_preds = estimator_preds[0]

    results_str += "<td class='pred_results'>%s</td>" % str(estimator_preds)

    results_str += "</tr>"
    results_dict[os.path.basename(fname)] = {
        "results_str": results_str, "ts_data": ts_data,
        "features_dict": features_dict, "pred_results": [estimator_preds]}


def add_to_predict_results_dict_regression(results_dict, estimator_preds,
                                           fname, ts_data, features_dict,
                                           n_cols_html_table):
    """
    """
    results_str = ("<tr class='pred_results'>"
                   "<td class='pred_results pred_results_fname_cell'>"
                   "<a href='#'>%s</a></td>") % os.path.basename(fname)
    if isinstance(estimator_preds, (list, np.ndarray, pd.core.series.Series)):
        estimator_preds = estimator_preds[0]

    results_str += "<td class='pred_results'>%s</td>" % str(estimator_preds)

    results_str += "</tr>"
    results_dict[os.path.basename(fname)] = {
        "results_str": results_str, "ts_data": ts_data,
        "features_dict": features_dict, "pred_results": [estimator_preds]}


def do_model_predictions(featureset, model):
    """

    """
    # Do probabilistic model prediction when possible
    feature_df = build_model.rectangularize_featureset(featureset)
    if issubclass(type(model), ClassifierMixin):
        try:
            preds = model.predict_proba(feature_df)
        except AttributeError:
            preds = model.predict(feature_df)
    elif issubclass(type(model), RegressorMixin):
        preds = model.predict(feature_df)
    else:
        raise ValueError("Invalid model type: must be classifier or regressor.")
    preds_df = pd.DataFrame(preds, index=featureset.name)
    if preds_df.shape[1] == 1:
        preds_df.columns = ['prediction']
    else:
        preds_df.columns = model.classes_
    return preds_df


def predict(newpred_path, model_key, model_type, featureset_key,
            sepr=',', n_cols_html_table=5, 
            custom_features_script=None, metadata_path=None):
    """Generate features from new TS data and perform model prediction.

    Generates features for new time series file, loads saved
    estimator model, calculates target predictions with extracted
    features, and returns a dictionary containing a list of target
    prediction probabilities, a string containing HTML markup for a
    table containing a list of the results, the time-series data itself
    used to generate features, and a dictionary of the features
    extracted. The respective dict keys of the above-mentioned values
    are: "pred_results", "results_str", "ts_data", "features_dict".

    Parameters
    ----------
    newpred_path : str
        Path to time series data file to be used in prediction.
    model_key : str
        ID of the model to be used.
    model_type : str
        Type (abbreviation, e.g. "RF") of the model to be used.
    featureset_key : str
        RethinkDB ID of the feature set used to create the
        above-specified model.
    sepr : str, optional
        Delimiting character in time series data file. Default is comma
        (",").
    n_cols_html_table : int, optional
        The number of highest-probability targets to include (one per
        column) in the generated HTML table.
    custom_features_script : str, optional
        Path to custom features script to be used in feature
        generation, defaults to None.
    metadata_path : str, optional
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
            "pred_results": A list of lists, each containing one
                of the most-probable targets and its probability.

    """
    if tarfile.is_tarfile(newpred_path) or zipfile.is_zipfile(newpred_path):
        ts_paths = ft.extract_data_archive(newpred_path)
    else:
        ts_paths = [newpred_path]
    all_ts_data = {util.shorten_fname(ts_path): ft.parse_ts_data(ts_path) 
                   for ts_path in ts_paths}
    
    featureset_path = os.path.join(cfg.FEATURES_FOLDER,
                                   '{}_featureset.nc'.format(featureset_key))
    featureset = xray.open_dataset(featureset_path)
    features_to_use = list(featureset.data_vars)
    new_featureset = featurize.featurize_data_file(newpred_path, metadata_path,
                                                   features_to_use=features_to_use,
                                                   custom_script_path=custom_features_script)

    model = joblib.load(os.path.join(cfg.MODELS_FOLDER,
                                     "{}.pkl".format(model_key)))
    preds_df = do_model_predictions(new_featureset, model)
    
    # TODO this code will go away when we stop producing HTML here; for now,
    # just separating it so that it can be more easily taken out
    results_dict = {}
    for fname, row in preds_df.iterrows():
        ts_data = all_ts_data[fname]
        featureset_row = build_model.rectangularize_featureset(new_featureset).loc[fname]
        features_dict = featureset_row.to_dict()
        # TODO this will also go away when we stop storing features in the DB;
        # labels all have to be strings, but multichannel data they are tuples
        for key in features_dict.keys():
            if isinstance(key, str):
                new_key = key
            elif 'channel' in new_featureset and len(new_featureset.channel) <= 1:
                new_key = key[0]
            else:
                new_key = '_'.join([str(el) for el in key])
            features_dict[new_key] = features_dict.pop(key)
        if len(row) > 1:
            add_to_predict_results_dict_classification_proba(
                results_dict, row, fname, ts_data, features_dict,
                featureset_key, n_cols_html_table)
        elif issubclass(type(model), ClassifierMixin):
            add_to_predict_results_dict_classification(
                results_dict, row, fname, ts_data, features_dict,
                featureset_key, n_cols_html_table)
        else:
            add_to_predict_results_dict_regression(results_dict, row,
                                                   fname, ts_data, features_dict,
                                                   n_cols_html_table)
    return results_dict
