import os
import numpy as np
from .cfg import config
from mltsp import data_management
from mltsp import time_series as tslib
# TODO remove 'except' for sklearn==0.18.0
try:
    from sklearn.model_selection import train_test_split as sklearn_split
except:
    from sklearn.cross_validation import train_test_split as sklearn_split


def transform_ts_files(input_paths, dataset_keys, transform_type):
    input_time_series = [tslib.from_netcdf(path) for path in input_paths]
    transform, _ = TRANSFORMS_INFO_DICT[transform_type]
    output_ts_lists = transform(input_time_series)

    if len(dataset_keys) != len(output_ts_lists):
        raise ValueError("Transform produced {} datasets; {} output dataset "
                         "IDs were provided.".format(len(output_ts_lists),
                                                     len(dataset_keys)))
    for ts_list, ds_name in zip(output_ts_lists, dataset_keys):
        for ts in ts_list:
            ts_fname = '{}_{}.nc'.format(ds_name, ts.name)
            ts.to_netcdf(os.path.join(config['paths']['ts_data_folder'],
                                      ts_fname))
    return output_ts_lists


def train_test_split(time_series, test_size=0.5, train_size=0.5,
                     random_state=None):
    if len(time_series) <= 1:
        return time_series, []
    inds = np.arange(len(time_series))
    if isinstance(time_series[0].target, str):
        stratify = np.array([ts.target for ts in time_series])
    else:
        stratify = None
    train, test = sklearn_split(inds, test_size=test_size,
                                train_size=train_size,
                                random_state=random_state, stratify=stratify)
    return [time_series[i] for i in train], [time_series[j] for j in test]


# TODO what do we think of this as the interface w/ the front end?
# Keys=transform names, values=(transform function, [output names])
TRANSFORMS_INFO_DICT = {'Train/Test Split': (train_test_split, ['train',
                                                                'test'])}
