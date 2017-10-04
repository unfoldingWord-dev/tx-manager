from __future__ import unicode_literals, print_function
from sqlalchemy import Column, String, DateTime, Boolean, func
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime
from libraries.models.tx_model import TxModel
from libraries.models.text_pickle_type import TextPickleType
from libraries.app.app import App
from libraries.general_tools.data_utils import convert_string_to_date


class TxJob(App.Base, TxModel):
    __tablename__ = App.job_table_name
    job_id = Column(String(100), primary_key=True)
    identifier = Column(String(255), nullable=True)
    owner_name = Column(String(255), nullable=True)
    repo_name = Column(String(255), nullable=True)
    commit_id = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=True, default=False)
    user = Column(String(255), nullable=True)  # Username of the token, not necessarily the repo's owner
    convert_module = Column(String(255), nullable=True)
    lint_module = Column(String(255), nullable=True)
    resource_type = Column(String(255), nullable=True)
    input_format = Column(String(255), nullable=True)
    output_format = Column(String(255), nullable=True)
    source = Column(String(2550), nullable=True)
    output = Column(String(2550), nullable=True)
    cdn_bucket = Column(String(255), nullable=True)
    cdn_file = Column(String(255), nullable=True)
    callback = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    message = Column(String(255), nullable=True)
    links = Column(TextPickleType(), nullable=True, default=[])
    options = Column(TextPickleType(), nullable=True, default={})
    log = Column(TextPickleType(), nullable=True, default=[])
    warnings = Column(TextPickleType(), nullable=True, default=[])
    errors = Column(TextPickleType(), nullable=True, default=[])

    def __init__(self, **kwargs):
        # Init attributes
        self.success = False
        self.links = []
        self.options = {}
        self.log = []
        self.warnings = []
        self.errors = []
        super(TxJob, self).__init__(**kwargs)
        self.created_at = convert_string_to_date(self.created_at)
        self.updated_at = convert_string_to_date(self.updated_at)
        self.started_at = convert_string_to_date(self.started_at)
        self.ended_at = convert_string_to_date(self.ended_at)
        self.expires_at = convert_string_to_date(self.expires_at)
        self.eta = convert_string_to_date(self.eta)

    def link(self, link):
        self.links.append(link)
        flag_modified(self, 'links')

    def log_message(self, message):
        self.log.append(message)
        flag_modified(self, 'log')
        App.logger.info(message)

    def error_message(self, message):
        self.errors.append(message)
        flag_modified(self, 'errors')
        App.logger.error(message)

    def warning_message(self, message):
        self.warnings.append(message)
        flag_modified(self, 'warnings')
        App.logger.warning(message)
