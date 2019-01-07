from breakcontent.factory import create_app
import flask_script as script
from script import Manager


app = create_app()
manager = Manager(app)
# manager.add_command('runserver', script.Server(host='0.0.0.0', port=8000))
manager.add_command('shell', script.Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()
