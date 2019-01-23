from breakcontent.api import errors


def sub_error():
    raise errors.AlanError


def key_error():
    raise KeyError


class AlanErrorClass:

    def sub_error(self):
        raise errors.AlanError
