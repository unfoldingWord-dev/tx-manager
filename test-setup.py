from setuptools import setup

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
    install_requires=[
        'requests==2.13.0',
        'responses==0.5.1',
        'boto3==1.4.4',
        'bs4==0.0.1',
        'gogs_client==1.0.3',
        'coveralls==1.1',
        'python-json-logger==0.1.5',
        'markdown==2.6.8',
        'future==0.16.0',
        'pyparsing==2.1.10',
        'usfm-tools==0.0.8',
        'mock',  # travis reports syntax error in mock setup.cfg if we give version
        'moto==0.4.31'
    ],
    test_suite='tests'
)
