"""
Utilities for mocking out AWS handlers
"""

import json

from mock import MagicMock


def mock_db_handler(data, keyname):
    """
    :param dict data: dict from keys to data
    """
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


def mock_lambda_handler(success_names, warning_names):
    """
    :param success_names: collection of function names that will have successful
    invocations
    :param warning_names: collection of warning names that will have warnings
    during their invocations
    """
    def invoke(name, payload):
        if name in success_names:
            result_payload = {
                "log": ["log1", "log2"],
                "errors": [],
                "warnings": [],
                "success": True
            }
        elif name in warning_names:
            result_payload = {
                "log": ["log1", "log2"],
                "errors": [],
                "warnings": ["warning1"],
                "success": True
            }
        else:
            result_payload = {
                "log": ["log1", "log2"],
                "errors": ["error1", "error1"],
                "warnings": [],
                "success": False
            }
        result = MagicMock()
        result.read.return_value = json.dumps(result_payload)
        return {"Payload": result}

    handler = MagicMock()
    handler.invoke = MagicMock(side_effect=invoke)
    return handler
