from sqlalchemy import select, text
from notq.cache import cache
from notq.data_model import readable_timediff
from notq.db import db_execute, db_execute_commit, get_db
from notq.db_structure import *
from notq.markup import sanitizeHtml

def get_user(db, user_id):
    query = select(user_table.c.username, user_table.c.is_golden).where(user_table.c.id == user_id)
    return db.execute(query).fetchone()

def get_notify_post(db, post_id):
    query = select(post_table.c.title, post_table.c.author_id).where(post_table.c.id == post_id)
    return db.execute(query).fetchone()

def get_notify_comment(db, post_id, comment_id):
    query = select(comment_table.c.author_id).where(comment_table.c.post_id == post_id, comment_table.c.id == comment_id)
    return db.execute(query).fetchone()

def describe(user):
    if user.is_golden:
        icon = 'gold.png'
    else:
        icon = 'silver.png'
    return f'<img src="/static/{icon}">{user.username}'

def create_answer_notify(post_id, parent_id, answer_author_id):
    db = get_db()
    user = get_user(db, answer_author_id)
    if not user:
        return
    post = get_notify_post(db, post_id)
    if not post:
        return
    title = sanitizeHtml(post.title)
    if parent_id:
        comment = get_notify_comment(db, post_id, parent_id)
        if not comment:
            return
        notify_user = comment.author_id
        notify_message = f'{describe(user)} ответил на ваш комментарий к записи «{title}»'
        link = f'/{post_id}#answer{parent_id}'
    else:
        notify_user = post.author_id
        notify_message = f'{describe(user)} ответил на вашу запись «{title}»'
        link = f'/{post_id}#answersection'
    if notify_user != answer_author_id:
        notify_html = f'<a class="notify" href="{link}">{notify_message}</a>'
        query = 'INSERT INTO notifies (user_id, post_id, text) VALUES(:u, :p, :t)'
        db.execute(text(query), {'u': notify_user, 'p': post_id, 't': notify_html})
        db.commit()

def get_notifies(user):
    res = db_execute(
        'SELECT text, created, is_read FROM notifies WHERE user_id=:u ORDER BY created DESC LIMIT 100',
        u=user.id
    ).fetchall()
    if not res:
        return [
            {
                'active': False, 
                'text': '<a class="notify" href="/best/week">Добро пожаловать! Здесь будут оповещения об ответах на ваши записи и комментарии. Пока их нет, можете почитать лучшие записи недели</a>',
                'created': ''
            }
        ]
    return [
        { 
            'active': not n.is_read,
            'text': n.text,
            'created': readable_timediff(n.created)
        } for n in res
    ]

def mark_as_read(user_id, post_id):
    query = 'UPDATE notifies SET is_read=:t WHERE user_id=:u AND post_id=:p'
    db_execute_commit(query, t=True, u=user_id, p=post_id)

def has_unread_notifies(user_id):
    res = db_execute(
        'SELECT 1 FROM notifies WHERE user_id=:u AND (is_read IS NULL OR NOT is_read)',
        u=user_id
    ).fetchone()
    return res != None
 