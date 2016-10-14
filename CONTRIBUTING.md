# Contributing



## Contributing Time-Series Features

We gratefully accept contributions of new time-series features, be they domain-specific or general. Please follow the guidelines below so that your features are successfully incorporated into the `cesium` feature base.

1. Add any new numerical code to a new or existing file in `cesium/features/`.
2. In `cesium/features/graphs.py`, add feature names to a new or existing list of features (see, e.g., `GENERAL_FEATS`).
3. In `cesium/features/graphs.py`, add feature computations to a new or existing `dask` graph of computations (see, e.g., `GENERAL_GRAPH`).
	1. By default, the keys `'t'`, `'m'`, and `'e'` refer to the time series times, measurements, and errors respectively.
	2. Most features will consist of a single function call, e.g. `{'amplitude': (amplitude, 'm')}`.
	3. More complicated operations which re-use intermediate values can be constructed via standard `dask` graph syntax: see the [`dask` documentation](http://dask.pydata.org/en/latest/custom-graphs.html) for details, or the feature `freq1_freq` in `graphs.py` for an example.
