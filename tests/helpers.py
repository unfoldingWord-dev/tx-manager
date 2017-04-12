from __future__ import absolute_import, unicode_literals, print_function


class JsonObject(object):
    def __init__(self, value_dict):
        self.__dict__ = value_dict
