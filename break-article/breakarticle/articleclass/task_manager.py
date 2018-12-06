import logging
from breakarticle.exceptions import BreakTaskError
from breakarticle.articleclass.orm_article import init_sitemap_url_info, init_sitemap_service_info
from breakarticle.articleclass.orm_article import exist_url_hash_urlinfo, init_task_info
from breakarticle.articleclass.orm_article import exist_url_hash_serviceinfo, exist_url_hash_taskinfo

logger_name = "logger_admin"
logger = logging.getLogger(logger_name)


class TaskInitialization:

    def __init__(self, task_type, url, url_hash, domain, priority, partner_id=None):
        self.url = url
        self.task_type = task_type
        self.partner_id = partner_id
        self.url_hash = url_hash
        self.domain = domain
        self.partner_id = partner_id

        if self.task_type == "sitemap":
            # Sitemap domain will not current while use "pure_url" this variable.
            self.service_name = "Zi_C"
            self.notify_status = "pending"
            self.status = "sync"
            self.priority = priority
            self.generator = ""
            self.request_id = ""

    def initial_url_info(self):
        try:
            urlinfo_validate = exist_url_hash_urlinfo(self.url_hash)
            if urlinfo_validate is False:
                init_sitemap_url_info(self.url, self.url_hash, self.partner_id, self.domain)

            serviceinfo_validate = exist_url_hash_serviceinfo(self.url_hash)
            if serviceinfo_validate is False and self.partner_id is not None:
                init_sitemap_service_info(self.url_hash, self.service_name, self.status)

            taskinfo_validate = exist_url_hash_taskinfo(self.url_hash)
            if taskinfo_validate is False:
                init_task_info(self.url_hash, self.notify_status, self.generator, self.priority, self.request_id, self.task_type)
        except:
            logger.debug("Can't initial url information, url: {}".format(self.url))
            raise BreakTaskError
