from breakarticle.factory import create_app
from breakarticle.model import db
from breakarticle.model import article

app = create_app()
with app.app_context():
    db.create_all()
    db.session.commit()
