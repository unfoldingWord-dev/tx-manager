from __future__ import unicode_literals, print_function
from six import string_types
from libraries.models.model import Model


class TxModule(Model):
    db_keys = [
        'name'
    ]

    db_fields = [
        'name',
        'input_format',
        'options',
        'output_format',
        'private_links',
        'public_links',
        'resource_types',
        'type',
        'version',
    ]

    default_values = {
        'options': [],
        'output_format': [],
        'private_links': [],
        'public_links': [],
        'resource_types': [],
        'version': 1,
    }

    def __init__(self, data=None, **kwargs):
        """Init attributes"""
        self.name = None
        self.input_format = None
        self.options = []
        self.output_format = []
        self.private_links = []
        self.public_links = []
        self.resource_types = []
        self.type = None
        self.version = 1

        super(TxModule, self).__init__(**kwargs)

        if isinstance(data, dict):
            self.populate(data)
        elif isinstance(data, string_types):
            self.name = data
            if self.db_handler:
                self.load()
