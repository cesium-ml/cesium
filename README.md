# Machine Learning Time-series Platform

[![Join the chat at https://gitter.im/cesium-ml/cesium](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/cesium-ml/cesium?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/cesium-ml/cesium.svg?branch=master)](https://travis-ci.org/cesium-ml/cesium)

## Summary
Cesium allows for the application of machine learning methods to time-series data by doing three things:

1. Extracting features from time-series data (i.e. turning time-series into feature sets)
2. Building models on the basis of these features. The model-building capabilities of Cesium are drawn from [scikit-learn](www.github.com/scikit-learn/scikit-learn).
3. Using these models for prediction. 

Here's an [example](http://cesium.ml/docs/examples/EEG_Example_output.html).

This package is distinct from [Cesium Web](www.github.com/cesium-ml/cesium_web), which is a front-end web application that allows people to do all three of the above through a web browser by running computations through Cesium. 

## Installation from binaries:
- `pip install cesium`

## Installation from source:

1. Install [Cython](http://cython.readthedocs.io/en/latest/src/quickstart/install.html)
2. Clone the repository `git clone https://github.com/cesium-ml/cesium.git`
3. Enter the newly cloned repository.
4. Run `pip install -e .`

## License:

Cesium uses the 3-clause BSD licence. The full license may be found in LICENSE.txt.

