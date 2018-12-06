from functools import wraps
from flask import request
from breakarticle.config import PARTNER_SYSTEM_API
from breakarticle.helper import generate_url_hash
import logging
import requests
import json

logger_name = "logger_admin"
logger = logging.getLogger(logger_name)


def generate_urlhash_validate_partnerids():
    """a naive json validator"""
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            url = request.args.get("url")
            url_hash, pure_url = generate_url_hash(url)
            partner_ids = request.args.get('partner_id').split(',')
            partner_id_list = []
            for partner_id in partner_ids:
                req_url = PARTNER_SYSTEM_API + "/check/service/" + partner_id + "/" + pure_url + "/"
                logger.debug("generate_url_hash_validate_partner_ids, url: {}".format(req_url))
                r = requests.get(req_url)
                if r.status_code == 200:
                    json_resp = json.loads(r.text)
                    partner_service = json_resp['service']
                    if 'ZIC' in partner_service:
                        partner_id_list.append(partner_id)
                else:
                    logger.debug("Can't connect to partner sysyem API for checking partner or not, partner_id: {}".format(partner_id))
            kwargs['partner_id_list'] = partner_id_list
            kwargs['url'] = url
            kwargs['url_hash'] = url_hash
            kwargs['domain'] = pure_url
            return func(*args, **kwargs)
        return wrapped_func
    return decorator
