import datetime
import logging
import pickle

from breakcontent import ContextManager, crawler_rules
from breakcontent.crawler_manager import parse_publish_date_from_xml_tree, parse_publish_date_from_specific_logic, \
    parse_publish_date_from_universe_logic, get_publish_date_from_ft, get_pixnet_publish_time, get_author_by_domain, \
    get_author_from_property_author, get_author_from_property_article_author, get_author_from_property_dable_author

logger = logging.getLogger('cc')


class BaseParser:
    file_name = "parser_rules.pickle"

    def __init__(self, url, url_hash, domain, rules, record_type, record=0):
        self.url = url
        self.url_hash = url_hash
        self.domain = domain
        self.rules = rules
        self.type = record_type
        self.record = record
        if self.type not in self.rules:
            self.rules[self.type] = None
        logging.info("crawler_rules: {}".format(crawler_rules))

    def update_pickle_rules(self, rules):
        write_back_pickle(self.file_name, self.record, self.type, crawler_rules, self.domain)
        crawler_rules[self.domain][self.type] = rules


class PublishDateParser(BaseParser):
    def setting_publish_date(self, tree, title, generator):
        if self.record != 0:
            publish_date = self.get_publish_date_from_record(tree, title)
            return publish_date
        else:
            publish_date = parse_publish_date_from_xml_tree(tree, self.url_hash)
            if publish_date is not None:
                self.update_pickle_rules(1)
                return publish_date
            # domain specific logic
            if publish_date is None:
                publish_date = parse_publish_date_from_specific_logic(tree, self.url, self.domain, title)
                if publish_date is not None:
                    self.update_pickle_rules(2)
                    return publish_date

            # ft-post-time
            if publish_date is None:
                publish_date = get_publish_date_from_ft(tree)
                if publish_date is not None:
                    self.update_pickle_rules(3)
                    return publish_date

            # universal logic
            if publish_date is None:
                publish_date = parse_publish_date_from_universe_logic(tree)
                if publish_date is not None:
                    self.update_pickle_rules(4)
                    return publish_date

            # bsp specific logic
            if publish_date is None and generator == "PChoc":
                publish_date = get_pixnet_publish_time(tree)
                if publish_date is not None:
                    self.update_pickle_rules(5)
                    return publish_date

            logger.error("Can not parse publish_date from this url: {}".format(self.url))
            return datetime.datetime.utcnow()

    def get_publish_date_from_record(self, tree, title):
        if self.record == 1:
            publish_date = parse_publish_date_from_xml_tree(tree, self.url_hash)

        elif self.record == 2:
            publish_date = parse_publish_date_from_specific_logic(tree, self.url, self.domain, title)

        elif self.record == 3:
            publish_date = parse_publish_date_from_universe_logic(tree)

        elif self.record == 4:
            publish_date = get_publish_date_from_ft(tree)

        elif self.record == 5:
            publish_date = get_pixnet_publish_time(tree)

        else:
            logger.error("Can not parse publish_date from this url: {}".format(self.url))
            publish_date = datetime.datetime.utcnow()
        return publish_date


class AuthorParser(BaseParser):
    def setting_author(self, tree):
        if self.record != 0:
            author = self.get_author_from_record(tree)
            return author
        else:
            author = get_author_by_domain(tree, self.url)
            if author is not None:
                self.update_pickle_rules(1)
                return author

            if author is None:
                author = get_author_from_property_author(tree)
                if author is not None:
                    self.update_pickle_rules(2)
                    return author

            if author is None:
                author = get_author_from_property_article_author(tree)
                if author is not None:
                    self.update_pickle_rules(3)
                    return author

            if author is None:
                author = get_author_from_property_dable_author(tree)
                if author is not None:
                    self.update_pickle_rules(4)
                    return author

            logger.error("Can not parse author from this url: {}".format(self.url))
            return None

    def get_author_from_record(self, tree):
        if self.record == 1:
            author = get_author_by_domain(tree, self.url)

        elif self.record == 2:
            author = get_author_from_property_author(tree)

        elif self.record == 3:
            author = get_author_from_property_article_author(tree)

        elif self.record == 4:
            author = get_author_from_property_dable_author(tree)

        else:
            logger.error("Can not parse author from this url: {}".format(self.url))
            author = None
        return author


def write_back_pickle(file_name, record, record_type, rules, domain):
    if domain not in rules:
        rules[domain] = dict()
    rules[domain][record_type] = record
    with ContextManager(file_name, "wb") as file:
        pickle.dump(rules, file)
        file.close()
