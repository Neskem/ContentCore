from breakcontent import db
from breakcontent.helper import pg_add_wrapper
from breakcontent.models import TaskMain, WebpagesNoService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, \
    TaskService


def init_task_main(url, url_hash, partner_id, domain, request_id):
    new_init_task = TaskMain(url=url, url_hash=url_hash, partner_id=partner_id, domain=domain, request_id=request_id)
    pg_add_wrapper(new_init_task)


def update_task_main_doing_status(url_hash, status, doing_time, done_time, zi_sync, inform_ac_status):
    db.session.query(TaskMain).filter_by(url_hash).update({
        'status': status,
        'doing_time': doing_time,
        'done_time': done_time,
        'zi_sync': zi_sync,
        'inform_ac_status': inform_ac_status
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


def get_task__service_data(url_hash):
    url_hash_task_service = TaskService.query.filter_by(url_hash=url_hash).first()
    if url_hash_task_service is not None:
        return url_hash_task_service
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

    exist_task_service = get_task__service_data(url_hash)
    if exist_task_service:
        db.session.query(TaskService).filter_by(url_hash=url_hash).delete()
        db.session.query(TaskMain).filter_by(url_hash=url_hash).delete()
        db.session.commit()
        return
