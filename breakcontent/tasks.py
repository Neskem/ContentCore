from breakcontent.article_manager import InformACObj
from breakcontent.crawler_manager import CrawlerObj
from breakcontent.factory import create_celery_app
from breakcontent.mercury_manager import MercuryObj
from breakcontent.orm_content import delete_old_related_data, get_task_main_data, update_task_main_detailed_status, \
    init_task_main, get_task_service_data, init_task_service, update_task_service_with_status, \
    get_task_no_service_data, init_task_no_service, update_task_no_service_with_status, update_task_main, \
    update_task_service, update_task_no_service, update_task_main_status, get_webpages_xpath, \
    update_webpages_for_external, create_webpages_xpath_with_data, get_task_main_tasks, \
    update_task_service_multipage, get_task_main_data_with_status, get_executing_tasks, get_cc_health_check_report, \
    get_xpath_parsing_rules_by_id, create_xpath_parsing_rules, clear_xpath_parsing_rule
from breakcontent.utils import get_domain_info, request_api
from breakcontent.utils import construct_email, send_email, to_csvstr, remove_html_tags
from celery.utils.log import get_task_logger
from urllib.parse import urlparse, unquote
from datetime import timedelta, datetime
from lxml import etree
from html import unescape
import hashlib
import lxml.html
import re
import os

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
    update_task_main_status(data['url_hash'], status='doing')

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
    else:
        update_task_main(data['url_hash'], data['partner_id'], data['request_id'], data['priority'], data['generator'])
    update_task_main_detailed_status(data['url_hash'], status='pending', doing_time=None, done_time=None,
                                     zi_sync=None, inform_ac_status=None)

    if 'partner_id' in data and data['partner_id'] is not None:
        task_service = get_task_service_data(data['url_hash'])
        if not task_service:
            init_task_service(data['url'], data['url_hash'], domain, data['partner_id'], data['request_id'])
        else:
            update_task_service(data['url_hash'], data['partner_id'], data['request_id'])
        update_task_service_with_status(data['url_hash'], status_ai='pending', status_xpath='pending', retry_xpath=0)
    else:
        task_no_service = get_task_no_service_data(data['url_hash'])
        if not task_no_service:
            init_task_no_service(data['url'], data['url_hash'], domain, data['request_id'])
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
        if task.partner_id is not None and len(task.partner_id) > 0:
            parsing_rules = get_xpath_parsing_rules_by_id(task.id)
            if parsing_rules is False:
                create_xpath_parsing_rules(task.id, task.url_hash)
                parsing_rules = [0, 0, 0, 0, 0]
        else:
            parsing_rules = None

        if task.task_partner_id:
            if int(priority) == 1:
                logger.debug('url_hash {}, sent to high_speed_p1.delay()'.format(task.url_hash))
                high_speed_p1.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, parsing_rules,
                                    task.partner_id)
            else:
                prepare_task.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, parsing_rules,
                                   task.partner_id)
        elif not task.partner_id:
            logger.debug('url_hash {}, sent task for tm.task_noservice'.format(task.url_hash))
            prepare_task.delay(int(priority), task.url_hash, task.url, task.domain, task.request_id)
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

    if task.partner_id is not None and len(task.partner_id) > 0:
        parsing_rules = get_xpath_parsing_rules_by_id(task.id)
        if parsing_rules is False:
            create_xpath_parsing_rules(task.id, task.url_hash)
            parsing_rules = [0, 0, 0, 0, 0]
    else:
        parsing_rules = None

    if task.partner_id:
        if int(priority) == 1:
            logger.debug('url_hash {}, sent to high_speed_p1.delay()'.format(task.url_hash))
            high_speed_p1.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, parsing_rules,
                                task.partner_id)
        else:
            prepare_task.delay(task.priority, task.url_hash, task.url, task.domain, task.request_id, parsing_rules,
                               task.partner_id)
    elif not task.partner_id:
        logger.debug('url_hash {}, sent task for tm.task_noservice'.format(task.url_hash))
        prepare_task.delay(int(priority), task.url_hash, task.url, task.domain, task.request_id)
    else:
        # this might happen if you use sql to change doing back to pending
        # plz use reset_doing_tasks() instead
        bypass_crawler.delay(task.url_hash)
    return True


@celery.task(ignore_result=True)
def high_speed_p1(priority: int, url_hash: str, url: str, domain: str, request_id: str, parsing_rules, partner_id=None):
    logger.debug("url_hash {}, in high_speed_p1()".format(url_hash))
    prepare_task(priority, url_hash, url, domain, request_id, parsing_rules, partner_id)
    return True


@celery.task(ignore_result=True)
def prepare_task(priority: int, url_hash: str, url: str, domain: str, request_id: str, parsing_rules=None,
                 partner_id=None):
    logger.debug('url_hash {}, execute prepare_task'.format(url_hash))

    update_task_main_status(url_hash, status='preparing')
    if partner_id:
        logger.debug('url_hash {}, domain {}, partner_id {}'.format(url_hash, domain, partner_id))
        domain_info = get_domain_info(domain, partner_id)
        if type(domain_info) is dict:
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
                    init_task_service(url, url_hash, domain, partner_id, request_id)
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
                        xpath_crawler(url_hash, url, partner_id, domain, domain_info, parsing_rules, multi_pages=True)
                    else:
                        xpath_crawler.delay(url_hash, url, partner_id, domain, domain_info, parsing_rules,
                                            multi_pages=True)
            else:
                # preparing for single page crawler
                update_task_service_with_status(url_hash, status_ai='preparing', status_xpath='preparing')
                if priority and int(priority) == 1:
                    logger.debug('url_hash {}, run xpath_single_crawler() in high_speed_p1 task func'.format(url_hash))
                    xpath_crawler(url_hash, url, partner_id, domain, domain_info, parsing_rules)
                else:
                    logger.debug('url_hash {}, sent task to xpath_single_crawler.delay()'.format(url_hash))
                    xpath_crawler.delay(url_hash, url, partner_id, domain, domain_info, parsing_rules)
        else:
            logger.error('url_hash {}, no domain_info!'.format(url_hash))
            logger.error('domain_info: {}'.format(domain_info))
            bypass_crawler.delay(url_hash)
    else:
        # none partner goes here
        task_no_service = get_task_no_service_data(url_hash)
        if task_no_service is False:
            init_task_no_service(url, url_hash, domain, request_id)
        update_task_no_service_with_status(url_hash, status='doing')

        if celery.conf['MERCURY_PATH']:
            ai_single_crawler.delay(url_hash, url, domain=domain)
            logger.debug('url_hash {}, sent task to ai_single_crawler()'.format(url_hash))
        else:
            logger.debug('url_hash {}, MERCURY_TOKEN env variable not set'.format(url_hash))
            bypass_crawler.delay(url_hash)

    return True


@celery.task()
def xpath_crawler(url_hash: str, url: str, partner_id: str, domain: str, domain_info: dict, parsing_rules: list,
                  multi_pages=False):
    """
    <purpose>
    use the domain config from Partner System to crawl through the entire page, then inform AC with request

    <notice>
    partner only
    """
    logger.debug('url_hash {}, start to crawl single-paged url.'.format(url_hash))

    crawler_obj = CrawlerObj(url_hash=url_hash, url=url, domain=domain, partner_id=partner_id,
                             parsing_rules=parsing_rules)
    crawler_obj.prepare_crawler(xpath=True)
    crawler_obj.xpath_a_crawler(domain_rules=domain_info, multi_pages=multi_pages)

    return True


@celery.task()
def ai_single_crawler(url_hash: str, url: str, partner_id: str = None, domain: str = None):
    """
    might be a partner or non-partner
    """
    logger.debug('run ai_single_crawler() on url_hash {}'.format(url_hash))

    mercury_obj = MercuryObj(url_hash, url, domain, partner_id=partner_id)
    mercury_obj.prepare_mercury()
    mercury_obj.mercury_a_crawler()


# ==== tool tasks ====

@celery.task()
def bypass_crawler(url_hash: str):
    """
    this url need not to crawl

    do two things:
    1. inform AC through request
    2. if (1) succeed, change db TaskMain() status to done

    data should have keys: url_hash, url, request_id
    """
    task_main = get_task_main_data(url_hash)
    if task_main is False:
        logger.error('{} url_hash does not exist.'.format(url_hash))
        return False

    inform_ac = InformACObj(task_main.url, url_hash, task_main.request_id)
    inform_ac.set_ac_sync(False)
    inform_ac.set_zi_sync(False)
    if task_main.partner_id is not None and task_main.partner_id != '':
        inform_ac.sync_to_ac(True)
    else:
        inform_ac.sync_to_ac(False)

    return True


@celery.task()
def reset_doing_tasks(hour: int = 1, priority: int = 0, limit: int = 10000):
    """
    query the hanging task (status = doing) from TaskMain() with _mtime at least a hour before now

    status = doing
    _mtime < now - 1 hour

    Caution: do not use sql syntax to update status 'doing' back to 'pending'
    """
    hours_before_now = datetime.utcnow() - timedelta(hours=hour)
    logger.debug(f'hours_before_now {hours_before_now}')

    if priority and priority != 0:
        executing_tasks = get_executing_tasks(priority, hours_before_now, limit)
        if executing_tasks is False:
            logger.error('There is no executing task.')
            return False

        logger.debug('executing tasks: {}'.format(len(executing_tasks)))
        for task in executing_tasks:
            create_task.delay(task.url_hash, task.priority, status=task.status)
            logger.debug('{} url_hash is retrying again'.format(task.url_hash))
    return True


@celery.task()
def stats_cc(input_type: str = None):
    """
    summarize the daily statistics of CC

    be triggered every 7:00AM TW

    itype:

    day => for yesterday
    hour => for last hour
    all => for all record
    """

    if input_type and input_type not in ['day', 'hour', 'all']:
        return

    if input_type == 'day':
        # converting to TW time range
        start_dt_str = (datetime.utcnow() - timedelta(days=1)
                        ).strftime("%Y-%m-%d 16:00:00")
        end_dt_str = (datetime.utcnow() - timedelta(days=0)
                      ).strftime("%Y-%m-%d 16:00:00")
    elif input_type == 'hour':
        start_dt_str = (datetime.utcnow() - timedelta(hours=1)
                        ).strftime("%Y-%m-%d %H:%M:%S")
        end_dt_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    else:
        input_type = 'all'
        start_dt_str = '2019-01-01 00:00:00'  # CC released date: 2019-03-05
        end_dt_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    logger.debug(f'start_dt_str \'{start_dt_str}\' ~ end_dt_str \'{end_dt_str}\'')
    report_list = get_cc_health_check_report(start_dt_str, end_dt_str)

    rows = []
    output = {}

    rows.append(['partner', 'priority', 'status', 'count'])
    for report in report_list:
        tmp = []
        partner = report['pbool']
        priority = report['priority']
        status = report['status']
        count = report['count']
        tmp = [partner, priority, status, count]
        rows.append(tmp)
        logger.debug(f'tmp row {tmp}')

    output['stats_cc_{}'.format(input_type)] = rows

    # send email
    mail_data = to_csvstr(rows)
    # construct_email(mail_from, mail_to, subject, content, attach_filename, data)

    conf = (
        'rd@breaktime.com.tw',
        ['rd@breaktime.com.tw', 'data-service@breaktime.com.tw'],
        '[CC] {} stats'.format(input_type),
        'Dear all,<br>Please find the {} report in the attached file.<br>'.format(input_type),
        'CC_{}_report'.format(input_type),
        mail_data
    )
    mail = construct_email(*conf)
    send_email(mail)

    return output


@celery.task(ignore_result=True)
def clear_xpath_parsing_rule_task(task_main_id, url_hash):
    if task_main_id is not None and url_hash is not None:
        clear_xpath_parsing_rule(task_main_id, url_hash)
        logger.info("clear parsing rule, url_hash: {}".format(url_hash))

    return True
