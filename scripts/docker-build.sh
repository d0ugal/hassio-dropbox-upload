#!/bin/bash

set -evx
set -x

repo=$1;

docker run \
  --rm \
  --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.docker:/root/.docker \
  -v "${repo}/dropbox-upload":/data \
  homeassistant/amd64-builder \
  --all \
  --test \
  -t /data
