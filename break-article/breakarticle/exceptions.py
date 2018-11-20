class BreakException(Exception):
    """Base exception"""
    pass


class BreakPartnerError(BreakException):
    """error during get partner setting from partner system"""
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
