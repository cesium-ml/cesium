# Machine Learning Time-series Platform

[![Join the chat at https://gitter.im/cesium-ml/cesium](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/cesium-ml/cesium?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/cesium-ml/cesium.svg?branch=master)](https://travis-ci.org/cesium-ml/cesium)

## Summary
Cesium allows for the application of machine learning methods to timeseries data by doing three things:

1. Extracting features from timeseries data (i.e. turning timeseries into feature sets)
2. Building models on the basis of these features. The model-building capabilities of Cesium are drawn from [scikit-learn](www.github.com/scikit-learn/scikit-learn).
3. Using these models for prediction. 

Here's an [example](http://cesium.ml/docs/examples/EEG_Example_output.html).

This package is distinct from [Cesium Web](www.github.com/cesium-ml/cesium_web), which is a front-end web application that allows people to do all three of the above through a web browser by running computations through Cesium. 

## Requirements:

- numpy>=1.10.4
- scipy>=0.16.0
- scikit-learn>=0.17.0
- pandas>=0.17.0
- dask
- toolz
- xarray>=0.8.1
- gatspy>=0.3.0
- netCDF4
- cloudpickle

## Installation from binaries:
- MacOS: `pip install cesium`
- Ubuntu/Debian: `pip3 install cesium`
- Bash on Ubuntu on Windows: After installing pip (`apt-get -y install python-pip`), run `pip3 install cesium`

## Installation from source:

1. Clone the repository `git clone https://github.com/cesium-ml/cesium.git`
2. Enter the newly cloned repository.
3. Run `pip install -e .`

## License:

Unless otherwise specified by LICENSE.txt files in individual
directories, all code is

Copyright (C) 2016, the cesium team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
 3. Neither the name of cesium nor the names of its contributors may be
    used to endorse or promote products derived from this software without
    specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

