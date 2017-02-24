from __future__ import unicode_literals


class JsonObject(object):
    def __init__(self, value_dict):
        self.__dict__ = value_dict
