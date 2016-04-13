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


section "install.hdf5.netcdf4"
export HDF5_DIR=/home/travis/.local
export PATH=$PATH:/home/travis/.local/bin
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
