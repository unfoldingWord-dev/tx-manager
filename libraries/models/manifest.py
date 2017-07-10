from __future__ import unicode_literals, print_function
from libraries.models.model import Model


class TxManifest(Model):
    db_keys = [
        'repo_name_lower',
        'user_name_lower',
    ]

    db_fields = [
        'repo_name_lower',
        'user_name_lower',
        'repo_name',
        'user_name',
        'lang_code',
        'resource_id',
        'resource_type',
        'title',
        'views',
        'last_updated',
        'manifest',
        'manifest_lower',
    ]

    default_values = {
        'views': 0,
        'manifest': {},
        'manifest_lower': {},
    }

    def __init__(self, *args, **kwargs):
        # Init attributes
        self.repo_name_lower = None
        self.user_name_lower = None
        self.repo_name = None
        self.user_name = None
        self.lang_code = None
        self.resource_id = None
        self.resource_type = None
        self.title = None
        self.views = 0
        self.last_updated = None
        self.manifest = {}
        self.manifest_lower = {}
        super(TxManifest, self).__init__(*args, **kwargs)
