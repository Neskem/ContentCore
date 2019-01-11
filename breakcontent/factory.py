from flask import Flask
from breakcontent import config
import os
from breakcontent import db
from celery import Celery
import logging
import logging.config
from breakcontent.mylogging import MY_LOGGINGS


def create_app(config_obj=None):
    logging.config.dictConfig(MY_LOGGINGS)
    app = Flask(__name__)
    app.logger.info(f'flask app is up by Lance!')
    app.config.from_object(config)

    if config_obj:
        app.config.from_object(config_obj)

    with app.app_context():
        db.init_app(app)
        db.create_all()
        db.session.commit()
        from breakcontent.api.v1.endpoints import bp as endpoints_bp
        app.register_blueprint(endpoints_bp, url_prefix='/v1')

    return app


def create_celery_app(app=None):
    app = app or create_app()
    # app.logger.info(app, type(app))
    # app.logger.info(type(app.config['CELERY_DISABLED']))
    if app.config['CELERY_DISABLED']:
        print(
            f"Cerely setting was disable, status: {app.config['CELERY_DISABLED']}")
        return Celery(__name__)

    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    # app.logger.info(type(TaskBase))

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    celery.app = app
    print(f'Celery is up by Lance!')
    return celery
