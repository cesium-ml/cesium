import copy
import netCDF4
import numpy as np
import pandas as pd
import xarray as xr


__all__ = ['from_netcdf', 'TimeSeries', 'DEFAULT_MAX_TIME',
           'DEFAULT_ERROR_VALUE']


DEFAULT_MAX_TIME = 1.0
DEFAULT_ERROR_VALUE = 1e-4


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
    if (isinstance(old_values, np.ndarray) and (old_values.ndim == 1
                                                or 1 in old_values.shape)):
        new_values[:] = np.linspace(lower, upper, len(new_values))
    else:
        for new_array in new_values:
            new_array[:] = np.linspace(lower, upper, len(new_array))

    return new_values


def _make_array(x):
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
    with xr.open_dataset(netcdf_path, group=channels[0]) as ds:
        t = [ds.time.values]
        m = [ds.measurement.values]
        e = [ds.error.values]
        target = ds.attrs.get('target')
        meta_features = ds.meta_features.to_series()
        name = ds.attrs.get('name')
        path = ds.attrs.get('path')

    for channel in channels[1:]:
        with xr.open_dataset(netcdf_path, group=channel) as ds:
            m.append(ds.measurement.values)
            if 'time' in ds:
                t.append(ds.time.values)
            if 'error' in ds:
                e.append(ds.error.values)

    return TimeSeries(_make_array(t), _make_array(m), _make_array(e), target,
                      meta_features, name, path)


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
        is multidimensional, this can be one-dimensional (same times for each
        channel) or multidimensional (different times for each channel).
    measurement : (n,) or (p, n) array or list of (n,) arrays
        Array(s) of measurement values; can be multidimensional for
        multichannel data. In the case of multichannel data with different
        numbers of measurements for each channel, `measurement` will be a list
        of arrays instead of a single two-dimensional array.
    error : (n,) or (p, n) array or list of (n,) arrays
        Array(s) of measurement errors for each value. If `measurement` is
        multidimensional, this can be one-dimensional (same times for each
        channel) or multidimensional (different times for each channel).
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
        if isinstance(m, np.ndarray) and m.ndim == 1:
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
        elif isinstance(m, list):
            self.n_channels = len(m)
            if t is None:
                t = _default_values_like(m, upper=DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m, value=DEFAULT_ERROR_VALUE)
        else:
            raise ValueError("...")

        self.time = t
        self.measurement = m
        self.error = e
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
                    dataset.attrs['name'] = self.name
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
