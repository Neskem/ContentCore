from sqlalchemy.exc import IntegrityError

from breakcontent import db


def pg_add_wrapper(row, retry=2, with_primary_key=False):
    while retry:
        retry -= 1
        try:
            db.session.add(row)
            db.session.commit()
            if with_primary_key is True:
                return row.id
            else:
                pass
        except IntegrityError as e:
            raise e
        except Exception as e:
            if retry <= 0:
                db.session.rollback()
                raise e
