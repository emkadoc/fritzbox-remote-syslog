#!/bin/bash
IMAGE_NAME="fritzbox-remote-syslog"
BUILD_CONTEXT="."

if [ -z "$1" ]; then
  echo "1: $0 arm64"
  echo "2: $0 amd64"
  exit 1
fi

PLATFORM=$1

docker buildx build --platform "linux/${PLATFORM}" --load -t "${IMAGE_NAME}" "${BUILD_CONTEXT}"