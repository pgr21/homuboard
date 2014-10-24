from . import app
import psycopg2
from psycopg2.extras import DictCursor
from flask import g
from werkzeug.local import LocalProxy

def get_db():
    db = getattr(g, 'db', None)
    if not db: db = g.db = psycopg2.connect(dbname=app.config['DB'], cursor_factory=DictCursor)
    return db

db = LocalProxy(get_db)

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, 'db', None)
    if db: db.close()
