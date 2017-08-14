from __future__ import unicode_literals
import inspect
import os


def get_app_root():
    current_dir = os.path.dirname(inspect.stack()[0][1])
    return os.path.dirname(os.path.dirname(current_dir))


def get_static_dir():
    return os.path.join(get_app_root(), 'static')


def get_output_dir():
    return os.path.join(get_app_root(), 'output')


def get_tools_dir():
    tools_dir = '/var/www/vhosts/door43.org/tools'
    if not os.path.isdir(tools_dir):
        tools_dir = os.path.expanduser('~/Projects/tools')

    if not os.path.isdir(tools_dir):
        return None

    return tools_dir
