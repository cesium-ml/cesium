import os
from os.path import join as pjoin
import numpy as np
import pandas as pd
import scipy.stats
import dask

from cesium import featurize
from cesium.tests.fixtures import sample_values, sample_ts_files, sample_featureset

import numpy.testing as npt
import pytest


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
FEATURES_CSV_PATH = pjoin(DATA_PATH, "test_features_with_targets.csv")


def test_featurize_files_function(tmpdir):
    """Test featurize function for on-disk time series"""
    with sample_ts_files(size=4, labels=["A", "B"]) as ts_paths:
        fset, labels = featurize.featurize_ts_files(
            ts_paths, features_to_use=["std_err"], scheduler=dask.get
        )
    assert "std_err" in fset
    assert fset.shape == (4, 1)
    npt.assert_array_equal(labels, ["A", "B", "A", "B"])


def test_featurize_time_series_single():
    """Test featurize wrapper function for single time series"""
    t, m, e = sample_values()
    features_to_use = ["amplitude", "std_err"]
    meta_features = {"meta1": 0.5}
    fset = featurize.featurize_time_series(
        t, m, e, features_to_use, meta_features, scheduler=dask.get
    )
    assert fset["amplitude"].values.dtype == np.float64


def test_featurize_time_series_single_multichannel():
    """Test featurize wrapper function for single multichannel time series"""
    n_channels = 3
    t, m, e = sample_values(channels=n_channels)
    features_to_use = ["amplitude", "std_err"]
    meta_features = {"meta1": 0.5}
    fset = featurize.featurize_time_series(
        t, m, e, features_to_use, meta_features, scheduler=dask.get
    )
    assert ("amplitude", 0) in fset.columns
    assert "meta1" in fset.columns


def test_featurize_time_series_multiple():
    """Test featurize wrapper function for multiple time series"""
    n_series = 5
    list_of_series = [sample_values() for i in range(n_series)]
    times, values, errors = (list(x) for x in zip(*list_of_series))
    features_to_use = ["amplitude", "std_err"]
    meta_features = [{"meta1": 0.5}] * n_series
    fset = featurize.featurize_time_series(
        times, values, errors, features_to_use, meta_features, scheduler=dask.get
    )
    npt.assert_array_equal(
        sorted(fset.columns.get_level_values("feature")),
        ["amplitude", "meta1", "std_err"],
    )


def test_featurize_time_series_multiple_multichannel():
    """Test featurize wrapper function for multiple multichannel time series"""
    n_series = 5
    n_channels = 3
    list_of_series = [sample_values(channels=n_channels) for i in range(n_series)]
    times, values, errors = (list(x) for x in zip(*list_of_series))
    features_to_use = ["amplitude", "std_err"]
    meta_features = {"meta1": 0.5}
    fset = featurize.featurize_time_series(
        times, values, errors, features_to_use, meta_features, scheduler=dask.get
    )
    assert ("amplitude", 0) in fset.columns
    assert "meta1" in fset.columns


def test_featurize_time_series_uneven_multichannel():
    """Test featurize wrapper function for uneven-length multichannel data"""
    n_channels = 3
    t, m, e = sample_values(channels=n_channels)
    t = [[t, t[0:-5], t[0:-10]]]
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    e = [[e[0], e[1][0:-5], e[2][0:-10]]]
    features_to_use = ["amplitude", "std_err"]
    meta_features = {"meta1": 0.5}
    fset = featurize.featurize_time_series(
        t, m, e, features_to_use, meta_features, scheduler=dask.get
    )
    assert ("amplitude", 0) in fset.columns
    assert "meta1" in fset.columns


def test_featurize_time_series_custom_functions():
    """Test featurize wrapper function for time series w/ custom functions"""
    n_channels = 3
    t, m, e = sample_values(channels=n_channels)
    features_to_use = ["amplitude", "std_err", "test_f"]
    meta_features = {"meta1": 0.5}
    custom_functions = {"test_f": lambda t, m, e: np.pi}
    fset = featurize.featurize_time_series(
        t,
        m,
        e,
        features_to_use,
        meta_features,
        custom_functions=custom_functions,
        scheduler=dask.get,
    )
    npt.assert_array_equal(fset["test_f", 0], np.pi)
    assert ("amplitude", 0) in fset.columns
    assert "meta1" in fset.columns


def test_featurize_time_series_custom_dask_graph():
    """Test featurize wrapper function for time series w/ custom dask graph"""
    n_channels = 3
    t, m, e = sample_values(channels=n_channels)
    features_to_use = ["amplitude", "std_err", "test_f", "test_meta"]
    meta_features = {"meta1": 0.5}
    custom_functions = {
        "test_f": (lambda x: x.min() - x.max(), "amplitude"),
        "test_meta": (lambda x: 2.0 * x, "meta1"),
    }
    fset = featurize.featurize_time_series(
        t,
        m,
        e,
        features_to_use,
        meta_features,
        custom_functions=custom_functions,
        scheduler=dask.get,
    )
    assert ("amplitude", 0) in fset.columns
    assert ("test_f", 0) in fset.columns
    assert ("test_meta", 0) in fset.columns


def test_featurize_time_series_default_times():
    """Test featurize wrapper function for time series w/ missing times"""
    n_channels = 3
    _, m, e = sample_values(channels=n_channels)
    features_to_use = ["amplitude", "std_err"]
    meta_features = {}
    fset = featurize.featurize_time_series(
        None, m, e, features_to_use, meta_features, scheduler=dask.get
    )

    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    e = [[e[0], e[1][0:-5], e[2][0:-10]]]
    fset = featurize.featurize_time_series(
        None, m, e, features_to_use, meta_features, scheduler=dask.get
    )

    m = m[0][0]
    e = e[0][0]
    fset = featurize.featurize_time_series(
        None, m, e, features_to_use, meta_features, scheduler=dask.get
    )
    assert ("amplitude", 0) in fset.columns


def test_featurize_time_series_default_errors():
    """Test featurize wrapper function for time series w/ missing errors"""
    n_channels = 3
    t, m, _ = sample_values(channels=n_channels)
    features_to_use = ["amplitude", "std_err"]
    meta_features = {}
    fset = featurize.featurize_time_series(
        t, m, None, features_to_use, meta_features, scheduler=dask.get
    )

    t = [[t, t[0:-5], t[0:-10]]]
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    fset = featurize.featurize_time_series(
        t, m, None, features_to_use, meta_features, scheduler=dask.get
    )

    t = t[0][0]
    m = m[0][0]
    fset = featurize.featurize_time_series(
        t, m, None, features_to_use, meta_features, scheduler=dask.get
    )
    assert ("amplitude", 0) in fset.columns


def test_featurize_time_series_pandas_metafeatures():
    """Test featurize function for metafeatures passed as Series/DataFrames."""
    t, m, e = sample_values()
    features_to_use = ["amplitude", "std_err"]
    meta_features = pd.Series({"meta1": 0.5})
    fset = featurize.featurize_time_series(
        t, m, e, features_to_use, meta_features, scheduler=dask.get
    )
    npt.assert_allclose(fset["meta1"], 0.5)

    n_series = 5
    list_of_series = [sample_values() for i in range(n_series)]
    times, values, errors = (list(x) for x in zip(*list_of_series))
    features_to_use = ["amplitude", "std_err"]
    meta_features = pd.DataFrame({"meta1": [0.5] * n_series, "meta2": [0.8] * n_series})
    fset = featurize.featurize_time_series(
        times, values, errors, features_to_use, meta_features, scheduler=dask.get
    )
    npt.assert_allclose(fset["meta1"], 0.5)
    npt.assert_allclose(fset["meta2"], 0.8)


def test_impute():
    """Test imputation of missing Featureset values."""
    fset, labels = sample_featureset(
        5,
        1,
        ["amplitude"],
        ["class1", "class2"],
        names=["a", "b", "c", "d", "e"],
        meta_features=["meta1"],
    )

    imputed = featurize.impute_featureset(fset)
    npt.assert_allclose(fset.amplitude.values, imputed.amplitude.values)
    assert isinstance(imputed, pd.DataFrame)

    fset = fset.copy()  # otherwise .values assignment below does not work
    fset.amplitude.values[0] = np.inf
    fset.amplitude.values[1] = np.nan
    amp_values = fset.amplitude.values[2:]
    other_values = fset.values.T.ravel()[2:]

    imputed = featurize.impute_featureset(fset, strategy="constant", value=None)
    npt.assert_allclose(
        -2 * np.nanmax(np.abs(other_values)), imputed.amplitude.values[0:2]
    )

    imputed = featurize.impute_featureset(fset, strategy="constant", value=-1e4)
    npt.assert_allclose(-1e4, imputed.amplitude.values[0:2])

    imputed = featurize.impute_featureset(fset, strategy="mean")
    npt.assert_allclose(np.mean(amp_values), imputed.amplitude.values[0:2])
    npt.assert_allclose(amp_values, imputed.amplitude.values[2:])

    imputed = featurize.impute_featureset(fset, strategy="median")
    npt.assert_allclose(np.median(amp_values), imputed.amplitude.values[0:2])
    npt.assert_allclose(amp_values, imputed.amplitude.values[2:])

    imputed = featurize.impute_featureset(fset, strategy="most_frequent")
    npt.assert_allclose(
        scipy.stats.mode(amp_values, keepdims=True).mode.item(),
        imputed.amplitude.values[0:2],
    )
    npt.assert_allclose(amp_values, imputed.amplitude.values[2:])

    featurize.impute_featureset(fset, strategy="constant", value=-1e4, inplace=True)
    npt.assert_allclose(-1e4, fset.amplitude.values[0:2])

    with pytest.raises(NotImplementedError):
        featurize.impute_featureset(fset, strategy="blah")


def test_roundtrip_featureset(tmpdir):
    fset_path = os.path.join(str(tmpdir), "test.npz")
    for n_channels in [1, 3]:
        for labels in [["class1", "class2"], []]:
            fset, labels = sample_featureset(
                3,
                n_channels,
                ["amplitude"],
                labels,
                names=["a", "b", "c"],
                meta_features=["meta1"],
            )

            pred_probs = pd.DataFrame(
                np.random.random((len(fset), 2)),
                index=fset.index.values,
                columns=["class1", "class2"],
            )

            featurize.save_featureset(
                fset, fset_path, labels=labels, pred_probs=pred_probs
            )
            fset_loaded, data_loaded = featurize.load_featureset(fset_path)
            npt.assert_allclose(fset.values, fset_loaded.values)
            npt.assert_array_equal(fset.index, fset_loaded.index)
            npt.assert_array_equal(fset.columns, fset_loaded.columns)
            assert isinstance(fset_loaded, pd.DataFrame)
            npt.assert_array_equal(labels, data_loaded["labels"])
            npt.assert_allclose(pred_probs, data_loaded["pred_probs"])
            npt.assert_array_equal(
                pred_probs.columns, data_loaded["pred_probs"].columns
            )


def test_ignore_exceptions():
    import cesium.features.graphs

    def raise_exc(x):
        raise ValueError()

    old_value = cesium.features.graphs.dask_feature_graph["mean"]
    try:
        cesium.features.graphs.dask_feature_graph["mean"] = (raise_exc, "t")
        t, m, e = sample_values()
        features_to_use = ["mean"]
        with pytest.raises(ValueError):
            fset = featurize.featurize_time_series(
                t, m, e, features_to_use, scheduler=dask.get, raise_exceptions=True
            )
        fset = featurize.featurize_time_series(
            t, m, e, features_to_use, scheduler=dask.get, raise_exceptions=False
        )
        assert np.isnan(fset.values).all()
    finally:
        cesium.features.graphs.dask_feature_graph["mean"] = old_value
