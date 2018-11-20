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
"""
CELERY_ROUTES = {
   'breakarticle.tasks.test_queue': {'queue': 'test_queue'},
}
"""
CELERYBEAT_SCHEDULE = {
    'sysinfo-scheduler': {
        'task': 'atomtarsier.tasks.start_sysinfo_gen_report_scheduler',
        'schedule': crontab(minute='*/5'),
        'args': (),
    },
    'hips-scheduler': {
        'task': 'atomtarsier.tasks.notify_virtual_patch_gradually',
        'schedule': crontab(minute='*'),
        'args': (),
    },

}

# enable this option to add a default schedule after baseline upload
ADD_DEFAULT_SCHEDULE = False

# Partner System MySQL
MYSQL_HOST = '35.201.153.247'
MYSQL_USER = 'bt_user'
MYSQL_PASSWD = 'i<3Breaktime'
MYSQL_DATABASE = 'alliance'
