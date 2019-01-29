class LanceError(Exception):
    pass


class AlanError(Exception):
    pass


class InvalidUsage(Exception):
    '''
    example from
    http://flask.pocoo.org/docs/1.0/patterns/apierrors/
    '''
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class BreakException(Exception):
    """Base exception"""
    pass


class BreakPartnerError(BreakException):
    """error during get partner setting from partner system"""
    pass


class BreakTaskError(BreakException):
    """error during initial task or insert task record to database"""
    pass


class BreakPartnerMessageError(BreakException):
    """
    the sample for exception for out message.
    trigger: raise BreakPartnerMessageError("Pattern file is required field")
    """
    message = None

    def __init__(self, message):
        super(BreakPartnerMessageError, self).__init__()
        self.message = message
