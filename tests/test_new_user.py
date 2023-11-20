def test_new_user(client):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'abc', 'password': 'a'}
    )
    assert response.headers["Location"] == "/auth/login"

    response = client.post(
        '/auth/login', data={'username': 'abc', 'password': 'a'}
    )
    assert response.headers["Location"] == "/"
    
    response = client.get('/u/abc')
    assert('abc'.encode() in response.data)
    assert('Этот пользователь пока ничего о себе не написал'.encode() in response.data)
