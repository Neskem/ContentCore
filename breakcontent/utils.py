import jwt
from urllib.parse import unquote
import re
import os
import json
import requests
import sendgrid

from sendgrid.helpers.mail import Email, Content, Mail, Attachment, Personalization
import base64

import logging

from breakcontent.orm_content import get_partner_domain_rules, init_partner_domain_rules, update_partner_domain_rules

logger = logging.getLogger('cc')


def retry_request(method: str, api: str, data: dict = None, headers: dict = None, retry: int = 5):
    method = method.lower()
    while retry:
        try:
            if method == 'put':
                r = requests.put(api, json=data, headers=headers)
            elif method == 'post':
                r = requests.post(api, json=data, headers=headers)
            elif method == 'get':
                r = requests.get(api, json=data, headers=headers)
        except ValueError as e:
            logger.error(f"url_hash {data['url_hash']} {e}")
            retry -= 1
            continue

        if r.status_code == 200:
            return r.json()
        else:
            logger.error(
                f"url_hash {data.get('url_hash', None)} request status code {r.status_code}")
            retry -= 1
            continue

    logger.error(f'failed requesting {api} {retry} times')
    return False


def parse_domain_info(data: dict):
    """
    return: a dict containing domain-specific informaion

    main dict = {
        'status': bool,
        'token': str (e.g. m2OZCcM2yqHYEiDiE8uUARc8lYMa20Dk),
        'message': str (e.g. OK),
        'data': dict
    }

    # 12 keys at most
    data = {
        'xpath': list (e.g. ["//div[@itemprop='articleBody']"]),
        'e_xpath': list,
        'category': list (e.g. ["Alan: Categoty"]),
        'e_category': list,
        'authorList': list (e.g. ["Alan: author"]),
        'e_authorList': list,
        'regex': list of dicts (e.g. [{'type': 'NOT_EQUALS', 'value': '/archives/126204'}, ...]),
        'e_title': list (e.g. [' - 電腦王阿達']),
        'syncDate': list (e.g. ['yyyy/mm/dd']),
        'page': list (e.g. ["d+"]),
        'delayday': list (e.g. ["38"]),
        'sitemap': list (e.g. ["Alan:  Sitemap_String"]),
    }

    terminology:
    xpath = content's xpath
    regex = rules of acceptable url
    e_title = words or chars in the title should be removed
    ...

    --- Logging error ---
    UnicodeEncodeError: 'ascii' codec can't encode characters in position 92-96: ordinal not in range(128)

    print() is fine, but raise Error when logger.debug()

    Best solution:
    change the encoding in logger to 'utf-8'

    solution:
    https://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20
    https://docs.python.org/2.7/howto/unicode.html#the-unicode-type

    vv0 = vv[0].encode('ascii', 'replace')
    vv0 = vv[0].encode('utf-8')
    """

    # if updated must ask Andy!
    optional = [
        'xpath',
        'e_xpath',
        'category',
        'e_category',
        'authorList',
        'e_authorList',
        'regex',
        'e_title',
        'syncDate',
        'page',
        'delayday',
        'sitemap',
    ]

    for k, v in data.items():
        if k == 'data':
            if isinstance(v, list):
                logger.error('it should be a dict')
                return None
            # key check and filter (not sure if necessary)
            # logger.debug(f'type(v) {type(v)}')
            # logger.debug(f'v {v}')
            domain_info = {kk: vv for kk, vv in v.items() if kk in optional}
            # logger.debug(f'filtered domain_info {domain_info}')
            return domain_info
        else:
            continue


def get_domain_info(domain: str, partner_id: str):
    """
    1. get info from db
    2. get info from api

    <note> requires a mechanism to update db when settings changed
    """
    logger.debug('start get_domain_info()...')
    domain_info = get_partner_domain_rules(partner_id=partner_id, domain=domain)
    if domain_info is not False:
        return domain_info.rules
    elif domain_info is False:
        ps_domain_api_prefix = os.environ.get('PS_DOMAIN_API') or 'https://partner.breaktime.com.tw/api/config/'
        ps_domain_api = ps_domain_api_prefix + f'{partner_id}/{domain}/'
        headers = {'Content-Type': "application/json"}

        response = requests.get(ps_domain_api, headers=headers)
        if response.status_code == 200:
            json_resp = json.loads(response.text)
            domain_info = parse_domain_info(json_resp) or None
            rules = get_partner_domain_rules(partner_id, domain)
            if rules is False:
                init_partner_domain_rules(partner_id, domain, domain_info)
            else:
                update_partner_domain_rules(partner_id, domain, domain_info)
            return domain_info
        else:
            logger.error('request failed status {}'.format(response.status_code))
            return None


def request_api(api: str, method: str, payload: dict = None, headers: dict = None):
    """
    a wrapper func for requesting api
    """
    method = method.lower()
    if not headers:
        headers = {'Content-Type': "application/json"}

    if payload:
        resp_data = retry_request(method, api, payload, headers)
    else:
        resp_data = retry_request(method, api, None, headers)
    return resp_data


# ===== below are def from PartnerSync =====


def remove_html_tags(text):
    """Remove html tags from a string"""
    # import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def to_csvstr(data: 'list of tuples'):
    """list of tuples turn into csv str"""
    datastr = ''
    for tp in data:
        ilist = [str(i) for i in tp]
        datastr += '\t'.join(ilist) + '\n'
    return datastr


def construct_email(mailfrom: str, mailto: list, subject: str, content: str, attfilename: str, data: str):
    """
    still intake one mailfrom and one mailto for now

    params:
    mailfrom: an email,
    mailto: an email,
    subject: str,
    data: csv-ready string
    attfilename: filename for attachment
    """
    mail = Mail()

    mail.from_email = Email(mailfrom)

    mail.subject = subject

    mail.add_content(Content("text/html", content))

    personalization = Personalization()
    for i in mailto:
        personalization.add_to(Email(i))
    mail.add_personalization(personalization)

    attachment = Attachment()
    attachment.content = str(base64.b64encode(data.encode('utf-8')), 'utf-8')
    attachment.type = 'text/csv'
    attachment.filename = attfilename
    attachment.disposition = 'attachment'
    mail.add_attachment(attachment)
    return mail


def send_email(mail):
    # dangerous
    SENDGRIDAPIKEY = "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"
    sg = sendgrid.SendGridAPIClient(apikey=SENDGRIDAPIKEY)
    response = sg.client.mail.send.post(request_body=mail.get())
    # print(response)
    print(response.status_code)
    print(response.body)
    print(response.headers)


def decode_url_function(url):
    if type(url) is not str:
        return url
    decode_url = unquote(url)
    if decode_url != url:
        while decode_url != url:
            decode_url, url = unquote(decode_url), decode_url

    return decode_url


def verify_ac_token(token):
    jwt_secret_key = "partneri<3breaktimepartner"
    jwt_authorization_code = "breaktime.com.tw"
    # if token payload has aud, decode must need "audience" key or while happen error.
    try:
        payload = jwt.decode(token, jwt_secret_key, audience='content_core', algorithms=['HS256'])
        if payload and payload["iss"] == jwt_authorization_code:
            return True, payload
        else:
            return False, token
    except Exception as ex:
        logger.error("Can not verify zi token, token: {}, exception: {}".format(token, ex))
        return False, token
