from __future__ import unicode_literals, print_function
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SqlDbTableHandler(object):
    """
    Class to handle DB actions for a given table/model
    """

    def __init__(self, model_class, db_protocol='mysql+pysql', db_user='tx', db_pass=None,
                 end_point='d43-gogs.ccidwldijq9p.us-west-2.rds.amazonaws.com', db_port='3306', db_name='tx',
                 connection_string=None, echo=False):
        """
        :param Base model_class: Required. A model that is a child of Base
        :param string db_protocol:
        :param string db_user:
        :param string string db_pass:
        :param string end_point:
        :param string db_port:
        :param string db_name:
        :param string connection_string: If a connection_string is given, it is used, otherwise can pass parts (defaults are what is used in production except for the password of course)
        :param bool echo:
        """
        self.model_class = model_class
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = "{0}://{1}:{2}@{3}:{4}/{5}".format(db_protocol, db_user, db_pass, end_point, db_port,
                                                                        db_name)
        self.echo = echo

        self.db_engine = None
        self.session = None
        self.setup_resources()

    def setup_resources(self):
        """
        Sets up the resources used to work with the DB and table
        """
        self.db_engine = create_engine(self.connection_string, echo=self.echo)
        self.session = sessionmaker(bind=self.db_engine)()

    def create_all(self):
        """
        Creates all the model tables that subclass Base
        """
        Base.metadata.create_all(self.db_engine)

    def get_item(self, query):
        """
        :param dict query:
        :return:
        """
        q = self.session.query(self.model_class)
        for attr, value in query.items():
            q = q.filter(getattr(self.model_class, attr).like("%s" % value))
        return q.first()

    def query_items(self, query=None, order_by=None):
        """
        :param dict query:
        :param Column|list order_by:
        :return:
        """
        q = self.session.query(self.model_class)
        for attr, value in query.items():
            q = q.filter(getattr(self.model_class, attr).like("%s" % value))
        if order_by:
            if not isinstance(order_by, list):
                order_by = [order_by]
            for col in order_by:
                q = q.order_by(col)
        return q

    def insert_item(self, o):
        """
        :param Base o:
        :return:
        """
        if isinstance(o, list):
            self.session.add_all(o)
        else:
            self.session.add(o)
        self.session.commit()

    def insert_items(self, o):
        """
        :param Base o:
        :return:
        """
        return self.insert_item(o)

    def update_item(self, o):
        """
        :param Base o:
        :return:
        """
        return self.insert_item(o)

    def delete_item(self, o):
        """
        :param Base o:
        :return:
        """
        self.session.delete(o)
        self.session.commit()
