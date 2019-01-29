from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


def do_upsert(table: object, data: dict, key: 'string: column with unique constraint', rkey: 'string: relationship column' = None, rtable: 'object: backref table object' = None, rdata: 'dict: required column in downstream table' = None, rukey: str = None):
    '''
    a wrapper function
    '''

    def do_r_upsert(idoc: object, rkey, rdata, rtable, rukey):
        '''
        do upsert on table with relationship
        '''
        logger.debug('run do_r_upsert()...')
        if hasattr(idoc, rkey):
            setattr(idoc, rkey, rtable(**rdata))
            try:
                db.session.add(idoc)
                db.session.commit()
                logger.debug(f'table: {rtable.__tablename__}, insert: {rdata}')
            except IntegrityError as e:
                logger.warning(
                    f'failed to insert rtable, do update instead: {e}')
                db.session.rollback()
                logger.debug('db.rollback() done')

                qq = {rukey: rdata[rukey]}
                logger.debug(f'qq {qq}')
                db.session.query(rtable).filter_by(
                    **qq).update({**rdata})
                db.session.commit()
                logger.debug(f'table: {rtable.__tablename__}, update: {rdata}')
        else:
            logger.error(f'{idoc} do not has attr: {rkey}')

    try:
        idoc = table(**data)
        db.session.add(idoc)
        db.session.commit()
        logger.debug(f'table: {table.__tablename__}, insert: {data}')
        if rkey and rtable and rdata:
            do_r_upsert(idoc, rkey, rdata, rtable, rukey)
        else:
            logger.debug(f'table: {table.__tablename__}, insert: {data}')
    except IntegrityError as e:
        logger.warning(f'failed to insert: {e}')
        db.session.rollback()
        q = {key: data[key]}
        db.session.query(table).filter_by(
            **q).update({**data})
        db.session.commit()
        logger.debug(f'table: {table.__tablename__}, update: {data}')
        if rkey and rtable and rdata:
            idoc = db.session.query(table).filter_by(
                **q).first()
            do_r_upsert(idoc, rkey, rdata, rtable, rukey)
