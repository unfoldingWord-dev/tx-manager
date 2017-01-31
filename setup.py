import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(f_name):
    return open(os.path.join(os.path.dirname(__file__), f_name)).read()

setup(
    name="tx-manager",
    packages=['aws_tools', 'client_tools', 'door43_tools', 'general_tools', 'gogs_tools', 'lambda_handlers'],
    version="0.2.0",
    author="unfoldingWord",
    author_email="info@unfoldingword.org",
    description="Classes for executing tX Manager",
    license="MIT",
    keywords="tX manager",
    url="https://github.org/unfoldingWord-dev/tx-manager",
    long_description=read('README.rst'),
    classifiers=[],
    install_requires=[
        'requests==2.13.0',
        'gogs_client==1.0.3',
        'bs4==0.0.1',
        'boto3==1.4.4'
    ]
)
