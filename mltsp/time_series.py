import copy
import netCDF4
import numpy as np
import pandas as pd
import xarray as xr
from mltsp import cfg


def _default_values_like(old_values, value=None, upper=None):
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


def make_array(x):
    try:
        x = np.asfarray(x).squeeze()
    except ValueError:
        pass
    return x

    
def from_netcdf(filename):
    with netCDF4.Dataset(filename) as ds:
        # TODO are the groups loaded in the order they're written...?
        channels = list(ds.groups)

    # First channel group stores time series metadata
    with xr.open_dataset(filename, group=channels[0]) as ds:
        t = [ds.time.values]
        m = [ds.measurement.values]
        e = [ds.error.values]
        target = ds.attrs.get('target')
        meta_features = ds.meta_features.to_series()
        name = ds.attrs.get('name')

    for channel in channels[1:]:
        with xr.open_dataset(filename, group=channel) as ds:
            m.append(ds.measurement.values)
            if 'time' in ds:
                t.append(ds.time.values)
            if 'error' in ds:
                e.append(ds.error.values)

    return TimeSeries(make_array(t), make_array(m), make_array(e), target,
                      meta_features, name)
    

class TimeSeries:
    def __init__(self, t=None, m=None, e=None, target=None, meta_features={},
                 name=None):
        if t is None and m is None:
            raise ValueError("Either times or measurements must be provided.")
        elif m is None:
            m = _default_values_like(t, value=np.nan)
        
        # If m is 1-dimensional, so are t and e
        if isinstance(m, np.ndarray) and m.ndim == 1:
            self.n_channels = 1
            if t is None:
                t = _default_values_like(m, upper=cfg.DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m, value=cfg.DEFAULT_ERROR_VALUE)
        # If m is 2-dimensional, t and e could be 1d or 2d; default is 1d
        elif isinstance(m, np.ndarray) and m.ndim == 2:
            self.n_channels = len(m)
            if t is None:
                t = _default_values_like(m[0], upper=cfg.DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m[0], value=cfg.DEFAULT_ERROR_VALUE)
        # If m is ragged (list of 1d arrays), t and e should also be ragged
        elif isinstance(m, list):
            self.n_channels = len(m)
            if t is None:
                t = _default_values_like(m, upper=cfg.DEFAULT_MAX_TIME)
            if e is None:
                e = _default_values_like(m, value=cfg.DEFAULT_ERROR_VALUE)
        else:
            raise ValueError("...")
        
        self.time = t
        self.measurement = m
        self.error = e
        self.target = target
        self.meta_features = dict(meta_features)
        self.name = name
        self.channel_names = ["channel_{}".format(i)
                              for i in range(self.n_channels)]
    
    # TODO indexing?
    #def __getitem__(self, inds):

    # TODO name?
    def channels(self):
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

    def to_netcdf(self, filename):
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
            dataset.to_netcdf(filename, group=self.channel_names[channel],
                              engine='netcdf4', mode=file_open_mode)
