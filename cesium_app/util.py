import ast
import contextlib
import errno
import os
import subprocess
import tarfile
import tempfile
import zipfile

import numpy as np

import requests


__all__ = ['check_model_param_types', 'make_list',
           'robust_literal_eval', 'warn_defaultdict']


def make_list(x):
    import collections
    if isinstance(x, collections.Iterable) and not isinstance(x, str):
        return x
    else:
        return [x,]


def check_model_param_types(model_type, model_params, all_as_lists=False):
    """Cast model parameter strings to expected types.

    Modifies `model_params` dict in place.

    Parameters
    ----------
    model_type : str
        Name of model.
    model_params : dict
        Dictionary containing model parameters to be checked against expected
        types.
    all_as_lists : bool, optional
        Boolean indicating whether `model_params` values are wrapped in lists,
        as in the case of parameter grids for optimization.

    Raises
    ------
    ValueError
        Raises ValueError if parameter(s) are not of expected type.

    """
    from .ext.sklearn_models import model_descriptions
    # Find relevant model description
    for entry in model_descriptions:
        if entry["name"] == model_type:
            params_list = entry["params"]
            break
    try:
        params_list
    except NameError:
        raise ValueError("model_type not in list of allowable models.")
    # Iterate through params and check against expected types
    for k, v in model_params.items():
        # Empty string or "None" goes to `None`
        if v in ["None", ""]:
            model_params[k] = None
            continue
        # Find relevant parameter description
        for p in params_list:
            if p["name"] == k:
                param_entry = p
                break
        dest_types_list = make_list(param_entry["type"])
        if not all_as_lists:
            v = [v,]
        if all(type(x) in dest_types_list or x is None for x in v):
            break
        else:
            raise ValueError("Model parameter is not of expected type "
                             "(parameter {} ({}) is of type {}, which is not "
                             "in list of expected types ({}).".format(
                                 param_entry["name"], v, type(v),
                                 dest_types_list))


def robust_literal_eval(val):
    """Call `ast.literal_eval` without raising `ValueError`.

    Parameters
    ----------
    val : str
        String literal to be evaluated.

    Returns
    -------
    Output of `ast.literal_eval(val)', or `val` if `ValueError` was raised.

    """
    try:
        return ast.literal_eval(val)
    except ValueError:
        return val
