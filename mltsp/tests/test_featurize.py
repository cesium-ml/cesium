from mltsp.cfg import config
from mltsp import featurize
from mltsp import manage_data
from nose.tools import with_setup
import numpy.testing as npt
import os
from os.path import join as pjoin
import shutil
import numpy as np
import xarray as xr


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
TS_NO_LABEL_PATHS = [pjoin(DATA_PATH, f) for f in ["dotastro_215153.nc",
                                                   "dotastro_215176.nc"]]
TS_CLASS_PATHS = [pjoin(DATA_PATH, f) for f in
                  ["dotastro_215153_with_class.nc",
                   "dotastro_215176_with_class.nc"]]
TS_TARGET_PATHS = [pjoin(DATA_PATH, f) for f in
                   ["dotastro_215153_with_target.nc",
                    "dotastro_215176_with_target.nc"]]
FEATURES_CSV_PATH = pjoin(DATA_PATH, "test_features_with_targets.csv")
CUSTOM_SCRIPT = pjoin(DATA_PATH, "testfeature1.py")
TEST_OUTPUT_PATHS = [pjoin(cfg['paths']['features_folder'], "test_featureset.nc")]


def copy_classification_test_data():
#    fnames = CLASSIFICATION_TEST_FILES
#    for fname in fnames:
#        if fname.endswith('.py'):
#            shutil.copy(pjoin(DATA_PATH, fname),
#                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
#        elif fname.endswith('.nc'):
#            shutil.copy(pjoin(DATA_PATH, fname), cfg.TS_DATA_FOLDER)
    pass


#def copy_regression_test_data():
#    fnames = REGRESSION_TEST_FILES
#    for fname in fnames:
#        if fname.endswith('.py'):
#            shutil.copy(pjoin(DATA_PATH, fname),
#                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
#        else:
#            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def remove_test_data():
    for f in TEST_OUTPUT_PATHS:
        try:
            os.remove(f)
        except OSError:
            pass


def sample_featureset():
    ds = xr.Dataset({'f1': ('name', [21.0, 23.4]),
                       'f2': ('name', [0.15, 2.31])},
                      coords={'target': ['c1', 'c2']})
    return ds


def sample_time_series(size=51, channels=1):
    times = np.sort(np.random.random(size))
    values = np.array([np.random.normal(size=size) for i in range(channels)])
    errors = np.array([np.random.exponential(size=size)
                       for i in range(channels)])
    if channels == 1:
        values = values[0]
        errors = errors[0]
    return times, values, errors


@with_setup(teardown=remove_test_data)
def test_write_features_to_disk():
    """Test writing features to disk"""
    featurize.write_features_to_disk(sample_featureset(), "test")
    with xr.open_dataset(pjoin(config['paths']['features_folder'],
                               "test_featureset.nc")) as fset:
        npt.assert_equal(sorted(fset.data_vars), ['f1', 'f2'])
        npt.assert_equal(sorted(fset.coords), ['name', 'target'])
        npt.assert_equal(fset['f1'].values, [21.0, 23.4])
        npt.assert_equal(fset['f2'].values, [0.15, 2.31])
        npt.assert_equal(fset['target'].values.astype('U'), ['c1', 'c2'])


@with_setup(copy_classification_test_data, remove_test_data)
def test_already_featurized_data():
    """Test featurize function for pre-featurized data"""
    fset = featurize.load_and_store_feature_data(FEATURES_CSV_PATH,
                                                 featureset_id="test",
                                                 first_N=config['TEST_N'])
    assert("std_err" in fset)
    assert("amplitude" in fset)
    assert(all(class_name in ['class1', 'class2', 'class3']
               for class_name in fset['target']))
    with xr.open_dataset(pjoin(config['paths']['features_folder']
                               "test_featureset.nc")) as loaded:
        assert("std_err" in loaded)
        assert("amplitude" in loaded)
        assert(all(class_name in ['class1', 'class2', 'class3']
                   for class_name in loaded['target']))


@with_setup(teardown=remove_test_data)
def test_featurize_files_function():
    """Test featurize function for on-disk time series"""
    fset = featurize.featurize_data_files(ts_paths=TS_CLASS_PATHS,
                                          features_to_use=["std_err", "f"],
                                          featureset_id="test",
                                          first_N=config['TEST_N'],
                                          custom_script_path=CUSTOM_SCRIPT)
    assert("std_err" in fset.data_vars)
    assert("f" in fset.data_vars)
    assert(all(class_name in ['class1', 'class2']
               for class_name in fset['target'].values))


@with_setup(teardown=remove_test_data)
def test_featurize_files_function_regression_data():
    """Test featurize function for on-disk time series - regression data"""
    fset = featurize.featurize_data_files(ts_paths=TS_TARGET_PATHS,
                                          features_to_use=["std_err", "f"],
                                          featureset_id="test",
                                          first_N=config['TEST_N'],
                                          custom_script_path=CUSTOM_SCRIPT)
    assert("std_err" in fset.data_vars)
    assert("f" in fset.data_vars)
    assert(all(target in [1.0, 3.0] for target in fset['target'].values))


def test_featurize_time_series_single():
    """Test featurize wrapper function for single time series"""
    t, m, e = sample_time_series()
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(fset.target.values, ['class1'])


def test_featurize_time_series_single_multichannel():
    """Test featurize wrapper function for single multichannel time series"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(fset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(fset.target.values, ['class1'])


def test_featurize_time_series_multiple():
    """Test featurize wrapper function for multiple time series"""
    n_series = 5
    list_of_series = [sample_time_series() for i in range(n_series)]
    times, values, errors = [list(x) for x in zip(*list_of_series)]
    features_to_use = ['amplitude', 'std_err']
    targets = np.array(['class1'] * n_series)
    meta_features = [{'meta1': 0.5}] * n_series
    fset = featurize.featurize_time_series(times, values, errors,
                                           features_to_use, targets,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(fset.target.values, ['class1'] * n_series)


def test_featurize_time_series_multiple_multichannel():
    """Test featurize wrapper function for multiple multichannel time series"""
    n_series = 5
    n_channels = 3
    list_of_series = [sample_time_series(channels=n_channels)
                      for i in range(n_series)]
    times, values, errors = [list(x) for x in zip(*list_of_series)]
    features_to_use = ['amplitude', 'std_err']
    targets = np.array(['class1', 'class1', 'class1', 'class2', 'class2'])
    meta_features = {'meta1': 0.5}
    fset = featurize.featurize_time_series(times, values, errors,
                                           features_to_use, targets,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(fset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(fset.target.values, targets)


def test_featurize_time_series_uneven_multichannel():
    """Test featurize wrapper function for uneven-length multichannel data"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    t = [[t, t[0:-5], t[0:-10]]]
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    e = [[e[0], e[1][0:-5], e[2][0:-10]]]
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(fset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(fset.target.values, ['class1'])


def test_featurize_time_series_custom_functions():
    """Test featurize wrapper function for time series w/ custom functions"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err', 'test_f']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    custom_functions = {'test_f': lambda t, m, e: np.mean(m)}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features,
                                           custom_functions=custom_functions,
                                           use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err', 'test_f'])
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(fset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(fset.target.values, ['class1'])


def test_featurize_time_series_custom_dask_graph():
    """Test featurize wrapper function for time series w/ custom dask graph"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err', 'test_f']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    custom_functions = {'test_f': (lambda x: x.min() - x.max(), 'amplitude')}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features,
                                           custom_functions=custom_functions,
                                           use_celery=False)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err', 'test_f'])
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(fset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(fset.target.values, ['class1'])


def test_featurize_time_series_default_times():
    """Test featurize wrapper function for time series w/ missing times"""
    n_channels = 3
    _, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {}
    fset = featurize.featurize_time_series(None, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    e = [[e[0], e[1][0:-5], e[2][0:-10]]]
    fset = featurize.featurize_time_series(None, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    m = m[0][0]
    e = e[0][0]
    fset = featurize.featurize_time_series(None, m, e, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, [0])


def test_featurize_time_series_default_errors():
    """Test featurize wrapper function for time series w/ missing errors"""
    n_channels = 3
    t, m, _ = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {}
    fset = featurize.featurize_time_series(t, m, None, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    t = [[t, t[0:-5], t[0:-10]]]
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    fset = featurize.featurize_time_series(t, m, None, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, np.arange(n_channels))
    t = t[0][0]
    m = m[0][0]
    fset = featurize.featurize_time_series(t, m, None, features_to_use, target,
                                           meta_features, use_celery=False)
    npt.assert_array_equal(fset.channel, [0])


def test_featurize_time_series_celery():
    """Test `featurize_time_series` with Celery.

    The actual featurization work is being done by
    `featurize_tools.featurize_single_time_series`, which is called by both the
    Celery and non-Celery versions; thus, besides the above tests, we only need
    to check that the Celery task is configured properly."""
    t, m, e = sample_time_series()
    features_to_use = ['amplitude', 'std_err', 'test_f']
    # This ideally would be a dummy lambda function but celery can't do that
    from mltsp.science_features import lomb_scargle_fast as lsf
    custom_functions = {'test_f': lsf.lomb_scargle_fast_period}
    target = 'class1'
    meta_features = {'meta1': 0.5}
    fset = featurize.featurize_time_series(t, m, e, features_to_use, target,
                                           meta_features,
                                           custom_functions=custom_functions,
                                           use_celery=True)
    npt.assert_array_equal(sorted(fset.data_vars),
                           ['amplitude', 'meta1', 'std_err', 'test_f'])
    npt.assert_array_equal(fset.target.values, ['class1'])
