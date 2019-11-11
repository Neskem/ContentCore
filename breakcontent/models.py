from breakcontent import db
import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import func, Index, Column, ForeignKey
from sqlalchemy import Integer, Boolean, Enum, DateTime, String, Text
from sqlalchemy.orm import relationship

import logging
logger = logging.getLogger('cc')

from sqlalchemy.orm import load_only
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError, DatabaseError


class TaskMain(db.Model):
    __tablename__ = 'task_main'
    id = Column(Integer, primary_key=True)
    # wpx = relationship('WebpagesPartnerXpath', backref='tm')  # alpha testing
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
    # notify_ac_time
    done_time = Column(DateTime(timezone=False), nullable=True, index=True)
    # notify_ac_time = Column(DateTime(timezone=False), nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow, index=True)

    def __init__(self, *args, **kwargs):
        super(TaskMain, self).__init__(*args, **kwargs)
        # wasn't used, but EX: tm = TaskMain(bt_key) for inserting dynamic.

    def __repr__(self):
        return f'<TaskMain(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'

    def to_dict(self):
        # for update use
        return {
            'id': self.id,
            # 'task_service': self.task_service,
            # 'task_noservice': self.task_noservice,
            'url_hash': self.url_hash,
            'url': self.url,
            'domain': self.domain,
            'request_id': self.request_id,
            'partner_id': self.partner_id,
            'priority': self.priority,
            'generator': self.generator,
            'parent_url': self.parent_url,
            'status': self.status,
            'doing_time': self.doing_time,
            'done_time': self.done_time
        }


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
    # retry_ai = Column(Integer, default=0)
    status_ai = Column(Enum('pending', 'preparing', 'doing', 'done',
                            'failed', name='status_ai'), default='pending', index=True)
    # partner only
    sent_content_time = Column(DateTime(timezone=False), nullable=True)
    sent_content_ini_time = Column(DateTime(timezone=False), nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return f'<TaskService(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'task_main_id': self.task_main_id,
            # 'webpages_partner_xpath': self.webpages_partner_xpath,
            # 'webpages_partner_ai': self.webpages_partner_ai,
            'url_hash': self.url_hash,
            'url': self.url,
            'domain': self.domain,
            'partner_id': self.partner_id,
            'request_id': self.request_id,
            'is_multipage': self.is_multipage,
            'page_query_param': self.page_query_param,
            'secret': self.secret,
            'status_code': self.status_code,
            # 'retry_xpath': self.retry_xpath,
            'status_xpath': self.status_xpath,
            # 'retry_ai': self.retry_ai,
            'status_ai': self.status_ai,
            # '_ctime': self._ctime,
            # '_mtime': self._mtime
        }


class TaskNoService(db.Model):
    __tablename__ = 'task_noservice'
    id = Column(Integer, primary_key=True)
    url_hash = Column(String(64), ForeignKey(
        'task_main.url_hash'), nullable=False, unique=True, index=True)
    url = Column(String(1000))
    domain = Column(String(500), index=True, nullable=True)
    request_id = Column(String(256), index=True, nullable=True)
    # secret = Column(Boolean, nullable=True)  # not required
    # retry = Column(Integer, default=0)
    status = Column(Enum('pending', 'preparing', 'doing', 'done',
                         'failed', name='task_noservice_status'), default='pending')
    # webpages_id = Column(Integer, nullable=True)
    # start datetime
    # _stime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TaskNoService(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'task_main_id': self.task_main_id,
            'url_hash': self.url_hash,
            'url': self.url,
            'domain': self.domain,
            # 'request_id': self.request_id,
            # 'retry': self.retry,
            'status': self.status
        }


class WebpagesPartnerXpath(db.Model):
    __tablename__ = 'webpages_partner_xpath'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True, index=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url_structure_type = Column(Enum(
        'home', 'list', 'content', 'others', name='url_structure_type'), nullable=True)
    url = Column(String(1000), nullable=False)
    wp_url = Column(String(500), nullable=True)  # only WP bsp has it
    title = Column(Text(), nullable=True)
    has_page_code = Column(postgresql.ARRAY(
        Text(), dimensions=1), nullable=True)  # todo
    meta_keywords = Column(String(200), nullable=True)
    meta_description = Column(Text(), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
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
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_gin_meta_jdoc', meta_jdoc, postgresql_using="gin"),
    )

    def __repr__(self):
        return f'<WebpagesPartnerXpath(id={self.id}, url_hash={self.url_hash}, url={self.url}, content_hash={self.content_hash})>'

    def checkQuality(self):
        '''
        if len_img < 2 and len_char < 100 => off bad quality
        '''
        if self.len_img < 2 and self.len_char < 100:
            # content of poor quality
            return False
        else:
            return True

    def to_dict(self):

        return {
            'id': self.id,
            # 'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            'wp_url': self.wp_url,
            'multi_page_urls': self.multi_page_urls or [],
            'url_structure_type': self.url_structure_type,
            'title': self.title,
            'meta_keywords': self.meta_keywords,
            'meta_description': self.meta_description,
            'meta_jdoc': self.meta_jdoc or {},
            'cover': self.cover,
            'author': self.author,
            'category': self.category,
            'categories': self.categories,
            'content': self.content,
            'len_char': self.len_char or 0,
            'content_h1': self.content_h1 or '',
            'content_h2': self.content_h2 or '',
            'content_p': self.content_p or '',
            'len_p': self.len_p or 0,
            'content_image': self.content_image or '',
            'len_img': self.len_img or 0,
            'publish_date': self.publish_date,
            'content_hash': self.content_hash,
            'content_xpath': self.content_xpath,
            # '_ctime': self._ctime,
            # '_mtime': self._mtime
        }

    def to_inform(self):
        '''
        return only the required key/value for xpath_a_crawler()
        '''
        return {
            'id': self.id,
            # 'request_id': self.task_service.request_id, # check!
            'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            # 'wp_url': self.wp_url,
            # 'multi_page_urls': self.multi_page_urls,
            # 'url_structure_type': self.url_structure_type,
            'title': self.title,
            # 'author': self.author,
            # 'category': self.category,
            # 'categories': self.categories,
            # 'content': self.content,
            # 'content_image': self.content_image,
            # 'len_img': self.len_img,
            'publish_date': self.publish_date,
            'content_hash': self.content_hash,
            'content_xpath': self.content_xpath,
        }

    def to_ac(self):
        return {
            'url': self.url,
            'url_structure_type': self.url_structure_type,
            'title': self.title,
            'cover': self.cover,
            'content': self.content,
            'publishedAt': self.publish_date.isoformat() if self.publish_date is not None else '',
        }

    def to_dict(self):

        return {
            'id': self.id,
            'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            'wp_url': self.wp_url,
            'multi_page_urls': self.multi_page_urls or [],
            'url_structure_type': self.url_structure_type,
            'title': self.title,
            'meta_keywords': self.meta_keywords,
            'meta_description': self.meta_description,
            'meta_jdoc': self.meta_jdoc or {},
            'cover': self.cover,
            'author': self.author,
            'category': self.category,
            'categories': self.categories,
            'content': self.content,
            'len_char': self.len_char or 0,
            'content_h1': self.content_h1 or '',
            'content_h2': self.content_h2 or '',
            'content_p': self.content_p or '',
            'len_p': self.len_p or 0,
            'content_image': self.content_image or '',
            'len_img': self.len_img or 0,
            'publish_date': self.publish_date,
            'content_hash': self.content_hash,
            'content_xpath': self.content_xpath,
            # '_ctime': self._ctime,
            # '_mtime': self._mtime
        }


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
    meta_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    content_h1 = Column(Text, nullable=True)
    content_h2 = Column(Text, nullable=True)
    content_p = Column(Text, nullable=True)
    content_image = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def to_inform(self):
        '''
        return only the required key/value for ai_a_crawler()
        '''
        return {
            'id': self.id,
            # 'request_id': self.task_service.request_id, # check!
            'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            # 'wp_url': self.wp_url,
            # 'multi_page_urls': self.multi_page_urls,
            'title': self.title,
            'publish_date': self.publish_date,
            # 'content_hash': self.content_hash,
        }

    def to_dict(self):

        return {
            'id': self.id,
            'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            'multi_page_urls': self.multi_page_urls or [],
            'title': self.title,
            'meta_jdoc': self.meta_jdoc or {},
            'cover': self.cover,
            'author': self.author,
            'content': self.content,
            'content_h1': self.content_h1 or '',
            'content_h2': self.content_h2 or '',
            'content_p': self.content_p or '',
            'content_image': self.content_image or '',
            'publish_date': self.publish_date,
            'content_hash': self.content_hash,
        }


class WebpagesNoService(db.Model):
    __tablename__ = 'webpages_noservice'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), index=True, nullable=True)
    # multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    content_h1 = Column(Text, nullable=True)
    content_h2 = Column(Text, nullable=True)
    content_p = Column(Text, nullable=True)
    content_image = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def to_inform(self):
        '''
        return only the required key/value for ai_a_crawler()
        '''
        return {
            'id': self.id,
            # 'request_id': self.task_service.request_id, # check!
            'task_noservice_id': self.task_noservice_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            # 'wp_url': self.wp_url,
            # 'multi_page_urls': self.multi_page_urls,
            'title': self.title,
            'publish_date': self.publish_date,
            # 'content_hash': self.content_hash,
        }

    def to_dict(self):

        return {
            'id': self.id,
            'task_noservice_id': self.task_noservice_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            # 'multi_page_urls': self.multi_page_urls or [],
            'title': self.title,
            'meta_jdoc': self.meta_jdoc or {},
            'cover': self.cover,
            'author': self.author,
            'content': self.content,
            'content_h1': self.content_h1 or '',
            'content_h2': self.content_h2 or '',
            'content_p': self.content_p or '',
            'content_image': self.content_image or '',
            'publish_date': self.publish_date,
            'content_hash': self.content_hash,
        }


class StructureData(db.Model):
    # to do
    __tablename__ = 'structure_data'

    id = Column(Integer, primary_key=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), index=True, nullable=True)
    og_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
    item_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)
    __table_args__ = (
        Index('idx_structure_data_og_jdoc_gin',
              og_jdoc, postgresql_using="gin"),
        Index('idx_structure_data_item_jdoc_gin',
              item_jdoc, postgresql_using="gin"),
    )


class UrlToContent(db.Model):
    '''
    only partner xpath is stored

    record all the url_hash and its content_hash history

    '''
    __tablename__ = 'url_to_content'

    id = Column(Integer, primary_key=True)
    request_id = Column(String(256), nullable=True)
    url_hash = Column(String(64), nullable=False)
    url = Column(String(1000), nullable=False)
    domain = Column(String(500), nullable=True, index=True)
    content_hash = Column(String(256), nullable=False)
    # a tag to present if AC is informed to replace this url_hash with new one
    replaced = Column(Boolean, default=False)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_url_to_content_url_hash_content_hash',
              url_hash, content_hash, unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'url_hash': self.url_hash,
            'domain': self.domain,
            'url': self.url,
            'content_hash': self.content_hash
        }


class DomainInfo(db.Model):
    __tablename__ = 'domain_info'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=False, index=True)
    partner_id = Column(String(64), nullable=False, index=True)
    rules = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)  # to be checked!

    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_domain_info_rules_gin', rules, postgresql_using="gin"),
        Index('idx_domain_info_domain_partner_id',
              domain, partner_id, unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'partner_id': self.partner_id,
            'rules': self.rules
        }


class BspInfo(db.Model):
    __tablename__ = 'bsp_info'

    id = Column(Integer, primary_key=True)
    bsp = Column(String(500), nullable=True)
    rule = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)  # to be checked!

    __table_args__ = (
        Index('idx_bsp_info_rule_gin', rule, postgresql_using="gin"),
    )


'''
ref:
# Sqlalchemy Table Configuration
https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/table_config.html
# Session
https://docs.sqlalchemy.org/en/latest/orm/session.html

# howto add a column w/o restarting db
# e.g.
ALTER TABLE task_service ADD status_code SMALLINT;

'''
