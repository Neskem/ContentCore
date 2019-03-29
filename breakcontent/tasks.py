from breakcontent.factory import create_celery_app
from breakcontent.utils import Secret, InformAC, DomainSetting, xpath_a_crawler, parse_domain_info, get_domain_info, retry_request, request_api


from breakcontent.utils import mercuryContent, prepare_crawler, ai_a_crawler

import re
import os
import json
import requests
import time
from flask import current_app
from celery.utils.log import get_task_logger

from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
from sqlalchemy.orm import load_only
from sqlalchemy import or_

from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
from breakcontent import mylogging
from urllib.parse import urlencode, quote_plus, unquote, quote, unquote_plus, parse_qs
from urllib.parse import urlparse, urljoin
# import datetime
from datetime import timedelta, datetime
import csv

celery = create_celery_app()
logger = get_task_logger('default')


ac_content_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)
ac_content_multipage_api = os.environ.get('AC_CONTENT_MULTIPAGE_API', None)
ac_content_async = os.environ.get('AC_CONTENT_ASYNC', None)


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
        'domain'
    ]
    task_data = {k: v for (k, v) in data.items() if k in task_required}

    url = data['url']
    if data.get('domain', None):
        domain = data['domain']
    else:
        o = urlparse(url)
        domain = o.netloc
        data['domain'] = domain

    q = {
        'url_hash': data['url_hash']
    }
    udata = {
        'status': 'pending',
        'doing_time': None,
        'done_time': None,
        'zi_sync': None,
        'inform_ac_status': None
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
            'retry_xpath': 0,
            'domain': domain
        }
        task_data.update(udata)
        ts = TaskService()
        ts.upsert(q, task_data)  # for insert
    else:
        udata = {
            'task_main_id': tm.id,  # for insert use
            'status': 'pending',
            # 'retry': 0,
            'domain': domain
        }
        if task_data.get('partner_id', None):
            task_data.pop('partner_id')
        task_data.update(udata)
        tns = TaskNoService()
        tns.upsert(q, task_data)

    logger.debug('upsert successful')


@celery.task()
def create_tasks(priority: str, limit: int=4000, asc: bool=True):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks() on priority {priority}")
    # with db.session.no_autoflush:

    q = dict(priority=priority, status='pending')
    tml = TaskMain().select(q, order_by=TaskMain._mtime, asc=asc,
                            limit=limit)

    logger.debug(f'priority {priority}, len {len(tml)}')
    if len(tml) == 0:
        logger.debug(f'no result, quit')
        return

    for tm in tml:
        request_id = tm.request_id
        url_hash = tm.url_hash
        logger.debug(f'sent task for url_hash {url_hash}')

        if tm.task_service and tm.partner_id:
            logger.debug(
                f'sent task for tm.task_service {tm.task_service} with priority {priority}')
            data = tm.task_service.to_dict()
            data['priority'] = int(priority)
            data['request_id'] = request_id
            if int(priority) == 1:
                logger.debug(
                    f'url_hash {url_hash} sent to high_speed_p1.delay()')
                high_speed_p1.delay(data)
                # return
            else:
                prepare_task.delay(data)

        elif tm.task_noservice and not tm.partner_id:
            logger.debug(
                f'sent task for tm.task_noservice {tm.task_noservice}')
            data = tm.task_noservice.to_dict()
            data['priority'] = int(priority)
            data['request_id'] = request_id
            prepare_task.delay(data)

        else:
            # this might happen if you use sql to change doing back to pending
            # plz use reset_doing_tasks() instead
            bypass_crawler.delay(url_hash)

    logger.debug(f'done sending {len(tml)} tasks to broker')


@celery.task()
def high_speed_p1(task: dict):
    '''
    1 task, 1 queue, 1 worker exclusively for priority=1 tasks

    that's it, this function will do all the rest
    '''
    logger.debug(f'task {task} in high_speed_p1()')
    prepare_task(task)


@celery.task()
def prepare_task(task: dict):
    '''
    fetch settings from partner system through api

    argument:
    task: could be a TaskService or TaskNoService dict

    '''
    # logger.debug(f'task {task}')
    logger.debug(f'task {task} in prepare_task()')
    priority = task['priority'] if task.get('priority', None) else None
    url_hash = task['url_hash']
    url = task['url']
    request_id = task['request_id']
    logger.debug(
        f'url_hash {url_hash}, run prepare_task() with priority {priority}')
    url = task['url']
    domain = task['domain']

    q = dict(url_hash=task['url_hash'])
    data = {
        'status': 'preparing',
        'doing_time': datetime.utcnow(),
        'domain': domain
    }
    tm = TaskMain()
    tm.update(q, data)
    if task.get('partner_id', None):

        partner_id = task['partner_id']
        logger.debug(
            f'url_hash {url_hash}, domain {domain}, partner_id {partner_id}')

        domain_info = get_domain_info(domain, partner_id)
        q = dict(id=task['id'])
        ts = TaskService()

        if domain_info:
            if domain_info.get('page', None) and domain_info['page'] != '':

                if not celery.conf['RUN_XPATH_MULTI_CRAWLER']:
                    tm = TaskMain()
                    tm.update(q, dict(status='done'))
                    return
                # preparing for multipage crawler
                page_query_param = domain_info['page'][0]

                udata = {
                    'is_multipage': True,
                    'page_query_param': page_query_param,
                    'status_ai': 'doing',
                    'status_xpath': 'preparing',
                    'domain': domain
                }
                ts.update(q, udata)
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
                    resp_data = request_api(
                        ac_content_multipage_api, 'post', data)

                    if resp_data:
                        logger.debug(f'resp_data {resp_data}')
                        q = dict(url_hash=url_hash)
                        tm = TaskMain()
                        doc = tm.select(q)
                        tm.delete(doc)
                        logger.debug(
                            f'url_hash {url_hash}, inform AC successful')
                    else:
                        logger.error(f'url_hash {url_hash}, inform AC failed')

                else:
                    logger.info('mp_url = url')
                    logger.debug(
                        f"task['id'] {task['id']}, partner_id {partner_id}, domain {domain}, domain_info {domain_info}")
                    if priority and int(priority) == 1:
                        xpath_multi_crawler(
                            url_hash, url, partner_id, domain, domain_info)
                    else:
                        xpath_multi_crawler.delay(
                            url_hash, url, partner_id, domain, domain_info)
                    if celery.conf['PARTNER_AI_CRAWLER']:
                        ai_multi_crawler.delay(
                            url_hash, partner_id, domain, domain_info)
                    else:
                        pass

            else:
                # preparing for singlepage crawler
                udata = {
                    'status_ai': 'preparing',
                    'status_xpath': 'preparing',
                    'domain': domain
                }
                ts.update(q, udata)

                if priority and int(priority) == 1:
                    logger.debug(
                        f'url_hash {url_hash} run xpath_single_crawler() in high_speed_p1 task func')
                    xpath_single_crawler(
                        url_hash, url, partner_id, domain, domain_info)
                else:
                    logger.debug(
                        f'url_hash {url_hash} sent task to xpath_single_crawler.delay()')
                    xpath_single_crawler.delay(
                        url_hash, url, partner_id, domain, domain_info)
                logger.debug(
                    f"celery.conf['PARTNER_AI_CRAWLER'] {celery.conf['PARTNER_AI_CRAWLER']}")
                if celery.conf['PARTNER_AI_CRAWLER']:
                    # even p1's aicrawler task will be sent to delay
                    ai_single_crawler.delay(
                        url_hash, url, partner_id, domain, domain_info)
                    logger.debug(f'url_hash {url_hash} task sent')
                else:
                    pass

        else:
            logger.error(
                f'url_hash {url_hash}, no domain_info!')
            bypass_crawler.delay(url_hash)

    else:
        # not partner goes here
        q = dict(id=task['id'])
        data = {
            'status': 'doing',
            'domain': domain
        }
        tns = TaskNoService()
        tns.upsert(q, data)

        if celery.conf['MERCURY_TOKEN']:
            ai_single_crawler.delay(url_hash, url)
            logger.debug(
                f'url_hash {url_hash}, sent task to ai_single_crawler()')
        else:
            logger.debug(
                f'url_hash {url_hash}, MERCURY_TOKEN env variable not set')
            bypass_crawler.delay(url_hash)


@celery.task()
def xpath_single_crawler(url_hash: str, url: str, partner_id: str, domain: str, domain_info: dict):
    '''
    <purpose>
    use the domain config from Partner System to crawl through the entire page, then inform AC with request

    <notice>
    partner only

    <arguments>
    url_hash,
    partner_id,
    domain,
    domain_info,

    <return>
    '''
    logger.debug(f'start to crawl single-paged url on url_hash {url_hash}')

    prepare_crawler(url_hash, partner=True, xpath=True)

    q = dict(url_hash=url_hash)
    tm = TaskMain().select(q)
    ts = TaskService().select(q)
    priority = tm.priority

    try:
        a_wpx, inform_ac = xpath_a_crawler(
            url_hash, url, partner_id, domain, domain_info)
    except requests.exceptions.ReadTimeout as e:
        logger.error(
            f'url_hash {url_hash} site task too long to response, quit waiting!')
        logger.error(e)
        bypass_crawler.delay(url_hash)
        return
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        bypass_crawler.delay(url_hash)
        return

    logger.debug(f'url_hash {url_hash}, a_wpx from xpath_a_crawler(): {a_wpx}')

    if inform_ac.skip_crawler:
        logger.debug(
            f'url_hash {url_hash}, inform_ac.skip_crawler {inform_ac.skip_crawler} no need to update WebpagesPartnerXpath() table')
    else:

        # check crawler status code, if 406/426 retry 5 time at most
        # retry stretagy: seny task into broker again
        retry = ts.retry_xpath
        status_code = ts.status_code
        candidate = [406, 426]
        retry_limit = 2
        if retry < retry_limit and (status_code in candidate or status_code != 200):
            logger.warning(
                f'url_hash {url_hash}, status_code {status_code}, retry {retry} times')
            retry += 1
            ts.update(q, dict(retry_xpath=retry))

            time.sleep(0.5)
            if int(priority) == 1:
                logger.debug(
                    f'url_hash {url_hash} run xpath_single_crawler() in high_speed_p1 task func')
                xpath_single_crawler(
                    url_hash, url, partner_id, domain, domain_info)
            else:
                # xpath_single_crawler.delay(
                    # url_hash, partner_id, domain, domain_info)
                xpath_single_crawler(
                    url_hash, url, partner_id, domain, domain_info)
            return  # exit this func
        elif retry >= retry_limit:
            logger.critical(
                f'url_hash {url_hash}, status_code {status_code}, stop after retry {retry} times!')
            ts.update(q, dict(status_xpath='failed'))
            tm.update(q, dict(status='failed'))

        wpx_data = a_wpx.to_dict()
        a_wpx.update(q, wpx_data)
        logger.debug(
            f'url_hash {url_hash}, update successful, crawler completed')

    # inform AC
    inform_ac.check_content_hash(a_wpx)
    inform_ac_data = inform_ac.to_dict()
    logger.debug(f'url_hash {url_hash}, inform_ac_data {inform_ac_data}')

    ts.update(q, dict(status_xpath='ready'))
    tm.update(q, dict(status='ready', zi_sync=inform_ac.zi_sync,
                      inform_ac_status=inform_ac.status))

    logger.debug(
        f'url_hash {url_hash} status {ts.status_xpath}')

    if not ac_content_status_api:
        return

    if celery.conf['ONLY_PERMIT_P1'] and priority != 1:
        return

    headers = {'Content-Type': "application/json"}
    resp_data = retry_request(
        'put', ac_content_status_api, inform_ac_data, headers)

    if resp_data:
        if inform_ac.old_url_hash:
            q = {
                'url_hash': inform_ac.old_url_hash,
                'content_hash': a_wpx.content_hash
            }
            u2c = UrlToContent().select(q)
            u2c.update(q, dict(replaced=True))
            logger.debug(
                f'url_hash {url_hash}, old url_hash {inform_ac.old_url_hash} record in UrlToContent() has been modified')

            q = {'url_hash': inform_ac.old_url_hash}
            # tm = TaskMain()
            doc = tm.select(q)
            tm.delete(doc)
            logger.debug(
                f'url_hash {url_hash}, old url_hash {inform_ac.old_url_hash} record in TaskMain() has been deleted')

        logger.debug(f'resp_data {resp_data}')
        q = dict(url_hash=url_hash)
        ts.update(q, dict(status_xpath='done'))
        tm.update(q, dict(status='done', done_time=datetime.utcnow()))
        logger.debug(f'url_hash {url_hash}, inform AC successful')

    else:
        q = dict(url_hash=url_hash)
        ts.update(q, dict(status_xpath='failed'))
        tm.update(q, dict(status='failed'))
        logger.error(f'url_hash {url_hash}, inform AC failed')


@celery.task()
def xpath_multi_crawler(url_hash: str, url: str, partner_id: str, domain: str, domain_info: dict):
    '''
    partner only

    loop xpath_a_crawler by page number

    ** remember to update the url & url_hash in CC and AC
    '''
    logger.debug(f'start to crawl multipaged url on url_hash {url_hash}')

    prepare_crawler(url_hash, partner=True, xpath=True)

    q = dict(url_hash=url_hash)
    tm = TaskMain()
    ts = TaskService().select(q)
    priority = ts.task_main.priority
    url = ts.url
    page_query_param = domain_info['page'][0]

    page_num = 0
    cat_wpx = WebpagesPartnerXpath()
    cat_inform_ac = InformAC()

    multi_page_urls = set()
    while page_num <= 10:
        page_num += 1
        if page_query_param == "d+":
            i_url = f'{url}/{page_num}'
        else:
            i_url = f'{url}?{page_query_param}={page_num}'

        try:
            a_wpx, inform_ac = xpath_a_crawler(
                url_hash, i_url, partner_id, domain, domain_info, multipaged=True)
            # multi_page_urls.add(i_url)
        except requests.exceptions.ReadTimeout as e:
            logger.error(
                f'url_hash {url_hash}, i_url {i_url} site take too long to response, quit waiting!')
            logger.error(e)
            if page_num == 1:
                bypass_crawler.delay(url_hash)
                return
            continue
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            if page_num == 1:
                bypass_crawler.delay(url_hash)
                return
            continue

        if not inform_ac.status:
            logger.debug(f'failed to crawl {i_url}')
            # cat_inform_ac.status = False
            break

        logger.debug(f'inform_ac.skip_crawler {inform_ac.skip_crawler}')
        if inform_ac.skip_crawler:
            cat_inform_ac.skip_crawler = True
            cat_wpx = a_wpx
            break

        multi_page_urls.add(i_url)
        if page_num == 1:
            # if successed, replace
            cat_wpx = a_wpx  # reference replacement
            cat_inform_ac = inform_ac

            if not inform_ac.status:
                # only if failed at first page, it is a total failure
                bypass_crawler.delay(url_hash)
                return

            # break  # Lance debug
        else:
            cat_wpx.content += a_wpx.content
            cat_wpx.content_h1 += a_wpx.content_h1
            cat_wpx.content_h2 += a_wpx.content_h2
            cat_wpx.content_p += a_wpx.content_p
            cat_wpx.content_image += a_wpx.content_image
            cat_wpx.len_p += a_wpx.len_p
            cat_wpx.len_img += a_wpx.len_img
            cat_wpx.len_char += a_wpx.len_char

    cat_inform_ac.url = url
    cat_wpx.url = url
    cat_wpx.url_hash = url_hash
    cat_inform_ac.check_content_hash(cat_wpx)

    if cat_inform_ac.status and cat_wpx.len_img < 2 and cat_wpx.len_char < 100:
        cat_inform_ac.zi_sync = False
        cat_inform_ac.zi_defy.add('quality')
        cat_inform_ac.quality = False

    if cat_inform_ac.skip_crawler:
        logger.debug(
            f'url_hash {url_hash} cat_inform_ac.skip_crawler {cat_inform_ac.skip_crawler} no need to update WebpagesPartnerXpath() table')
    else:
        wpx = WebpagesPartnerXpath()
        cat_wpx.multi_page_urls = sorted(multi_page_urls)
        cat_wpx.task_service_id = ts.id
        cat_wpx_data = cat_wpx.to_dict()
        logger.debug(f'cat_wpx_data {cat_wpx_data}')
        wpx.update(q, cat_wpx_data)

    ts.update(q, dict(status_xpath='ready'))
    tm.update(q, dict(status='ready', zi_sync=cat_inform_ac.zi_sync,
                      inform_ac_status=cat_inform_ac.status))

    if not ac_content_status_api:
        return
    if celery.conf['ONLY_PERMIT_P1'] and priority != 1:
        return

    data = cat_inform_ac.to_dict()
    logger.debug(f'url_hash {url_hash}, payload {data}')
    headers = {'Content-Type': "application/json"}
    resp_data = retry_request('put', ac_content_status_api, data, headers)
    logger.debug(f'resp_data {resp_data}')
    if resp_data:
        if cat_inform_ac.old_url_hash:
            q = {
                'url_hash': cat_inform_ac.old_url_hash,
                'content_hash': cat_wpx.content_hash
            }
            u2c = UrlToContent().select(q)
            u2c.update(q, dict(replaced=True))
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in UrlToContent() has been modified')

            q = {'url_hash': cat_inform_ac.old_url_hash}
            tm = TaskMain()
            doc = tm.select(q)
            tm.delete(doc)
            logger.debug(
                f'url_hash {url_hash}, old url_hash {cat_inform_ac.old_url_hash} record in TaskMain() has been deleted')

        logger.debug(f'url_hash {url_hash}, before updating TaskService()')
        q = dict(url_hash=url_hash)
        ts.update(q, dict(status_xpath='done'))
        tm = TaskMain()
        tm.update(q, dict(status='done', done_time=datetime.utcnow()))

        logger.debug(f'url_hash {url_hash}, inform AC successful')
    else:
        q = dict(url_hash=url_hash)
        ts.update(q, dict(status_xpath='failed'))
        tm.update(q, dict(status='failed'))
        # cat_wpx.task_service.status_xpath = 'failed'
        logger.error(f'url_hash {url_hash} inform AC failed')


@celery.task()
def ai_single_crawler(url_hash: str, url: str, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    might be a partner or non-partner
    '''
    logger.debug(f'run ai_single_crawler() on url_hash {url_hash}')

    if partner_id:

        wp_dict = prepare_crawler(url_hash, partner=True, xpath=False)
        url_hash = wp_dict['url_hash']
        a_wp = ai_a_crawler(wp_dict, partner_id)

        q = dict(url_hash=url_hash)

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
        # only non-partner should inform AC
        wp_dict = prepare_crawler(url_hash, partner=False, xpath=False)
        url_hash = wp_dict['url_hash']
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

        if not ac_content_status_api:
            return

        # inform AC
        logger.debug(f'url_hash {url_hash} ready to inform AC')
        headers = {'Content-Type': "application/json"}
        resp_data = retry_request(
            'put', ac_content_status_api, iac_data, headers)

        if resp_data:
            logger.debug(f'url_hash {url_hash} inform AC successful')
            data = dict(status='done')
            tns.update(q, data)

            data = {
                'done_time': datetime.utcnow(),
                'status': 'done'
            }
            tm.update(q, data)

            logger.debug('inform AC successful')
        else:
            data = dict(status='failed')
            tm.update(q, data)
            logger.error('inform AC failed')


@celery.task()
def ai_multi_crawler(url_hash: str, url: str, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    must be a partner

    no need to inform AC
    '''
    logger.debug(f'run ai_multi_crawler() on url_hash {url_hash}')

    if partner_id:
        prepare_crawler(url_hash, partner=True, xpath=False)
        cat_wp_data = WebpagesPartnerAi().to_dict()
        # logger.debug(f'cat_wp_data {cat_wp_data}')

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


# ==== tool tasks ====

@celery.task()
def bypass_crawler(url_hash: str, status: str='done'):
    '''
    this url need not to crawl

    do two things:
    1. infrom AC through request
    2. if (1) succeed, change db TaskMain() status to done

    data should have keys: url_hash, url, request_id
    '''

    q = dict(url_hash=url_hash)
    tm = TaskMain().select(q)
    priority = tm.priority
    iac = InformAC()
    iac.url = tm.url
    iac.url_hash = tm.url_hash
    iac.request_id = tm.request_id
    # iac.zi_sync = False
    iac.status = False
    iac_data = iac.to_dict()

    if not ac_content_status_api:
        return
    if celery.conf['ONLY_PERMIT_P1'] and priority != 1:
        return

    resp_data = request_api(ac_content_status_api, 'put', iac_data)
    if resp_data:
        logger.debug(f'url_hash {url_hash} inform AC successful')
        data = dict(status=status, done_time=datetime.utcnow(),
                    zi_sync=False, inform_ac_status=False)
        tm.update(q, data)
    else:
        logger.error(f'url_hash {url_hash} inform AC failed')
        data = dict(status='failed', done_time=datetime.utcnow(),
                    zi_sync=False, inform_ac_status=False)
        tm.update(q, data)


@celery.task()
def reset_doing_tasks(hour: int=1, priority: int=None, limit: int=10000):
    '''
    query the hanging task (status = doing) from TaskMain() with _mtime at least a hour before now

    status = doing
    _mtime < now - 1 hour

    Caution: do not use sql syntax to update status 'doing' back to 'pending'
    '''
    # q = {
    #     'status': 'doing',
    # }
    hours_before_now = datetime.utcnow() - timedelta(hours=hour)
    logger.debug(f'hours_before_now {hours_before_now}')
    # tml = TaskMain.query.options(load_only('url_hash')).filter_by(
    #     **q).filter(db.cast(TaskMain._mtime, db.DateTime) < db.cast(hours_before_now, db.DateTime)).order_by(TaskMain._mtime.asc()).limit(limit).all()

    if priority and priority != 0:
        tml = TaskMain.query.options(load_only('url_hash')).filter_by(priority=priority).filter(db.cast(TaskMain._mtime, db.DateTime) < db.cast(
            hours_before_now, db.DateTime), or_(TaskMain.status == 'preparing', TaskMain.status == 'doing')).order_by(TaskMain._mtime.asc()).limit(limit).all()
    else:
        tml = TaskMain.query.options(load_only('url_hash')).filter(db.cast(TaskMain._mtime, db.DateTime) < db.cast(hours_before_now, db.DateTime), or_(
            TaskMain.status == 'preparing', TaskMain.status == 'doing')).order_by(TaskMain._mtime.asc()).limit(limit).all()

    # TaskMain.partner_id is not None
    # logger.debug(f'type(tml) {type(tml)}')
    logger.debug(f'len {len(tml)}')
    if not len(tml):
        logger.debug(
            f'too good to be true, no doing tasks left before an hour')
        return

    for tm in tml:
        # only partner need to be redo

        data = dict(url_hash=tm.url_hash, domain=tm.domain, url=tm.url)
        if tm.partner_id:
            data['partner_id'] = tm.partner_id
        upsert_main_task.delay(data)
        logger.debug(f'url_hash {tm.url_hash}, upsert_main_task.delay() sent')


@celery.task()
def stats_cc(itype: str='day'):
    '''
    summarize the daily statistics of CC
    '''

    if itype not in ['day', 'hour']:
        return

    start_dt_str = None
    end_dt_str = None

    if itype == 'day':
        start_dt_str = (datetime.utcnow() - timedelta(days=2)
                        ).strftime("%Y-%m-%d 16:00:00")
        end_dt_str = (datetime.utcnow() - timedelta(days=1)
                      ).strftime("%Y-%m-%d 16:00:00")

    logger.debug(
        f'start_dt_str \'{start_dt_str}\' ~ end_dt_str \'{end_dt_str}\'')
    # under construction
    sql_str = f'select priority,status,count(id) from task_main where _mtime > \'{start_dt_str}\' and _mtime < \'{end_dt_str}\' group by priority,status;'
    logger.debug(f'sql_str {sql_str}')

    ret = db.engine.execute(sql_str)
    logger.debug(f'ret {ret}')

    rows = []
    for irow in ret:
        pass
        # todo


@celery.task()
def patch_mimic_aujs(limit: int=10000, file: str=None, itype: str='url_hash'):
    '''
    [queue name] default

    extract url_hash(page_id) from csv file provided by Lisa and use them to query TaskMain() table to get url, partner_id and generator and request AC with those payloads.

    [example]
    tasks.patch_mimic_aujs.delay(10000)

    [old example]
    file: /usr/src/app/tmp/test.csv

    tasks.patch_mimic_aujs.delay('/usr/src/app/tmp/test.csv')

    tasks.patch_mimic_aujs.delay('/usr/src/app/tmp/url_pageid_2019-03-05T00~2019-03-07T00_v2.csv', 'url')



    [case 1: no generator]
    http://localhost:80/v1/content/async?service\_name=Zi_C&&partner_id=9ZT4W18&url=http://tomchun.tw/tomchun/category/3c%e8%b3%87%e8%a8%8a/%e9%9b%bb%e8%85%a6/%e7%a1%ac%e7%a2%9f/page/3/

    [case 2: w/ generator]
    curl -X GET "http://localhost:80/v1/content/async?&partner_id=F7YWH18&url=https://yii.tw/blog/post/44832748&generator=WordPress 5.0.1"

    total: ~1150000
    '''

    if itype not in ['url_hash', 'url']:
        logger.error(f'patch_mimic_aujs() itype not correct: {itype}')
        return

    if not ac_content_async:
        logger.debug(f'ac_content_async api url not set: {ac_content_async}')
        return
    dedup = {}

    total_count = 0
    map_count = 0
    ac_yes_count = 0
    if file:
        with open(file) as f:
            for i, line in enumerate(f):
                total_count += 1
                candit = line.split()[0]
                logger.debug(f'{i}|||{candit}|||')
                if candit not in dedup:
                    dedup[candit] = 1
                    if itype == 'url_hash':
                        q = dict(url_hash=candit)
                    elif itype == 'url':
                        q = dict(url=candit)
                    tm = TaskMain().select(q)
                    if not tm or not tm.partner_id:
                        logger.debug(
                            f'no record for this {itype} {candit}, skip.')
                        continue

                    map_count += 1
                    if not celery.conf['MIMIC_AUJS']:
                        logger.info(
                            f'patch_mimic_aujs() no need to inform AC, total_count {total_count}, map_count {map_count}, ac_yes_count {ac_yes_count}')
                        continue

                    if tm.generator:
                        ac_content_async_cat = f'{ac_content_async}?service_name=Zi_C&partner_id={tm.partner_id}&url={tm.url}&generator={tm.generator}'
                    else:
                        ac_content_async_cat = f'{ac_content_async}?service_name=Zi_C&partner_id={tm.partner_id}&url={tm.url}'

                    resp_data = request_api(ac_content_async_cat, 'GET')
                    if resp_data:
                        ac_yes_count += 1
                        logger.info(
                            f'patch_mimic_aujs() inform AC successful, total_count {total_count}, map_count {map_count}, ac_yes_count {ac_yes_count}')
                    else:
                        logger.error(f'patch_mimic_aujs() imform AC failed')
                else:
                    pass  # skip this url_hash
        logger.info(
            f'patch_mimic_aujs(): total_count {total_count}, map_count {map_count}, ac_yes_count {ac_yes_count}')

    else:
        if not celery.conf['MIMIC_AUJS']:
            logger.info(
                f'patch_mimic_aujs() no need to inform AC, total_count {total_count}')
            return

        # not from file
        tml = TaskMain.query.options(load_only('url_hash', 'url', 'partner_id', 'generator')).filter(
            TaskMain.partner_id != None, TaskMain.status == 'failed', TaskMain.done_time == None).limit(limit).all()

        if not len(tml):
            logger.debug(f'patch_mimic_aujs() no record found!')
        else:
            for tm in tml:
                total_count += 1
                mimic_aujs_request_ac.delay(
                    tm.url_hash, tm.url, tm.partner_id, tm.generator)
                logger.debug(
                    f'patch_mimic_aujs() url_hash {tm.url_hash} mimic_aujs_request_ac.delay() task sent. total_count {total_count}')


@celery.task()
def mimic_aujs_request_ac(url_hash: str, url: str, partner_id: str, generator: str):
    '''
    [queue name]: bypass_crawler
    '''
    tm = TaskMain()
    q = dict(url_hash=url_hash)

    if generator and generator != '':
        ac_content_async_cat = f'{ac_content_async}?service_name=Zi_C&partner_id={partner_id}&url={url}&generator={generator}'
    else:
        ac_content_async_cat = f'{ac_content_async}?service_name=Zi_C&partner_id={partner_id}&url={url}'

    resp_data = request_api(ac_content_async_cat, 'GET')
    if resp_data:
        tm.update(q, dict(status='debug'))
        logger.info(
            f'mimic_aujs_request_ac() url_hash {url_hash} inform AC successful')
    else:
        tm.update(q, dict(status='failed'))
        logger.error(
            f'mimic_aujs_request_ac() url_hash {url_hash} inform AC failed')
