import calendar
import datetime
import hashlib
import json
import logging
import os
import re
from datetime import timedelta
from html import unescape
from urllib.parse import urlparse, unquote, urljoin, parse_qs

import dateparser
from lxml import etree
import lxml.html
import requests

from breakcontent.article_manager import InformACObj
from breakcontent.orm_content import get_task_service_data, get_task_no_service_data, get_task_main_data, \
    update_task_main_status, update_task_service_status_xpath, get_webpages_partner_xpath_data, \
    create_webpages_xpath_without_data, update_task_service_status_ai, get_webpages_partner_ai_data, \
    create_webpages_ai_without_data, update_task_no_service_with_status, get_webpages_no_service_data, \
    create_webpages_no_service_without_data, update_webpages_for_xpath

logger = logging.getLogger('cc')


class CrawlerObj:
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/70.0.3538.77 Safari/537.36'}

    def __init__(self, url_hash, url, domain, partner_id, parsing_rules):
        self.url_hash = url_hash
        self.url = url
        self.domain = domain
        self.partner_id = partner_id
        self.parsing_rules = parsing_rules
        self.priority = None
        self.request_id = None
        self.generator = None
        self.title = None

    def prepare_crawler(self, xpath=False):
        task_service = get_task_service_data(self.url_hash) if self.partner_id is not None \
            else get_task_no_service_data(self.url_hash)
        task_main = get_task_main_data(self.url_hash)

        if task_service is False or task_main is False:
            logger.error('url_hash {} does not exist. Please check prepare_crawler function and this record again.')
            return None

        update_task_main_status(self.url_hash, status='doing')

        if self.partner_id is not None and xpath is True:
            update_task_service_status_xpath(self.url_hash, status_xpath='doing')
            webpages_xpath = get_webpages_partner_xpath_data(self.url_hash)
            if webpages_xpath is False:
                create_webpages_xpath_without_data(self.url, self.url_hash, self.domain)
        elif self.partner_id is not None and xpath is False:
            update_task_service_status_ai(self.url_hash, status_ai='doing')
            webpages_ai = get_webpages_partner_ai_data(self.url_hash)
            if webpages_ai is False:
                create_webpages_ai_without_data(self.url, self.url_hash, self.domain)
        elif self.partner_id is None:
            update_task_no_service_with_status(self.url_hash, status='doing')
            webpages_mercury = get_webpages_no_service_data(self.url_hash)
            if webpages_mercury is False:
                create_webpages_no_service_without_data(self.url, self.url_hash, self.domain)

        return True

    def xpath_a_crawler(self, domain_rules, multi_pages=False):
        task_main = get_task_main_data(self.url_hash)
        task_service = get_task_service_data(self.url_hash)
        if task_main is False or task_service is False:
            return False

        webpages_data = get_webpages_partner_xpath_data(self.url_hash)
        if webpages_data is False:
            self.prepare_crawler(xpath=True)

        self.priority = task_main.priority
        self.request_id = task_main.request_id
        self.generator = task_main.generator

        if multi_pages is False:
            inform_ac = InformACObj(self.url_hash, self.url_hash, self.request_id)
            check_rules = True if self.priority == 1 else check_sync_rules(self.url, domain_rules)
            if check_rules is True:
                inform_ac.set_zi_sync(True)
            else:
                defy = 'regex'
                inform_ac.set_zi_sync(False)
                inform_ac.add_zi_defy(defy)
            response = self.get_url_content_with_requests(self.url, self.priority, multi_pages)
            if response is not False:
                response.encoding = 'utf-8'
                html = response.text
                content_directory = None

                try:
                    au_js = (re.search(r'a.breaktime.com.tw\/js\/au.js\?spj', str(html)).span())
                except AttributeError as e:
                    # AttributeError: 'NoneType' object has no attribute 'span'
                    logger.warning('url_hash {}, au.js exception: {}'.format(self.url_hash, e))
                    au_js = False
                if au_js is True:
                    inform_ac.set_page_code(True)

                try:
                    tree = lxml.html.fromstring(html)
                except ValueError as e:
                    logger.error('url_hash {}, tree xml exception: {}'.format(self.url_hash, e))
                    inform_ac.set_ac_sync(False)
                    return

                # ----- check if content_xpath can be matched, parsing canonical url ----
                match_xpath = None
                for xpath in domain_rules['xpath']:
                    xpath = unquote(xpath)
                    content_directory = tree.xpath(xpath)  # content directory
                    if len(content_directory) > 0:
                        match_xpath = xpath
                        logger.info('url_hash {}, match xpath: {}'.format(self.url_hash, xpath))
                        break
                if match_xpath is not None:
                    logger.debug("url_hash {}, xpath matched!".format(self.url_hash))

                logger.error('content_directory: {}'.format(content_directory))
                iac, content_hash, len_char = self.get_content_from_xml_tree(inform_ac, tree, domain_rules,
                                                                             content_directory, match_xpath,
                                                                             self.generator)
                iac.check_url_to_content(content_hash)
                iac.sync_to_ac()

        elif multi_pages is True:
            page_query_param = domain_rules['page'][0]
            page_num = 0

            cat_wpx = dict()
            cat_iac = None
            multi_page_urls = set()

            inform_ac = InformACObj(self.url, self.url_hash, self.request_id)
            while page_num <= 10:
                page_num += 1
                if page_query_param == "d+":
                    i_url = '{}/{}'.format(self.url, page_num)
                else:
                    i_url = '{}?{}={}'.format(self.url, page_query_param, page_num)

                response = self.get_url_content_with_requests(i_url, self.priority, multi_pages)
                if response is not False:
                    response.encoding = 'utf-8'
                    html = response.text
                    content_directory = None

                    try:
                        au_js = (re.search(r'a.breaktime.com.tw\/js\/au.js\?spj', str(html)).span())
                    except AttributeError as e:
                        # AttributeError: 'NoneType' object has no attribute 'span'
                        logger.warning(f'url_hash {self.url_hash}, aujs exception: {e}')
                        au_js = False

                    if au_js is not False:
                        inform_ac.set_page_code(True)

                    try:
                        tree = lxml.html.fromstring(html)
                    except ValueError as e:
                        logger.error(f'url_hash {self.url_hash}, tree xml exception: {e}')
                        inform_ac.set_ac_sync(False)
                        return

                    match_xpath = None

                    # ----- check if content_xpath can be matched, parsing canonical url ----
                    for xpath in domain_rules['xpath']:
                        xpath = unquote(xpath)
                        content_directory = tree.xpath(xpath)  # content directory
                        if len(content_directory) > 0:
                            match_xpath = xpath
                            logger.info(f'url_hash {self.url_hash}, match xpath: {xpath}')

                            break
                    if match_xpath is not None:
                        logger.debug("url_hash {}, xpath matched!".format(self.url_hash))

                    iac, a_wpx = self.get_content_from_xml_tree(inform_ac, tree, domain_rules, content_directory,
                                                                match_xpath, multi_pages)

                    multi_page_urls.add(i_url)
                    if page_num == 1:
                        cat_wpx = a_wpx
                        cat_iac = iac
                    else:
                        cat_wpx['content'] += a_wpx['content']
                        cat_wpx['content_h1'] += a_wpx['content_h1']
                        cat_wpx['content_h2'] += a_wpx['content_h2']
                        cat_wpx['content_p'] += a_wpx['content_p']
                        cat_wpx['content_image'] += a_wpx['content_image']
                        cat_wpx['len_p'] += a_wpx['len_p']
                        cat_wpx['len_img'] += a_wpx['len_img']
                        cat_wpx['len_char'] += a_wpx['len_char']

                else:
                    break

            cat_wpx['url'] = self.url
            cat_wpx['url_hash'] = self.url_hash
            cat_wpx['content_hash'] = generate_content_hash(cat_wpx['url'], cat_wpx['title'], multipaged=True,
                                                            wp_url=cat_wpx['wp_url'], partner_id=self.partner_id,
                                                            meta_description=cat_wpx['meta_description'],
                                                            publish_date=cat_wpx['publish_date'])
            cat_wpx['multi_page_urls'] = sorted(multi_page_urls)
            cat_iac.check_url_to_content(cat_wpx['content_hash'])
            cat_wpx.setdefault('len_img', 0)
            cat_wpx.setdefault('len_char', 0)

            update_webpages_for_xpath(cat_wpx['url'], cat_wpx['url_hash'], content_hash=cat_wpx['content_hash'],
                                      title=cat_wpx['title'], content=cat_wpx['content'], len_char=cat_wpx['len_char'],
                                      content_p=cat_wpx['content_p'], len_p=cat_wpx['len_p'],
                                      content_h1=cat_wpx['content_h1'], content_h2=cat_wpx['content_h2'],
                                      content_image=cat_wpx['content_image'], len_img=cat_wpx['len_img'],
                                      content_xpath=cat_wpx['content_xpath'], cover=cat_wpx['cover'],
                                      author=cat_wpx['author'], publish_date=cat_wpx['publish_date'],
                                      meta_jdoc=cat_wpx['meta_jdoc'], meta_description=cat_wpx['meta_description'],
                                      meta_keywords=cat_wpx['meta_keywords'], wp_url=cat_wpx['wp_url'],
                                      category=cat_wpx['category'], categories=cat_wpx['categories'])
            inform_ac.set_ac_sync(True)
            inform_ac.calculate_crawl_quality(cat_wpx['len_char'], cat_wpx['len_img'])
            inform_ac.check_url_to_content(cat_wpx['content_hash'])
            inform_ac.sync_to_ac(partner=True)

    def get_url_content_with_requests(self, url, priority, multi_pages):
        timeout = 12

        if priority == 5 or multi_pages is True:
            crawlera_apikey = os.environ.get('CRAWLERA_APIKEY', None)
            logging.info('apikey: {}'.format(crawlera_apikey))
            candidate = [
                'www.top1health.com'
            ]

            if crawlera_apikey and self.domain in candidate:
                proxies = {
                    'http': f"http://{crawlera_apikey}:x@proxy.crawlera.com:8010/",
                    'https': f"https://{crawlera_apikey}:x@proxy.crawlera.com:8010/"
                }
                response = requests.get(url, allow_redirects=False, headers=self.headers, proxies=proxies, verify=False,
                                        timeout=timeout)
                if response.status_code == 200:
                    logger.debug('url_hash {}, CRAWLER reqeust successful'.format(self.url_hash))
                else:
                    logger.warning('url_hash {}, CRAWLER request failed, try local'.format(self.url_hash))
                    response = requests.get(url, allow_redirects=False, headers=self.headers, timeout=timeout)

            else:
                logger.debug('url_hash {}, use local to request'.format(self.url_hash))
                response = requests.get(url, allow_redirects=False, headers=self.headers, timeout=timeout)

        else:
            response = requests.get(url, verify=False, allow_redirects=False, headers=self.headers, timeout=timeout)

        if response.status_code == 200:
            update_task_service_status_xpath(self.url_hash, status_xpath='doing', status_code=response.status_code)
            return response

        else:
            update_task_service_status_xpath(self.url_hash, status_xpath='failed', status_code=response.status_code)
            update_task_main_status(self.url_hash, status='failed')
            return False

    def get_content_from_xml_tree(self, iac, tree, domain_rules, content_directory, match_xpath, multi_pages=False):
        remove_redundant_tags(content_directory[0])

        # ----- removing excluded xpath ----
        if getattr(domain_rules, 'e_xpath', None) and len(domain_rules.e_xpath) > 0:
            for bad_node in domain_rules.e_xpath:
                exclude_xpath = unquote(bad_node)
                logger.debug(f"url_hash {self.url_hash}, exclude xpath: {exclude_xpath}")
                for bad in content_directory[0].xpath(exclude_xpath):
                    bad.getparent().remove(bad)

        # ----- parsing meta ----
        meta_jdoc = get_meta_document_from_xml_tree(tree)

        # ----- sanlih ----
        if "webtest1.sanlih.com.tw" in self.url or "www.setn.com" in self.url:
            iac.zi_sync = False
            if 'auth' in meta_jdoc.keys():
                if meta_jdoc['auth'][0] == "1":
                    iac.zi_sync = True

        # ----- parsing images ----
        content_img, len_img = get_img_from_xml_tree(content_directory, self.url, self.url_hash)

        # ----- parsing present_image ----
        cover = get_cover_from_xml_tree(tree, content_directory, self.url, self.url_hash, len_img=len_img)

        # ----- parsing generator ----
        if self.generator is None:
            self.generator = get_generator_from_xml_tree(tree, self.generator)

        # ----- parsing wp_url ----
        wp_url = parse_wp_url(tree, self.url, self.generator)

        # ----- parsing categories ----
        category, categories = get_categories_from_xml_tree(tree, self.url, self.url_hash, self.generator)

        # check if category should sync
        categories_validate = judge_categories(domain_rules, categories)
        if categories_validate is False:
            iac.set_zi_sync(False)
            iac.add_zi_defy('category')

        # ----- parsing content_h1 & content_h2 ----
        content_h1, content_h2 = parse_content_html(tree)

        # ----- parsing content_p ----
        content_p, len_p = parse_content_paragraphs(content_directory)

        # ----- parsing secret ----
        password_check_forms = content_directory[0].xpath("//form[contains(@class, 'post-password-form')]")
        if len(password_check_forms) > 0:
            logger.debug('this is a secret article w/ password lock')
            # secret.secret = True
            iac.secret = True
            iac.zi_sync = False
            iac.zi_defy.add('secret')

        # ----- parsing title ----
        from breakcontent.rules_manager import ParsingRulesObj
        parsing_rule_object = ParsingRulesObj(self.url_hash, self.url, self.domain, self.parsing_rules)
        title = parsing_rule_object.get_title(tree)

        # domain specific: title exclude words
        if title and isinstance(title, str) and getattr(domain_rules, 'e_title', None):
            title = title.replace(domain_rules.e_title[0], "")

        # BSP specific logic: pixnet
        if title and self.generator == "PChoc":
            title = re.sub('@(?!.*?@).*:: 痞客邦 ::', '', title)

        self.title = title

        # ----- parsing author ----
        author = parsing_rule_object.get_author(tree)

        isa = is_sync_author(domain_rules, author)
        iac.zi_sync = isa if iac.zi_sync else False
        if not isa:
            iac.zi_defy.add('authorList')

        # ----- parsing publish_date ----
        publish_date = parsing_rule_object.get_publish_date(tree, self.title)

        if not publish_date and domain_rules['delayday']:
            logger.critical('url_hash {}, failed to parse publish_date for {}'.format(self.url_hash, self.url))

        # assume all the parsed publish_date is in TW format, must convert them to utc before storing them in db

        if publish_date:
            if isinstance(publish_date, str):
                logger.debug('url_hash {}, publish_date str type {}'.format(self.url_hash, publish_date))
                publish_date = publish_date.split('+')[0]
                publish_date = dateparser.parse(publish_date, date_formats=[
                    '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'],
                                                settings={'TIMEZONE': '+0000', 'TO_TIMEZONE': 'UTC'})
            iac.publish_date = publish_date

            if "delayday" in domain_rules and len(domain_rules["delayday"]) > 0:
                delay_day = int(domain_rules['delayday'][0])
            else:
                delay_day = 0
            delay_date = publish_date + timedelta(days=delay_day)
            delay_datetime = delay_date.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=0)))
            now = datetime.datetime.utcnow() + timedelta(hours=8)
            now = now.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=0)))
            logger.debug(f'ddt {delay_datetime}')
            logger.debug(f'now {now}')

            if delay_datetime < now:
                isd = True
            else:
                isd = False
            iac.zi_sync = isd if iac.zi_sync else False
            if isd is False:
                iac.zi_defy.add('delayday')

        # ----- parsing meta_keywords ----
        meta_keywords = parsing_rule_object.get_meta_keywords(tree)

        # ----- parsing meta_description ----
        meta_description = parsing_rule_object.get_meta_description(tree)

        # ----- update parsing rules ----
        parsing_rule_object.update_rules_from_db()

        # ----- counting img and char ----
        # reparse the content
        content = etree.tostring(content_directory[0], pretty_print=True, method='html').decode("utf-8")
        content = unquote(content)

        # h = HTMLParser()
        content = remove_html_tags(content)
        pattern = re.compile(r'\s+')
        content = re.sub(pattern, '', content)
        content = unescape(content)
        len_char = len(content)
        logger.info(f"url_hash {self.url_hash}, chars: {len_char}, p count: {len_p}, img count: {len_img}")

        # ----- constructing content_hash -----
        content_hash = generate_content_hash(self.url, title, partner_id=self.partner_id, multipaged=multi_pages,
                                             wp_url=wp_url, meta_description=meta_description,
                                             publish_date=publish_date)

        # concat publish_date
        if publish_date:
            if isinstance(publish_date, datetime.datetime):
                pass
            else:
                publish_date = dateparser.parse(publish_date)

        if not publish_date:
            logger.debug(f'url_hash {self.url_hash}, use utcnow() if failed to parse publish_date')
            publish_date = datetime.datetime.utcnow()
            iac.publish_date = publish_date

        if multi_pages is True:
            webpage = {'title': title, 'content': content, 'len_char': len_char, 'content_p': content_p, 'len_p': len_p,
                       'content_h1': content_h1, 'content_h2': content_h2, 'content_image': content_img,
                       'len_img': len_img, 'content_xpath': match_xpath, 'cover': cover, 'author': author,
                       'publish_date': publish_date, 'meta_jdoc': meta_jdoc, 'meta_description': meta_description,
                       'meta_keywords': meta_keywords, 'wp_url': wp_url, 'category': category, 'categories': categories
                       }
            return iac, webpage
        update_webpages_for_xpath(self.url, self.url_hash, content_hash=content_hash, title=title, content=content,
                                  len_char=len_char, content_p=content_p, len_p=len_p, content_h1=content_h1,
                                  content_h2=content_h2, content_image=content_img, len_img=len_img,
                                  content_xpath=match_xpath, cover=cover, author=author, publish_date=publish_date,
                                  meta_jdoc=meta_jdoc, meta_description=meta_description, meta_keywords=meta_keywords,
                                  wp_url=wp_url, category=category, categories=categories)

        iac.calculate_crawl_quality(len_char, len_img)
        return iac, content_hash, len_char


def check_sync_rules(url: str, domain_info: dict):
    logger.debug(f'url {url}, starting checkSyncRule()')

    # Paul reported that black list should has the highest priority
    black_rules = ['NOT_EQUALS', 'NOT_MATCH_REGEX', 'NOT_MATCH_REGEX_I']
    if domain_info['regex'] and len(domain_info['regex']) > 0:
        # list of dict
        # 1. scan through black rules first
        for rule in domain_info['regex']:
            if rule['type'] in black_rules:
                status = check_url(url, rule)
                if status is False:
                    logger.debug(f'url {url}: rule {rule}, status {status}')
                    return False
        # 2. scan through white rules next
        for rule in domain_info['regex']:
            if rule['type'] not in black_rules:
                status = check_url(url, rule)
                if status is True:
                    logger.debug(f'url {url}: rule {rule}, status {status}')
                    return True


def check_url(url: str, rule: dict):
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
    if match_type == 'MATCH_REGEX' and re.search(my_regex, url) is not None:
        return True
    if match_type == 'NOT_MATCH_REGEX' and re.search(my_regex, url):
        return False
    if match_type == 'MATCH_REGEX_I' and re.search(my_regex, url, re.IGNORECASE):
        return True
    if match_type == 'NOT_MATCH_REGEX_I' and re.search(my_regex, url, re.IGNORECASE):
        return False
    return None


def get_meta_document_from_xml_tree(tree):
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
    return meta_all


def get_img_from_xml_tree(content_directory, url, url_hash):
    logger.error('content_directory: {}'.format(content_directory))
    ximage = content_directory[0].xpath('.//img')
    len_img = len(ximage) if ximage else 0
    content_image = ''
    for image in ximage:
        if image.get('data-pagespeed-lazy-src', None) is not None:
            image.set('src', image.get('data-pagespeed-lazy-src'))
        if image.get('data-lazy-src', None) is not None:
            image.set('src', image.get('data-lazy-src'))
        if image.get('data-original', None) is not None:
            image.set('src', image.get('data-original'))
        if image.get('data-src', None) is not None:
            image.set('src', image.get('data-src'))

        src = image.get('src')
        if src is not None and src.strip():
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

    return content_image, len_img


def get_cover_from_xml_tree(tree, content_directory, url, url_hash, len_img=0):
    present_image = None
    cover = None
    x_og_images = tree.xpath('/html/head/meta[@property="og:image"]')
    if len(x_og_images) > 0:
        present_image = x_og_images[0].get('content')
        logger.debug(f'url_hash {url_hash}, present_image: {present_image}')

    if "www.iphonetaiwan.org" in url and present_image is None:
        ximage = content_directory[0].xpath('.//img')
        if len(ximage) > 0:
            present_image = ximage[0].get('src')

    if present_image:
        present_image = urljoin(url, present_image)
        cover = present_image

    if present_image:
        if len_img == 0 or "thebetteraging.businesstoday.com.tw" in url:
            logger.debug(f'url_hash {url_hash}, code block here is weird!')
            h_img = etree.Element('img', src=present_image)
            content_directory[0].insert(0, h_img)

    return cover


def get_generator_from_xml_tree(tree, generator=None):
    if generator is None or generator is False:
        x_generator = tree.xpath('/html/head/meta[@name="generator"]')
        if len(x_generator) > 0:
            generator = x_generator[0].get('content')

    return generator


def get_wp_real_link(url, short_link):
    """
    shortlink might not be valid, like:
    //wp.me/p7zK7N-5lY
    which should be:
    http://wp.me/p7zK7N-5lY
    """
    logger.info(url + " .... " + short_link)
    if re.search(r'\?p\=\d+', url, re.I):
        return url
    if re.search(r'\?p\=\d+', short_link, re.I):
        return short_link

    try:
        r = requests.get(short_link, allow_redirects=False)
    except requests.exceptions.MissingSchema as e:
        logger.error(e)
        shortlink = 'http:' + short_link
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


def get_categories_from_xml_tree(tree, url, url_hash, generator):
    category = None
    categories = []
    # domain specific logic
    if category is None and "thebetteraging.businesstoday.com.tw" in url:
        x_categories = tree.xpath(
            '//span[contains(@class, "service-type")]/text()')
        x_cat = x_categories[0].replace('分類：', '')
        categories.append(x_cat)
    # bsp specific logic: pixnet
    if category is None and generator == "PChoc":
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
    if category is None:
        x_categories = tree.xpath(
            '/html/head/meta[@property="article:section"]')
        if len(x_categories) > 0:
            category = x_categories[0].get('content')
            for c in x_categories:
                if c.get('content') not in categories:
                    categories.append(c.get('content'))

    return category, categories


def judge_categories(domain_rules: dict, categories: list) -> bool:
    if domain_rules['e_category'] and len(domain_rules['e_category']) > 0:
        for cat in categories:
            if cat in domain_rules['e_category']:
                return False
    if domain_rules['category'] and len(domain_rules['category']) > 0:
        for category in categories:
            if category in domain_rules['category']:
                print("white category sync!!")
                return True
        print("only white category sync!!")
        return False
    else:
        return True


def parse_content_html(tree):
    content_h1, content_h2 = '', ''
    xh1 = tree.xpath('//h1/text()')
    for h1 in xh1:
        if h1.strip():
            content_h1 += '<h1>{}</h1>'.format(h1)

    xh2 = tree.xpath('//h2/text()')
    for h2 in xh2:
        if h2.strip():
            content_h2 += '<h2>{}</h2>'.format(h2)

    return content_h1, content_h2


def parse_wp_url(tree, url, generator):
    wp_url = None
    short_link = tree.xpath('//link[@rel="shortlink"]/@href')
    if len(short_link) > 0:
        if generator is not None and re.search('wordpress', generator, re.I):
            wp_url = get_wp_real_link(url, short_link[0])
    return wp_url


def remove_html_tags(text):
    """Remove html tags from a string"""
    # import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def parse_content_paragraphs(content_directory):
    content_p = ''
    len_p = 0
    content = etree.tostring(content_directory[0], pretty_print=True, method='html').decode("utf-8")
    content = unquote(content)
    content_directory[0] = lxml.html.fromstring(content)
    xp = content_directory[0].xpath('.//p')
    for p in xp:
        txt = remove_html_tags(etree.tostring(
            p, pretty_print=True, method='html').decode("utf-8"))
        s = unescape(txt.strip())
        if s.strip():
            content_p += '<p>{}</p>'.format(s)
            len_p = len_p + 1

    return content_p, len_p


def parse_publish_date_from_xml_tree(tree, url_hash):
    publish_date = None
    x_publish_date = tree.xpath('/html/head/meta[@property="article:published_time"]')
    if len(x_publish_date) > 0:
        publish_date = x_publish_date[0].get('content')
    else:
        data_blocks = tree.xpath('//script[@type="application/ld+json"]/text()')
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
    return publish_date


def get_udn_publish_time(tree):
    publish_times = tree.xpath('//div[@class="article_datatime"]')
    if len(publish_times) > 0:
        publish_time = publish_times[0]
        year = publish_time.xpath('//span[@class="yyyy"]/text()')
        month = publish_time.xpath('//span[@class="mm"]/text()')
        date = publish_time.xpath('//span[@class="dd"]/text()')
        h = publish_time.xpath('//span[@class="hh"]/text()')
        i = publish_time.xpath('//span[@class="ii"]/text()')
        return '{}/{}/{}T{}:{}:00+08:00'.format(year[0].strip(), month[0].strip(), date[0].strip(), h[0].strip(),
                                                i[0].strip())
    return None


def get_kangaroo_publish_time(tree):
    publish_times = tree.xpath('//div[contains(@class, "diary_datetime")]')
    if len(publish_times) > 0:
        publish_time = publish_times[0]
        year = publish_time.xpath('//span[@class="dt_year"]/text()')
        month = publish_time.xpath('//span[@class="dt_month"]/text()')
        date = publish_time.xpath('//span[@class="dt_day"]/text()')
        time = publish_time.xpath('//span[@class="dt_time"]/text()')
        return '{}/{}/{}T{}:00+08:00'.format(year[0].strip(), month[0].strip(), date[0].strip(), time[0].strip())
    return None


def parse_publish_date_from_specific_logic(tree, url, domain, title):
    publish_date = None
    if publish_date is None and "blogspot.com" in url:
        published_dates = tree.xpath('//abbr[@itemprop="datePublished"]')
        if len(published_dates) > 0:
            publish_date = published_dates[0].get("title")
            return publish_date

    if publish_date is None and domain == "momo.foxpro.com.tw":
        s = re.search(r'^(\d{4}).(\d{2}).(\d{2})', title)
        year = s.group(1)
        month = s.group(2)
        day = s.group(3)
        publish_date = f'{year}-{month}-{day}'
        return publish_date

    if publish_date is None and "blog.udn.com" in url:
        publish_date = get_udn_publish_time(tree)
        return publish_date

    if publish_date is None and "kangaroo5118.nidbox.com" in url:
        publish_date = get_kangaroo_publish_time(tree)
        return publish_date

    if publish_date is None and "bonbg.com" in url:
        x_publish_dates = tree.xpath('//span[@class="meta_date"]/text()')
        if len(x_publish_dates) > 0:
            publish_date = dateparser.parse(x_publish_dates[0])
        return publish_date

    if publish_date is None and "thebetteraging.businesstoday.com.tw" in url:
        published_dates = tree.xpath('//span[contains(@class, "date")]/text()')
        if len(published_dates) > 0:
            publish_date = published_dates[0].replace('日期：', '')
            if publish_date is None:
                groups = re.match(r'(\d+)年(\d+)月(\d+)日', published_dates[0])
                publish_date = "{}-{:02d}-{:02d}".format(int(groups[1]), int(groups[2]), int(groups[3]))
        return publish_date

    if publish_date is None and "iphone4.tw" in url:
        published_dates = tree.xpath('//span[@class="date"]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
        return publish_date

    if publish_date is None and "imreadygo.com" in url:
        published_dates = tree.xpath(
            '//div[@class="newsmag-date"]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
        return publish_date

    if publish_date is None and "jct.tw" in url:
        published_dates = tree.xpath(
            '//h1/following-sibling::div[1]/text()')
        # print(x_author)
        if len(published_dates) > 0:
            publish_date = published_dates[0].strip(
            ).replace("文章日期 : ", "").strip()
            publish_date = dateparser.parse(publish_date)
        return publish_date

    if publish_date is None and "www.amplframe.com" in url:
        published_dates = tree.xpath(
            '/html/body/div[1]/div[3]/div/div/div/ul/li[2]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
        return publish_date

    return publish_date


def parse_publish_date_from_universe_logic(tree):
    publish_date = None
    if publish_date is None:
        published_dates = tree.xpath('//abbr[contains(@class, "published")]')
        if len(published_dates) > 0:
            publish_date = published_dates[0].get("title")
            return publish_date

    if publish_date is None:
        published_dates = tree.xpath('//time[contains(@class, "published")]')
        if len(published_dates) > 0:
            publish_date = published_dates[0].get("datetime")
            return publish_date

    if publish_date is None:
        published_dates = tree.xpath('//span[contains(@class, "thetime")][1]/text()')
        if len(published_dates) > 0:
            publish_date = published_dates[0]
            return publish_date

    if publish_date is None:
        published_dates = tree.xpath('//h4[@class="post-section__text"][2]/text()')
        if len(published_dates) > 0:
            publish_date = published_dates[0]
            return publish_date

    if publish_date is None:
        published_dates = tree.xpath('//h2[contains(@class, "date-header")]/span/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
            if publish_date is None:
                groups = re.match(r'(\d+)年(\d+)月(\d+)日', published_dates[0])
                publish_date = "{}-{:02d}-{:02d}".format(int(groups[1]), int(groups[2]), int(groups[3]))
                return publish_date

    if publish_date is None:
        xpublish_date = tree.xpath('//*[@itemprop="datePublished"]')
        if len(xpublish_date) > 0:
            # logger.debug("xpublish_date[0].text {xpublish_date[0].text}")
            publish_date = xpublish_date[0].get('content') or xpublish_date[0].get('datetime')
            if publish_date is None and xpublish_date[0].text:
                publish_date = dateparser.parse(xpublish_date[0].text)

    if publish_date is None:
        xpublish_date = tree.xpath('//meta[@name="Creation-Date"]')
        if len(xpublish_date) > 0:
            publish_date = dateparser.parse(xpublish_date[0].get('content'))
            return publish_date

    if publish_date is None:
        published_dates = tree.xpath('//span[contains(@class, "entry-date")]/text()')
        if len(published_dates) == 1:
            groups = re.match(r'(\d+)\s{0,1}年\s{0,1}(\d+)\s{0,1}月\s{0,1}(\d+)\s{0,1}日', published_dates[0])
            publish_date = "{}-{:02d}-{:02d}".format(int(groups[1]), int(groups[2]), int(groups[3]))
            return publish_date
    return publish_date


def get_publish_date_from_ft(tree):
    publish_date = None
    if publish_date is None:
        published_dates = tree.xpath('//span[contains(@class, "ft-post-time")]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
            return publish_date
    if publish_date is None:
        published_dates = tree.xpath('//span[contains(@class, "date-text")]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
            return publish_date
    if publish_date is None:
        published_dates = tree.xpath('//div[contains(@data-text,"日期：")]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
            return publish_date
    if publish_date is None:
        published_dates = tree.xpath('//time[@itemprop="dateCreated"]/text()')
        if len(published_dates) > 0:
            publish_date = dateparser.parse(published_dates[0])
            return publish_date
    if publish_date is None:
        published_dates = tree.xpath('//div[contains(@class, "category-date")]/text()')
        if len(published_dates) > 0:
            groups = re.match(r'(\d+)-(\d+)-(\d+)', published_dates[2].strip())
            publish_date = "{}-{:02d}-{:02d}".format(int(groups[1]), int(groups[2]), int(groups[3]))
            return publish_date
    return publish_date


def get_pixnet_publish_time(tree):
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


def get_author_by_domain(tree, url):
    author = None
    # domain specific logic
    if "blog.tripbaa.com" in url:
        x_author = tree.xpath("//div[@class='td-post-author-name']/a/text()")
        if len(x_author) > 0:
            author = x_author[0].strip()
    if "www.expbravo.com" in url:
        x_author = tree.xpath("//*[@id]/header/div[3]/span[1]/span/a/text()")
        if len(x_author) > 0:
            author = x_author[0].strip()
    if "www.tripresso.com" in url:
        x_author = tree.xpath("//*[@id]/header/div/span[2]/span/a/text()")
        if len(x_author) > 0:
            author = x_author[0].strip()
    if "newtalk.tw" in url:
        x_author = tree.xpath('//div[contains(@class, "content_reporter")]/a/following-sibling::text()')
        if len(x_author) > 0:
            author = x_author[0].strip().replace("文/", "").replace('文／', "").strip()
    if "www.saydigi.com" in url:
        x_author = tree.xpath('//a[@rel="author"]/text()')
        if len(x_author) > 0:
            author = x_author[0].strip()
    if "iphone4.tw" in url:
        x_author = tree.xpath('//a[contains(@class, "username")]/strong/text()')
        if len(x_author) > 0:
            author = x_author[0].strip()
    return author


def get_author_by_universe_logic(tree):
    author = None
    # universal logic
    if author is None:
        x_author = tree.xpath('/html/head/meta[@property="author"]')
        if len(x_author) > 0:
            author = x_author[0].get('content')
    if author is None:
        x_author = tree.xpath('/html/head/meta[@property="article:author"]/@content')
        if len(x_author) > 0:
            author = x_author[0]
    if author is None:
        x_author = tree.xpath('/html/head/meta[@property="dable:author"]')
        if len(x_author) > 0:
            author = x_author[0].get('content')
    return author


def get_author_from_property_author(tree):
    x_author = tree.xpath('/html/head/meta[@property="author"]')
    author = None
    if len(x_author) > 0:
        author = x_author[0].get('content')
    return author


def get_author_from_property_article_author(tree):
    x_author = tree.xpath('/html/head/meta[@property="article:author"]/@content')
    author = None
    if len(x_author) > 0:
        author = x_author[0]
    return author


def get_author_from_property_dable_author(tree):
    x_author = tree.xpath('/html/head/meta[@property="dable:author"]')
    author = None
    if len(x_author) > 0:
        author = x_author[0].get('content')
    return author


def is_sync_author(rules, author: list) -> bool:
    if "e_authorList" in rules and len(rules["e_authorList"]) > 0 and author in rules["e_authorList"]:
        return False
    if "authorList" in rules and len(rules["authorList"]) > 0:
        print("only white authors sync!!")
        if author in rules["authorList"]:
            return True
        else:
            return False
    else:
        return True


def generate_content_hash(url, title, partner_id=None, multipaged=False, wp_url=None, meta_description=None,
                          publish_date=None):
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
        elif meta_description is not None and meta_description != "":
            content_hash += meta_description
        else:
            # use title only if there is no description
            if title:
                content_hash += title

    # concat publish_date
    if publish_date:
        if isinstance(publish_date, datetime.datetime):
            content_hash += publish_date.isoformat()
        else:
            content_hash += publish_date

    m = hashlib.sha1(content_hash.encode('utf-8'))
    content_hash = partner_id + '_' + m.hexdigest()

    return content_hash


def get_medium_iframe_source(url):
    r = requests.get(url, verify=False, allow_redirects=False)
    if r.status_code == 200:
        r.encoding = 'utf-8'
        html = r.text
        tree = etree.HTML(html)
        xiframe = tree.xpath("//iframe")
        if len(xiframe) > 0:
            url = xiframe[0].get("src", None)
            if url is not None:
                o = urlparse(url)
                params = parse_qs(o.query)
                return params['src'][0]
    return None


def remove_redundant_tags(content_first_directory):
    # ----- removing script ----
    # TODO: need to remove script or not
    for script in content_first_directory.xpath("//noscript"):
        script.getparent().remove(script)

    # ----- removing style ----
    # TODO: need to remove style or not
    for style in content_first_directory.xpath("//style"):
        style.getparent().remove(style)

    # ----- removing script and exclude tag ----
    # TODO: need to remove or not
    for script in content_first_directory.xpath(".//script"):
        if script.get('type', '') == "application/ld+json":
            continue
        src_script = script.get('src', "")
        # keep 360 js, but remove others
        if src_script not in ["https://theta360.com/widgets.js", "//www.instagram.com/embed.js"]:
            if script.tail is not None and script.tail.strip() != "":
                script.drop_tag()
            else:
                script.getparent().remove(script)
