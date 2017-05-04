#!/bin/bash

set -e

if [[ $TRAVIS_PULL_REQUEST == false && \
      $TRAVIS_BRANCH == "master" && \
      $DEPLOY_DOCS == 1 ]]
then
    pip install doctr
    doctr deploy --gh-pages-docs '.' --deploy-repo "cesium-ml/docs"
else
    echo "-- will only push docs from master --"
fi

