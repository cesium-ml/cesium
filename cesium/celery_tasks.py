from celery import group, chord
import joblib
import xarray as xr

from cesium import time_series
from cesium import util
from cesium import featurize_tools as ft
from cesium import build_model
from cesium import predict
from cesium.celery_app import app


@app.task()
def check_celery():
    """Test task."""
    return "OK"


def celery_available():
    """Test Celery task; this is much faster than running `celery status`."""
    try:
        res = check_celery.apply_async()
        return "OK" == res.get(timeout=2)
    except:
        return False


@app.task()
def featurize_ts_file(ts_file_path, features_to_use, custom_script_path=None):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_file_path : str
        Time-series data file disk location path.
    features_to_use : list of str
        List of names of features to be generated.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.

    Returns
    -------
    tuple
        Tuple with elements (file name, feature dictionary, class/regression
        target, metafeature dictionary).

    """
    short_fname = util.shorten_fname(ts_file_path)
    ts = time_series.from_netcdf(ts_file_path)
    all_features = ft.featurize_single_ts(ts, features_to_use,
                                          custom_script_path)
    return (short_fname, all_features, ts.target, ts.meta_features)


@app.task()
def featurize_ts_data(time_series, features_to_use, custom_script_path=None,
                      custom_functions=None):
    """Featurize time-series objects.

    Parameters
    ----------
    time_series : TimeSeries object
        Time series data to be featurized.
    features_to_use : list of str
        List of names of features to be generated.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.
    custom_functions : dict, optional
        Dictionary of custom feature functions to be evaluated for the given
        time series, or a dictionary representing a dask graph of function
        evaluations. Dictionaries of functions should have keys `feature_name`
        and values functions that take arguments (t, m, e); in the case of a
        dask graph, these arrays should be referenced as 't', 'm', 'e',
        respectively, and any values with keys present in `features_to_use`
        will be computed.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the time series name and
        second element is a dictionary of features.

    """
    all_features = ft.featurize_single_ts(time_series, features_to_use,
                                          custom_script_path, custom_functions)
    return (time_series.name, all_features)


@app.task()
def combine_features(res_list, output_path, *args, **kwargs):
    """TODO"""
    fnames, feature_dicts, targets, meta_feature_dicts = zip(*res_list)
    featureset = ft.assemble_featureset(feature_dicts, targets,
                                        meta_feature_dicts, fnames)
    if output_path:
        featureset.to_netcdf(output_path)

    return featureset


@app.task()
def predict_featureset(fset, model, output_path=None):
    """TODO"""
    predset = predict.model_predictions(fset, model)
    if output_path:
        predset.to_netcdf(output_path)

    return predset


def featurize_task(ts_paths, features_to_use, output_path=None,
                   custom_script_path=None):
    """TODO

    Parameters
    ----------
    custom_script_path : str, optional
        Path to custom features definition script, if applicable.
    """

    return (group(featurize_ts_file.s(ts_path, features_to_use,
                                             custom_script_path)
                       for ts_path in ts_paths) |
            combine_features.s(output_path))


@app.task()
def build_model_task(model_type, model_params, fset_path, output_path=None,
                     params_to_optimize=None):
    """TODO"""
    with xr.open_dataset(fset_path) as fset:
        model = build_model.build_model_from_featureset(fset,
            model_type=model_type, model_options=model_params,
            params_to_optimize=params_to_optimize)
        if output_path:
            joblib.dump(model, output_path, compress=3)

        return model


def prediction_task(ts_paths, features_to_use, model_path, output_path=None,
                    custom_features_script=None):
    """Generate features from new TS data and perform model prediction.

    Generates features for new time series file, loads saved
    estimator model, calculates target predictions with extracted
    features, and returns TODO

    Parameters
    ----------
    ts_paths : str
        Path to netCDF files containing seriealized TimeSeries objects to be
        used in prediction.
    features_to_use : list of str
        List of features to extract for new time series data
    model_path : str
        Path to pickled model to use for making predictions on new input time series
    output_path
    custom_features_script : str, optional
        Path to custom features script to be used in feature
        generation. Defaults to None.

    Returns
    -------
    """
    model = joblib.load(model_path)
    return (featurize_task(ts_paths, features_to_use=features_to_use,
                           custom_script_path=custom_features_script) |
            predict_featureset.s(model, output_path) | forward.s())


def predict_prefeaturized_task(featureset_path, model_path, output_path=None,
                               custom_features_script=None):
    """Perform model predictions for pre-featurized data.

    Loads saved model, calculates target predictions with extracted features,
    and returns Dataset containing features and predictions.

    Parameters
    ----------
    ts_paths : str
        Path to netCDF files containing seriealized TimeSeries objects to be
        used in prediction.
    features_to_use : list of str
        List of features to extract for new time series data
    model_path : str
        Path to pickled model to use for making predictions on new input time series
    output_path
    custom_features_script : str, optional
        Path to custom features script to be used in feature
        generation. Defaults to None.

    Returns
    -------
    """
    fset = xr.open_dataset(featureset_path).load()
    model = joblib.load(model_path)
    return predict_featureset.s(fset, model, output_path)


@app.task()
def forward(x):
    """Workaround for https://github.com/celery/celery/issues/3191.

    Remove when 4.0 is released.

    """
    return x
