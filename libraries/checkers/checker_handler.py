from __future__ import print_function, unicode_literals
from libraries.checkers.bible_checker import BibleChecker
from libraries.checkers.obs_checker import ObsChecker
from libraries.checkers.udb_checker import UdbChecker
from libraries.checkers.ulb_checker import UlbChecker
from libraries.checkers.ta_checker import TaChecker
from libraries.checkers.tn_checker import TnChecker
from libraries.checkers.tq_checker import TqChecker
from libraries.checkers.tw_checker import TwChecker
from libraries.resource_container.ResourceContainer import BIBLE_RESOURCE_TYPES


def get_checker(resource_id):
    if resource_id == 'obs':
        return ObsChecker
    elif resource_id == 'ta':
        return TaChecker
    elif resource_id == 'tn':
        return TnChecker
    elif resource_id == 'tq':
        return TqChecker
    elif resource_id == 'tw':
        return TwChecker
    elif resource_id == 'udb':
        return UdbChecker
    elif resource_id == 'ulb':
        return UlbChecker
    elif resource_id in BIBLE_RESOURCE_TYPES:
        return BibleChecker
