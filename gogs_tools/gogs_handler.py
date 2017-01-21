# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Richard Mahn <richard_mahn@wycliffeassociates.org>

from gogs_client import GogsApi
from gogs_client import Token


class GogsHandler(object):
    def __init__(self, gogs_url):
        self.gogs_url = gogs_url
        self.gogs_api = GogsApi(gogs_url)

    def authenticate_user_token(self, user_token):
        return self.gogs_api.valid_authentication(Token(user_token))

    def get_user(self, user_token):
        valid = self.authenticate_user_token(user_token)
        if valid:
            return self.gogs_api.authenticated_user(Token(user_token))
        else:
            return None
