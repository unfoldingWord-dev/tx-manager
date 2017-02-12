from setuptools import setup

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
    author_email='unfoldingword.org',
    description='Unit test setup file.',
    keywords=[
        'tX manager',
        'unfoldingword',
        'usfm',
        'md2html',
        'usfm2html'
    ],
    url='https://github.org/unfoldingWord-dev/tx-manager',
    long_description='Unit test setup file',
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
        'usfm_tools==0.0.7',
        'mock'
    ],
    test_suite='tests'
)
