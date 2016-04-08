#!/bin/bash

set -ex

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

# RabbitMQ (http://www.scotthelm.com/2013/11/27/rabbit-mq-and-erlang-and-ubuntu-oh-my.html)
sudo apt-get purge -y rabbitmq-server
sudo apt-get autoremove -y rabbitmq-server
source /etc/lsb-release && echo "deb http://packages.erlang-solutions.com/ubuntu $DISTRIB_CODENAME contrib" | sudo tee /etc/apt/sources.list.d/rabbitmq.list
wget http://packages.erlang-solutions.com/ubuntu/erlang_solutions.asc
sudo apt-key add erlang_solutions.asc
sudo apt-get update
sudo apt-get install -y erlang erlang-nox
# Needed to start RabbitMQ in Docker:
# https://github.com/docker/docker/issues/1024#issuecomment-20018600
#sudo dpkg-divert --local --rename --add /sbin/initctl
#sudo ln -s /bin/true /sbin/initctl
wget https://www.rabbitmq.com/releases/rabbitmq-server/v3.2.1/rabbitmq-server_3.2.1-1_all.deb
sudo dpkg -i rabbitmq-server_3.2.1-1_all.deb

# Newer HDF5/netCDF headers
sudo apt-get update -qq
sudo apt-get install libhdf5-7 libhdf5-serial-dev libnetcdf7 libnetcdf-dev -y --force-yes

# Python requirements
sed -i 's/>=/==/g' requirements.txt
WHEELHOUSE="--no-index --trusted-host travis-wheels.scikit-image.org \
            --find-links=http://travis-wheels.scikit-image.org/"
WHEELBINARIES="numpy scipy matplotlib scikit-learn pandas"
for requirement in $WHEELBINARIES; do
    WHEELS="$WHEELS $(grep $requirement requirements.txt)"
done
pip install --retries 3 -q $WHEELHOUSE $WHEELS
pip install --retries 3 -q -r requirements.txt
pip list
section_end "install.cesium.requirements"


section "build.cython.extensions"
pip install --retries 3 -q $WHEELHOUSE cython==0.23.4
python setup.py build_ext -i
section_end "build.cython.extensions"


section "configure.cesium"
pip install -e .
section_end "configure.cesium"


#echo "[Drone] Build HTML documentation"
#set +e
#errors=`make html 2>&1 | tee errors.log | grep -i error`
#set -e
#cat errors.log
#if [[ -n $errors ]]; then
#    echo "Errors detected in Sphinx build; exiting..."
#    exit 1;
#fi

