import re
import jwt
from urllib.parse import unquote, urlparse
# from breakcontent.tasks import logger
from sqlalchemy.orm import load_only
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError, DatabaseError
from breakcontent import db
from breakcontent.config import MERCURY_PATH
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo

from Naked.toolshed.shell import execute_js, muterun_js
from flask import current_app
from urllib.parse import urlencode, quote_plus, unquote, quote, unquote_plus, parse_qs
from urllib.parse import urlparse, urljoin
import requests
import time
from lxml import etree
import lxml.html
import xml.etree.ElementTree as ET
import time
import re
import dateparser
from html import unescape
from datetime import datetime, timedelta
import datetime as dt
import hashlib
import base64
import calendar
import os
import json
import requests
import sendgrid

from sendgrid.helpers.mail import Email, Content, Mail, Attachment, Personalization
import base64

import logging
logger = logging.getLogger('cc')

class Secret():

    def __init__(self, secret: bool=False, domain: str=None, bsp: str=None):
        self.secret = secret
        self.domain = domain
        self.bsp = bsp  # pixnet, xuite, wordpress, ...

    def to_dict(self):
        return {
            'secret': self.secret,
            'domain': self.domain,
            'bsp': self.bsp
        }


class InformAC():
    '''
    record all the attrs required to inform AC
    '''
    data = {
        'url_hash': None,
        'parent_url': None,
        'url': None,
        'old_url_hash': None,  # yet
        'content_update': None,  # yet
        'request_id': None,
        'publish_date': None,
        'url_structure_type': None,  # yet
        'secret': False,
        'has_page_code': None,
        'quality': None,
        'zi_sync': True,
        'zi_defy': set(),
        'status': True,
        'skip_crawler': None
    }

    def __init__(self):
        for k, v in self.data.items():
            setattr(self, k, v)

    def to_dict(self):

        data = {
            'url_hash': self.url_hash,
            'parent_url': self.parent_url,  # yet
            'url': self.url,
            'old_url_hash': self.old_url_hash,  # todo
            'content_update': self.content_update,  # done
            'request_id': self.request_id,
            'publish_date': str(self.publish_date) if self.publish_date is not None else None,  # for JSON transfer
            'url_structure_type': self.url_structure_type,  # yet
            'secret': self.secret,
            'has_page_code': self.has_page_code,
            'quality': self.quality,
            'zi_sync': self.zi_sync,
            'zi_defy': list(self.zi_defy) if self.zi_defy else [],
            'status': self.status
        }

        if data['zi_sync']:
            data.pop('zi_defy')

        return data

    def check_content_hash(self, wp: object):
        '''
        1. search for content_hash and url_hash
        2. if not exists, insert
        3. if exists, update
        4. delete the old_url_hash related docs in db
        '''
        logger.debug(f'run check_content_hash() on url_hash {wp.url_hash}')
        if not wp.url_hash or not wp.content_hash:
            logger.debug(f'wp.url_hash {wp.url_hash}, wp.content_hash {wp.content_hash}')
            return

        q = {
            'url_hash': wp.url_hash,
            'content_hash': wp.content_hash
        }
        idata = {
            'request_id': self.request_id,
            'url_hash': wp.url_hash,
            'domain': wp.domain,
            'url': wp.url,
            'content_hash': wp.content_hash,
            'replaced': False,
        }
        uc = UrlToContent()
        uc.upsert(q, idata)
        # doc = UrlToContent().select(q)
        # logger.debug(f'doc {doc}')
        # if doc:
        #     logger.debug('do update')
        #     # update
        #     # db_session_update(UrlToContent, q, idata)
        #     doc.update(q, idata)
        # else:
        #     logger.debug('do insert')
        #     # insert
        #     doc = UrlToContent()
        #     # db_session_insert(u2c)
        #     doc.upsert(q, idata)

        q = dict(content_hash=wp.content_hash)
        # query out the previous url_hash with the same content_hash
        doc_list = UrlToContent.query.options(load_only('url_hash', 'replaced')).filter_by(**q).filter(
            UrlToContent.url_hash != self.url_hash).all()

        for i, doc in enumerate(doc_list):
            logger.debug(f'doc.url_hash {doc.url_hash}')
            if i == 0 and doc.replaced is False:
                self.old_url_hash = doc.url_hash

            if i > 0:
                # only keep 2 url_hash for each content_hash
                doc.delete(doc)


class DomainSetting():

    data = {
        'xpath': None,
        'e_xpath': None,
        'category': None,
        'e_category': None,
        'authorList': None,
        'e_authorList': None,
        'regex': None,
        'e_title': None,
        'syncDate': None,
        'page': None,
        'delayday': None,
        'sitemap': None
    }

    def __init__(self, *initial_data, **kwargs):
        for k, v in self.data.items():
            setattr(self, k, v)
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def to_dict(self):
        return {
            'xpath': self.xpath,
            'e_xpath': self.e_xpath,
            'category': self.category,
            'e_category': self.e_category,
            'authorList': self.authorList,
            'e_authorList': self.e_authorList,
            'regex': self.regex,
            'e_title': self.e_title,
            'syncDate': self.syncDate,
            'page': self.page,
            'delayday': self.delayday,
            # 'sitemap': self.sitemap
        }

    def isSyncCategory(self, categories: list) -> bool:
        if self.e_category and len(self.e_category) > 0:
            for cat in categories:
                if cat in self.e_category:
                    return False
        if self.category and len(self.category) > 0:
            for category in categories:
                if category in self.category:
                    print("white category sync!!")
                    return True
            print("only white category sync!!")
            return False
        else:
            return True

    def isSyncAuthor(self, author: list) -> bool:
        if self.e_authorList and author in self.e_authorList:
            return False
        if self.authorList and len(self.authorList) > 0:
            print("only white authors sync!!")
            if author in self.authorList:
                return True
            else:
                return False
        else:
            return True

    # staticmethod or classmethod, not exposed to outside world
    def checkUrl(self, url, rule: dict):
        o = urlparse(url)
        url = o.path
        if o.query != "":
            url = url + '?' + o.query
        if o.fragment != "":
            url = url + "#" + o.fragment

        match_type, match_string = rule['type'], unquote(rule['value'])
        if match_type == 'EQUALS' and match_string == url:
            return True
        if match_type == 'NOT_EQUALS' and match_string == url:
            return False
        my_regex = match_string
        if match_type == 'MATCH_REGEX' and re.search(my_regex, url) != None:
            return True
        if match_type == 'NOT_MATCH_REGEX' and re.search(my_regex, url):
            return False
        if match_type == 'MATCH_REGEX_I' and re.search(my_regex, url, re.IGNORECASE):
            return True
        if match_type == 'NOT_MATCH_REGEX_I' and re.search(my_regex, url, re.IGNORECASE):
            return False
        return None

    def checkSyncRule(self, url):
        logger.debug(f'url {url}, starting checkSyncRule()')

        # Paul reported that black list should has the highest priority
        black_rules = ['NOT_EQUALS', 'NOT_MATCH_REGEX', 'NOT_MATCH_REGEX_I']
        if self.regex and len(self.regex) > 0:
            # list of dict
            # 1. scan through black rules first
            for rule in self.regex:
                if rule['type'] in black_rules:
                    status = self.checkUrl(url, rule)
                    if status is False:
                        logger.debug(f'url {url}: rule {rule}, status {status}')
                        return False
            # 2. scan through white rules next
            for rule in self.regex:
                if rule['type'] not in black_rules:
                    status = self.checkUrl(url, rule)
                    if status is True:
                        logger.debug(f'url {url}: rule {rule}, status {status}')
                        return True

        return False

    def isSyncDay(self, publish_date: object):
        '''
        check if the published_date violates the delayday
        '''
        logger.debug(f'publish_date {publish_date}')
        logger.debug(f'type(publish_date) {type(publish_date)}')

        delayday = int(self.delayday[0]) if self.delayday else 0
        logger.debug(f'delayday {delayday}')
        delaydt = publish_date + timedelta(days=delayday)
        ddt = delaydt.replace(tzinfo=dt.timezone(dt.timedelta(hours=0)))
        '''
        # TypeError: can't compare offset-naive and offset-aware datetimes

        https://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes
        https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow

        delaydt 2019-02-03 21:28:00+00:00
        datetime.utcnow() 2019-02-23 08:12:37.602162
        '''
        now = datetime.utcnow() + timedelta(hours=8)
        now = now.replace(tzinfo=dt.timezone(dt.timedelta(hours=0)))
        logger.debug(f'ddt {ddt}')
        logger.debug(f'now {now}')

        if ddt < now:
            return True
        else:
            return False

    def checkQuality(self):
        '''
        Strickly speaking, this func should not be under this class. Only for handy purpose.
        '''
        pass


def retry_request(method: str, api: str, data: dict=None, headers: dict=None, retry: int=5):

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


def parse_domain_info(data: dict) -> dict:
    '''
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
    '''

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
            domain_info = {kk: vv for kk,
                           vv in v.items() if kk in optional}
            # logger.debug(f'filtered domain_info {domain_info}')
            return domain_info
        else:
            continue


def get_domain_info(domain: str, partner_id: str) -> dict:
    '''
    1. get info from db
    2. get info from api

    <note> requires a mechanism to update db when settings changed
    '''
    logger.debug('start get_domain_info()...')
    q = dict(domain=domain, partner_id=partner_id)
    di = DomainInfo().select(q)
    if di:
        # 1. get domain info from db
        domain_info = di.rules
        return domain_info
    elif not di:
        # 2. get domain info from api
        ps_domain_api_prefix = os.environ.get(
            'PS_DOMAIN_API') or 'https://partner.breaktime.com.tw/api/config/'
        ps_domain_api = ps_domain_api_prefix + f'{partner_id}/{domain}/'
        headers = {'Content-Type': "application/json"}

        r = requests.get(ps_domain_api, headers=headers)
        if r.status_code == 200:
            json_resp = json.loads(r.text)
            domain_info = parse_domain_info(json_resp) or None
            # if not exist in DomainInfo insert
            idata = dict(domain=domain, partner_id=partner_id,
                         rules=domain_info)
            doc = DomainInfo()
            doc.upsert(q, idata)
            return domain_info
        else:
            logger.error(f'request failed status {r.status_code}')
            return None


def db_session_insert(doc: object):
    '''
    handle insert

    to avoid OperationalError, redo with loop

    IntegrityError was handled elsewhere
    '''
    retry = 0
    while 1:
        try:
            db.session.add(doc)
            db.session.commit()
            logger.debug('insert successful')
            return True
        except OperationalError as e:
            db.session.rollback()
            if retry > 5:
                logger.error(f'{e}: retry {retry}')
                logger.debug('usually this should not happen')
                return False
                # raise
                # break
            retry += 1


def db_session_update(table: object, query: dict, data: dict):
    '''
    handle update retry
    '''
    retry = 0
    while 1:
        try:
            logger.debug(f'data {data}')
            table.query.filter_by(**query).update(data)
            db.session.commit()
            logger.debug('update successful')
            break
        except OperationalError as e:
            logger.error(e)
            db.session.rollback()
            if retry > 5:
                logger.error(f'{e}: retry {retry}')
                logger.debug('usually this should not happen')
                raise
                # break
            retry += 1


def db_session_query(table: object, query: dict, order_by: 'column name'=None, asc: bool=True, limit: int=None) -> 'a object or list of objects':
    '''
    return a table record object
    '''
    retry = 0
    while 1:
        try:
            # logger.debug(f'order_by {order_by}')
            # logger.debug(f'limit {limit}')
            if order_by and limit:
                if asc:
                    docs = table.query.filter_by(
                        **query).order_by(order_by.asc()).limit(limit).all()
                else:
                    docs = table.query.filter_by(
                        **query).order_by(order_by.desc()).limit(limit).all()
                logger.debug('query many record successful')
                return docs
            else:
                doc = table.query.filter_by(**query).first()
                logger.debug('query a record successful')
                return doc
            # break
        except OperationalError as e:
            retry += 1
            db.session.rollback()
            if retry > 5:
                logger.error(f'{e}, retry {retry}')
                raise
        except DatabaseError as e:
            retry += 1
            db.session.rollback()
            logger.error(e)
            if retry > 5:
                logger.error(f'{e}, retry {retry}')
                raise


def prepare_crawler(url_hash: str, partner: bool=False, xpath: bool=False):
    '''
    init record in WebpagesPartnerXpath for singlepage or multipage crawler, so the fk will be linked to TaskService and the pk will be created.

    <return>
    a WebpagesPartnerXpath dict
    or
    a WebpagesPartnerAi dict
    or
    a WebpagesNoService dict
    '''
    logger.debug('start prepare_crawler()...')
    q = dict(url_hash=url_hash)

    if partner:
        ts = TaskService().select(q)
    else:
        ts = TaskNoService().select(q)

    tm = TaskMain()
    if not ts:
        # this will cause the task be hanging at status 'preparing'
        logger.error(f'url_hash {url_hash} this usually should not happen!')
        tm.update(q, dict(status='failed'))
        return None

    tm.update(q, dict(status='doing'))

    udata = {
        'url_hash': ts.url_hash,
        'url': ts.url,  # should url be updated here?
    }
    if partner and xpath:
        ts.status_xpath = 'doing'
        ts.commit()
        wpx = WebpagesPartnerXpath()
        udata['task_service_id'] = ts.id
        wpx.upsert(q, udata)
        # wp_data = ts.webpages_partner_xpath.to_inform()
        # wp_data['generator'] = ts.task_main.generator
        # logger.debug(f'wp_data {wp_data}')
        # return wp_data

    elif partner and not xpath:
        # prepare for ai crawler
        ts.status_ai = 'doing'
        ts.commit()
        wpa = WebpagesPartnerAi()
        udata['task_service_id'] = ts.id
        wpa.upsert(q, udata)
        # wp_data = ts.webpages_partner_ai.to_inform()
        # wp_data['generator'] = ts.task_main.generator
        # logger.debug(f'wp_data {wp_data}')
        # return wp_data

    elif not partner:
        # prepare for ai crawler
        ts.status = 'doing'
        ts.commit()
        wns = WebpagesNoService()
        udata['task_noservice_id'] = ts.id
        wns.upsert(q, udata)
        # wp_data = ts.webpages_noservice.to_inform() # if the tm-ts relation was bound to another one this will fail
        # wp_data['generator'] = ts.task_main.generator
        # logger.debug(f'wp_data {wp_data}')
        # return wp_data


def check_r(r: 'response', ts: object=None):
    if ts:
        ts.status_code = r.status_code
        db.session.commit()
        logger.debug(f'url_hash {ts.url_hash} status_code {r.status_code}')
    if r.status_code == 200:
        return True
    else:
        # logger.warning(f'url_hash {ts.url_hash} status_code {r.status_code}')
        return False


def xpath_a_crawler(url_hash: str, url: str, partner_id: str, domain: str, domain_info: dict, multipaged: bool=False, timeout: int=6) -> (object, object):
    """
    note: this is not a celery task function

    use xpath to crawl a page

    <arguments>
    wpx,
    partner_id,
    domain,
    domain_info, dict

    <return>
    (obj1, obj2)
    obj1, a WebpagesPartnerXpath instance
    obj2, an InformAC instance

    """
    logger.debug(f'url_hash {url_hash}, run the basic unit of xpath crawler.')
    q = dict(url_hash=url_hash)
    tm = TaskMain().select(q)

    # task_service_id = wpx['task_service_id']
    ts = TaskService().select(q)
    priority = tm.priority

    ds = DomainSetting(domain_info)

    # required, some previous data will be brought in for comparison use
    if multipaged:
        a_wpx = WebpagesPartnerXpath()
    else:
        a_wpx = WebpagesPartnerXpath.query.options(load_only('url_hash', 'content_hash')).filter_by(**q).first()
        a_wpx.task_service_id = ts.id
    a_wpx.domain = domain

    iac = InformAC()
    iac.url_hash = url_hash
    iac.url = url
    iac.request_id = tm.request_id

    generator = tm.generator

    secrt = Secret()

    check_rule = None
    if priority == 1:
        logger.info(f'url_hash {url_hash}, sync rule check is skipped for p1 tasks')
        check_rule = True
    else:
        check_rule = ds.checkSyncRule(url)
    logger.debug(f'url_hash {url_hash}, check_rule {check_rule}')
    iac.zi_sync = check_rule if iac.zi_sync else False
    if check_rule is False:
        iac.zi_defy.add('regex')

    # below are prepartion for request
    html = None
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

    if multipaged or priority == 5:
        timeout = 12

        crawlera_apikey = os.environ.get('CRAWLERA_APIKEY', None)
        candidate = [
            'www.top1health.com'
        ]

        if crawlera_apikey and (domain in candidate or priority == 5):
            proxies = {
                'http': f"http://{crawlera_apikey}:x@proxy.crawlera.com:8010/",
                'https': f"https://{crawlera_apikey}:x@proxy.crawlera.com:8010/"
            }
            r = requests.get(url, allow_redirects=False,
                             headers=headers, proxies=proxies, verify=False, timeout=timeout)

            if check_r(r):
                logger.debug(f'url_hash {url_hash}, CRAWLERA reqeust successful')
            else:
                logger.warning(f'url_hash {url_hash}, CRAWLERA request failed, try local')
                # don't use crawlera if failed at once
                r = requests.get(url, allow_redirects=False, headers=headers, timeout=timeout)
        else:
            logger.debug(f'url_hash {url_hash}, use local to request')
            r = requests.get(url, allow_redirects=False, headers=headers, timeout=timeout)

        if url != r.url:
            logger.warning(f'url_hash {url_hash}, url {url} != r.url {r.url}, exit crawler.')
            iac.status = False
            return a_wpx, iac

    else:
        r = requests.get(url, verify=False, allow_redirects=False, headers=headers, timeout=timeout)

    ts = ts if not multipaged else None
    if check_r(r, ts):
        r.encoding = 'utf-8'
        html = r.text
        content = None
        cd = None
        category = None
        # url = None
        wp_url = None

        tStart = time.time()
        try:
            aujs = (
                re.search(r'a.breaktime.com.tw\/js\/au.js\?spj', str(html)).span())
        except AttributeError as e:
            # AttributeError: 'NoneType' object has no attribute 'span'
            logger.warning(f'url_hash {url_hash}, aujs exception: {e}')
            aujs = False

        logger.debug(f'url_hash {url_hash}, aujs {aujs}')

        if aujs:
            iac.has_page_code = True
        else:
            pass
        tEnd = time.time()
        logger.debug(f"url_hash {url_hash}, scanning aujs cost {tEnd - tStart} sec")

        try:
            tree = lxml.html.fromstring(html)
        except ValueError as e:
            logger.error(f'url_hash {url_hash}, tree xml exception: {e}')
            iac.status = False
            return a_wpx, iac

        match_xpath = None

        # ----- check if content_xpath can be matched, parsing canonical url ----
        for xpath in ds.xpath:
            xpath = unquote(xpath)
            cd = tree.xpath(xpath)  # content directory
            if len(cd) > 0:
                match_xpath = xpath
                logger.info(f'url_hash {url_hash}, match xpath: {xpath}')

                if 0:
                    # this block ready to be deprecated
                    x_canonical_url = tree.xpath(
                        '/html/head/link[@rel="canonical"]')
                    if len(x_canonical_url) > 0:
                        url = x_canonical_url[0].get('href')
                    else:
                        x_og_url = tree.xpath(
                            '/html/head/meta[@property="og:url"]')
                        if len(x_og_url):
                            url = x_og_url[0].get('content')
                        else:
                            # url = a_wpx['url']
                            pass
                break

        # ----- parsing content ----
        if match_xpath != None:
            a_wpx.content_xpath = match_xpath
            logger.debug(f"url_hash {url_hash}, xpath matched!")

            # ----- parsing meta ----
            metas = tree.xpath('//meta')
            meta_all = {}
            for meta in metas:
                meta_name = None
                if meta.get('name', None):
                    meta_name = meta.get('name', None)
                if meta.get('property', None):
                    meta_name = meta.get('property', None)
                if meta.get('itemprop', None):
                    meta_name = meta.get('itemprop', None)

                if meta_name:
                    meta_name = re.sub('[.$]', '', meta_name)
                    if meta_name not in meta_all:
                        meta_all[meta_name] = []
                    meta_all[meta_name].append(meta.get('content', None))
            a_wpx.meta_jdoc = meta_all

            if "webtest1.sanlih.com.tw" in url or "www.setn.com" in url:
                iac.zi_sync = False
                if 'auth' in meta_all.keys():
                    if meta_all['auth'][0] == "1":
                        iac.zi_sync = True

            # ----- parsing images ----
            ximage = cd[0].xpath('.//img')
            len_img = len(ximage)
            content_image = ''
            for image in ximage:
                if image.get('data-pagespeed-lazy-src', None) != None:
                    image.set('src', image.get('data-pagespeed-lazy-src'))
                if image.get('data-lazy-src', None) != None:
                    image.set('src', image.get('data-lazy-src'))
                if image.get('data-original', None) != None:
                    image.set('src', image.get('data-original'))
                if image.get('data-src', None) != None:
                    image.set('src', image.get('data-src'))

                src = image.get('src')
                if src != None and src.strip():
                    alt = image.get('alt')
                    src = urljoin(url, src)
                    try:
                        image.set('src', src)
                    except ValueError as e:
                        logger.error(f'url {url}')
                        logger.error(f'url_hash {url_hash}, image: {image} ValueError.')
                        logger.error(f'url_hash {url_hash}, src {src}')
                        logger.error(f'url_hash {url_hash}, set image ValueError exception: {e}')
                    content_image += f'<img src=\"{src}\" alt=\"{alt}\">'
            # domain specifc logic
            try:
                if "www.iphonetaiwan.org" in url and len(ximage) > 0:
                    present_image = ximage[0].get('src')
            except TypeError as e:
                logger.error(f'url_hash {url_hash}, ximage TypeError exception: {e}')
                logger.error(f'url_hash {url_hash}, url {url} ximage {ximage}')
                raise e

            a_wpx.content_image = content_image
            a_wpx.len_img = len_img
            # ----- parsing present_image ----
            present_image = None
            cover = None
            x_og_images = tree.xpath('/html/head/meta[@property="og:image"]')
            if len(x_og_images) > 0:
                present_image = x_og_images[0].get('content')
                logger.debug(f'url_hash {url_hash}, present_image: {present_image}')

            if present_image:
                present_image = urljoin(url, present_image)
                cover = present_image

            if present_image:
                if len_img == 0 or "thebetteraging.businesstoday.com.tw" in url:
                    logger.debug(f'url_hash {url_hash}, code block here is weird!')
                    h_img = etree.Element('img', src=present_image)
                    cd[0].insert(0, h_img)

            a_wpx.cover = cover
            # ----- removing script ----
            for script in cd[0].xpath("//noscript"):
                logger.debug(f'url_hash {url_hash}, script.text {script.text}')
                script.getparent().remove(script)

            # ----- parsing generator ----
            if not generator:
                x_generator = tree.xpath('/html/head/meta[@name="generator"]')
                if len(x_generator) > 0:
                    generator = x_generator[0].get('content')
            # ----- parsing wp_url ----
            wp_url = None
            x_shortlink = tree.xpath('//link[@rel="shortlink"]/@href')
            if len(x_shortlink) > 0:
                if generator != None and re.search('wordpress', generator, re.I):
                    wp_url = getWpRealLink(url, x_shortlink[0])
            a_wpx.wp_url = wp_url
            # ----- parsing categories ----
            category = None
            categories = []
            # domain specific logic
            if category == None and "thebetteraging.businesstoday.com.tw" in url:
                x_categories = tree.xpath(
                    '//span[contains(@class, "service-type")]/text()')
                x_cat = x_categories[0].replace('分類：', '')
                categories.append(x_cat)
            # bsp specific logic: pixnet
            if category == None and generator == "PChoc":
                g_x_categories = tree.xpath(
                    '//ul[@class="refer"]/li[1]/a/text()')

                logger.debug(f'url_hash {url_hash}, g_x_categories {g_x_categories}')
                logger.debug(f'url_hash {url_hash}, type(g_x_categories) {type(g_x_categories)}')
                # if len(g_x_categories)
                if len(g_x_categories) > 0:
                    category = g_x_categories[0]
                    categories += g_x_categories
                    x_categories = tree.xpath(
                        '//ul[@class="refer"]/li[2]/a/text()')
                    if len(x_categories) > 0:
                        logger.debug(f'url_hash {url_hash}, x_categories[0] {x_categories[0]}')
                        logger.debug(
                            f'url_hash {url_hash}, type(x_categories[0]) {type(x_categories[0])}')
                        logger.debug(
                            f'url_hash {url_hash}, dir(x_categories[0]) {dir(x_categories[0])}')

            # universal logic
            if category == None:
                x_categories = tree.xpath(
                    '/html/head/meta[@property="article:section"]')
                if len(x_categories) > 0:
                    category = x_categories[0].get('content')
                    for c in x_categories:
                        if c.get('content') not in categories:
                            categories.append(c.get('content'))

            # check if category should sync
            isc = ds.isSyncCategory(categories)
            iac.zi_sync = isc if iac.zi_sync else False
            if not isc:
                iac.zi_defy.add('category')

            a_wpx.category = category
            a_wpx.categories = categories
            # ----- parsing content_h1 ----
            content_h1 = ''
            xh1 = tree.xpath('//h1/text()')
            for h1 in xh1:
                if h1.strip():
                    content_h1 += '<h1>{}</h1>'.format(h1)
            a_wpx.content_h1 = content_h1
            # ----- parsing content_h2 ----
            content_h2 = ''
            xh2 = tree.xpath('//h2/text()')
            for h2 in xh2:
                if h2.strip():
                    content_h2 += '<h2>{}</h2>'.format(h2)
            a_wpx.content_h2 = content_h2
            # ----- parsing content_p ----
            content_p = ''
            len_p = 0
            content = etree.tostring(
                cd[0], pretty_print=True, method='html').decode("utf-8")
            content = unquote(content)
            cd[0] = lxml.html.fromstring(content)
            xp = cd[0].xpath('.//p')
            len_xp = len(xp)
            for p in xp:
                txt = remove_html_tags(etree.tostring(
                    p, pretty_print=True, method='html').decode("utf-8"))
                s = unescape(txt.strip())
                if s.strip():
                    content_p += '<p>{}</p>'.format(s)
                    len_p = len_p + 1
            a_wpx.content_p = content_p
            a_wpx.len_p = len_p
            # ----- parsing secret ----
            password_check_forms = cd[0].xpath(
                "//form[contains(@class, 'post-password-form')]")
            if len(password_check_forms) > 0:
                logger.debug('this is a secret article w/ password lock')
                secrt.secret = True
                iac.secret = True
                iac.zi_sync = False
                iac.zi_defy.add('secret')
            logger.debug(f'url_hash {url_hash}, secrt.to_dict() {secrt.to_dict()}')
            # ----- parsing href (what for?) ----
            # reformating href?
            xarch = cd[0].xpath('.//a')
            for a in xarch:
                try:
                    href = a.get('href')
                    if href != None and href.strip():
                        href = urljoin(url, href)
                        try:
                            a.set('href', str(href))
                        except:
                            pass
                except:
                    pass
            logger.debug(f'url_hash {url_hash}, xarch {xarch}')
            # ----- parsing iframe ----
            # reformating
            xiframe = cd[0].xpath('//iframe')
            for iframe in xiframe:
                src = iframe.get('src')
                if src != None and src.strip():
                    alt = iframe.get('alt')
                    src = urljoin(url, src)
                    # domain spefic logic
                    if domain == "medium.com":
                        src = getMediumIframeSource(src)
                    iframe.set('src', src)

            # ----- parsing publish_date ----

            publish_date = None
            x_publish_date = tree.xpath(
                '/html/head/meta[@property="article:published_time"]')
            if len(x_publish_date) > 0:
                publish_date = x_publish_date[0].get('content')
            else:
                data_blocks = tree.xpath(
                    '//script[@type="application/ld+json"]/text()')
                logger.debug(f'url_hash {url_hash}, data_blocks {data_blocks}')
                for data_block in data_blocks:
                    try:
                        data = json.loads(data_block)
                        if "datePublished" in data:
                            publish_date = data.get("datePublished")
                            break
                    except Exception as e:
                        logger.error(f'url_hash {url_hash}, datePublished data_block exception: {e}')
                        data_block = str(data_block).replace(
                            '[', '').replace(',]', '')
                        logger.debug(f'url_hash {url_hash}, data_block {data_block}')
                        data = json.dumps(data_block)
                        data = json.loads(data)
                        if "datePublished" in data:
                            try:
                                publish_date = data.get("datePublished")
                            except AttributeError as e:
                                logger.error(f'url_hash {url_hash}, datePublished AttributeError exception: {e}')
                                logger.debug(
                                    f'url_hash {url_hash}, data {data}')
                                publish_date = None
                            break

            # domain specific logic
            if publish_date == None and "blogspot.com" in url:
                published_dates = tree.xpath(
                    '//abbr[@itemprop="datePublished"]')
                if len(published_dates) > 0:
                    publish_date = published_dates[0].get("title")

            if publish_date == None and domain == "momo.foxpro.com.tw":
                try:
                    s = re.search(r'^(\d{4}).(\d{2}).(\d{2})', title)
                    year = s.group(1)
                    month = s.group(2)
                    day = s.group(3)
                    publish_date = f'{year}-{month}-{day}'
                except:
                    pass

            if publish_date == None and "blog.udn.com" in url:
                publish_date = getUdnPublishTime(tree)

            if publish_date == None and "kangaroo5118.nidbox.com" in url:
                publish_date = getkangaroo5118Time(tree)

            if publish_date == None and "bonbg.com" in url:
                x_publish_dates = tree.xpath(
                    '//span[@class="meta_date"]/text()')
                if len(x_publish_dates) > 0:
                    publish_date = dateparser.parse(x_publish_dates[0])

            if publish_date == None and "thebetteraging.businesstoday.com.tw" in url:
                published_dates = tree.xpath(
                    '//span[contains(@class, "date")]/text()')
                if len(published_dates) > 0:
                    publish_date = published_dates[0].replace('日期：', '')
                    if publish_date == None:
                        groups = re.match(
                            r'(\d+)年(\d+)月(\d+)日', published_dates[0])
                        publish_date = "{}-{:02d}-{:02d}".format(
                            int(groups[1]), int(groups[2]), int(groups[3]))
            if publish_date == None and "iphone4.tw" in url:
                published_dates = tree.xpath('//span[@class="date"]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
            if publish_date == None and "imreadygo.com" in url:
                published_dates = tree.xpath(
                    '//div[@class="newsmag-date"]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])

            if publish_date == None and "jct.tw" in url:
                published_dates = tree.xpath(
                    '//h1/following-sibling::div[1]/text()')
                # print(x_author)
                if len(published_dates) > 0:
                    publish_date = published_dates[0].strip(
                    ).replace("文章日期 : ", "").strip()
                    publish_date = dateparser.parse(publish_date)

            if publish_date == None and "www.amplframe.com" in url:
                published_dates = tree.xpath(
                    '/html/body/div[1]/div[3]/div/div/div/ul/li[2]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])

            # bsp specific logic
            if publish_date == None and generator == "PChoc":
                publish_date = getPixnetPublishTime(tree)

            # universal logic
            if publish_date == None:
                published_dates = tree.xpath(
                    '//abbr[contains(@class, "published")]')
                if len(published_dates) > 0:
                    publish_date = published_dates[0].get("title")

            if publish_date == None:
                published_dates = tree.xpath(
                    '//time[contains(@class, "published")]')
                if len(published_dates) > 0:
                    publish_date = published_dates[0].get("datetime")

            if publish_date == None:
                published_dates = tree.xpath(
                    '//span[contains(@class, "thetime")][1]/text()')
                if len(published_dates) > 0:
                    publish_date = published_dates[0]

            if publish_date == None:
                published_dates = tree.xpath(
                    '//h4[@class="post-section__text"][2]/text()')
                if len(published_dates) > 0:
                    publish_date = published_dates[0]

            if publish_date == None:
                published_dates = tree.xpath(
                    '//h2[contains(@class, "date-header")]/span/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
                    if publish_date == None:
                        groups = re.match(
                            r'(\d+)年(\d+)月(\d+)日', published_dates[0])
                        publish_date = "{}-{:02d}-{:02d}".format(
                            int(groups[1]), int(groups[2]), int(groups[3]))

            if publish_date == None:
                xpublish_date = tree.xpath('//*[@itemprop="datePublished"]')
                if len(xpublish_date) > 0:
                    # logger.debug(
                        # f"xpublish_date[0].text {xpublish_date[0].text}")
                    publish_date = xpublish_date[0].get(
                        'content') or xpublish_date[0].get('datetime')
                    if publish_date == None and xpublish_date[0].text:
                        publish_date = dateparser.parse(xpublish_date[0].text)

            if publish_date == None:
                xpublish_date = tree.xpath('//meta[@name="Creation-Date"]')
                if len(xpublish_date) > 0:
                    publish_date = dateparser.parse(
                        xpublish_date[0].get('content'))

            if publish_date == None:
                published_dates = tree.xpath(
                    '//span[contains(@class, "entry-date")]/text()')
                if len(published_dates) == 1:
                    groups = re.match(
                        r'(\d+)\s{0,1}年\s{0,1}(\d+)\s{0,1}月\s{0,1}(\d+)\s{0,1}日', published_dates[0])
                    publish_date = "{}-{:02d}-{:02d}".format(
                        int(groups[1]), int(groups[2]), int(groups[3]))

            # ft-post-time
            if publish_date == None:
                published_dates = tree.xpath(
                    '//span[contains(@class, "ft-post-time")]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
            if publish_date == None:
                published_dates = tree.xpath(
                    '//span[contains(@class, "date-text")]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
            if publish_date == None:
                published_dates = tree.xpath(
                    '//div[contains(@data-text,"日期：")]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
            if publish_date == None:
                published_dates = tree.xpath(
                    '//time[@itemprop="dateCreated"]/text()')
                if len(published_dates) > 0:
                    publish_date = dateparser.parse(published_dates[0])
            if publish_date == None:
                published_dates = tree.xpath(
                    '//div[contains(@class, "category-date")]/text()')
                if len(published_dates) > 0:
                    groups = re.match(r'(\d+)-(\d+)-(\d+)',
                                      published_dates[2].strip())
                    publish_date = "{}-{:02d}-{:02d}".format(
                        int(groups[1]), int(groups[2]), int(groups[3]))

            if not publish_date and ds.delayday:
                logger.critical(f'url_hash {url_hash}, failed to parse publish_date for {url}')

            # assume all the parsed publish_date is in TW format, must convert them to utc before storing them in psql db

            if publish_date:
                if isinstance(publish_date, str):
                    logger.debug(f'url_hash {url_hash}, publish_date str type {publish_date}')
                    publish_date = publish_date.split('+')[0]
                    publish_date = dateparser.parse(publish_date, date_formats=[
                                                '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'], settings={'TIMEZONE': '+0000', 'TO_TIMEZONE': 'UTC'})
                a_wpx.publish_date = publish_date
                iac.publish_date = publish_date

                isd = ds.isSyncDay(publish_date)
                iac.zi_sync = isd if iac.zi_sync else False
                if not isd:
                    iac.zi_defy.add('delayday')
            else:
                # publish_date = datetime.utcnow()
                publish_date = None

            # ----- parsing title ----
            title = None
            x_title = tree.xpath('/html/head/title/text()')

            if len(x_title):
                title = x_title[0]

            # domain specific logic:
            if title == None and "www.soft4fun.net" in url:
                x_title = tree.xpath(
                    '//*[@class="post"]/div[1]/h1/span/text()')
                title = x_title[0]

            if "webtest1.sanlih.com.tw" in url or "www.setn.com" in url:
                if title:
                    setn_title_list = title.split('|')
                    title = setn_title_list[0]

            # domain specific: title exclude words
            if title and isinstance(title, str) and getattr(ds, 'e_title', None):
                title = title.replace(ds.e_title[0], "")

            # BSP specific logic: pixnet
            if title and generator == "PChoc":
                title = re.sub('@(?!.*?@).*:: 痞客邦 ::', '', title)

            a_wpx.title = title
            # ----- parsing meta_keywords ----
            meta_keywords = None
            x_news_keywords = tree.xpath(
                '/html/head/meta[@property="news_keywords"]')
            if len(x_news_keywords) > 0:
                meta_keywords = x_news_keywords[0].get('content').split(',')
            else:
                x_keywords = tree.xpath(
                    '/html/head/meta[@property="keywords"]')
                if len(x_keywords) > 0:
                    meta_keywords = x_keywords[0].get('content').split(',')
            a_wpx.meta_keywords = meta_keywords

            # ----- parsing meta_description ----
            meta_description = None
            x_description = tree.xpath('/html/head/meta[@name="description"]')
            if len(x_description) > 0:
                meta_description = x_description[0].get('content')
            else:
                x_description = tree.xpath(
                    '/html/head/meta[@property="og:description"]')
                if len(x_description) > 0:
                    meta_description = x_description[0].get('content')
            a_wpx.meta_description = meta_description
            # ----- parsing author ----
            author = None
            # domain specific logic
            if "blog.tripbaa.com" in url:
                x_author = tree.xpath(
                    "//div[@class='td-post-author-name']/a/text()")
                if len(x_author) > 0:
                    author = x_author[0].strip()
            if "www.expbravo.com" in url:
                x_author = tree.xpath(
                    "//*[@id]/header/div[3]/span[1]/span/a/text()")
                if len(x_author) > 0:
                    author = x_author[0].strip()
            if "www.tripresso.com" in url:
                x_author = tree.xpath(
                    "//*[@id]/header/div/span[2]/span/a/text()")
                if len(x_author) > 0:
                    author = x_author[0].strip()
            if "newtalk.tw" in url:
                x_author = tree.xpath(
                    '//div[contains(@class, "content_reporter")]/a/following-sibling::text()')
                if len(x_author) > 0:
                    author = x_author[0].strip().replace(
                        "文/", "").replace('文／', "").strip()
            if "www.saydigi.com" in url:
                x_author = tree.xpath('//a[@rel="author"]/text()')
                if len(x_author) > 0:
                    author = x_author[0].strip()
            if "iphone4.tw" in url:
                x_author = tree.xpath(
                    '//a[contains(@class, "username")]/strong/text()')
                if len(x_author) > 0:
                    author = x_author[0].strip()
            if "www.winentaste.com" in url:
                x_author = tree.xpath(
                    '/html/body/div[2]/main/div/div/article/div/div[8]/div[2]/div/h2/a/text()')
                if len(x_author) > 0:
                    author = x_author[0].strip()
            # universal logic
            if author == None:
                x_author = tree.xpath('/html/head/meta[@property="author"]')
                if len(x_author) > 0:
                    author = x_author[0].get('content')
            if author == None:
                x_author = tree.xpath(
                    '/html/head/meta[@property="article:author"]/@content')
                if len(x_author) > 0:
                    author = x_author[0]
            if author == None:
                x_author = tree.xpath(
                    '/html/head/meta[@property="dable:author"]')
                if len(x_author) > 0:
                    author = x_author[0].get('content')

            # i_author = domain_info.get('authorList', None)
            # e_author = domain_info.get('e_authorList', None)
            isa = ds.isSyncAuthor(author)
            iac.zi_sync = isa if iac.zi_sync else False
            if not isa:
                iac.zi_defy.add('authorList')

            a_wpx.author = author
            # ----- removing style ----
            for style in cd[0].xpath("//style"):
                style.getparent().remove(style)

            # ----- removing script and exclude tag ----
            remove_text = []
            for script in cd[0].xpath(".//script"):
                if script.get('type', '') == "application/ld+json":
                    continue
                srcScript = script.get('src', "")
                # keep 360 js, but remove others
                if srcScript not in ["https://theta360.com/widgets.js", "//www.instagram.com/embed.js"]:
                    logger.debug(f"url_hash {url_hash}, tail: {script.tail}")
                    if script.tail != None and script.tail.strip() != "":
                        logger.debug(f"url_hash {url_hash}, drop tag")
                        script.drop_tag()
                    else:
                        logger.debug(f"url_hash {url_hash}, remove tag text: {script.text}")
                        script.getparent().remove(script)

            # ----- removing excluded xpath ----
            if getattr(ds, 'e_xpath', None) and len(ds.e_xpath) > 0:
                for badnode in ds.e_xpath:
                    exclude_xpath = unquote(badnode)
                    logger.debug(f"url_hash {url_hash}, exclude xpath: {exclude_xpath}")
                    for bad in cd[0].xpath(exclude_xpath):
                        bad.getparent().remove(bad)

            # ----- counting img and char ----
            # reparse the content
            content = etree.tostring(
                cd[0], pretty_print=True, method='html').decode("utf-8")
            content = unquote(content)

            # h = HTMLParser()
            content = remove_html_tags(content)
            pattern = re.compile(r'\s+')
            content = re.sub(pattern, '', content)
            content = unescape(content)
            len_char = len(content)
            a_wpx.len_char = len_char
            logger.info(f"url_hash {url_hash}, chars: {len_char}, p count: {len_p}, img count: {len_img}")
            ckquality = a_wpx.checkQuality()
            iac.zi_sync = ckquality if iac.zi_sync else False
            if not ckquality:
                iac.quality = False
                iac.zi_defy.add('quality')

            # ----- re-parse content -----
            content = etree.tostring(
                cd[0], pretty_print=True, method='html').decode("utf-8")
            a_wpx.content = content

            # ----- constructing content_hash -----
            content_hash = ''
            # wp_url, meta_description or title
            if multipaged:
                content_hash += title
            else:
                if wp_url:
                    o = urlparse(url)
                    if o.query != "":
                        text = "{}{}{}".format(o.netloc, o.path, o.query)
                    else:
                        text = "{}{}".format(o.netloc, o.path)
                    content_hash += text
                elif meta_description != None and meta_description != "":
                    content_hash += meta_description
                else:
                    # use title only if there is no description
                    if title:
                        content_hash += title

            # concat publish_date
            if publish_date:
                if isinstance(publish_date, datetime):
                    content_hash += publish_date.isoformat()
                else:
                    content_hash += publish_date
                    publish_date = dateparser.parse(publish_date)

            m = hashlib.sha1(content_hash.encode('utf-8'))
            content_hash = partner_id + '_' + m.hexdigest()
            logger.debug(f'url_hash {url_hash}, content_hash: {content_hash}')

            if a_wpx.content_hash and a_wpx.content_hash != content_hash:
                iac.content_update = True
            a_wpx.content_hash = content_hash

            if not publish_date:
                logger.debug(
                    f'url_hash {url_hash}, use utcnow() if failed to parse publish_date')
                a_wpx.publish_date = datetime.utcnow()
                iac.publish_date = a_wpx.publish_date
            # ----- check if publish_date changed -----
            # todo

            logger.debug(f'url_hash {url_hash}, a_wpx {a_wpx}')
            iac.status = True
            logger.info(f'url_hash {url_hash}, crawling successful')
            return a_wpx, iac
        else:
            logger.debug(f'url_hash {url_hash}, xpath not matched')

            secret = None
            # BSP specific: Pixnet 痞客邦
            if secret == None:
                metas = tree.xpath(
                    "//div[@class='article-content']/form/ul/li[1]/text()")
                if len(metas) and metas[0] == "這是一篇加密文章，請輸入密碼":
                    secrt.secret = True
                    secrt.bsp = 'pixnet'

            # BSP specific: Xuite 隨意窩
            if secret == None:
                metas = tree.xpath("//form[@name='main']/text()")
                if len(metas) and metas[0] == "本文章已受保護, 請輸入密碼才能閱讀本文章: ":
                    secrt.secret = True
                    secrt.bsp = 'xuite'

            if secrt.secret:  # this obj is not yet used
                logger.debug(
                    f'url_hash {url_hash}, secrt.bsp: {secrt.bsp}, secrt.secret: {secrt.secret}')
                logger.debug(f'url_hash {url_hash}, secrt.to_dict(): {secrt.to_dict()}')
                iac.secret = True
                iac.zi_sync = False
                iac.zi_defy.add('secret')


            iac.status = False
            return a_wpx, iac

    else:
        logger.error(f'url_hash {url_hash}, requesting {url} failed!')
        iac.status = False
        return a_wpx, iac


def mercury_parser(url):
    if os.environ.get('MERCURY_PATH', None):
        mercury_path = os.environ.get('MERCURY_PATH', None)
        mercury = muterun_js(mercury_path, arguments=url)

        if mercury.exitcode == 0:
            res = mercury.stdout.decode('utf-8')
            response = json.loads(res)
            return response
        else:
            return None
    else:
        logger.error(f'url_ {url}, failed mercury parsing.')
        return None


def ai_a_crawler(url_hash: str, url: str, partner_id: str=None, domain: str=None, domain_info: str=None, multipaged: bool=False) -> object:
    '''
    use mercury to crawl a page

    <return>

    '''
    logger.debug(f'run ai_a_crawler() on url_hash {url_hash}')

    q = dict(url_hash=url_hash)
    if partner_id:
        ts = TaskService.query.filter_by(**q).first()
        wp = WebpagesPartnerAi()
    else:
        ts = TaskNoService.query.filter_by(**q).first()
        wp = WebpagesNoService.query.filter_by(**q).first()

    # logger.debug(f'wp {wp}')
    # logger.debug(f'parseData {parseData}')

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    if multipaged:
        crawlera_apikey = os.environ.get('CRAWLERA_APIKEY', None)


        # slight different w/ that of xpath_a_crawler
        candidate = [
            'www.top1health.com'
        ]

        use_crawlera = False
        for i in candidate:
            if i in url:
                use_crawlera = True

        decode_url = decode_url_function(url)
        if crawlera_apikey and use_crawlera:
            proxies = {
                'http': f"http://{crawlera_apikey}:x@proxy.crawlera.com:8010/",
                'https': f"https://{crawlera_apikey}:x@proxy.crawlera.com:8010/"
            }
            r = requests.get(decode_url, allow_redirects=False,
                             headers=headers, proxies=proxies, verify=False)

            if check_r(r):
                logger.debug('CRAWLERA reqeust successful')
            else:
                logger.warning('CRAWLERA request failed, try local')
                # don't use crawlera if failed at once
                r = requests.get(decode_url, allow_redirects=False, headers=headers)
        else:
            r = requests.get(decode_url, allow_redirects=False, headers=headers)
    else:
        decode_url = decode_url_function(url)
        r = requests.get(decode_url, allow_redirects=False, headers=headers)

    # ======== xpath ========
    if check_r(r):
        logger.debug(f'r {r}')
        # replace the tree
        r.encoding = 'utf-8'
        html = r.text
        tree = lxml.html.fromstring(html)
        metas = tree.xpath('//meta')
        meta_all = {}
        for meta in metas:
            meta_name = None
            if meta.get('name', None):
                meta_name = meta.get('name', None)
            if meta.get('property', None):
                meta_name = meta.get('property', None)
            if meta.get('itemprop', None):
                meta_name = meta.get('itemprop', None)

            if meta_name:
                meta_name = re.sub('[.$]', '', meta_name)
                if meta_name not in meta_all:
                    meta_all[meta_name] = []
                meta_all[meta_name].append(meta.get('content', None))
        wp.meta_jdoc = meta_all
    else:
        logger.error(f'failed to request {url}')
        return None

    # =========== mercury ===========
    parseData = mercury_parser(url)
    if parseData:

        wp.title = parseData['title']
        wp.content = parseData['content']
        wp.publish_date = parseData['date_published']

        tree = etree.HTML(parseData['content'])
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

        # ----- parsing domain ----
        o = urlparse(url)
        domain = o.netloc
        wp.domain = domain
        # ----- parsing content_h1 ----
        content_h1 = ''
        xh1 = tree.xpath('//h1/text()')
        for h1 in xh1:
            if h1.strip():
                content_h1 += '<h1>{}</h1>'.format(h1)
        wp.content_h1 = content_h1
        # ----- parsing content_h2 ----
        content_h2 = ''
        xh2 = tree.xpath('//h2/text()')
        for h2 in xh2:
            if h2.strip():
                content_h2 += '<h2>{}</h2>'.format(h2)
        wp.content_h2 = content_h2
        # ----- parsing content_p ----
        content_p = ''
        xp = tree.xpath('//p/text()')
        for p in xp:
            if p.strip():
                content_p += '<p>{}</p>'.format(p)
        wp.content_p = content_p
        ximage = tree.xpath('//img')
        # ----- parsing cover ----
        present_image = None
        cover = None
        x_og_images = tree.xpath('/html/head/meta[@property="og:image"]')
        if len(x_og_images) > 0:
            present_image = x_og_images[0].get('content')
            # logger.debug(f'present_image: {present_image}')

        if present_image:
            cover = urljoin(url, present_image)

        wp.cover = cover
        # ----- parsing image ----
        content_image = ''
        for image in ximage:
            src = image.get('src')
            if src != None and src.strip():
                alt = image.get('alt')
                src = urljoin(url, src)
                image.set('src', src)
                content_image += '<img src="{}" alt="{}">'.format(src, alt)
            else:
                if image.get('data-original', None) != None:
                    image.set('src', image.get('data-original'))
        wp.content_image = content_image
        # ----- generate content_hash ----
        m = hashlib.sha1(wp.content.encode('utf-8'))
        content_hash = wp.domain + '_' + m.hexdigest()

        wp.content_hash = content_hash
        return wp
    else:
        logger.error('failed to parse with Mercury')
        return None


def request_api(api: str, method: str, payload: dict=None, headers: dict=None):
    '''
    a wrapper func for requesting api
    '''
    method = method.lower()
    if not headers:
        headers = {'Content-Type': "application/json"}

    if payload:
        resp_data = retry_request(
            method, api, payload, headers)
    else:
        resp_data = retry_request(
            method, api, None, headers)
    return resp_data


# ===== below are def from PartnerSync =====


def getWpRealLink(url, shortlink):
    '''
    shortlink might not be valid, like:
    //wp.me/p7zK7N-5lY

    which should be:
    http://wp.me/p7zK7N-5lY
    '''
    logger.info(url + " .... " + shortlink)
    if re.search(r'\?p\=\d+', url, re.I):
        return url
    if re.search(r'\?p\=\d+', shortlink, re.I):
        return shortlink

    try:
        r = requests.get(shortlink, allow_redirects=False)
    except requests.exceptions.MissingSchema as e:
        logger.error(e)
        shortlink = 'http:'+shortlink
        r = requests.get(shortlink, allow_redirects=False)

    if r.status_code == 301:
        wpRealLink = r.headers['Location']
        wp_o = urlparse(wpRealLink)
        o = urlparse(url)
        if wp_o.netloc == o.netloc and re.search(r'\?p\=\d+', wpRealLink, re.I):
            logger.debug(f'wpRealLink {wpRealLink}')
            return wpRealLink
        else:
            return None
    else:
        return None


def getMediumIframeSource(url):
    r = requests.get(url, verify=False, allow_redirects=False)
    if r.status_code == 200:
        r.encoding = 'utf-8'
        html = r.text
        tree = etree.HTML(html)
        xiframe = tree.xpath("//iframe")
        if len(xiframe) > 0:
            url = xiframe[0].get("src", None)
            if url != None:
                o = urlparse(url)
                params = parse_qs(o.query)
                return params['src'][0]
    return None


def getPixnetPublishTime(tree):
    abbr_to_num = {name: str(num).zfill(2)
                   for num, name in enumerate(calendar.month_abbr) if num}
    logger.debug("get pixnet time")
    publish = tree.xpath('//li[@class="publish"]')
    if len(publish) > 0:
        year = tree.xpath('//span[@class="year"]/text()')
        month = tree.xpath('//span[@class="month"]/text()')
        date = tree.xpath('//span[@class="date"]/text()')
        time = tree.xpath('//span[@class="time"]/text()')
        month = abbr_to_num[month[0].strip()]
        return '{}/{}/{}T{}:00+08:00'.format(year[0].strip(), month, date[0].strip(), time[0].strip())
        # return datetime.strptime(dt_str, '%Y/%m/%dT%H:%M:%S%z')
    return None


def getUdnPublishTime(tree):
    publish_times = tree.xpath('//div[@class="article_datatime"]')
    if len(publish_times) > 0:
        publish_time = publish_times[0]
        year = publish_time.xpath('//span[@class="yyyy"]/text()')
        month = publish_time.xpath('//span[@class="mm"]/text()')
        date = publish_time.xpath('//span[@class="dd"]/text()')
        h = publish_time.xpath('//span[@class="hh"]/text()')
        i = publish_time.xpath('//span[@class="ii"]/text()')
        return '{}/{}/{}T{}:{}:00+08:00'.format(year[0].strip(), month[0].strip(), date[0].strip(), h[0].strip(), i[0].strip())
    return None


def getkangaroo5118Time(tree):
    publish_times = tree.xpath('//div[contains(@class, "diary_datetime")]')
    if len(publish_times) > 0:
        publish_time = publish_times[0]
        year = publish_time.xpath('//span[@class="dt_year"]/text()')
        month = publish_time.xpath('//span[@class="dt_month"]/text()')
        date = publish_time.xpath('//span[@class="dt_day"]/text()')
        time = publish_time.xpath('//span[@class="dt_time"]/text()')
        return '{}/{}/{}T{}:00+08:00'.format(year[0].strip(), month[0].strip(), date[0].strip(), time[0].strip())
    return None


def remove_html_tags(text):
    """Remove html tags from a string"""
    # import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def to_csvstr(data: 'list of tuples'):
  '''list of tuples turn into csv str'''
  datastr = ''
  for tp in data:
    ilist = [str(i) for i in tp]
    datastr += '\t'.join(ilist) + '\n'
  return datastr


def construct_email(mailfrom: str, mailto: list, subject: str, content: str, attfilename: str, data: str):
  '''
  still intake one mailfrom and one mailto for now

  params:
  mailfrom: an email,
  mailto: an email,
  subject: str,
  data: csv-ready string
  attfilename: filename for attachment
  '''
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
    jwt_authorizate_code = "breaktime.com.tw"
    # if token payload has aud, decode must need "audience" key or while happen error.
    try:
        payload = jwt.decode(token, jwt_secret_key, audience='content_core', algorithms=['HS256'])
        if payload and payload["iss"] == jwt_authorizate_code:
            return True, payload
        else:
            return False, token
    except Exception as ex:
        logger.error("Can not verify zi token, token: {}, exception: {}".format(token, ex))
        return False, token
