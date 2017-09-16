from __future__ import unicode_literals, print_function
from sqlalchemy import Column, String, Integer, UniqueConstraint, DateTime, UnicodeText
from libraries.models.text_pickle_type import TextPickleType
from libraries.app.app import App


class TxJob(App.ModelBase):
    __tablename__ = App.job_table_name
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    job_id = Column(String(255), nullable=False, unique=True)
    user = Column(String(255), nullable=False)
    identifier = Column(String(255), nullable=False)
    convert_module = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    eta = Column(DateTime)
    resource_type = Column(String(255), nullable=False)
    input_format = Column(String(255), nullable=False)
    source = Column(String(2550), nullable=False)
    output_format = Column(String(255), nullable=False)
    output = Column(String(2550), nullable=False)
    cdn_bucket = Column(String(255), nullable=False)
    cdn_file = Column(String(2550), nullable=False)
    callback = Column(String(2550), nullable=False)
    links = Column(TextPickleType(), nullable=False)
    status = Column(String(255), nullable=False)
    success = Column(String(255), nullable=False)
    message = Column(String(255), nullable=False)
    log = Column(TextPickleType(), nullable=False)
    warnings = Column(TextPickleType(), nullable=False)
    errors = Column(TextPickleType(), nullable=False)

    def __init__(self, *args, **kwargs):
        # Init attributes
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
