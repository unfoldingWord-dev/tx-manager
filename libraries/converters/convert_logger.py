from __future__ import unicode_literals, print_function
from libraries.app.app import App


class ConvertLogger(object):
    def __init__(self):
        self.logs = {
            "error": [],
            "info": [],
            "warning": [],
        }

    def log(self, log_type, msg):
        if log_type in self.logs:
            self.logs[log_type].append(msg)
            App.logger.debug("CONVERSION {0}: {1}".format(log_type.upper(), msg))

    def warning(self, msg):
        self.log("warning", msg)

    def error(self, msg):
        self.log("error", msg)

    def info(self, msg):
        self.log("info", msg)
