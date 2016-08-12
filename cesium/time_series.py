import copy
from collections import Iterable
import netCDF4
import numpy as np
import pandas as pd
import xarray as xr


__all__ = ['from_netcdf', 'TimeSeries', 'DEFAULT_MAX_TIME',
           'DEFAULT_ERROR_VALUE']


DEFAULT_MAX_TIME = 1.0
DEFAULT_ERROR_VALUE = 1e-4


def _ndim(x):
    """Return number of dimensions for a (possibly ragged) array."""
    n = 0
    while isinstance(x, Iterable):
        x = x[0]
        n += 1
    return n


def _compatible_shapes(x, y):
    """Check recursively that iterables x and y (and each iterable contained
    within, if applicable), have compatible sizes.
    """
    if hasattr(x, 'shape') and hasattr(y, 'shape'):
        return x.shape == y.shape
    else:
        return (len(x) == len(y) and all(np.shape(x_i) == np.shape(y_i)
                                         for x_i, y_i in zip(x, y)))


def _default_values_like(old_values, value=None, upper=None):
    """Creates a range of default values with the same shape as the input
    `old_values`. If `value` is provided then each entry will equal `value`;
    if `upper` is provided then the values will be linearly-spaced from 0 to
    `upper`.

    Parameters
    ----------
    old_values : (n,) or (p,n) array or list of (n,) arrays
        Input array(s), typically time series measurements for which default
        time or error values need to be inferred.
    value : float, optional
        Value that each output entry will be set to (omitted if `upper` is
        provided).
    upper : float, optional
        Upper bound of range of linearly-spaced output entries (omitted if
        `value` is provided).
    """
    if value and upper:
        raise ValueError("Only one of `value` or `upper` may be proivded.")
    elif value is not None:
        lower = value
        upper = value
    elif upper is not None:
        lower = 0.
    else:
        raise ValueError("Either `value` or `upper` must be provided.")

    new_values = copy.deepcopy(old_values)
    if _ndim(old_values) == 1 or (isinstance(old_values, np.ndarray) and 1 in
                                  old_values.shape):
        new_values[:] = np.linspace(lower, upper, len(new_values))
    else:
        for new_array in new_values:
            new_array[:] = np.linspace(lower, upper, len(new_array))

    return new_values


def _make_array_if_possible(x):
    """Helper function to cast (1, n) arrays to (n,) arrrays, or uniform lists
    of arrays to (p, n) arrays.
    """
    try:
        x = np.asfarray(x).squeeze()
    except ValueError:
        pass
    return x


def from_netcdf(netcdf_path):
    """Load serialized TimeSeries from netCDF file."""
    with netCDF4.Dataset(netcdf_path) as ds:
        channels = list(ds.groups)

        # First channel group stores time series metadata
        metadata = ds[channels[0]]
        target = None
        name = None
        path = None
        if hasattr(metadata, 'target'):
            target = metadata.target
        if hasattr(metadata, 'ts_name'):
            name = metadata.ts_name
        if hasattr(metadata, 'ts_path'):
            path = metadata.ts_path
        meta_features = {k: v for k, v in zip(metadata['feature'],
                                              metadata['meta_features'])}

        t = []
        m = []
        e = []
        for channel in channels:
            m.append(ds[channel]['measurement'][:])
            if 'time' in ds[channel].variables:
                t.append(ds[channel]['time'][:])
            if 'error' in ds[channel].variables:
                e.append(ds[channel]['error'][:])

    return TimeSeries(t, m, e, target, meta_features, name, path)


class TimeSeries:
    """Class representing a single time series of measurements and metadata.
    
    A `TimeSeries` object encapsulates a single set of time-domain
    measurements, along with any metadata describing the observation.
    Typically the observations will consist of times, measurements, and
    (optionally) measurement errors. The measurements can be scalar- or
    vector-valued (i.e., "multichannel"); for multichannel measurements, the 
    times and errors can also be vector-valued, or they can be shared across
    all channels of measurement. 

    Attributes
    ----------
    time : (n,) or (p, n) array or list of (n,) arrays
        Array(s) of times corresponding to measurement values. If `measurement`
        is two-dimensional, this can be one-dimensional (same times for each
        channel) or two-dimensional (different times for each channel). If
        `time` is one-dimensional then it will be broadcast to match
        `measurement.shape`.
    measurement : (n,) or (p, n) array or list of (n,) arrays
        Array(s) of measurement values; can be two-dimensional for
        multichannel data. In the case of multichannel data with different
        numbers of measurements for each channel, `measurement` will be a list
        of arrays instead of a single two-dimensional array.
    error : (n,) or (p, n) array or list of (n,) arrays
        Array(s) of measurement errors for each value. If `measurement` is
        two-dimensional, this can be one-dimensional (same times for each
        channel) or two-dimensional (different times for each channel).
        If `error` is one-dimensional then it will be broadcast match
        `measurement.shape`.
    target : str, float, or None
        Class label or target value for the given time series (if applicable).
    meta_features : dict
        Dictionary of feature names/values specified independently of the
        featurization process in `featurize`.
    name : str or None
        Identifying name/label for the given time series (if applicable). 
        Typically the name of the raw data file from which the time series was
        created.
    path : str or None
        Path to the file where the time series is stored on disk (if
        applicable).
    channel_names : list of str
        List of names of channels of measurement; by default these are simply
        `channel_{i}`, but can be arbitrary depending on the nature of the
        different measurement channels.
    """
    def __init__(self, t=None, m=None, e=None, target=None, meta_features={},
                 name=None, path=None, channel_names=None):
        """Create a `TimeSeries` object from measurement values/metadata.

        See `TimeSeries` documentation for parameter values.
        """
        if t is None and m is None:
            raise ValueError("Either times or measurements must be provided.")
        elif m is None:
            m = _default_values_like(t, value=np.nan)

        # If m is 1-dimensional, so are t and e
        if _ndim(m) == 1:
            self.n_channels = 1
            if t is None:
                t = _default_values_like(m, upper=DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m, value=DEFAULT_ERROR_VALUE)
        # If m is 2-dimensional, t and e could be 1d or 2d; default is 1d
        elif isinstance(m, np.ndarray) and m.ndim == 2:
            self.n_channels = len(m)
            if t is None:
                t = _default_values_like(m[0], upper=DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m[0], value=DEFAULT_ERROR_VALUE)
        # If m is ragged (list of 1d arrays), t and e should also be ragged
        elif _ndim(m) == 2:
            self.n_channels = len(m)
            if t is None:
                t = _default_values_like(m, upper=DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m, value=DEFAULT_ERROR_VALUE)
        else:
            raise ValueError("m must be a 1D or 2D array, or a 2D list of"
                             " arrays.")

        self.time = _make_array_if_possible(t)
        self.measurement = _make_array_if_possible(m)
        self.error = _make_array_if_possible(e)

        if _ndim(self.time) == 1 and _ndim(self.measurement) == 2:
            if isinstance(self.measurement, np.ndarray):
                self.time = np.broadcast_to(self.time, self.measurement.shape)
            else:
                raise ValueError("Times for each channel must be provided if m"
                                 " is a ragged array.")
                                 
        if _ndim(self.error) == 1 and _ndim(self.measurement) == 2:
            if isinstance(self.measurement, np.ndarray):
                self.error = np.broadcast_to(self.error, self.measurement.shape)
            else:
                raise ValueError("Errors for each channel must be provided if m"
                                 " is a ragged array.")
                                 
        if not (_compatible_shapes(self.measurement, self.time) and
                _compatible_shapes(self.measurement, self.error)):
            raise ValueError("times, values, errors are not of compatible"
                             " types/sizes. Please refer to the docstring"
                             " for list of allowed input types.")

        self.target = target
        self.meta_features = dict(meta_features)
        self.name = name
        self.path = path
        if channel_names is None:
            self.channel_names = ["channel_{}".format(i)
                                  for i in range(self.n_channels)]
        else:
            self.channel_names = channel_names

    def channels(self):
        """Iterates over measurement channels (whether one or multiple)."""
        t_channels = self.time
        m_channels = self.measurement
        e_channels = self.error
        if isinstance(self.time, np.ndarray) and self.time.ndim == 1:
            t_channels = [self.time] * self.n_channels
        if (isinstance(self.measurement, np.ndarray)
            and self.measurement.ndim == 1):
            m_channels = [self.measurement] * self.n_channels
        if isinstance(self.error, np.ndarray) and self.error.ndim == 1:
            e_channels = [self.error] * self.n_channels
        return zip(t_channels, m_channels, e_channels)

    def to_netcdf(self, path=None):
        """Store TimeSeries object as a single netCDF.

        Each channel of measurements is stored in a separate HDF5 group; metadata
        describing the whole time series is stored in the group corresponding to
        the first channel.

        If `path` is omitted then the `path` attribute from the TimeSeries object
        is used.
        """
        if path is None:
            path = self.path

        for (t_i, m_i, e_i), channel in zip(self.channels(),
                                            range(self.n_channels)):
            dataset = xr.Dataset({'measurement': (['i'], m_i)})
            # Store meta_features, name, target in first group only
            if channel == 0:
                meta_feat_series = pd.Series(self.meta_features)
                dataset['meta_features'] = xr.DataArray(meta_feat_series,
                                                        dims='feature')
                if self.name:
                    dataset.attrs['ts_name'] = self.name
                if self.path:
                    dataset.attrs['ts_path'] = self.path
                if self.target:
                    dataset.attrs['target'] = self.target
            # If time is a 1d array, only store once (in the first group)
            if isinstance(self.time, np.ndarray) and self.time.ndim == 1:
                if channel == 0:
                    dataset['time'] = (['i'], t_i)
            # Otherwise time is multi-dimensional; store it for every channel
            else:
                dataset['time'] = (['i'], t_i)
            # Same logic as above for time
            if isinstance(self.error, np.ndarray) and self.error.ndim == 1:
                if channel == 0:
                    dataset['error'] = (['i'], e_i)
            else:
                dataset['error'] = (['i'], e_i)

            # xarray won't append to a netCDF file that doesn't exist yet
            file_open_mode = 'w' if channel == 0 else 'a'
            dataset.to_netcdf(path, group=self.channel_names[channel],
                              engine='netcdf4', mode=file_open_mode)
