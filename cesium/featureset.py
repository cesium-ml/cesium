import numpy as np
from sklearn.preprocessing import Imputer
import xarray as xr


__all__ = ['Featureset']


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
            if value == None:
                # If no fill-in value is provided, use a large negative value
                max_by_var = abs(masked).max()
                value = -2. * np.array([v.values for v in max_by_var.values()]).max()
            return masked.fillna(value)
        elif strategy in ('mean', 'median', 'most_frequent'):
            imputer = Imputer(strategy=strategy, axis=1)
            for var, values in masked.data_vars.items():
                values[:] = imputer.fit_transform(values)
            return masked
        else:
            raise NotImplementedError("Imputation strategy '{}' not"
                                      "recognized.".format(strategy))

    def __getitem__(self, key):
        """Overloads indexing of `xarray.Dataset` to handle special cases for
        extracting features for specific time series. The `name` attribute is
        treated as the "primary" coordinate since this indicates which time
        series the features correspond to.

        - First, if we pass in indices/slice, return data corresponding to
          `name[key]`.
        - Next, if we pass in a set of labels that are all present in `name`,
          return data for those time series with `name`s present in `key`.
        - Otherwise, fall back on standard `xarray.Dataset` indexing.

        NOTE: the warning `FutureWarning: elementwise comparison failed;
        returning scalar instead, but in the future will perform elementwise
        comparison` is due to a bug in `numpy`:
        https://github.com/numpy/numpy/issues/6784
        """
        names = self._construct_dataarray('name').values
        if (isinstance(key, (slice, int))
            or (hasattr(key, '__iter__') and all(isinstance(el, int)
                                                 for el in key))):
            return super().isel(name=key)
        elif ((hasattr(key, '__iter__') and all(el in names for el in key)) or
              key in names):
            return super().sel(name=key)
        else:
            return super().__getitem__(key)
