from datetime import datetime
from notq.data_model import get_new_posts, get_user_posts

from flask import Blueprint, abort, make_response, render_template

bp = Blueprint('feed', __name__, url_prefix='/feed')

def make_atom_feed(name, link, selfurl, posts):
    justnow = datetime.now()
    filtered_posts = [p for p in posts if p['created_ts'] < justnow]
    updated = max([p['created_ts'] for p in filtered_posts])
    updated_str = updated.strftime(r'%Y-%m-%dT%H:%M:%SZ')
    for p in filtered_posts:
        p['updated'] = p['created_ts'].strftime(r'%Y-%m-%dT%H:%M:%SZ')
    
    content = render_template('feed/atom.xml', name=name, posts=filtered_posts, updated=updated_str, link=link, selfurl=selfurl)
    res = make_response(content)
    res.headers['Content-Type'] = 'application/atom+xml; charset=utf-8'
    return res

@bp.route('/new', methods=['GET'])
def atom_new():
    return make_atom_feed('Новое', 'https://notq.ru/new', 'https://notq.ru/feed/new', get_new_posts())

@bp.route('/upvoted', methods=['GET'])
def atom_upvoted():
    posts = [p for p in get_new_posts() if p['votes'] > 2]
    return make_atom_feed('Оцененное', 'https://notq.ru/', 'https://notq.ru/feed/upvoted', posts)

@bp.route('/u/<username>', methods=['GET'])
def atom_userpage(username):
    posts = get_user_posts(username)
    if not posts:
        abort(404)
    return make_atom_feed(username, 'https://notq.ru/u/' + username, 'https://notq.ru/feed/u/' + username, posts)
