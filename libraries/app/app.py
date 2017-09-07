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
    gogs_url = 'https://git.door43.org'
    pre_convert_bucket = 'tx-client-webhook'
    cdn_bucket = 'cdn.door43.org'
    door43_bucket = 'door43.org'

    dcs_url = 'https://git.door43.org'
    dcs_domain_name = 'git.door43.org'
    dcs_ip_address = '127.0.0.1'
    dcs_user_token = ''

    job_table_name = 'tx-job'
    manifest_table_name = 'manifests'
    module_table_name = 'tx-module'
    linter_messaging_name = 'linter_complete'

    db = None
    db_protocol = 'mysql+pymysql'
    db_user = 'tx'
    db_pass = None
    db_end_point = 'd43-gogs.ccidwldijq9p.us-west-2.rds.amazonaws.com'
    db_port = '3306'
    db_name = 'tx'
    db_connection_string = None

    def __init__(self, **kwargs):
        """
        Using init to set the class variables with App(var=value)
        :param kwargs:
        """
        for var, value in kwargs.iteritems():
            setattr(App, var, value)
        if self.db_pass or self.db_connection_string:
            self.setup_db()

    @classmethod
    def setup_db(cls, echo=False):
        """
        :param bool echo:
        """
        if not App.db_connection_string:
            App.construct_connection_string()
        App.db_engine = create_engine(App.db_connection_string, echo=echo)
        session = sessionmaker(bind=App.db_engine)()
        App.db = session
        App.ModelBase.metadata.create_all(App.db_engine)
        return session

    @classmethod
    def construct_connection_string(cls):
        App.db_connection_string = "{0}://{1}:{2}@{3}:{4}/{5}".format(
            App.db_protocol, App.db_user, App.db_pass, App.db_end_point, App.db_port, App.db_name)
        return App.db_connection_string
