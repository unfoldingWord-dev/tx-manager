#!/usr/bin/env bash

set -e

export TEST_DEPLOYED=test_deployed
python -m unittest -v tests.integration_tests.test_conversion

echo "Completed Successfully"
