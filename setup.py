import os
from setuptools import setup


def read(f_name):
    """
    Utility function to read the README file.

    Used for the long_description.  It's nice, because now 1) we have a top level
    README file and 2) it's easier to type in the README file than to put a raw
    string in below ...
    """
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()

setup(
    name='tx-manager',
    version='0.3.0',
    package_dir={
        'client_converter_callback': 'functions/client_converter_callback',
        'client_linter_callback': 'functions/client_linter_callback',
        'client_webhook': 'functions/client_webhook',
        'convert_md2html': 'functions/convert_md2html',
        'convert_usfm2html': 'functions/convert_usfm2html',
        'door43_deploy': 'functions/door43_deploy',
        'list_endpoints': 'functions/list_endpoints',
        'register_module': 'functions/register_module',
        'client': 'libraries/client',
        'converters': 'libraries/converters',
        'aws_tools': 'libraries/aws_tools',
        'door43_tools': 'libraries/door43_tools',
        'general_tools': 'libraries/general_tools',
        'gogs_tools': 'libraries/gogs_tools',
        'lambda_handlers': 'libraries/lambda_handlers',
        'manager': 'libraries/manager',
        'resource_container': 'libraries/resource_container'
    },
    packages=[
        'client_converter_callback',
        'client_linter_callback',
        'client_webhook',
        'convert_md2html',
        'convert_usfm2html',
        'door43_deploy',
        'list_endpoints',
        'register_module',
        'client',
        'converters',
        'aws_tools',
        'door43_tools',
        'general_tools',
        'gogs_tools',
        'lambda_handlers',
        'manager',
        'resource_container'
    ],
    package_data={'converters': ['templates/*.html']},
    author='unfoldingWord',
    author_email='info@unfoldingword.org',
    description='Classes for executing tX Manager',
    license='MIT',
    keywords=[
        'tX manager',
        'unfoldingword',
        'usfm',
        'md2html',
        'usfm2html'
    ],
    url='https://github.org/unfoldingWord-dev/tx-manager',
    long_description=read('README.rst'),
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[
        'requests==2.13.0',
        'responses==0.5.1',
        'gogs_client==1.0.3',
        'bs4==0.0.1',
        'boto3==1.4.4',
        'python-json-logger==0.1.5',
        'markdown==2.6.8',
        'markdown2==2.4.0',
        'future==0.16.0',
        'pyparsing==2.1.10',
        'usfm-tools==0.0.22',
        'PyYAML==3.12',
        'pymysql==0.7.11',
        'sqlalchemy==1.2.0b2',
    ]
)
