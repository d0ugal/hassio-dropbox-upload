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
  --target dropbox-upload \
  --tag-latest \
  --push \
  --all
