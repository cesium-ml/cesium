# Installation

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
- [cython](http://cython.org/) (development only)

## From source

1. Install [Cython](http://cython.readthedocs.io/en/latest/src/quickstart/install.html)
2. Clone the repository: `git clone https://github.com/cesium-ml/cesium.git && cd cesium`
4.1. For a regular install: `pip install .`
4.2. For an in-place developer build: `pip install --no-build-isolation -e .`

Note that cesium requires a C99 compiler which, in particular, excludes
MSVC. On Windows, we recommend clang.

## Testing

- `pip install pytest mock`
- `make test`
