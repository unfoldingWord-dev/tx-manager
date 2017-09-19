from __future__ import unicode_literals, print_function
from sqlalchemy import inspect
from libraries.app.app import App


class TxModel(object):

    def insert(self):
        App.db().add(self)
        self.update()

    def update(self):
        App.db().commit()

    def delete(self):
        App.db().delete(self)
        self.update()

    @classmethod
    def get(cls, *args, **kwargs):
        if args:
            kwargs[inspect(cls).primary_key[0].name] = args[0]
        item = cls.query(**kwargs).first()
        return item

    @classmethod
    def query(cls, **kwargs):
        items = App.db().query(cls).filter_by(**kwargs)
        return items

    def __iter__(self):
        for c in inspect(self).mapper.column_attrs:
            yield (c.key, getattr(self, c.key))
