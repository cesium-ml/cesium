#!/bin/bash

if [[ -f build_pull.sh ]]; then
    cd ..
fi

images=`ls -d dockerfiles/*`

for image in $images; do
    container="cesium/`basename $image`"
    docker pull $container
done

