from __future__ import unicode_literals, print_function
from six import string_types
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from object import TxObject


class TxManifest(TxObject):
    db_fields = [
        'repo_name',
        'user_name',
        'lang_code',
        'resource_id',
        'resource_type',
        'title',
        'views',
        'last_updated',
        'manifest'
    ]

    def __init__(self, data):
        # Init attributes
        self.repo_name = None
        self.user_name = None
        self.lang_code = None
        self.resource_id = None
        self.resource_type = None
        self.title = None
        self.views = 0
        self.last_updated = None
        self.manifest = {}

        super(TxManifest, self).__init__()

        if isinstance(data, dict):
            self.populate(data)
