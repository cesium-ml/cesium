#!/bin/bash

set -e 

if [[$COVERAGE == 1]]

then
    echo "Python version: 3.4/3.5"
    echo "Running coverage.py"
    nosetests -v --exe --with-coverage
else
    echo "Python version: 2.x"
    echo "Coverage not set up for python 2.x"
fi
