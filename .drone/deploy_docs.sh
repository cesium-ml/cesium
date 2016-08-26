#!/bin/bash
if [[ $TRAVIS_PULL_REQUEST == false && $TRAVIS_BRANCH == "master" &&
    $TRAVIS_PYTHON_VERSION == 3.5 && -n "$GH_TOKEN" ]]
then
    # See https://help.github.com/articles/creating-an-access-token-for-command-line-use/ for how to generate a token
    # See http://docs.travis-ci.com/user/encryption-keys/ for how to generate
    # a secure variable on Travis
    echo "-- pushing docs --"

    (
    git clone --quiet --branch=gh-pages https://${GH_REF} doc_build
    cp -r doc/_build/html/* doc_build/

    cd doc_build
    git config user.email "travis@travis-ci.com"
    git config user.name "Travis Bot"

    git add -A
    git commit -m "Deployed to GitHub Pages"
    git push --force --quiet "https://${GH_TOKEN}@${GH_REF}" gh-pages > /dev/null 2>&1
    )
else
    echo "-- will only push docs from master --"
fi
