#!/bin/bash

set -ex

section "upgrade.system.supervisor"
export PATH=$PATH:/home/travis/.local/bin
pip2.7 install supervisor --upgrade --user
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


section "install.libraries"
mkdir -p ~/.local
export PATH=$PATH:/home/travis/.local/bin
if [[ -n `which rethinkdb` ]]; then
    echo "Using cached RethinkDB."
else
    echo "Downloading RethinkDB binary."
    wget http://download.rethinkdb.com/apt/pool/precise/main/r/rethinkdb/rethinkdb_2.3.0~0precise_amd64.deb
    mkdir -p ~/rethinkdb
    dpkg -x rethinkdb_2.3.0~0precise_amd64.deb ~/rethinkdb
    cp -rf ~/rethinkdb/usr/* ~/.local/
fi

export HDF5_DIR=/home/travis/.local
if [[ -f $HDF5_DIR/lib/libhdf5.so ]]; then
    echo "Using cached HDF5/netCDF4."
else
    echo "Compiling HDF5/netCDF4 from source."
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
fi
section_end "install.hdf5.netcdf4"


section "install.cesium.requirements"
curl https://raw.githubusercontent.com/cesium-ml/cesium/master/requirements.txt \
    -o requirements_cesium.txt
sed -i 's/>=/==/g' requirements_cesium.txt
WHEELHOUSE="--no-index --trusted-host travis-wheels.scikit-image.org \
            --find-links=http://travis-wheels.scikit-image.org/"
WHEELBINARIES="numpy scipy matplotlib scikit-learn pandas"
for requirement in $WHEELBINARIES; do
    WHEELS="$WHEELS $(grep $requirement requirements_cesium.txt)"
done
pip install --retries 3 -q $WHEELHOUSE $WHEELS
pip install --retries 3 -q -r requirements.txt  # also installs cesium
pip list
section_end "install.cesium.requirements"


section "configure.services"
sudo rabbitmq-server &
make db && sleep 1
cesium --db-init
section_end "configure.services"


section "install.testing.tools"
# Use pre-packaged 1.9.8 for now
phantomjs --version
section_end "install.testing.tools"


section "start.nginx"
sudo mkdir -p /var/lib/nginx/body
sudo chmod 777 /var/lib/nginx /var/lib/nginx/body
( cd web_client ; sudo nginx -c nginx.conf -p . -g "daemon off;" & )
section_end "start.nginx"


section "configure.cesium"
cesium --install
section_end "configure.cesium"
