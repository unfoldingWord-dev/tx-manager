from __future__ import unicode_literals, print_function
from six import iteritems


class TxObject(object):
    db_fields = []

    def __init__(self, quiet=False):
        self.quiet = quiet
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
        if not self.quiet:
            print(message)
        self.log.append(message)

    def error_message(self, message):
        if not self.quiet:
            print(message)
        self.errors.append(message)

    def warning_message(self, message):
        if not self.quiet:
            print(message)
        self.warnings.append(message)
