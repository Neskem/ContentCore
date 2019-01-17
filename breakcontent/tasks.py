from breakcontent.factory import create_celery_app
import json
import requests
from flask import current_app
from celery.utils.log import get_task_logger
import xml.etree.ElementTree as ET
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
from breakcontent import mylogging

celery = create_celery_app()
logger = get_task_logger('default')


@celery.task()
def test_task():
    '''
    for testing logging only
    '''
    logger.info('[celery] run test_task')


@celery.task()
def delete_main_task(data: dict):
    logger.debug(f'run delete_main_task()...')
    tm = db.session.query(TaskMain).filter_by(**data).first()
    db.session.delete(tm)
    db.session.commit()
    logger.debug('done delete_main_task()')


@celery.task()
def upsert_main_task(data: dict):
    '''
    upsert doc in TaskMain, TaskService and TaskNoService
    '''
    r_required = ['url_hash', 'url']
    rdata = {k: v for (k, v) in data.items() if k in r_required}
    # logger.debug(f'rdata {rdata}')

    try:
        logger.debug('start insert')
        tm = TaskMain(**data)
        tm.task_service = TaskService(**rdata)
        db.session.add(tm)
        db.session.commit()
        logger.debug('done insert')
    except IntegrityError as e:
        logger.error(e)
        db.session.rollback()
        logger.debug('start update')
        udata = {'url_hash': data['url_hash']}
        tmf = TaskMain.query.filter_by(**udata).first()
        for k, v in data.items():
            if hasattr(tmf, k):
                setattr(tmf, k, v)
        for k, v in rdata.items():
            if hasattr(tmf.task_service, k):
                setattr(tmf.task_service, k, v)
        db.session.commit()
        logger.debug('done update')

    # if data.get('partner_id', None):
    #     do_upsert(TaskMain, data, 'url_hash',
    #               'task_service', TaskService, rdata, 'url_hash')
    # else:
    #     do_upsert(TaskMain, data, 'url_hash',
    #               'task_noservice', TaskNoService, rdata, 'url_hash')



@celery.task()
def create_tasks(priority):
    '''
    generate tasks

    test in python shell:
from breakcontent.tasks import create_tasks
create_tasks.delay(1)

    '''
    logger.debug(f"run create_tasks()...")
    with db.session.no_autoflush:
        tml = db.session.query(TaskMain).filter_by(
            priority=priority).order_by(TaskMain._ctime.asc()).limit(10).all()

        logger.debug(f'len {len(tml)}')

        for tm in tml:
            logger.debug(f'tm.url_hash: {tm.url_hash}')
            if hasattr(tm, 'task_service'):
                data = {
                    'status_ai': 'doing',
                    'status_xpath': 'doing'
                }
                data.update({'url_hash': tm.url_hash})
                logger.debug(f'lance debug 001: {data}')
                tm.task_service = TaskService(**data)

            # if hasattr(tm, 'task_noservice'):
            #     data = {
            #         'status': 'doing',
            #     }
            #     data.update({'url_hash': tm.url_hash})
            #     logger.debug(f'lance debug 002: {data}')
            #     tm.task_noservice = TaskNoService(**data)
            # db.session.add(tm)
        db.session.commit()
        logger.debug('done create_tasks()')


@celery.task()
def do_task(priority):
    '''
    generate tasks by priority
    '''
    pass


@celery.task()
def xpath_single_crawler():
    pass


@celery.task()
def xpath_multi_crawler():
    '''
    loop xpath_a_crawler by page number
    '''
    pass


def xpath_a_crawler():
    '''
    use xpath to crawl a page
    '''


@celery.task()
def ai_single_crawler():
    pass


@celery.task()
def ai_multi_crawler():
    pass


def ai_a_crawler():
    '''
    use mercury to crawl a page
    '''
