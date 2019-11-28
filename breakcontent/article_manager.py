import logging
import os

import requests

from urllib.parse import urlparse

from breakcontent.orm_content import update_task_main_sync_status, get_url_to_content_data, \
    init_url_to_content, update_task_main_status, update_task_service_with_status_only_xpath, \
    update_url_to_content, delete_old_related_data, update_task_no_service_with_status, update_webpages_page_code

logger = logging.getLogger('cc')


class InformACObj:

    WORD_COUNT_STANDARD = 100
    PIC_COUNT_STANDARD = 2
    ac_content_multipage_api = os.environ.get('AC_CONTENT_MULTIPAGE_API', None)
    ac_status_api = os.environ.get('AC_CONTENT_STATUS_API', None)

    def __init__(self, url, url_hash, request_id, publish_date=None, ai_article=False):
        self.url = url
        self.url_hash = url_hash
        self.request_id = request_id
        self.publish_date = publish_date
        self.ai_article = ai_article
        self.ac_sync = True
        self.zi_sync = True
        self.quality = True
        self.secret = False
        self.zi_defy = list()
        self.headers = {'Content-Type': "application/json"}

        self.has_page_code = False
        self.old_url_hash = None
        self.content_hash = None

    def calculate_quality(self, len_char):
        if len_char < self.WORD_COUNT_STANDARD:
            self.quality = False
            self.zi_sync = False
            self.zi_defy.append('quality')
        else:
            self.quality = True
            self.zi_sync = True

        update_task_main_sync_status(self.url_hash, status='doing', inform_ac_status=self.ac_sync, zi_sync=self.zi_sync)
        return True

    def calculate_crawl_quality(self, len_char, len_img):
        if len_char < self.WORD_COUNT_STANDARD and len_img < self.PIC_COUNT_STANDARD:
            self.quality = False
            self.zi_sync = False
            self.zi_defy.append('quality')
        else:
            self.quality = True
            self.zi_sync = True

        update_task_main_sync_status(self.url_hash, status='doing', inform_ac_status=self.ac_sync, zi_sync=self.zi_sync)
        return True

    def sync_external_to_ac(self):

        data = dict()
        data['url'] = self.url
        data['url_hash'] = self.url_hash
        data['request_id'] = self.request_id
        data['publish_date'] = self.publish_date

        data['content_update'] = None
        data['old_url_hash'] = None
        data['url_structure_type'] = None
        data['has_page_code'] = None

        data['status'] = self.ac_sync
        data['quality'] = self.quality
        data['secret'] = self.secret
        data['zi_sync'] = self.zi_sync
        data['zi_defy'] = self.zi_defy
        data['ai_article'] = self.ai_article

        logger.debug('url_hash {}, run init_external_task(), inform_ac_data {}'.format(self.url_hash, data))

        r = retry_requests('put', self.ac_status_api, data=data, headers=self.headers)
        if r.status_code == 200:
            update_task_main_status(self.url_hash, status='failed')
            update_task_service_with_status_only_xpath(self.url_hash, status_xpath='failed')
            logger.debug('url_hash {}, inform AC failed'.format(self.url_hash))
        else:
            update_task_main_status(self.url_hash, status='done')
            update_task_service_with_status_only_xpath(self.url_hash, status_xpath='done')
            logger.debug('url_hash {}, inform AC successful'.format(self.url_hash))

        return True

    def check_url_to_content(self, content_hash):
        self.content_hash = content_hash
        url_content = get_url_to_content_data(content_hash)
        if url_content is False:
            init_url_to_content(self.url, self.url_hash, content_hash, self.request_id, replaced=False)
        else:
            if url_content.url != self.url:
                self.old_url_hash = url_content.url

    def sync_to_ac(self, partner=True):
        data = {
            'url_hash': self.url_hash,
            'url': self.url,
            'old_url_hash': self.old_url_hash,
            'request_id': self.request_id,
            'publish_date': str(self.publish_date),
            'secret': self.secret,
            'has_page_code': self.has_page_code,
            'quality': self.quality,
            'zi_sync': self.zi_sync,
            'zi_defy': self.zi_defy,
            'status': self.ac_sync,
        }
        r = retry_requests('put', self.ac_status_api, data=data, headers=self.headers)

        if partner is True:
            if r.status_code == 200:
                if self.old_url_hash is not None and self.content_hash is not None:
                    update_url_to_content(self.content_hash, self.url, self.url_hash, self.request_id, replaced=True)
                update_task_main_status(self.url_hash, status='done')
                update_task_service_with_status_only_xpath(self.url_hash, status_xpath='done')
            else:
                logger.error('url_hash {}, inform AC failed'.format(self.url_hash))
                update_task_main_status(self.url_hash, status='failed')
                update_task_service_with_status_only_xpath(self.url_hash, status_xpath='failed')

        else:
            if r.status_code == 200:
                update_task_main_status(self.url_hash, status='done')
                update_task_no_service_with_status(self.url_hash, status='done')
            else:
                logger.error('url_hash {}, inform AC failed'.format(self.url_hash))
                update_task_main_status(self.url_hash, status='failed')
                update_task_no_service_with_status(self.url_hash, status='failed')

        return True

    def remove_multipage_data(self, multipage_url, domain=None):
        if domain is None:
            url_parse = urlparse(self.url)
            domain = url_parse.netloc
        data = dict(url=self.url, url_hash=self.url_hash, multipage=multipage_url, domain=domain)

        response = retry_requests('post', self.ac_content_multipage_api, data=data, headers=self.headers)

        if response:
            logger.debug('url_hash {}, mp_url != url: resp_data {}, inform AC successful'.format(self.url_hash, response))
            delete_old_related_data(self.url_hash)
            logger.debug('url_hash {}, mp_url != url: after delete tm.'.format(self.url_hash))
        else:
            logger.error('url_hash {}, mp_url != url: resp_data {}, inform AC failed'.format(self.url_hash, response))

        return True

    def set_zi_sync(self, zi_sync=True):
        self.zi_sync = zi_sync

    def add_zi_defy(self, defy):
        if defy is not None and type(defy) is str:
            self.zi_defy.append(defy)

    def set_ac_sync(self, status):
        self.ac_sync = status

    def set_page_code(self, page_code):
        self.has_page_code = page_code
        update_webpages_page_code(self.url_hash, page_code)


def retry_requests(method, api, data=None, headers=None, retry=3):
    method = method.lower()
    while retry:
        try:
            if method == 'put':
                r = requests.put(api, json=data, headers=headers)
            elif method == 'post':
                r = requests.post(api, json=data, headers=headers)
            elif method == 'delete':
                r = requests.delete(api, json=data, headers=headers)
            else:
                r = requests.get(api, json=data, headers=headers)

            if r.status_code == 200:
                return r
            else:
                logger.error("url_hash {} request status code {}".format(data.get('url_hash', None), r.status_code))
                retry -= 1
                continue
        except ValueError as e:
            logger.error("url_hash {} {}".format(data['url_hash'], e))
            retry -= 1
            continue

    logger.error('failed requesting {} {} times'.format(api, retry))
    return False
