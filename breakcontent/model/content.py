from breakcontent.model import db
import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import func, Index
from sqlalchemy.exc import IntegrityError


class TaskMain(db.Model):
    __tablename__ = 'task_main'
    id = db.Column(db.Integer, primary_key=True)
    url_hash = db.Column(db.String(64), nullable=False, index=True)
    url = db.Column(db.String(1000), nullable=False)
    request_id = db.Column(db.String(256), nullable=True)
    partner_id = db.Column(db.String(64), nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    # generate many from one
    parent_url = db.Column(db.String(1000), nullable=True)
    is_multipage = db.Column(db.Boolean, nullable=True)
    task_service_id = db.Column(db.Integer, nullable=True)
    task_noservice_id = db.Column(db.Integer, nullable=True)
    # notify AC when the task is finished
    notify_status = db.Column(
        db.Enum('yes', 'no', name='notify_status'), nullable=True)
    notify_time = db.Column(db.DateTime(timezone=False), nullable=True)
    # return article data as AC requested
    article_send_status = db.Column(
        db.Enum('yes', 'no', name='article_send_status'), nullable=True)
    article_send_time = db.Column(db.DateTime(timezone=False), nullable=True)
    _ctime = db.Column(db.DateTime(timezone=False),
                       default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    db.Index('idx_url_hash', url_hash, unique=True)

    def __init__(**kwargs):
        super(TaskMain, self).__init__(**kwargs)
        # do custom stuff

    def upsert(self, row, retry=2, with_primary_key=False):
        while retry:
            retry -= 1
            try:
                db.session.add(row)
                db.session.commit()
                if with_primary_key is True:
                    return row.id
            except IntegrityError as e:
                raise e
            except Exception as e:
                if retry <= 0:
                    db.session.rollback()
                    raise e

    def __repr__(self):
        return f'<TaskMain(id={self.id}, url_hash={self.url_hash}, url={url}, request_id={self.request_id})>'


class TaskService(db.Model):
    __tablename__ = 'task_service'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(
        'task_main.id'), nullable=False)
    url_hash = db.Column(db.String(64), nullable=False, index=True)
    url = db.Column(db.String(1000), nullable=False)
    request_id = db.Column(db.String(256), nullable=False)
    secret = db.Column(db.Boolean, nullable=True)
    retry_xpath = db.Column(db.Integer, default=0)
    status_xpath = db.Column(db.Enum('pending', 'doing', 'done',
                                     'failed', name='status_xpath'), nullable=True)
    retry_ai = db.Column(db.Integer, default=0)
    status_ai = db.Column(db.Enum('pending', 'doing', 'done',
                                  'failed', name='status_ai'), nullable=True)
    webpages_xpath_id = db.Column(db.Integer, nullable=True)
    webpages_ai_id = db.Column(db.Integer, nullable=True)
    # start datetime
    _stime = db.Column(db.DateTime(timezone=False),
                       default=datetime.datetime.utcnow)
    _ctime = db.Column(db.DateTime(timezone=False),
                       default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TaskService(id={self.id}, url_hash={self.url_hash}, url={url}, request_id={self.request_id})>'


class TaskNoService(db.Model):
    __tablename__ = 'task_noservice'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(
        'task_main.id'), nullable=False)
    url_hash = db.Column(db.String(64), nullable=False, index=True)
    url = db.Column(db.String(1000), nullable=False)
    request_id = db.Column(db.String(256), nullable=True)
    secret = db.Column(db.Boolean, nullable=True)
    retry = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('pending', 'doing', 'done',
                               'failed', name='task_noservice_status'), nullable=True)
    webpages_id = db.Column(db.Integer, nullable=True)
    # start datetime
    _stime = db.Column(db.DateTime(timezone=False),
                       default=datetime.datetime.utcnow)
    _ctime = db.Column(db.DateTime(timezone=False),
                       default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(
        timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<TaskNoService(id={self.id}, url_hash={self.url_hash}, url={url}, request_id={self.request_id})>'


class WebpagesPartnerXpath(db.Model):
    __tablename__ = 'webpages_partner_xpath'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(
        'task_service.id'), nullable=False)
    domain = db.Column(db.String(500), nullable=True)
    url_hash = db.Column(db.String(64), nullable=False, index=True)
    content_hash = db.Column(db.String(256), nullable=True)
    multi_page_urls = db.Column(postgresql.ARRAY(db.Text(), dimensions=1))
    url_structure_type = db.Column(db.Enum(
        'home', 'list', 'content', 'others', name='url_structure_type'), nullable=True)
    url = db.Column(db.String(1000), nullable=False)
    wp_url = db.Column(db.String(500), nullable=True)  # only WP bsp has it
    title = db.Column(db.Text(), nullable=True)
    meta_keywords = db.Column(db.String(200), nullable=True)
    meta_description = db.Column(db.Text(), nullable=True)
    meta_jdoc = db.Column(postgresql.JSONB(
        none_as_null=False, astext_type=None), nullable=True)

    __table_args__ = (
        db.Index('idx_gin_meta_jdoc', meta_jdoc, postgresql_using="gin"),
    )


'''
ref:
# Sqlalchemy Table Configuration
https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/table_config.html
# Session
https://docs.sqlalchemy.org/en/latest/orm/session.html


'''
