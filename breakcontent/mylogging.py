from breakcontent.config import CONTAINER_TAG
import logging.config
import logging
import uuid
import flask

# Custom logging filter class


class RequestIdFilter(logging.Filter):
    """
    This is a logging filter that makes the request ID available for use in
    the logging format. Note that we're checking if we're in a request
    context, as we may want to log things before Flask is fully loaded.
    """

    def filter(self, record):
        record.request_id = RequestIdFilter.request_id(
        ) if flask.has_request_context() else '-'
        return True

    @classmethod
    def request_id(cls):
        """
        Returns the current request ID or a new one if there is none
        In order of preference:
          * If we've already created a request ID and stored it in the flask.g context local, use that
          * If a client has passed in the X-Request-Id header, create a new ID with that prepended
          * Otherwise, generate a request ID and store it in flask.g.request_id
        :return:
        """
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
            "level": "WARNING",
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
            "backupCount": 7,
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
        "default": {  # this is for celery logger
            "level": "DEBUG",  # change to higher level when switching to prd
            "handlers": ['console', 'file']
        }
    },
    "disable_existing_loggers": False,
}

logging.config.dictConfig(MY_LOGGINGS)

'''
* further study

1. https://docs.python.org/3/library/logging.config.html#user-defined-objects
2. https://docs.python.org/3/howto/logging-cookbook.html


'''
