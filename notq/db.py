from sqlalchemy import create_engine, insert, text

import click
from flask import current_app, g

from notq.db_structure import db_metadata, user_table

g_engine = None

def get_db():
    global g_engine
    if not g_engine:
        g_engine = create_engine(current_app.config['DATABASE'])
    if 'db' not in g:
        g.db = g_engine.connect()

    return g.db

def db_execute(query, **kwargs):
    return get_db().execute(text(query), kwargs)

def db_execute_commit(query, **kwargs):
    db = get_db()
    db.execute(text(query), kwargs)
    db.commit()

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    global g_engine
    g_engine = create_engine(current_app.config['DATABASE'])
    db_metadata.drop_all(g_engine)
    db_metadata.create_all(g_engine)
    db = g_engine.connect()
    db.execute(insert(user_table).values(username='anonymous',password=''))
    db.commit()

@click.command('init-db-drops-all-extremely-unsafe')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
