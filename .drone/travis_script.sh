#!/bin/bash

set -ex

section "Tests"

make ${TEST_TARGET}

section_end "Tests"

section "Build.docs"

make html
.drone/deploy_docs.sh

section_end "Build.docs"
