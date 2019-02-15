from breakcontent.factory import create_celery_app
from breakcontent.utils import Secret, InformAC, DomainSetting, db_session_query, db_session_update, xpath_a_crawler, parse_domain_info, get_domain_info, retry_request

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
import datetime
from datetime import timedelta

celery = create_celery_app()
logger = get_task_logger('default')


ac_content_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)
ac_content_multipage_api = os.environ.get('AC_CONTENT_MULTIPAGE_API', None)


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
    task_required = [
        'url_hash',
        'url',
        'request_id',
        'partner_id',
    ]
    task_data = {k: v for (k, v) in data.items() if k in task_required}

    q = {
        'url_hash': data['url_hash']
    }
    udata = {
        'status': 'pending',
        'doing_time': None,
        'done_time': None
    }
    data.update(udata)
    tm = TaskMain(**data)
    tm.upsert(q)

    # tm = tm.select(q)
    logger.debug(f'tm.id {tm.id}')
    if data.get('partner_id', None):
        udata = {
            'task_main_id': tm.id,  # for insert use
            'status_ai': 'pending',
            'status_xpath': 'pending',
            # 'retry_ai': 0,
            # 'retry_xpath': 0
        }
        task_data.update(udata)
        ts = TaskService(**task_data)
        ts.upsert(q)  # for insert
        # logger.debug(f'tm.task_service {tm.task_service}')
        # logger.debug(f'tm {tm}')
    else:
        udata = {
            'task_main_id': tm.id,  # for insert use
            'status': 'pending',
            # 'retry': 0,
        }
        task_data.update(udata)
        tns = TaskNoService(**task_data)
        tns.upsert(q)

    logger.debug('upsert successful')


@celery.task()
def create_tasks(priority):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks()...")
    # with db.session.no_autoflush:

    q = dict(priority=priority, status='pending')
    tml = TaskMain().select(q, order_by=TaskMain._mtime, asc=True, limit=10)

    logger.debug(f'len {len(tml)}')
    if len(tml) == 0:
        logger.debug(f'no result, quit')
        return

    for tm in tml:
        logger.debug(f'update {tm}...')
        q = dict(url_hash=tm.url_hash)
        data = {
            'status': 'doing',
            'doing_time': datetime.datetime.utcnow()
        }
        tm.upsert(q, data)

        if tm.task_service:
            logger.debug(f'update {tm.task_service}...')
            udata = {
                'url_hash': tm.url_hash,
                'status_ai': 'doing',
                'status_xpath': 'doing',
            }
            q = {'id': tm.task_service.id}
            tm.task_service.upsert(q, udata)
            prepare_task.delay(tm.task_service.to_dict())

        if tm.task_noservice:
            logger.debug(f'update {tm.task_noservice}...')
            udata = {
                'url_hash': tm.url_hash,
                'status': 'doing'
            }
            q = {'id': tm.task_noservice.id}
            tm.task_noservice.upsert(q, udata)
            prepare_task.delay(tm.task_noservice.to_dict())

    logger.debug('done sending a batch of tasks to broker')


@celery.task()
def prepare_task(task: dict):
    '''
    fetch settings from partner system through api

    argument:
    task: could be a TaskService or TaskNoService dict

    '''
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
        # return # Lance debug
        if domain_info:
            logger.debug(f'domain_info {domain_info}')
            if domain_info.get('page', None) and domain_info['page'] != '':
                # preparing for multipage crawler
                page_query_param = domain_info['page'][0]
                # tsf = db_session_query(TaskService, dict(id=task['id']))
                q = dict(id=task['id'])
                tsf = TaskService().select(q)
                udata = {
                    'is_multipage': True,
                    'page_query_param': page_query_param
                }
                # tsf.is_multipage = True
                # tsf.page_query_param = page_query_param
                tsf.upsert(q, udata)
                # db.session.commit()
                # logger.debug('update successful')

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

                if mp_url != url and ac_content_multipage_api:

                    headers = {'Content-Type': "application/json"}
                    data = {
                        'url': url,
                        'url_hash': task['url_hash'],
                        'multipage': mp_url
                    }

                    resp_data = retry_request(
                        'post', ac_content_multipage_api, data, headers)

                    if resp_data:
                        logger.debug(f'resp_data {resp_data}')
                        logger.debug('inform AC successful')
                        # tmf = db_session_query(
                        # TaskMain, dict(id=tsf.task_main_id))
                        q = dict(id=tsf.task_main_id)
                        tmf = TaskMain().select(q)
                        tmf.delete()
                        # db.session.delete(tmf)
                        # db.session.commit()
                    else:
                        logger.error(f'inform AC failed')

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
        # to do
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
    wpx_dict = prepare_crawler(tid, partner=True, xpath=True)
    # logger.debug(f'wpx {wpx}')

    a_wpx, inform_ac = xpath_a_crawler(
        wpx_dict, partner_id, domain, domain_info)
    logger.debug(f'a_wpx from xpath_a_crawler(): {a_wpx}')
    logger.debug(f'inform_ac {inform_ac.to_dict()}')

    wpx_data = a_wpx.to_dict()
    q = dict(id=a_wpx.id)
    a_wpx.update(q, wpx_data)
    logger.debug('update successful, crawler completed')

    inform_ac.check_content_hash(a_wpx)
    inform_ac_data = inform_ac.to_dict()
    logger.debug(f'inform_ac_data {inform_ac_data}')

    headers = {'Content-Type': "application/json"}

    resp_data = retry_request(
        'put', ac_content_status_api, inform_ac_data, headers)

    if resp_data:
        logger.debug(f'resp_data {resp_data}')
        a_wpx.task_service.status_xpath = 'done'
        a_wpx.task_service.task_main.status = 'done'
        a_wpx.task_service.task_main.done_time = datetime.datetime.utcnow()
        db.session.commit()
        logger.debug('inform AC successful')
    else:
        logger.error(f'inform AC failed, retry {retry}')
        a_wpx.task_service.status_xpath = 'failed'
        a_wpx.task_service.task_main.status = 'failed'
        db.session.commit()


@celery.task()
def xpath_multi_crawler(tid: int, partner_id: str, domain: str, domain_info: dict):
    '''
    partner only

    loop xpath_a_crawler by page number

    ** remember to update the url & url_hash in CC and AC
    '''
    logger.debug(f'start to crawl multipaged url on tid {tid}')

    wpx_dict = prepare_crawler(tid, partner=True, xpath=True)
    url = wpx_dict['url']
    page_query_param = domain_info['page'][0]

    # logger.debug(f'url {url}')
    logger.debug(f'page_query_param {page_query_param}')

    # return
    page_num = 0
    cat_wpx = WebpagesPartnerXpath()
    cat_wpx_data = cat_wpx.to_dict()
    # object
    cat_inform_ac = InformAC()
    # dict
    cat_inform_ac_data = cat_inform_ac.to_dict()
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
        wpx_dict['url'] = i_url
        a_wpx, inform_ac = xpath_a_crawler(
            wpx_dict, partner_id, domain, domain_info, multipaged=True)

        if not inform_ac.status:
            logger.debug(f'failed to crawl {i_url}')
            # cat_inform_ac.status = False
            # ['status'] = False
            break

        if not inform_ac.zi_sync:
            logger.critical(
                f'{i_url} does not match the sync criteria (regex/author/category/delayday)')
            # don't break, keep crawling

        # wpx_data = a_wpx.to_dict()

        # inform_ac_data = inform_ac.to_dict()

        logger.debug(f'a_wpx from xpath_a_crawler(): {a_wpx.to_dict()}')
        logger.debug(
            f'inform_ac from xpath_a_crawler(): {inform_ac.to_dict()}')

        if page_num == 1:

            cat_wpx = a_wpx

            # cat_wpx.content = cat_wpx.content if cat_wpx.content else ''
            # cat_wpx.content_h1 = cat_wpx.content_h1 if cat_wpx.content_h1 else ''
            # cat_wpx.content_h2 = cat_wpx.content_h2 if cat_wpx.content_h2 else ''
            # cat_wpx.content_p = cat_wpx.content_p if cat_wpx.content_p else ''
            # cat_wpx.content_image = cat_wpx.content_image if cat_wpx.content_image else ''
            # cat_wpx.len_p = cat_wpx.len_p if cat_wpx.len_p else 0
            # cat_wpx.len_img = cat_wpx.len_img if cat_wpx.len_img else 0
            # cat_wpx.len_char = cat_wpx.len_char if cat_wpx.len_char else 0

            # cat_wpx_data.update(wpx_data)
            cat_inform_ac = inform_ac
            # cat_inform_ac_data.update(inform_ac_data)
            if not inform_ac.status:
                cat_inform_ac.status = False
        else:
            cat_wpx.content += a_wpx.content
            cat_wpx.content_h1 += a_wpx.content_h1
            cat_wpx.content_h2 += a_wpx.content_h2
            cat_wpx.content_p += a_wpx.content_p
            cat_wpx.content_image += a_wpx.content_image
            cat_wpx.len_p += a_wpx.len_p
            cat_wpx.len_img += a_wpx.len_img
            cat_wpx.len_char += a_wpx.len_char

            # cat_wpx_data['content'] += wpx_data['content']
            # cat_wpx_data['content_h1'] += wpx_data['content_h1']
            # cat_wpx_data['content_h2'] += wpx_data['content_h2']
            # cat_wpx_data['content_p'] += wpx_data['content_p']
            # cat_wpx_data['content_image'] += wpx_data['content_image']
            # cat_wpx_data['len_p'] += wpx_data['len_p']
            # cat_wpx_data['len_img'] += wpx_data['len_img']
            # cat_wpx_data['len_char'] += wpx_data['len_char']

        multi_page_urls.add(i_url)

    # cat_inform_ac_data['url'] = url
    cat_inform_ac.url = url
    cat_wpx.url = url
    cat_wpx.multi_page_urls = sorted(multi_page_urls)

    # cat_wpx_data['url'] = url
    # cat_wpx_data['multi_page_urls'] = sorted(multi_page_urls)

    if cat_inform_ac.status and cat_wpx.len_img < 2 and cat_wpx.len_char < 100:
        # cat_inform_ac_data['quality'] = False
        cat_inform_ac.quality = False

    db_session_update(WebpagesPartnerXpath,
                      dict(id=cat_wpx.id), cat_wpx.to_dict())
    # logger.debug('update successful')

    # lance to do
    cat_inform_ac.check_content_hash(cat_wpx)
    # inform_ac_dict = inform_ac.to_dict()
    # data = json.dumps(cat_inform_ac_data)
    data = cat_inform_ac.to_dict()
    logger.debug(f'payload {data}')
    headers = {'Content-Type': "application/json"}

    # r = requests.put(ac_content_status_api, json=data, headers=headers)

    resp_data = retry_request('put', ac_content_status_api, data, headers)

    # if r.status_code == 200:
    if resp_data:
        cat_wpx.task_service.status_xpath = 'done'
        cat_wpx.task_service.task_main.done_time = datetime.datetime.utcnow()
        db.session.commit()
        logger.debug('inform AC successful')
    else:
        cat_wpx.task_service.status_xpath = 'failed'
        logger.error('inform AC failed')


@celery.task()
def ai_single_crawler(tid: int, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    might be a partner or non-partner
    '''
    logger.debug('run ai_single_crawler()...')

    if partner_id:
        wp_dict = prepare_crawler(tid, partner=True, xpath=False)
        a_wp = ai_a_crawler(wp_dict, partner_id)
    else:
        wp_dict = prepare_crawler(tid, partner=False, xpath=False)
        a_wp = ai_a_crawler(wp_dict)

    wp_data = a_wp.to_dict()

    if partner_id:
        db_session_update(WebpagesPartnerAi,
                          dict(id=wp_data['id']), wp_data)
        a_wp.task_service.status_ai = 'done'
        db.session.commit()
        # do not notify AC here
    else:
        # must inform AC
        db_session_update(WebpagesNoService,
                          dict(id=wp_data['id']), wp_data)
        a_wp.task_noservice.status = 'done'
        db.session.commit()

        # notify AC
        iac = InformAC()
        iac_data = iac.to_dict()
        udata = {
            'url_hash': wp_data['url_hash'],
            'url': wp_data['url'],
            'request_id': a_wp.task_noservice.task_main.request_id,
            'status': True
        }
        iac_data.update(udata)

        resp_data = retry_request(
            'put', ac_content_status_api, iac_data, headers)

        if resp_data:
            a_wp.task_noservice.task_main.done_time = datetime.datetime.utcnow()
            a_wp.task_noservice.task_main.status = 'done'
            db.session.commit()
            logger.debug('inform AC successful')
        else:
            a_wp.task_noservice.task_main.status = 'failed'
            logger.error('inform AC failed')


@celery.task()
def ai_multi_crawler(tid: int, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    must be a partner

    no need to inform AC
    '''
    logger.debug('run ai_multi_crawler()...')

    if partner_id:
        wp_dict = prepare_crawler(tid, partner=True, xpath=False)
        cat_wp_data = WebpagesPartnerAi().to_dict()
        logger.debug(f'cat_wp_dataf {cat_wp_data}')

    url = wp_dict['url']

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
        wp_dict['url'] = i_url
        a_wp = ai_a_crawler(wp_dict, partner_id, multipaged=True)
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

    db_session_update(WebpagesPartnerAi,
                      dict(id=cat_wp_data['id']), cat_wp_data)

    if partner_id:
        a_wp.task_service.status_ai = 'done'
    else:
        a_wp.task_noservice.status = 'done'
    db.session.commit()

    # notify AC, not necessary
