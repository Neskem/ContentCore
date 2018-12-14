from flask import Flask
from . import config
import os
from .model import db
from celery import Celery
import logging
import logging.config
from breakcontent.mylogging import MY_LOGGINGS


def create_app(config_obj=None):
    logging.config.dictConfig(MY_LOGGINGS)
    app = Flask(__name__)
    app.logger.info(f'flask app is up!')
    # load default settings

    # load environment-specific settings
    app.config.from_object(config)
    # load extra settings for testing purpose
    if config_obj:
        app.config.from_object(config_obj)
    with app.app_context():
        db.init_app(app)
        from breakcontent.api.v1.aujs import bp as aujs_bp
        app.register_blueprint(aujs_bp, url_prefix='/v1')

    return app


def create_celery_app(app=None):
    app = app or create_app()
    if app.config['CELERY_DISABLED']:
        logging.info('Celery setting was disable, status: {}'.format(
            app.config['CELERY_DISABLED']))
        return Celery(__name__)

    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    celery.app = app
    return celery
