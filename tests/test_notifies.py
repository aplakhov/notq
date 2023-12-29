from sqlalchemy import text
from notq.db import get_db
from tests.util import *

def has_notifies(username):
    return get_db().execute(
            text(f"SELECT * FROM notifies n JOIN notquser u ON u.id=n.user_id WHERE u.username = '{username}'"),
        ).fetchone() is not None

def test_no_notify_on_self_answer(client, app):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'title1', 'post1')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    with app.app_context():
        assert not has_notifies('abc')

def test_notify(client, app):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'title1', 'post1')
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    with app.app_context():
        assert has_notifies('abc')
        assert not has_notifies('def')
    register_and_login(client, 'ghi', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    with app.app_context():
        assert has_notifies('def')
        assert not has_notifies('ghi')

def test_notify_anon_answer(client, app):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'title1', 'post1')
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1', 'authorship': 'anon'})
    with app.app_context():
        notify = get_db().execute(
            text("SELECT * FROM notifies n JOIN notquser u ON u.id=n.user_id WHERE u.username = 'abc'"),
        ).fetchone()
        assert notify
        assert 'title1' in notify.text
        assert 'anonymous' in notify.text
        assert 'def' not in notify.text
