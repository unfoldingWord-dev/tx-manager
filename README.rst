master:

.. image:: https://travis-ci.org/unfoldingWord-dev/tx-manager.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/unfoldingWord-dev/tx-manager

.. image:: https://coveralls.io/repos/github/unfoldingWord-dev/tx-manager/badge.svg?branch=master)
    :alt: Coveralls
    :target: https://coveralls.io/github/unfoldingWord-dev/tx-manager?branch=master

develop:

.. image:: https://travis-ci.org/unfoldingWord-dev/tx-manager.svg?branch=develop
    :alt: Build Status
    :target: https://travis-ci.org/unfoldingWord-dev/tx-manager

.. image:: https://coveralls.io/repos/github/unfoldingWord-dev/tx-manager/badge.svg?branch=develop)
    :alt: Coveralls
    :target: https://coveralls.io/github/unfoldingWord-dev/tx-manager?branch=develop


tx-manager
==========

This is a python module used with tx-manager-lambda

Project description at https://github.com/unfoldingWord-dev/door43.org/wiki/tX-Development-Architecture#tx-manager-module.

Issue for its creation at https://github.com/unfoldingWord-dev/door43.org/issues/53


tX Pipeline
===========

1. webhook
2. job_request
3. job_handle
4. [CONVERTER]
5. callback
6. door43_deploy
7. d43_catalog
