from notq.db import db_execute_commit

def register_and_login(client, username, password):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': username, 'password': password}
    )
    assert response.headers["Location"] == "/"

def make_post(client, title, body, authorship="thisuser"):
    check_page_contains(client, '/create', 'Написать')
    client.post('/create', data={'title':title, 'body':body, 'authorship':authorship})

def check_page_contains(client, url, what):
    response = client.get(url)
    assert response.status_code == 200
    if not what.encode() in response.data:
        print(response.data.decode())
    assert what.encode() in response.data

def check_page_doesnt_contain(client, url, what):
    response = client.get(url)
    assert response.status_code == 200
    if what.encode() in response.data:
        print(response.data.decode())
    assert what.encode() not in response.data

def check_page_contains_several(client, url, fragments):
    response = client.get(url)
    assert response.status_code == 200
    for what in fragments:
        if not what.encode() in response.data:
            print(response.data.decode())
            print(what)
        assert what.encode() in response.data

def check_forbidden_action(client, url, data=None):
    response = client.post(url, data=data)
    assert response.status_code == 403 or (response.status_code == 302 and response.headers["Location"] == '/auth/login')

def become_moderator(app, username):
    with app.app_context():
        db_execute_commit("UPDATE user SET is_moderator=1 WHERE username = :u", u=username)

def make_user_golden(app, username):
    with app.app_context():
        db_execute_commit("UPDATE user SET is_golden=1 WHERE username = :u", u=username)
