import pickle

from flask_sqlalchemy import SQLAlchemy
from breakcontent import mylogging
import logging

from breakcontent.file_manager import ContextManager

logger = logging.getLogger()
# sqlalchemy-related env variable should be loaded automatically
db = SQLAlchemy()

with ContextManager("parser_rules.pickle", "wb+") as file:
    try:
        crawler_rules = pickle.load(file)
    except EOFError:
        crawler_rules = {"breaktime.com": {}}
        pickle.dump(crawler_rules, file)
