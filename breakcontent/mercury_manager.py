import hashlib
import json
import logging
import os
import re

import lxml.html
from urllib.parse import urljoin

import requests
from Naked.toolshed.shell import execute_js, muterun_js
from lxml import etree

from breakcontent.article_manager import InformACObj
from breakcontent.orm_content import get_task_service_data, get_task_no_service_data, get_task_main_data, \
    update_task_main_status, update_task_service_status_ai, get_webpages_partner_ai_data, \
    create_webpages_ai_without_data, update_task_no_service_with_status, get_webpages_no_service_data, \
    create_webpages_no_service_without_data, update_webpages_partner_ai
from breakcontent.utils import decode_url_function

logger = logging.getLogger('cc')


class MercuryObj:
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/70.0.3538.77 Safari/537.36'}
    mercury_path = os.environ.get('MERCURY_PATH', None)

    def __init__(self, url_hash, url, domain, request_id=None, partner_id=None):
        self.url_hash = url_hash
        self.url = url
        self.domain = domain
        self.partner_id = partner_id
        self.request_id = request_id

    def prepare_mercury(self):
        task_service = get_task_service_data(self.url_hash) if self.partner_id is not None \
            else get_task_no_service_data(self.url_hash)
        task_main = get_task_main_data(self.url_hash)

        if task_service is False or task_main is False:
            logger.error('url_hash {} does not exist. Please check prepare_crawler function and this record again.')
            return None
        else:
            self.request_id = task_main.request_id

        update_task_main_status(self.url_hash, status='doing')

        if self.partner_id is not None:
            update_task_service_status_ai(self.url_hash, status_ai='doing')
            webpages_mercury = get_webpages_partner_ai_data(self.url_hash)
            if webpages_mercury is False:
                create_webpages_ai_without_data(self.url, self.url_hash, self.domain)
        elif self.partner_id is None:
            update_task_no_service_with_status(self.url_hash, status='doing')
            webpages_mercury = get_webpages_no_service_data(self.url_hash)
            if webpages_mercury is False:
                create_webpages_no_service_without_data(self.url, self.url_hash, self.domain)

        return True

    def mercury_parse(self):
        if self.mercury_path is not None:
            mercury = muterun_js(self.mercury_path, arguments=self.url)
            if mercury.exitcode == 0:
                res = mercury.stdout.decode('utf-8')
                response = json.loads(res)
                return response
            else:
                return None
        else:
            logger.error('url_ {}, failed mercury parsing.'.format(self.url))
            return None

    def mercury_a_crawler(self):
        parse_data = self.mercury_parse()
        if parse_data:
            title = parse_data['title']
            content = parse_data['content']
            publish_date = parse_data['date_published']
            tree = etree.HTML(parse_data['content'])

            content_h1, content_h2, content_p, content_image = parse_content_html(tree, self.url)
            m = hashlib.sha1(content.encode('utf-8'))
            content_hash = self.domain + '_' + m.hexdigest()
            meta_jdoc = parse_meta_jdoc(self.url, self.headers)
            if self.partner_id:
                update_webpages_partner_ai(self.url_hash, self.url, meta_jdoc=meta_jdoc, content_hash=content_hash,
                                           title=title, content=content, content_h1=content_h1, content_h2=content_h2,
                                           content_p=content_p, content_image=content_image, publish_date=publish_date,
                                           partner=True)
                update_task_service_status_ai(self.url_hash, status_ai='done')
            else:
                update_webpages_partner_ai(self.url_hash, self.url, meta_jdoc=meta_jdoc, content_hash=content_hash,
                                           title=title, content=content, content_h1=content_h1, content_h2=content_h2,
                                           content_p=content_p, content_image=content_image, publish_date=publish_date,
                                           partner=False)
                update_task_no_service_with_status(self.url_hash, status='done')

                if self.request_id is None:
                    inform_ac = InformACObj(self.url, self.url_hash, self.request_id, publish_date=publish_date)
                    inform_ac.set_ac_sync(True)
                    inform_ac.sync_to_ac(partner=False)
        else:
            if self.partner_id is not None:
                update_task_service_status_ai(self.url_hash, status_ai='failed')
            else:
                update_task_no_service_with_status(self.url_hash, status='failed')

    def get_url_content_with_requests(self, multi_pages=False):
        decode_url = decode_url_function(self.url)
        if multi_pages is True:
            crawlera_api_key = os.environ.get('CRAWLERA_APIKEY', None)

            # slight different w/ that of xpath_a_crawler
            candidate = ['www.top1health.com']
            use_crawlera = False

            for i in candidate:
                if i in self.url:
                    use_crawlera = True

            if crawlera_api_key is not None and use_crawlera:
                proxies = {
                    'http': "http://{}:x@proxy.crawlera.com:8010/".format(crawlera_api_key),
                    'https': "https://{}:x@proxy.crawlera.com:8010/".format(crawlera_api_key)
                }
                response = requests.get(decode_url, allow_redirects=False, headers=self.headers, proxies=proxies,
                                        verify=False)

                if response.status_code == 200:
                    logger.debug('CRAWLERA reqeust successful')
                else:
                    logger.warning('CRAWLERA request failed, try local')
                    # don't use crawlera if failed at once
                    response = requests.get(decode_url, allow_redirects=False, headers=self.headers)
            else:
                response = requests.get(decode_url, allow_redirects=False, headers=self.headers)

        else:
            response = requests.get(decode_url, allow_redirects=False, headers=self.headers)

        if response.status_code == 200:
            return response
        else:
            return False


def parse_content_html(tree, url):
    content_h1, content_h2, content_p, content_image = '', '', '', ''
    xh1 = tree.xpath('//h1/text()')
    for h1 in xh1:
        if h1.strip():
            content_h1 += '<h1>{}</h1>'.format(h1)

    xh2 = tree.xpath('//h2/text()')
    for h2 in xh2:
        if h2.strip():
            content_h2 += '<h2>{}</h2>'.format(h2)

    xp = tree.xpath('//p/text()')
    for p in xp:
        if p.strip():
            content_p += '<p>{}</p>'.format(p)

    ximage = tree.xpath('//img')
    for image in ximage:
        src = image.get('src')
        if src is not None and src.strip():
            alt = image.get('alt')
            src = urljoin(url, src)
            image.set('src', src)
            content_image += '<img src="{}" alt="{}">'.format(src, alt)
        else:
            if image.get('data-original', None) is not None:
                image.set('src', image.get('data-original'))

    return content_h1, content_h2, content_p, content_image


def parse_meta_jdoc(url, headers):
    response = requests.get(url, allow_redirects=False, headers=headers)
    meta_all = {}
    if response.status_code == 200:
        response.encoding = 'utf-8'
        html = response.text
        tree = lxml.html.fromstring(html)
        metas = tree.xpath('//meta')

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

    return meta_all
