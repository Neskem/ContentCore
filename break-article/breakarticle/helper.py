from flask import current_app, make_response, request
from flask.json import jsonify
from breakarticle.model import db
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
from functools import update_wrapper
import datetime
import logging

# error codes should be tuned
error_threshold = 400
err_dict = defaultdict(lambda: (500, "Unknown error"), {
        # Generic
        'OK': (200, 'OK'),
        'CREATED': (201, 'CREATED'),
        'ACCEPTED': (202, 'ACCEPTED'),
        'NOT_MODIFIED': (304, 'Not modified'),
        'BAD_REQUEST': (400, 'Bad request'),
        'NOT_AUTHORIZED': (401, 'Not authorized'),
        'NOT_FOUND': (404, 'Not Found'),
        'INTERNAL_ERROR': (500, "Internal error"),
        'NOT_IMPLEMENTED': (518, 'Method not implemented'),
        'INVALID_APIKEY': (401, 'Apikey is missing or invalid'),
        'INVALID_AUTH_INFO': (403, 'Auth info is missing or invalid'),
        'AUTH_FAILED': (403, 'Auth failed'),
        'CONFLICT': (409, 'Resource state is conflict'),
        # API specific
        'INVALID_KEY_TYPE': (1000, 'Key type is missing or invalid'),
        'KEY_TYPE_NOT_ALLOWED': (1001, 'Key type is not allowed'),
        'NO_PARENT_CERT': (1002, 'Parent certificate does not exist'),
        'INVALID_KEY_NAME': (1010, 'Key name is invalid'),
        'VALIDITY_PERIOD_TOO_LONG': (1020, 'Validity period is too long'),
        'DUPLICATE_CLIENT_CERT': (1030, 'duplicate client crtificate'),
        'INVALID_QURI': (1040, 'mqtt uri is invalid'),
})


def api_err(name='INTERNAL_ERROR', data=None, message=None, log_level='INFO'):
    err_obj = err_dict[name]
    ret_obj = dict()

    try:
        getattr(logging, log_level.lower())('API %s %s %s', request.method, request.path, name)
    except AttributeError:
        logging.error("logging method {} did not exist".format(log_level))

    if data is None:
        ret_obj['data'] = {}
    else:
        ret_obj['data'] = data

    if message is None:
        ret_obj['message'] = err_obj[1]

    if err_obj[0] >= error_threshold:
       ret_obj['error_code'] = err_obj[0]

    return jsonify(ret_obj)


def api_ok(ret_str, **kwargs):
    log_level = 'INFO'
    return api_err(name=ret_str, data=kwargs, log_level=log_level)


def api_pattern_exist(log_level='INFO', **kwargs):
    return api_err(name='NOT_MODIFIED', data=kwargs, log_level=log_level)


def api_created(log_level='INFO', **kwargs):
    return api_err(name='CREATED', data=kwargs, log_level=log_level)

def api_accepted(log_level='INFO', **kwargs):
    return api_err(name='ACCEPTED', data=kwargs, log_level=log_level)

def crossdomain(allow_origins=None, methods=None, headers='Authorization',
                max_age=21600, attach_to_all=True,
                automatic_options=True, **kwargs):
    if allow_origins is None:
        allow_origins = set(current_app.config['ALLOW_ORIGINS'])
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)

    if isinstance(max_age, datetime.timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))

            if ('Origin' in request.headers and
                    request.headers['Origin'] in allow_origins):
                origin = request.headers['Origin']
                h = resp.headers
                h['Access-Control-Allow-Origin'] = origin
                h['Access-Control-Allow-Methods'] = get_methods()
                h['Access-Control-Max-Age'] = str(max_age)
                if headers is not None:
                    h['Access-Control-Allow-Headers'] = headers

            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def pg_add_wrapper(row, retry=2, with_primary_key=False):
    while retry:
        retry -= 1
        try:
            db.session.add(row)
            db.session.commit()
            if with_primary_key is True:
                return row.id
            else:
                pass
        except IntegrityError as e:
            raise e
        except Exception as e:
            if retry <= 0:
                db.session.rollback()
                raise e
