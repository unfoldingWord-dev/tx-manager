from setuptools import setup

setup(
    name="tx-manager",
    version="0.0.1",
    author="unfoldingWord",
    author_email="unfoldingword.org",
    description="Unit test setup file.",
    keywords="",
    url="https://github.org/unfoldingWord-dev/tx-manager",
#    packages=['tx_manager'],
    long_description='Unit test setup file',
    classifiers=[],
    install_requires=[
        'requests==2.12.5',
        'gogs_client==1.0.3',
        'bs4==0.0.1',
        'boto3==1.4.4'
    ],
    test_suite='tests'
)
