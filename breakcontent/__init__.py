from flask_sqlalchemy import SQLAlchemy
from breakcontent import mylogging
import logging

from breakcontent.file_manager import ContextManager

logger = logging.getLogger()
# sqlalchemy-related env variable should be loaded automatically
db = SQLAlchemy()
