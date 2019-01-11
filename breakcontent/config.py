from celery.schedules import crontab
import os

DEBUG = os.environ.get('DEBUG', False)

CONTAINER_TAG = os.environ.get('CONTAINER_TAG', '')

OUTBOUND_PROXY = None  # for both http/https e.g.'http://127.0.0.1:8080'

# ALEMBIC_DATABASE_URI = 'sqlite:///:memory:'
# SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 4)
REDIS_DB_NUMBER = os.environ.get('REDIS_DB_NUMBER', 7)

# Worker
CELERY_DISABLED = os.environ.get('CELERY_DISABLED', False)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_TASK_SERIALIZER = os.environ.get('CELERY_TASK_SERIALIZER')
CELERY_RESULT_SERIALIZER = os.environ.get('CELERY_RESULT_SERIALIZER')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE')
CELERY_ENABLE_UTC = True
# CELERY_ACCEPT_CONTENT = os.environ.get('CELERY_ACCEPT_CONTENT')
# copy the syntax from Eric
CELERY_ACCEPT_CONTENT = (os.environ.get(
    'CELERY_ACCEPT_CONTENT') or ' '.join(['msgpack'])).split()
SINGLE_BEAT_REDIS_SERVER = os.environ.get('SINGLE_BEAT_REDIS_SERVER')

ALLOW_ORIGINS = os.environ.get('ALLOW_ORIGINS')

# defines how tasks are sent into broker, which task to which queue
CELERY_ROUTES = {
    # 'breakcontent.tasks.upsert_main_task': {'queue': 'task_manager'},
}

# priority: 1(blogger), 2(was partner), 3(wasn't partner), 4(scan index page), 5(sitemap), 6(main update/day)
CELERYBEAT_SCHEDULE = {
    # 'aync_partner_task': {
    #     'task': 'breakcontent.tasks.aync_filter_task',
    #     # 'schedule': crontab(minute=30, hour=1),
    #     # Testing schedule beat for sending task to content core in every minute.
    #     'schedule': crontab(minute='*'),
    #     'args': ([2])
    # },
    # 'main_update_content_task': {
    #     'task': 'breakcontent.tasks.main_update_content',
    #     # 'schedule': crontab(minute=30, hour=2),
    #     'schedule': crontab(minute='*'),
    #     'args': ([6])
    # },
    # 'sitemap_content_task': {
    #     'task': 'breakcontent.tasks.sitemap_update_content',
    #     'schedule': crontab(minute=30, hour=3),
    #     'args': ([5])
    # },
    # 'retry-content-core': {
    #     'task': 'breakcontent.tasks.test_sync_beat',
    #     'schedule': crontab(minute='*/2'),
    #     'args': (),
    # },
    # 'scan-index-update': {
    #     'task': 'breakcontent.tasks.execute_aysnc_task',
    #     'schedule': crontab(minute='*'),
    #     'args': (),
    #     'options': {'queue': 'aysnc_task'}
    # },
}


PARTNER_SYSTEM_API = os.environ.get('PARTNER_SYSTEM_API')
ADD_DEFAULT_SCHEDULE = os.environ.get('ADD_DEFAULT_SCHEDULE')
UPLOAD_BASELINE_LOCK_TIMEOUT = os.environ.get('UPLOAD_BASELINE_LOCK_TIMEOUT')
MAX_CONTENT_LENGTH = os.environ.get('MAX_CONTENT_LENGTH')
