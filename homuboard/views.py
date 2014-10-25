from . import app
from flask import render_template, request, flash, redirect, url_for, session
from .db import db
from .mysql import mysql323
from .user import user
from datetime import datetime
from jinja2 import Markup

board_list = None
def load_board_list():
    global board_list

    if not board_list:
        with db.cursor() as cur:
            cur.execute('''
                SELECT id, name
                FROM board
            ''')

            board_list = Markup('\n'.join(
                '<a href="{}">{}</a><br>'.format(
                    url_for('board', id=board['id']),
                    board['name'],
                ) for board in cur))

    return board_list

@app.context_processor
def inject_env():
    return {
        'site_name': app.config['SITE_NAME'],
        'board_list': load_board_list(),
    }

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
            SELECT id, name
            FROM board
            WHERE id = %s
        ''', [id])

        board = cur.fetchone()

        if not board:
            flash('Board not exists')
            return redirect(url_for('index'))

        cur.execute('''
            SELECT post.id, post.name, "user".name AS user_name, post.ts, views, votes
            FROM post JOIN "user" ON post.user_id = "user".id
            WHERE board_id=%s
            ORDER BY post.ts DESC LIMIT 20
        ''', [id])

        posts = cur.fetchall()

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

        cur.execute('''
            SELECT comm.id, "user".name AS user_name, comm.text, comm.ts, user_id, level
            FROM comm JOIN "user" ON comm.user_id = "user".id
            WHERE post_id = %s
            ORDER BY sort_key
        ''', [id])

        comms = []
        level = 0
        for row in cur:
            comm = dict(row)

            gap = comm['level'] - level
            if gap:
                level = comm['level']

                indents = []

                if gap > 0:
                    indents.append('<div class="comm_indent">' * gap)
                else:
                    indents.append('</div>' * -gap)

                comm['html'] = ''.join(indents)

            comms.append(comm)

        comms_html = '</div>' * level

    return render_template('post.html', post=post, comms=comms, comms_html=comms_html)

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
        if id:
            with db.cursor() as cur:
                cur.execute('''
                    SELECT name, text
                    FROM post
                    WHERE id=%s
                ''', [id])

                post_form = cur.fetchone()

                if not post_form:
                    flash('Post not exists')
                    return redirect(url_for('index'))
        else:
            post_form = {
                'name': '',
                'text': '',
            }

    return render_template('post_edit.html', post=post_form)

def get_comm_sort_code(num):
    return chr(num)

@app.route('/comm/<id>/edit/', methods=['GET', 'POST'])
@app.route('/post/<post_id>/new/', methods=['GET', 'POST'])
def comm_edit(id=None, post_id=None):
    if request.method == 'POST':
        comm_form = {
            'id': id,
            'text': request.form['text'],
        }

        if not user:
            flash('Not logged in')

        elif not comm_form['text']:
            flash('Insufficient input')

        else:
            with db.cursor() as cur:
                if id:
                    cur.execute('''
                        SELECT user_id, post_id
                        FROM comm
                        WHERE id = %s
                    ''', [id])

                    comm = cur.fetchone()

                    post_id = comm['post_id']

                    if comm['user_id'] != user['id']:
                        flash('Insufficient permission')

                    else:
                        cur.execute('''
                            UPDATE comm
                            SET text = %s
                            WHERE id = %s
                        ''', [comm_form['text'], id])

                        db.commit()

                        return redirect(url_for('post', id=post_id))

                else:
                    level = None

                    parent_id = request.args.get('parent_id')
                    if parent_id:
                        cur.execute('''
                            SELECT level, sort_key, child_cnt
                            FROM comm
                            WHERE id = %s
                        ''', [parent_id])

                        parent_comm = cur.fetchone()
                        if not parent_comm:
                            flash('Parent comment not found')
                        else:
                            cur.execute('''
                                UPDATE comm
                                SET child_cnt = child_cnt + 1
                                WHERE id = %s
                            ''', [parent_id])

                            level = parent_comm['level'] + 1
                            sort_key = parent_comm['sort_key'] + '.' + get_comm_sort_code(parent_comm['child_cnt'] + 1)
                    else:
                        cur.execute('''
                            SELECT child_cnt
                            FROM post
                            WHERE id = %s
                        ''', [post_id])

                        post = cur.fetchone()
                        if not post:
                            flash('Post not found')
                        else:
                            cur.execute('''
                                UPDATE post
                                SET child_cnt = child_cnt + 1
                                WHERE id = %s
                            ''', [post_id])

                            level = 0
                            sort_key = get_comm_sort_code(post['child_cnt'] + 1)

                    if level is not None:
                        cur.execute('''
                            INSERT INTO comm
                            (text, user_id, ts, post_id, level, sort_key)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', [comm_form['text'], user['id'], datetime.now(), post_id, level, sort_key])

                        db.commit()

                        return redirect(url_for('post', id=post_id))

    else:
        if id:
            with db.cursor() as cur:
                cur.execute('''
                    SELECT text
                    FROM comm
                    WHERE id = %s
                ''', [id])

                comm_form = cur.fetchone()

        else:
            comm_form = {
                'text': '',
            }

    return render_template('comm_edit.html', comm=comm_form)
