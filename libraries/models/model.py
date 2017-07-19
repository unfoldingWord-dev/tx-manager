from __future__ import unicode_literals, print_function
import copy
from six import iteritems, string_types


class Model(object):
    db_keys = []
    db_fields = []
    default_values = {}

    def __init__(self, data=None, db_handler=None):
        self.db_handler = db_handler
        if isinstance(data, dict):
            self.populate(data)
            if self.db_handler and len(data) == len(self.db_keys) and data.keys().sort() == self.db_keys.sort():
                self.load()
        elif isinstance(data, string_types) and len(self.db_keys) == 1:
            setattr(self, self.db_keys[0], data)
            if self.db_handler:
                self.load()

    def populate(self, data, clear_before_populate=True):
        if clear_before_populate:
            self.clear_db_fields()
        if data and isinstance(data, dict):
            for field, value in iteritems(data):
                if hasattr(self, field):
                    setattr(self, field, value)
        return self

    def clear_db_fields(self):
        for field in self.db_fields:
            if hasattr(self, field):
                if field in self.default_values:
                    setattr(self, field, copy.copy(self.default_values[field]))
                else:
                    setattr(self, field, None)

    def get_keys(self):
        keys = {}
        for key in self.db_keys:
            if hasattr(self, key):
                keys[key] = getattr(self, key)
        return keys

    def get_db_data(self):
        data = {}
        for field in self.db_fields:
            if hasattr(self, field):
                data[field] = getattr(self, field)
            else:
                data[field] = None
        return data

    def insert(self, data=None):
        if data:
            self.populate(data, clear_before_populate=False)
        self.db_handler.insert_item(self.get_db_data())
        return self

    def load(self, data=None):
        if data:
            self.populate(data, clear_before_populate=False)
        self.populate(self.db_handler.get_item(self.get_keys()))
        return self

    def update(self, data=None):
        if not data:
            data = self.get_db_data()
        for field in data.keys():
            if field not in self.db_fields or field in self.db_keys:
                data.pop(field)
            else:
                setattr(self, field, data[field])
        self.db_handler.update_item(self.get_keys(), data)
        return self

    def delete(self):
        self.db_handler.delete_item(self.get_keys())

    def query(self, query=None):
        items = self.db_handler.query_items(query)
        models = []
        if items and len(items):
            for item in items:
                models.append(self.__class__(item))
        return models
