from breakcontent.factory import create_celery_app
# from breakcontent.helper import generate_url_hash
# import loggings
import json
import requests
from flask import current_app
import xml.etree.ElementTree as ET
from sqlalchemy.exc import IntegrityError
from breakcontent import db
from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo

try:
    celery = create_celery_app()
except Exception as e:
    print('error here 01')
    current_app.logger.error(f'error here')
    raise


# @celery.task(bind=True)
# def upsert_main_task(self, data: dict):
#     '''
#     structure check already done by endpoint func init_task()
#     '''
#     print(data)
#     # current_app.logger.debug(data)
#     try:
#         idoc = TaskMain(**data)
#         # with app.app_context():
#         db.session.add(idoc)
#         db.session.commit()
#     except IntegrityError as e:
#         # insert failure do update
#         # current_app.logger.warning(f'{e}')
#         raise e


# @celery.task(bind=True)
# def upsert_main_task(self, data):
#     print('Lance test 01')
#     print(data)
#     print(type(data))
