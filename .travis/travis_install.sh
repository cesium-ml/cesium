#!/bin/bash

set -ex


section "install.base.requirements"
pip install --upgrade pip
hash -d pip  # find upgraded pip
pip install --retries 3 -q requests six python-dateutil pytest>=3.6 pytest-cov \
                           mock coverage
section_end "install.base.requirements"


section "install.cesium.requirements"
pip install --retries 3 -q -r requirements.txt
pip list
section_end "install.cesium.requirements"


section "build.cython.extensions"
pip install --retries 3 -q cython==0.25.2
python setup.py build_ext -i
section_end "build.cython.extensions"


section "configure.cesium"
pip install -e .
section_end "configure.cesium"
