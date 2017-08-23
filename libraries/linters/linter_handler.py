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
from libraries.resource_container.ResourceContainer import RC


class LinterHandler:
    
    def __init__(self, rc, **kwargs):
        """
        :param RC rc:
        :param dict **kwargs: so we can pass other arguments and not throw an exception
        """
        self.rc = rc

    def get_linter_class(self):
        if self.rc.resource.identifier == 'obs':
            return ObsLinter
        elif self.rc.resource.identifier == 'ta':
            return TaLinter
        elif self.rc.resource.identifier == 'tn':
            return TnLinter
        elif self.rc.resource.identifier == 'tq':
            return TqLinter
        elif self.rc.resource.identifier == 'tw':
            return TwLinter
        elif self.rc.resource.identifier == 'udb':
            return UdbLinter
        elif self.rc.resource.identifier == 'ulb':
            return UlbLinter
        elif self.rc.resource.identifier in BIBLE_RESOURCE_TYPES or self.rc.resource.file_ext == 'usfm':
            return UsfmLinter
        elif self.rc.resource.file_ext == 'md':
            return MarkdownLinter
        else:
            return MarkdownLinter
