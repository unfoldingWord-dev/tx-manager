from __future__ import print_function, unicode_literals

from libraries.linters.usfm_linter import UsfmLinter
from libraries.linters.obs_linter import ObsLinter
from libraries.linters.udb_linter import UdbLinter
from libraries.linters.ulb_linter import UlbLinter
from libraries.linters.ta_linter import TaLinter
from libraries.linters.tn_linter import TnLinter
from libraries.linters.tq_linter import TqLinter
from libraries.linters.tw_linter import TwLinter
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.resource_container.ResourceContainer import BIBLE_RESOURCE_TYPES


class LinterHandler:
    
    def __init__(self, resource_id, **kwargs):
        """
        :param string resource_id:
        :param dict **kwargs: so we can pass other arguments and not throw an exception
        """
        self.resource_id = resource_id

    def get_linter_class(self):
        if self.resource_id == 'obs':
            return ObsLinter
        elif self.resource_id == 'ta':
            return TaLinter
        elif self.resource_id == 'tn':
            return TnLinter
        elif self.resource_id == 'tq':
            return TqLinter
        elif self.resource_id == 'tw':
            return TwLinter
        elif self.resource_id == 'udb':
            return UdbLinter
        elif self.resource_id == 'ulb':
            return UlbLinter
        elif self.resource_id in BIBLE_RESOURCE_TYPES:
            return UsfmLinter
        else:
            return MarkdownLinter
