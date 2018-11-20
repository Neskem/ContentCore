from flask import Blueprint, request, g
from flask_headers import headers
from flask_cors import cross_origin
from breakarticle.articleclass.partner_manager import PartnerSetting

import logging
import re
from urllib.parse import urlparse
from breakarticle.helper import api_ok

bp = Blueprint('aujs', __name__)


@bp.route('/admin/service/sync', methods=['GET', 'OPTIONS'])
@headers({'Content-Type': 'image/png'})
@cross_origin()
def task_to_service():
    partner_ids = request.args.get('partner_id').split(',')
    for partner_id in partner_ids:
        partner_obj = PartnerSetting(partner_id)
        with partner_obj:
            partner_res = partner_obj.validate_partner()
            if partner_res:
                website_id_res = partner_obj.get_website_id()
                logging.info("website_id_res: {}".format(website_id_res))
                partner_config_res = partner_obj.get_partner_config(website_id_res)
        logging.info("Partner id: {}, and this partner id is partner or not: {}".format(partner_id, partner_res))

    service_name = request.args.get("service_name", "Zi_C")
    status = request.args.get("status")
    url = request.args.get("url")
    generator = request.args.get('generator', '')
    return api_ok("OK")
