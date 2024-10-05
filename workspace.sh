#!/bin/sh
set -exu

docker build . -t ws -f Dockerfile.ws
docker run -it --rm ws bash
