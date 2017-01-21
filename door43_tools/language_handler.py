from __future__ import unicode_literals
import json
from general_tools.url_utils import get_url


class Language(object):
    def __init__(self, json_obj=None):
        """
        Class constructor. Optionally accepts an object for initialization.
        :param object json_obj: An object to initialize the instance member variables
        """
        # deserialize
        if json_obj:
            self.__dict__ = json_obj

        else:
            self.ln = ''
            self.gw = False
            self.ang = ''
            self.lr = ''
            self.ld = 'ltr'
            self.lc = ''
            self.alt = []
            self.pk = 0
            self.cc = []

    @staticmethod
    def load_languages():
        return_val = []

        lang_file = 'http://td.unfoldingword.org/exports/langnames.json'
        langs = json.loads(get_url(lang_file))
        for lang in langs:
            return_val.append(Language(lang))

        return return_val
