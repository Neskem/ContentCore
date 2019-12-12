import datetime
import logging

from breakcontent.crawler_manager import parse_publish_date_from_xml_tree, parse_publish_date_from_specific_logic, \
    parse_publish_date_from_universe_logic, get_publish_date_from_ft, get_pixnet_publish_time, get_author_by_domain, \
    get_author_from_property_author, get_author_from_property_article_author, get_author_from_property_dable_author
from breakcontent.orm_content import update_xpath_parsing_rules_by_url_hash

logger = logging.getLogger('cc')


class ParsingRulesObj:
    __slots__ = ['task_main_id', 'url_hash', 'url', 'domain', 'parsing_rules', 'title_rule', 'author_rule',
                 'publish_date_rule', 'meta_keywords_rule', 'meta_description_rule', 'ctime']

    def __init__(self, url_hash, url, domain, parsing_rules):
        self.url_hash = url_hash
        self.url = url
        self.domain = domain
        self.parsing_rules = parsing_rules
        self.title_rule = parsing_rules[0]
        self.author_rule = parsing_rules[1]
        self.publish_date_rule = parsing_rules[2]
        self.meta_keywords_rule = parsing_rules[3]
        self.meta_description_rule = parsing_rules[4]
        self.ctime = parsing_rules[5]

    def update_rules_from_db(self):
        if self.title_rule != self.parsing_rules[0] or self.author_rule != self.parsing_rules[1] or \
                self.publish_date_rule != self.parsing_rules[2] or self.meta_keywords_rule != self.parsing_rules[3] or \
                self.meta_description_rule != self.parsing_rules[4]:
            update_xpath_parsing_rules_by_url_hash(self.url_hash, self.title_rule, self.author_rule,
                                                   self.publish_date_rule, self.meta_keywords_rule,
                                                   self.meta_description_rule)

    def get_publish_date(self, tree, title):
        if self.publish_date_rule != 0:
            publish_date = self.get_publish_date_from_rule(tree, title)
            return publish_date
        else:
            publish_date = parse_publish_date_from_xml_tree(tree, self.url_hash)
            if publish_date is not None:
                self.publish_date_rule = 1
                return publish_date
            # domain specific logic
            publish_date = parse_publish_date_from_specific_logic(tree, self.url, self.domain, title)
            if publish_date is not None:
                self.publish_date_rule = 2
                return publish_date

            # ft-post-time
            publish_date = get_publish_date_from_ft(tree)
            if publish_date is not None:
                self.publish_date_rule = 3
                return publish_date

            # universal logic
            publish_date = parse_publish_date_from_universe_logic(tree)
            if publish_date is not None:
                self.publish_date_rule = 4
                return publish_date

            # bsp specific logic
            publish_date = get_pixnet_publish_time(tree)
            if publish_date is not None:
                self.publish_date_rule = 5
                return publish_date

            logger.error("Can not parse publish_date from this url: {}".format(self.url))
            self.publish_date_rule = 0
            return None

    def get_publish_date_from_rule(self, tree, title):
        try:
            if self.publish_date_rule == 1:
                publish_date = parse_publish_date_from_xml_tree(tree, self.url_hash)
            elif self.publish_date_rule == 2:
                publish_date = parse_publish_date_from_specific_logic(tree, self.url, self.domain, title)
            elif self.publish_date_rule == 3:
                publish_date = parse_publish_date_from_universe_logic(tree)
            elif self.publish_date_rule == 4:
                publish_date = get_publish_date_from_ft(tree)
            elif self.publish_date_rule == 5:
                publish_date = get_pixnet_publish_time(tree)
            else:
                logger.error("Can not parse publish_date from this url: {}".format(self.url))
                self.publish_date_rule = 0
                publish_date = None
        except Exception as e:
            logger.error("Exception: {}, url: {}, url_hash:{}, publish_date_rule:{}".format(
                e, self.url, self.url_hash, self.publish_date_rule))
            publish_date = None

        return publish_date

    def get_author(self, tree):
        if self.author_rule != 0:
            author = self.get_author_from_rule(tree)
            return author
        else:
            author = get_author_by_domain(tree, self.url)
            if author is not None:
                self.author_rule = 1
                return author

            author = get_author_from_property_author(tree)
            if author is not None:
                self.author_rule = 2
                return author

            author = get_author_from_property_article_author(tree)
            if author is not None:
                self.author_rule = 3
                return author

            author = get_author_from_property_dable_author(tree)
            if author is not None:
                self.author_rule = 4
                return author

            logger.error("Can not parse author from this url: {}".format(self.url))
            self.author_rule = 0
            return None

    def get_author_from_rule(self, tree):
        try:
            if self.author_rule == 1:
                author = get_author_by_domain(tree, self.url)
            elif self.author_rule == 2:
                author = get_author_from_property_author(tree)
            elif self.author_rule == 3:
                author = get_author_from_property_article_author(tree)
            elif self.author_rule == 4:
                author = get_author_from_property_dable_author(tree)
            else:
                logger.error("Can not parse author from this url: {}".format(self.url))
                self.author_rule = 0
                author = None
        except Exception as e:
            logger.error("Exception: {}, url: {}, url_hash:{}, author_rule:{}".format(
                e, self.url, self.url_hash, self.author_rule))
            author = None

        return author

    def get_title(self, tree):
        if self.title_rule != 0:
            title = self.get_title_from_rule(tree)
            return title
        else:
            text_title = tree.xpath('/html/head/title/text()')
            if len(text_title) > 0:
                title = text_title[0]

                if title is not None:
                    self.title_rule = 1
                    if "webtest1.sanlih.com.tw" in self.url or "www.setn.com" in self.url:
                        title = title.split('|')[0]
                    return title

            text_title = tree.xpath('//*[@class="post"]/div[1]/h1/span/text()')
            if len(text_title) > 0:
                title = text_title[0]
                if title is not None:
                    self.title_rule = 2
                    return title

            logger.error("Can not parse title from this url: {}".format(self.url))
            self.title_rule = 0
            return None

    def get_title_from_rule(self, tree):
        try:
            if self.title_rule == 1:
                text_title = tree.xpath('/html/head/title/text()')
                title = text_title[0]

                if "webtest1.sanlih.com.tw" in self.url or "www.setn.com" in self.url:
                    title = title.split('|')[0]

            elif self.title_rule == 2:
                text_title = tree.xpath('//*[@class="post"]/div[1]/h1/span/text()')
                title = text_title[0]
            else:
                logger.error("Can not parse title from this url: {}".format(self.url))
                self.title_rule = 0
                title = None
        except Exception as e:
            logger.error("Exception: {}, url: {}, url_hash:{}, title_rule:{}".format(
                e, self.url, self.url_hash, self.title_rule))
            title = None

        return title

    def get_meta_keywords(self, tree):
        if self.meta_keywords_rule != 0:
            meta_keywords = self.get_meta_keywords_from_rule(tree)
            return meta_keywords
        else:
            news_keywords = tree.xpath('/html/head/meta[@property="news_keywords"]')
            if len(news_keywords) > 0:
                meta_keywords = news_keywords[0].get('content').split(',')
                if meta_keywords is not None:
                    self.meta_keywords_rule = 1
                    return meta_keywords

            keywords = tree.xpath('/html/head/meta[@property="keywords"]')
            if len(keywords) > 0:
                meta_keywords = keywords[0].get('content').split(',')

                if meta_keywords is not None:
                    self.meta_keywords_rule = 2
                    return meta_keywords

            logger.error("Can not parse meta keyword from this url: {}".format(self.url))
            self.meta_keywords_rule = 0
            return None

    def get_meta_keywords_from_rule(self, tree):
        try:
            if self.meta_keywords_rule == 1:
                news_keywords = tree.xpath('/html/head/meta[@property="news_keywords"]')
                meta_keywords = news_keywords[0].get('content').split(',')
            elif self.meta_keywords_rule == 2:
                keywords = tree.xpath('/html/head/meta[@property="keywords"]')
                meta_keywords = keywords[0].get('content').split(',')
            else:
                logger.error("Can not parse meta keyword from this url: {}".format(self.url))
                self.meta_keywords_rule = 0
                meta_keywords = None
        except Exception as e:
            logger.error("Exception: {}, url: {}, url_hash:{}, meta_keywords_rule:{}".format(
                e, self.url, self.url_hash, self.meta_keywords_rule))
            meta_keywords = None

        return meta_keywords

    def get_meta_description(self, tree):
        if self.meta_description_rule != 0:
            meta_description = self.get_meta_description_from_rule(tree)
            return meta_description
        else:
            description = tree.xpath('/html/head/meta[@name="description"]')
            if len(description) > 0:
                meta_description = description[0].get('content')

                if meta_description is not None:
                    self.meta_description_rule = 1
                    return meta_description

            og_description = tree.xpath('/html/head/meta[@property="og:description"]')
            if len(og_description) > 0:
                meta_description = og_description[0].get('content')

                if meta_description is not None:
                    self.meta_description_rule = 2
                    return meta_description

            logger.error("Can not parse meta description from this url: {}".format(self.url))
            self.meta_description_rule = 0
            return None

    def get_meta_description_from_rule(self, tree):
        try:
            if self.meta_description_rule == 1:
                description = tree.xpath('/html/head/meta[@name="description"]')
                meta_description = description[0].get('content')
            elif self.meta_description_rule == 2:
                og_description = tree.xpath('/html/head/meta[@property="og:description"]')
                meta_description = og_description[0].get('content')
            else:
                logger.error("Can not parse meta description from this url: {}".format(self.url))
                self.meta_description_rule = 0
                meta_description = None
        except Exception as e:
            logger.error("Exception: {}, url: {}, url_hash:{}, meta_description_rule:{}".format(
                e, self.url, self.url_hash, self.meta_description_rule))
            meta_description = None

        return meta_description
