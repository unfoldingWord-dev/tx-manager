from __future__ import unicode_literals, print_function
import os
import json
import boto3
import botocore
from boto3.session import Session
from libraries.general_tools.file_utils import get_mime_type


class S3Handler(object):
    def __init__(self, bucket_name=None, aws_access_key_id=None, aws_secret_access_key=None,
                 aws_region_name=None):
        self.bucket_name = bucket_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region_name = aws_region_name
        self.bucket = None
        self.client = None
        self.resource = None
        self.setup_resources()

    def setup_resources(self):
        if self.aws_access_key_id and self.aws_secret_access_key:
            session = Session(aws_access_key_id=self.aws_access_key_id,
                              aws_secret_access_key=self.aws_secret_access_key,
                              region_name=self.aws_region_name)
            self.resource = session.resource('s3')
            self.client = session.client('s3')
        else:
            self.resource = boto3.resource('s3',
                                           aws_access_key_id=self.aws_access_key_id,
                                           aws_secret_access_key=self.aws_secret_access_key,
                                           region_name=self.aws_region_name)
            self.client = boto3.client('s3',
                                       aws_access_key_id=self.aws_access_key_id,
                                       aws_secret_access_key=self.aws_secret_access_key,
                                       region_name=self.aws_region_name)

        self.bucket_name = self.bucket_name
        self.bucket = None
        if self.bucket_name:
            self.bucket = self.resource.Bucket(self.bucket_name)

    def download_file(self, key, local_file):
        """
        Download file from S3 bucket. Similar to s3.download_file except that does
        not play nicely with moto, this however, does.
        :param string key: object to download
        :param string local_file: file to download to
        """
        body = self.resource.Object(bucket_name=self.bucket_name, key=key).get()['Body']
        with open(local_file, 'wb') as f:
            for chunk in iter(lambda: body.read(1024), b''):
                f.write(chunk)

    # Downloads all the files in S3 that have a prefix of `key_prefix` from `bucket` to the `local` directory
    def download_dir(self, key_prefix, local):
        paginator = self.client.get_paginator('list_objects')
        for result in paginator.paginate(Bucket=self.bucket_name, Delimiter='/', Prefix=key_prefix):
            if result.get('CommonPrefixes') is not None:
                for subdir in result.get('CommonPrefixes'):
                    self.download_dir(subdir.get('Prefix'), local)
            if result.get('Contents') is not None:
                for file in result.get('Contents'):
                    local_file = os.path.join(local, file.get('Key'))
                    if local_file.endswith('/'):
                        pass
                    else:
                        if not os.path.exists(os.path.dirname(local_file)):
                            os.makedirs(os.path.dirname(local_file))
                        self.download_file(file.get('Key'), local_file)

    def key_exists(self, key, bucket_name=None):
        if not bucket_name:
            bucket = self.bucket
        else:
            bucket = self.resource.Bucket(bucket_name)

        try:
            bucket.Object(key=key).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                exists = False
            else:
                raise
        else:
            exists = True

        return exists

    def key_modified_time(self, key, bucket_name=None):
        """
        get last modified time for key
        :param key:
        :param bucket_name:
        :return:
        """
        if not bucket_name:
            bucket = self.bucket
        else:
            bucket = self.resource.Bucket(bucket_name)

        try:
            s3_object = bucket.Object(key=key)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return None
            else:
                raise

        return s3_object.last_modified

    def copy(self, from_key, from_bucket=None, to_key=None, catch_exception=True):
        if not to_key:
            to_key = from_key
        if not from_bucket:
            from_bucket = self.bucket_name

        if catch_exception:
            try:
                return self.resource.Object(bucket_name=self.bucket_name, key=to_key).copy_from(
                    CopySource='{0}/{1}'.format(from_bucket, from_key))
            except:
                return False
        else:
            return self.resource.Object(bucket_name=self.bucket_name, key=to_key).copy_from(
                CopySource='{0}/{1}'.format(from_bucket, from_key))

    def replace(self, key, catch_exception=True):
        if catch_exception:
            try:
                return self.resource.Object(bucket_name=self.bucket_name, key=key).copy_from(
                    CopySource='{0}/{1}'.format(self.bucket_name, key), MetadataDirective='REPLACE')
            except:
                return False
        else:
            return self.resource.Object(bucket_name=self.bucket_name, key=key).copy_from(
                CopySource='{0}/{1}'.format(self.bucket_name, key), MetadataDirective='REPLACE')

    def upload_file(self, path, key, cache_time=600, content_type=None):
        """
        Upload file to S3 storage. Similar to the s3.upload_file, however, that
        does not work nicely with moto, whereas this function does.
        :param string path: file to upload
        :param string key: name of the object in the bucket
        """
        with open(path, 'rb') as f:
            binary = f.read()
        if content_type is None:
            content_type = get_mime_type(path)
        self.bucket.put_object(
            Key=key,
            Body=binary,
            ContentType=content_type,
            CacheControl='max-age={0}'.format(cache_time)
        )

    def get_object(self, key):
        return self.resource.Object(bucket_name=self.bucket_name, key=key)

    def redirect(self, key, location):
        self.bucket.put_object(Key=key, WebsiteRedirectLocation=location, CacheControl='max-age=0')

    def get_file_contents(self, key, catch_exception=True):
        if catch_exception:
            try:
                return self.get_object(key).get()['Body'].read()
            except:
                return None
        else:
            return self.get_object(key).get()['Body'].read()

    def get_json(self, key, catch_exception = True):
        if catch_exception:
            try:
                return json.loads(self.get_file_contents(key))
            except:
                return {}
        else:
            return json.loads(self.get_file_contents(key, catch_exception))

    def get_objects(self, prefix=None, suffix=None):
        filtered = []
        objects = self.bucket.objects.filter(Prefix=prefix)
        if objects:
            if suffix:
                for obj in objects:
                    if obj.key.endswith(suffix):
                        filtered.append(obj)
            else:
                filtered = objects
        return filtered

    def put_contents(self, key, body, catch_exception=True):
        if catch_exception:
            try:
                return self.get_object(key).put(Body=body)
            except:
                return None
        else:
            return self.get_object(key).put(Body=body)

    def delete_file(self, key, catch_exception=True):
        if catch_exception:
            try:
                return self.resource.Object(bucket_name=self.bucket_name, key=key).delete()
            except:
                return False
        else:
            return self.resource.Object(bucket_name=self.bucket_name, key=key).delete()

    def create_bucket(self, bucket_name=None, catch_exception=True):
        if not bucket_name:
            bucket_name = self.bucket_name
        if catch_exception:
            try:
                return self.resource.create_bucket(Bucket=bucket_name)
            except:
                return None
        else:
            return self.resource.create_bucket(Bucket=bucket_name)
