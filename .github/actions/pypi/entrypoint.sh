#!/bin/bash

set -eu

echo "#########################################"
echo "Starting ${GITHUB_WORKFLOW}:${GITHUB_ACTION}"

rm -rf ./dist
python setup.py sdist bdist_wheel
twine upload dist/*

echo "#########################################"
echo "Completed ${GITHUB_WORKFLOW}:${GITHUB_ACTION}"
