#!/bin/bash

# See also:
# http://paislee.io/how-to-build-and-deploy-docker-images-with-drone/

set -e

wrapdocker &
pip install -r requirements.txt
python setup.py build_ext -i
make test
