"""
Utilities for mocking out AWS handlers
"""

import json

from mock import MagicMock


def mock_db_handler(data, keyname):
    """
    :param dict data: dict from keys to data
    :param string keyname:
    """
    def setup_resources():
        pass

    def get_item(keys):
        key = keys[keyname]
        if key in data:
            return data[key]
        return None

    def query_items(*ignored):
        return data.values()

    handler = MagicMock()
    handler.get_item = MagicMock(side_effect=get_item)
    handler.query_items = MagicMock(side_effect=query_items)
    handler.setup_resources = MagicMock(side_effects=setup_resources)
    handler.mock_data = data
    return handler


def mock_gogs_handler(tokens):
    """
    :param tokens: collection of valid user tokens
    """
    def get_user(token):
        if token in tokens:
            return MagicMock()
        else:
            return None

    handler = MagicMock()
    handler.get_user = MagicMock(side_effect=get_user)
    return handler


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.text = json.dumps(json_data)
        self.status_code = status_code

    def json(self):
        return self.json_data


# This method will be used by the mock to replace requests.post() when the job is good
def mock_requests_post_good(*args, **kwargs):
    return MockResponse({
        'Payload': {
            "log": [],
            "warnings": ['Missing something'],
            "errors": [],
            "success": True,
            "message": "All good"
        }
    }, 200)


# This method will be used by the mock to replace requests.post() when the job is bad
def mock_requests_post_bad(*args, **kwargs):
    return MockResponse({
        'Payload': {
            "log": [],
            "warnings": ['Missing something'],
            "errors": ['Some error'],
            "success": False,
            "message": "All bad"
        }
    }, 200)
