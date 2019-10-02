from breakcontent.factory import create_app
from breakcontent import db
from breakcontent import models
# from breakcontent import tasks
from flask_script import Server, Shell, Manager
from sys import argv

if __name__ == '__main__':
    app = create_app()


    def _make_context():
        return dict(app=app, db=db, models=models)


    manager = Manager(app)
    manager.add_command("runserver", Server(host='0.0.0.0', port=8100))
    manager.add_command("shell", Shell(make_context=_make_context))

    if argv[1] == 'runserver':
        app.logger.info(f'init flask in debug mode')
    elif argv[1] == 'shell':
        app.logger.info(f'enter flask shell mode')

    manager.run()

else:
    app = create_app()
    app.logger.info(f'init flask in production mode')
