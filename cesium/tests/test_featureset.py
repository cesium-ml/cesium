import os
from os.path import join as pjoin
import tempfile
import numpy as np
import numpy.testing as npt
import scipy.stats
import xarray as xr
from cesium import featureset
from cesium.featureset import Featureset
from cesium.tests.fixtures import sample_featureset


def test_repr():
    """Testing Featureset printing."""
    fset = sample_featureset(10, 3, ['amplitude', 'maximum', 'minimum'],
                             ['class1', 'class2'])
    repr(fset)


def test_impute():
    """Test imputation of missing Featureset values."""
    fset = sample_featureset(3, 1, ['amplitude'], ['class1', 'class2'],
                             names=['a', 'b', 'c'], meta_features=['meta1'])

    imputed = fset.impute()
    npt.assert_allclose(fset.amplitude.values, imputed.amplitude.values)
    assert isinstance(imputed, Featureset)

    fset.amplitude.values[0, 0] = np.inf
    fset.amplitude.values[0, 1] = np.nan
    masked = Featureset(fset.where(abs(fset) < np.inf))
    values = fset.amplitude.values[0, 2:]

    imputed = fset.impute(strategy='constant', value=None)
    abs_values = np.abs(np.array([v.values.ravel() for v in
                                  masked.data_vars.values()]))
    npt.assert_allclose(-2 * np.nanmax(abs_values),
                        imputed.amplitude.values[0, 0:2])
    assert isinstance(imputed, Featureset)

    imputed = fset.impute(strategy='constant', value=-1e4)
    npt.assert_allclose(-1e4, imputed.amplitude.values[0, 0:2])
    assert isinstance(imputed, Featureset)

    imputed = fset.impute(strategy='mean')
    npt.assert_allclose(np.mean(values), imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])
    assert isinstance(imputed, Featureset)

    imputed = fset.impute(strategy='median')
    npt.assert_allclose(np.median(values), imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])
    assert isinstance(imputed, Featureset)

    imputed = fset.impute(strategy='most_frequent')
    npt.assert_allclose(scipy.stats.mode(values).mode.item(),
                        imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])
    assert isinstance(imputed, Featureset)


def test_indexing():
    fset = sample_featureset(3, 1, ['amplitude'], ['class1', 'class2'],
                             names=['a', 'b', 'c'])
    """Test indexing overloading (__getattr__)."""
    assert all(fset[0] == fset.isel(name=0))
    assert all(fset[0:2] == fset.isel(name=[0, 1]))
    assert all(fset[[0, 2]] == fset.isel(name=[0, 2]))
    assert all(fset[np.array([0, 2])] == fset.isel(name=[0, 2]))
    assert all(fset['a'] == fset.sel(name='a'))
    assert all(fset[['a', 'b']] == fset.sel(name=['a', 'b']))
    npt.assert_allclose(fset['amplitude'].values.ravel(),
                        fset.data_vars['amplitude'].values.ravel())


def test_to_dataframe():
    fset = sample_featureset(3, 1, ['amplitude'], ['class1', 'class2'],
                             names=['a', 'b', 'c'])
    df = fset.to_dataframe()
    npt.assert_allclose(fset['amplitude'].values.ravel(), df['amplitude'])
    assert 'target' not in df


def test_from_netcdf():
    fset = sample_featureset(3, 1, ['amplitude'], ['class1', 'class2'],
                             names=['a', 'b', 'c'])
    data_dir = tempfile.mkdtemp()
    fset.to_netcdf(pjoin(data_dir, 'test.nc'))
    loaded = featureset.from_netcdf(pjoin(data_dir, 'test.nc'))
    assert isinstance(loaded, Featureset)
    assert set(fset.data_vars) == set(loaded.data_vars)
    assert set(fset.coords) == set(loaded.coords)
