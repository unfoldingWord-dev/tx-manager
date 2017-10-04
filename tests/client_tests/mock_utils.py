"""
Utilities for mocking out AWS handlers
"""
from mock import MagicMock

valid_token = 'token'

class MockUser(MagicMock):
    username = 'username'

def get_user(self, token):
    if token == valid_token:
        user = MockUser()
        return user
    else:
        return None
