from sklearn.externals import joblib
from sklearn.grid_search import GridSearchCV
import os
import numpy as np
import pandas as pd
import xarray as xr
from . import build_model
from . import time_series
from . import util


__all__ = ['model_predictions', 'predict_data_files']


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
    if return_probs and hasattr(model, 'predict_proba'):
        preds = model.predict_proba(feature_df)
    else:
        preds = model.predict(feature_df)

    predset = featureset.copy()
    if len(preds.shape) == 1:
        predset['prediction'] = (['name'], preds)
    else:
        if isinstance(model, GridSearchCV):
            columns = model.best_estimator_.classes_
        else:
            columns = model.classes_
        predset['class_label'] = columns
        predset['prediction'] = (['name', 'class_label'], preds)
    return predset
