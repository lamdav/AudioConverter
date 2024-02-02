#!/bin/bash

set -eu

echo "#########################################"
echo "Starting ${GITHUB_WORKFLOW}:${GITHUB_ACTION}"

rm -rf ./dist
poetry publish --build 

echo "#########################################"
echo "Completed ${GITHUB_WORKFLOW}:${GITHUB_ACTION}"
