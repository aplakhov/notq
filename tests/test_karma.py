from tests.util import *
from notq.cache import cache

def test_karma(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/1/vote/2')
    register_and_login(client, 'ghi', 'a')
    client.post('/1/vote/2')

    cache.clear()

    check_page_contains(client, '/u/abc', '<strong>2</strong>')

    client.post('/auth/login', data={'username': 'abc', 'password': 'a'})
    check_page_contains(client, '/', '<span title="ваша карма" class="navkarma">2</span>')

def test_comments_karma(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3'})

    register_and_login(client, 'def', 'a')
    client.post('/1/votec/1/2')
    client.post('/1/votec/2/2')
    register_and_login(client, 'ghi', 'a')
    client.post('/1/votec/2/2')
    client.post('/1/votec/3/2')

    cache.clear()

    check_page_contains(client, '/u/abc', '<strong>1</strong>')

    client.post('/auth/login', data={'username': 'abc', 'password': 'a'})
    check_page_contains(client, '/', '<span title="ваша карма" class="navkarma">1</span>')
