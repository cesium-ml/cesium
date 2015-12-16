#!/bin/bash

set -e

REPO_PATH=`pwd`
SHARED_PATH=/tmp/`ls -1 /tmp/ | grep -E ^drone_shared | head -n 1`

echo "[Drone] systems check..."
echo "[Drone] ----------------------------------------------------"
echo "[Drone] Current path: ${REPO_PATH}"
echo "[Drone] Shared path: ${SHARED_PATH}"

echo -e "[Drone] Docker info:\n"
docker -H unix:///var/run/docker.sock info
echo
echo "[Drone] ----------------------------------------------------"

echo "[Drone] Installing requirements"
pip install --upgrade pip requests six python-dateutil nose nose-exclude
hash -d pip  # find upgraded pip
sed -i 's/>=/==/g' requirements.txt
WHEELHOUSE="--trusted-host travis-wheels.scikit-image.org \
            --find-links=http://travis-wheels.scikit-image.org/"
pip install $WHEELHOUSE -r requirements.txt

mv ${REPO_PATH} ${SHARED_PATH}
cd ${SHARED_PATH}/mltsp

echo "[Drone] Build extension"
python setup.py build_ext -i

echo "[Drone] Installing mltsp in-place"
pip install -e .

echo "[Drone] Configure MLTSP"
mltsp --install

echo "[Drone] Launch RabbitMQ"
rabbitmq-server &

echo "[Drone] Launch RethinkDB"
make db && sleep 1

echo "[Drone] Initialize database"
mltsp --db-init

echo "[Drone] Run test suite"
make test_no_docker

echo "[Drone] Build HTML documentation"
set +e
errors=`make html 2>&1 | tee errors.log | grep -i error`
set -e
cat errors.log
if [[ -n $errors ]]; then
    echo "Errors detected in Sphinx build; exiting..."
    exit 1;
fi
