#!/bin/bash

set -ex

section "Tests"

if [[ -n $COVERAGE ]]; then
    PYTEST_FLAGS='--cov=./'
fi
python -m pytest -v $PYTEST_FLAGS

section_end "Tests"

section "Build.docs"

if [[ $SKIP_DOCS != 1 ]]; then
  pip install matplotlib
  make html
fi

section_end "Build.docs"
