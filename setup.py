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
    version='0.2.61',
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
        'future==0.16.0',
        'pyparsing==2.1.10',
        'usfm-tools==0.0.8'
    ]
)
