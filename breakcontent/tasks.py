from breakcontent.factory import create_celery_app
from breakcontent.utils import Secret
import os
import json
import requests
from flask import current_app
from celery.utils.log import get_task_logger

from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError
from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
from breakcontent import mylogging
from urllib.parse import urlencode, quote_plus, unquote, quote, unquote_plus, parse_qs
from urllib.parse import urlparse, urljoin

from lxml import etree
# import lxml
import lxml.html
import xml.etree.ElementTree as ET
import time
import re
import dateparser
from html import unescape
from datetime import datetime, timedelta
import hashlib, base64


celery = create_celery_app()
logger = get_task_logger('default')


@celery.task()
def test_task():
    '''
    for testing logging only
    '''
    logger.info('[celery] run test_task')


@celery.task()
def delete_main_task(data: dict):
    logger.debug(
        f'run delete_main_task(), down stream records will also be deleted...')
    tmd = TaskMain.query.filter_by(**data).first()
    db.session.delete(tmd)
    db.session.commit()
    logger.debug('done delete_main_task()')


@celery.task()
def upsert_main_task(data: dict):
    '''
    upsert doc in TaskMain, TaskService and TaskNoService
    '''
    logger.debug(f'data: {data}')
    r_required = [
        'url_hash',
        'url',
        'request_id',
        'partner_id',
    ]
    rdata = {k: v for (k, v) in data.items() if k in r_required}

    try:
        logger.debug('start inserting')
        logger.debug(f'data {data}')
        logger.debug(f'rdata {rdata}')
        tm = TaskMain(**data)
        if data.get('partner_id', None):
            tm.task_service = TaskService(**rdata)
        else:
            rdata.pop('partner_id')
            tm.task_noservice = TaskNoService(**rdata)
        db.session.add(tm)
        db.session.commit()
        logger.debug(f'done insert')
    except IntegrityError as e:
        logger.warning(e)
        db.session.rollback()
        logger.debug('update url/request_id/status/partner_id by url_hash')
        q = dict(url_hash=data['url_hash'])
        logger.debug(f'q {q}')
        data.update(dict(status='pending'))
        TaskMain.query.filter_by(**q).update(data)
        if data.get('partner_id', None):
            rdata.update(dict(status_ai='pending', status_xpath='pending'))
            TaskService.query.filter_by(**q).update(rdata)
            logger.debug('done update for partner')
        else:
            rdata.pop('partner_id')
            rdata.update(dict(status='pending'))
            TaskNoService.query.filter_by(**q).update(rdata)
        db.session.commit()
        logger.debug('done update')


@celery.task()
def create_tasks(priority):
    '''
    update status (pending > doing) and generate tasks
    '''
    logger.debug(f"run create_tasks()...")
    with db.session.no_autoflush:

        q = dict(priority=priority, status='pending')
        tml = TaskMain.query.filter_by(**q).order_by(
            TaskMain._ctime.asc()).limit(10).all()

        logger.debug(f'len {len(tml)}')
        if len(tml) == 0:
            logger.debug(f'no result, quit')
            return

        for tm in tml:
            logger.debug(f'update {tm}...')
            tm.status = 'doing'
            db.session.commit()

            if tm.task_service:
                logger.debug(f'update {tm.task_service}...')
                update_ts = {
                    'status_ai': 'doing',
                    'status_xpath': 'doing'
                }
                TaskService.query.filter_by(
                    id=tm.task_service.id).update(update_ts)
                prepare_task.delay(tm.task_service.to_dict())

            if tm.task_noservice:
                logger.debug(f'update {tm.task_noservice}...')
                update_tns = {
                    'status': 'doing'
                }
                TaskNoService.query.filter_by(
                    id=tm.task_noservice.id).update(update_tns)
                db.session.commit()
                prepare_task.delay(tm.task_noservice)

        logger.debug('done sending a batch of tasks to broker')


@celery.task()
def prepare_task(task: dict):
    '''
    fetch settings from partner system through api

    argument:
    task: could be a TaskService or TaskNoService dict

    '''

    def parse_data(data: dict) -> dict:
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
            'e_autherList',
            'regex',
            'e_title',
            'syncDate',
            'page',
            'delayday',
            'sitemap',
        ]

        for k, v in data.items():
            if k == 'data':
                # key check and filter (not sure if necessary)
                domain_info = {kk: vv for kk,
                               vv in v.items() if kk in optional}
                logger.debug(f'filtered domain_info {domain_info}')
                return domain_info
            else:
                continue

    api_prefix = os.environ.get(
        'PS_DOMAIN_API') or 'https://partner.breaktime.com.tw/api/config/'

    logger.debug('run prepare_task()...')
    logger.debug(f'task {task}')

    # task {'id': 1, 'task_main_id': 1, 'webpages_partner_xpath': None, 'webpages_partner_ai': None, 'url_hash': 'ce65ca9a29f408496abfb7e7a978b2d4e31d93df', 'url': 'https://fangcat.com/autonomic-instability-summer-strategy/', 'request_id': 'b9da619f-576c-4473-add2-e53d08b74ac7', 'page_query_param': None, 'secret': None, 'retry_xpath': 0, 'status_xpath': 'doing', 'retry_ai': 0, 'status_ai': 'doing', '_ctime': '2019-01-18T09:12:43.033354', '_mtime': '2019-01-18T09:29:49.076318'}

    if task.get('partner_id', None):

        url = task['url']
        partner_id = task['partner_id']
        o = urlparse(url)
        domain = o.netloc

        logger.debug(f'domain {domain}')
        logger.debug(f'partner_id {partner_id}')

        api = api_prefix + f'{partner_id}/{domain}/'
        logger.debug(f'api {api}')
        headers = {'Content-Type': "application/json"}

        r = requests.get(api, headers=headers)
        if r.status_code == 200:
            json_resp = json.loads(r.text)
            # logger.debug(f'json_resp {json_resp}')
            # logger.debug(f'type {type(json_resp)}')
            domain_info = parse_data(json_resp)
            logger.debug(f'domain_info {domain_info}')

            if domain_info.get('page', None):
                # to be revised!

                # send job to multipage crawler
                logger.debug(f"domain_info['page'] {domain_info['page']}")
                logger.debug(f'task {task}')
                # update db
                tsf = TaskService.query.filter_by(id=task['id']).first()
                logger.debug(f'tsf {tsf}')
                tsf.is_multipage = True
                tsf.page_query_param = domain_info['page']
                logger.debug(f'tsf {tsf}')
                db.session.commit()
                logger.debug('update successful')
                # xpath_multi_crawler.delay(task['id'], domain, domain_info)

                # inform AC here! Alan is working on a new endpoint for this specfic change

            else:
                # send job to singlepage crawler
                xpath_single_crawler.delay(task['id'], partner_id, domain, domain_info)

            logger.debug('done requesting api')
        else:
            logger.debug(f'request failed status {r.status_code}')

    else:
        # not partner goes here
        pass


@celery.task()
def do_task(priority):
    '''
    generate tasks by priority
    '''
    pass


def prepare_crawler(tid: int) -> dict:
    '''
    init record in WebpagesPartnerXpath for singlepage or multipage crawler, so the fk will be linked to TaskService and the pk will be created.
    '''

    retry = 1
    while retry:
        try:
            tsf = TaskService.query.filter_by(id=tid).first()
            retry = 0
        except OperationalError as e:
            retry += 1
            db.session.rollback()
            logger.error(f'lance debug: {e}')
            logger.debug(f'retry {retry}')
            if retry > 5:
                retry = 0
                logger.error('quit query, this should not happen!')
                raise

    logger.debug(f'tsf {tsf}')
    tsf.status_xpath = 'doing'

    wpx = {
        'url_hash': tsf.url_hash,
        'url': tsf.url,  # should url be updated here?
    }
    try:
        tsf.webpages_partner_xpath = WebpagesPartnerXpath(**wpx)
        db.session.commit()
        logger.debug('insert succesful')
    except IntegrityError as e:
        # insert should will violate unique constraint but update won't
        db.session.rollback()
        logger.warning(e)
        WebpagesPartnerXpath.query.filter_by(
            url_hash=tsf.url_hash).update(wpx)
        db.session.commit()
        logger.debug('update tsf succesful')
    tsf_wpx_dic = tsf.webpages_partner_xpath.to_dict()
    # logger.debug(f'tsf_wpx_dic {tsf_wpx_dic}')
    # get generator from TaskMain through TaskService
    try:
        generator = tsf.task_main.generator
        logger.debug(f'generator {generator}')
        tsf_wpx_dic.update(dict(generator=generator))
    except Exception as e:
        # might need more script here!
        logger.error(e)
        raise e

    return tsf_wpx_dic


@celery.task()
def xpath_single_crawler(tid: int, partner_id: str, domain: str, domain_info: dict):
    '''
    partner only
    '''
    logger.debug(f'start to crawl single-paged url on tid {tid}')
    # logger.debug(f'tid type {type(tid)}')

    wpx = prepare_crawler(tid)
    # logger.debug(f'wpx {wpx}')

    xpath_a_crawler(wpx, partner_id, domain, domain_info)


@celery.task()
def xpath_multi_crawler(tid: int, partner_id: str, domain: str, domain_info: dict):
    '''
    partner only

    loop xpath_a_crawler by page number

    ** remember to update the url & url_hash in CC and AC
    '''
    logger.debug(f'start to crawl multipaged url on tid {tid}')
    # xpath_a_crawler()


def xpath_a_crawler(wpx: dict, partner_id:str, domain: str, domain_info: dict):
    '''
    use xpath to crawl a page
    '''
    logger.debug(f'run the basic unit of xpath crawler')
    logger.debug(f'wpx {wpx}')
    # logger.debug(f'domain_info {domain_info}')

    task_service_id = wpx['task_service_id']
    tsf = TaskService.query.filter_by(id=task_service_id).first()
    logger.debug(f'tsf {tsf}')

    url = wpx.get('url')
    generator = wpx.get('generator', None)
    secrt = Secret()

    # use an object to store the required and optional attribute
    a_wpx = WebpagesPartnerXpath()
    logger.debug(f'a_wpx {a_wpx}')
    logger.debug(f'type(a_wpx) {type(a_wpx)}')


    # if generator == "blogger":
    #     url = re.sub(r'\?.*?$', '', url)
    # if generator == "PChoc" or domain == "blog.xuite.net":
    #     if url.find("preview=") != -1:
    #         return
    #     url = re.sub('-.*', '', url)
    # # AC has done this already

    # x_generator = tree.xpath('/html/head/meta[@name="generator"]')
    # if len(x_generator) > 0:
    #     generator = x_generator[0].get('content')
    # x_shortlink = tree.xpath('//link[@rel="shortlink"]/@href')
    # if len(x_shortlink) > 0:
    #     if generator != None and re.search('wordpress', generator, re.I):
    #         wp_real_link = getWpRealLink(url, x_shortlink[0])

    html = None
    r = requests.get(url, verify=False, allow_redirects=True)
    if r.status_code == 200:
        r.encoding = 'utf-8'
        html = r.text  # full html here!
        generator = None
        content = None
        cd = None
        category = None
        wp_real_link = None

        tStart = time.time()
        try:
            aujs = (
                re.search(r'a.breaktime.com.tw\/js\/au.js\?spj', str(html)).span())
            logger.debug(f'aujs {aujs}')

            if aujs != None:
                aujs = True
                logger.debug(f'aujs {aujs}')
            else:
                pass
        except:
            aujs = 'None'
            logger.debug(f'aujs {aujs}')
        tEnd = time.time()
        logger.debug(f"scanning aujs cost {tEnd - tStart} sec")

        tree = lxml.html.fromstring(html)
        match_xpath = None

        for xpath in domain_info['xpath']:
            xpath = unquote(xpath)
            cd = tree.xpath(xpath) # content directory
            if len(cd) > 0:
                #print("match xpath")
                match_xpath = xpath
                logger.info("match xpath: {}".format(xpath))
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
                        url = wpx['url']
                break

        # ----- parsing content ----
        if match_xpath != None:
            logger.debug("xpath matched!")

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

            # ----- parsing present_image ----
            present_image = None
            x_og_images = tree.xpath('/html/head/meta[@property="og:image"]')
            if len(x_og_images) > 0:
                present_image = x_og_images[0].get('content')
                logger.debug(f'og img: {present_image}')

            if present_image:
                present_image = urljoin(url, present_image)
                cover = present_image

            # ----- parsing script ----
            for script in cd[0].xpath("//noscript"):
                logger.debug(f'script.text {script.text}')
                script.getparent().remove(script)

            # ----- parsing generator ----
            x_generator = tree.xpath('/html/head/meta[@name="generator"]')
            if len(x_generator) > 0:
                generator = x_generator[0].get('content')
                # parse generator from full html again, replace

            # ----- parsing wp url ----
            x_shortlink = tree.xpath('//link[@rel="shortlink"]/@href')
            if len(x_shortlink) > 0:
                if generator != None and re.search('wordpress', generator, re.I):
                    wp_real_link = getWpRealLink(url, x_shortlink[0])

            # ----- parsing categories ----
            categories = []
            x_categories = tree.xpath(
                '/html/head/meta[@property="article:section"]')
            if len(x_categories) > 0:
                category = x_categories[0].get('content')
                for c in x_categories:
                    if c.get('content') not in categories:
                        categories.append(c.get('content'))
            if generator == "PChoc" and category == None:
                g_x_categories = tree.xpath(
                    '//ul[@class="refer"]/li[1]/a/text()')
                if len(g_x_categories) == 0:
                    tsf.status_xpath = 'done'
                    db.session.commit()
                    return
                x_categories = tree.xpath(
                    '//ul[@class="refer"]/li[2]/a/text()')
                if len(x_categories) > 0:
                    category = x_categories[0]
                else:
                    pass
            # domain specific logic
            if len(categories) == 0 and "thebetteraging.businesstoday.com.tw" in url:
                x_categories = tree.xpath(
                    '//span[contains(@class, "service-type")]/text()')
                x_cat = x_categories[0].replace('分類：', '')
                categories.append(x_cat)

            # ----- parsing content_h1 ----
            xh1 = tree.xpath('//h1/text()')
            content_h1 = ''
            for h1 in xh1:
                if h1.strip():
                    content_h1 += '<h1>{}</h1>'.format(h1)

            # ----- parsing content_h2 ----
            xh2 = tree.xpath('//h2/text()')
            content_h2 = ''
            for h2 in xh2:
                if h2.strip():
                    content_h2 += '<h2>{}</h2>'.format(h2)

            # ----- parsing content_p ----
            # h = HTMLParser()
            content = etree.tostring(
                cd[0], pretty_print=True, method='html').decode("utf-8")
            content = unquote(content)
            cd[0] = lxml.html.fromstring(content)
            xp = cd[0].xpath('.//p')
            len_xp = len(xp)
            content_p = ''
            len_p = 0

            # content = etree.tostring(cd[0], pretty_print=True, method='html').decode("utf-8")
            # content = unquote(content)
            for p in xp:
                txt = remove_html_tags(etree.tostring(
                    p, pretty_print=True, method='html').decode("utf-8"))
                s = unescape(txt.strip())
                if s.strip():
                    content_p += '<p>{}</p>'.format(s)
                    len_p = len_p + 1

            # ----- parsing secret ----
            # Paul version
            # ppf = re.search('post-password-form', content) or None

            # if ppf != None:
            #     logger.debug('this is a secrete article w/ password lock')

            # Eric version
            password_check_forms = cd[0].xpath("//form[contains(@class, 'post-password-form')]")
            if len(password_check_forms) > 0:
                logger.debug('this is a secret article w/ password lock')
                # secret = True
                secrt.secret = True
            logger.debug(f'{secrt.to_dict()}')

            # ----- parsing href (what for?) ----
            xarch = cd[0].xpath('.//a')
            for a in xarch:
                href = a.get('href')
                if href != None and href.strip():
                    href = urljoin(url, href)
                    logger.debug(f'href {href}')
                    try:
                        a.set('href', str(href))
                    except:
                        pass

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
                    image.set('src', src)
                    content_image += '<img src="{}" alt="{}">'.format(src, alt)
            # domain specifc logic
            if "www.iphonetaiwan.org" in url and len(ximage) > 0:
                present_image = ximage[0].get('src')

            # ----- parsing iframe ----
            xiframe = cd[0].xpath('//iframe')
            for iframe in xiframe:
                src = iframe.get('src')
                if src != None and src.strip():
                    alt = iframe.get('alt')
                    src = urljoin(url, src)
                    # domain spefic logic
                    if tc.partner.domain == "medium.com":
                        src = getMediumIframeSource(src)
                    iframe.set('src', src)

            # ----- parsing publish_date ----
            if wp_real_link:
                wp_url = wp_real_link
            publish_date = None
            x_publish_date = tree.xpath(
                '/html/head/meta[@property="article:published_time"]')
            if len(x_publish_date) > 0:
                publish_date = x_publish_date[0].get('content')
            else:
                data_blocks = tree.xpath(
                    '//script[@type="application/ld+json"]/text()')
                logger.debug(f'data_blocks {data_blocks}')
                for data_block in data_blocks:
                    try:
                        data = json.loads(data_block)
                        if "datePublished" in data:
                            publish_date = data.get("datePublished")
                            break
                    except Exception as e:
                        logger.error(e)
                        data_block = str(data_block).replace(
                            '[', '').replace(',]', '')
                        logger.debug(f'data_block {data_block}')
                        data = json.dumps(data_block)
                        data = json.loads(data)
                        if "datePublished" in data:
                            publish_date = data.get("datePublished")
                            break

            # ----- parsing title ----
            x_title = tree.xpath('/html/head/title/text()')

            if len(x_title):
                title = x_title[0]
                if domain_info.get('e_title', None):
                    title = title.replace(domain_info['e_title'][0], "")

                # check is pixnet or not
                # BSP specific logic
                logger.debug(f'this code block is weird!!!')
                if publish_date == None and generator == "PChoc":
                    publish_date = getPixnetPublishTime(tree)
                    title = re.sub('@(?!.*?@).*:: 痞客邦 ::', '', title)
            else:
                # if failed to parse title
                # domain specific logic
                if "www.soft4fun.net" in url:
                    x_title = tree.xpath(
                        '//*[@class="post"]/div[1]/h1/span/text()')
                    title = x_title[0]
                    if domain_info.get('e_title', None):
                        title = title.replace(domain_info['e_title'][0], "")

            if publish_date == None and "blogspot.com" in url:
                published_dates = tree.xpath(
                    '//abbr[@itemprop="datePublished"]')
                if len(published_dates) > 0:
                    publish_date = published_dates[0].get("title")

            if publish_date == None and domain == "momo.foxpro.com.tw":
                s = re.search(r'^(\d{4}).(\d{2}).(\d{2})', title)
                year = s.group(1)
                month = s.group(2)
                day = s.group(3)
                publish_date = f'{year}-{month}-{day}'

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
            if publish_date == None and "thebetteraging.businesstoday.com.tw" in url:
                published_dates = tree.xpath(
                    '//span[contains(@class, "date")]/text()')
                if len(published_dates) > 0:
                    published_dates[0] = published_dates[0].replace('日期：', '')
                    groups = re.match(r'(\d+)年(\d+)月(\d+)日',
                                      published_dates[0].strip())
                    publish_date = "{}-{:02d}-{:02d}".format(
                        int(groups[1]), int(groups[2]), int(groups[3]))

            # non-domain specifc
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
                    logger.debug(
                        f"xpublish_date[0].text {xpublish_date[0].text}")
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

            # ----- parsing meta_keywords ----
            x_news_keywords = tree.xpath(
                '/html/head/meta[@property="news_keywords"]')
            if len(x_news_keywords) > 0:
                meta_keywords = x_news_keywords[0].get('content').split(',')
            else:
                x_keywords = tree.xpath(
                    '/html/head/meta[@property="keywords"]')
                if len(x_keywords) > 0:
                    meta_keywords = x_keywords[0].get('content').split(',')

            # ----- parsing meta_description ----
            x_description = tree.xpath('/html/head/meta[@name="description"]')
            if len(x_description) > 0:
                meta_description = x_description[0].get('content')
            else:
                x_description = tree.xpath(
                    '/html/head/meta[@property="og:description"]')
                if len(x_description) > 0:
                    meta_description = x_description[0].get('content')

            # ----- parsing author ----

            # universal logic
            x_author = tree.xpath('/html/head/meta[@property="author"]')
            if len(x_author) > 0:
                author = x_author[0].get('content')
            else:
                x_author = tree.xpath(
                    '/html/head/meta[@property="article:author"]/@content')
                if len(x_author) > 0:
                    author = x_author[0]

            if author == None:
                x_author = tree.xpath(
                    '/html/head/meta[@property="dable:author"]')
                if len(x_author) > 0:
                    author = x_author[0].get('content')

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

            # ----- removing style ----
            for style in cd[0].xpath("//style"):
                style.getparent().remove(style)

            # ----- removing script and exclude tag ----
            remove_text = []
            for script in cd[0].xpath(".//script"):
                if script.get('type', '') == "application/ld+json":
                    continue
                srcScript = script.get('src', "")
                """ keep 360 js, but remove others """
                if srcScript not in ["https://theta360.com/widgets.js", "//www.instagram.com/embed.js"]:
                    logger.debug("tail: {}".format(script.tail))
                    if script.tail != None and script.tail.strip() != "":
                        logger.debug("drop tag")
                        #if script.text:
                            #remove_text.append(remove_html_tags(script.text))
                        script.drop_tag()
                    else:
                        logger.debug("remove tag")
                        logger.debug(script.text)
                        script.getparent().remove(script)

            # ----- removing script and exclude tag ----
            if domain_info.get('e_xpath', None) and len(domain_info['e_xpath']) > 0:
                for badnode in domain_info['e_xpath']:
                    exclude_xpath = unquote(badnode)
                    logger.debug("exclude xpath: {}".format(exclude_xpath))
                    for bad in cd[0].xpath(exclude_xpath):
                        bad.getparent().remove(bad)

            # ----- counting img and char ----
            # reparse the content
            content = etree.tostring(cd[0], pretty_print=True, method='html').decode("utf-8")
            content = unquote(content)

            # h = HTMLParser()
            content = remove_html_tags(content)
            pattern = re.compile(r'\s+')
            content = re.sub(pattern, '', content)
            content = unescape(content)
            chars_p = len(content)
            logger.info("chars: {},p count: {}, img count: {}".format(chars_p, len_p, len_img))
            if len_img < 2 and chars_p < 100:
                pass
                # content of poor quality
                quality = False

            if present_image != None:
                if len_img == 0 or "thebetteraging.businesstoday.com.tw" in url:
                    logger.debug('code block here is weird!')
                    h_img = etree.Element('img', src=present_image)
                    cd[0].insert(0, h_img)

            # re-parse content
            content = etree.tostring(cd[0], pretty_print=True, method='html').decode("utf-8")

            # ----- constructing content_hash -----
            content_hash = ''
            # wp_url, meta_description or title
            if wp_real_link:
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
                if title != None:
                    content_hash += sp.title

            # concat publish_date
            if publish_date != None:
                if isinstance(publish_date, datetime):
                    content_hash += publish_date.isoformat()
                else:
                    content_hash += publish_date
                    publish_date = dateparser.parse(publish_date)

            logger.debug(f'content_hash: {content_hash}')
            m = hashlib.sha1(content_hash.encode('utf-8'))
            content_hash = partner_id + '_' + m.hexdigest()

            # ----- check if publish_date changed -----
            # todo

            logger.info('crawling succesful')

        else:
            logger.debug('xpath not matched')


            secret = None
            # BSP specific: Pixnet 痞客邦
            if secret == None:
                metas = tree.xpath("//div[@class='article-content']/form/ul/li[1]/text()")
                logger.debug(metas[0])
                if metas[0] == "這是一篇加密文章，請輸入密碼":
                    secrt.secret = True
                    secrt.bsp = 'pixnet'


            # BSP specific: Xuite 隨意窩
            if secret == None:
                metas = tree.xpath("//form[@name='main']/text()")
                logger.debug(metas[0])
                if metas[0] == "本文章已受保護, 請輸入密碼才能閱讀本文章: ":
                    secrt.secret = True
                    secrt.bsp = 'xuite'

            if secret:
                logger.debug(f'{secrt.to_dict()}')

    else:
        # request failed goes here
        pass


@celery.task()
def ai_single_crawler():
    pass


@celery.task()
def ai_multi_crawler():
    pass


def ai_a_crawler():
    '''
    use mercury to crawl a page
    '''

# ===== below are def from PartnerSync =====


@celery.task()
def getWpRealLink(url, shortlink):
    logger.info(url + " .... " + shortlink)
    if re.search(r'\?p\=\d+', url, re.I):
        return url
    if re.search(r'\?p\=\d+', shortlink, re.I):
        return shortlink

    r = requests.get(shortlink, allow_redirects=False)
    if r.status_code == 301:
        wpRealLink = r.headers['Location']
        wp_o = urlparse(wpRealLink)
        o = urlparse(url)
        if wp_o.netloc == o.netloc and re.search(r'\?p\=\d+', wpRealLink, re.I):
            return wpRealLink
        else:
            return None
    else:
        return None


def remove_html_tags(text):
    """Remove html tags from a string"""
    # import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def getMediumIframeSource(url):
    r = requests.get(url, verify=False, allow_redirects=True)
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
    logger.debug("get pixnet time")
    publish = tree.xpath('//li[@class="publish"]')
    if len(publish) > 0:
        year = tree.xpath('//span[@class="year"]/text()')
        month = tree.xpath('//span[@class="month"]/text()')
        date = tree.xpath('//span[@class="date"]/text()')
        time = tree.xpath('//span[@class="time"]/text()')
        return '{}/{}/{}T{}:00+08:00'.format(year[0].strip(), month[0].strip(), date[0].strip(), time[0].strip())
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
