#!/usr/bin/env bash

[[ -z "$1" ]] && echo "please define a version tag" && exit

unset DOCKER_TLS_VERIFY
unset DOCKER_HOST
unset DOCKER_CERT_PATH

docker --config ./docker-tmp login
docker --config ./docker-tmp buildx create --use
docker --config ./docker-tmp buildx build --push \
  --platform linux/arm/v7,linux/arm64/v8,linux/amd64 \
  --tag bbricardo/fritzinfluxdb:latest \
  --tag bbricardo/fritzinfluxdb:${1} .

rm -rf ./docker-tmp

# EOF