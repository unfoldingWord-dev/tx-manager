from __future__ import unicode_literals, print_function
import logging
from six import iteritems


class TxObject(object):
    db_fields = [
        'log',
        'warnings',
        'errors'
    ]

    def __init__(self):
        self.log = []
        self.warnings = []
        self.errors = []

    def populate(self, data):
        for key, value in iteritems(data):
            if hasattr(self, key):
                setattr(self, key, value)

    def get_db_data(self):
        data = {}
        for field in self.db_fields:
            if hasattr(self, field):
                data[field] = getattr(self, field)
            else:
                data[field] = None
        return data

    def log_message(self, message):
        self.log.append(message)

    def error_message(self, message):
        self.errors.append(message)

    def warning_message(self, message):
        self.warnings.append(message)
