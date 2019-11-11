import datetime

from sqlalchemy import or_

from breakcontent import db
from breakcontent.helper import pg_add_wrapper
from breakcontent.models import TaskMain, WebpagesNoService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, \
    TaskService, DomainInfo, UrlToContent


def init_task_main(url, url_hash, partner_id, domain, request_id, priority, generator=None):
    new_init_task = TaskMain(url=url, url_hash=url_hash, partner_id=partner_id, domain=domain, request_id=request_id,
                             priority=priority, generator=generator)
    pg_add_wrapper(new_init_task)


def update_task_main(url_hash, partner_id, request_id, priority, generator=None):
    db.session.query(TaskMain).filter_by(url_hash=url_hash).update({
        'partner_id': partner_id,
        'request_id': request_id,
        'priority': priority,
        'generator': generator
    })
    db.session.commit()


def init_task_service(url, url_hash, domain, partner_id, request_id):
    new_init_task_service = TaskService(url=url, url_hash=url_hash, domain=domain, partner_id=partner_id,
                                        request_id=request_id)
    pg_add_wrapper(new_init_task_service)


def update_task_service(url_hash, partner_id, request_id):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'partner_id': partner_id,
        'request_id': request_id
    })
    db.session.commit()


def init_task_no_service(url, url_hash, domain, request_id):
    new_init_task_no_service = TaskNoService(url=url, url_hash=url_hash, domain=domain, request_id=request_id)
    pg_add_wrapper(new_init_task_no_service)


def update_task_no_service(url_hash, request_id):
    db.session.query(TaskNoService).filter_by(url_hash=url_hash).update({
        'request_id': request_id
    })
    db.session.commit()


def update_task_main_status(url_hash, status):
    db.session.query(TaskMain).filter_by(url_hash=url_hash).update({
        'status': status
    })
    db.session.commit()


def update_task_main_sync_status(url_hash, status, zi_sync, inform_ac_status):
    db.session.query(TaskMain).filter_by(url_hash=url_hash).update({
        'status': status,
        'zi_sync': zi_sync,
        'inform_ac_status': inform_ac_status
    })
    db.session.commit()


def update_task_main_detailed_status(url_hash, status, doing_time, done_time, zi_sync, inform_ac_status):
    db.session.query(TaskMain).filter_by(url_hash=url_hash).update({
        'status': status,
        'doing_time': doing_time,
        'done_time': done_time,
        'zi_sync': zi_sync,
        'inform_ac_status': inform_ac_status
    })
    db.session.commit()


def update_task_service_status_xpath(url_hash, status_xpath, status_code=None):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'status_xpath': status_xpath,
        'status_code': status_code
    })
    db.session.commit()


def update_task_service_status_ai(url_hash, status_ai):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'status_ai': status_ai
    })
    db.session.commit()


def init_task_service_with_xpath(url_hash, domain, status_ai, status_xpath, retry_xpath):
    new_init_task_service = TaskService(url_hash=url_hash, domain=domain, status_ai=status_ai,
                                        status_xpath=status_xpath, retry_xpath=retry_xpath)
    pg_add_wrapper(new_init_task_service)


def update_task_service_with_status(url_hash, status_ai, status_xpath, retry_xpath=0):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'status_ai': status_ai,
        'status_xpath': status_xpath,
        'retry_xpath': retry_xpath
    })
    db.session.commit()


def update_task_service_with_status_only_xpath(url_hash, status_xpath):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'status_xpath': status_xpath
    })
    db.session.commit()


def update_task_no_service_with_status(url_hash, status):
    db.session.query(TaskNoService).filter_by(url_hash=url_hash).update({
        'status': status
    })
    db.session.commit()


def get_webpages_no_service_data(url_hash):
    url_hash_no_service = WebpagesNoService.query.filter_by(url_hash=url_hash).first()
    if url_hash_no_service is not None:
        return url_hash_no_service
    else:
        return False


def get_webpages_partner_xpath_data(url_hash):
    url_hash_no_service = WebpagesPartnerXpath.query.filter_by(url_hash=url_hash).first()
    if url_hash_no_service is not None:
        return url_hash_no_service
    else:
        return False


def get_webpages_partner_ai_data(url_hash):
    url_hash_no_service = WebpagesPartnerAi.query.filter_by(url_hash=url_hash).first()
    if url_hash_no_service is not None:
        return url_hash_no_service
    else:
        return False


def get_task_no_service_data(url_hash):
    url_hash_task_no_service = TaskNoService.query.filter_by(url_hash=url_hash).first()
    if url_hash_task_no_service is not None:
        return url_hash_task_no_service
    else:
        return False


def get_task_service_data(url_hash):
    url_hash_task_service = TaskService.query.filter_by(url_hash=url_hash).first()
    if url_hash_task_service is not None:
        return url_hash_task_service
    else:
        return False


def get_task_main_data(url_hash):
    url_hash_task_main = TaskMain.query.filter_by(url_hash=url_hash).first()
    if url_hash_task_main is not None:
        return url_hash_task_main
    else:
        return False


def get_task_main_data_with_status(url_hash, priority, status):
    url_hash_task_main = TaskMain.query.filter_by(url_hash=url_hash, priority=priority, status=status).first()
    if url_hash_task_main is not None:
        return url_hash_task_main
    else:
        return False


def delete_old_related_data(url_hash):
    exist_no_service = get_webpages_no_service_data(url_hash)
    if exist_no_service:
        db.session.query(WebpagesNoService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskNoService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return

    exist_partner_xpath = get_webpages_partner_xpath_data(url_hash)
    if exist_partner_xpath:
        db.session.query(WebpagesPartnerXpath).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskNoService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return

    exist_partner_ai = get_webpages_partner_ai_data(url_hash)
    if exist_partner_ai:
        db.session.query(WebpagesPartnerAi).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return

    exist_task_no_service = get_task_no_service_data(url_hash)
    if exist_task_no_service:
        db.session.query(TaskNoService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return

    exist_task_service = get_task_service_data(url_hash)
    if exist_task_service:
        db.session.query(TaskService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return


def create_webpages_xpath_without_data(url, url_hash, domain):
    new_init_webpages = WebpagesPartnerXpath(url=url, url_hash=url_hash, domain=domain)
    pg_add_wrapper(new_init_webpages)


def create_webpages_ai_without_data(url, url_hash, domain):
    new_init_webpages = WebpagesPartnerAi(url=url, url_hash=url_hash, domain=domain)
    pg_add_wrapper(new_init_webpages)


def create_webpages_no_service_without_data(url, url_hash, domain):
    new_init_webpages = WebpagesNoService(url=url, url_hash=url_hash, domain=domain)
    pg_add_wrapper(new_init_webpages)


def create_webpages_xpath_with_data(url, url_hash, domain, title, content, content_hash, author=None, publish_date=None,
                                    cover=None, meta_description=None, content_p=None, len_p=None, len_char=None):
    if publish_date is not None and (type(publish_date) is datetime.date or type(publish_date) is datetime.datetime):
        new_init_webpages = WebpagesPartnerXpath(url=url, url_hash=url_hash, domain=domain, title=title,
                                                 content=content, content_hash=content_hash, author=author, cover=cover,
                                                 meta_description=meta_description, content_p=content_p, len_p=len_p,
                                                 len_char=len_char, publish_date=publish_date)
    else:
        new_init_webpages = WebpagesPartnerXpath(url=url, url_hash=url_hash, domain=domain, title=title,
                                                 content=content, content_hash=content_hash, author=author, cover=cover,
                                                 meta_description=meta_description, content_p=content_p, len_p=len_p,
                                                 len_char=len_char)
    pg_add_wrapper(new_init_webpages)


def update_webpages_for_external(url_hash, title, content, content_hash, author=None, publish_date=None, cover=None,
                                 meta_description=None, content_p=None, len_p=None, len_char=None):
    if publish_date is not None and (type(publish_date) is datetime.date or type(publish_date) is datetime.datetime):
        db.session.query(WebpagesPartnerXpath).filter_by(url_hash=url_hash).update({
            'title': title,
            'content': content,
            'content_hash': content_hash,
            'author': author,
            'publish_date': publish_date,
            'cover': cover,
            'meta_description': meta_description,
            'content_p': content_p,
            'len_p': len_p,
            'len_char': len_char
        })
    else:
        db.session.query(WebpagesPartnerXpath).filter_by(url_hash=url_hash).update({
            'title': title,
            'content': content,
            'content_hash': content_hash,
            'author': author,
            'cover': cover,
            'meta_description': meta_description,
            'content_p': content_p,
            'len_p': len_p,
            'len_char': len_char
        })
    db.session.commit()


def get_webpages_xpath(url_hash):
    webpages_xpath = db.session.query(WebpagesPartnerXpath).filter_by(url_hash=url_hash).first()
    if webpages_xpath is not None:
        return webpages_xpath
    else:
        return False


def get_task_main_tasks(priority, status, limit=4000):
    tasks = TaskMain.query.filter_by(priority=priority, status=status).limit(limit).all()
    if tasks is not None:
        return tasks
    else:
        return False


def update_task_service_multipage(url_hash, is_multipage, page_query_param, status_ai, status_xpath, retry_xpath=0):
    db.session.query(TaskService).filter_by(url_hash=url_hash).update({
        'is_multipage': is_multipage,
        'page_query_param': page_query_param,
        'status_ai': status_ai,
        'status_xpath': status_xpath,
        'retry_xpath': retry_xpath
    })
    db.session.commit()


def get_partner_domain_rules(partner_id, domain):
    rules = DomainInfo.query.filter_by(partner_id=partner_id, domain=domain).first()
    if rules is not None:
        return rules
    else:
        return False


def init_partner_domain_rules(partner_id, domain, rules):
    new_init_rules = DomainInfo(partner_id=partner_id, domain=domain, rules=rules)
    pg_add_wrapper(new_init_rules)


def update_partner_domain_rules(partner_id, domain, rules):
    db.session.query(DomainInfo).filter_by(partner_id=partner_id, domain=domain).update({
        'rules': rules
    })
    db.session.commit()


def get_url_to_content_data(content_hash):
    url_content = UrlToContent.query.filter_by(content_hash=content_hash).first()
    if url_content is not None:
        return url_content
    else:
        return False


def init_url_to_content(url, url_hash, content_hash, request_id, replaced=False):
    new_init_url_content = UrlToContent(url=url, url_hash=url_hash, content_hash=content_hash, request_id=request_id,
                                        replaced=replaced)
    pg_add_wrapper(new_init_url_content)


def update_url_to_content(content_hash, url, url_hash, request_id, replaced):
    db.session.query(UrlToContent).filter_by(content_hash=content_hash).update({
        'url': url,
        'url_hash': url_hash,
        'request_id': request_id,
        'replaced': replaced
    })
    db.session.commit()


def update_webpages_for_xpath(url, url_hash, content_hash, title, content, len_char, content_p, len_p, content_h1,
                              content_h2, content_image, len_img, content_xpath, cover, author, publish_date, meta_jdoc,
                              meta_description, meta_keywords, wp_url, category, categories, multi_page_urls=''):
    db.session.query(WebpagesPartnerXpath).filter_by(url=url, url_hash=url_hash).update({
        'content_hash': content_hash,
        'title': title,
        'content': content,
        'len_char': len_char,
        'content_p': content_p,
        'len_p': len_p,
        'content_h1': content_h1,
        'content_h2': content_h2,
        'content_image': content_image,
        'len_img': len_img,
        'content_xpath': content_xpath,
        'cover': cover,
        'author': author,
        'publish_date': publish_date,
        'meta_jdoc': meta_jdoc,
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'wp_url': wp_url,
        'category': category,
        'categories': categories,
        'multi_page_urls': multi_page_urls
    })
    db.session.commit()


def update_webpages_partner_ai(url_hash, url, content_hash, title, content, meta_jdoc, author=None, cover=None,
                               content_h1=None, content_h2=None, content_p=None, content_image=None, publish_date=None,
                               partner=False):
    if partner is True:
        if publish_date is not None and publish_date != '':
            db.session.query(WebpagesPartnerAi).filter_by(url_hash=url_hash).update({
                'url': url,
                'content_hash': content_hash,
                'title': title,
                'content': content,
                'author': author,
                'meta_jdoc': meta_jdoc,
                'cover': cover,
                'content_h1': content_h1,
                'content_h2': content_h2,
                'content_p': content_p,
                'content_image': content_image,
                'publish_date': publish_date
            })
        else:
            db.session.query(WebpagesPartnerAi).filter_by(url_hash=url_hash).update({
                'url': url,
                'content_hash': content_hash,
                'title': title,
                'content': content,
                'author': author,
                'meta_jdoc': meta_jdoc,
                'cover': cover,
                'content_h1': content_h1,
                'content_h2': content_h2,
                'content_p': content_p,
                'content_image': content_image
            })
    else:
        if publish_date is not None and publish_date != '':
            db.session.query(WebpagesNoService).filter_by(url_hash=url_hash).update({
                'url': url,
                'content_hash': content_hash,
                'title': title,
                'content': content,
                'author': author,
                'meta_jdoc': meta_jdoc,
                'cover': cover,
                'content_h1': content_h1,
                'content_h2': content_h2,
                'content_p': content_p,
                'content_image': content_image,
                'publish_date': publish_date
            })
        else:
            db.session.query(WebpagesNoService).filter_by(url_hash=url_hash).update({
                'url': url,
                'content_hash': content_hash,
                'title': title,
                'content': content,
                'author': author,
                'meta_jdoc': meta_jdoc,
                'cover': cover,
                'content_h1': content_h1,
                'content_h2': content_h2,
                'content_p': content_p,
                'content_image': content_image
            })
    db.session.commit()


def get_executing_tasks(priority, judge_time, limit=10000):
    executing_tasks = TaskMain.query.filter_by(priority=priority).filter(
        db.cast(TaskMain._mtime, db.DateTime) < db.cast(judge_time, db.DateTime),
        or_(TaskMain.status == 'preparing', TaskMain.status == 'doing')).limit(limit).all()

    if executing_tasks is not None:
        return executing_tasks
    else:
        return False


def get_cc_health_check_report(start_time, end_time):
    report_list = db.engine.execute(f'select case when partner_id is null then false else true '
                                    f'end as pbool,priority,status,count(id) from task_main '
                                    f'where _mtime > \'{start_time}\' and _mtime < \'{end_time}\' '
                                    f'group by pbool,priority,status order by pbool desc,priority,status;')
    if report_list is not None:
        return report_list
    else:
        return False
