import os
import xarray as xr
from .cfg import config
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
from sklearn.externals import joblib
from sklearn import grid_search


MODELS_TYPE_DICT = {'RandomForestClassifier': RandomForestClassifier,
                    'RandomForestRegressor': RandomForestRegressor,
                    'LinearSGDClassifier': SGDClassifier,
                    'LinearRegressor': LinearRegression,
                    'RidgeClassifierCV': RidgeClassifierCV,
                    'BayesianARDRegressor': ARDRegression,
                    'BayesianRidgeRegressor': BayesianRidge}


def rectangularize_featureset(featureset):
    """Convert xarray.Dataset into (2d) Pandas.DataFrame for use with sklearn."""
    featureset = featureset.drop([coord for coord in ['target', 'class']
                                  if coord in featureset])
    feature_df = featureset.to_dataframe()
    if 'channel' in featureset:
        feature_df = feature_df.unstack(level='channel')
        if len(featureset.channel) == 1:
            feature_df.columns = [pair[0] for pair in feature_df.columns]
        else:
            feature_df.columns = ['_'.join([str(el) for el in pair])
                                  for pair in feature_df.columns]
    return feature_df.loc[featureset.name]  # preserve original row ordering


def fit_model_optimize_hyperparams(data, targets, model, params_to_optimize):
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

    Returns
    -------
    `sklearn.grid_search.GridSearchCV` estimator object

    """
    optimized_model = grid_search.GridSearchCV(model, params_to_optimize)
    optimized_model.fit(data, targets)
    return optimized_model


def build_model_from_featureset(featureset, model=None, model_type=None,
                                model_options={}, params_to_optimize=None):
    """Build model from (non-rectangular) xarray.Dataset of features."""
    if model is None:
        if model_type:
            model = MODELS_TYPE_DICT[model_type](**model_options)
        else:
            raise ValueError("If model is None, model_type must be specified")
    feature_df = rectangularize_featureset(featureset)
    if params_to_optimize:
        model = fit_model_optimize_hyperparams(feature_df, featureset['target'],
                                               model, params_to_optimize)
    else:
        model.fit(feature_df, featureset['target'])
    return model


def create_and_pickle_model(model_key, model_type, featureset_key,
                            model_options={}, params_to_optimize=None):
    """Build a `scikit-learn` model.

    Builds the specified model and pickles it in the file
    whose name is given by
    ``'%s_%s.pkl' % (featureset_key, model_type)``
    in the directory `config['paths']['models_folder']`.


    Parameters
    ----------
    model_key : str
        Unique model ID.
    featureset_key: str
        RethinkDB ID of the associated feature set from which to build
        the model, which will also become the ID/key for the model.
    model_type : str
        Abbreviation of the type of model to be created.
    model_options : dict, optional
        Dictionary specifying `scikit-learn` model parameters to be used.
    params_to_optimize : dict or list of dict, optional
        Dictionary with parameter names as keys and lists of values to try
        as values, or a list of such dictionaries. Defaults to None.

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """

    featureset_path = os.path.join(config['paths']['features_folder'],
                                   '{}_featureset.nc'.format(featureset_key))
    featureset = xr.open_dataset(featureset_path)

    model = build_model_from_featureset(featureset, model_type=model_type,
                                        model_options=model_options,
                                        params_to_optimize=params_to_optimize)

    # Store the model:
    foutname = os.path.join(config['paths']['models_folder'], '{}.pkl'.format(model_key))
    joblib.dump(model, foutname, compress=3)
    return("New model successfully created. Click the Predict tab to "
           "start using it.")
