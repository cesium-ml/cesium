#!/bin/bash

if [[ -f build_docker_images.sh ]]; then
    cd ..
fi

echo '**********************************************'
echo "Updating base Ubuntu image..."
echo '**********************************************'
docker pull ubuntu

base_images=`ls -d dockerfiles/base*`
images=`ls -d dockerfiles/* | grep -v base_`


build_image () {
    container="mltp/`basename $1`"
    echo '**********************************************'
    echo Building: $container
    echo '**********************************************'

    docker build -t $container $image
}


for image in $base_images; do
    build_image $image
done

for image in $images; do
    build_image $image
done
