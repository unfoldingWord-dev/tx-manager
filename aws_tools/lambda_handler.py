# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

import json
import boto3

from boto3 import Session

class LambdaHandler(object):
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_region_name='us-west-2'):
        if aws_access_key_id and aws_secret_access_key:
            session = Session(aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key,
                                   region_name=aws_region_name)
            self.client = session.client('lambda')
        else:
            self.client = boto3.client('lambda')

    def invoke(self, function_name, payload):
        return self.client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )
