from breakcontent.factory import create_app
import sys
from flask_script import Server, Shell, Manager

app = create_app()

if __name__ == '__main__':
    def _make_context():
        return dict(app=app, db=db, models=content)
    manager = Manager(app)
    manager.add_command("runserver", Server(host='0.0.0.0', port=8100))
    manager.add_command("shell", Shell(make_context=_make_context))
    app.logger.info(f'init flask in debug mode')
    manager.run()
else:
    app.logger.info(f'init flask in production mode')
