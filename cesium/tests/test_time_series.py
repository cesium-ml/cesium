import os
from uuid import uuid4
import numpy.testing as npt
import numpy as np
from cesium import time_series
from cesium.time_series import TimeSeries


def sample_time_series(size=51, channels=1):
    times = np.array(
        [np.sort(np.random.random(size)) for i in range(channels)]
    ).squeeze()
    values = np.array([np.random.normal(size=size) for i in range(channels)]).squeeze()
    errors = np.array(
        [np.random.exponential(size=size) for i in range(channels)]
    ).squeeze()
    return times, values, errors


def test__compatible_shapes():
    compat = time_series._compatible_shapes

    assert compat(np.arange(5), np.arange(5))
    assert not compat(np.arange(5), np.arange(6))

    assert compat([np.arange(5)] * 5, [np.arange(5)] * 5)
    assert not compat([np.arange(5)] * 5, [np.arange(5)] * 6)
    assert not compat([np.arange(5)] * 5, [np.arange(6)] * 5)
    assert not compat(np.arange(5), [np.arange(6)] * 5)

    assert compat([[0, 1], [0, 1]], [[0, 1], [0, 1]])
    assert not compat([[0, 1], [0, 1]], [[0], [0, 1]])

    assert compat([0, 1], np.arange(2))


def assert_ts_equal(ts1, ts2):
    for x1, x2 in zip(
        (ts1.time, ts1.measurement, ts1.error), (ts2.time, ts2.measurement, ts2.error)
    ):
        assert type(x1) == type(x2)
        if isinstance(x1, np.ndarray):
            assert np.array_equal(x1, x2)
        else:
            assert all(np.array_equal(x1_i, x2_i) for x1_i, x2_i in zip(x1, x2))
    assert ts1.label == ts2.label
    assert ts1.meta_features == ts2.meta_features
    assert ts1.name == ts2.name


def test_time_series_init_1d():
    t, m, e = sample_time_series(channels=1)
    ts = TimeSeries(t, m, e)
    assert ts.time.shape == t.shape and np.allclose(ts.time, t)
    assert ts.measurement.shape == m.shape and np.allclose(ts.measurement, m)
    assert ts.error.shape == e.shape and np.allclose(ts.error, e)
    assert ts.n_channels == 1


def test_time_series_init_2d():
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    ts = TimeSeries(t, m, e)
    assert ts.time.shape == t.shape and np.allclose(ts.time, t)
    assert ts.measurement.shape == m.shape and np.allclose(ts.measurement, m)
    assert ts.error.shape == e.shape and np.allclose(ts.error, e)
    assert ts.n_channels == n_channels

    ts = TimeSeries(t[0], m, e[0])
    assert ts.time.shape == m.shape and np.allclose(ts.time[0], t[0])
    assert ts.measurement.shape == m.shape and np.allclose(ts.measurement, m)
    assert ts.error.shape == m.shape and np.allclose(ts.error[0], e[0])
    assert ts.n_channels == n_channels


def test_time_series_init_ragged():
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    t = [t[i][0 : i + 2] for i in range(len(t))]
    m = [m[i][0 : i + 2] for i in range(len(m))]
    e = [e[i][0 : i + 2] for i in range(len(e))]
    ts = TimeSeries(t, m, e)
    assert all(np.allclose(ts.time[i], t[i]) for i in range(len(t)))
    assert all(np.allclose(ts.measurement[i], m[i]) for i in range(len(t)))
    assert all(np.allclose(ts.error[i], e[i]) for i in range(len(t)))
    assert ts.n_channels == n_channels


def test_time_series_default_values():
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    ts = TimeSeries(None, m[0], None)
    npt.assert_allclose(
        ts.time, np.linspace(0.0, time_series.DEFAULT_MAX_TIME, m.shape[1])
    )
    npt.assert_allclose(
        ts.error, np.repeat(time_series.DEFAULT_ERROR_VALUE, m.shape[1])
    )
    assert ts.n_channels == 1

    ts = TimeSeries(None, m, None)
    npt.assert_allclose(
        ts.time[0], np.linspace(0.0, time_series.DEFAULT_MAX_TIME, m.shape[1])
    )
    npt.assert_allclose(
        ts.error[0], np.repeat(time_series.DEFAULT_ERROR_VALUE, m.shape[1])
    )
    assert ts.n_channels == n_channels

    t = [t[i][0 : i + 2] for i in range(len(t))]
    m = [m[i][0 : i + 2] for i in range(len(m))]
    e = [e[i][0 : i + 2] for i in range(len(e))]
    ts = TimeSeries(None, m, None)
    for i in range(n_channels):
        npt.assert_allclose(
            ts.time[i], np.linspace(0.0, time_series.DEFAULT_MAX_TIME, len(m[i]))
        )
        npt.assert_allclose(
            ts.error[i], np.repeat(time_series.DEFAULT_ERROR_VALUE, len(m[i]))
        )
    assert ts.n_channels == n_channels


def test_channels_iterator():
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    ts = TimeSeries(t[0], m[0], e[0])
    for t_i, m_i, e_i in ts.channels():
        npt.assert_allclose(t_i, t[0])
        npt.assert_allclose(m_i, m[0])
        npt.assert_allclose(e_i, e[0])

    ts = TimeSeries(t, m, e)
    for (t_i, m_i, e_i), i in zip(ts.channels(), range(n_channels)):
        npt.assert_allclose(t_i, t[i])
        npt.assert_allclose(m_i, m[i])
        npt.assert_allclose(e_i, e[i])

    t = [t[i][0 : i + 2] for i in range(len(t))]
    m = [m[i][0 : i + 2] for i in range(len(m))]
    e = [e[i][0 : i + 2] for i in range(len(e))]
    ts = TimeSeries(t, m, e)
    for (t_i, m_i, e_i), i in zip(ts.channels(), range(n_channels)):
        npt.assert_allclose(t_i, t[i])
        npt.assert_allclose(m_i, m[i])
        npt.assert_allclose(e_i, e[i])


def test_time_series_npz(tmpdir):
    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)

    ts = TimeSeries(t[0], m[0], e[0])
    ts_path = os.path.join(str(tmpdir), str(uuid4()) + ".npz")
    ts.save(ts_path)
    ts_loaded = time_series.load(ts_path)
    assert_ts_equal(ts, ts_loaded)

    ts = TimeSeries(t[0], m, e[0])
    ts_path = os.path.join(str(tmpdir), str(uuid4()) + ".npz")
    ts.save(ts_path)
    ts_loaded = time_series.load(ts_path)
    assert_ts_equal(ts, ts_loaded)

    t = [t[i][0 : i + 2] for i in range(len(t))]
    m = [m[i][0 : i + 2] for i in range(len(m))]
    e = [e[i][0 : i + 2] for i in range(len(e))]
    ts = TimeSeries(t, m, e)
    ts_path = os.path.join(str(tmpdir), str(uuid4()) + ".npz")
    ts.save(ts_path)
    ts_loaded = time_series.load(ts_path)
    assert_ts_equal(ts, ts_loaded)


def test_time_series_sort():
    t, m, e = sample_time_series(channels=1)
    t[:2] = t[1::-1]
    ts = TimeSeries(t, m, e)
    npt.assert_allclose(ts.time, np.sort(t))
    npt.assert_allclose(ts.measurement, m[np.argsort(t)])
    npt.assert_allclose(ts.error, e[np.argsort(t)])

    n_channels = 3
    t, m, e = sample_time_series(channels=n_channels)
    t[:, :2] = t[:, 1::-1]
    ts = TimeSeries(t, m, e)
    for i in range(len(m)):
        npt.assert_allclose(ts.time[i], np.sort(t[i]))
        npt.assert_allclose(ts.measurement[i], m[i][np.argsort(t[i])])
        npt.assert_allclose(ts.error[i], e[i][np.argsort(t[i])])

    ts = TimeSeries(t[0], m, e[0])
    for i in range(len(m)):
        npt.assert_allclose(ts.time[i], np.sort(t[0]))
        npt.assert_allclose(ts.measurement[i], m[i][np.argsort(t[0])])
        npt.assert_allclose(ts.error[i], e[0][np.argsort(t[0])])
