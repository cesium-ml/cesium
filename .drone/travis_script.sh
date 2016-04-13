#!/bin/bash

set -ex

section "Tests"

export C_FORCE_ROOT=1 # override warning about running Celery+pickle as root
make ${TEST_TARGET}

section_end "Tests"

section "Build.docs"

make html

section_end "Build.docs"
