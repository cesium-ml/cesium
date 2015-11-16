import os
import xray
from . import cfg
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
from sklearn.externals import joblib


MODELS_TYPE_DICT = {'RFC': RandomForestClassifier,
                    'RFR': RandomForestRegressor,
                    'LC': SGDClassifier,
                    'LR': LinearRegression,
                    'RC': RidgeClassifierCV,
                    'ARDR': ARDRegression,
                    'BRR': BayesianRidge}


def rectangularize_featureset(featureset):
    """Convert xray.Dataset into (2d) Pandas.DataFrame for use with sklearn."""
    featureset = featureset.drop([coord for coord in ['target', 'class']
                                  if coord in featureset])
    feature_df = featureset.to_dataframe()
    if 'channel' in featureset:
        feature_df = feature_df.unstack(level='channel')
        if len(featureset.channel) == 1:
            feature_df.columns = [pair[0] for pair in feature_df.columns]
        else:
            feature_df.columns = ['_'.join(pair)
                                  for pair in feature_df.columns]
    return feature_df


def build_model_from_featureset(featureset, model=None, model_type=None,
                                model_options={}):
    """Build model from (non-rectangular) xray.Dataset of features."""
    if model is None:
        if model_type:
            model = MODELS_TYPE_DICT[model_type](**model_options)
        else:
            raise ValueError("If model is None, model_type must be specified")
    feature_df = rectangularize_featureset(featureset)
    model.fit(feature_df, featureset['target'])
    return model


def create_and_pickle_model(model_key, model_type, featureset_key,
                            model_options={}):
    """Build a `scikit-learn` model.

    Builds the specified model and pickles it in the file
    whose name is given by
    ``'%s_%s.pkl' % (featureset_key, model_type)``
    in the directory `cfg.MODELS_FOLDER`.


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

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """

    featureset_path = os.path.join(cfg.FEATURES_FOLDER,
                                   '{}_featureset.nc'.format(featureset_key))
    featureset = xray.open_dataset(featureset_path)

    model = build_model_from_featureset(featureset, model_type=model_type,
                                        model_options=model_options)

    # Store the model:
    foutname = os.path.join(cfg.MODELS_FOLDER, '{}.pkl'.format(model_key))
    joblib.dump(model, foutname, compress=3)
    return("New model successfully created. Click the Predict tab to "
           "start using it.")
