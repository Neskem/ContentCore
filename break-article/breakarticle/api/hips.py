from flask import Blueprint, request
import logging
from breakarticle.helper import api_ok

bp = Blueprint('hips', __name__)


@bp.route('/hips/dpi/callback2', methods=['POST', 'OPTIONS'])
def dpi_callback2():
    """
    This API is for testing celery worker:
    trigger: curl -X POST 'http://localhost:80/v0/hips/dpi/callback2' -H 'Content-Type: application/json' -d 'testing'

    :return: {"data":{},"message":"OK"}

    While watch app-article.log that before sleep fun the result.ready() is False,
        but after sleep fun the result.ready() is True.

    Print article-worker.log will see "Alan_test: test_delay" output from tasks.py

    PS: Remove CELERY_IGNORE_RESULT setting from config.py to prevent result value can't insert to redis backend.
        (Need to rebuild container to reset celery setting)
    """
    dpi_json = request.get_data()
    logging.info("dpi2 : {}".format(dpi_json))
    from breakarticle.tasks import test_delay
    result = test_delay.delay(dpi_json)
    logging.info("result.ready()_up: {}".format(result.ready()))
    import time
    time.sleep(5)
    logging.info("result.ready()_down: {}".format(result.ready()))
    if result.ready():
        logging.info("result.get : {}".format(result.get(timeout=1)))
    return api_ok("OK")


@bp.route('/hips/dpi/callback3', methods=['POST', 'OPTIONS'])
def dpi_callback3():
    """
    This API is for testing celery worker by queue to execute:

    Add content to config.py:
        CELERY_ROUTES = {
            'breakarticle.tasks.test_queue': {'queue': 'test_queue'},
        }

    Execute worker in article-dev container:
    /usr/bin/python3 /usr/local/bin/celery -A breakarticle.tasks worker -Q test_queue -l info &

    trigger: curl -X POST 'http://localhost:80/v0/hips/dpi/callback3' -H 'Content-Type: application/json' -d 'testing'

    Only listen test_queue worker will execute this job and print output to screen.
    """
    dpi_json = request.get_data()
    logging.info("dpi3 : {}".format(dpi_json))
    from breakarticle.tasks import test_queue
    result = test_queue.delay(dpi_json)
    logging.info("result.get() : {}".format(result.get()))
    logging.info("result.traceback : {}".format(result.traceback))
    return api_ok("OK")
