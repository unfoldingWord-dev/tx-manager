from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.convert_handler import ConvertHandler
from libraries.converters.md2html_converter import Md2HtmlConverter


def handle(event, context):
    """
    Called through API Gateway to convert a given archive from MD to HTML
    :param dict event:
    :param context:
    :return dict:
    """
    return ConvertHandler(Md2HtmlConverter).handle(event, context)
