from sqlalchemy.orm import relationship

from breakcontent import db
import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import Index, Column, ForeignKey
from sqlalchemy import Integer, Boolean, Enum, DateTime, String, Text

import logging
logger = logging.getLogger('cc')


class TaskMain(db.Model):
    __tablename__ = 'task_main'
    id = Column(Integer, primary_key=True)
    task_service = relationship(
        "XpathParsingRules", back_populates="task_main", uselist=False, foreign_keys='XpathParsingRules.task_main_id',
        cascade="all, delete-orphan", passive_deletes=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    url = Column(String(1000), nullable=False, index=True)
    domain = Column(String(500), index=True, nullable=True)
    request_id = Column(String(256), nullable=True)
    partner_id = Column(String(64), nullable=True, index=True)
    priority = Column(Integer, nullable=True, index=True)
    generator = Column(String(100), nullable=True)
    # generate many from one
    parent_url = Column(String(1000), nullable=True)

    # notify ac after crawler done, no matter partner or non-partner
    status = Column(Enum('pending', 'preparing', 'doing', 'ready', 'done', 'failed', 'debug',
                         name='status_tm'), default='pending', index=True)
    zi_sync = Column(Boolean, default=False, index=True)
    inform_ac_status = Column(Boolean, default=False, index=True)
    doing_time = Column(DateTime(timezone=False), nullable=True)
    done_time = Column(DateTime(timezone=False), nullable=True, index=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow, index=True)

    def __init__(self, *args, **kwargs):
        super(TaskMain, self).__init__(*args, **kwargs)
        # wasn't used, but EX: tm = TaskMain(bt_key) for inserting dynamic.

    def __repr__(self):
        return f'<TaskMain(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'


class TaskService(db.Model):
    __tablename__ = 'task_service'
    id = Column(Integer, primary_key=True)
    url_hash = Column(String(64), unique=True, nullable=False)
    url = Column(String(1000))
    domain = Column(String(500), index=True, nullable=True)
    partner_id = Column(String(64), nullable=True)
    request_id = Column(String(256), index=True, nullable=True)
    page_query_param = Column(String(50), nullable=True)
    is_multipage = Column(Boolean, default=False, index=True)
    secret = Column(Boolean, default=False)
    status_code = Column(Integer, index=True, nullable=True)
    retry_xpath = Column(Integer, default=0)
    status_xpath = Column(Enum('pending', 'preparing', 'doing', 'ready', 'done',
                               'failed', name='status_xpath'), default='pending', index=True)
    status_ai = Column(Enum('pending', 'preparing', 'doing', 'done',
                            'failed', name='status_ai'), default='pending', index=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return f'<TaskService(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'


class TaskNoService(db.Model):
    __tablename__ = 'task_noservice'
    id = Column(Integer, primary_key=True)
    url_hash = Column(String(64), ForeignKey('task_main.url_hash'), nullable=False, unique=True, index=True)
    url = Column(String(1000))
    domain = Column(String(500), index=True, nullable=True)
    request_id = Column(String(256), index=True, nullable=True)
    status = Column(Enum('pending', 'preparing', 'doing', 'done',
                         'failed', name='task_noservice_status'), default='pending')
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TaskNoService(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'


class WebpagesPartnerXpath(db.Model):
    __tablename__ = 'webpages_partner_xpath'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True, index=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url_structure_type = Column(Enum('home', 'list', 'content', 'others', name='url_structure_type'), nullable=True)
    url = Column(String(1000), nullable=False)
    wp_url = Column(String(500), nullable=True)  # only WP bsp has it
    title = Column(Text(), nullable=True)
    has_page_code = Column(postgresql.ARRAY(Text(), dimensions=1), nullable=True)  # todo
    meta_keywords = Column(String(200), nullable=True)
    meta_description = Column(Text(), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    categories = Column(postgresql.ARRAY(Text(), dimensions=1))
    content = Column(Text, default='')
    len_char = Column(Integer, default=0)
    content_h1 = Column(Text, default='')
    content_h2 = Column(Text, default='')
    content_p = Column(Text, default='')
    len_p = Column(Integer, default=0)
    content_image = Column(Text, default='')
    len_img = Column(Integer, default=0)
    publish_date = Column(DateTime, nullable=True)
    content_xpath = Column(Text, nullable=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_gin_meta_jdoc', meta_jdoc, postgresql_using="gin"),
    )

    def __repr__(self):
        return f'<WebpagesPartnerXpath(id={self.id}, url_hash={self.url_hash}, url={self.url}, content_hash={self.content_hash})>'


class WebpagesPartnerAi(db.Model):
    __tablename__ = 'webpages_partner_ai'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    content_h1 = Column(Text, nullable=True)
    content_h2 = Column(Text, nullable=True)
    content_p = Column(Text, nullable=True)
    content_image = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)


class WebpagesNoService(db.Model):
    __tablename__ = 'webpages_noservice'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), index=True, nullable=True)
    url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    content_h1 = Column(Text, nullable=True)
    content_h2 = Column(Text, nullable=True)
    content_p = Column(Text, nullable=True)
    content_image = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)


class StructureData(db.Model):
    # to do
    __tablename__ = 'structure_data'

    id = Column(Integer, primary_key=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), index=True, nullable=True)
    og_jdoc = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)
    item_jdoc = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)
    __table_args__ = (
        Index('idx_structure_data_og_jdoc_gin', og_jdoc, postgresql_using="gin"),
        Index('idx_structure_data_item_jdoc_gin', item_jdoc, postgresql_using="gin"),
    )


class UrlToContent(db.Model):
    """
    only partner xpath is stored

    record all the url_hash and its content_hash history

    """
    __tablename__ = 'url_to_content'

    id = Column(Integer, primary_key=True)
    request_id = Column(String(256), nullable=True)
    url_hash = Column(String(64), nullable=False)
    url = Column(String(1000), nullable=False)
    domain = Column(String(500), nullable=True, index=True)
    content_hash = Column(String(256), nullable=False)
    # a tag to present if AC is informed to replace this url_hash with new one
    replaced = Column(Boolean, default=False)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_url_to_content_url_hash_content_hash',
              url_hash, content_hash, unique=True),
    )


class DomainInfo(db.Model):
    __tablename__ = 'domain_info'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=False, index=True)
    partner_id = Column(String(64), nullable=False, index=True)
    rules = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)  # to be checked!

    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_domain_info_rules_gin', rules, postgresql_using="gin"),
        Index('idx_domain_info_domain_partner_id',
              domain, partner_id, unique=True),
    )


class BspInfo(db.Model):
    __tablename__ = 'bsp_info'

    id = Column(Integer, primary_key=True)
    bsp = Column(String(500), nullable=True)
    rule = Column(postgresql.JSONB(none_as_null=False, astext_type=None), nullable=True)  # to be checked!

    __table_args__ = (
        Index('idx_bsp_info_rule_gin', rule, postgresql_using="gin"),
    )


class XpathParsingRules(db.Model):
    __tablename__ = 'xpath_parsing_rules'

    id = Column(Integer, primary_key=True)
    task_main_id = Column(Integer, ForeignKey('task_main.id', ondelete='CASCADE'), index=True)
    task_main = relationship('TaskMain', foreign_keys=task_main_id, single_parent=True)
    title = Column(Integer, nullable=True)
    author = Column(Integer, nullable=True)
    publish_date = Column(Integer, nullable=True)
    meta_keywords = Column(Integer, nullable=True)
    meta_description = Column(Integer, nullable=True)
    _ctime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow, index=True)
