from flask_sqlalchemy import SQLAlchemy
from breakcontent import mylogging
import logging

from breakcontent.file_manager import ContextManager

KUBERNETES = 35


class KubernetesLogger(logging.Logger):
    def kubernetes(self, msg, *args, **kwargs):
        if self.isEnabledFor(KUBERNETES):
            self._log(KUBERNETES, msg, args, kwargs)


logging.addLevelName(KUBERNETES, 'KUBERNETES')
logging.setLoggerClass(KubernetesLogger)

logger = logging.getLogger()
# sqlalchemy-related env variable should be loaded automatically
db = SQLAlchemy()
