import logging
from breakarticle.model import db
from breakarticle.helper import pg_add_wrapper
from breakarticle.model.article import UrlInfo, TaskInfo, ServiceInfo
import datetime

# logger_name = "logger_admin"
# logger = logging.getLogger(logger_name)
# logger.debug("message: {}".format(variable))


def init_url_info(url, url_hash, domain):
    new_init_partner = UrlInfo(url=url, url_hash=url_hash, domain=domain)
    pg_add_wrapper(new_init_partner)


def init_sitemap_url_info(url, url_hash, partner_id, domain):
    new_init_partner = UrlInfo(url=url, url_hash=url_hash, partner_id=partner_id, domain=domain)
    pg_add_wrapper(new_init_partner)


def init_task_info(url_hash, notify_status, generator, priority, request_id, task_type):
    if task_type == "sync":
        new_init_task = TaskInfo(url_hash=url_hash, notify_status=notify_status,
                                 generator=generator, request_id=request_id, sync_priority=priority)
    elif task_type == "async":
        new_init_task = TaskInfo(url_hash=url_hash, notify_status=notify_status,
                                 generator=generator, request_id=request_id, async_priority=priority)
    elif task_type == "sitemap":
        new_init_task = TaskInfo(url_hash=url_hash, notify_status=notify_status,
                                 generator=generator, request_id=request_id, others_priority=priority)
    pg_add_wrapper(new_init_task)


def update_partner_id_urlinfo(url_hash, partner_id, url):
    db.session.query(UrlInfo).filter_by(url_hash=url_hash).update({
        'partner_id': partner_id,
        'url': url
    })
    db.session.commit()


def init_service_info(url_hash, service):
    new_init_service = ServiceInfo(url_hash=url_hash, service=service)
    pg_add_wrapper(new_init_service)


def init_sitemap_service_info(url_hash, service, status):
    new_init_service = ServiceInfo(url_hash=url_hash, service=service, status=status)
    pg_add_wrapper(new_init_service)


def exist_url_hash_urlinfo(url_hash):
    url_hash_res_urlinfo = UrlInfo.query.filter_by(url_hash=url_hash).first()
    if url_hash_res_urlinfo is not None:
        return True
    else:
        return False


def update_service_info(url_hash, status, partner_id):
    db.session.query(ServiceInfo).filter_by(url_hash=url_hash).update({
        'partner_id': partner_id,
        'status': status
    })
    db.session.commit()


def exist_url_hash_serviceinfo(url_hash):
    url_hash_res_serviceinfo = ServiceInfo.query.filter_by(url_hash=url_hash).first()
    if url_hash_res_serviceinfo is not None:
        return True
    else:
        return False


def exist_url_hash_taskinfo(url_hash):
    url_hash_res_taskinfo = TaskInfo.query.filter_by(url_hash=url_hash).first()
    if url_hash_res_taskinfo is not None:
        return True
    else:
        return False


def exist_finished_taskinfo(url_hash):
    url_hash_finished_res = TaskInfo.query.filter_by(url_hash=url_hash,  notify_status='finished').first()
    url_hash_pending_res = TaskInfo.query.filter_by(url_hash=url_hash,  notify_status='pending').first()
    if url_hash_finished_res is not None:
        return "finished"
    elif url_hash_pending_res is not None:
        return "pending"


def update_task_info(url_hash, request_id, notify_status, priority, task_type):
    if task_type == "sync":
        db.session.query(TaskInfo).filter_by(url_hash=url_hash).update({
            'notify_status': notify_status,
            'request_id': request_id,
            'sync_priority': priority
        })
    elif task_type == "async":
        db.session.query(TaskInfo).filter_by(url_hash=url_hash).update({
            'request_id': request_id,
            'async_priority': priority
        })
    db.session.commit()


def async_filter_urlinfo():
    current_time = datetime.datetime.utcnow()
    async_judge_day = current_time - datetime.timedelta(days=1)
    update_async_res_list = TaskInfo.query.filter(TaskInfo.async_priority == 2,
                        db.cast(TaskInfo._mtime, db.DATE) > db.cast(async_judge_day, db.DATE)).all()
    if update_async_res_list is not None:
        return update_async_res_list
    else:
        return False


def generate_aysc_info(url_hash):
    url_hash_urlinfo = UrlInfo.query.filter_by(url_hash=url_hash).first()
    url_hash_taskinfo = TaskInfo.query.filter_by(url_hash=url_hash).first()
    if url_hash_urlinfo and url_hash_taskinfo is not None:
        return url_hash_urlinfo, url_hash_taskinfo
    else:
        return False


def check_task_status_to_doing(url_hash):
    check_task_res = TaskInfo.query.filter_by(url_hash=url_hash,  notify_status='pending').first()
    if check_task_res:
        db.session.query(TaskInfo).filter_by(url_hash=url_hash,  notify_status='pending').update({
            'notify_status': "doing"
        })
        db.session.commit()
        return True
    else:
        return False


def main_update_filter_urlinfo():
    current_time = datetime.datetime.utcnow()
    main_judge_day = current_time - datetime.timedelta(days=7)
    update_main_list_res = TaskInfo.query.filter(TaskInfo.others_priority != 5,
                        db.cast(TaskInfo._mtime, db.DATE) > db.cast(main_judge_day, db.DATE)).all()
    if update_main_list_res is not None:
        return update_main_list_res
    else:
        return False
