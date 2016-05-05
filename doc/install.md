## Installation

The latest version of `cesium` can be installed via `pip`:
```
pip install cesium
```

*Note:* We depend on NetCDF4, which currently has no Linux wheel, so tries to
compile itself.  You may therefore need to install the netcdf4 headers and
library separately.

The cesium library has the following dependencies:
- [numpy](http://www.numpy.org/)
- [scipy](http://www.scipy.org/)
- [pandas](http://pandas.pydata.org)
- [scikit-learn](http://scikit-learn.org/)
- [cython](http://cython.org/)
- [dask](http://dask.pydata.org/)
- [xarray](http://xarray.pydata.org/)
- [NetCDF4](http://unidata.github.io/netcdf4-python/)

For parallel processing, you will also need:

* Install [RabbitMQ](https://www.rabbitmq.com/download.html)
  * Ensure server is running with `rabbitmq-server -detached`

The `cesium` library runs on Python 3.

## Testing

- `pip install nose nose-exclude mock`
- `make test`

