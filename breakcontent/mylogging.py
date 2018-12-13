MY_LOGGINGS = {
    "version": 1,
    "filters": {
        "request_id": {
            "()": "breakcontent.atomlogging.RequestIdFilter"
        }
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s.%(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(request_id)s - %(message)s"
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
            "filename": "/var/log/breaktime/app-content.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": None,
            "delay": False,
            "utc": False,
            "atTime": None
        }
    },
    "root": {
        'level': 'INFO',
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