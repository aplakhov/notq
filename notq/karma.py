from collections import defaultdict
from cachetools import cached, TTLCache
from notq.db import db_execute
from notq.data_model import get_starting_date
@cached(cache=TTLCache(maxsize=64, ttl=60))
def get_user_karma(username):
    posts = db_execute(
        'SELECT SUM(v.karma_vote) AS votes'
        ' FROM post p JOIN notquser u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' WHERE username=:u AND p.author_id != v.user_id', u=username
    ).fetchone()
    comments = db_execute(
        'SELECT SUM(v.karma_vote) AS votes'
        ' FROM comment c JOIN notquser u ON c.author_id = u.id'
        ' JOIN commentvote v ON v.comment_id = c.id'
        ' WHERE username=:u AND c.author_id != v.user_id', u=username
    ).fetchone()
    pv = posts.votes or 0
    cv = comments.votes or 0
    return int(pv + cv // 3)

def get_best_users(period):
    start = get_starting_date(period)
    userkarma = defaultdict(float)
    is_golden = defaultdict(bool)
    posts = db_execute(
        'SELECT SUM(v.karma_vote) AS votes, u.id, username, is_golden'
        ' FROM post p JOIN notquser u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' WHERE p.created > :since AND p.author_id != v.user_id'
        ' GROUP BY u.id', since=start
    ).fetchall()
    for p in posts:
        if p.id != 1: #not anomymous
            userkarma[p.username] += p.votes
        if p.is_golden:
            is_golden[p.username] = True
    comments = db_execute(
        'SELECT SUM(v.karma_vote) AS votes, u.id, username, is_golden'
        ' FROM comment c JOIN notquser u ON c.author_id = u.id'
        ' JOIN commentvote v ON v.comment_id = c.id'
        ' WHERE c.created > :since AND c.author_id != v.user_id'
        ' GROUP BY u.id', since=start
    ).fetchall()
    for c in comments:
        if c.id != 1: #not anomymous
            userkarma[c.username] += c.votes / 3
        if c.is_golden:
            is_golden[c.username] = True
    for u in userkarma:
        userkarma[u] = int(userkarma[u])
    users = [
        {
            'username': k,
            'karma': v,
            'is_golden': is_golden[k]
        }
        for k, v in userkarma.items() if v >= 0
    ]
    users.sort(key = lambda u: u['karma'], reverse=True)
    for n in range(len(users)):
        users[n]['rank'] = n + 1
        if users[n]['karma'] == 0:
            users[n]['karma'] = "ɛ"
    return users
