from setuptools import setup

setup(
    name="tx-manager",
    packages=['aws_tools', 'client_tools', 'door43_tools', 'general_tools', 'gogs_tools'],
    version="0.0.1",
    author="unfoldingWord",
    author_email="unfoldingword.org",
    description="Unit test setup file.",
    keywords="",
    url="https://github.org/unfoldingWord-dev/tx-manager",
    long_description='Unit test setup file',
    classifiers=[],
    install_requires=[
        'requests==2.13.0',
        'responses==0.5.1',
        'boto3==1.4.4',
        'bs4==0.0.1',
        'gogs_client==1.0.3',
        'mock', # travis reports syntax error in mock setup.cfg if we give version
        'coveralls==1.1'
    ],
    test_suite='tests'
)
