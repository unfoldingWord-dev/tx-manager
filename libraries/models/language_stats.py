from __future__ import unicode_literals, print_function
from libraries.models.model import Model
from libraries.app.app import App


class LanguageStats(Model):
    db_keys = [
        'lang_code',
    ]

    db_fields = [
        'lang_code',
        'views',
        'last_updated',
        'monitor',
    ]

    default_values = {
        'views': 0,
        'monitor': True,
    }

    def __init__(self, *args, **kwargs):
        # Init attributes
        self.lang_code = None
        self.views = 0
        self.last_updated = None
        self.monitor = True
        if 'db_handler' not in kwargs or not kwargs['db_handler']:
            kwargs['db_handler'] = App.language_stats_db_handler
        super(LanguageStats, self).__init__(*args, **kwargs)
