from __future__ import print_function
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.externals import joblib
# from sklearn.cross_validation import train_test_split
# from sklearn.metrics import confusion_matrix
import os
import numpy as np
import pickle
from . import cfg
from mltsp.celery_tasks import fit_and_store_model


def create_and_pickle_model_celery(model_key, model_type, featureset_key,
                                   model_options={}):
    """
    """

    res = fit_and_store_model.delay(model_key, model_type, featureset_key,
                                    model_options)
    fout_name = res.get(timeout=200)

    print(fout_name, "created!")


def build_model(model_key, model_type, featureset_key, model_options={}):
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

    create_and_pickle_model_celery(model_key, model_type, featureset_key,
                                   model_options)

    print("Done!")
    return("New model successfully created. Click the Predict tab to "
           "start using it.")
