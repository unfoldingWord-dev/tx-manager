from __future__ import unicode_literals, print_function
import logging
from logging import Logger
from aws_tools.s3_handler import S3Handler
from aws_tools.dynamodb_handler import DynamoDBHandler
from aws_tools.lambda_handler import LambdaHandler
from gogs_tools.gogs_handler import GogsHandler


class Handler(object):

    def __init__(self, logger=None,
                 dynamodb_handler_class=DynamoDBHandler,
                 s3_handler_class=S3Handler,
                 lambda_handler_class=LambdaHandler,
                 gogs_handler_class=GogsHandler,
                 **kwargs):
        """
        :param Logger logger:
        :param class dynamodb_handler_class:
        :param class s3_handler_class:
        :param class lambda_handler_class:
        :param class gogs_handler_class:
        :param kwargs: for subclasses
        """
        if logger:
            self.logger = logger
        else:
            logging.basicConfig()
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
        self.dynamodb_handler_class = dynamodb_handler_class
        self.s3_handler_class = s3_handler_class
        self.lambda_handler_class = lambda_handler_class
        self.gogsl_handler_class = gogs_handler_class

    def handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        try:
            return self.__handle(event, context)
        except Exception as e:
            e.message = 'Bad Request: {0}'.format(e.message)
            self.logger.exception(e)

    def __handle(self, event, context):
        """
        Dummy function for handlers. Override this so handle() will catch the exception and make it a "Bad Request: "
        :param dict event:
        :param context:
        :return dict:
        """
        pass

    @staticmethod
    def retrieve(dictionary, key, dict_name=None):
        """
        Retrieves a value from a dictionary, raising an error message if the
        specified key is not valid
        :param dict dictionary:
        :param any key:
        :param str|unicode dict_name: name of dictionary, for error message
        :return: value corresponding to key
        """
        if key in dictionary:
            return dictionary[key]
        dict_name = "dictionary" if dict_name is None else dict_name
        raise Exception('{k} not found in {d}'.format(k=repr(key), d=dict_name))
