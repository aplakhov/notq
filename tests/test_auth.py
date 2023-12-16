import pytest
from notq.db import get_db
from sqlalchemy import text

def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'abc', 'password': 'a'}
    )
    assert response.headers["Location"] == "/"

    with app.app_context():
        assert get_db().execute(
            text("SELECT * FROM notquser WHERE username = 'abc'"),
        ).fetchone() is not None
        assert get_db().execute(
            text("SELECT * FROM notquser WHERE username = 'def'"),
        ).fetchone() is None


def test_register_bad_username(client):
    response = client.post('/auth/register', data={'username': 'SuperModerator', 'password': 'a'})
    assert 'Такое имя нельзя зарегистрировать' in response.data.decode()


def test_register_twice(client):
    client.post('/auth/register', data={'username': 'AndreyPlakhov', 'password': 'a'})
    response = client.post('/auth/register', data={'username': 'andreyPlakhov', 'password': 'a'})
    assert 'уже зарегистрирован' in response.data.decode()


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('', '', 'Нужно указать имя пользователя.'),
    ('a', 'abc', 'Слишком короткое имя пользователя.'),
    ('01234567890123456789012345678901234567890', '', 'Слишком длинное имя пользователя.'),
    ('Вася', '', 'Имя пользователя может состоять только из латиницы, цифр и символа'),
    ('John Snow', '', 'Имя пользователя может состоять только из латиницы, цифр и символа'),
    ('abc', '', 'Нужно указать пароль.'),
))
def test_register_validate_input(client, username, password, message):
    response = client.post(
        '/auth/register',
        data={'username': username, 'password': password}
    )
    assert message.encode() in response.data