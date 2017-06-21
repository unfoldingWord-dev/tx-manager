#!/usr/bin/env bash

set -e

cd "$( dirname "${BASH_SOURCE[0]}" )/.."

export TEST_DEPLOYED=test_deployed
python -m unittest -v tests.integration_tests.test_conversion

echo "Completed Successfully"
