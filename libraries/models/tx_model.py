from __future__ import unicode_literals, print_function
from sqlalchemy import inspect
from datetime import datetime, date
from libraries.app.app import App


class TxModel(object):

    def insert(self):
        App.db().add(self)
        App.db().commit()
        App.db().close()

    def update(self):
        App.db().merge(self)
        App.db().commit()
        App.db().close()

    def delete(self):
        App.db().delete(self)
        App.db().commit()
        App.db().close()

    @classmethod
    def get(cls, *args, **kwargs):
        if args:
            kwargs[inspect(cls).primary_key[0].name] = args[0]
        item = cls.query(**kwargs).first()
        App.db().close()
        return item

    @classmethod
    def query(cls, **kwargs):
        items = App.db().query(cls).filter_by(**kwargs)
        return items

    def __iter__(self):
        for c in inspect(self).mapper.column_attrs:
            value = getattr(self, c.key)
            if isinstance(value, (datetime, date)):
                value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            yield (c.key, value)
