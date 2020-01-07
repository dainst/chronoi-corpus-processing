#!/bin/bash
set -e
set -x

# the directory this script is in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# read the version from the VERSION file
version=`cat "${DIR}/VERSION"`

# Build & publish image on dockerhub
docker build --tag=dainst/chronoi-heideltime:latest "$DIR"
docker tag dainst/chronoi-heideltime:latest "dainst/chronoi-heideltime:${version}"
docker push "dainst/chronoi-heideltime:latest"
docker push "dainst/chronoi-heideltime:${version}"
