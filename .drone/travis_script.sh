#!/bin/bash

set -x

section "Tests"

make ${TEST_TARGET}

section_end "Tests"

section "Build.docs"

source ~/virtualenv/python3.5/bin/activate
pip install matplotlib
ls ~/.cache/matplotlib
fc-list
python -c 'import matplotlib; print(matplotlib.get_cachedir())'
python -c 'import matplotlib.pyplot'
python -c 'import matplotlib.pyplot'
find ~ -name fontList.cache
find ~ -name fontList.py3k.cache
ls ~/.cache/matplotlib
ls ~/.cache/fontconfig
ls ~/.matplotlib
make html

section_end "Build.docs"
