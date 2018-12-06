from .factory import create_celery_app
from breakarticle.helper import generate_url_hash
from breakarticle.articleclass.task_manager import TaskInitialization
from breakarticle.articleclass.partner_manager import get_sitemap_url
from breakarticle.articleclass.orm_article import async_filter_urlinfo, generate_aysc_info, check_task_status_to_doing
from breakarticle.articleclass.orm_article import main_update_filter_urlinfo, exist_url_hash_urlinfo

import logging
import json
import requests
import xml.etree.ElementTree as ET
celery = create_celery_app()


@celery.task()
def test_delay(task_json):
    import time
    time.sleep(2)
    logging.info('Alan_test: test_delay: {}'.format(task_json))
    return task_json


@celery.task(ignore_result=True)
def test_queue(dpi_json):
    logging.info('Alan_test: test_queue: {}'.format(dpi_json))


@celery.task(ignore_result=True)
def send_task_content_core(task_dict):
    check_task_status = check_task_status_to_doing(task_dict['url_hash'])
    if check_task_status:
        task_json = json.dumps(task_dict)
        logging.info('Celery_task: send_task_content_core, task_json: {}'.format(task_json))
    return True


@celery.task(ignore_result=True)
def generate_task_info(url_hash, priority):
    url_hash_urlinfo_res, url_hash_taskinfo_res = generate_aysc_info(url_hash)
    task_dict = {'request_id': str(url_hash_taskinfo_res.request_id), 'partner_id': url_hash_urlinfo_res.partner_id,
                 'url_hash': url_hash, 'url': url_hash_urlinfo_res.url, 'generator': url_hash_taskinfo_res.generator,
                 'priority': priority}
    send_task_content_core(task_dict)
    return True


@celery.task(ignore_result=True)
def aync_filter_task(priority):
    """
    Update record in database for testing filter successfully or not.
    SQL command:
        update task_info set _ctime = '2018-11-20 06:35:07.220547' where url_hash = '<url_hash>';
        update task_info set async_priority = '3' where url_hash = '<url_hash>';
    """
    async_filter_task_list = async_filter_urlinfo()
    for async_filter_task_res in async_filter_task_list:
        # update_async_res means this task was mapping partner and including on one day.
        generate_task_info(async_filter_task_res.url_hash, priority)
    return True


@celery.task(ignore_result=True)
def main_update_content(priority):
    main_update_filter_task_list = main_update_filter_urlinfo()
    for main_update_filter_task_res in main_update_filter_task_list:
        generate_task_info(main_update_filter_task_res.url_hash, priority)
    return True


@celery.task(ignore_result=True)
def sitemap_update_content(priority):
    sitemap_url_task_list = get_sitemap_url()
    for sitemap_url_res in sitemap_url_task_list:
        sitemap_url = sitemap_url_res['sitemap']
        sitemap_url_domain = sitemap_url_res['domain']
        sitemap_partner_id = sitemap_url_res['partner']
        try:
            r = requests.get(sitemap_url)
        except requests.exceptions.InvalidSchema:
            logging.info(
                "This sitemap url can't be request, sitemap_url: {}".format(sitemap_url))
            continue
        if r.status_code == 200:
            main_menu = ET.fromstring(r.content)
            for urltag in main_menu:
                loc = urltag[0]
                url = loc.text
                task_type = "sitemap"
                url_hash, pure_url = generate_url_hash(url)
                urlinfo_validate = exist_url_hash_urlinfo(url_hash)
                if urlinfo_validate is False:
                    init_task_obj = TaskInitialization(task_type, url, url_hash, sitemap_url_domain, priority, sitemap_partner_id)
                    init_task_obj.initial_url_info()
                    generate_task_info(url_hash, priority)
                else:
                    # Exist URL will not do everything.
                    continue
    return True
