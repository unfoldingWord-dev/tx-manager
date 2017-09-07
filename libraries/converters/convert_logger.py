from __future__ import unicode_literals, print_function
import logging


class ConvertLogger(object):
    def __init__(self):
        self.logs = {
            "error": [],
            "info": [],
            "warning": [],
        }
        self.logger = logging.getLogger('tx-manager')
        self.logger.addHandler(logging.NullHandler())

    def log(self, type, msg):
        if type in self.logs:
            self.logs[type].append(msg)
            self.logger.debug("CONVERSION {0}: {1}".format(type.upper(), msg))

    def warning(self, msg):
        self.log("warning", msg)

    def error(self, msg):
        self.log("error", msg)

    def info(self, msg):
        self.log("info", msg)
