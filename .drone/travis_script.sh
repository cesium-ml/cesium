#!/bin/bash

set -ex

source ~/envs/cesium/bin/activate


section "Tests"

make ${TEST_TARGET}

section_end "Tests"


section "Build.docs"

if [[ $SKIP_DOCS != 1 ]]; then
  pip install matplotlib
  make html
fi

section_end "Build.docs"
