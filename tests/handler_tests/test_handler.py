from __future__ import absolute_import, unicode_literals
from unittest import TestCase
from libraries.lambda_handlers.handler import Handler
from libraries.app.app import App


class MyHandler(Handler):

    def __init__(self):
        self.was_called = False
        self.event = None
        self.context = None
        super(MyHandler, self).__init__()

    def _handle(self, event, context):
        self.was_called = True
        self.event = event
        self.context = context
        if not self.context:
            bad = 1/0
            print('never get here: bad = {0}'.format(bad))


class TestHandlers(TestCase):

    def test_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Handler, None)

    def test_retrieve(self):
        self.assertEqual(Handler.retrieve({'test': 1}, 'test'), 1)
        self.assertRaises(Exception, Handler.retrieve, {'foor': 'bar'}, 'boo')
        try:
            Handler.retrieve({'foo': 'bar'}, 'boo')
        except Exception as e:
            self.assertEqual(e.message, "'boo' not found in dictionary")
        try:
            Handler.retrieve({'foo': 'bar'}, 'boo', 'Payload')
        except Exception as e:
            self.assertEqual(e.message, "'boo' not found in Payload")
        self.assertIsNone(Handler.retrieve({'foo': 'bar'}, 'boo', required=False))
        self.assertEqual(Handler.retrieve({'foo': 'bar'}, 'boo', required=False, default='far'), 'far')

    def test_handle(self):
        handler = MyHandler()
        event = {
            'data': {
                'key1': 'value1'
            },
            'body-json': {
                'key2': 'value2'
            },
            'vars': {
                'cdn_bucket': 'test-cdn-bucket'
            }
        }
        context = {
            'some': 'text'
        }
        handler.handle(event=event, context=context)
        self.assertEqual(App.cdn_bucket, event['vars']['cdn_bucket'])
        self.assertEqual(handler.context['some'], context['some'])
        self.assertEqual(handler.data['key1'], event['data']['key1'])
        self.assertEqual(handler.data['key2'], event['body-json']['key2'])
        self.assertRaises(EnvironmentError, handler.handle, event, None)
        try:
            handler.handle(event, None)
        except Exception as e:
            self.assertEqual(e.message, 'Bad Request: integer division or modulo by zero')
