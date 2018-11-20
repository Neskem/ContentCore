from . import db
import datetime


class UrlInfo(db.Model):
    __tablename__ = 'url_info'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000), nullable=False)
    url_hash = db.Column(db.String(256), nullable=True, index=True, unique=True)
    url_structure_type = db.Column(db.String(64), nullable=True)
    partner_id = db.Column(db.String(64), nullable=True)
    _ctime = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)


class TaskInfo(db.Model):
    __tablename__ = 'task_info'
    id = db.Column(db.Integer, primary_key=True)
    url_hash = db.Column(db.String(64), db.ForeignKey('url_info.url_hash'), nullable=False, index=True)
    notify_status = db.Column(db.String(64), nullable=True)
    priority = db.Column(db.Integer, nullable=True)
    retry = db.Column(db.Integer, nullable=True)
    request_id = db.Column(db.String(256), nullable=True)
    _ctime = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)


class ServiceInfo(db.Model):
    __tablename__ = 'service_info'
    id = db.Column(db.Integer, primary_key=True)
    url_hash = db.Column(db.String(64), db.ForeignKey('url_info.url_hash'), nullable=False, index=True)
    status = db.Column(db.Enum('syncing', 'failed', 'finished', name='sync_status'), nullable=True)
    service = db.Column(db.String(64), nullable=False)
    service_status = db.Column(db.String(64), nullable=True)
    service_url_title = db.Column(db.String(1000), nullable=True)
    get_content_status = db.Column(db.String(64), nullable=True)
    _ctime = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    _mtime = db.Column(db.DateTime(timezone=False), onupdate=datetime.datetime.utcnow, default=datetime.datetime.utcnow)
