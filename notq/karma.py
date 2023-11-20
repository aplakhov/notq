from collections import defaultdict
from notq.cache import cache
from notq.db import get_db
from notq.data_model import get_starting_date

@cache.memoize(timeout=30)
def get_user_karma(username):
    db = get_db()
    posts = db.execute(
        'SELECT SUM(v.vote) AS votes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' WHERE username == ?', (username,)
    ).fetchone()
    comments = db.execute(
        'SELECT SUM(v.vote) AS votes'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' JOIN commentvote v ON v.comment_id = c.id'
        ' WHERE username == ?', (username,)
    ).fetchone()
    pv = posts['votes'] or 0
    cv = comments['votes'] or 0
    return pv + cv // 3

@cache.memoize(timeout=60)
def get_best_users(period):
    start = get_starting_date(period)
    db = get_db()
    userkarma = defaultdict(float)
    posts = db.execute(
        'SELECT SUM(v.vote) AS votes, u.id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' WHERE p.created > ?'
        ' GROUP BY u.id', (start,)
    ).fetchall()
    for p in posts:
        userkarma[p['username']] += p['votes']
    comments = db.execute(
        'SELECT SUM(v.vote) AS votes, u.id, username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' JOIN commentvote v ON v.comment_id = c.id'
        ' WHERE c.created > ?'
        ' GROUP BY u.id', (start,)
    ).fetchall()
    for c in comments:
        userkarma[c['username']] += c['votes'] / 3
    for u in userkarma:
        userkarma[u] = int(userkarma[u])
    return sorted(userkarma.items(), key = lambda kv: kv[1], reverse=True)
