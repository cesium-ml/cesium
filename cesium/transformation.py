import os
import numpy as np
from six import string_types
from . import data_management
from . import time_series as tslib
# TODO remove 'except' for sklearn==0.18.0
try:
    from sklearn.model_selection import train_test_split as sklearn_split
except:
    from sklearn.cross_validation import train_test_split as sklearn_split


__all__ = ['transform_ts_files', 'train_test_split']


def transform_ts_files(time_series, transform_type):
    """Apply some transformation to a list of time series and save outputs.

    Some transformations will affect each time series individually, whereas
    some will split the input data into multiple outputs; in either case the
    time series are returned as a list of lists.

    Parameters
    ----------
    time_series : list of TimeSeries objects
        Input time series to be transformed
    transform_type : str
        Name of transformation to be applied to input time series. Possible
        values are the keys of `TRANSFORM_INFO_DICT`.

    Returns
    -------
    list of lists of TimeSeries objects
    """
    transform, labels = TRANSFORMS_INFO_DICT[transform_type]
    output_ts_lists = transform(time_series)
    if len(labels) != len(output_ts_lists):
        raise ValueError("Number of output time series groups does not match "
                         "the number of labels provided by "
                         "`TRANSFORMS_INFO_DICT`.")
    return output_ts_lists


def train_test_split(time_series, test_size=0.5, train_size=0.5,
                     random_state=None):
    """Splits input time series into training and test sets.

    Samples are stratified based on `TimeSeries.target` if it is a string
    (i.e. a class label). See the `stratify` parameter of
    `sklearn.model_selection` for details.

    Parameters
    ----------
    time_series : list of TimeSeries objects
        Input time series to be split
    test_size : float, optional
        Fraction of data to be included in the test set; defaults to 50/50.
    training_size : float, optional
        Fraction of data to be included in the training set; defaults to 50/50.
    random_state : int or RandomState, optional
        Random number generator seed or state for shuffling of indices.

    Returns
    -------
        tuple (list of training set time series, list of test set time series)
    """
    if len(time_series) <= 1:
        return time_series, []
    inds = np.arange(len(time_series))
    if isinstance(time_series[0].target, string_types):
        stratify = np.array([ts.target for ts in time_series])
    else:
        stratify = None
    train, test = sklearn_split(inds, test_size=test_size,
                                train_size=train_size,
                                random_state=random_state, stratify=stratify)
    return [time_series[i] for i in train], [time_series[j] for j in test]


# Keys=transform names, values=(transform function, [output names])
TRANSFORMS_INFO_DICT = {'Train/Test Split': (train_test_split, ['train',
                                                                'test'])}
