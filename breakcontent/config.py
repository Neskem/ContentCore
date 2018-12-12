from celery.schedules import crontab

OUTBOUND_PROXY = None  # for both http/https e.g.'http://127.0.0.1:8080'

ALEMBIC_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB_NUMBER = 7

# Worker
CELERY_DISABLED = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://redis:6379/7'
CELERY_TIMEZONE = 'utc'
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ['json']
# CELERY_ROUTES = {
#    'breakcontent.tasks.execute_aysnc_task': {'queue': 'aysnc_task'},
# }

# priority: 1(blogger), 2(was partner), 3(wasn't partner), 4(scan index page), 5(sitemap), 6(main update/day)
CELERYBEAT_SCHEDULE = {
    'aync_partner_task': {
        'task': 'breakcontent.tasks.aync_filter_task',
        # 'schedule': crontab(minute=30, hour=1),
        # Testing schedule beat for sending task to content core in every minute.
        'schedule': crontab(minute='*'),
        'args': ([2])
    },
    'main_update_content_task': {
        'task': 'breakcontent.tasks.main_update_content',
        # 'schedule': crontab(minute=30, hour=2),
        'schedule': crontab(minute='*'),
        'args': ([6])
    },
    'sitemap_content_task': {
        'task': 'breakcontent.tasks.sitemap_update_content',
        'schedule': crontab(minute=30, hour=3),
        'args': ([5])
    },
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

# Partner System
PARTNER_SYSTEM_API = 'https://partner.breaktime.com.tw/api'
