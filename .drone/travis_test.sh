#!/bin/bash

#set -e
set +e

export C_FORCE_ROOT=1 # override warning about running Celery+pickle as root
make ${TEST_TARGET}
