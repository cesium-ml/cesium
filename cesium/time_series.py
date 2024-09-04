import copy
from collections.abc import Iterable

import numpy as np

__all__ = ["load", "TimeSeries", "DEFAULT_MAX_TIME", "DEFAULT_ERROR_VALUE"]


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
    if hasattr(x, "shape") and hasattr(y, "shape"):
        return x.shape == y.shape
    else:
        return len(x) == len(y) and all(
            np.shape(x_i) == np.shape(y_i) for x_i, y_i in zip(x, y)
        )


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
        lower = 0.0
    else:
        raise ValueError("Either `value` or `upper` must be provided.")

    new_values = copy.deepcopy(old_values)
    if _ndim(old_values) == 1 or (
        isinstance(old_values, np.ndarray) and 1 in old_values.shape
    ):
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
        x = np.asarray(x, dtype=float).squeeze()
    except ValueError:
        pass
    return x


def load(ts_path):
    """Load serialized TimeSeries from .npz file."""
    with np.load(ts_path) as npz_file:
        data = dict(npz_file)

    for key in ["time", "measurement", "error"]:
        if key not in data:  # combine channel arrays into list
            n_channels = sum(1 for c in data.keys() if key in c)  # time0, ...
            data[key] = [data[key + str(i)] for i in range(n_channels)]

    # Convert 0d arrays to single values
    if "name" in data:
        data["name"] = data["name"].item()
    if "label" in data:
        data["label"] = data["label"].item()

    return TimeSeries(
        t=data.get("time"),
        m=data.get("measurement"),
        e=data.get("error"),
        meta_features=dict(zip(data["meta_feat_names"], data["meta_feat_values"])),
        name=data.get("name"),
        label=data.get("label"),
    )


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
    label : str, float, or None
        Class label or regression target for the given time series (if
        applicable).
    meta_features : dict
        Dictionary of feature names/values specified independently of the
        featurization process in `featurize`.
    name : str or None
        Identifying name for the given time series (if applicable).
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

    def __init__(
        self,
        t=None,
        m=None,
        e=None,
        label=None,
        meta_features={},
        name=None,
        path=None,
        channel_names=None,
    ):
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
            raise ValueError("m must be a 1D or 2D array, or a 2D list of" " arrays.")

        self.time = _make_array_if_possible(t)
        self.measurement = _make_array_if_possible(m)
        self.error = _make_array_if_possible(e)
        self.sort()  # re-order by time before broadcasting

        if _ndim(self.time) == 1 and _ndim(self.measurement) == 2:
            if isinstance(self.measurement, np.ndarray):
                self.time = np.broadcast_to(self.time, self.measurement.shape)
            else:
                raise ValueError(
                    "Times for each channel must be provided if m" " is a ragged array."
                )

        if _ndim(self.error) == 1 and _ndim(self.measurement) == 2:
            if isinstance(self.measurement, np.ndarray):
                self.error = np.broadcast_to(self.error, self.measurement.shape)
            else:
                raise ValueError(
                    "Errors for each channel must be provided if"
                    " m is a ragged array."
                )

        if not (
            _compatible_shapes(self.measurement, self.time)
            and _compatible_shapes(self.measurement, self.error)
        ):
            raise ValueError(
                "times, values, errors are not of compatible"
                " types/sizes. Please refer to the docstring"
                " for list of allowed input types."
            )

        self.label = label
        self.meta_features = dict(meta_features)
        self.name = name
        self.path = path
        if channel_names is None:
            self.channel_names = [f"channel_{i}" for i in range(self.n_channels)]
        else:
            self.channel_names = channel_names

    def channels(self):
        """Iterates over measurement channels (whether one or multiple)."""
        t_channels = self.time
        m_channels = self.measurement
        e_channels = self.error
        if isinstance(self.time, np.ndarray) and self.time.ndim == 1:
            t_channels = np.broadcast_to(self.time, (self.n_channels, len(self.time)))
        if isinstance(self.measurement, np.ndarray) and self.measurement.ndim == 1:
            m_channels = np.broadcast_to(
                self.measurement, (self.n_channels, len(self.measurement))
            )
        if isinstance(self.error, np.ndarray) and self.error.ndim == 1:
            e_channels = np.broadcast_to(self.error, (self.n_channels, len(self.error)))
        return zip(t_channels, m_channels, e_channels)

    def sort(self):
        """Sort times, measurements, and errors by time."""
        if _ndim(self.time) == 1:
            inds = np.argsort(self.time)
            self.time = self.time[inds]
            if _ndim(self.measurement) == 1:
                self.measurement = self.measurement[inds]
            else:
                for i in range(len(self.measurement)):
                    self.measurement[i] = self.measurement[i][inds]
            if _ndim(self.error) == 1:
                self.error = self.error[inds]
            else:
                for i in range(len(self.error)):
                    self.error[i] = self.error[i][inds]
        else:  # if time is 2d, so are measurement and error
            for i in range(len(self.time)):
                inds = np.argsort(self.time[i])
                self.time[i] = self.time[i][inds]
                self.measurement[i] = self.measurement[i][inds]
                self.error[i] = self.error[i][inds]

    def save(self, path=None):
        """Store TimeSeries object as a single .npz file.

        Attributes are stored in the following arrays:
            - time
            - measurement
            - error
            - meta_feat_names
            - meta_feat_values
            - name
            - label

        If `path` is omitted then the `path` attribute from the TimeSeries
        object is used.
        """
        if path is None:
            path = self.path

        data = {
            "meta_feat_names": list(self.meta_features.keys()),
            "meta_feat_values": list(self.meta_features.values()),
        }

        for key in ["time", "measurement", "error"]:
            value = getattr(self, key)
            if isinstance(value, np.ndarray):
                data[key] = value
            else:  # list of arrays -> save each channel separately
                for i, value_i in enumerate(value):
                    data[key + str(i)] = value_i

        if self.name:
            data["name"] = self.name
        if self.label:
            data["label"] = self.label
        np.savez(path, **data)
