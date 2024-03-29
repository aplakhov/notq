import functools
import re

from notq.db_structure import *
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from notq.karma import get_user_karma
from cachetools import cached, TTLCache

from hashlib import sha256

from flask import (
    Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from notq.db import get_db
from notq.notify import has_unread_notifies

bp = Blueprint('auth', __name__, url_prefix='/auth')

def do_login(username, password):
    if username == "anonymous":
        error = True
    else:
        db = get_db()
        query = select(user_table.c.id, user_table.c.password).where(user_table.c.username == username)
        user = db.execute(query).fetchone()
        error = (user is None) or (not check_password_hash(user[1], password))

    if not error:
        session.clear()
        session['user_id'] = user[0]
        return redirect(url_for('index'))

    flash('Неверное имя пользователя или пароль. Возможно, вы имели в виду "correct horse battery staple"?')
    return redirect(url_for('auth.login'))

usernamere = re.compile("^[A-Za-z0-9-]+$")
def check_username(username):
    return usernamere.match(username)

def is_disallowed_username(username):
    if username in ['admin', 'anonymous', 'u', 'yandex', 'mail', 'vk', 'sber', 'dzen']:
        return True
    if 'moderator' in username:
        return True
    if username.startswith('robot-'):
        return True
    return False

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Нужно указать имя пользователя.'
        elif not check_username(username):
            error = 'Имя пользователя может состоять только из латиницы, цифр и символа "-".'
            ' Это нужно для того, чтобы адреса страниц пользователей были короткими и запоминающимися.'
        elif is_disallowed_username(username):
            error = 'Такое имя нельзя зарегистрировать обычному пользователю.'
        elif len(username) < 3:
            error = "Слишком короткое имя пользователя. Имя не может состоять менее чем из трёх символов."
        elif len(username) > 40:
            error = "Слишком длинное имя пользователя."
        elif not password:
            error = 'Нужно указать пароль.'

        if error is None:
            try:
                db.execute(insert(user_table).values(username=username, password=generate_password_hash(password)))
                db.commit()
            except IntegrityError:
                error = f"Пользователь {username} уже зарегистрирован."
            else:
                return do_login(username, password)

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        return do_login(username, password)
    return render_template('auth/login.html')

def make_token(secret, username):
    token_source = secret + username
    return sha256(token_source.encode()).hexdigest()

@cached(cache=TTLCache(maxsize=64, ttl=5))
def do_load_user(user_id):
    query = select(user_table).where(user_table.c.id == user_id)
    return get_db().execute(query).fetchone()

@bp.before_app_request
def load_logged_in_user():
    g.user = None
    g.karma = None
    g.canVote = 0
    g.token = None
    
    user_id = session.get('user_id')
    if user_id is not None:
        g.user = do_load_user(user_id)
        if g.user:
            g.karma = get_user_karma(g.user.username)
            g.active_notifies = has_unread_notifies(g.user.id)
            g.canVote = 1
            g.token = make_token(current_app.config['SECRET_KEY'], g.user.username)
            session.permanent = True

@bp.route('/logout/<token>')
def logout(token):
    if token != g.token:
        abort(403)
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
