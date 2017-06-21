#!/usr/bin/env bash
################################################################################
#
# The AWS environment variables will only be available when merging a
# pull request from develop into master due to travis security settings.
#
################################################################################

if [[ ${TRAVIS_EVENT_TYPE} == "push" && (${TRAVIS_BRANCH} == "master" || ${TRAVIS_BRANCH} == "develop") && ${TRAVIS_SECURE_ENV_VARS} == "true" ]]
then
    echo "Deploying..."
    repoDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
    thisDir="$( dirname "${repoDir}" )"
    "${thisDir}/apex" deploy -C "${repoDir}" --env ${TRAVIS_BRANCH}
else
    echo "Not deploying:"
    echo "  TRAVIS_EVENT_TYPE = $TRAVIS_EVENT_TYPE (must be 'push')"
    echo "  TRAVIS_BRANCH = $TRAVIS_BRANCH (must be 'master' or 'develop')"
    echo "  TRAVIS_SECURE_ENV_VARS = $TRAVIS_SECURE_ENV_VARS (must be 'true')"
fi
