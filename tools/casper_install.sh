#!/bin/bash
THIS_DIR="$( dirname "${BASH_SOURCE[0]}")"
EXTERNAL_DIR=$(cd "${THIS_DIR}/../external" && pwd)

mkdir -p $EXTERNAL_DIR
cd $EXTERNAL_DIR

if [[ -d "casperjs" ]]; then
    echo "CasperJS already downloaded"
else
    wget https://github.com/n1k0/casperjs/tarball/master -O - | tar -xz
    mv n1k0-casperjs-* casperjs
fi

