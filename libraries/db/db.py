from __future__ import unicode_literals, print_function
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DB(object):
    session = None
    Base = declarative_base()

    """
    Class to handle DB connect
    """
    def __init__(self, db_protocol='mysql+pymysql', db_user='tx', db_pass=None,
                 end_point='d43-gogs.ccidwldijq9p.us-west-2.rds.amazonaws.com', db_port='3306', db_name='tx',
                 connection_string=None, echo=False, default_db=False, create_tables=True):
        """
        :param string db_protocol:
        :param string db_user:
        :param string string db_pass:
        :param string end_point:
        :param string db_port:
        :param string db_name:
        :param string connection_string: If a connection_string is given, it is used, otherwise can pass parts (defaults are what is used in production except for the password of course)
        :param bool echo:
        """
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = "{0}://{1}:{2}@{3}:{4}/{5}".format(db_protocol, db_user, db_pass, end_point,
                                                                        db_port, db_name)
        self.session = None
        self.engine = None
        self.default_db = default_db
        self.echo = echo
        self.setup_resources()
        if create_tables:
            DB.Base.metadata.create_all(self.engine)

    def setup_resources(self):
        self.engine = create_engine(self.connection_string, echo=self.echo)
        self.session = sessionmaker(bind=self.engine)()
        if self.default_db:
            DB.session = self.session
