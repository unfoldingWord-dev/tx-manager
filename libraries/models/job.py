from __future__ import unicode_literals, print_function
from sqlalchemy import Column, String, DateTime, Boolean, inspect
from datetime import datetime
from libraries.models.text_pickle_type import TextPickleType
from libraries.app.app import App


class TxJob(App.ModelBase):
    __tablename__ = App.job_table_name
    job_id = Column(String(100), primary_key=True)
    identifier = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=True, default=False)
    user = Column(String(255), nullable=True)
    convert_module = Column(String(255), nullable=True)
    resource_type = Column(String(255), nullable=True)
    input_format = Column(String(255), nullable=True)
    output_format = Column(String(255), nullable=True)
    source = Column(String(2550), nullable=True)
    output = Column(String(2550), nullable=True)
    cdn_bucket = Column(String(255), nullable=True)
    cdn_file = Column(String(2550), nullable=True)
    callback = Column(String(2550), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    links = Column(TextPickleType(), nullable=True, default=[])
    message = Column(String(255), nullable=True)
    log = Column(TextPickleType(), nullable=True, default=[])
    warnings = Column(TextPickleType(), nullable=True, default=[])
    errors = Column(TextPickleType(), nullable=True, default=[])

    def __init__(self, *args, **kwargs):
        self.links = []
        self.log = []
        self.warnings = []
        self.errors = []
        super(TxJob, self).__init__(*args, **kwargs)

    def log_message(self, message):
        self.log.append(message)

    def error_message(self, message):
        self.errors.append(message)

    def warning_message(self, message):
        self.warnings.append(message)

    def get_db_data(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}
