#!/bin/bash

set -ex

section "upgrade.system.supervisor"
pip2.7 install supervisor --upgrade --user
export PATH=$PATH:~/.local/bin/
supervisord --version
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


section "install.hdf5.netcdf4"
export HDF5_DIR=/home/travis/.local
export PATH=$PATH:/home/travis/.local/bin
wget http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.16.tar.gz
tar -xzf hdf5-1.8.16.tar.gz
(cd hdf5-1.8.16/ &&
./configure --prefix=$HDF5_DIR --enable-shared --enable-hl &&
make &&
make install)

wget ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.4.0.tar.gz
tar -xzf netcdf-4.4.0.tar.gz
(cd netcdf-4.4.0/ &&
LDFLAGS=-L$HDF5_DIR/lib CPPFLAGS=-I$HDF5_DIR/include ./configure --enable-netcdf-4 --enable-dap --enable-shared --prefix=$HDF5_DIR &&
make &&
make install)
section_end "install.hdf5.netcdf4"


section "install.cesium.requirements"
# RethinkDB
#source /etc/lsb-release && echo "deb http://download.rethinkdb.com/apt $DISTRIB_CODENAME main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list
#wget -qO- http://download.rethinkdb.com/apt/pubkey.gpg | sudo apt-key add -
#sudo apt-get update -qq
#sudo apt-get install rethinkdb -y --force-yes

# Python requirements
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
section_end "install.cesium.requirements"


section "build.cython.extensions"
pip install --retries 3 -q $WHEELHOUSE cython==0.23.4
python setup.py build_ext -i
section_end "build.cython.extensions"


section "configure.cesium"
pip install -e .
cesium --install
section_end "configure.cesium"


#section "configure.services"
#make db && sleep 1
#cesium --db-init
#section_end "configure.services"


#section "start.nginx"
#sudo mkdir -p /var/lib/nginx/body
#sudo chmod 777 /var/lib/nginx /var/lib/nginx/body
#( cd web_client ; sudo nginx -c nginx.conf -p . -g "daemon off;" & )
#section_end "start.nginx"
