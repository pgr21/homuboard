from . import app
from werkzeug.local import LocalProxy
from flask import session
from .db import db

def get_user():
    user_id = session.get('user_id', None)

    if not user_id: return None

    with db.cursor() as cur:
        cur.execute('''
            SELECT name
            FROM "user"
            WHERE id=%s
        ''', [user_id])

        user = cur.fetchone()

    return user

user = LocalProxy(get_user)

@app.context_processor
def inject_user():
    return {'user': user}
