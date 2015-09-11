#!/bin/bash

set -e

REPO_PATH=`pwd`
SHARED_PATH=/tmp/`ls -1 /tmp/ | grep -E ^drone_shared | head -n 1`

echo "Drone systems check..."
echo "----------------------------------------------------"
echo Current path: ${REPO_PATH}
echo Shared path: ${SHARED_PATH}

echo -e "Docker info:\n"
docker -H unix:///var/run/docker.sock info
echo
echo "----------------------------------------------------"

pip install -r requirements.txt

mv ${REPO_PATH} ${SHARED_PATH}
cd ${SHARED_PATH}/mltsp

python setup.py build_ext -i
pip install -e .

cp mltsp.yaml.example mltsp.yaml

make db && sleep 1 && make init
make test_no_docker
