import numbers
import numpy as np
from sklearn.preprocessing import Imputer
import xarray as xr


__all__ = ['Featureset', 'from_netcdf']


def from_netcdf(netcdf_path, engine='netcdf4'):
    """Load serialized Featureset from netCDF file."""
    with xr.open_dataset(netcdf_path, engine=engine) as dset:
        fset = Featureset(dset.load())
    return fset


class Featureset(xr.Dataset):
    """Extension of `xarray.Dataset` class that implements some convenience
    functions specific to featuresets generated from a set of time series.

    In particular, provides a method `impute` for filling missing values and
    overloads indexing so that the `name` attribute becomes the "primary"
    coordinate to simplify extracting features for specific time series.
    """
    def __repr__(self):
        """Replace <xarray.Dataset> when printing."""
        s = xr.Dataset.__repr__(self)
        return s.replace('<xarray.', '<cesium.')

    def impute(self, strategy='constant', value=None):
        """Replace NaN/Inf values with imputed values as defined by `strategy`.
        Output should always satisfy `sklearn.validation.assert_all_finite` so
        that training a model will never produce an error.

        Parameters
        ----------
        strategy : str, optional
            The imputation strategy. Defaults to 'constant'.

            - 'constant': replace all missing with `value`
            - 'mean': replace all missing with mean along `axis`
            - 'median': replace all missing with median along `axis`
            - 'most_frequent': replace all missing with mode along `axis`

        value : float or None, optional
            Replacement value to use for `strategy='constant'`. Defaults to
            `None`, in which case a very large negative value is used (a
            good choice for e.g. random forests).

        Returns
        -------
        cesium.Featureset
            Featureset wth no missing/infinite values.
        """
        masked = self.where(abs(self) < np.inf)
        if strategy == 'constant':
            if value is None:
                # If no fill-in value is provided, use a large negative value
                abs_values = np.abs(np.array([v.values.ravel() for v in
                                              masked.data_vars.values()]))
                value = -2. * np.nanmax(abs_values)
            return Featureset(masked.fillna(value))
        elif strategy in ('mean', 'median', 'most_frequent'):
            imputer = Imputer(strategy=strategy, axis=1)
            for var, values in masked.data_vars.items():
                values[:] = imputer.fit_transform(values)
            return Featureset(masked)
        else:
            raise NotImplementedError("Imputation strategy '{}' not"
                                      "recognized.".format(strategy))

    def to_dataframe(self):
        """Convert underlying xarray.Dataset into (2d) Pandas.DataFrame for use
        with sklearn.

        Returns
        -------
        Pandas.DataFrame
            2-D, sklearn-compatible Dataframe containing features.

        """
        fset = self.drop([coord for coord in self.coords
                          if coord not in ['name', 'channel']])
        feature_df = xr.Dataset.to_dataframe(fset)
        if 'channel' in fset:
            feature_df = feature_df.unstack(level='channel')
            if len(fset.channel) == 1:
                feature_df.columns = [pair[0] for pair in feature_df.columns]
            else:
                feature_df.columns = ['_'.join([str(el) for el in pair])
                                      for pair in feature_df.columns]
        # sort columns by name for consistent ordering
        feature_df = feature_df[sorted(feature_df.columns)]
        return feature_df.loc[fset.name]  # preserve original row ordering

    def __getitem__(self, key):
        """Overloads indexing of `xarray.Dataset` to handle special cases for
        extracting features for specific time series. The `name` attribute is
        treated as the "primary" coordinate since this indicates which time
        series the features correspond to.

        - First, if we pass in indices/slice, return data corresponding to
          `name[key]`.
        - Next, if we pass in a set of names that are all present in `name`,
          return data for those time series with `name`s present in `key`.
        - Otherwise, fall back on standard `xarray.Dataset` indexing.
        """
        dset = xr.Dataset(self)
        # Convert names to list to suppress warning when using `in`
        # cf. https://github.com/numpy/numpy/issues/6784
        names = list(np.atleast_1d(dset.name.values))
        if (isinstance(key, (slice, numbers.Integral))
            or (hasattr(key, '__iter__') and all(isinstance(el, numbers.Integral)
                                                 for el in key))):
            return dset.isel(name=key)
        elif ((hasattr(key, '__iter__') and all(el in names for el in key)) or
              key in names):
            return dset.sel(name=key)
        else:
            return dset.__getitem__(key)
