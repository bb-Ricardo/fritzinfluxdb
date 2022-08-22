#!/usr/bin/env bash

DOCKERHUB_IMAGE_PATH="bbricardo/fritzinfluxdb"

[[ -z "$1" ]] && echo "please define a version tag" && exit

read -p "Is this a beta (b) release or final (f) release: " -n1 ANSWER && echo

[[ $ANSWER =~ [bB] ]] && FINAL=false
[[ $ANSWER =~ [fF] ]] && FINAL=true
[[ -z "${FINAL+default}" ]] && echo "Please select 'b' or 'f'." && exit 1

unset DOCKER_TLS_VERIFY
unset DOCKER_HOST
unset DOCKER_CERT_PATH

docker --config ./docker-tmp login
docker --config ./docker-tmp buildx create --use
if [[ $FINAL ]]; then
  docker --config ./docker-tmp buildx build --push \
    --platform linux/arm/v7,linux/arm64/v8,linux/amd64 \
    --tag ${DOCKERHUB_IMAGE_PATH}:latest \
    --tag ${DOCKERHUB_IMAGE_PATH}:${1} .
  [[ $? -ne 0 ]] && exit 1
  which docker-pushrm >/dev/null 2>&1 &&  docker-pushrm ${DOCKERHUB_IMAGE_PATH}:latest
else
  docker --config ./docker-tmp buildx build --push \
    --platform linux/arm/v7,linux/arm64/v8,linux/amd64 \
    --tag ${DOCKERHUB_IMAGE_PATH}:${1} .
fi

rm -rf ./docker-tmp

# EOF