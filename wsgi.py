from breakcontent.factory import create_app
# from breakcontent.atomlogging import init_logging
import sys

if __name__ == '__main__':
    # init_logging(console=True)
    app = create_app()
    if sys.argv[-1] == '--init':
        from breakcontent.model import db
        with app.app_context():
            db.create_all()
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=8100)
else:
    # init_logging()
    app = create_app()

    with app.app_context():
        from breakcontent.model import db
        # This command is necessary for create_all() that means which table will be created. ex: only content or ..etc
        from breakcontent.model import content

        db.create_all()
        db.session.commit()
