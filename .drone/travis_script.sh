#!/bin/bash

set -ex

section "Tests"

make ${TEST_TARGET}

section_end "Tests"

section "Build.docs"

make html

section_end "Build.docs"
