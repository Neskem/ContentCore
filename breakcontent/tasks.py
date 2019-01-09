from breakcontent.factory import create_celery_app
# from breakcontent.helper import generate_url_hash
# import loggings
import json
import requests
import xml.etree.ElementTree as ET
from breakcontent import db
celery = create_celery_app()


# @celery.task(bind=True)
# def upsert_main_task(task, data: 'json'):
#     print(data)
#     print(type(data))
#     indata = json.loads(data)
#     print('Lance test')
#     print(indata)
#     print(type(indata))
# for r in required:
#     if data.get(r, None):
#         kwargs = {}
#         kwargs[r] = data[r]
#         indoc = TaskMain(**kwargs)
#         db.session.add(indoc)
#     else:
#         res['msg'] = f'{r} is required'

# for o in optional:
#     if data.get(o, None):
#         kwargs = {}
#         kwargs[o] = data[o]
#         indoc = TaskMain(**kwargs)
#         db.session.add(indoc)

# db.session.commit()

@celery.task(bind=True)
def upsert_main_task(task):
    print('Lance test')
    # print(data)
