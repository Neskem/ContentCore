import re
from urllib.parse import unquote, urlparse


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
        'zi_sync_rule': None,
        'status': None
    }

    def __init__(self):
        for k, v in self.data.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            'url_hash': self.url_hash,
            'parent_url': self.parent_url,
            'url': self.url,
            'old_url_hash': self.old_url_hash,
            'content_update': self.content_update,
            'request_id': self.request_id,
            'publish_date': self.publish_date,
            'url_structure_type': self.url_structure_type,
            'secret': self.secret,
            'has_page_code': self.has_page_code,
            'quality': self.quality,
            'zi_sync_rule': self.zi_sync_rule,
            'status': self.status
        }


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
        #my_regex = r"" + re.escape(match_string) + r""
        # my_regex = r"" + match_string + r""
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
        # if self.status == 'off':
            # return None
        if self.regex and len(self.regex) > 0:
            # loop through all the rules
            for rule in self.regex:
                status = self.checkUrl(url, rule)
                if status:
                    return status
        return False
