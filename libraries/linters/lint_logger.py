from __future__ import unicode_literals, print_function
from libraries.app.app import App


class LintLogger(object):
    def __init__(self):
        self.warnings = []

    def warning(self, msg):
        self.warnings.append(msg)
        App.logger.debug("LINT ISSUE: {}".format(msg))
