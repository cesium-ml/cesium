## Installation

The latest version of `cesium` can be installed via `pip`:
```
pip install cesium
```

The cesium library has the following dependencies:
- [numpy](http://www.numpy.org/)
- [scipy](http://www.scipy.org/)
- [pandas](http://pandas.pydata.org)
- [scikit-learn](http://scikit-learn.org/)
- [dask](http://dask.pydata.org/)
- [xarray](http://xarray.pydata.org/)
- [NetCDF4](http://unidata.github.io/netcdf4-python/)
- [cython](http://cython.org/) (development only)

The `cesium` library runs on Python 2 and 3.

## Testing

- `pip install pytest pytest-cov mock`
- `make test`
