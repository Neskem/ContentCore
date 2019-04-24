from flask import Flask, current_app
from breakcontent import config
# import os
from breakcontent import db
from celery import Celery
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration


def create_app(config_obj=None):
    app = Flask(__name__)
    app.logger.info(f'flask app is up by Lance!')
    # app.logger.error(f'error from create_app')
    app.config.from_object(config)
    if app.config['SENTRY_DSN']:
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration(), CeleryIntegration()]
        )

    if config_obj:
        app.config.from_object(config_obj)

    with app.app_context():
        db.init_app(app)
        app.logger.debug(f"app.config['CLEAN_TABLE'] {app.config['CLEAN_TABLE']}")
        if app.config['CLEAN_TABLE']:
            db.drop_all()
            app.logger.debug('drop all tables')
        db.create_all()
        db.session.commit()
        from breakcontent.api.v1.endpoints import bp as endpoints_bp
        app.register_blueprint(endpoints_bp, url_prefix='/v1')

    return app


def create_celery_app(app=None):
    app = app or create_app()
    if app.config['CELERY_DISABLED']:
        app.logger.error(
            f"Celery setting was disable, status: {app.config['CELERY_DISABLED']}")
        return Celery(__name__)

    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND'], include=['breakcontent.tasks'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    # celery.autodiscover_tasks(['breakcontent'], related_name='tasks')

    celery.app = app
    app.logger.info(f'Celery is up by Lance!')
    return celery
