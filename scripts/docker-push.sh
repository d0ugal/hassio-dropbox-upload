#!/bin/bash

set -evx
set -x

repo=$1;

docker run -it --rm --privileged --name "dropbox-upload" \
    -v ~/.docker:/root/.docker \
    -v "${repo}":/docker \
    hassioaddons/build-env:latest \
    --image "d0ugal/hassio-dropbox-upload-{arch}" \
    --target "dropbox-upload" \
    --git \
    --all \
    --push
