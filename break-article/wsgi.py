from breakarticle.factory import create_app
from breakarticle.atomlogging import init_logging
import sys

if __name__ == '__main__':
    init_logging(console=True)
    app = create_app()
    if sys.argv[-1] == '--init':
        from breakarticle.model import db
        with app.app_context():
            db.create_all()
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=8100)
else:
    init_logging()
    app = create_app()
