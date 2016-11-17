import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
try:
    from sklearn.model_selection import GridSearchCV
except:
    from sklearn.grid_search import GridSearchCV


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
    """Convert xarray.Dataset into (2d) Pandas.DataFrame for use with sklearn.

    Parameters
    ----------
    featureset : xarray.Dataset
        The xarray.Dataset object containing features.

    Returns
    -------
    Pandas.DataFrame
        2-D, sklearn-compatible Dataframe containing features.

    """
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
    # sort columns by name for consistent ordering
    feature_df = feature_df[sorted(feature_df.columns)]
    return feature_df.loc[featureset.name]  # preserve original row ordering


def fit_model_optimize_hyperparams(data, targets, model, params_to_optimize,
                                   cv=None):
    """Optimize estimator hyperparameters.

    Perform hyperparamter optimization using
    `sklearn.model_selection.GridSearchCV`.

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
    `sklearn.model_selection.GridSearchCV.best_estimator_` estimator object

    """
    optimized_model = GridSearchCV(model, params_to_optimize, cv=cv)
    optimized_model.fit(data, targets)
    return optimized_model.best_estimator_


def build_model_from_featureset(featureset, model=None, model_type=None,
                                model_parameters={}, params_to_optimize=None,
                                cv=None):
    """Build model from (non-rectangular) xarray.Dataset of features.

    Parameters
    ----------
    featureset : xarray.Dataset of features
        Features for training model.
    model : scikit-learn model, optional
        Instantiated scikit-learn model. If None, `model_type` must not be.
        Defaults to None.
    model_type : str, optional
        String indicating model to be used, e.g. "RandomForestClassifier".
        If None, `model` must not be. Defaults to None.
    model_parameters : dict, optional
        Dictionary with hyperparameter values to be used in model building.
        Keys are parameter names, values are the associated parameter values.
        These hyperparameters will be passed to the model constructor as-is
        (for hyperparameter optimization, see `params_to_optimize`).
        If None, default values will be used (see scikit-learn documentation
        for specifics).
    params_to_optimize : dict or list of dict, optional
        During hyperparameter optimization, various model parameters
        are adjusted to give an optimal fit. This dictionary gives the
        different values that should be explored for each parameter. E.g.,
        `{'alpha': [1, 2], 'beta': [4, 5, 6]}` would fit models on all
        6 combinations of alpha and beta and compare the resulting models'
        goodness-of-fit. If None, only those hyperparameters specified in
        `model_parameters` will be used (passed to model constructor as-is).
        Defaults to None.
    cv : int, cross-validation generator or an iterable, optional
        Number of folds (defaults to 3 if None) or an iterable yielding
        train/test splits. See documentation for `GridSearchCV` for details.
        Defaults to None (yielding 3 folds).

    Returns
    -------
    sklearn estimator object
        The fitted sklearn model.

    """
    if featureset.get('target') is None:
        raise ValueError("Cannot build model for unlabeled feature set.")

    if model is None:
        if model_type:
            model = MODELS_TYPE_DICT[model_type](**model_parameters)
        else:
            raise ValueError("If model is None, model_type must be specified")
    feature_df = rectangularize_featureset(featureset)
    try:
        if params_to_optimize:
            model = fit_model_optimize_hyperparams(feature_df, featureset['target'],
                                                   model, params_to_optimize, cv)
        else:
            model.fit(feature_df, featureset['target'])
    except ValueError as e:
        nan_feats = np.isnan(feature_df).any()
        inf_feats = np.isinf(feature_df).any()
        message = "Invalid feature values detected:"
        if nan_feats.any():
            message += " NaN in {}.".format(", ".join(feature_df.columns[nan_feats]))
        if inf_feats.any():
            message += " Inf in {}.".format(", ".join(feature_df.columns[inf_feats]))
        raise ValueError(message)
    return model


def score_model(model, featureset, sample_weight=None):
    """Compute the model training score.

    Parameters
    ----------
    model : scikit-learn model object
        The fitted model.
    featureset : xarray.Dataset of features
        Feature set used for training model.
    sample_weight : array-like, shape = [n_samples], optional
        Sample weights. Defaults to None.

    Returns
    -------
    float
        Normalized training score.
    """
    feature_df = rectangularize_featureset(featureset)
    return model.score(feature_df, featureset['target'], sample_weight)
