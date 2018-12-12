from flask import Blueprint, request, g
from flask_headers import headers
from flask_cors import cross_origin
from breakcontent.contentclass.orm_content import init_url_info, update_partner_id_urlinfo, init_service_info
from breakcontent.contentclass.orm_content import exist_url_hash_urlinfo, update_service_info, init_task_info
from breakcontent.contentclass.orm_content import exist_url_hash_serviceinfo, exist_url_hash_taskinfo, update_task_info
from breakcontent.contentclass.orm_content import exist_finished_taskinfo
from breakcontent.contentclass.decorators import generate_urlhash_validate_partnerids
from breakcontent.helper import api_ok
import logging
import json

bp = Blueprint('aujs', __name__)


@bp.route('/admin/service/sync', methods=['GET', 'OPTIONS'])
@headers({'Content-Type': 'image/png'})
@cross_origin()
@generate_urlhash_validate_partnerids()
def task_to_sync(url, url_hash, domain, partner_id_list=None):
    """
    Curl testing: curl -X GET "http://localhost:80/v1/admin/service/sync?
        service\_name=Zi_C&status=sync&partner_id=EBFMM18,EBFMM19&url=https://doppelgangerwander.com"
    """
    service_name = request.args.get("service_name", "Zi_C")
    status = request.args.get("status")
    generator = request.args.get('generator', '')
    # priority: 1(blogger trigger), 5(sitemap), 4(scan index page)
    priority = 1

    logging.info("This is new request for syncing content by sync api, url: {}".format(url))
    urlinfo_validate = exist_url_hash_urlinfo(url_hash)
    if urlinfo_validate is False:
        # this url was recorded and in url_info table
        init_url_info(url, url_hash, domain)

    serviceinfo_validate = exist_url_hash_serviceinfo(url_hash)
    if serviceinfo_validate is False and partner_id_list is not None:
        init_service_info(url_hash, service_name)

    if partner_id_list:
        for partner_id in partner_id_list:
            update_partner_id_urlinfo(url_hash, partner_id, url)
            update_service_info(url_hash, status, partner_id)
            logging.info("This partner id: {} is mapping of partner system in sync api.".format(partner_id))

    request_id = g.request_id
    # If task notify_status is doing: Don't recording this request_id and also don't send task to broker.
    notify_status = "doing"
    taskinfo_validate = exist_url_hash_taskinfo(url_hash)
    task_dict = {'request_id': str(request_id), 'partner_id': partner_id_list, 'url_hash': url_hash, 'url': url,
                 'generator': generator, 'priority': priority}
    task_type = "sync"
    if taskinfo_validate:
        taskinfo_finished_validate = exist_finished_taskinfo(url_hash)
        if taskinfo_finished_validate is "finished" or "pending":
            # This task was finished by last time, and need to resend task again.
            update_task_info(url_hash, request_id, notify_status, priority, task_type)
            from breakcontent.tasks import send_task_content_core
            send_task_content_core.delay(task_dict)
    else:
        # The task first trigger
        init_task_info(url_hash, notify_status, generator, priority, request_id, task_type)
        from breakcontent.tasks import send_task_content_core
        # task_result is task hash from celery creation.
        send_task_content_core.delay(task_dict)
    return api_ok("OK")


@bp.route('/admin/service/async', methods=['GET', 'OPTIONS'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@headers({'Content-Type': 'image/png'})
@cross_origin()
@generate_urlhash_validate_partnerids()
def task_to_async(url, url_hash, domain, partner_id_list=None):
    generator = request.args.get('generator', '')
    # priority: 2(was mapping partner), 3(wasn't mapping partner) ..etc
    priority = 3
    notify_status = "pending"

    logging.info("This is new request for syncing content by async api, url: {}".format(url))
    urlinfo_validate = exist_url_hash_urlinfo(url_hash)
    if urlinfo_validate is False:
        init_url_info(url, url_hash, domain)

    request_id = g.request_id
    taskinfo_validate = exist_url_hash_taskinfo(url_hash)
    task_type = "async"

    if partner_id_list:
        priority = 2
        for partner_id in partner_id_list:
            status = "sync"
            update_partner_id_urlinfo(url_hash, partner_id, url)
            update_service_info(url_hash, status, partner_id)
            logging.info("This partner id: {} is mapping of partner system in async api.".format(partner_id))

    if taskinfo_validate:
        update_task_info(url_hash, request_id, notify_status, priority, task_type)
    else:
        init_task_info(url_hash, notify_status, generator, priority, request_id, task_type)

    # Testing schedule beat for sending task to content core from API.
    from breakcontent.tasks import sitemap_update_content
    test_priority = 5
    sitemap_update_content.delay(test_priority)
    return api_ok("OK")
