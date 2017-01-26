from setuptools import setup

setup(
    name="tx-manager",
    packages=['aws_tools', 'client_tools', 'door43_tools', 'general_tools', 'gogs_tools', 'lambda_handlers'],
    version="0.0.1",
    author="unfoldingWord",
    author_email="unfoldingword.org",
    description="Unit test setup file.",
    keywords="",
    url="https://github.org/unfoldingWord-dev/tx-manager",
    long_description='Unit test setup file',
    classifiers=[],
    install_requires=[
        'requests',
        'responses',
        'boto3',
        'bs4',
        'gogs_client',
        'mock',
        'coveralls'
    ],
    test_suite='tests'
)
