import json
import sqlalchemy
from sqlalchemy.types import TypeDecorator
from libraries.app.app import App

SIZE = 65535


class TextPickleType(TypeDecorator):

    impl = sqlalchemy.Text(SIZE)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                value = json.loads(value)
            except:
                App.logger.debug("Bad JSON: {0}".format(value))
        return value
