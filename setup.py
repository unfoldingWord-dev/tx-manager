import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(f_name):
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()

setup(
    name='tx-manager',
    version='0.2.1',
    packages=[
        'client',
        'manager',
        'converters',
        'aws_tools',
        'door43_tools',
        'general_tools',
        'gogs_tools',
        'lambda_handlers'
    ],
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
    dependency_links=[
        'git+ssh://git@github.com/unfoldingword-dev/usfm-tools.git#egg=usfm_tools-0.0.7'
    ],
    install_requires=[
        'requests',
        'responses',
        'gogs_client',
        'bs4',
        'boto3',
        'python-json-logger',
        'markdown',
        'future',
        'pyparsing',
        'usfm_tools==0.0.7'
    ]
)
