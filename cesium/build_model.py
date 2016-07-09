import os
import xarray as xr
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
from sklearn.externals import joblib
from sklearn import grid_search


__all__ = ['MODELS_TYPE_DICT', 'rectangularize_featureset',
           'fit_model_optimize_hyperparams', 'build_model_from_featureset']


MODELS_TYPE_DICT = {'RandomForestClassifier': RandomForestClassifier,
                    'RandomForestRegressor': RandomForestRegressor,
                    'LinearSGDClassifier': SGDClassifier,
                    'LinearRegressor': LinearRegression,
                    'RidgeClassifierCV': RidgeClassifierCV,
                    'BayesianARDRegressor': ARDRegression,
                    'BayesianRidgeRegressor': BayesianRidge}


def rectangularize_featureset(featureset):
    """Convert xarray.Dataset into (2d) Pandas.DataFrame for use with sklearn."""
    featureset = featureset.drop([coord for coord in featureset.coords
                                  if coord not in ['name', 'channel']])
    feature_df = featureset.to_dataframe()
    if 'channel' in featureset:
        feature_df = feature_df.unstack(level='channel')
        if len(featureset.channel) == 1:
            feature_df.columns = [pair[0] for pair in feature_df.columns]
        else:
            feature_df.columns = ['_'.join([str(el) for el in pair])
                                  for pair in feature_df.columns]
    return feature_df.loc[featureset.name]  # preserve original row ordering


def fit_model_optimize_hyperparams(data, targets, model, params_to_optimize,
                                   cv=None):
    """Optimize estimator hyperparameters.

    Perform hyperparamter optimization using
    `sklearn.grid_search.GridSearchCV`.

    Parameters
    ----------
    data : Pandas.DataFrame
        Features for training model.
    targets : Pandas.Series
        Targets corresponding to feature vectors in `data`.
    model : sklearn estimator object
        The model/estimator whose hyperparameters are to be optimized.
    params_to_optimize : dict or list of dict
        Dictionary with parameter names as keys and lists of values to try
        as values, or a list of such dictionaries.
    cv : int, cross-validation generator or an iterable, optional
        Number of folds (defaults to 3) or an iterable yielding train/test
        splits. See documentation for `GridSearchCV` for details.

    Returns
    -------
    `sklearn.grid_search.GridSearchCV` estimator object

    """
    optimized_model = grid_search.GridSearchCV(model, params_to_optimize, cv=cv)
    optimized_model.fit(data, targets)
    return optimized_model


def build_model_from_featureset(featureset, model=None, model_type=None,
                                model_options={}, params_to_optimize=None,
                                cv=None):
    """Build model from (non-rectangular) xarray.Dataset of features."""
    if model is None:
        if model_type:
            model = MODELS_TYPE_DICT[model_type](**model_options)
        else:
            raise ValueError("If model is None, model_type must be specified")
    feature_df = rectangularize_featureset(featureset)
    if params_to_optimize:
        model = fit_model_optimize_hyperparams(feature_df, featureset['target'],
                                               model, params_to_optimize, cv)
    else:
        model.fit(feature_df, featureset['target'])
    return model
