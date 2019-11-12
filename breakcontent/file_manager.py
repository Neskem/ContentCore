# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger('cc')


class ContextManager(object):
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode

    def __enter__(self):
        logger.info("Starting to open file {}".format(self.filename))
        try:
            self.open_file = open(self.filename, self.mode)
            return self.open_file
        except EOFError:
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Starting to close file {}".format(self.filename))
        self.open_file.close()




