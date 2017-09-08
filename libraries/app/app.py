from __future__ import unicode_literals, print_function
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class App(object):
    """
    For all things used for by this app, from DB connection to DCS IP Address
    """
    ModelBase = declarative_base()

    prefix = ''
    api_url = 'https://api.door43.org'
    pre_convert_bucket = 'tx-client-webhook'
    cdn_bucket = 'cdn.door43.org'
    door43_bucket = 'door43.org'

    gogs_url = 'https://git.door43.org'
    gogs_domain_name = 'git.door43.org'
    gogs_ip_address = '127.0.0.1'
    gogs_user_token = ''

    job_table_name = 'tx-job'
    manifest_table_name = 'manifests'
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

    auto_setup_db = True
    db = None

    def __init__(self, **kwargs):
        """
        Using init to set the class variables with App(var=value)
        :param kwargs:
        """
        for var, value in kwargs.iteritems():
            setattr(App, var, value)
        if App.auto_setup_db:
            App.setup_db()

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
        App.ModelBase.metadata.create_all(App.db_engine)
        return session

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
        return db_connection_string
