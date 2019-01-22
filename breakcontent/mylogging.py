from breakcontent.config import CONTAINER_TAG
import logging.config

MY_LOGGINGS = {
    "version": 1,
    "filters": {
        "request_id": {
            "()": "breakcontent.atomlogging.RequestIdFilter"
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
            "filename": f"/var/log/contentcore/app-contentcore-{CONTAINER_TAG}.log" if CONTAINER_TAG else "/var/log/contentcore/app-contentcore.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            # "encoding": None,
            "encoding": 'utf-8',  # if not set to 'utf-8', Unicode char will fail to log
            "delay": False,
            "utc": False,
            "atTime": None
        }
    },
    "root": {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    },
    "loggers": {
        "default": {
            "level": "DEBUG",
            "handlers": ["console", "file"]
        }
    },
    "disable_existing_loggers": False,
}

logging.config.dictConfig(MY_LOGGINGS)
