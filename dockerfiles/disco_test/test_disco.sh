#!/bin/bash

THIS_DIR="$( dirname "${BASH_SOURCE[0]}")"
MLTP_DIR=$(cd "${THIS_DIR}/../.." && pwd)

set -ex
docker build -t disco_test .
docker run -v "$MLTP_DIR:/home/mltsp/mltsp/mltsp" disco_test
