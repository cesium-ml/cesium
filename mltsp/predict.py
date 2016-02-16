from sklearn.externals import joblib
from sklearn.grid_search import GridSearchCV
import os
import pandas as pd
import xarray as xr
import tarfile
import zipfile
from . import build_model
from .cfg import config
from . import featurize
from . import data_management
from . import util


def model_predictions(featureset, model, return_probs=True):
    """Construct a DataFrame of model predictions for given featureset.

    Parameters
    ----------
    featureset : xarray.Dataset
        Dataset containing feature values for which predictions are desired
    model : scikit-learn model
        Fitted scikit-learn model to be used to generate predictions
    return_probs : bool, optional
        Parameter to control the type of prediction made in the classification
        setting (the parameter has no effect for regression models). If True,
        probabilities for each class are returned where possible; if False,
        only the top predicted label for each time series is returned.

    Returns
    -------
    pandas.DataFrame
        DataFrame of model predictions, indexed by `featureset.name`. Each row
        contains either a single class/target prediction or (for probabilistic
        predictions) a list of class probabilities.
    """
    feature_df = build_model.rectangularize_featureset(featureset)
    if return_probs:
        try:
            preds = model.predict_proba(feature_df)
        except AttributeError:
            preds = model.predict(feature_df)
    else:
        preds = model.predict(feature_df)

    if len(preds.shape) == 1:
        return pd.Series(preds, index=feature_df.index, name='prediction')
    else:
        if isinstance(model, GridSearchCV):
            columns = model.best_estimator_.classes_
        else:
            columns = model.classes_
        return pd.DataFrame(preds, index=feature_df.index, columns=columns)


def predict_data_file(newpred_path, model_key, model_type, featureset_key,
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
    custom_features_script : str, optional
        Path to custom features script to be used in feature
        generation. Defaults to None.
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

            - "results_str": String containing table listing results in markup.
            - "ts_data": The original time-series data provided.
            - "features_dict": A dictionary containing the generated features.
            - "pred_results": A list of lists, each containing one of the
              most-probable targets and its probability.

    """
    with util.extract_time_series(data_path, cleanup_archive=False,
                                  cleanup_files=True) as ts_paths:
        all_ts_data = {util.shorten_fname(ts_path):
                       data_management.parse_ts_data(ts_path)
                       for ts_path in ts_paths}

        featureset_path = os.path.join(config['paths']['features_folder'],
                                       '{}_featureset.nc'.format(featureset_key))
        featureset = xr.open_dataset(featureset_path)
        features_to_use = list(featureset.data_vars)
        new_featureset = featurize.featurize_data_file(newpred_path, metadata_path,
                                                       features_to_use=features_to_use,
                                                       custom_script_path=custom_features_script)

        model = joblib.load(os.path.join(config['paths']['models_folder'],
                                         "{}.pkl".format(model_key)))
        # Covert to DataFrame so we can treat 1d/2d predictions in the same way
        preds_df = pd.DataFrame(model_predictions(new_featureset, model))

        # TODO this code will go away when we stop returning all the data here,
        # which should happen when we develop a file management system.
        results_dict = {}
        new_feature_df = build_model.rectangularize_featureset(new_featureset)
        results_dict = {fname: {"results_str": "",
                                "ts_data": all_ts_data[fname],
                                "features_dict": new_feature_df.loc[fname].to_dict(),
                                "pred_results": list(row.sort_values(inplace=False,
                                                     ascending=False).iteritems())
                                                if len(row) > 1 else row}
                        for fname, row in preds_df.iterrows()}
    return results_dict
