from flask import Blueprint, jsonify, redirect, url_for, Response, current_app
# import jwt
import json
from breakcontent.api.v1.endpoints import bp
from breakcontent.api.errors import LanceError, InvalidUsage, AlanError
from sqlalchemy.exc import IntegrityError, InvalidRequestError, OperationalError


# from breakcontent import mylogging
# import logging
# current_app.logger = logging.getLogger('default')


@bp.errorhandler(LanceError)
def handle_lance_error(e):
    # current_app.logger.error(f'this is a customized Exception:')
    response = dict(status=0, message="500 Error")
    return jsonify(response), 500


@bp.errorhandler(404)
def error_404(e):
    # current_app.logger.error(f'this is a 404 error')
    response = dict(status=0, message="404 Error from CC")
    return jsonify(response), 404


@bp.errorhandler(OperationalError)
def handle_operationalerror(e):
    response = dict(status=0, message="DB OperationalError from CC")
    return jsonify(response), 500


@bp.errorhandler(InvalidUsage)
def handle_invalid_usage(e):
    response = jsonify(e.to_dict())
    response.status_code = e.status_code
    return response


@bp.errorhandler(KeyError)
# @bp.errorhandler(Exception)
def handle_key_error(e):
    current_app.logger.error(f'this is a KeyError')
    response = dict(status=0, message="KeyError from CC")
    return jsonify(response), 401


@bp.errorhandler(AlanError)
def handle_alan(e):
    current_app.logger.error(f'this is a AlanError')
    response = dict(status=0, message="KeyError by Alan")
    current_app.logger.error(f'response {response}')
    # return jsonify(response), 401
