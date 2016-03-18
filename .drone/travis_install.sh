#!/bin/bash

set -ex

section "upgrade.system.supervisor"
sudo pip2.7 install supervisor
section_end "upgrade.system.supervisor"

section "create.virtualenv"
python${TRAVIS_PYTHON_VERSION} -m venv ~/envs/cesium
source ~/envs/cesium/bin/activate
section_end "create.virtualenv"


section "install.base.requirements"
pip install --upgrade pip
hash -d pip  # find upgraded pip
pip install --retries 3 -q requests six python-dateutil nose nose-exclude mock
section_end "install.base.requirements"


section "install.cesium.requirements"

sed -i 's/>=/==/g' requirements.txt
WHEELHOUSE="--no-index --trusted-host travis-wheels.scikit-image.org \
            --find-links=http://travis-wheels.scikit-image.org/"

WHEELBINARIES="numpy scipy matplotlib scikit-learn pandas pyzmq"
for requirement in $WHEELBINARIES; do
    WHEELS="$WHEELS $(grep $requirement requirements.txt)"
done
pip install --retries 3 -q $WHEELHOUSE $WHEELS

pip install --retries 3 -q -r requirements.txt
pip list

source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
sudo apt-get update -qq
sudo apt-get install rethinkdb -y --force-yes

section_end "install.cesium.requirements"


section "build.cython.extensions"
pip install --retries 3 -q $WHEELHOUSE cython==0.23.4
python setup.py build_ext -i
section_end "build.cython.extensions"


section "configure.cesium"
pip install -e .
cesium --install
section_end "configure.cesium"


section "configure.services"
sudo rabbitmq-server &
make db && sleep 1
cesium --db-init
section_end "configure.services"

#echo "[Drone] Build HTML documentation"
#set +e
#errors=`make html 2>&1 | tee errors.log | grep -i error`
#set -e
#cat errors.log
#if [[ -n $errors ]]; then
#    echo "Errors detected in Sphinx build; exiting..."
#    exit 1;
#fi

section "install.testing.tools"

cd /tmp && \
wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 && \
tar xjf phantomjs-*.tar.bz2 && \
sudo rm -f /usr/local/bin/phantomjs && \
sudo ln -s /tmp/phantomjs-*/bin/phantomjs /usr/local/bin/phantomjs

section_end "install.testing.tools"
