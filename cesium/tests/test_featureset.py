import os
from os.path import join as pjoin
import numpy as np
import numpy.testing as npt
import scipy.stats
import xarray as xr
from cesium.tests.fixtures import sample_featureset


def test_repr():
    """Testing Featureset printing."""
    fset = sample_featureset(10, 3, ['amplitude', 'maximum', 'minimum'],
                             ['class1', 'class2'])
    repr(fset)


def test_impute():
    """Test imputation of missing Featureset values."""
    fset = sample_featureset(10, 1, ['amplitude'], ['class1', 'class2'])
    fset.amplitude.values[0, 0] = np.inf
    fset.amplitude.values[0, 1] = np.nan
    values = fset.amplitude.values[0, 2:]

    imputed = fset.impute(strategy='constant', value=-1e4)
    npt.assert_allclose(-1e4, imputed.amplitude.values[0, 0:2])

    imputed = fset.impute(strategy='mean')
    npt.assert_allclose(np.mean(values), imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])

    imputed = fset.impute(strategy='median')
    npt.assert_allclose(np.median(values), imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])

    imputed = fset.impute(strategy='most_frequent')
    npt.assert_allclose(scipy.stats.mode(values).mode.item(),
                        imputed.amplitude.values[0, 0:2])
    npt.assert_allclose(values, imputed.amplitude.values[0, 2:])


def test_indexing():
    fset = sample_featureset(3, 1, ['amplitude'], ['class1', 'class2'],
                             labels=['a', 'b', 'c'])
    """Test indexing overloading (__getattr__)."""
    assert all(fset[0] == fset.isel(name=0))
    assert all(fset[0:2] == fset.isel(name=[0, 1]))
    assert all(fset['a'] == fset.sel(name='a'))
    assert all(fset[['a', 'b']] == fset.sel(name=['a', 'b']))
    npt.assert_allclose(fset['amplitude'].values.ravel(),
                        fset.data_vars['amplitude'].values.ravel())
