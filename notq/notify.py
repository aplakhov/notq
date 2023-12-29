from sqlalchemy import select, text
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
    return f'<a class="username" href="/u/{user.username}"><img src="/static/{icon}">{user.username}</a>'

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
        notify = f'{describe(user)} ответил на ваш комментарий к записи "{post.title}"'
    else:
        notify_user = post.author_id
        notify = f'На вашу запись "{post.title}" ответил {describe(user)}'
    if notify_user != answer_author_id:
        query = 'INSERT INTO notifies (user_id, post_id, text) VALUES(:u, :p, :t)'
        db.execute(text(query), {'u': notify_user, 'p': post_id, 't': notify})
        db.commit()
