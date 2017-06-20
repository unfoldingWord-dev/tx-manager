from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.convert_handler import ConvertHandler
from libraries.converters.usfm2html_converter import Usfm2HtmlConverter


def handle(event, context):
    """
    Called through API Gateway to convert a given archive from MD to HTML
    :param dict event:
    :param context:
    :return dict:
    """
    return ConvertHandler(Usfm2HtmlConverter).handle(event, context)
