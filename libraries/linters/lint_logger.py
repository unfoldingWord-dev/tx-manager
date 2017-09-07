from __future__ import unicode_literals, print_function
import logging


class LintLogger(object):
    def __init__(self):
        self.warnings = []
        self.logger = logging.getLogger('tx-manager')
        self.logger.addHandler(logging.NullHandler())

    def warning(self, msg):
        self.warnings.append(msg)
        self.logger.debug("LINT ISSUE: {}".format(msg))
