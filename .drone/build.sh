#!/bin/bash

set -e

REPO_PATH=`pwd`
SHARED_PATH=/tmp/`ls -1 /tmp/ | grep -E ^drone_shared | head -n 1`

echo "[Drone] systems check..."
echo "[Drone] ----------------------------------------------------"
echo "[Drone] Current path: ${REPO_PATH}"
echo "[Drone] ----------------------------------------------------"

echo "[Drone] Creating Python virtual environment"
pip install virtualenv
virtualenv /envs/mltsp -p python${PYTHON_VERSION}
source /envs/mltsp/bin/activate

echo "[Drone] Installing base requirements"
pip install --upgrade pip requests six python-dateutil nose nose-exclude mock
hash -d pip  # find upgraded pip

echo "[Drone] Build HTML documentation"
# Build before installing requirements since readthedocs doesn't install them
set +e
errors=`make html 2>&1 | tee errors.log | grep -i error`
set -e
cat errors.log
if [[ -n $errors ]]; then
    echo "Errors detected in Sphinx build; exiting..."
    exit 1;
fi

echo "[Drone] Installing MLTSP requirements"
sed -i 's/>=/==/g' requirements.txt
WHEELHOUSE="--trusted-host travis-wheels.scikit-image.org \
            --find-links=http://travis-wheels.scikit-image.org/"
pip install $WHEELHOUSE -r requirements.txt

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
