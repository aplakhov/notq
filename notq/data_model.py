from heapq import nlargest
from datetime import datetime
from notq.cache import cache
from notq.db import get_db

@cache.memoize(timeout=9)
def get_user_votes_for_posts(user_id):
    db = get_db()
    votes = db.execute(
        'SELECT vote, post_id FROM vote WHERE user_id = ?', (user_id,)
    ).fetchall()
    upvoted = [v['post_id'] for v in votes if v['vote'] > 0]
    downvoted = [v['post_id'] for v in votes if v['vote'] < 0]
    return upvoted, downvoted

@cache.cached(timeout=12)
def get_posts_comments_number():
    db = get_db()
    ncomments = db.execute(
        'SELECT post_id, COUNT(*) AS ncomments FROM post p JOIN comment c ON c.post_id == p.id GROUP BY p.id'
    ).fetchall()
    res = { p['post_id'] : p['ncomments'] for p in ncomments }
    return res

def make_comments_string(n):
    if n == 0:
        return "ответить"
    flexn = n % 100
    if flexn >= 5 and flexn <= 20:
        return str(n) + " ответов"
    flexn = n % 10
    if flexn == 1:
        return str(n) + " ответ"
    if flexn < 5:
        return str(n) + " ответа"
    return str(n) + " ответов"

def post_from_sql_row(p, ncomments, add_comments):
    nc = 0
    if ncomments and p['id'] in ncomments:
        nc = ncomments[p['id']]
    res = {
        'id': p['id'],
        'title': p['title'],
        'rendered': p['rendered'],
        'created': p['created'],
        'author_id': p['author_id'],
        'username': p['username'],
        'votes': p['votes'],
        'ncomments': make_comments_string(nc)
    }
    if add_comments:
        res['comments'] = get_post_comments(p['id'])
    return res

def post_scoring(post, now):
    halflife = 18 * 3600
    timediff = (now - post['created']).total_seconds()
    decay = halflife / (halflife + timediff)
    print(f"score for post {post['id']} is {decay} * {post['votes']+4}, timediff is {timediff}")
    return (post['votes'] + 4) * decay

@cache.cached(timeout=10)
def get_top_posts():
    db = get_db()
    all_posts = db.execute(
        'SELECT p.id, title, rendered, p.created, author_id, username, SUM(v.vote) AS votes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' GROUP BY p.id'
        ' ORDER BY p.created DESC'
    ).fetchall()
    now = datetime.now()
    ncomments = get_posts_comments_number()
    top_posts = [
        post_from_sql_row(p, ncomments, False) for p in nlargest(100, all_posts, key=lambda post: post_scoring(post, now))
    ]
    return top_posts

def readable_timediff(created):
    diff = (datetime.now() - created).total_seconds()
    if diff < 60:
        return "только что"
    elif diff < 3600:
        return str(int(diff//60)) + " мин назад"
    elif diff < 24 * 3600:
        return str(int(diff//3600)) + " ч назад"
    else:
        return created.strftime('%d-%m-%Y')

def comment_from_data(c, commentvotes):
    res = {
        'id': c['id'],
        'author_id': c['author_id'],
        'created': readable_timediff(c['created']),
        'rendered': c['rendered'],
        'parent_id': c['parent_id'],
        'username': c['username']
    }
    if c['id'] in commentvotes:
        res['votes'] = commentvotes[c['id']]
    else:
        res['votes'] = 0
    return res

@cache.memoize(timeout=9)
def get_user_votes_for_posts(user_id):
    db = get_db()
    votes = db.execute(
        'SELECT vote, post_id FROM vote WHERE user_id = ?', (user_id,)
    ).fetchall()
    upvoted = [v['post_id'] for v in votes if v['vote'] > 0]
    downvoted = [v['post_id'] for v in votes if v['vote'] < 0]
    return upvoted, downvoted

def sort_comments_tree(comments):
    comments.sort(key=lambda c: c['votes'], reverse=True)
    for c in comments:
        if c['votes'] < -4:
            c['closed'] = True
        if 'children' in c:
            sort_comments_tree(c['children'])

@cache.memoize(timeout=10)
def get_post_comments(post_id):
    # collect comments
    db = get_db()
    comments = db.execute(
        'SELECT c.id, author_id, c.created, rendered, parent_id, username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE post_id = ? ORDER BY c.id', (post_id,)
    ).fetchall()

    # collect comment votes
    commentvotes = get_post_comments_likes(post_id)

    # collect all top-level comments
    res = [ comment_from_data(c, commentvotes) for c in comments if not c['parent_id'] ]
    index = { c['id']: c for c in res }

    # insert all others into a tree
    for c in comments:
        if c['parent_id'] and c['parent_id'] in index:
            parent = index[c['parent_id']]
            if not 'children' in parent:
                parent['children'] = []
            parent['children'].append(comment_from_data(c, commentvotes))
            index[c['id']] = parent['children'][-1]

    sort_comments_tree(res)
    return res

def get_post_comments_likes(post_id):
    db = get_db()
    votes = db.execute(
        'SELECT comment_id, SUM(vote) AS votes FROM commentvote '
        'WHERE post_id = ? GROUP BY comment_id', (post_id,)
    ).fetchall()
    res = { v['comment_id'] : v['votes'] for v in votes }
    return res

def add_comment(text, rendered, author_id, post_id, parent_id):
    db = get_db()
    db.execute(
        'INSERT INTO comment (body, rendered, author_id, post_id, parent_id)'
        ' VALUES (?, ?, ?, ?, ?)',
        (text, rendered, author_id, post_id, parent_id)
    )
    db.commit()

@cache.memoize(timeout=10)
def get_posts_by_id(id):
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, rendered, p.created, author_id, username, SUM(v.vote) AS votes'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' JOIN vote v ON v.post_id = p.id'
        ' WHERE p.id = ?'
        ' GROUP BY p.id', (id,)
    ).fetchall()
    return [post_from_sql_row(p, None, True) for p in posts]

@cache.memoize(timeout=10)
def get_user_votes_for_comments(user_id, post_id):
    db = get_db()
    votes = db.execute(
        'SELECT comment_id, vote FROM commentvote '
        'WHERE post_id = ? AND user_id = ?', (post_id, user_id)
    ).fetchall()
    upvoted = [v['comment_id'] for v in votes if v['vote'] > 0]
    downvoted = [v['comment_id'] for v in votes if v['vote'] < 0]
    return upvoted, downvoted
