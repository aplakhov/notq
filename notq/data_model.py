from collections import namedtuple
from heapq import nlargest
from datetime import datetime, timedelta
from flask import g
from sqlalchemy import select
from notq.cache import cache
from notq.db import get_db, db_execute, db_execute_commit
from notq.markdown_tags import collect_tags
from notq.markup import make_html
from notq.constants import POST_COMMENTS_PAGE_SIZE

from notq.db_structure import *

@cache.memoize(timeout=9)
def get_user_votes_for_posts(user_id):
    votes = db_execute('SELECT vote, post_id FROM vote WHERE user_id = :id', id=user_id).fetchall()
    upvoted = [v.post_id for v in votes if v.vote > 0]
    downvoted = [v.post_id for v in votes if v.vote < 0]
    return upvoted, downvoted

@cache.cached(timeout=12)
def get_posts_comments_number():
    ncomments = db_execute(
        'SELECT post_id, COUNT(*) AS ncomments FROM post p JOIN comment c ON c.post_id == p.id GROUP BY p.id'
    ).fetchall()
    res = { nc.post_id : nc.ncomments for nc in ncomments }
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

def post_from_sql_row(p, ncomments, full_post):
    nc = 0
    if ncomments and p.id in ncomments:
        nc = ncomments[p.id]
    res = {
        'id': p.id,
        'title': p.title,
        'rendered': p.rendered,
        'created_ts': p.created,
        'created': readable_timediff(p.created),
        'author_id': p.author_id,
        'username': p.username,
        'is_golden': p.is_golden,
        'votes': p.votes,
        'ncomments': make_comments_string(nc),
        'edited_by_moderator': p.edited_by_moderator
    }
    if not full_post:
        cut_rendered = p.cut_rendered
        if cut_rendered and cut_rendered != res['rendered']:
            id = res['id']
            res['rendered'] = cut_rendered + f'<p><a href="/{id}">Читать дальше →</a></p>'
    if p.edited:
        timediff = p.edited - p.created
        if timediff > timedelta(minutes=5):
            res['edited'] = readable_timediff(p.edited)
            if res['edited'] == res['created']:
                res['edited'] = ''
    if p.anon:
        res['author_id'] = 1
        res['username'] = 'anonymous'
        res['is_golden'] = False
    if full_post:
        res['comments'] = get_post_comments(p.id)
    return res

def top_post_scoring(post, now):
    halflife = 18 * 3600
    timediff = (now - post.created).total_seconds()
    decay = halflife / (halflife + timediff)
    return (post.weighted_votes + 4) * decay

def best_post_scoring(post):
    return post.weighted_votes

def select_posts_with_votes():
    query = select(
        post_table.c.id,
        post_table.c.title,
        post_table.c.rendered,
        post_table.c.cut_rendered,
        post_table.c.created,
        post_table.c.anon,
        post_table.c.edited,
        post_table.c.edited_by_moderator,
        post_table.c.author_id,
        user_table.c.username,
        user_table.c.is_golden,
        func.sum(vote_table.c.vote).label('votes'),
        func.sum(vote_table.c.weighted_vote).label('weighted_votes'),
    )
    query = query.join(user_table, user_table.c.id==post_table.c.author_id)
    query = query.join(vote_table, vote_table.c.post_id==post_table.c.id)
    query = query.group_by(post_table.c.id)
    return query

@cache.cached(timeout=10)
def get_top_posts():
    all_posts = get_db().execute(select_posts_with_votes().order_by(post_table.c.id.desc())).fetchall()
    now = datetime.now()
    ncomments = get_posts_comments_number()
    top_posts = [
        post_from_sql_row(p, ncomments, False) for p in nlargest(500, all_posts, key=lambda post: top_post_scoring(post, now))
    ]
    return top_posts

@cache.cached(timeout=10)
def get_new_posts():
    query = select_posts_with_votes().order_by(post_table.c.created.desc()).limit(500)
    new_posts = get_db().execute(query).fetchall()
    ncomments = get_posts_comments_number()
    return [ post_from_sql_row(p, ncomments, False) for p in new_posts ]

def get_starting_date(period):
    now = datetime.now()
    if period == "day":
        start = now - timedelta(days=1)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "year":
        start = now - timedelta(days=365)
    else:
        start = now - timedelta(days=100*365)
    return start

@cache.memoize(timeout=30)
def get_best_posts(period):
    start = get_starting_date(period)
    query = select_posts_with_votes().where(post_table.c.created > start)
    period_posts = get_db().execute(query).fetchall()
    ncomments = get_posts_comments_number()
    return [
        post_from_sql_row(p, ncomments, False) 
        for p in nlargest(100, period_posts, key=lambda post: best_post_scoring(post))
        if p.weighted_votes >= 0
    ]

@cache.cached(timeout=60)
def get_user_posts(username):
    query = select_posts_with_votes().where(user_table.c.username==username, ~post_table.c.anon)
    query = query.order_by(post_table.c.created.desc()).limit(500)
    print(query)
    user_posts = get_db().execute(query).fetchall()
    ncomments = get_posts_comments_number()
    return [post_from_sql_row(p, ncomments, False) for p in user_posts]

@cache.cached(timeout=60)
def get_tag_posts(tagname):
    tagdata = db_execute('SELECT * FROM tag WHERE tagname = :tagname', tagname=tagname).fetchone()
    if tagdata is None:
        return []
    query = select_posts_with_votes().join(posttag_table, posttag_table.c.post_id==post_table.c.id)
    query = query.where(posttag_table.c.tag_id == tagdata.id)
    tag_posts = get_db().execute(query).fetchall()
    ncomments = get_posts_comments_number()
    now = datetime.now()
    top_posts = [
        post_from_sql_row(p, ncomments, False) 
        for p in nlargest(100, tag_posts, key=lambda post: top_post_scoring(post, now))
    ]
    return top_posts

def get_anon_posts():
    query = select_posts_with_votes().where(post_table.c.anon).order_by(post_table.c.created).limit(500)
    anon_posts = get_db().execute(query).fetchall()
    ncomments = get_posts_comments_number()
    return [post_from_sql_row(p, ncomments, False) for p in anon_posts]

def get_user_stats(username):
    user_posts = db_execute(
        'SELECT COUNT(*) AS n FROM post p JOIN notquser u ON p.author_id = u.id'
        ' WHERE username=:u', u=username).fetchone()
    user_comments = db_execute(
        'SELECT COUNT(*) AS n FROM comment c JOIN notquser u ON c.author_id = u.id'
        ' WHERE username=:u', u=username).fetchone()
    userdata = get_db().execute(select(user_table).where(user_table.c.username == username)).fetchone()
    if userdata is None:
        return None, 0, 0, None, False
    if userdata.banned_until and userdata.banned_until > datetime.now():
        banned = userdata.banned_until.strftime('%d-%m-%Y')
    else:
        banned = None
    return userdata.created.strftime('%d-%m-%Y'), user_posts.n, user_comments.n, banned, userdata.is_golden

def get_about_post(username):
    if g.user and username == g.user.username:
        about_post_id = g.user.about_post_id
    elif username:
        userdata = db_execute(
            'SELECT about_post_id FROM notquser WHERE username = :u', u=username
        ).fetchone()
        if userdata:
            about_post_id = userdata.about_post_id
    if about_post_id:
        return db_execute(
            'SELECT * FROM post WHERE id = :p', p=about_post_id
        ).fetchone()
    else:
        default_about = 'Этот пользователь пока ничего о себе не написал'
        about_post = namedtuple('post', ('body, rendered'))
        return about_post(body=default_about, rendered=default_about)

def comment_from_data(c):
    res = {
        'id': c.id,
        'author_id': c.author_id,
        'created': readable_timediff(c.created),
        'rendered': c.rendered,
        'parent_id': c.parent_id,
        'username': c.username,
        'is_golden': c.is_golden,
        'votes': c.votes,
        'weighted': c.weighted_votes,
        'post_id': c.post_id,
        'title': c.title
    }
    if c.anon:
        res['author_id'] = 1
        res['username'] = 'anonymous'
        res['is_golden'] = False
    if c.edited:
        timediff = c.edited - c.created
        if timediff > timedelta(minutes=2):
            res['edited'] = readable_timediff(c.edited)
            if res['edited'] == res['created']:
                res['edited'] = ''
    return res

def select_comments_with_votes():
    query = select(
        comment_table.c.id,
        comment_table.c.author_id,
        comment_table.c.post_id,
        comment_table.c.created,
        comment_table.c.rendered,
        comment_table.c.parent_id,
        comment_table.c.anon,
        comment_table.c.edited,
        comment_table.c.edited_by_moderator,
        user_table.c.username,
        user_table.c.is_golden,
        func.sum(commentvote_table.c.vote).label('votes'),
        func.sum(commentvote_table.c.weighted_vote).label('weighted_votes'),
        post_table.c.title
    )
    query = query.join(user_table, user_table.c.id==comment_table.c.author_id)
    query = query.join(post_table, post_table.c.id==comment_table.c.post_id)
    query = query.join(commentvote_table, commentvote_table.c.comment_id==comment_table.c.id)
    query = query.group_by(comment_table.c.id)
    return query

@cache.memoize(timeout=60)
def get_best_comments(period):
    start = get_starting_date(period)
    query = select_comments_with_votes().where(comment_table.c.created > start)
    comments_data = get_db().execute(query).fetchall()
    return [
        comment_from_data(c) 
        for c in nlargest(250, comments_data, key=lambda c: c.weighted_votes)
        if c.weighted_votes >= 0
    ]

def get_last_user_comments(username):
    query = select_comments_with_votes().where(user_table.c.username == username, ~comment_table.c.anon)
    query = query.order_by(comment_table.c.created.desc()).limit(20)
    comments_data = get_db().execute(query).fetchall()
    return [comment_from_data(c) for c in comments_data]

@cache.memoize(timeout=9)
def get_user_votes_for_posts(user_id):
    votes = db_execute('SELECT vote, post_id FROM vote WHERE user_id = :id', id=user_id).fetchall()
    upvoted = [v.post_id for v in votes if v.vote > 0]
    downvoted = [v.post_id for v in votes if v.vote < 0]
    return upvoted, downvoted

def sort_comments_tree(comments):
    comments.sort(key=lambda c: c['weighted'], reverse=True)
    for c in comments:
        if c['votes'] < -4:
            c['closed'] = True
        if 'children' in c:
            sort_comments_tree(c['children'])

def subtree_num_comments(subtree):
    res = 1
    if 'children' in subtree:
        for child in subtree['children']:
            res += subtree_num_comments(child)
    return res

def set_subtree_page_num(subtree, page):
    subtree['page'] = page
    if 'children' in subtree:
        for child in subtree['children']:
            set_subtree_page_num(child, page)

def add_page_numbers(comments):
    current_page = 0
    current_page_num_comments = 0
    for c in comments:
        set_subtree_page_num(c, current_page)
        current_page_num_comments += subtree_num_comments(c)
        if current_page_num_comments >= POST_COMMENTS_PAGE_SIZE:
            current_page += 1
            current_page_num_comments = 0

@cache.memoize(timeout=10)
def get_post_comments(post_id):
    # select comments with votes from database
    query = select_comments_with_votes().where(comment_table.c.post_id == post_id)
    comments = get_db().execute(query).fetchall()

    # collect all top-level comments
    res = [ comment_from_data(c) for c in comments if not c.parent_id ]
    index = { c['id']: c for c in res }

    # insert all others into a tree
    for c in comments:
        if c.parent_id and c.parent_id in index:
            parent = index[c.parent_id]
            if not 'children' in parent:
                parent['children'] = []
            parent['children'].append(comment_from_data(c))
            index[c.id] = parent['children'][-1]

    sort_comments_tree(res)
    add_page_numbers(res)
    return res

def get_post_comments_likes(post_id):
    votes = db_execute(
        'SELECT comment_id, SUM(vote) AS votes, SUM(weighted_vote) AS weighted FROM commentvote '
        'WHERE post_id = :p GROUP BY comment_id', p=post_id
    ).fetchall()
    res = { v.comment_id : { 'votes': v.votes, 'weighted': v.weighted } for v in votes }
    return res

def add_comment(text, rendered, author_id, post_id, parent_id, anon, linked_post_id):
    db_execute_commit(
        'INSERT INTO comment (body, rendered, author_id, post_id, parent_id, anon, linked_post_id)'
        ' VALUES (:t, :r, :author, :p, :c, :anon, :linked)',
        t=text, r=rendered, author=author_id, p=post_id, c=parent_id, anon=anon, linked=linked_post_id
    )

def vote_values(voteparam, is_golden_user):
    vote = voteparam - 1
    if is_golden_user:
        weighted_vote = 42 * vote
        karma_vote = 7 * vote
    else:
        weighted_vote = karma_vote = vote
    if karma_vote < 0:
        karma_vote = karma_vote / 2
    return vote, weighted_vote, karma_vote

def add_vote(user_id, is_golden_user, post_id, voteparam):
    if voteparam == 0 or voteparam == 1 or voteparam == 2:
        vote, weighted_vote, karma_vote = vote_values(voteparam, is_golden_user)
        db_execute_commit(
            'INSERT INTO vote(user_id,post_id,vote,weighted_vote,karma_vote) VALUES(:u,:p,:v,:w,:k) '
            'ON CONFLICT(user_id,post_id) DO UPDATE '
            'SET vote=excluded.vote,weighted_vote=excluded.weighted_vote,karma_vote=excluded.karma_vote',
            u=user_id, p=post_id, v=vote, w=weighted_vote, k=karma_vote
        )

def add_comment_vote(user_id, is_golden_user, post_id, comment_id, voteparam):
    if voteparam == 0 or voteparam == 1 or voteparam == 2:
        vote, weighted_vote, karma_vote = vote_values(voteparam, is_golden_user)
        db_execute_commit(
            'INSERT INTO commentvote(user_id,post_id,comment_id,vote,weighted_vote,karma_vote) VALUES(:u,:p,:c,:v,:w,:k)'
            'ON CONFLICT(user_id,post_id,comment_id) DO UPDATE '
            'SET vote=excluded.vote,weighted_vote=excluded.weighted_vote,karma_vote=excluded.karma_vote',
            u=user_id, p=post_id, c=comment_id, v=vote, w=weighted_vote, k=karma_vote
        )

@cache.memoize(timeout=10)
def get_posts_by_id(id):
    posts = get_db().execute(select_posts_with_votes().where(post_table.c.id == id)).fetchall()
    res = [post_from_sql_row(p, None, True) for p in posts]
    return res

def upvoted_downvoted(votes):
    upvoted = [v.comment_id for v in votes if v.vote > 0]
    downvoted = [v.comment_id for v in votes if v.vote < 0]
    return upvoted, downvoted

@cache.memoize(timeout=10)
def get_user_votes_for_comments(user_id, post_id):
    votes = db_execute(
        'SELECT comment_id, vote FROM commentvote '
        'WHERE post_id = :p AND user_id = :u', p=post_id, u=user_id
    ).fetchall()
    return upvoted_downvoted(votes)

@cache.memoize(timeout=60)
def get_user_votes_for_all_comments(user_id):
    # this should probably be optimized somehow?
    votes = db_execute(
        'SELECT comment_id, vote FROM commentvote '
        'WHERE user_id = :u', u=user_id
    ).fetchall()
    return upvoted_downvoted(votes)

def update_or_delete_user_comment(is_moderator, body, post_id, comment_id):

    if not body:
        if is_moderator:
            rendered = "<p><em>комментарий удалён модератором</em></p>"
        else:
            rendered = "<p><em>комментарий удалён</em></p>"
        candelete = db_execute(
            'SELECT id FROM comment WHERE post_id=:p AND parent_id=:c', p=post_id, c=comment_id
        ).fetchone() is None
    else:
        rendered = make_html(body, do_embeds=False)
        candelete = False

    if candelete:
        db_execute_commit('DELETE FROM comment WHERE id=:c', c=comment_id)
    else:
        db_execute_commit(
            'UPDATE comment SET body = :b, rendered = :r, edited = :e, edited_by_moderator = :m WHERE id = :c',
            b=body, r=rendered, e=datetime.now(), m=is_moderator, c=comment_id
        )


def delete_user_comments(since, username):
    comments_data = db_execute(
        '''
        SELECT c.id, c.author_id, c.post_id, u.username
        FROM comment c JOIN notquser u ON c.author_id = u.id
        WHERE u.username == :u AND c.created > :c
        ''', u=username, c=since
    ).fetchall()
    for c in comments_data:
        update_or_delete_user_comment(True, '', c.post_id, c.id)


def delete_user_posts(username):
    id = db_execute('SELECT id FROM notquser WHERE username=:u', u=username).fetchone().id
    db_execute_commit('DELETE FROM post WHERE author_id=:a', a=id)


def add_tags(post_text, post_id, remove_old_tags):
    if remove_old_tags:
        db_execute_commit('DELETE FROM posttag WHERE post_id=:p', p=post_id)
    tags = collect_tags(post_text)
    for tag in tags:
        db_execute_commit('INSERT INTO tag (tagname) VALUES (:t) ON CONFLICT DO NOTHING', t=tag)

        tagdata = db_execute('SELECT id FROM tag WHERE tagname=:t', t=tag).fetchone()
        if tagdata:            
            db_execute_commit('INSERT INTO posttag (post_id, tag_id) VALUES (:p, :t) ON CONFLICT DO NOTHING', 
                              p=post_id, t=tagdata.id)
