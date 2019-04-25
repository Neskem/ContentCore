from flask import Blueprint, request, g, jsonify, current_app, abort
from flask_headers import headers
from flask_cors import cross_origin
from breakcontent import db
import json
from breakcontent.api import errors
import datetime
from sqlalchemy.orm import joinedload, Load, load_only

from breakcontent.models import TaskMain, TaskService, TaskNoService, WebpagesPartnerXpath, WebpagesPartnerAi, WebpagesNoService, StructureData, UrlToContent, DomainInfo, BspInfo

bp = Blueprint('endpoints', __name__)


@bp.route('/task', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_task():
    '''
    # insert singlepage partner
    curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "aaaa619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.kocpc.com.tw/archives/693", "url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'

    # only url_hash changed
    curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "aaaa619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.kocpc.com.tw/archives/693", "url_hash": "aaaa2aaef4856b23d7d8016e4e77409001d999fa", "priority": 1, "partner_id": "3WYST18", "generator": "WordPress2", "notexpected": "blablabla"}'

    # insert multipage partner
    curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "bbbb619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.top1health.com/Article/55932?page=1", "url_hash": "5532f49157b55651c8ab313cd91e5d93eee1ce75", "priority": 2, "partner_id": "VM22718", "generator": "WordPress2", "notexpected": "deadline is 1/31"}'

    # insert multipage parent page
    curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "eeee619f-576c-4473-add2-e53d08b74ac7", "url": "https://www.top1health.com/Article/55932", "url_hash": "eeeef49157b55651c8ab313cd91e5d93eee1ce75", "priority": 2, "partner_id": "VM22718", "generator": "WordPress2", "notexpected": "deadline is 1/31"}'

    # insert not partner
    curl -v -X POST 'http://localhost:80/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "ffff619f-576c-4473-add2-e53d08b74ac7", "url": "https://news.sina.com.tw/article/20190215/30068464.html?fbclid=IwAR25e4TpKc9rTsKN2tUt-4PQZoYJCmoBgfj7xmWr22j2bBGuTkQyQ5oQVEo", "url_hash": "f19535b1374ef771502d8fe488fbc57e77d2c96d", "priority": 3, "domain": "news.sina.com.tw", "generator": ""}'

    if {"500": "blablabla"} exists return 500

    # Rule check should be False
    curl -v -X POST 'http://localhost:8100/v1/task' -H 'Content-Type: application/json' -d '{"request_id": "aaaa619f-576c-4473-add2-e53d08b74ac7", "url": "https://ez3c.tw/tag/powercfg%20batteryreport-1", "url_hash": "9039f44873d8d2e0fef8c53a8f58fe5244be8c07", "priority": 2, "partner_id": "PPY6H18", "generator": "", "notexpected": "blablabla"}'

    # 20190123 update
    get request_id from header

    '''

    # current_app.logger.error(f'use current_app and sentry to log')
    res = {'msg': '', 'status': False}

    current_app.logger.debug(f'request.json {request.json}')
    request_id = request.headers.get("X-REQUEST-ID", None)
    data = request.json

    required = [
        'url',
        'url_hash',
        'priority',
    ]

    optional = [
        'request_id',
        'partner_id',
        'generator',
        'domain'
    ]

    odata = {}
    odata['request_id'] = request_id
    for r in required:
        if not data.get(r, None):
            res['msg'] = f'{r} is required'
            return jsonify(res), 401

    for i in data.keys():
        if i not in required + optional:
            current_app.logger.warning(
                f'drop unexpected key {i}:{data[i]} from input payload')
            if i == '500':
                return jsonify(res), 500
        else:
            odata[i] = data[i]

    from breakcontent.tasks import upsert_main_task
    upsert_main_task.delay(odata)

    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/delete_task', methods=['DELETE'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def delete_task():
    '''
    # delete partner from maintask
    curl -v -X DELETE 'http://localhost:80/v1/delete_task' -H 'Content-Type: application/json' -d '{"url_hash": "a6d62aaef4856b23d7d8016e4e77409001d999fa"}'

    # delete nopartner from maintask
    curl -v -X DELETE 'http://localhost:80/v1/delete_task' -H 'Content-Type: application/json' -d '{"url_hash": "test2"}'
    '''

    res = {'msg': '', 'status': False}
    data = request.json

    from breakcontent.tasks import delete_main_task
    delete_main_task.delay(data)
    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/create_tasks/<priority>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def create_tasks(priority):
    '''
    # delete partner from maintask
    curl -v -X GET 'http://localhost:80/v1/create_tasks/1'
    '''

    res = {'msg': '', 'status': False}
    data = request.json

    from breakcontent.tasks import create_tasks
    create_tasks.delay(priority)
    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/content/<url_hash>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def get_content(url_hash):
    '''
    AC requesting article

    this is a sync function

    <example>
    curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:80/v1/content/a6d62aaef4856b23d7d8016e4e77409001d999fa'

    curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:80/v1/content/2151238f566088dd8f5b56857938f28dced4d899'

    '''

    res = {'msg': '', 'status': False}

    wpxf = WebpagesPartnerXpath.query.filter_by(url_hash=url_hash).first()
    data = {'data': wpxf.to_ac()}
    res.update(data)
    # wpxf_json = json.dumps(wpxf.to_ac())
    # current_app.logger.debug(f'wpxf_json {wpxf_json}')
    res.update({
        'msg': 'ok',
        'status': True
    })
    # record sent_content_time/sent_content_ini_time in TaskMain
    wpxf.task_service.sent_content_time = datetime.datetime.utcnow()
    if not wpxf.task_service.sent_content_ini_time:
        wpxf.task_service.sent_content_ini_time = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify(res), 200


@bp.route('/partner/setting/<partner_id>/<domain>', methods=['PUT', 'POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def partner_setting_add_update(partner_id, domain):
    '''
    curl -v -X PUT -H 'Content-Type: application/json' 'http://localhost:80/v1/partner/setting/3WYST18/www.kocpc.com.tw' -d '{"xpath": "blablabla"}'

    this is a sync func
    '''
    current_app.logger.debug('run partner_setting_add_update()...')

    q = dict(domain=domain, partner_id=partner_id)
    data = request.json  # data should be a dict
    res = {'msg': '', 'status': False}
    idata = dict(rules=data)
    idata.update(q)

    di = DomainInfo()
    di.upsert(q, idata)

    # di = DomainInfo.query.filter_by(**q).first()
    # if di:
    #     # update no matter what
    #     db_session_update(db.session, DomainInfo, q, idata)
    # else:
    #     # insert
    #     doc = DomainInfo(**idata)
    #     db_session_insert(db.session, doc)

    res = {'msg': 'ok', 'status': True}
    return jsonify(res), 200


@bp.route('/hc/<itype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def health_check(itype: str=None):
    '''
    this is a sync function

    daily health check

    curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:8100/v1/hc/all'

    curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:8100/v1/hc/day'

    curl -v -X GET -H 'Content-Type: application/json' 'http://localhost:8100/v1/hc/hour'

    '''
    current_app.logger.debug('run health_check()...')
    res = {'msg': '', 'status': False}

    if itype not in ['all', 'day', 'hour']:
        abort(500)

    from breakcontent.tasks import stats_cc
    data = stats_cc(itype)

    current_app.logger.debug(f'data {data}')

    res.update({
        'msg': 'ok',
        'status': True,
        'data': data
    })
    return jsonify(res), 200


@bp.route('/content/<partner_id>/<domain>/pd', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def get_pd(partner_id, domain):
    '''
    a sync function

    too much request might halt my system

    return url_hash, publish_date to AC
    '''
    current_app.logger.debug('run get_pd()...')
    res = {'msg': '', 'status': False}

    if 0:
        # query only with domain, should be fastest
        q = dict(domain=domain)
        wp_list = WebpagesPartnerXpath.query.options(
            load_only('url_hash', 'publish_date')).filter_by(**q).all()
        current_app.logger.debug(f'len wp_list {len(wp_list)}')
        data = []
        for i in wp_list:
            adict = {}
            adict['url_hash'] = i.url_hash
            adict['publish_date'] = i.publish_date
            data.append(adict)

    if 0:
        # orm join works but painful
        q = dict(partner_id=partner_id, domain=domain)
        wp_list = db.session.query(TaskMain).options(joinedload('wpx', innerjoin=True).load_only(
            'publish_date'), Load(TaskMain).load_only('url_hash')).all()

        current_app.logger.debug(f'len wp_list {len(wp_list)}')
        data = []

        for i in wp_list:
            # i is object of TaskMain
            adict = {}
            adict['url_hash'] = i.url_hash
            adict['publish_date'] = i.wpx[0].publish_date
            data.append(adict)

    if 1:
        # raw sql
        sql_str = f'select a.url_hash, b.publish_date from task_main as a join webpages_partner_xpath as b on a.url_hash = b.url_hash where a.partner_id = \'{partner_id}\' and a.domain = \'{domain}\';'

        current_app.logger.debug(f'sql_str {sql_str}')

        wp_list = db.engine.execute(sql_str)
        current_app.logger.debug(f'wp_list {wp_list}')
        data = []
        for i in wp_list:
            # i is object of TaskMain
            adict = {}
            adict['url_hash'] = i['url_hash']
            adict['publish_date'] = i['publish_date']
            data.append(adict)

    # current_app.logger.debug(f'wp_list {wp_list}')

    res.update({
        'msg': 'ok',
        'status': True,
        'data': data
    })
    return jsonify(res), 200

# ===== Below are for debug use =====


@bp.route('/error/<etype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def error_handler(etype):
    '''
    curl -v -X GET 'http://localhost:80/v1/error/2'
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
    # elif etype == 5:
    #     current_app.logger.debug('alan error test')
    #     try:
    #         alan.sub_error()
    #     except:
    #         pass
    #     # aec = AlanErrorClass()
    #     # try:
    #     #     aec.sub_error()
    #     # except Exception as e:
    #     #     pass
    #     return jsonify(res), 200
    elif etype == 6:
        pass
