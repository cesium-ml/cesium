import os
import numpy as np
from mltsp import cfg
from mltsp import data_management
from mltsp import time_series as tslib
from sklearn import model_selection


def transform_ts_files(input_paths, output_dataset_names, transform):
    # TODO database key instead of paths? or should that be separate?
    input_time_series = [tslib.from_netcdf(path) for path in input_paths]
    output_ts_lists = transform(input_time_series)

    if len(output_dataset_names) != len(output_ts_lists):
        raise ValueError("Transform produced {} datasets; {} output labels"
                         " were provided.".format(len(output_ts_lists),
                                                  len(output_dataset_names)))
    for ts_list, ds_name in zip(output_ts_lists, output_dataset_names):
        #ds_key = data_management.add_dataset_to_db(name, project_id)
# TODO better way to organize files?
# should this wait for next PR w/ filesystem abstraction layer?
        for ts in ts_list:
            ts_fname = '{}_{}.nc'.format(ds_name, ts.name)
            ts.to_netcdf(os.path.join(cfg.TS_DATA_FOLDER, ts_fname))
    return output_ts_lists


def train_test_split(time_series, test_size=None, train_size=None,
                     random_state=None):
    if len(time_series) <= 1:
        return time_series, []
    inds = np.arange(len(time_series))
    if isinstance(time_series[0].target, str):
        stratify = np.array([ts.target for ts in time_series])
    else:
        stratify = None
    train, test = model_selection.train_test_split(inds, test_size=test_size,
                                                   train_size=train_size,
                                                   random_state=random_state,
                                                   stratify=stratify)
    return [time_series[i] for i in train], [time_series[j] for j in test]
