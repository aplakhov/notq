from datetime import datetime, timedelta
from flask import g, render_template
from notq.db import get_db
from notq.db_structure import *

# hardcoding some texts and constants for now, because it is still unclear 
# what this feature will look like in a stable state 
# and will it even exist in several weeks

def insert_motivating_post(posts):
    p = get_motivating_post()
    if not p:
        return posts
    return posts[:2] + [p] + posts[2:]

def get_motivating_post():
    if not g.user:
        return None
    post_time = last_time_created_a_post(g.user.id)
    if not post_time:
        motivating_message = 'Вы зарегистрировались, но пока не опубликовали ни одной записи. Давайте начнём, ведь если все будут только читать, то читать скоро станет и нечего!'
    elif post_time < datetime.now() - timedelta(days=30):
        motivating_message = 'Вы давно ничего не публиковали. Давайте продолжим!'
    else:
        return None
    html = render_template('blog/motivator.html', motivating_message=motivating_message)
    return {
        'custom_html': html,
        'created_ts': datetime.now()
    }

def last_time_created_a_post(user_id):
    query = select(post_table.c.created).where(post_table.c.author_id == user_id).order_by(post_table.c.created.desc()).limit(1)
    res = get_db().execute(query).fetchone()
    if not res:
        return None
    return res[0]

def make_post_starting_text(post_type):
    starting_texts = [
        "",
        "Сейчас я работаю в ",
        "Сегодня я узнал, что ",
        "А вот такая задача: ",
        "Мне очень нравится ",
        "Я всегда мечтал сделать ",
        "https://www.youtube.com/watch?v=\n\nПосмотрите этот ролик, "
    ]
    if post_type >= 0 and post_type < len(starting_texts):
        return starting_texts[post_type]
    return ""
