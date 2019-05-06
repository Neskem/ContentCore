from breakcontent.config import *
import logging.config
import logging
import uuid
import flask


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = RequestIdFilter.request_id(
        ) if flask.has_request_context() else '-'
        return True

    @classmethod
    def request_id(cls):
        if getattr(flask.g, 'request_id', None):
            return flask.g.request_id

        headers = flask.request.headers
        original_request_id = headers.get("X-REQUEST-ID")
        new_uuid = RequestIdFilter.generate_request_id(original_request_id)
        flask.g.request_id = new_uuid

        return new_uuid

    @classmethod
    # Generate a new request ID, optionally including an original request ID
    def generate_request_id(cls, original_id=''):
        if original_id:
            new_id = original_id
        else:
            new_id = uuid.uuid4()
        return new_id


MY_LOGGINGS = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": RequestIdFilter
        }
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s:%(module)s:%(funcName)s:%(lineno)d - %(levelname)s - %(process)d - %(request_id)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filters": ["request_id"]
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filters": ["request_id"],
            "filename": f"/var/log/contentcore/{CONTAINER_TAG}.log" if CONTAINER_TAG else "/var/log/contentcore/app-contentcore.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 3,
            "encoding": 'utf-8',  # if not set to 'utf-8', Unicode char will fail to log
            "delay": False,
            "utc": False,
            "atTime": None
        }
    },
    "root": {
        'level': 'DEBUG',  # change to higher level when switching to prd
        'handlers': ['console', 'file']
    },
    "loggers": {
        "cc": {
            "level": "DEBUG",  # change to higher level when switching to prd
            "handlers": ['console', 'file']
            # "propagate": True
        }
    },
}

logging.config.dictConfig(MY_LOGGINGS)

# client = google.cloud.logging.Client()
# cloud_handler = CloudLoggingHandler(client, name='cc_cloud')
# logger = logging.getLogger('cc')
# logger.addHandler(cloud_handler)
# logger.info('CC Hello World!')
