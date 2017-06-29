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

    def get_item_count():
        return len(data.values())

    def query_items(query=None, only_fields_with_values=True, queryChunkLimit=-1):
        return data.values()

    handler = MagicMock()
    handler.get_item = MagicMock(side_effect=get_item)
    handler.query_items = MagicMock(side_effect=query_items)
    handler.get_item_count = MagicMock(side_effect=get_item_count)
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
