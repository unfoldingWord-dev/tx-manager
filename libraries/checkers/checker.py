from __future__ import print_function, unicode_literals
from abc import ABCMeta, abstractmethod
from libraries.converters.convert_logger import ConvertLogger


class Checker(object):
    __metaclass__ = ABCMeta

    def __init__(self, preconvert_dir, converted_dir, log=None):
        self.preconvert_dir = preconvert_dir
        self.converted_dir = converted_dir
        self.log = log
        if not self.log:
            self.log = ConvertLogger()

    @abstractmethod
    def run(self):
        pass
