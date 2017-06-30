#!/usr/bin/env python
"""
Touches every build_log.json file in a given s3 CDN bucket to trigger the door43 deploy to re-template the files

"""
import boto3
import logging
import sys
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_build_logs(bucket):
    build_logs = []
    objects = bucket.objects.filter(Prefix='u/')
    for obj in objects:
        if obj.key.endswith('/build_log.json'):
            build_logs.append(obj.key)
    return build_logs


def touch(client, bucket_name, key):
    source = bucket_name + "/" + key
    logger.info("Setting source key to %s" % source)
    try:
        client.copy_object(Bucket=bucket_name, CopySource=source, Key=key, StorageClass='REDUCED_REDUNDANCY')
        logger.info("Updated %s..." % key)
    except Exception as e:
        logger.error("--- Unable to modify key %s in bucket %s" % (key, bucket_name))
        logger.error(str(e))
    return


def main():
    if len(sys.argv) < 2:
        logger.critical('You must provide a bucket name!')
        exit(1)
    bucket_name = sys.argv[1]
    client = boto3.client('s3')
    resource = boto3.resource('s3')
    bucket = resource.Bucket(bucket_name)
    keys = get_build_logs(bucket)
    i = 0
    for k in keys:
        touch(client, bucket_name, k)
        i += 1
        if i == 500:
            time.sleep(300)
            i = 0


if __name__ == '__main__':
    main()

