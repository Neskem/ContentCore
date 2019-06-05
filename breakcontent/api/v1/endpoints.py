from flask import Blueprint, request, g, jsonify, current_app, abort
from flask_headers import headers
from flask_cors import cross_origin
from breakcontent import db
from breakcontent.api import errors
from sqlalchemy.orm import joinedload, Load, load_only
from breakcontent.models import TaskMain, WebpagesPartnerXpath, DomainInfo
import datetime


bp = Blueprint('endpoints', __name__)


@bp.route('/task', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_task():
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
    res = {'msg': '', 'status': False}
    wpxf = WebpagesPartnerXpath.query.filter_by(url_hash=url_hash).first()
    data = {'data': wpxf.to_ac()}
    res.update(data)
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
    current_app.logger.debug(f'domain{domain}, partner_id{partner_id}, run partner_setting_add_update()...')

    q = dict(domain=domain, partner_id=partner_id)
    data = request.json  # data should be a dict
    res = {'msg': '', 'status': False}
    idata = dict(rules=data)
    idata.update(q)

    di = DomainInfo()
    di.upsert(q, idata)

    res = {'msg': 'ok', 'status': True}
    return jsonify(res), 200


@bp.route('/hc/<itype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def health_check(itype: str=None):
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
    """
    this is a sync function
    too much request might halt my system
    return url_hash, publish_date to AC
    """
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
        sql_str = f'select a.url_hash, b.publish_date from task_main as a join webpages_partner_xpath as b on a.url_hash = b.url_hash where a.partner_id = \'{partner_id}\' and a.domain = \'{domain}\';'

        current_app.logger.debug(f'sql_str {sql_str}')

        wp_list = db.engine.execute(sql_str)
        current_app.logger.debug(f'wp_list {wp_list}')
        data = []
        for i in wp_list:
            adict = {}
            adict['url_hash'] = i['url_hash']
            adict['publish_date'] = i['publish_date']
            data.append(adict)

    res.update({
        'msg': 'ok',
        'status': True,
        'data': data
    })
    return jsonify(res), 200


@bp.route('/error/<etype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def error_handler(etype):
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
    elif etype == 6:
        pass


@bp.route('/content/extPage', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_external_content():
    res = {'msg': '', 'status': False}
    current_app.logger.debug(f'init_external_content start: request.json {request.json}')
    request_id = request.headers.get("X-REQUEST-ID", None)
    data = request.json

    required = ['url', 'url_hash', 'priority', 'partner_id']
    task_optional = ['request_id', 'generator', 'domain']
    wxp_optional = ['request_id', 'generator', 'domain', 'title', 'content', 'publish_date', 'cover', 'description', 'author']

    odata = {}
    wxp_data = {}
    odata['request_id'] = request_id
    ai_article = data['ai_article'] if data['ai_article'] else False
    for r in required:
        if not data.get(r, None):
            res['msg'] = f'{r} is required'
            return jsonify(res), 401

    for i in data.keys():
        if i not in required + task_optional:
            if i == '500':
                return jsonify(res), 500
        else:
            odata[i] = data[i]

    for i in data.keys():
        if i not in required + wxp_optional:
            if i == '500':
                return jsonify(res), 500
        else:
            wxp_data[i] = data[i]

    from breakcontent.tasks import init_external_task
    init_external_task.delay(odata, wxp_data, ai_article)

    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200
