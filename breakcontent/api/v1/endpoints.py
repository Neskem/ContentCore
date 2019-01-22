from flask import Blueprint, request, g, jsonify, current_app, abort
from flask_headers import headers
from flask_cors import cross_origin
from breakcontent import db
from breakcontent.helper import api_ok
import json
from breakcontent.api import errors
from breakcontent.api.v1 import alan
# from breakcontent.api.v1.alan import AlanErrorClass

from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo
# import breakcontent.tasks as tasks

bp = Blueprint('endpoints', __name__)


@bp.route('/test', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def test():
    '''
    curl -v -X POST 'http://localhost:8100/v1/test' -H 'Content-Type: application/json'

    '''
    res = {'msg': '', 'status': False}

    from breakcontent.tasks import test_task
    test_task.delay()

    return jsonify(res), 200


@bp.route('/task', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_task():
    '''
    # insert singlepage partner
    curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "aaaa619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.kocpc.com.tw/archives/693", "url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'

    # insert multipage partner
    curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "bbbb619f-576c-4473-add2-e53d08b74ac7", "url": "https://kafkalin.com/magpiecafe/", "url_hash": "5532f49157b55651c8ab313cd91e5d93eee1ce75", "priority": 2, "partner_id": "UYTFH18", "generator": "WordPress2", "notexpected": "deadline is 1/31"}'

    # insert not partner
    curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "test2", "url": "test2", "url_hash": "test2", "priority": 1, "generator": "test2", "notexpected": "test2"}'
    '''

    current_app.logger.error(f'use current_app and sentry to log')
    res = {'msg': '', 'status': False}
    data = request.json

    required = [
        'request_id',
        'url',
        'url_hash',
        'priority'
    ]

    optional = [
        'partner_id',
        'generator'
    ]

    odata = {}

    for r in required:
        if not data.get(r, None):
            res['msg'] = f'{r} is required'
            return jsonify(res), 401

    for i in data.keys():
        if i not in required + optional:
            current_app.logger.warning(
                f'drop unexpected key {i}:{data[i]} from input payload')
        else:
            odata[i] = data[i]

    from breakcontent.tasks import upsert_main_task
    upsert_main_task.delay(odata)

    # # for testing purpose
    # from breakcontent.tasks import create_tasks
    # create_tasks.delay(1)

    return jsonify(res), 200


@bp.route('/delete_task', methods=['DELETE'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def delete_task():
    '''
    # delete partner from maintask
    curl -v -X DELETE 'http://localhost:8100/v1/delete_task' -H 'Content-Type: application/json' -d '{"url_hash": "ce65ca9a29f408496abfb7e7a978b2d4e31d93df"}'

    # delete nopartner from maintask
    curl -v -X DELETE 'http://localhost:8100/v1/delete_task' -H 'Content-Type: application/json' -d '{"url_hash": "test2"}'
    '''

    res = {'msg': '', 'status': False}
    data = request.json

    from breakcontent.tasks import delete_main_task
    delete_main_task.delay(data)

    return jsonify(res), 200


@bp.route('/create_tasks/<priority>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def create_tasks(priority):
    '''
    # delete partner from maintask
    curl -v -X GET 'http://localhost:8100/v1/create_tasks/1'
    '''

    res = {'msg': '', 'status': False}
    data = request.json

    from breakcontent.tasks import create_tasks
    create_tasks.delay(priority)

    return jsonify(res), 200


@bp.route('/error/<etype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def error_handler(etype):
    '''
    curl -v -X GET 'http://localhost:8100/v1/error/2'
    '''
    res = {'msg': '', 'status': False}

    current_app.logger.debug(f'type {type(etype)}')
    etype = int(etype)
    current_app.logger.debug(f'type {type(etype)}')
    if etype == 1:
        raise errors.LanceError
    elif etype == 2:
        abort(404)
    elif etype == 3:
        raise errors.InvalidUsage('invalid usage', status_code=410)
    elif etype == 4:
        adict = {'a': 'aaa'}
        # try:
        #     tmp = adict['b']
        # except Exception as e:
        #     raise
        tmp = adict['b']
    elif etype == 5:
        current_app.logger.debug('alan error test')
        try:
            alan.sub_error()
        except:
            pass
        # aec = AlanErrorClass()
        # try:
        #     aec.sub_error()
        # except Exception as e:
        #     pass
        return jsonify(res), 200
    elif etype == 6:
        pass
