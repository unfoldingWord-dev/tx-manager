from __future__ import unicode_literals, print_function
from abc import ABCMeta, abstractmethod
import json
from exceptions import EnvironmentError


class Handler(object):
    __metaclass__ = ABCMeta

    def handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        print("EVENT:")
        print(json.dumps(event))
        try:
            return self._handle(event, context)
        except Exception as e:
            raise EnvironmentError('Bad Request: {}'.format(e.message))

    @abstractmethod
    def _handle(self, event, context):
        """
        Dummy function for handlers. Override this so handle() will catch the exception and make it a "Bad Request: "
        :param dict event:
        :param context:
        :return dict:
        """
        raise NotImplementedError()

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
