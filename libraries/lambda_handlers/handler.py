from __future__ import unicode_literals, print_function
import json
import logging
import traceback
from abc import ABCMeta, abstractmethod
from exceptions import EnvironmentError
from libraries.app.app import App


class Handler(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        global db
        # Make Boto3 not be so noisy
        logging.getLogger('boto3').setLevel(logging.ERROR)
        logging.getLogger('botocore').setLevel(logging.ERROR)
        # Set up logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

    def handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        self.logger.debug("EVENT:")
        self.logger.debug(json.dumps(event))

        if 'vars' in event:
            App(event['vars'])
        if App.db_pass:
            App.setup_db()

        try:
            return self._handle(event, context)
        except Exception as e:
            self.logger.error(e.message)
            self.logger.error('{0}: {1}'.format(str(e), traceback.format_exc()))
            raise EnvironmentError('Bad Request: {}'.format(e.message))

    @abstractmethod
    def _handle(self, event, context):
        """
        Dummy function for handlers.

        Override this so handle() will catch the exception and make it a "Bad Request: "

        :param dict event:
        :param context:
        :return dict:
        """
        raise NotImplementedError()

    @staticmethod
    def retrieve(dictionary, key, dict_name=None, required=True, default=None):
        """
        Retrieves a value from a dictionary.

        raises an error message if the specified key is not valid

        :param dict dictionary:
        :param any key:
        :param str|unicode dict_name: name of dictionary, for error message
        :param bool required:
        :param any default:
        :return: value corresponding to key
        """
        if key in dictionary:
            return dictionary[key]
        if required:
            dict_name = "dictionary" if dict_name is None else dict_name
            raise Exception('\'{k}\' not found in {d}'.format(k=key, d=dict_name))
        else:
            return default
