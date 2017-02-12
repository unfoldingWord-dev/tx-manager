from __future__ import unicode_literals, print_function
from six import string_types
from object import TxObject


class TxModule(TxObject):
    db_fields = [
        'name',
        'input_format',
        'options',
        'output_format',
        'private_links',
        'public_links',
        'resource_types',
        'type',
        'version'
    ]

    def __init__(self, data, quiet=False):
        # Init attributes
        self.name = None
        self.input_format = None
        self.options = []
        self.output_format = []
        self.private_links = []
        self.public_links = []
        self.resource_types = []
        self.type = None
        self.version = 1

        if isinstance(data, dict):
            self.populate(data)
        elif isinstance(data, string_types):
            self.populate({'name': data})

        super(TxModule, self).__init__(quiet)
