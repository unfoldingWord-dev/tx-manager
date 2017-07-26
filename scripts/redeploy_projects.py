#!/usr/bin/env python
"""
Touches every build_log.json file in a given s3 CDN bucket to trigger the door43 deploy to re-template the files
1st parameter is bucket name (required)
2nd parameter is starting folder (default is '/u')

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
count = 0


def update_build_logs(client, bucket_name, prefix):
    global count

    # check for build log in folder
    key = prefix + 'build_log.json'
    result = client.list_objects(Bucket=bucket_name, Prefix=key)
    if 'Contents' in result:
        count += 1
        print(str(count) + ": Updating: " + key)
        touch(client, bucket_name, key)

    # get sub-folders
    result = client.list_objects(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
    if 'CommonPrefixes' in result:
        folders = []
        for object in result.get('CommonPrefixes'):
            key = object.get('Prefix')
            folders.append(key)
        for key in folders:
            print("Found folder: " + key)
            update_build_logs(client, bucket_name, key)


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
    prefix = 'u/'
    if len(sys.argv) > 2:
        prefix = sys.argv[2]
        print("Using prefix of '" + prefix + "'")
    client = boto3.client('s3')
    start = time.time()
    update_build_logs(client, bucket_name, prefix)
    elapsed_seconds = time.time() - start
    print("Done in '" + str(int(elapsed_seconds/60)) + "' minutes")


if __name__ == '__main__':
    main()
