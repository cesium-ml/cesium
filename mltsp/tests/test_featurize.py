from mltsp import featurize
from mltsp import featurize_tools
from mltsp import cfg
from nose.tools import with_setup
import numpy.testing as npt
import os
from os.path import join as pjoin
import shutil
import numpy as np
import xray


DATA_PATH = pjoin(os.path.dirname(__file__), "data")
CLASSIFICATION_TEST_FILES = ["asas_training_subset_classes_with_metadata.dat",
                             "asas_training_subset.tar.gz", "testfeature1.py",
                             "test_features_with_targets.csv",
                             "test_features_with_targets.csv",
                             "247327.dat"]
REGRESSION_TEST_FILES = ["asas_training_subset_targets.dat",
                         "asas_training_subset.tar.gz", "testfeature1.py"]


def copy_classification_test_data():
    fnames = CLASSIFICATION_TEST_FILES
    for fname in fnames:
        if fname.endswith('.py'):
            shutil.copy(pjoin(DATA_PATH, fname),
                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def copy_regression_test_data():
    fnames = REGRESSION_TEST_FILES
    for fname in fnames:
        if fname.endswith('.py'):
            shutil.copy(pjoin(DATA_PATH, fname),
                        cfg.CUSTOM_FEATURE_SCRIPT_FOLDER)
        else:
            shutil.copy(pjoin(DATA_PATH, fname), cfg.UPLOAD_FOLDER)


def remove_test_data():
    fnames = CLASSIFICATION_TEST_FILES + REGRESSION_TEST_FILES
    for fname in fnames:
        for data_dir in [cfg.UPLOAD_FOLDER, cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                         cfg.FEATURES_FOLDER]:
            try:
                os.remove(pjoin(data_dir, fname))
            except OSError:
                pass


def test_headerfile_parser():
    """Test header file parsing."""
    targets, metadata = featurize_tools.parse_headerfile(
        pjoin(DATA_PATH, "sample_classes_with_metadata_headerfile.dat"))
    npt.assert_array_equal(metadata.keys(), ["meta1", "meta2", "meta3"])
    npt.assert_equal(targets.loc["237022"], "W_Ursae_Maj")
    npt.assert_almost_equal(metadata.loc["230395"].meta1, 0.270056761691)


def sample_featureset():
    ds = xray.Dataset({'f1': ('name', [21.0, 23.4]),
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


def test_write_features_to_disk():
    """Test writing features to disk"""
    featurize.write_features_to_disk(sample_featureset(), "test")
    featureset = xray.open_dataset(pjoin(cfg.FEATURES_FOLDER,
                                         "test_featureset.nc"))
    npt.assert_equal(sorted(featureset.data_vars), ['f1', 'f2'])
    npt.assert_equal(sorted(featureset.coords), ['name', 'target'])
    npt.assert_equal(featureset['f1'].values, [21.0, 23.4])
    npt.assert_equal(featureset['f2'].values, [0.15, 2.31])
    npt.assert_equal(featureset['target'].values, [b'c1', b'c2'])


@with_setup(copy_classification_test_data, remove_test_data)
def test_main_featurize_function():
    """Test main featurize function"""
    featureset = featurize.featurize_data_file(header_path=pjoin(
        cfg.UPLOAD_FOLDER, "asas_training_subset_classes_with_metadata.dat"),
        data_path=pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "f"], featureset_id="test",
        first_N=cfg.TEST_N,
        custom_script_path=pjoin(cfg.CUSTOM_FEATURE_SCRIPT_FOLDER,
                                 "testfeature1.py"))
    assert("std_err" in featureset.data_vars)
    assert("f" in featureset.data_vars)
    assert(all(class_name in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj',
                              'Delta_Scuti']
               for class_name in featureset['target'].values))


@with_setup(copy_classification_test_data, remove_test_data)
def test_main_featurize_function_single_ts():
    """Test main featurize function for single time series"""
    featureset = featurize.featurize_data_file(header_path=pjoin(
        cfg.UPLOAD_FOLDER, "asas_training_subset_classes_with_metadata.dat"),
        data_path=pjoin(cfg.UPLOAD_FOLDER, "247327.dat"),
        features_to_use=["std_err", "f"], featureset_id="test",
        first_N=cfg.TEST_N)
    assert("std_err" in featureset.data_vars)
    assert("f" in featureset.data_vars)
    assert(all(class_name in ['Mira', 'Herbig_AEBE', 'Beta_Lyrae',
                              'Classical_Cepheid', 'W_Ursae_Maj',
                              'Delta_Scuti']
               for class_name in featureset['target'].values))


@with_setup(copy_classification_test_data, remove_test_data)
def test_already_featurized_data():
    """Test featurize function for pre-featurized data"""
    featureset = featurize.load_and_store_feature_data(
        pjoin(cfg.UPLOAD_FOLDER, "test_features_with_targets.csv"),
        featureset_id="test", first_N=cfg.TEST_N)
    assert("std_err" in featureset)
    assert("amplitude" in featureset)
    assert(all(class_name in ['class1', 'class2', 'class3']
               for class_name in featureset['target']))


@with_setup(copy_regression_test_data, remove_test_data)
def test_main_featurize_function_regression_data():
    """Test main featurize function - regression data"""
    featureset = featurize.featurize_data_file(
        header_path=pjoin(cfg.UPLOAD_FOLDER,
                          "asas_training_subset_targets.dat"),
        data_path=pjoin(cfg.UPLOAD_FOLDER, "asas_training_subset.tar.gz"),
        features_to_use=["std_err", "freq1_freq", "amplitude"],
        featureset_id="test", first_N=cfg.TEST_N, custom_script_path=None)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ["amplitude", "freq1_freq", "std_err"])
    assert(all(isinstance(target, (float, np.float))
               for target in featureset['target'].values))


def test_featurize_time_series_single():
    """Test featurize wrapper function for single time series"""
    t, m, e = sample_time_series()
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    featureset = featurize.featurize_time_series(t, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(featureset.target.values, ['class1'])


def test_featurize_time_series_single_multichannel():
    """Test featurize wrapper function for single multichannel time series"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    featureset = featurize.featurize_time_series(t, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(featureset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(featureset.target.values, ['class1'])


def test_featurize_time_series_multiple():
    """Test featurize wrapper function for multiple time series"""
    n_series = 5
    list_of_series = [sample_time_series() for i in range(n_series)]
    times, values, errors = [list(x) for x in zip(*list_of_series)]
    features_to_use = ['amplitude', 'std_err']
    targets = np.array(['class1'] * n_series)
    meta_features = [{'meta1': 0.5}] * n_series
    featureset = featurize.featurize_time_series(times, values, errors,
                                                 features_to_use, targets,
                                                 meta_features)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(featureset.target.values, ['class1'] * n_series)


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
    featureset = featurize.featurize_time_series(times, values, errors,
                                                 features_to_use, targets,
                                                 meta_features)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(featureset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(featureset.target.values, targets)


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
    featureset = featurize.featurize_time_series(t, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err'])
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(featureset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(featureset.target.values, ['class1'])


def test_featurize_time_series_custom_functions():
    """Test featurize wrapper function for time series w/ custom functions"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err', 'test_f']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    custom_functions = {'test_f': lambda t, m, e: np.mean(m)}
    featureset = featurize.featurize_time_series(t, m, e, features_to_use,
                                                 target, meta_features,
                                                 custom_functions=custom_functions)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err', 'test_f'])
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(featureset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(featureset.target.values, ['class1'])


def test_featurize_time_series_custom_dask_graph():
    """Test featurize wrapper function for time series w/ custom dask graph"""
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err', 'test_f']
    target = 'class1'
    meta_features = {'meta1': 0.5}
    custom_functions = {'test_f': (lambda x: 2*x, 'amplitude')}
    featureset = featurize.featurize_time_series(t, m, e, features_to_use,
                                                 target, meta_features,
                                                 custom_functions=custom_functions)
    npt.assert_array_equal(sorted(featureset.data_vars),
                           ['amplitude', 'meta1', 'std_err', 'test_f'])
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    npt.assert_array_equal(sorted(featureset.amplitude.coords),
                           ['channel', 'name', 'target'])
    npt.assert_array_equal(featureset.target.values, ['class1'])


def test_featurize_time_series_default_times():
    """Test featurize wrapper function for time series w/ missing times"""
    n_channels = 3
    _, m, e = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {}
    featureset = featurize.featurize_time_series(None, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    e = [[e[0], e[1][0:-5], e[2][0:-10]]]
    featureset = featurize.featurize_time_series(None, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    m = m[0][0]
    e = e[0][0]
    featureset = featurize.featurize_time_series(None, m, e, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, [0])


def test_featurize_time_series_default_errors():
    """Test featurize wrapper function for time series w/ missing errors"""
    n_channels = 3
    t, m, _ = sample_time_series(channels=n_channels)
    features_to_use = ['amplitude', 'std_err']
    target = 'class1'
    meta_features = {}
    featureset = featurize.featurize_time_series(t, m, None, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    t = [[t, t[0:-5], t[0:-10]]]
    m = [[m[0], m[1][0:-5], m[2][0:-10]]]
    featureset = featurize.featurize_time_series(t, m, None, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, np.arange(n_channels))
    t = t[0][0]
    m = m[0][0]
    featureset = featurize.featurize_time_series(t, m, None, features_to_use,
                                                 target, meta_features)
    npt.assert_array_equal(featureset.channel, [0])
