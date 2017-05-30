from __future__ import unicode_literals
import json
from general_tools import url_utils


class TdLanguage(object):

    language_list = None

    def __init__(self, json_obj=None):
        """
        Optionally accepts an object for initialization.
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
    def get_languages():
        """
        Gets the list of Languages. Retrieves the list from tD if needed.
        :return: list<TdLanguage>
        """
        if TdLanguage.language_list is None:
            TdLanguage.language_list = []
            lang_file = 'http://td.unfoldingword.org/exports/langnames.json'
            langs = json.loads(url_utils.get_url(lang_file))
            for lang in langs:
                TdLanguage.language_list.append(TdLanguage(lang))
        return TdLanguage.language_list

    @staticmethod
    def get_language(lang):
        languages = TdLanguage.get_languages()
        found = [x for x in languages if x.lc == lang]
        if len(found):
            return found[0]
