from breakcontent.factory import create_celery_app
from breakcontent.utils import Secret, InformAC, DomainSetting, xpath_a_crawler, parse_domain_info, get_domain_info, retry_request


from breakcontent.utils import mercuryContent, prepare_crawler, ai_a_crawler

import re
import os
import json
import requests
import time
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
    '''
    for dev use
    '''
    logger.debug(
        f'run delete_main_task(), down stream records will also be deleted...')
    tmd = TaskMain.query.filter_by(**data).first()
    db.session.delete(tmd)
    db.session.commit()

    logger.debug('done delete_main_task()')


@celery.task(bind=True)
def upsert_main_task(task, data: dict):
    '''
    upsert doc in TaskMain, TaskService and TaskNoService
    '''

    logger.debug(
        f"url_hash {data['url_hash']}, task.request.id {task.request.id}")

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
    tm = TaskMain()
    tm.upsert(q, data)

    # tm = tm.select(q)
    logger.debug(f'tm.id {tm.id}')
    if data.get('partner_id', None):
        udata = {
            'task_main_id': tm.id,  # for insert use
            'status_ai': 'pending',
            'status_xpath': 'pending',
            # 'retry_ai': 0,
            'retry_xpath': 0
        }
        task_data.update(udata)
        ts = TaskService()
        ts.upsert(q, task_data)  # for insert
    else:
        udata = {
            'task_main_id': tm.id,  # for insert use
            'status': 'pending',
            # 'retry': 0,
        }
        task_data.update(udata)
        tns = TaskNoService()
        tns.upsert(q, task_data)

    logger.debug('upsert successful')


@celery.task()
def create_tasks(priority):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks() on priority {priority}")
    # with db.session.no_autoflush:

    q = dict(priority=priority, status='pending')
    tml = TaskMain().select(q, order_by=TaskMain._mtime, asc=True, limit=500)

    logger.debug(f'priority {priority}, len {len(tml)}')
    if len(tml) == 0:
        logger.debug(f'no result, quit')
        return

    for tm in tml:
        url_hash = tm.url_hash
        logger.debug(f'update {tm}...')
        q = dict(url_hash=url_hash)
        data = {
            'status': 'doing',
            'doing_time': datetime.datetime.utcnow()
        }
        tm.update(q, data)

        if tm.task_service:
            logger.debug(f'update {tm.task_service}...')
            udata = {
                'url_hash': url_hash,
                'status_ai': 'doing',
                'status_xpath': 'doing',
            }
            q = {'id': tm.task_service.id}
            tm.task_service.upsert(q, udata)
            prepare_task.delay(tm.task_service.to_dict())

        if tm.task_noservice:
            logger.debug(f'update {tm.task_noservice}...')
            udata = {
                'url_hash': url_hash,
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
    # logger.debug(f'task {task}')
    url_hash = task['url_hash']
    logger.debug(f'url_hash {url_hash}, run prepare_task()...')
    url = task['url']
    o = urlparse(url)
    domain = o.netloc
    q = dict(url_hash=task['url_hash'])
    data = dict(domain=domain)
    tm = TaskMain()
    tm.update(q, data)

    if task.get('partner_id', None):

        partner_id = task['partner_id']
        logger.debug(
            f'url_hash {url_hash}, domain {domain}, partner_id {partner_id}')

        domain_info = get_domain_info(domain, partner_id)
        q = dict(id=task['id'])
        ts = TaskService().select(q)
        ts.upsert(q, data)

        if domain_info:
            logger.debug(f'url_hash {url_hash}, domain_info {domain_info}')
            if domain_info.get('page', None) and domain_info['page'] != '':
                # preparing for multipage crawler
                page_query_param = domain_info['page'][0]

                udata = {
                    'is_multipage': True,
                    'page_query_param': page_query_param,
                    # 'domain': domain
                }
                ts.upsert(q, udata)

                mp_url = url
                if page_query_param:
                    if page_query_param == "d+":
                        # mp_url.replace(r'\/\d+$', '')
                        mp_url = re.sub(r'\/\d+$', '', url)
                    else:
                        # mp_url.replace(r'\?(page|p)=\d+', '')
                        mp_url = re.sub(r'\?(page|p)=\d+', '', url)
                logger.debug(
                    f'url_hash {url_hash}, url {url}, mp_url {mp_url}')

                if mp_url != url and ac_content_multipage_api:
                    headers = {'Content-Type': "application/json"}
                    data = {
                        'url': url,
                        'url_hash': task['url_hash'],
                        'multipage': mp_url,
                        'domain': domain
                    }
                    resp_data = retry_request(
                        'post', ac_content_multipage_api, data, headers)

                    if resp_data:
                        logger.debug(f'resp_data {resp_data}')
                        q = dict(id=ts.task_main_id)
                        tmf = TaskMain().select(q)
                        tmf.delete()
                        logger.debug(
                            f'url_hash {url_hash}, inform AC successful')
                    else:
                        logger.error(f'url_hash {url_hash}, inform AC failed')

                else:
                    logger.info('mp_url = url')
                    xpath_multi_crawler.delay(
                        task['id'], partner_id, domain, domain_info)
                    if celery.conf['PARTNER_AI_CRAWLER']:
                        ai_multi_crawler.delay(
                            task['id'], partner_id, domain, domain_info)

            else:
                # preparing for singlepage crawler
                xpath_single_crawler.delay(
                    task['id'], partner_id, domain, domain_info)
                if celery.conf['PARTNER_AI_CRAWLER']:
                    ai_single_crawler.delay(
                        task['id'], partner_id, domain, domain_info)
                logger.debug(f'url_hash {url_hash} task sent')
        else:
            logger.error(
                f'there is no partner settings for partner_id {partner_id} domain {domain}')

            iac = InformAC()
            iac.url_hash = url_hash
            iac.url = url
            iac.request_id = task['request_id']
            iac.zi_sync = False
            iac.status = False
            data = iac.to_dict()
            # need more code
            headers = {'Content-Type': "application/json"}
            resp_data = retry_request(
                'put', ac_content_status_api, data, headers)

            if resp_data:
                logger.debug(f'resp_data {resp_data}')
                ts.status_xpath = 'done'
                ts.task_main.status = 'done'
                ts.task_main.done_time = datetime.datetime.utcnow()
                db.session.commit()
                logger.debug(f'url_hash {url_hash}, inform AC successful')
            else:
                ts.status_xpath = 'failed'
                ts.task_main.status = 'failed'
                db.session.commit()
                logger.error(f'url_hash {url_hash}, inform AC failed')

            # task {'id': 1398, 'task_main_id': 1398, 'url_hash': '5cd6548adc4c7d13c896b1670eef51772c22092d', 'url': 'https://healthnice.org/8adb355df5914ecfeefdaf046cf5cb4793745bd7/', 'partner_id': 'YUZ7T18', '
            # request_id': 'ee7fbaa2-6433-4232-8666-8b96923f8447', 'is_multipage': False, 'page_query_param': None, 'secret': False, 'status_xpath': 'doing', 'status_ai': 'doing'}

    else:

        q = dict(id=task['id'])
        tns = TaskNoService().select(q)
        tns.upsert(q, data)

        # not partner goes here
        ai_single_crawler.delay(
            task['id'])

        logger.debug(f'url_hash {url_hash}, sent task to ai_single_crawler()')


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
    url_hash = wpx_dict['url_hash']
    # logger.debug(f'wpx {wpx}')

    a_wpx, inform_ac = xpath_a_crawler(
        wpx_dict, partner_id, domain, domain_info)
    logger.debug(f'url_hash {url_hash}, a_wpx from xpath_a_crawler(): {a_wpx}')
    # logger.debug(f'inform_ac {inform_ac.to_dict()}')

    # check crawler status code, if 406/426 retry 5 time at most
    # retry stretagy: seny task into broker again
    retry = a_wpx.task_service.retry_xpath
    status_code = a_wpx.task_service.status_code
    candidate = [406, 426]
    if retry < 5 and (status_code in candidate or status_code != 200):
        logger.warning(
            f'url_hash {url_hash}, status_code {status_code}, retry {retry} times')
        a_wpx.task_service.retry_xpath += 1
        time.sleep(0.5)
        xpath_single_crawler.delay(tid, partner_id, domain, domain_info)
        db.session.commit()
        return
    elif retry >= 5:
        logger.critical(
            f'url_hash {url_hash}, status_code {status_code}, stop after retry {retry} times!')
        a_wpx.task_service.status_xpath = 'failed'
        a_wpx.task_service.task_main.status = 'failed'
        db.session.commit()

    # inform AC
    wpx_data = a_wpx.to_dict()
    q = dict(id=a_wpx.id)
    a_wpx.update(q, wpx_data)
    logger.debug(f'url_hash {url_hash}, update successful, crawler completed')

    inform_ac.check_content_hash(a_wpx)
    inform_ac_data = inform_ac.to_dict()
    logger.debug(f'url_hash {url_hash}, inform_ac_data {inform_ac_data}')

    a_wpx.task_service.status_xpath = 'ready'
    db.session.commit()
    logger.debug(
        f'url_hash {url_hash} status {a_wpx.task_service.status_xpath}')

    headers = {'Content-Type': "application/json"}
    resp_data = retry_request(
        'put', ac_content_status_api, inform_ac_data, headers)

    if resp_data:
        if cat_inform_ac.old_url_hash:
            q = {
                'url_hash': cat_inform_ac.old_url_hash,
                'content_hash': cat_wpx.content_hash
            }
            u2c = UrlToContent().select(q)
            u2c.replaced = True
            db.session.commit()
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in UrlToContent() has been modified')

            q = {'url_hash': cat_inform_ac.old_url_hash}
            tm = TaskMain().select(q)
            tm.delete()
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in TaskMain() has been deleted')

        logger.debug(f'resp_data {resp_data}')
        a_wpx.task_service.status_xpath = 'done'
        a_wpx.task_service.task_main.status = 'done'
        a_wpx.task_service.task_main.done_time = datetime.datetime.utcnow()
        db.session.commit()
        logger.debug(f'url_hash {url_hash}, inform AC successful')

    else:
        logger.error(f'url_hash {url_hash}, inform AC failed')
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
    url_hash = wpx_dict['url_hash']
    page_query_param = domain_info['page'][0]

    # logger.debug(f'url {url}')
    logger.debug(f'page_query_param {page_query_param}')

    page_num = 0
    cat_wpx = WebpagesPartnerXpath()
    cat_wpx_data = cat_wpx.to_dict()
    # object
    cat_inform_ac = InformAC()
    # dict
    cat_inform_ac_data = cat_inform_ac.to_dict()
    logger.debug(f'cat_wpx_data {cat_wpx_data}')
    logger.debug(f'cat_inform_ac_dict {cat_inform_ac_data}')

    multi_page_urls = set()
    while page_num <= 40:
        page_num += 1
        if page_query_param == "d+":
            i_url = f'{url}/{page_num}'
        else:
            i_url = f'{url}?{page_query_param}={page_num}'

        wpx_dict['url'] = i_url
        a_wpx, inform_ac = xpath_a_crawler(
            wpx_dict, partner_id, domain, domain_info, multipaged=True)

        if not inform_ac.status:
            logger.debug(f'failed to crawl {i_url}')
            break

        if not inform_ac.zi_sync:
            logger.critical(
                f'{i_url} does not match the sync criteria (regex/author/category/delayday)')
            # don't break, keep crawling

        logger.debug(f'a_wpx from xpath_a_crawler(): {a_wpx.to_dict()}')
        logger.debug(
            f'inform_ac from xpath_a_crawler(): {inform_ac.to_dict()}')

        if page_num == 1:
            cat_wpx = a_wpx
            cat_inform_ac = inform_ac

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

        multi_page_urls.add(i_url)

    cat_inform_ac.url = url
    cat_wpx.url = url
    cat_wpx.multi_page_urls = sorted(multi_page_urls)

    if cat_inform_ac.status and cat_wpx.len_img < 2 and cat_wpx.len_char < 100:
        cat_inform_ac.quality = False

    cat_inform_ac.check_content_hash(cat_wpx)
    data = cat_inform_ac.to_dict()
    logger.debug(f'url_hash {url_hash}, payload {data}')
    headers = {'Content-Type': "application/json"}
    resp_data = retry_request('put', ac_content_status_api, data, headers)

    if resp_data:
        if cat_inform_ac.old_url_hash:
            q = {
                'url_hash': cat_inform_ac.old_url_hash,
                'content_hash': cat_wpx.content_hash
            }
            u2c = UrlToContent().select(q)
            u2c.replaced = True
            db.session.commit()
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in UrlToContent() has been modified')

            q = {'url_hash': cat_inform_ac.old_url_hash}
            tm = TaskMain().select(q)
            tm.delete()
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in TaskMain() has been deleted')

        cat_wpx.task_service.status_xpath = 'done'
        cat_wpx.task_service.task_main.done_time = datetime.datetime.utcnow()
        db.session.commit()

        logger.debug(f'url_hash {url_hash}, inform AC successful')
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

        q = dict(url_hash=wp_dict['url_hash'])

        wpa = WebpagesPartnerAi()
        ts = TaskService()

        if not a_wp:
            data = dict(status_ai='failed')
            ts.update(q, data)
            logger.debug('ai_single_crawler() failed')
            return

        wpa.update(q, a_wp.to_dict())
        data = dict(status_ai='done')
        ts.update(q, data)
        logger.debug('ai_single_crawler() successful')
        # do not notify AC here
    else:
        # must inform AC
        wp_dict = prepare_crawler(tid, partner=False, xpath=False)
        a_wp = ai_a_crawler(wp_dict)

        q = dict(url_hash=wp_dict['url_hash'])

        wpns = WebpagesNoService()
        tns = TaskNoService()
        tm = TaskMain()

        iac = InformAC()
        iac_data = iac.to_dict()

        if a_wp:
            udata = {
                'url_hash': wp_dict['url_hash'],
                'url': wp_dict['url'],
                'request_id': a_wp.task_noservice.request_id,
                # 'status': True # default value
            }
            iac_data.update(udata)
            wpns.update(q, a_wp.to_dict())
        else:
            # no need to update if a_wp == None
            iac_data['status'] = False

        # inform AC
        headers = {'Content-Type': "application/json"}
        resp_data = retry_request(
            'put', ac_content_status_api, iac_data, headers)

        if resp_data:
            data = dict(status='done')
            tns.update(q, data)

            data = {
                'done_time': datetime.datetime.utcnow(),
                'status': 'done'
            }
            tm.update(q, data)

            logger.debug('inform AC successful')
        else:
            data = dict(status='failed')
            tm.update(q, data)
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
        # logger.debug(f'cat_wp_data {cat_wp_data}')

    url = wp_dict['url']
    url_hash = wp_dict['url_hash']
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
        logger.debug(f'a_wp {a_wp}')
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
    cat_wp_data['url_hash'] = url_hash
    cat_wp_data['multi_page_urls'] = sorted(multi_page_urls)

    logger.debug(f'cat_wp_data {cat_wp_data}')
    q = dict(url_hash=url_hash)

    if partner_id:
        wpa = WebpagesPartnerAi()
        wpa.update(q, cat_wp_data)
        # logger.debug(f'wpa {wpa}')
        data = dict(status_ai='done')
        ts = TaskService()
        ts.update(q, data)
    else:
        wpns = WebpagesNoService()
        wpns.update(q, cat_wp_data)
        data = dict(status='done')
        tns = TaskNoService()
        tns.update(q, data)
