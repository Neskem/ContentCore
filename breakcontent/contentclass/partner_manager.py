import logging
import requests
import json
from breakcontent.config import PARTNER_SYSTEM_API
from breakcontent.exceptions import BreakPartnerError

logger_name = "logger_admin"
logger = logging.getLogger(logger_name)


def get_sitemap_url():
  try:
    req_url = PARTNER_SYSTEM_API + "/sitemap/"
    logger.debug(
        "generate_url_hash_validate_partner_ids, url: {}".format(req_url))
    r = requests.get(req_url)
    if r.status_code == 200:
      json_resp = json.loads(r.text)
      sitemap_data_list = json_resp['data']
      logger.debug(
          "generate_url_hash_validate_partner_ids, json_resp: {}".format(json_resp))
      return sitemap_data_list
  except:
    logger.debug(
        "Can't search  sitemap url list from partner system or system has happen error.")
    raise BreakPartnerError
