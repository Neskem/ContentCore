import logging
import logging.config
import uuid
import flask
import os
import simplejson
from breakcontent.mylogging import MY_LOGGINGS

# Available logging levels:
# DEBUG
# INFO
# WARNING
# ERROR
# CRITICAL

# make sure to initialize logging once to avoid breaking logging for Flask
log_init = False


# Custom logging filter class
class RequestIdFilter(logging.Filter):
    """
    This is a logging filter that makes the request ID available for use in
    the logging format. Note that we're checking if we're in a request
    context, as we may want to log things before Flask is fully loaded.
    """

    def filter(self, record):
        record.request_id = request_id() if flask.has_request_context() else '-'
        return True


def request_id():
    """
    Returns the current request ID or a new one if there is none
    In order of preference:
      * If we've already created a request ID and stored it in the flask.g context local, use that
      * If a client has passed in the X-Request-Id header, create a new ID with that prepended
      * Otherwise, generate a request ID and store it in flask.g.request_id
    :return:
    """
    if getattr(flask.g, 'request_id', None):
        return flask.g.request_id

    headers = flask.request.headers
    original_request_id = headers.get("X-REQUEST-ID")
    new_uuid = generate_request_id(original_request_id)
    flask.g.request_id = new_uuid

    return new_uuid

# Generate a new request ID, optionally including an original request ID


def generate_request_id(original_id=''):
    if original_id:
        new_id = original_id
    else:
        new_id = uuid.uuid4()
    return new_id


# def init_logging(console=False):
#     global log_init
#     if log_init:
#         return

#     if console:
#         logging.basicConfig(
#             level=logging.DEBUG, format='%(asctime)s %(levelname)s %(module)s %(lineno)d %(message)s')
#     else:
#         logging.config.dictConfig(MY_LOGGINGS)
#     log_init = True
