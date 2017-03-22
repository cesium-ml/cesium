import shutil
import tempfile
import uuid
from contextlib import contextmanager
from itertools import cycle, islice
from os.path import join as pjoin
import numpy as np
import pandas as pd

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
        path = pjoin(temp_dir, '{}.npz'.format(name))
        ts = TimeSeries(t, m, e, target=target, path=path, name=name)
        ts.to_npz(path)
        paths.append(path)

    yield paths

    shutil.rmtree(temp_dir)


def sample_featureset(size, n_channels=1, features=['mean'], targets=None,
                      names=None, meta_features=[]):
    ts_names = np.arange(size).astype('str')
    index = pd.MultiIndex.from_tuples([(f, i) for f in features for i in range(n_channels)],
                                      names=['feature', 'channel'])
    fset = pd.DataFrame(np.random.random((size, len(features) * n_channels)),
                        columns=index)
    if targets:
        targets = np.array(list(islice(cycle(targets), size)))
    if names:
        fset.index = names
    for feat in meta_features:
        fset[feat] = np.random.random(size)

    return fset, targets
