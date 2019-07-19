#!/usr/bin/env bash

# stop on errors
set -e

if [ "${DOCKER_USER}" == "" ]; then
  echo "Deploy to DockerHub skipped since the DOCKER_USER env var is not available"
  exit 0
fi
if [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
  echo "Deploy to DockerHub skipped since the current job is a Pull Request job"
  exit 0
fi

echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
if [ "${TRAVIS_BRANCH}" == "master" ]; then
  echo "Deploying master branch to DockerHub..."
  docker tag openwpm ${DOCKERHUB_REPO}:latest
  docker push ${DOCKERHUB_REPO}:latest
fi
if [ ! -z "${TRAVIS_TAG}" ]; then
  echo "Deploying release tag to DockerHub..."
  echo "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
  docker tag openwpm "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
  docker push "${DOCKERHUB_REPO}:${TRAVIS_TAG}"
fi
if [ ! -z "${TRAVIS_COMMIT}" ]; then
  echo "Deploying commit-based build to DockerHub..."
  echo "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
  docker tag openwpm "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
  docker push "${DOCKERHUB_REPO}:commit-${TRAVIS_COMMIT}"
fi

exit 0
