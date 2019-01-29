from breakcontent.factory import create_celery_app
from breakcontent.utils import Secret, InformAC, DomainSetting, db_session_insert, db_session_query, db_session_update, xpath_a_crawler, parse_domain_info, get_domain_info

from breakcontent.utils import mercuryContent, prepare_crawler, ai_a_crawler

import re
import os
import json
import requests
from flask import current_app
from celery.utils.log import get_task_logger

from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
from breakcontent import mylogging
from urllib.parse import urlencode, quote_plus, unquote, quote, unquote_plus, parse_qs
from urllib.parse import urlparse, urljoin


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
    logger.debug(f'data: {data}')
    r_required = [
        'url_hash',
        'url',
        'request_id',
        'partner_id',
    ]
    rdata = {k: v for (k, v) in data.items() if k in r_required}

    try:
        logger.debug('start inserting')
        logger.debug(f'data {data}')
        logger.debug(f'rdata {rdata}')
        tm = TaskMain(**data)
        if data.get('partner_id', None):
            tm.task_service = TaskService(**rdata)
        else:
            rdata.pop('partner_id')
            tm.task_noservice = TaskNoService(**rdata)
        # db.session.add(tm)
        db_session_insert(db.session, tm)
        logger.debug(f'done insert')
    except IntegrityError as e:
        logger.warning(e)
        db.session.rollback()
        logger.debug('update url/request_id/status/partner_id by url_hash')
        q = dict(url_hash=data['url_hash'])
        # logger.debug(f'q {q}')
        data.update(dict(status='pending'))
        # TaskMain.query.filter_by(**q).update(data)
        logger.debug(f'data {data}')
        db_session_update(db.session, TaskMain, q, data)
        if data.get('partner_id', None):
            rdata.update(dict(status_ai='pending', retry_ai=0,
                              status_xpath='pending', retry_xpath=0))
            # TaskService.query.filter_by(**q).update(rdata)
            db_session_update(db.session, TaskService, q, rdata)
            logger.debug('done update for partner')
        else:
            rdata.pop('partner_id')
            rdata.update(dict(status='pending', retry=0))
            # TaskNoService.query.filter_by(**q).update(rdata)
            db_session_update(db.session, TaskNoService, q, rdata)
        # db.session.commit()
            logger.debug('done update for non partner')


@celery.task()
def create_tasks(priority):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks()...")
    with db.session.no_autoflush:

        q = dict(priority=priority, status='pending')
        tml = db_session_query(db.session, TaskMain, q,
                               order_by=TaskMain._mtime, asc=True, limit=10)

        logger.debug(f'len {len(tml)}')
        if len(tml) == 0:
            logger.debug(f'no result, quit')
            return

        for tm in tml:
            logger.debug(f'update {tm}...')
            tm.status = 'doing'
            db.session.commit()

            if tm.task_service:
                logger.debug(f'update {tm.task_service}...')
                update_ts = {
                    # 'status_ai': 'doing',
                    'status_xpath': 'doing'
                }
                # TaskService.query.filter_by(
                # id=tm.task_service.id).update(update_ts)
                db_session_update(db.session, TaskService, dict(
                    id=tm.task_service.id), update_ts)
                prepare_task.delay(tm.task_service.to_dict())

            if tm.task_noservice:
                logger.debug(f'update {tm.task_noservice}...')
                udata = {'status': 'doing'}
                # TaskNoService.query.filter_by(
                # id=tm.task_noservice.id).update(udata)
                db_session_update(db.session, TaskNoService, dict(
                    id=tm.task_noservice.id), udata)
                prepare_task.delay(tm.task_noservice.to_dict())

        logger.debug('done sending a batch of tasks to broker')


@celery.task()
def prepare_task(task: dict):
    '''
    fetch settings from partner system through api

    argument:
    task: could be a TaskService or TaskNoService dict

    '''

    ps_domain_api_prefix = os.environ.get(
        'PS_DOMAIN_API') or 'https://partner.breaktime.com.tw/api/config/'

    logger.debug('run prepare_task()...')
    logger.debug(f'task {task}')

    if task.get('partner_id', None):

        url = task['url']
        partner_id = task['partner_id']
        o = urlparse(url)
        domain = o.netloc

        logger.debug(f'domain {domain}')
        logger.debug(f'partner_id {partner_id}')

        domain_info = get_domain_info(domain, partner_id)
        return # Lance debug
        if domain_info:
            logger.debug(f'domain_info {domain_info}')
            if domain_info.get('page', None) and domain_info['page'] != '':
                # preparing for multipage crawler
                page_query_param = domain_info['page'][0]
                tsf = db_session_query(
                    db.session, TaskService, dict(id=task['id']))
                tsf.is_multipage = True
                tsf.page_query_param = page_query_param
                db.session.commit()
                logger.debug('update successful')

                mp_url = url
                if page_query_param:
                    if page_query_param == "d+":
                        # mp_url.replace(r'\/\d+$', '')
                        mp_url = re.replace(r'\/\d+$', '', url)
                    else:
                        # mp_url.replace(r'\?(page|p)=\d+', '')
                        mp_url = re.sub(r'\?(page|p)=\d+', '', url)
                logger.debug(f'url {url}')
                logger.debug(f'mp_url {mp_url}')
                ac_content_multipage_api = os.environ.get(
                    'AC_CONTENT_MULTIPAGE_API', None)
                logger.debug(
                    f'ac_content_multipage_api {ac_content_multipage_api}')
                if mp_url != url and ac_content_multipage_api:

                    headers = {'Content-Type': "application/json"}
                    data = {
                        'url': url,
                        'url_hash': task['url_hash'],
                        'multipage': mp_url
                    }

                    r = requests.post(
                        ac_content_multipage_api, json=data, headers=headers)

                    if r.status_code == 200:
                        # json = r.json()
                        logger.debug('inform AC successful')
                        tmf = db_session_query(
                            db.session, TaskMain, dict(id=tsf.task_main_id))
                        db.session.delete(tmf)
                        db.session.commit()

                    else:
                        logger.error('inform AC failed')
                else:
                    logger.info('mp_url = url')
                    xpath_multi_crawler.delay(
                        task['id'], partner_id, domain, domain_info)
                    ai_multi_crawler.delay(
                        task['id'], partner_id, domain, domain_info)

            else:
                # preparing for singlepage crawler

                xpath_single_crawler.delay(
                    task['id'], partner_id, domain, domain_info)

                ai_single_crawler.delay(
                    task['id'], partner_id, domain, domain_info)

        else:
            logger.error(
                f'there is no partner settings for partner_id {partner_id} domain {domain}')

    else:
        # not partner goes here
        pass


@celery.task()
def xpath_single_crawler(tid: int, partner_id: str, domain: str, domain_info: dict):
    '''
    <purpose>
    use the domain config from Partner System to crawl through the entire page, then inform AC with request

    <notice>
    partner only

    <arguments>
    tid,
    partner_id,
    domain,
    domain_info,

    <return>
    '''
    logger.debug(f'start to crawl single-paged url on tid {tid}')
    # logger.debug(f'tid type {type(tid)}')
    # iac = InformAC()
    wpx = prepare_crawler(tid, partner=True, xpath=True)
    # logger.debug(f'wpx {wpx}')

    a_wpx, inform_ac = xpath_a_crawler(wpx, partner_id, domain, domain_info)
    logger.debug(f'a_wpx from xpath_a_crawler(): {a_wpx}')
    logger.debug(f'inform_ac {inform_ac.to_dict()}')

    wpx_data = a_wpx.to_dict()
    # WebpagesPartnerXpath.query.filter_by(
    # id=a_wpx.id).update(wpx_data)

    db_session_update(db.session, WebpagesPartnerXpath,
                      dict(id=a_wpx.id), wpx_data)
    # request_id = wpx_data['request_id']
    # logger.debug(f'request_id {request_id}')
    logger.debug('update successful')

    inform_ac_dict = inform_ac.to_dict()
    # inform_ac_dict.set('request_id', request_id)
    # logger.debug(f'inform_ac_dict {inform_ac_dict}')
    data = json.dumps(inform_ac_dict)
    headers = {'Content-Type': "application/json"}

    ac_content_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)
    logger.debug(f'ac_content_status_api {ac_content_status_api}')
    # inform AC
    r = requests.put(ac_content_status_api, json=data, headers=headers)
    logger.debug(f'payload {data}')
    # logger.debug(f'r {r}')
    # logger.debug(f'r type {type(r)}')
    # logger.debug(f'r dir {dir(r)}')
    # logger.debug(f'r.json {r.json}')
    # logger.debug(f'r.json dir {dir(r.json)}')
    # logger.debug(f'r.text {r.text}')
    # logger.debug(f'r.content {r.content}')
    if r.status_code == 200:
        # json = r.json()
        a_wpx.task_service.status_xpath = 'done'
        db.session.commit()
        logger.debug('inform AC successful')
    elif r.status_code == 400:
        logger.debug('inform AC failed, bad request')
    else:
        logger.error('inform AC failed')


@celery.task()
def xpath_multi_crawler(tid: int, partner_id: str, domain: str, domain_info: dict):
    '''
    partner only

    loop xpath_a_crawler by page number

    ** remember to update the url & url_hash in CC and AC
    '''
    logger.debug(f'start to crawl multipaged url on tid {tid}')

    wpx = prepare_crawler(tid, partner=True, xpath=True)
    url = wpx['url']
    page_query_param = domain_info['page'][0]

    # logger.debug(f'url {url}')
    logger.debug(f'page_query_param {page_query_param}')

    # return
    page_num = 0
    cat_wpx_data = WebpagesPartnerXpath().to_dict()
    cat_inform_ac_data = InformAC().to_dict()
    logger.debug(f'cat_wpx_data {cat_wpx_data}')
    logger.debug(f'cat_inform_ac_dict {cat_inform_ac_data}')
    # return
    multi_page_urls = set()
    while page_num <= 40:
        page_num += 1
        if page_query_param == "d+":
            i_url = f'{url}/{page_num}'
        else:
            i_url = f'{url}?{page_query_param}={page_num}'

        # replace url
        wpx['url'] = i_url
        a_wpx, inform_ac = xpath_a_crawler(
            wpx, partner_id, domain, domain_info, multipaged=True)

        if not inform_ac.status:
            logger.debug(f'failed to crawl {i_url}')
            cat_inform_ac_data['status'] = False
            break

        if not inform_ac.zi_sync_rule:
            logger.critical(
                f'{i_url} does not match the sync criteria (rule/author/category)')
            # don't break, keep crawling

        wpx_data = a_wpx.to_dict()
        inform_ac_data = inform_ac.to_dict()

        logger.debug(f'a_wpx from xpath_a_crawler(): {a_wpx}')
        logger.debug(
            f'inform_ac from xpath_a_crawler(): {inform_ac.to_dict()}')

        if page_num == 1:
            cat_wpx_data.update(wpx_data)
            cat_inform_ac_data.update(inform_ac_data)
        else:
            cat_wpx_data['content'] += wpx_data['content']
            cat_wpx_data['content_h1'] += wpx_data['content_h1']
            cat_wpx_data['content_h2'] += wpx_data['content_h2']
            cat_wpx_data['content_p'] += wpx_data['content_p']
            cat_wpx_data['content_image'] += wpx_data['content_image']
            cat_wpx_data['len_p'] += wpx_data['len_p']
            cat_wpx_data['len_img'] += wpx_data['len_img']
            cat_wpx_data['len_char'] += wpx_data['len_char']

        multi_page_urls.add(i_url)

    cat_wpx_data['url'] = url
    cat_inform_ac_data['url'] = url
    cat_wpx_data['multi_page_urls'] = sorted(multi_page_urls)

    if cat_inform_ac_data['status'] and cat_wpx_data['len_img'] < 2 and cat_wpx_data['len_char'] < 100:
        cat_inform_ac_data['quality'] = False

    db_session_update(db.session, WebpagesPartnerXpath,
                      dict(id=cat_wpx_data['id']), cat_wpx_data)
    # logger.debug('update successful')

    # inform_ac_dict = inform_ac.to_dict()
    data = json.dumps(cat_inform_ac_data)
    logger.debug(f'payload {data}')
    headers = {'Content-Type': "application/json"}

    ac_content_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)
    logger.debug(f'ac_content_status_api {ac_content_status_api}')
    # inform AC
    r = requests.put(ac_content_status_api, json=data, headers=headers)

    if r.status_code == 200:
        a_wpx.task_service.status_xpath = 'done'
        db.session.commit()
        logger.debug('inform AC successful')
    else:
        logger.error('inform AC failed')


@celery.task()
def ai_single_crawler(tid: int, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    might be a partner or non-partner
    '''
    logger.debug('run ai_single_crawler()...')

    if partner_id:
        wp = prepare_crawler(tid, partner=True, xpath=False)
        a_wp = ai_a_crawler(wp, partner_id)
    else:
        wp = prepare_crawler(tid, partner=False, xpath=False)
        a_wp = ai_a_crawler(wp)

    wp_data = a_wp.to_dict()

    if partner_id:
        db_session_update(db.session, WebpagesPartnerAi,
                          dict(id=wp_data['id']), wp_data)
    else:
        db_session_update(db.session, WebpagesNoService,
                          dict(id=wp_data['id']), wp_data)


@celery.task()
def ai_multi_crawler(tid: int, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    must be a partner
    '''
    logger.debug('run ai_multi_crawler()...')

    if partner_id:
        wp = prepare_crawler(tid, partner=True, xpath=False)
        cat_wp_data = WebpagesPartnerAi().to_dict()
        logger.debug(f'cat_wp_dataf {cat_wp_data}')

    url = wp['url']

    if domain_info['page']:
        page_query_param = domain_info['page'][0]
        logger.debug(f'page_query_param {page_query_param}')

    page_num = 0
    multi_page_urls = set()
    while page_num <= 40:
        page_num += 1
        if page_query_param == "d+":
            i_url = f'{url}/{page_num}'
        else:
            i_url = f'{url}?{page_query_param}={page_num}'

        # replace url
        wp['url'] = i_url
        a_wp = ai_a_crawler(wp, partner_id, multipaged=True)
        if not a_wp:
            break
        wp_data = a_wp.to_dict()
        logger.debug(f'wp_data from xpath_a_crawler(): {wp_data}')

        if page_num == 1:
            cat_wp_data.update(wp_data)
        else:
            cat_wp_data['content'] += wp_data['content']
            cat_wp_data['content_h1'] += wp_data['content_h1']
            cat_wp_data['content_h2'] += wp_data['content_h2']
            cat_wp_data['content_p'] += wp_data['content_p']
            cat_wp_data['content_image'] += wp_data['content_image']

        multi_page_urls.add(i_url)

    cat_wp_data['url'] = url
    cat_wp_data['multi_page_urls'] = sorted(multi_page_urls)

    db_session_update(db.session, WebpagesPartnerAi,
                      dict(id=cat_wp_data['id']), cat_wp_data)

    if partner_id:
        a_wp.task_service.status_ai = 'done'
    else:
        a_wp.task_noservice.status = 'done'
    db.session.commit()
