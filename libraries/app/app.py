from __future__ import unicode_literals, print_function
import sys
import logging
import re
from libraries.aws_tools.s3_handler import S3Handler
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.aws_tools.lambda_handler import LambdaHandler
from libraries.gogs_tools.gogs_handler import GogsHandler
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def resetable(cls):
    cls._resetable_cache_ = cls.__dict__.copy()
    return cls


def reset_class(cls):
    cache = cls._resetable_cache_  # raises AttributeError on class without decorator
    for key in [key for key in cls.__dict__ if key not in cache and key != '_resetable_cache_']:
        delattr(cls, key)
    for key, value in cache.items():  # reset the items to original values
        try:
            if key != '_resetable_cache_':
                setattr(cls, key, value)
        except AttributeError:
            pass


def setup_logger(logger, level):
    """
    Logging for the App, and turn off boto logging.
    Set here so automatically ready for any logging calls
    :param logger:
    :param level:
    :return:
    """
    for h in logger.handlers:
        logger.removeHandler(h)
    sh = logging.StreamHandler(sys.stdout)
    head = '%(asctime)s - %(levelname)s: %(message)s'
    sh.setFormatter(logging.Formatter(head))
    logger.addHandler(sh)
    logger.setLevel(level)
    # Change these loggers to only report errors:
    logging.getLogger('boto3').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)


@resetable
class App(object):
    """
    For all things used for by this app, from DB connection to global handlers
    """
    _resetable_cache_ = {}
    name = 'tx-manager'

    # Stage Variables, defaults
    prefix = ''
    api_url = 'https://api.door43.org'
    pre_convert_bucket = 'tx-webhook-client'
    cdn_bucket = 'cdn.door43.org'
    door43_bucket = 'door43.org'
    gogs_user_token = None
    gogs_url = 'https://git.door43.org'
    gogs_domain_name = 'git.door43.org'
    gogs_ip_address = '127.0.0.1'
    job_table_name = 'tx-job'
    module_table_name = 'tx-module'
    language_stats_table_name = 'language-stats'
    linter_messaging_name = 'linter_complete'
    db_protocol = 'mysql+pymysql'
    db_user = 'tx'
    db_pass = None
    db_end_point = 'd43-gogs.ccidwldijq9p.us-west-2.rds.amazonaws.com'
    db_port = '3306'
    db_name = 'tx'
    db_connection_string = None
    db_connection_string_params = 'charset=utf8mb4&use_unicode=1'

    # Prefixing vars
    # All variables that we change based on production, development and testing environments.
    prefixable_vars = ['api_url', 'pre_convert_bucket', 'cdn_bucket', 'door43_bucket', 'job_table_name',
                       'module_table_name', 'language_stats_table_name', 'linter_messaging_name',
                       'db_name', 'db_user']

    # DB related
    ModelBase = declarative_base()  # To be used in all libraries/model classes as the parent class: App.ModelBase
    auto_setup_db = True
    manifest_table_name = 'manifests'
    db_echo = False  # Whether or not to echo DB queries to the debug log. Useful for debugging. Set before setup_db()
    db_engine = None
    db = None
    echo = False

    # S3 and DynamoDB Handler related
    auto_setup_handlers = True
    cdn_s3_handler = None
    door43_s3_handler = None
    pre_convert_s3_handler = None
    job_db_handler = None
    module_db_handler = None
    language_stats_db_handler = None
    lambda_handler = None
    gogs_handler = None
    aws_access_key_id = None
    aws_secret_access_key = None
    aws_region_name = 'us-west-2'

    logger = logging.getLogger()
    setup_logger(logger, logging.DEBUG)

    def __init__(self, reset=True, **kwargs):
        """
        Using init to set the class variables with App(var=value)
        :param kwargs:
        """
        if reset:
            reset_class(App)

        if 'prefix' in kwargs and kwargs['prefix'] != App.prefix:
            App.prefix_vars(kwargs['prefix'])

        App.set_vars(**kwargs)

        if App.auto_setup_handlers:
            App.setup_handlers()

        if App.auto_setup_db and (App.db_connection_string or App.db_pass or App.db_protocol == 'sqlite'):
            App.setup_db(self.echo)

    @classmethod
    def prefix_vars(cls, prefix):
        """
        Prefixes any variables in App.prefixable_variables. This includes URLs
        :return:
        """
        url_re = re.compile(r'^(https*://)')  # Current prefix in URLs
        for var in App.prefixable_vars:
            value = getattr(App, var)
            if re.match(url_re, value):
                value = re.sub(url_re, r'\1{0}'.format(prefix), value)
            else:
                value = prefix + value
            setattr(App, var, value)
        App.prefix = prefix

    @classmethod
    def set_vars(cls, **kwargs):
        for var, value in kwargs.iteritems():
            if hasattr(App, var):
                setattr(App, var, value)

    @classmethod
    def setup_handlers(cls):
        App.cdn_s3_handler = S3Handler(bucket_name=App.cdn_bucket,
                                       aws_access_key_id=App.aws_access_key_id,
                                       aws_secret_access_key=App.aws_secret_access_key,
                                       aws_region_name=App.aws_region_name)
        App.door43_s3_handler = S3Handler(bucket_name=App.door43_bucket,
                                          aws_access_key_id=App.aws_access_key_id,
                                          aws_secret_access_key=App.aws_secret_access_key,
                                          aws_region_name=App.aws_region_name)
        App.pre_convert_s3_handler = S3Handler(bucket_name=App.pre_convert_bucket,
                                               aws_access_key_id=App.aws_access_key_id,
                                               aws_secret_access_key=App.aws_secret_access_key,
                                               aws_region_name=App.aws_region_name)
        App.job_db_handler = DynamoDBHandler(table_name=App.job_table_name,
                                             aws_access_key_id=App.aws_access_key_id,
                                             aws_secret_access_key=App.aws_secret_access_key,
                                             aws_region_name=App.aws_region_name)
        App.module_db_handler = DynamoDBHandler(table_name=App.module_table_name,
                                                aws_access_key_id=App.aws_access_key_id,
                                                aws_secret_access_key=App.aws_secret_access_key,
                                                aws_region_name=App.aws_region_name)
        App.language_stats_db_handler = DynamoDBHandler(table_name=App.language_stats_table_name,
                                                        aws_access_key_id=App.aws_access_key_id,
                                                        aws_secret_access_key=App.aws_secret_access_key,
                                                        aws_region_name=App.aws_region_name)
        App.lambda_handler = LambdaHandler(aws_access_key_id=App.aws_access_key_id,
                                           aws_secret_access_key=App.aws_secret_access_key,
                                           aws_region_name=App.aws_region_name)
        App.gogs_handler = GogsHandler(gogs_url=App.gogs_url)

    @classmethod
    def setup_db(cls, echo=False):
        """
        :param bool echo:
        """
        if not App.db_connection_string:
            App.db_connection_string = App.construct_connection_string()
        App.db_engine = create_engine(App.db_connection_string, echo=echo)
        session = sessionmaker(bind=App.db_engine)()
        App.db = session

        from libraries.models.manifest import TxManifest
        TxManifest.__table__.name = App.manifest_table_name
        App.create_tables([TxManifest.__table__])
        return session

    @classmethod
    def create_tables(cls, tables=None):
        App.ModelBase.metadata.create_all(App.db_engine, tables=tables)

    @classmethod
    def construct_connection_string(cls):
        db_connection_string = App.db_protocol+'://'
        if App.db_user:
            db_connection_string += App.db_user
            if App.db_pass:
                db_connection_string += ':'+App.db_pass
            if App.db_end_point:
                db_connection_string += '@'
        if App.db_end_point:
            db_connection_string += App.db_end_point
            if App.db_port:
                db_connection_string += ':'+App.db_port
        if App.db_name:
            db_connection_string += '/'+App.db_name
        if App.db_connection_string_params:
            db_connection_string += '?'+App.db_connection_string_params
        return db_connection_string
