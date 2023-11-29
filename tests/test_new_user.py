from tests.util import *

def assert_default_self_page(client, username):
    response = client.get('/u/' + username)
    assert response.status_code == 200
    assert(username.encode() in response.data)
    assert('Этот пользователь пока ничего о себе не написал'.encode() in response.data)

def test_new_user(client):
    register_and_login(client, 'abc', 'a')
    assert_default_self_page(client, 'abc')

def test_two_new_users(client):
    register_and_login(client, 'abc', 'a')
    client.get('/auth/logout')
    
    register_and_login(client, 'def', 'a')
    
    assert_default_self_page(client, 'abc')
    assert_default_self_page(client, 'def')
    
    assert client.get('/about').status_code == 200
    client.post('/about', data={'body': 'hello world'})
    check_page_contains(client, '/u/def', 'hello world')
    assert_default_self_page(client, 'abc')

def check_all_pages(client):
    assert client.get('/').status_code == 200
    assert client.get('/u/some_unknown_user').status_code == 404
    assert client.get('/new').status_code == 200
    assert client.get('/best/day').status_code == 200
    assert client.get('/best/day/users').status_code == 200
    assert client.get('/best/day/comments').status_code == 200

def test_empty_service(client):
    check_all_pages(client)
    register_and_login(client, 'abc', 'a')
    check_all_pages(client)

def test_logout(client):
    register_and_login(client, 'abc', 'a')
    client.get('/auth/logout')
    check_page_contains(client, '/', 'Войти')
    assert_default_self_page(client, 'abc')

def test_first_post_self_upvote(client):
    register_and_login(client, 'abc', 'a')
    title = 'Пост'
    body = 'А теперь о погоде'
    make_post(client, title, body)
    fragments = [title, body, '<div id="nv1">1</div>']
    check_page_contains_several(client, '/', fragments + ['style="color: #00a000"'])
    client.get('/auth/logout')
    check_page_contains_several(client, '/', fragments)

def test_two_votes(client):
    register_and_login(client, 'abc', 'a')
    title = 'Some post'
    body = 'Need upvotes'
    make_post(client, title, body)

    register_and_login(client, 'def', 'a')
    client.post('/1/vote/2')

    fragments = [title, body, '<div id="nv1">2</div>']
    check_page_contains_several(client, '/', fragments + ['style="color: #00a000"'])
