import shutil
import tempfile
import uuid
from contextlib import contextmanager
from itertools import cycle, islice
from os.path import join as pjoin
import numpy as np
import xarray as xr

from cesium.featureset import Featureset
from cesium.time_series import TimeSeries


def sample_values(size=51, channels=1):
    times = np.sort(np.random.random(size))
    values = np.array([np.random.normal(size=size) for i in range(channels)])
    errors = np.array([np.random.exponential(size=size)
                       for i in range(channels)])
    if channels == 1:
        values = values[0]
        errors = errors[0]
    return times, values, errors


@contextmanager
def sample_ts_files(size, targets=[None]):
    temp_dir = tempfile.mkdtemp()
    paths = []
    for target in islice(cycle(targets), size):
        t, m, e = sample_values()
        name = str(uuid.uuid4())
        path = pjoin(temp_dir, '{}.nc'.format(name))
        ts = TimeSeries(t, m, e, target=target, path=path, name=name)
        ts.to_netcdf(path)
        paths.append(path)

    yield paths

    shutil.rmtree(temp_dir)


def sample_featureset(size, n_channels=1, features=[], targets=None,
                      labels=None):
    ts_names = np.arange(size).astype('str')
    feat_dict = {f: (['channel', 'name'], [np.random.random(size)
                                           for i in range(n_channels)])
                 for f in features}
    fset = xr.Dataset(feat_dict)
    fset.coords['name'] = ('name', ts_names)
    if targets:
        ts_targets = np.array(list(islice(cycle(targets), size)))
        fset.coords['target'] = ('name', ts_targets)
    if labels:
        fset.name.values = labels

    return Featureset(fset)
