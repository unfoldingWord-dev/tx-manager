from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.convert_handler import ConvertHandler
from libraries.converters.md2html_converter import Md2HtmlConverter
from libraries.converters.usfm2html_converter import Usfm2HtmlConverter


class TestConvertHandler(TestCase):
    @mock.patch('libraries.converters.converter.Converter.run')
    def test_handle_for_obs(self, mock_convert_run):
        mock_convert_run.return_value = None
        event = {
            'data': {
                'source_url': 'https://cdn.example.com/preconvert/705948ab00.zip',
                'cdn_bucket': 'test_cdn_bucket',
                'cdn_file': 'tx/job/1234567890.zip',
                'callback': 'https://api.example.com/client/callback',
                'identifier': 'richmahn/en-obs/705948ab00',
                'resource_type': 'obs',
                'options': {'pageSize': 'A4'}
            }
        }
        self.assertIsNone(ConvertHandler(Md2HtmlConverter).handle(event, None))

    @mock.patch('libraries.converters.converter.Converter.run')
    def test_handle_for_usfm(self, mock_convert_run):
        mock_convert_run.return_value = None
        event = {
            'data': {
                'identifier': 'richmahn/en-obs/705948ab00',
                'source_url': 'https://cdn.example.com/preconvert/705948ab00.zip',
                'cdn_bucket': 'test_cdn_bucket',
                'cdn_file': 'tx/job/1234567890.zip',
                'resource_type': 'obs',
                'options': {'pageSize': 'A4'}
            }
        }
        self.assertIsNone(ConvertHandler(converter_class=Usfm2HtmlConverter).handle(event, None))

    @mock.patch('libraries.converters.converter.Converter.run')
    def test_handle_for_client_callback(self, mock_convert_run):
        mock_convert_run.return_value = None
        event = {
            'data': {
                'identifier': 'richmahn/en-obs/705948ab00',
                'convert_callback': 'http://callback.org',
                'cdn_file': 'tx/job/1234567890.zip',
                'source_url': 'https://cdn.example.com/preconvert/705948ab00.zip',
                'resource_type': 'obs',
                'options': {'pageSize': 'A4'}
            }
        }
        self.assertIsNone(ConvertHandler(converter_class=Usfm2HtmlConverter).handle(event, None))
