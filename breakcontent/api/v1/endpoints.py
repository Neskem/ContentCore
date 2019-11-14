from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, current_app, abort
from flask_headers import headers
from flask_cors import cross_origin

from breakcontent.orm_content import get_webpages_xpath, get_partner_domain_rules, init_partner_domain_rules, \
    update_partner_domain_rules
from breakcontent.utils import verify_ac_token

bp = Blueprint('endpoints', __name__)


@bp.route('/task', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_task():
    res = {'msg': '', 'status': False}
    current_app.logger.debug(f'request.json {request.json}')
    jwt_token = request.headers.get("Authorization", None)
    verify_successfully, token = verify_ac_token(jwt_token)
    if verify_successfully is False:
        res['msg'] = f'Authorization is not correct.'
        return jsonify(res), 401

    data = request.json

    if 'url' not in data or 'url_hash' not in data or 'priority' not in data:
        res['msg'] = 'Lack of required parameters'
        return jsonify(res), 401

    if data.get('domain', None):
        pass
    else:
        o = urlparse(data['url'])
        domain = o.netloc
        data['domain'] = domain

    data['request_id'] = request.headers.get("X-REQUEST-ID", None)
    data.setdefault('partner_id', None)
    data.setdefault('generator', None)

    from breakcontent.tasks import upsert_main_task
    upsert_main_task.delay(data)

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
    jwt_token = request.headers.get("Authorization", None)

    verify_successfully, token = verify_ac_token(jwt_token)
    if verify_successfully is False:
        res['msg'] = f'Authorization is not correct.'
        return jsonify(res), 401
    from breakcontent.tasks import delete_main_task
    if "url_hash" in data:
        delete_main_task.delay(data["url_hash"])
        res.update({
            'msg': 'ok',
            'status': True
        })
    else:
        res.update({
            'msg': 'Can not find the url_hash',
            'status': False
        })
    return jsonify(res), 200


@bp.route('/create_tasks/<priority>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def create_tasks(priority):
    res = {'msg': '', 'status': False}

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
    jwt_token = request.headers.get("Authorization", None)

    verify_successfully, token = verify_ac_token(jwt_token)
    if verify_successfully is False:
        res['msg'] = f'Authorization is not correct.'
        return jsonify(res), 401
    webpages_data = get_webpages_xpath(url_hash)
    return_data = {'data': {'url': webpages_data.url, 'url_structure_type': webpages_data.url_structure_type,
                            'title': webpages_data.title, 'cover': webpages_data.cover,
                            'content': webpages_data.content,
                            'publishedAt': webpages_data.publish_date.isoformat()
                            if webpages_data.publish_date is not None else ''}}
    res.update(return_data)
    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/partner/setting/<partner_id>/<domain>', methods=['PUT', 'POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def partner_setting_add_update(partner_id, domain):
    current_app.logger.debug(f'domain{domain}, partner_id{partner_id}, run partner_setting_add_update()...')
    res = {'msg': '', 'status': False}
    rules = get_partner_domain_rules(partner_id, domain)
    data = request.json

    if rules is False:
        init_partner_domain_rules(partner_id, domain, data)
    else:
        update_partner_domain_rules(partner_id, domain, data)

    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/hc/<itype>', methods=['GET'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def health_check(itype: str = None):
    current_app.logger.debug('run health_check()...')
    res = {'msg': '', 'status': False}

    if itype != 'all' and itype != 'day' and itype != 'hour':
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


@bp.route('/content/extPage', methods=['POST'])
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
@cross_origin()
def init_external_content():
    res = {'msg': '', 'status': False}
    current_app.logger.debug(f'init_external_content start: request.json {request.json}')
    jwt_token = request.headers.get("Authorization", None)

    verify_successfully, token = verify_ac_token(jwt_token)
    if verify_successfully is False:
        res['msg'] = f'Authorization is not correct.'
        return jsonify(res), 401

    data = request.json
    data['request_id'] = request.headers.get("X-REQUEST-ID", None)
    if 'url' not in data or 'url_hash' not in data or 'priority' not in data or 'partner_id' not in data or \
            'request_id' not in data or 'title' not in data or 'content' not in data:
        res['msg'] = "lack of required parameters"
        return jsonify(res), 401

    # check all parameters expect for requires.
    if data.get('domain', None):
        pass
    else:
        o = urlparse(data['url'])
        domain = o.netloc
        data['domain'] = domain
    data.setdefault('generator', None)
    data.setdefault('publish_date', None)
    data.setdefault('cover', None)
    data.setdefault('description', None)
    data.setdefault('author', None)
    data.setdefault('ai_article', False)

    from breakcontent.tasks import init_external_task
    init_external_task.delay(data)

    res.update({
        'msg': 'ok',
        'status': True
    })
    return jsonify(res), 200


@bp.route('/health', methods=['GET'])
@headers({'Content-Type': 'text/json'})
@headers({'Cache-Control': 's-maxage=0, max-age=0'})
def hc():
    res = {'msg': 'This endpoint for GCP health check', 'status': True}
    return jsonify(res), 200
