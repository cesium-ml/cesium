from __future__ import print_function
import os
import numpy as np
import pandas as pd
from . import cfg
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, SGDClassifier,\
    RidgeClassifierCV, ARDRegression, BayesianRidge
from sklearn.externals import joblib


def create_and_pickle_model(model_key, model_type, featureset_key, model_options={}):
    """Build a `scikit-learn` model.

    Builds the specified model and pickles it in the file
    whose name is given by
    ``"%s_%s.pkl" % (featureset_key, model_type)``
    in the directory `cfg.MODELS_FOLDER` (or is later copied there
    from within the Docker container if `in_docker_container` is True.

    Parameters
    ----------
    model_key : str
        Unique model ID.
    featureset_key: str
        RethinkDB ID of the associated feature set from which to build
        the model, which will also become the ID/key for the model.
    model_type : str
        Abbreviation of the type of model to be created. Defaults
        to "RFC".
    model_options : dict, optional
        Dictionary specifying `scikit-learn` model parameters to be used.

    Returns
    -------
    str
        Human-readable message indicating successful completion.

    """
    features_filename = os.path.join(cfg.FEATURES_FOLDER, "%s_features.csv" %
                                     featureset_key)
    features = pd.read_csv(features_filename)
    targets = np.load(features_filename.replace("_features.csv",
                                                "_targets.npy"))
    
    models_type_dict = {"RFC": RandomForestClassifier,
                        "RFR": RandomForestRegressor,
                        "LC": SGDClassifier,
                        "LR": LinearRegression,
                        "RC": RidgeClassifierCV,
                        "ARDR": ARDRegression,
                        "BRR": BayesianRidge}

    model_obj = models_type_dict[model_type](**model_options)
    model_obj.fit(features, targets)

    # Store the model:
    foutname = os.path.join(cfg.MODELS_FOLDER, "{}.pkl".format(model_key))
    joblib.dump(model_obj, foutname, compress=3)
    return("New model successfully created. Click the Predict tab to "
           "start using it.")
