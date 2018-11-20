from .factory import create_celery_app
import logging
celery = create_celery_app()


# @celery.task()
@celery.task()
def test_delay(dpi_json):
    import time
    time.sleep(2)
    logging.info('Alan_test: test_delay: {}'.format(dpi_json))
    return dpi_json


@celery.task(ignore_result=True)
def test_queue(dpi_json):
    logging.info('Alan_test: test_queue: {}'.format(dpi_json))
