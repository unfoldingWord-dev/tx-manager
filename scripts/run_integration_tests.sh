#!/usr/bin/env bash
# default is to run all integration tests against against our AWS test site.

#   !!!! Warning this is very slow to run all the tests.
#   You must first set up ./aws/config and ./aws/credentials for the test site
#       (or setup credentials for the prod site if you are going to run tests on prod or dev

#   And setup the gogs token: export GOGS_USER_TOKEN=<token>

# parameters are: ./scripts/run_integration_tests.sh [site] [integration_test_name]
#   site can be one of 'prod', 'dev', 'test' where the default is 'test'
#   integration_test_name is the name of a single test to run. The default is to run ALL TESTS! (which is very slow).
#       see the list of tests in tests/integration_tests/test_conversion.py

# to run a single basic bible conversion test do:
#
#   ./scripts/run_integration_tests.sh test_ts_mat_conversion
#
#       (see the list of tests in tests/integration_tests/test_conversion.py)

# to run a single OBS conversion test do:
#
#   ./scripts/run_integration_tests.sh test_obs_conversion
#

# to run a multi-book bible conversion test do:
#
#   ./scripts/run_integration_tests.sh test_usfm_en_bundle_conversion
#

set -e

cd "$( dirname "${BASH_SOURCE[0]}" )/.."

export TEST_DEPLOYED=test_deployed
# default to run on test
export TRAVIS_BRANCH=test

if [ -z $GOGS_USER_TOKEN ]
then
    echo "Need to set GOGS_USER_TOKEN"
fi

echo ""
echo "*** Running Integration Tests"
echo ""

if [ "$#" -ge 1 ]
then

    testTarget=$1
    testName=$2

    if [ "$1" == "dev" ]
    then
        echo "Running tests on 'dev'"
        export TRAVIS_BRANCH=develop

    elif [ "$1" == "prod" ]
    then
        echo "Running tests on 'prod'"
        export TRAVIS_BRANCH=master

    elif [ "$1" == "test" ]
    then
        echo "Running tests on 'test'"
        export TRAVIS_BRANCH=test

    else
        # if first parameter does match a site, use as test name
        testName=$1
        echo "Default to running tests on 'test'"
    fi
fi


if [ -z "$testName" ]
then
  echo "No test name found, so running all.  This is very slow.  Do CTRL-C to stop"
  python -m unittest -v tests.integration_tests.test_conversion
else
  echo "Running single test: $testName"
  python -m unittest -v tests.integration_tests.test_conversion.TestConversions.$testName
fi

echo ""
echo "Completed Successfully"
