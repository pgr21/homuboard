from . import app
from flask import render_template, request, flash, redirect, url_for, session
from .db import db
from .mysql import mysql323
from .user import user
from datetime import datetime

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

    board = {
        'id': id,
    }

    return render_template('board.html', board=board, posts=posts)

@app.route('/post/<id>/')
def post(id):
    with db.cursor() as cur:
        cur.execute('''
            SELECT post.id, post.name, "user".name AS user_name, post.ts, text, user_id
            FROM post JOIN "user" ON post.user_id = "user".id
            WHERE post.id=%s
        ''', [id])

        post = cur.fetchone()

    return render_template('post.html', post=post)

@app.route('/post/<id>/edit/', methods=['GET', 'POST'])
@app.route('/board/<board_id>/new/', methods=['GET', 'POST'])
def post_edit(id=None, board_id=None):
    if request.method == 'POST':
        post_form = {
            'id': id,
            'board_id': board_id,
            'name': request.form['name'],
            'text': request.form['text'],
        }

        if not user:
            flash('Not logged in')

        elif not post_form['name'] or not post_form['text']:
            flash('Insufficient input')

        else:
            with db.cursor() as cur:
                if id:
                    cur.execute('''
                        SELECT user_id, board_id, ts
                        FROM post
                        WHERE id=%s
                    ''', [id])

                    post = cur.fetchone()

                    if post['user_id'] != user['id']:
                        flash('Insufficient permission')

                    else:
                        post_form['ts'] = post['ts']

                        if not post_form['board_id']:
                            post_form['board_id'] = post['board_id']

                        elif post_form['board_id'] != post['board_id']:
                            post_form['ts'] = datetime.now()

                        cur.execute('''
                            UPDATE post
                            SET name=%s, text=%s, board_id=%s, ts=%s
                            WHERE id=%s
                        ''', [post_form['name'], post_form['text'], post_form['board_id'], post_form['ts'], id])

                        db.commit()
                else:
                    cur.execute('''
                        INSERT INTO post
                        (name, text, ts, user_id, board_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    ''', [post_form['name'], post_form['text'], datetime.now(), user['id'], post_form['board_id']])

                    id = cur.fetchone()['id']

                    db.commit()

            return redirect(url_for('post', id=id))

    else:
        if not id:
            post_form = {
                'id': 0,
                'name': '',
                'text': '',
            }
        else:
            with db.cursor() as cur:
                cur.execute('''
                    SELECT id, name, text
                    FROM post
                    WHERE id=%s
                ''', [id])

                post_form = cur.fetchone()

                if not post_form:
                    flash('Post not exists')
                    return redirect(url_for('index'))

    return render_template('post_edit.html', post=post_form)
