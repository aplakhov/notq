def register_and_login(client, username, password):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': username, 'password': password}
    )
    assert response.headers["Location"] == "/auth/login"

    response = client.post(
        '/auth/login', data={'username': username, 'password': password}
    )
    assert response.headers["Location"] == "/"

def assert_default_self_page(client, username):
    response = client.get('/u/' + username)
    assert(username.encode() in response.data)
    assert('Этот пользователь пока ничего о себе не написал'.encode() in response.data)

def assert_nondefault_self_page(client, username, text):
    response = client.get('/u/' + username)
    assert(username.encode() in response.data)
    assert(text.encode() in response.data)

def test_new_user(client):
    register_and_login(client, "abc", "a")
    assert_default_self_page(client, "abc")

def test_two_new_users(client):
    register_and_login(client, "abc", "a")
    client.get('/auth/logout')
    
    register_and_login(client, "def", "a")
    
    assert_default_self_page(client, "abc")
    assert_default_self_page(client, "def")
    
    assert client.get('/about').status_code == 200
    client.post('/about', data={'body': 'hello world'})
    assert_nondefault_self_page(client, "def", "hello world")
    assert_default_self_page(client, "abc")

def check_all_pages(client):
    assert client.get('/').status_code == 200
    assert client.get('/u/some_unknown_user').status_code == 404
    assert client.get('/new').status_code == 200
    assert client.get('/best/day').status_code == 200
    assert client.get('/best/day/users').status_code == 200
    assert client.get('/best/day/comments').status_code == 200

def test_empty_service(client):
    check_all_pages(client)
    register_and_login(client, "abc", "a")
    check_all_pages(client)
