import mock
import unittest

from gogs_tools.gogs_handler import GogsHandler


class GogsHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handler = GogsHandler("https://www.example.com/")
        cls.handler.gogs_api = mock.MagicMock()

    def setUp(self):
        self.handler.gogs_api.reset_mock()

    def test_authenticate_user_token(self):
        def valid_auth(token):
            return token.token == "valid"
        self.handler.gogs_api.valid_authentication = valid_auth
        self.assertTrue(self.handler.authenticate_user_token("valid"))
        self.assertFalse(self.handler.authenticate_user_token("invalid"))

    def test_get_user(self):
        def valid_auth(token):
            return token.token == "valid"
        self.handler.gogs_api.valid_authentication = valid_auth
        mock_user = mock.MagicMock()
        self.handler.gogs_api.authenticated_user.return_value = mock_user
        self.assertIs(self.handler.get_user("valid"), mock_user)
        self.assertIsNone(self.handler.get_user("invalid"))
