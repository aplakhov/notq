import time
from tests.util import *

def test_golden_user(client, app):
    register_and_login(client, 'gld', 'a')
    make_user_golden(app, 'gld')
    check_page_contains(client, '/', 'gold.png')
    make_post(client, 'title1', 'post1')
    make_post(client, 'title2', 'post2', authorship='anon')
    register_and_login(client, 'def', 'a')
    check_page_doesnt_contain(client, '/', 'gold.png')
    check_page_contains(client, '/1', 'gold.png')
    check_page_doesnt_contain(client, '/2', 'gold.png')

def test_golden_user_comments(client, app):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'title1', 'post1')
    make_post(client, 'title2', 'post2')
    register_and_login(client, 'gld', 'a')
    make_user_golden(app, 'gld')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment2'})
    client.post('/addcomment', data={'parentpost':2, 'parentcomment':0, 'text':'comment3'})
    check_page_contains(client, '/1', 'gold.png')
    check_page_doesnt_contain(client, '/2', 'gold.png')
