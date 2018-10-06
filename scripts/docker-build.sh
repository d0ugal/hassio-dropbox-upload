#!/bin/bash

set -evx
set -x

repo=$1;

docker run \
  --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$repo":/docker \
  hassioaddons/build-env:latest \
  --image "d0ugal/hassio-dropbox-upload-{arch}" \
  --cache-tag test \
  --git \
  --target dropbox-upload \
  --${ARCH:-all}
