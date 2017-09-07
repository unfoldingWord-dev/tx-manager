from __future__ import unicode_literals, print_function
from sqlalchemy import Column, String, Integer, LargeBinary, UniqueConstraint, DateTime
from libraries.app.app import App


class TxManifest(App.ModelBase):
    __tablename__ = App.manifest_table_name

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    repo_name = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    lang_code = Column(String(32), nullable=False)
    resource_id = Column(String(32), nullable=False)
    resource_type = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    views = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, nullable=False)
    manifest = Column(LargeBinary, default=None, nullable=True)

    __table_args__ = (
        UniqueConstraint('repo_name', 'user_name'),
    )
