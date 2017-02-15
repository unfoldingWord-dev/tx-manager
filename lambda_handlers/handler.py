from __future__ import unicode_literals, print_function


class Handler(object):

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
            raise e

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
