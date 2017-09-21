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
from sqlalchemy.pool import NullPool


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
    cls.dirty = False


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
    dirty = False

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
    db_connection_string_params = 'charset=utf8mb4&use_unicode=0'

    # Prefixing vars
    # All variables that we change based on production, development and testing environments.
    prefixable_vars = ['api_url', 'pre_convert_bucket', 'cdn_bucket', 'door43_bucket',
                       'module_table_name', 'language_stats_table_name', 'linter_messaging_name',
                       'db_name', 'db_user']

    # DB related
    Base = declarative_base()  # To be used in all libraries/model classes as the parent class: App.ModelBase
    auto_setup_db = True
    manifest_table_name = 'manifests'
    job_table_name = 'jobs'
    db_echo = False  # Whether or not to echo DB queries to the debug log. Useful for debugging. Set before setup_db()
    echo = False

    # Credentials
    aws_access_key_id = None
    aws_secret_access_key = None
    aws_region_name = 'us-west-2'

    # Handlers
    _db_engine = None
    _db = None
    _cdn_s3_handler = None
    _door43_s3_handler = None
    _pre_convert_s3_handler = None
    _job_db_handler = None
    _module_db_handler = None
    _language_stats_db_handler = None
    _lambda_handler = None
    _gogs_handler = None

    # Logger
    logger = logging.getLogger()
    setup_logger(logger, logging.DEBUG)

    def __init__(self, **kwargs):
        """
        Using init to set the class variables with App(var=value)
        :param kwargs:
        """
        self.init(**kwargs)

    @classmethod
    def init(cls, reset=True, **kwargs):
        """
        Class init method to set all vars
        :param bool reset:
        :param kwargs:
        """
        if cls.dirty and reset:
            App.db_close()
            reset_class(App)
        if 'prefix' in kwargs and kwargs['prefix'] != cls.prefix:
            cls.prefix_vars(kwargs['prefix'])
        cls.set_vars(**kwargs)

    @classmethod
    def prefix_vars(cls, prefix):
        """
        Prefixes any variables in App.prefixable_variables. This includes URLs
        :return:
        """
        url_re = re.compile(r'^(https*://)')  # Current prefix in URLs
        for var in cls.prefixable_vars:
            value = getattr(App, var)
            if re.match(url_re, value):
                value = re.sub(url_re, r'\1{0}'.format(prefix), value)
            else:
                value = prefix + value
            setattr(App, var, value)
        cls.prefix = prefix
        cls.dirty = True

    @classmethod
    def set_vars(cls, **kwargs):
        for var, value in kwargs.iteritems():
            if hasattr(App, var):
                setattr(App, var, value)
                cls.dirty = True

    @classmethod
    def cdn_s3_handler(cls):
        if not cls._cdn_s3_handler:
            cls._cdn_s3_handler = S3Handler(bucket_name=cls.cdn_bucket,
                                            aws_access_key_id=cls.aws_access_key_id,
                                            aws_secret_access_key=cls.aws_secret_access_key,
                                            aws_region_name=cls.aws_region_name)
        return cls._cdn_s3_handler

    @classmethod
    def door43_s3_handler(cls):
        if not cls._door43_s3_handler:
            cls._door43_s3_handler = S3Handler(bucket_name=cls.door43_bucket,
                                               aws_access_key_id=cls.aws_access_key_id,
                                               aws_secret_access_key=cls.aws_secret_access_key,
                                               aws_region_name=cls.aws_region_name)
        return cls._door43_s3_handler

    @classmethod
    def pre_convert_s3_handler(cls):
        if not cls._pre_convert_s3_handler:
            cls._pre_convert_s3_handler = S3Handler(bucket_name=cls.pre_convert_bucket,
                                                    aws_access_key_id=cls.aws_access_key_id,
                                                    aws_secret_access_key=cls.aws_secret_access_key,
                                                    aws_region_name=cls.aws_region_name)
        return cls._pre_convert_s3_handler

    @classmethod
    def module_db_handler(cls):
        if not cls._module_db_handler:
            cls._module_db_handler = DynamoDBHandler(table_name=cls.module_table_name,
                                                     aws_access_key_id=cls.aws_access_key_id,
                                                     aws_secret_access_key=cls.aws_secret_access_key,
                                                     aws_region_name=cls.aws_region_name)
        return cls._module_db_handler

    @classmethod
    def language_stats_db_handler(cls):
        if not cls._language_stats_db_handler:
            cls._language_stats_db_handler = DynamoDBHandler(table_name=cls.language_stats_table_name,
                                                             aws_access_key_id=cls.aws_access_key_id,
                                                             aws_secret_access_key=cls.aws_secret_access_key,
                                                             aws_region_name=cls.aws_region_name)
        return cls._language_stats_db_handler

    @classmethod
    def lambda_handler(cls):
        if not cls._lambda_handler:
            cls._lambda_handler = LambdaHandler(aws_access_key_id=cls.aws_access_key_id,
                                                aws_secret_access_key=cls.aws_secret_access_key,
                                                aws_region_name=cls.aws_region_name)
        return cls._lambda_handler

    @classmethod
    def gogs_handler(cls):
        if not cls._gogs_handler:
            cls._gogs_handler = GogsHandler(gogs_url=cls.gogs_url)
        return cls._gogs_handler

    @classmethod
    def db_engine(cls, echo=None):
        """
        :param mixed echo:
        """
        if echo is None or not isinstance(echo, bool):
            echo = cls.echo
        if not cls._db_engine:
            if not cls.db_connection_string:
                cls.db_connection_string = cls.construct_connection_string()
            if not cls.db_connection_string.startswith('sqlite://'):
                cls._db_engine = create_engine(cls.db_connection_string, echo=echo, poolclass=NullPool)
            else:
                cls._db_engine = create_engine(cls.db_connection_string, echo=echo)
        return cls._db_engine

    @classmethod
    def db(cls, echo=None):
        """
        :param mixed echo:
        """
        if not cls._db:
            cls._db = sessionmaker(bind=cls.db_engine(echo), expire_on_commit=False)()
            from libraries.models.manifest import TxManifest
            TxManifest.__table__.name = cls.manifest_table_name
            from libraries.models.job import TxJob
            TxJob.__table__.name = cls.job_table_name
            cls.db_create_tables([TxManifest.__table__, TxJob.__table__])
        return cls._db

    @classmethod
    def db_close(cls):
        if cls._db:
            cls._db.close_all()
            cls._db.dispose()
            cls._db = None
            cls._db_engine = None

    @classmethod
    def db_create_tables(cls, tables=None):
        cls.Base.metadata.create_all(cls.db_engine(), tables=tables)

    @classmethod
    def construct_connection_string(cls):
        db_connection_string = cls.db_protocol+'://'
        if cls.db_user:
            db_connection_string += cls.db_user
            if cls.db_pass:
                db_connection_string += ':'+cls.db_pass
            if cls.db_end_point:
                db_connection_string += '@'
        if cls.db_end_point:
            db_connection_string += cls.db_end_point
            if cls.db_port:
                db_connection_string += ':'+cls.db_port
        if cls.db_name:
            db_connection_string += '/'+cls.db_name
        if cls.db_connection_string_params:
            db_connection_string += '?'+cls.db_connection_string_params
        return db_connection_string
