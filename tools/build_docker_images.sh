if [[ -f build_docker_images.sh ]]; then
    cd ..
fi

for image in `ls -d dockerfiles/*`; do
    echo '**********************************************'
    echo Building: $image
    echo '**********************************************'

    docker build $image
done
