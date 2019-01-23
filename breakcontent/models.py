from breakcontent import db
import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import func, Index, Column, ForeignKey
from sqlalchemy import Integer, Boolean, Enum, DateTime, String, Text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, backref

'''
ref
* cascade delete
https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete
* cascade
https://docs.sqlalchemy.org/en/latest/orm/cascades.html
'''


class TaskMain(db.Model):
    __tablename__ = 'task_main'
    id = Column(Integer, primary_key=True)
    task_service = relationship(
        "TaskService", back_populates="task_main", uselist=False, foreign_keys='TaskService.task_main_id', cascade="all, delete-orphan", passive_deletes=True)
    task_noservice = relationship(
        "TaskNoService", back_populates="task_main", uselist=False, foreign_keys='TaskNoService.task_main_id', cascade="all, delete-orphan", passive_deletes=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    url = Column(String(1000), nullable=False, unique=True)
    # request_id = Column(String(256), index=True, nullable=True)
    request_id = Column(String(256), nullable=True)
    partner_id = Column(String(64), nullable=True)
    priority = Column(Integer, nullable=True)
    generator = Column(String(100), nullable=True)
    # generate many from one
    parent_url = Column(String(1000), nullable=True)
    # is_multipage = Column(Boolean, nullable=True)
    # task_service_id = Column(Integer, nullable=True)
    # task_noservice_id = Column(Integer, nullable=True)
    # notify AC when the task is finished
    status = Column(Enum('pending', 'doing', 'done',
                         'failed', name='status_tm'), default='pending')
    notify_status = Column(
        Enum('yes', 'no', name='notify_status'), default='no')
    notify_time = Column(DateTime(timezone=False), nullable=True)
    # return article data as AC requested
    article_send_status = Column(
        Enum('yes', 'no', name='article_send_status'), default='no')
    article_send_time = Column(DateTime(timezone=False), nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(TaskMain, self).__init__(*args, **kwargs)
        # do custom stuff

    def __repr__(self):
        return f'<TaskMain(id={self.id}, url_hash={self.url_hash}, url={self.url}, request_id={self.request_id})>'


class TaskService(db.Model):
    __tablename__ = 'task_service'
    id = Column(Integer, primary_key=True)
    task_main_id = Column(Integer, ForeignKey(
        'task_main.id', ondelete='CASCADE'))
    task_main = relationship(
        'TaskMain', foreign_keys=task_main_id, single_parent=True)
    webpages_partner_xpath = relationship("WebpagesPartnerXpath", back_populates="task_service", uselist=False,
                                          foreign_keys='WebpagesPartnerXpath.task_service_id', cascade="all, delete-orphan", passive_deletes=True)
    webpages_partner_ai = relationship("WebpagesPartnerAi", back_populates="task_service", uselist=False,
                                       foreign_keys='WebpagesPartnerAi.task_service_id', cascade="all, delete-orphan", passive_deletes=True)
    url_hash = Column(String(64), unique=True, nullable=False)
    url = Column(String(1000), unique=True)
    partner_id = Column(String(64), nullable=True)
    request_id = Column(String(256), index=True, nullable=True)
    page_query_param = Column(String(50), nullable=True)
    is_multipage = Column(Boolean, default=False)
    secret = Column(Boolean, default=False)
    retry_xpath = Column(Integer, default=0)
    status_xpath = Column(Enum('pending', 'doing', 'done',
                               'failed', name='status_xpath'), default='pending')
    retry_ai = Column(Integer, default=0)
    status_ai = Column(Enum('pending', 'doing', 'done',
                            'failed', name='status_ai'), default='pending')
    # webpages_xpath_id = Column(Integer, nullable=True)
    # webpages_ai_id = Column(Integer, nullable=True)
    # start datetime
    # _stime = Column(DateTime(timezone=False), default=datetime.datetime.utcnow)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

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
            'partner_id': self.partner_id,
            'request_id': self.request_id,
            'is_multipage': self.is_multipage,
            'page_query_param': self.page_query_param,
            'secret': self.secret,
            'retry_xpath': self.retry_xpath,
            'status_xpath': self.status_xpath,
            'retry_ai': self.retry_ai,
            'status_ai': self.status_ai,
            '_ctime': self._ctime,
            '_mtime': self._mtime
        }


class TaskNoService(db.Model):
    __tablename__ = 'task_noservice'
    id = Column(Integer, primary_key=True)
    task_main_id = Column(Integer, ForeignKey(
        'task_main.id', ondelete='CASCADE'))
    task_main = relationship(
        'TaskMain', foreign_keys=task_main_id, single_parent=True)
    url_hash = Column(String(64), ForeignKey(
        'task_main.url_hash'), nullable=False, unique=True)
    url = Column(String(1000), unique=True)
    request_id = Column(String(256), index=True, nullable=True)
    secret = Column(Boolean, nullable=True)  # not required
    retry = Column(Integer, default=0)
    status = Column(Enum('pending', 'doing', 'done',
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
        pass
        # to do


class WebpagesPartnerXpath(db.Model):
    __tablename__ = 'webpages_partner_xpath'

    id = Column(Integer, primary_key=True)
    task_service_id = Column(Integer, ForeignKey(
        'task_service.id', ondelete='CASCADE'))
    task_service = relationship(
        'TaskService', foreign_keys=task_service_id, single_parent=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url_structure_type = Column(Enum(
        'home', 'list', 'content', 'others', name='url_structure_type'), nullable=True)
    url = Column(String(1000), nullable=False)
    wp_url = Column(String(500), nullable=True)  # only WP bsp has it
    title = Column(Text(), nullable=True)
    meta_keywords = Column(String(200), nullable=True)
    meta_description = Column(Text(), nullable=True)
    meta_jdoc = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)
    cover = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    categories = Column(postgresql.ARRAY(Text(), dimensions=1))
    content = Column(Text, nullable=True)
    content_h1 = Column(Text, nullable=True)
    content_h2 = Column(Text, nullable=True)
    content_p = Column(Text, nullable=True)
    len_p = Column(Integer, nullable=True)
    content_image = Column(Text, nullable=True)
    len_img = Column(Integer, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    content_xpath = Column(Text, nullable=True)
    _ctime = Column(DateTime(timezone=False),
                    default=datetime.datetime.utcnow)
    _mtime = Column(DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_gin_meta_jdoc', meta_jdoc, postgresql_using="gin"),
    )

    def to_dict(self):

        return {
            'id': self.id,
            'task_service_id': self.task_service_id,
            'domain': self.domain,
            'url_hash': self.url_hash,
            'url': self.url,
            'wp_url': self.wp_url,
            'multi_page_urls': self.multi_page_urls,
            'url_structure_type': self.url_structure_type,
            'title': self.title,
            'meta_keywords': self.meta_keywords,
            'meta_description': self.meta_description,
            'meta_jdoc': self.meta_jdoc,
            'cover': self.cover,
            'author': self.author,
            'category': self.category,
            'categories': self.categories,
            'content': self.content,
            'content_h1': self.content_h1,
            'content_h2': self.content_h2,
            'content_p': self.content_p,
            'len_p': self.len_p,
            'content_image': self.content_image,
            'len_img': self.len_img,
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
            'wp_url': self.wp_url,
            # 'multi_page_urls': self.multi_page_urls,
            'url_structure_type': self.url_structure_type,
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
            'publishedAt': self.publish_date.isoformat(),
        }


class WebpagesPartnerAi(db.Model):
    __tablename__ = 'webpages_partner_ai'

    id = Column(Integer, primary_key=True)
    task_service_id = Column(Integer, ForeignKey(
        'task_service.id', ondelete='CASCADE'))
    task_service = relationship(
        'TaskService', foreign_keys=task_service_id, single_parent=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
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


class WebpagesNoService(db.Model):
    __tablename__ = 'webpages_noservice'

    id = Column(Integer, primary_key=True)
    task_noservice_id = Column(Integer, ForeignKey(
        'task_noservice.id'), nullable=False)
    task_noservice = relationship(
        'TaskNoService', foreign_keys=task_noservice_id, single_parent=True)
    domain = Column(String(500), nullable=True)
    url_hash = Column(String(64), nullable=False, index=True, unique=True)
    content_hash = Column(String(256), index=True, nullable=True)
    multi_page_urls = Column(postgresql.ARRAY(Text, dimensions=1))
    url = Column(String(1000), nullable=False)
    title = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
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


class StructureData(db.Model):
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
    record all the url_hash and its content_hash history
    '''
    __tablename__ = 'url_to_content'

    id = Column(Integer, primary_key=True)
    request_id = Column(String(256), index=True, nullable=True)
    url_hash = Column(String(64), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    content_hash = Column(String(256), index=True, nullable=True)

    __table_args__ = (
        Index('idx_url_to_content_url_hash_content_hash',
              url_hash, content_hash, unique=True),
    )


class DomainInfo(db.Model):
    __tablename__ = 'domain_info'

    id = Column(Integer, primary_key=True)
    domain = Column(String(500), nullable=True)
    rule = Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)  # to be checked!
    __table_args__ = (
        Index('idx_domain_info_rule_gin', rule, postgresql_using="gin"),
    )


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

'''
