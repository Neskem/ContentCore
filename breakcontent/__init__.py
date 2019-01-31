from flask_sqlalchemy import SQLAlchemy
from breakcontent import mylogging
import logging

logger = logging.getLogger()
db = SQLAlchemy()
