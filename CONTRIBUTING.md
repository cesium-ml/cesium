# Contributing

## Contributing Time-Series Features

We gratefully accept contributions of new time-series features, be they
domain-specific or general.

To add your features to the project, please follow the guidelines below:

1. Add your code to a new or existing file in `cesium/features/`.
2. In `cesium/features/graphs.py`, add your features to the
   `dask_feature_graph`.
3. Add your features to the `feature_categories` & (optionally)
   `feature_tags` dictionaries in `cesium/features/graphs.py`.

Notes:

 - The keys `'t'`, `'m'`, and `'e'` refer to the time series times,
   measurements, and errors respectively.
 - More complicated operations which re-use intermediate values can be
   constructed via standard `dask` graph syntax: see the [`dask`
   documentation](http://dask.pydata.org/en/latest/custom-graphs.html) for
   details, or the feature `freq1_freq` in `graphs.py` as an example.
