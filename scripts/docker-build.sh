#!/bin/bash

set -evx
set -x

# repo=$1;

image="d0ugal/hassio-dropbox-upload-${ARCH}"
tag=$(git describe --exact-match HEAD --abbrev=0 --tags 2> /dev/null || true)

docker build \
   --build-arg "BUILD_DATE=$(date +"%Y-%m-%dT%H:%M:%SZ")" \
   --build-arg "BUILD_ARCH=${ARCH}" \
   --build-arg "BUILD_GIT_URL=https://github.com/d0ugal/hassio-dropbox-upload" \
   --tag "${image}:${tag#v}" \
   dropbox-upload/

# docker run \
#  --privileged \
#  -v /var/run/docker.sock:/var/run/docker.sock \
#  -v "$repo":/docker \
#  hassioaddons/build-env:latest \
#  --image "d0ugal/hassio-dropbox-upload-{arch}" \
#  --git \
#  --target dropbox-upload \
#  --${ARCH:-all}
