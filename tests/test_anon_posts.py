from tests.util import *

def test_anon_post1(client):
    register_and_login(client, 'abc', 'a')

    title = 'Some post'
    body = 'This is very sensitive'
    make_post(client, title, body, authorship='anon')

    fragments = [title, body, '<div id="nv1">1</div>']
    check_page_contains_several(client, '/', fragments + ['style="color: #00a000"'])
    check_page_doesnt_contain(client, '/u/abc', title)

    client.get('/auth/logout')
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/u/abc', title)

def test_anon_post2(client):
    register_and_login(client, 'abc', 'a')

    title = 'Some post'
    body = 'This is very sensitive'
    make_post(client, title, body, authorship='paranoid')

    fragments = [title, body, '<div id="nv1">0</div>']
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/', 'style="color: #00a000"')
    check_page_doesnt_contain(client, '/u/abc', title)

    client.get('/auth/logout')
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/u/abc', title)

def test_comment(client):
    register_and_login(client, 'abc', 'a')
    title = 'Some post'
    body = 'This is a post'
    make_post(client, title, body)

    commenttext = "answer1"
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':commenttext})

    fragments = [title, body, commenttext, 'abc', 'def']
    check_page_contains_several(client, '/1', fragments + ['style="color: #00a000"'])
    client.get('/auth/logout')
    check_page_contains_several(client, '/1', fragments)

def anon_comment_checks(client, type):
    register_and_login(client, 'abc', 'a')
    title = 'Some post'
    body = 'This is a post'
    make_post(client, title, body)

    commenttext = "answer1"
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':commenttext, 'authorship': type})

    fragments = [title, body, commenttext, 'abc', 'anonymous']
    check_page_contains_several(client, '/1', fragments)
    client.get('/auth/logout')
    check_page_contains_several(client, '/1', fragments)
    check_page_doesnt_contain(client, '/1', 'def')

def test_anon_comment1(client):
    anon_comment_checks(client, 'anon')
    
def test_anon_comment2(client):
    anon_comment_checks(client, 'paranoid')

def test_anonymous_userpage(client):
    check_page_contains_several(client, '/u/anonymous', ['logo.png', 'anonymous'])
