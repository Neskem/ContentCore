from celery.schedules import crontab
import os


DEBUG = os.environ.get('DEBUG', False)

CONTAINER_TAG = os.environ.get('CONTAINER_TAG', '')

OUTBOUND_PROXY = None
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 10))
SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('SQLALCHEMY_POOL_TIMEOUT', 30))
SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 30))
SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 15))
CLEAN_TABLE = True if os.environ.get('CLEAN_TABLE') == 'True' else False

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
REDIS_DB = os.environ.get('REDIS_DB', 4)
REDIS_DB_NUMBER = os.environ.get('REDIS_DB_NUMBER', 7)

# Worker
CELERY_DISABLED = False if os.environ.get('CELERY_DISABLED', False) in [
    'False', 'false', False] else True
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_TASK_SERIALIZER = os.environ.get('CELERY_TASK_SERIALIZER')
CELERY_RESULT_SERIALIZER = os.environ.get('CELERY_RESULT_SERIALIZER')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE')
CELERY_TASK_RESULT_EXPIRES = os.environ.get('CELERY_TASK_RESULT_EXPIRES', 3600)
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = (os.environ.get(
    'CELERY_ACCEPT_CONTENT') or ' '.join(['msgpack'])).split()
SINGLE_BEAT_REDIS_SERVER = os.environ.get('SINGLE_BEAT_REDIS_SERVER')

ALLOW_ORIGINS = os.environ.get('ALLOW_ORIGINS')

CELERY_ROUTES = {
    'breakcontent.tasks.upsert_main_task': {'queue': 'upsert_tm'},
    'breakcontent.tasks.prepare_task': {'queue': 'prepare'},
    'breakcontent.tasks.mimic_aujs_request_ac': {'queue': 'bypass_crawler'},
    'breakcontent.tasks.bypass_crawler': {'queue': 'bypass_crawler'},
    'breakcontent.tasks.ai_single_crawler': {'queue': 'aicrawler'},
    'breakcontent.tasks.ai_multi_crawler': {'queue': 'aicrawler'},
    'breakcontent.tasks.xpath_single_crawler': {'queue': 'xpcrawler'},
    'breakcontent.tasks.xpath_multi_crawler': {'queue': 'xpmcrawler'},
    'breakcontent.tasks.high_speed_p1': {'queue': 'priority_1'}
}

# priority: 1(blogger), 2(was partner), 3(wasn't partner), 4(scan index page), 5(sitemap)
CELERYBEAT_SCHEDULE = {
    # 'create_tasks_1': {
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([1])
    # },
    # 'create_tasks_2': {
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([2, 4000])
    # },
    # 'create_tasks_3': {
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([3])
    # },
    # 'create_tasks_4': {
    #     # todo: selenium
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([4])
    # },
    # 'create_tasks_5': {
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([5])
    # },
    # 'create_tasks_6': {  # Update task (including daily and monthly)
    #     'task': 'breakcontent.tasks.create_tasks',
    #     'schedule': crontab(minute='*'),
    #     'args': ([6]),
    #     # 'options': {'queue': 'postman'}
    # },
    # 'reset_doing_task': {
    #     'task': 'breakcontent.tasks.reset_doing_tasks',
    #     'schedule': crontab(minute=0, hour='*'),
    #     'args': ([1])
    # },
    # 'stats_cc': {
    #     'task': 'breakcontent.tasks.stats_cc',
    #     'schedule': crontab(minute=0, hour=7),
    #     # this is 7:00AM TW time
    #     'args': (['day']),
    # },
}

# CC
TASK_NUMBER_PER_BEAT = os.environ.get('TASK_NUMBER_PER_BEAT', 500)
PARTNER_SYSTEM_API = os.environ.get('PARTNER_SYSTEM_API')
# ADD_DEFAULT_SCHEDULE = os.environ.get('ADD_DEFAULT_SCHEDULE')
# UPLOAD_BASELINE_LOCK_TIMEOUT = os.environ.get('UPLOAD_BASELINE_LOCK_TIMEOUT')
# MAX_CONTENT_LENGTH = os.environ.get('MAX_CONTENT_LENGTH')
SENTRY_DSN = os.environ.get('SENTRY_DSN', None)
MIMIC_AUJS = False if os.environ.get('MIMIC_AUJS', False) in [
    'False', 'false', False] else True
RUN_XPATH_MULTI_CRAWLER = False if os.environ.get('RUN_XPATH_MULTI_CRAWLER', False) in [
    'False', 'false', False] else True
ONLY_PERMIT_P1 = False if os.environ.get('ONLY_PERMIT_P1', False) in [
    'False', 'false', False] else True

# PartnerSystem
PS_DOMAIN_API = os.environ.get('PS_DOMAIN_API', None)

# AI crawler
MERCURY_TOKEN = os.environ.get('MERCURY_TOKEN', None)
PARTNER_AI_CRAWLER = False if os.environ.get('PARTNER_AI_CRAWLER', None) in [
    'false', 'False', 0, False] else True


# Article Center
AC_CONTENT_STATUS_API = os.environ.get('AC_CONTENT_STATUS_API', None)

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS', None)

MERCURY_PATH = os.environ.get('MERCURY_PATH', None)
