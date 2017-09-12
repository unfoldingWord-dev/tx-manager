from __future__ import unicode_literals, print_function
import json
import traceback
from abc import ABCMeta, abstractmethod
from exceptions import EnvironmentError
from libraries.app.app import App


class Handler(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.data = None

    def handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        if 'vars' in event:
            App(**event['vars'])

        App.logger.debug("EVENT:")
        App.logger.debug(json.dumps(event))

        self.data = {}
        if 'data' in event and isinstance(event['data'], dict):
            self.data = event['data']
        if 'body-json' in event and isinstance(event['body-json'], dict):
            self.data.update(event['body-json'])

        try:
            return self._handle(event, context)
        except Exception as e:
            App.logger.error(e.message)
            App.logger.error('{0}: {1}'.format(str(e), traceback.format_exc()))
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
