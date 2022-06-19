# `cesium`: Open-Source Platform for Time Series Inference
[![Join the chat at https://gitter.im/cesium-ml/cesium](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/cesium-ml/cesium?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/cesium-ml/cesium.svg?branch=master)](https://travis-ci.org/cesium-ml/cesium)
[![codecov.io](http://codecov.io/github/cesium-ml/cesium/coverage.svg?branch=master)](http://codecov.io/github/cesium-ml/cesium?branch=master)

## Summary
`cesium` is an open source library that allows users to:
- extract features from raw time series data ([see list](http://cesium-ml.org/docs/feature_table.html)),
- build machine learning models from these features, and
- generate predictions for new data.

More information and [examples](http://cesium-ml.org/docs/auto_examples/index.html) can be found on our [home page](http://cesium-ml.org).

## Installation from binaries:
- Wheels for Mac and Linux can be installed via `pip install cesium`.
- We do not build binary wheels for Windows. To install on Windows, follow the instructions below for installation from source.

## Installation from source:
1. Install [Cython](http://cython.readthedocs.io/en/latest/src/quickstart/install.html)
2. Clone the repository: `git clone https://github.com/cesium-ml/cesium.git`
3. `cd cesium && pip install -e .`

Note that cesium requires a C99 compiler, which in particular excludes MSVC. On Windows, a different compiler like MinGW has to be used. Please refer to the [instructions for installing Cython & MinGW on Windows](https://cython.readthedocs.io/en/latest/src/tutorial/appendix.html#appendix-installing-mingw-on-windows).

## License:
`cesium` uses the [3-clause BSD licence](https://github.com/cesium-ml/cesium/blob/master/LICENSE.txt).
