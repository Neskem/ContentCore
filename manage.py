#!/usr/bin/env python3
from breakcontent.factory import create_app
from breakcontent.atomlogging import init_logging
from flask_script import Manager

# init_logging()
app = create_app()
manager = Manager(app)

if __name__ == '__main__':
    manager.run()
