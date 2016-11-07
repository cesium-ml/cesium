import os
from os.path import join as pjoin
from nose.tools import with_setup
import numpy as np
import numpy.testing as npt
from cesium.time_series import TimeSeries
from cesium import transformation
from cesium.tests.fixtures import sample_values


def test_train_test_split():
    # Mock out unevenly-labeled test data: 4 class1, 8 class2
    n_class1 = 4
    n_class2 = 8
    transform_type = "Train/Test Split"
    time_series = []
    for i in range(n_class1):
        t, m, e = sample_values()
        time_series.append(TimeSeries(t, m, e, target='class1'))
    for i in range(n_class2):
        t, m, e = sample_values()
        time_series.append(TimeSeries(t, m, e, target='class2'))
    np.random.seed(0)
    train, test = transformation.transform_ts_files(time_series,
                                                    transform_type)
    npt.assert_equal(sum(ts.target == 'class1' for ts in train), 1 * n_class1 / 2)
    npt.assert_equal(sum(ts.target == 'class1' for ts in test), n_class1 / 2)
    npt.assert_equal(sum(ts.target == 'class2' for ts in train), 1 * n_class2 / 2)
    npt.assert_equal(sum(ts.target == 'class2' for ts in test), n_class2 / 2)

def test_transform_ts_files():
    n_class1 = 4
    n_class2 = 8
    transform_type = "Train/Test Split"
    time_series = []
    class1samples = np.array([sample_values() for i in range(n_class1)])
    class2samples = np.array([sample_values() for i in range(n_class2)])
    time_series.extend([TimeSeries(x[0],x[1],x[2],target='class1') for x in class1samples])
    time_series.extend([TimeSeries(x[0],x[1],x[2],target='class2') for x in class2samples])
    output = transformation.transform_ts_files(time_series, transform_type)
    npt.assert_equal(len(output), 2)

def test_train_test_split_basecase():
    npt.assert_equal(transformation.train_test_split([]), ([], []))

def test_train_test_split_ratios():
    n_class1 = 4
    n_class2 = 8
    transform_type = "Train/Test Split"
    time_series = []
    class1samples = np.array([sample_values() for i in range(n_class1)])
    class2samples = np.array([sample_values() for i in range(n_class2)])
    time_series.extend([TimeSeries(x[0], x[1], x[2], target='class1') for x in class1samples])
    time_series.extend([TimeSeries(x[0], x[1], x[2], target='class2') for x in class2samples])
    outputs = transformation.train_test_split(time_series, test_size = 0.5, train_size= 0.5)
    npt.assert_equal(len(outputs[1]), len(time_series)/2)
    npt.assert_equal(len(outputs[0]), len(time_series)/2)