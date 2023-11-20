import pytest
from notq.db import get_db

def test_register(client, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'abc', 'password': 'a'}
    )
    assert response.headers["Location"] == "/auth/login"

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'abc'",
        ).fetchone() is not None


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