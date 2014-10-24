from . import app
from flask import render_template, request, flash, redirect, url_for, session
from .db import db
from .mysql import mysql323
from .user import user

@app.context_processor
def inject_env():
    return {'site_name': app.config['SITE_NAME']}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    url = request.form.get('next', url_for('index'))

    with db.cursor() as cur:
        cur.execute('''
            SELECT id
            FROM "user"
            WHERE username=%s AND password=%s
        ''', [username, mysql323(password.encode('utf-8'))])

        user = cur.fetchone()

    if not user:
        flash('Invalid username or password')
        return redirect(url)

    session['user_id'] = user['id']
    return redirect(url)

@app.route('/logout/')
def logout():
    del session['user_id']
    return redirect(request.args.get('next', url_for('index')))

@app.route('/board/<id>/')
def board(id):
    with db.cursor() as cur:
        cur.execute('''
            SELECT post.id, post.name, "user".name AS user_name, post.ts, views, votes
            FROM post JOIN "user" ON post.user_id = "user".id
            WHERE board_id=%s
            ORDER BY post.ts DESC LIMIT 20
        ''', [id])

        posts = cur.fetchall()

    return render_template('board.html', posts=posts)

@app.route('/post/<id>/')
def post(id):
    with db.cursor() as cur:
        cur.execute('''
            SELECT post.id, post.name, "user".name AS user_name, post.ts, text
            FROM post JOIN "user" ON post.user_id = "user".id
            WHERE post.id=%s
        ''', [id])

        post = cur.fetchone()

    return render_template('post.html', post=post)
