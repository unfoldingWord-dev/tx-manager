from __future__ import unicode_literals, print_function


class ConvertLogger(object):
    def __init__(self):
        self.logs = {
            "error": [],
            "info": [],
            "warning": [],
        }

    def log(self, type, msg):
        if type in self.logs:
            self.logs[type].append(msg)

    def warning(self, msg):
        self.log("warning", msg)

    def error(self, msg):
        self.log("error", msg)

    def info(self, msg):
        self.log("info", msg)
