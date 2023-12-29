from sqlalchemy import select, text
from notq.data_model import readable_timediff
from notq.db import get_db
from notq.db_structure import *

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
    if parent_id:
        comment = get_notify_comment(db, post_id, parent_id)
        if not comment:
            return
        notify_user = comment.author_id
        notify_message = f'{describe(user)} ответил на ваш комментарий к записи «{post.title}»'
        link = f'/{post_id}#answer{parent_id}'
    else:
        notify_user = post.author_id
        notify_message = f'{describe(user)} ответил на вашу запись «{post.title}»'
        link = f'/{post_id}#answersection'
    if notify_user != answer_author_id:
        notify_html = f'<a class="notify" href="{link}">{notify_message}</a>'
        query = 'INSERT INTO notifies (user_id, post_id, text) VALUES(:u, :p, :t)'
        db.execute(text(query), {'u': notify_user, 'p': post_id, 't': notify_html})
        db.commit()

def get_notifies(user):
    query = select(notifies_table.c.text, notifies_table.c.created, notifies_table.c.is_read)
    query = query.where(notifies_table.c.user_id == user.id)
    query = query.order_by(notifies_table.c.created.desc()).limit(100)
    res = get_db().execute(query).fetchall()
    if not res:
        return [
            {
                'active': False, 
                'text': '<a class="notify" href="/best/week">Добро пожаловать! Можете начать знакомство с сервисом с лучших постов недели</a>',
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
