#!/usr/bin/env python
"""
Adds N number of rows of dummy data to the manifest table specified

"""
from __future__ import unicode_literals, print_function
import boto3
import logging
import sys


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def remove_dummy_data_from_manifest_table(table_name):
    resource = boto3.resource('dynamodb')
    dbtable = resource.Table(table_name)

    delete_success = True
    i = 1
    while delete_success:
        repo_name = 'repo{0}'.format(i)
        user_name = 'user{0}'.format(i)
        key = {'repo_name': repo_name, 'user_name': user_name}
        response = dbtable.get_item(Key=key)
        if 'Item' in response:
            dbtable.delete_item(Key=key)
        else:
            delete_success = False
            logger.info('Ended deleting at repo{0}, user{0}'.format(i))
        i += 1


def main():
    if len(sys.argv) < 2:
        logger.critical('You must provide a table name.')
        logger.critical('Example: ./remove_dummy_data_from_manifest_table.py tx-manifest')
        exit(1)
    table_name = sys.argv[1]
    remove_dummy_data_from_manifest_table(table_name)


if __name__ == '__main__':
    main()
