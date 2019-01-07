from .factory import create_celery_app
from breakcontent.helper import generate_url_hash
# from breakcontent.contentclass.task_manager import TaskInitialization
# from breakcontent.contentclass.partner_manager import get_sitemap_url
# from breakcontent.contentclass.orm_content import async_filter_urlinfo, generate_aysc_info, check_task_status_to_doing
# from breakcontent.contentclass.orm_content import main_update_filter_urlinfo, exist_url_hash_urlinfo

import logging
import json
import requests
import xml.etree.ElementTree as ET
celery = create_celery_app()
