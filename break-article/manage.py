#!/usr/bin/env python3
from breakarticle.factory import create_app
from breakarticle.atomlogging import init_logging
from flask_script import Manager

init_logging()
app = create_app()
manager = Manager(app)

if __name__ == '__main__':
    manager.run()
