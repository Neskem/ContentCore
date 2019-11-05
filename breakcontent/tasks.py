from breakcontent.article_manager import InformACObj
from breakcontent.crawler_manager import CrawlerObj
from breakcontent.factory import create_celery_app
from breakcontent.orm_content import delete_old_related_data, get_task_main_data, update_task_main_detailed_status, \
    init_task_main, get_task_service_data, init_task_service_with_xpath, init_task_service, \
    update_task_service_with_status, \
    get_task_no_service_data, init_task_no_service, update_task_no_service_with_status, update_task_main, \
    update_task_service, update_task_no_service, update_task_main_status, get_webpages_xpath, \
    update_webpages_for_external, update_task_main_sync_status, create_webpages_xpath_with_data, get_task_main_tasks, \
    update_task_service_multipage, get_task_main_data_with_status
from breakcontent.utils import Secret, InformAC, DomainSetting, xpath_a_crawler, parse_domain_info, get_domain_info, \
    retry_request, request_api
from breakcontent.utils import mercury_parser, prepare_crawler, ai_a_crawler
from breakcontent.utils import construct_email, send_email, to_csvstr, remove_html_tags
from flask import current_app
from celery.utils.log import get_task_logger
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
from sqlalchemy.orm import load_only
from sqlalchemy import or_
from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi
from breakcontent.models import WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
from urllib.parse import urlencode, quote_plus, unquote, quote, unquote_plus, parse_qs
from urllib.parse import urlparse, urljoin
from datetime import timedelta, datetime
from lxml import etree
from html import unescape
import hashlib
import dateparser
import lxml.html
import re
import os
import requests
import time

celery = create_celery_app()
logger = get_task_logger('cc')

ac_content_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)
ac_content_multipage_api = os.environ.get('AC_CONTENT_MULTIPAGE_API', None)


@celery.task(ignore_result=True)
def delete_main_task(url_hash):
    logger.debug(f'run delete_main_task(), down stream records will also be deleted...')
    delete_old_related_data(url_hash)
    logger.debug('done delete_main_task()')
    return True


@celery.task(ignore_result=True)
def init_external_task(data: dict):
    upsert_main_task(data)
    update_task_main_status(data['url_hash'], status='doing', doing_time=datetime.utcnow())

    content_p = ''
    len_p = 0
    content = unquote(data['content'])
    content_html = lxml.html.fromstring(content)

    xpath_p = content_html.xpath('.//p')
    for p in xpath_p:
        txt = remove_html_tags(etree.tostring(
            p, pretty_print=True, method='html').decode("utf-8"))
        s = unescape(txt.strip())
        if s.strip():
            content_p += '<p>{}</p>'.format(s)
            len_p = len_p + 1

    content = remove_html_tags(content)
    pattern = re.compile(r'\s+')
    content = re.sub(pattern, '', content)
    content = unescape(content)
    len_char = len(content)

    content_hash = ''
    if data['description'] is not None and data['description'] != "":
        content_hash += data['description']
    else:
        if data['title']:
            content_hash += data['title']
    # concat publish_date
    if isinstance(data['publish_date'], datetime):
        content_hash += data['publish_date'].isoformat()
    elif data['publish_date'] is not None and len(data['publish_date']) > 0:
        content_hash += str(data['publish_date'])
    m = hashlib.sha1(content_hash.encode('utf-8'))
    content_hash = data['partner_id'] + '_' + m.hexdigest()

    webpages_xpath = get_webpages_xpath(data['url_hash'])
    if webpages_xpath is False:
        create_webpages_xpath_with_data(data['url'], data['url_hash'], data['domain'], data['title'], data['content'],
                                        content_hash, author=data['author'], publish_date=data['publish_date'],
                                        cover=data['cover'], meta_description=data['description'], content_p=content_p,
                                        len_p=len_p, len_char=len_char)
    else:
        update_webpages_for_external(data['url_hash'], title=data['title'], content=data['content'],
                                     content_hash=content_hash, author=data['author'],
                                     publish_date=data['publish_date'], cover=data['cover'],
                                     meta_description=data['description'], content_p=content_p, len_p=len_p,
                                     len_char=len_char)
    inform_ac = InformACObj(url=data['url'], url_hash=data['url_hash'], request_id=data['request_id'],
                            publish_date=data['publish_date'], ai_article=data['ai_article'])
    inform_ac.calculate_quality(len_char)
    inform_ac.sync_external_to_ac()
    return True


@celery.task(ignore_result=True)
def upsert_main_task(data: dict):
    logger.debug(f'org_data: {data}')

    if data.get('domain', None):
        domain = data['domain']
    else:
        o = urlparse(data['url'])
        domain = o.netloc
        data['domain'] = domain

    task_main = get_task_main_data(data['url_hash'])
    if not task_main:
        init_task_main(data['url'], data['url_hash'], data['partner_id'], domain, data['request_id'], data['priority'],
                       data['generator'])
        task_main = get_task_main_data(data['url_hash'])
    else:
        update_task_main(data['url_hash'], data['partner_id'], data['request_id'], data['priority'], data['generator'])
    update_task_main_detailed_status(data['url_hash'], status='pending', doing_time=None, done_time=None,
                                     zi_sync=None, inform_ac_status=None)

    if 'partner_id' in data and data['partner_id'] is not None:
        task_service = get_task_service_data(data['url_hash'])
        if not task_service:
            init_task_service(task_main.id, data['url'], data['url_hash'], domain, data['partner_id'],
                              data['request_id'])
        else:
            update_task_service(data['url_hash'], data['partner_id'], data['request_id'])
        update_task_service_with_status(data['url_hash'], status_ai='pending', status_xpath='pending', retry_xpath=0)
    else:
        task_no_service = get_task_no_service_data(data['url_hash'])
        if not task_no_service:
            init_task_no_service(task_main.id, data['url'], data['url_hash'], domain, data['request_id'])
        else:
            update_task_no_service(data['url_hash'], data['request_id'])
        update_task_no_service_with_status(data['url_hash'], status='pending')

    if 'priority' in data and data['priority'] != 7:
        create_task.delay(data['url_hash'], data['priority'], status='pending')

    return True


@celery.task(ignore_result=True)
def create_tasks(priority: str, limit: int = 4000):
    tasks = get_task_main_tasks(priority=priority, status='pending', limit=limit)
    if len(tasks) == 0 or tasks is False:
        return False
    for task in tasks:
        logger.debug('url_hash {}, in task list'.format(task.url_hash))

        if task.task_service and task.task_partner_id:
            if int(priority) == 1:
                logger.debug('url_hash {}, sent to high_speed_p1.delay()'.format(task.url_hash))
                high_speed_p1.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, task.id,
                                    task.partner_id)
            else:
                prepare_task.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, task.id,
                                   task.partner_id)
        elif task.task_noservice and not task.partner_id:
            logger.debug('url_hash {}, sent task for tm.task_noservice {}'.format(task.url_hash, task.task_noservice))
            prepare_task.delay(int(priority), task.url_hash, task.url, task.domain, task.request_id, task.domain,
                               task.id)
        else:
            # this might happen if you use sql to change doing back to pending
            # plz use reset_doing_tasks() instead
            bypass_crawler.delay(task.url_hash)
    return True


@celery.task(ignore_result=True)
def create_task(url_hash, priority, status):
    task = get_task_main_data_with_status(url_hash, priority, status)
    if task is False:
        return False

    if task.task_service and task.partner_id:
        if int(priority) == 1:
            logger.debug('url_hash {}, sent to high_speed_p1.delay()'.format(task.url_hash))
            high_speed_p1.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, task.id,
                                task.partner_id)
        else:
            prepare_task.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, task.id,
                               task.partner_id)
    elif task.task_noservice and not task.partner_id:
        logger.debug('url_hash {}, sent task for tm.task_noservice {}'.format(task.url_hash, task.task_noservice))
        prepare_task.delay(int(priority), task.url_hash, task.url, task.domain, task.request_id, task.domain,
                           task.id)
    else:
        # this might happen if you use sql to change doing back to pending
        # plz use reset_doing_tasks() instead
        bypass_crawler.delay(task.url_hash)
    return True


@celery.task(ignore_result=True)
def high_speed_p1(priority: int, url_hash: str, url: str, domain: str, request_id: str, task_main_id: str,
                  partner_id=None):
    logger.debug("url_hash {}, in high_speed_p1()".format(url_hash))
    prepare_task(priority, url_hash, url, domain, request_id, task_main_id, partner_id)
    return True


@celery.task(ignore_result=True)
def prepare_task(priority: int, url_hash: str, url: str, domain: str, request_id: str, task_main_id: str,
                 partner_id=None):
    logger.debug('url_hash {}, execute prepare_task'.format(url_hash))

    update_task_main_status(url_hash, status='preparing', doing_time=datetime.utcnow())
    if partner_id is not None:
        logger.debug('url_hash {}, domain {}, partner_id {}'.format(url_hash, domain, partner_id))
        domain_info = get_domain_info(domain, partner_id)
        if domain_info:
            if domain_info.get('page', None) and domain_info['page'] != '':
                execute_multi_crawler = celery.conf['RUN_XPATH_MULTI_CRAWLER']
                if not execute_multi_crawler:
                    logger.debug("url_hash {}, multi crawler is closed".format(url_hash))
                    update_task_main_status(url_hash, status='done')
                    return
                # preparing for multipage crawler
                page_query_param = domain_info['page'][0]
                task_service = get_task_service_data(url_hash)
                if task_service is False:
                    init_task_service(task_main_id, url, url_hash, domain, partner_id, request_id)
                update_task_service_multipage(url_hash, is_multipage=True, page_query_param=page_query_param,
                                              status_ai='doing', status_xpath='preparing')

                multi_url = url
                if page_query_param:
                    if page_query_param == "d+":
                        multi_url = re.sub(r'\/\d+$', '', url)
                    else:
                        multi_url = re.sub(r'\?(page|p)=\d+', '', url)
                logger.debug('url_hash {}, multipage: url {}, multi_url {}'.format(url_hash, url, multi_url))

                if multi_url != url and ac_content_multipage_api:
                    data = {'url': url, 'url_hash': url_hash, 'multipage': multi_url, 'domain': domain}
                    resp_data = request_api(ac_content_multipage_api, 'post', data)
                    if resp_data:
                        logger.debug('url_hash {}, mp_url != url: resp_data {}, inform AC successful'.format(
                            url_hash, resp_data))
                        delete_old_related_data(url_hash)
                        logger.debug(f'url_hash {url_hash}, mp_url != url: after delete tm.')
                    else:
                        logger.error('url_hash {}, mp_url != url: resp_data {}, inform AC failed'.format(
                            url_hash, resp_data))
                else:
                    logger.debug("url_hash {}, mp_url = url: partner_id {}, domain {}".format(
                        url_hash, partner_id, domain))
                    if priority and int(priority) == 1:
                        xpath_crawler(url_hash, url, partner_id, domain, domain_info, multi_pages=True)
                    else:
                        xpath_crawler.delay(url_hash, url, partner_id, domain, domain_info, multi_pages=True)
            else:
                # preparing for single page crawler
                update_task_service_with_status(url_hash, status_ai='preparing', status_xpath='preparing')
                if priority and int(priority) == 1:
                    logger.debug('url_hash {}, run xpath_single_crawler() in high_speed_p1 task func'.format(url_hash))
                    xpath_crawler(url_hash, url, partner_id, domain, domain_info)
                else:
                    logger.debug('url_hash {}, sent task to xpath_single_crawler.delay()'.format(url_hash))
                    xpath_crawler.delay(url_hash, url, partner_id, domain, domain_info)
        else:
            logger.error('url_hash {}, no domain_info!'.format(url_hash))
            bypass_crawler.delay(url_hash)
    else:
        # none partner goes here
        task_no_service = get_task_no_service_data(url_hash)
        if task_no_service is False:
            init_task_no_service(task_main_id, url, url_hash, domain, request_id)
        update_task_no_service_with_status(url_hash, status='doing')

        if celery.conf['MERCURY_PATH']:
            ai_single_crawler.delay(url_hash, url)
            logger.debug('url_hash {}, sent task to ai_single_crawler()'.format(url_hash))
        else:
            logger.debug('url_hash {}, MERCURY_TOKEN env variable not set'.format(url_hash))
            bypass_crawler.delay(url_hash)

    return True


@celery.task()
def xpath_crawler(url_hash: str, url: str, partner_id: str, domain: str, domain_info: dict, multi_pages=False):
    """
    <purpose>
    use the domain config from Partner System to crawl through the entire page, then inform AC with request

    <notice>
    partner only
    """
    logger.debug('url_hash {}, start to crawl single-paged url.'.format(url_hash))

    crawler_obj = CrawlerObj(url_hash=url_hash, url=url, domain=domain, partner_id=partner_id)
    crawler_obj.prepare_crawler(xpath=True)
    crawler_obj.xpath_a_crawler(domain_rules=domain_info, multi_pages=multi_pages)

    return True


@celery.task()
def ai_single_crawler(url_hash: str, url: str, partner_id: str=None, domain: str=None, domain_info: dict=None):
    '''
    might be a partner or non-partner
    '''
    logger.debug(f'run ai_single_crawler() on url_hash {url_hash}')

    if partner_id:
        # this part deprecated
        prepare_crawler(url_hash, partner=True, xpath=False)
        # url_hash = wp_dict['url_hash']
        a_wp = ai_a_crawler(url_hash, url, partner_id, domain, domain_info)

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
        prepare_crawler(url_hash, partner=False, xpath=False)
        # url_hash = wp_dict['url_hash']
        try:
            a_wp = ai_a_crawler(url_hash, url)
        except requests.exceptions.ConnectionError as e:
            logger.error(e)
            bypass_crawler.delay(url_hash)
            return

        q = dict(url_hash=url_hash)

        wpns = WebpagesNoService()
        tns = TaskNoService().select(q)
        tm = TaskMain()

        iac = InformAC()
        iac_data = iac.to_dict()

        if a_wp:
            udata = {
                'url_hash': url_hash,
                'url': url,
                'request_id': tns.request_id,
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
def ai_multi_crawler(url_hash: str, url: str, partner_id: str = None, domain: str = None, domain_info: dict = None):
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
def bypass_crawler(url_hash: str, status: str = 'done'):
    """
    this url need not to crawl

    do two things:
    1. infrom AC through request
    2. if (1) succeed, change db TaskMain() status to done

    data should have keys: url_hash, url, request_id
    """

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
def reset_doing_tasks(hour: int = 1, priority: int = None, limit: int = 10000):
    """
    query the hanging task (status = doing) from TaskMain() with _mtime at least a hour before now

    status = doing
    _mtime < now - 1 hour

    Caution: do not use sql syntax to update status 'doing' back to 'pending'
    """
    hours_before_now = datetime.utcnow() - timedelta(hours=hour)
    logger.debug(f'hours_before_now {hours_before_now}')

    if priority and priority != 0:
        tml = TaskMain.query.options(load_only('url_hash')).filter_by(priority=priority).filter(
            db.cast(TaskMain._mtime, db.DateTime) < db.cast(
                hours_before_now, db.DateTime),
            or_(TaskMain.status == 'preparing', TaskMain.status == 'doing')).order_by(TaskMain._mtime.asc()).limit(
            limit).all()
    else:
        tml = TaskMain.query.options(load_only('url_hash')).filter(
            db.cast(TaskMain._mtime, db.DateTime) < db.cast(hours_before_now, db.DateTime), or_(
                TaskMain.status == 'preparing', TaskMain.status == 'doing')).order_by(TaskMain._mtime.asc()).limit(
            limit).all()

    # TaskMain.partner_id is not None
    # logger.debug(f'type(tml) {type(tml)}')
    logger.debug(f'len {len(tml)}')
    if not len(tml):
        logger.debug(f'too good to be true, no doing tasks left before an hour')
        return

    for tm in tml:
        # only partner need to be redo

        data = dict(url_hash=tm.url_hash, domain=tm.domain, url=tm.url)
        if tm.partner_id:
            data['partner_id'] = tm.partner_id
        upsert_main_task.delay(data)
        logger.debug(f'url_hash {tm.url_hash}, upsert_main_task.delay() sent')


@celery.task()
def stats_cc(itype: str = None):
    '''
    summarize the daily statistics of CC

    be triggered every 7:00AM TW

    itype:

    day => for yesterday
    hour => for last hour
    all => for all record
    '''

    if itype and itype not in ['day', 'hour', 'all']:
        return

    start_dt_str = None
    end_dt_str = None

    if itype == 'day':
        # converting to TW time range
        start_dt_str = (datetime.utcnow() - timedelta(days=1)
                        ).strftime("%Y-%m-%d 16:00:00")
        end_dt_str = (datetime.utcnow() - timedelta(days=0)
                      ).strftime("%Y-%m-%d 16:00:00")
    elif itype == 'hour':
        start_dt_str = (datetime.utcnow() - timedelta(hours=1)
                        ).strftime("%Y-%m-%d %H:%M:%S")
        end_dt_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    else:
        itype = 'all'
        start_dt_str = '2019-01-01 00:00:00'  # CC released date: 2019-03-05
        end_dt_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    logger.debug(
        f'start_dt_str \'{start_dt_str}\' ~ end_dt_str \'{end_dt_str}\'')
    # under construction
    sql_str = f'select case when partner_id is null then false else true end as pbool,priority,status,count(id) from task_main where _mtime > \'{start_dt_str}\' and _mtime < \'{end_dt_str}\' group by pbool,priority,status order by pbool desc,priority,status;'
    logger.debug(f'sql_str {sql_str}')

    ret = db.engine.execute(sql_str)
    logger.debug(f'ret {ret}')

    rows = []
    outdata = {}

    rows.append(['partner', 'priority', 'status', 'count'])
    for row in ret:
        tmp = []
        partner = row['pbool']
        priority = row['priority']
        status = row['status']
        count = row['count']
        tmp = [partner, priority, status, count]
        rows.append(tmp)
        logger.debug(f'tmp row {tmp}')

    outdata[f'stats_cc_{itype}'] = rows

    # send email
    datastr = to_csvstr(rows)
    # construct_email(mailfrom, mailto, subject, content, attfilename, data)

    conf = (
        'rd@breaktime.com.tw',
        ['rd@breaktime.com.tw', 'data-service@breaktime.com.tw'],
        f'[CC] {itype} stats',
        f'Dear all,<br>Please find the {itype} report in the attached file.<br>',
        f'CC_{itype}_report',
        datastr
    )
    mail = construct_email(*conf)
    send_email(mail)

    return outdata
