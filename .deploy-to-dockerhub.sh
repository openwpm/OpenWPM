#!/usr/bin/env bash

# stop on errors
set -e

if [ "${DOCKER_USER}" != "" ]; then
    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
    if [ "${TRAVIS_BRANCH}" == "master" ]; then
      # deploy master
      docker tag app:build ${DOCKERHUB_REPO}:latest
      docker push ${DOCKERHUB_REPO}:latest
    elif  [ ! -z "${TRAVIS_TAG}" ]; then
      # deploy a release tag...
      echo "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
      docker tag app:build "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
      docker images
      docker push "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
    elif  [ ! -z "${TRAVIS_COMMIT}" ]; then
      # deploy a commit tag...
      echo "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
      docker tag app:build "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
      docker images
      docker push "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
    fi
else
    echo "Deploy to Docker Hub skipped since the DOCKER_USER env var is not available"
fi

exit 0
