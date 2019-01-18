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
    logger.debug(
        f'run delete_main_task(), down stream records will also be deleted...')
    tmd = TaskMain.query.filter_by(**data).first()
    db.session.delete(tmd)
    db.session.commit()
    logger.debug('done delete_main_task()')


@celery.task()
def upsert_main_task(data: dict):
    '''
    upsert doc in TaskMain, TaskService and TaskNoService
    '''
    r_required = ['url_hash', 'url']
    rdata = {k: v for (k, v) in data.items() if k in r_required}

    try:
        tm = TaskMain(**data)
        if data.get('partner_id', None):
            tm.task_service = TaskService(**rdata)
        else:
            tm.task_noservice = TaskNoService(**rdata)
        db.session.add(tm)
        db.session.commit()
        logger.debug(f'done insert')
    except IntegrityError as e:
        db.session.rollback()
        udata = {'url_hash': data['url_hash']}
        data.pop('url_hash')
        rdata.pop('url_hash')
        tmu = TaskMain.query.filter_by(**udata).first()
        diff = None
        for k, v in data.items():
            if hasattr(tmu, k) and getattr(tmu, k) != v:
                setattr(tmu, k, v)
                diff = True
        for k, v in rdata.items():
            if data.get('partner_id', None):
                if hasattr(tmu.task_service, k) and getattr(tmu.task_service, k) != v:
                    setattr(tmu.task_service, k, v)
                    diff = True
            else:
                if hasattr(tmu.task_noservice, k) and getattr(tmu.task_noservice, k) != v:
                    setattr(tmu.task_noservice, k, v)
                    diff = True
        if diff:
            db.session.commit()
            logger.debug('done update')
        else:
            logger.debug('no change, quit update')


@celery.task()
def create_tasks(priority):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks()...")
    with db.session.no_autoflush:
        tml = TaskMain.query.filter_by(priority=priority).order_by(
            TaskMain._ctime.asc()).limit(10).all()

        logger.debug(f'len {len(tml)}')

        diff = None
        for tm in tml:
            logger.debug(f'update {tm.task_service}...')
            data = {
                'status_ai': 'doing',
                'status_xpath': 'doing'
            }
            for k, v in data.items():
                if hasattr(tm.task_service, k) and getattr(tm.task_service, k) != v:
                    setattr(tm.task_service, k, v)
                    diff = True

            logger.debug(f'update {tm.task_noservice}...')
            data = {
                'status': 'doing',
            }
            for k, v in data.items():
                if hasattr(tm.task_noservice, k) and getattr(tm.notask_service, k) != v:
                    setattr(tm.task_noservice, k, v)
                    diff = True

        if diff == True:
            db.session.commit()
            logger.debug('done create_tasks()')
        else:
            logger.debug('no change, quit update')


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
