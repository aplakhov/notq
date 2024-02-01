from tests.util import *

def make_some_spam_and_a_moderator(client, app):
    register_and_login(client, 'spamer', 'a')
    make_post(client, 'post1', 'spamcontent1')
    make_post(client, 'post2', 'spamcontent2')
    make_post(client, 'post3', 'spamcontent3')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'spamcontent in comment'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'https://spamcontent.ru'})
    client.post('/addcomment', data={'parentpost':2, 'parentcomment':0, 'text':r'%%spamcontent%%'})

    register_and_login(client, 'mdrtr', 'a')
    become_moderator(app, 'mdrtr')

def test_moderator_ui(client, app):
    make_some_spam_and_a_moderator(client, app)
    client.get('/u/spamer')
    check_page_contains_several(client, '/u/spamer', [
        'spamcontent',
        'https://spamcontent.ru',
        'spamcontent in comment',
        'Забанить', 'Удалить', 'Последние комментарии',
        'Мод.'
    ])

def test_moderator_post_actions(client, app):
    make_some_spam_and_a_moderator(client, app)
    
    client.post('/1/update', data={'title':'post1', 'body':'Тут был спам'})

    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'spamcontent1' not in html
    assert 'Тут был спам' in html
    assert 'Отредактировано модератором' in html

    check_page_contains_several(client, '/1', ['Тут был спам', 'Отредактировано модератором'])


def test_moderator_comment_actions(client, app):
    make_some_spam_and_a_moderator(client, app)
    
    client.post('/1/updatecomment/1', data={'body':'Тут был спам'})

    response = client.get('/1')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'spamcontent in comment' not in html
    assert 'Тут был спам' in html

    client.post('/1/updatecomment/2', data={'body':''})
    check_page_doesnt_contain(client, '/1', 'https://spamcontent.ru')


def test_moderator_user_actions(client, app):
    make_some_spam_and_a_moderator(client, app)

    client.get('/u/spamer/delete/all')

    response = client.get('/1')
    assert response.status_code == 404

    check_page_doesnt_contain(client, '/', 'spamcontent')

    response = client.get('/u/spamer')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'Лишен слова' in html and 'spamer' in html

def test_moderator_anonymous(client, app):
    register_and_login(client, 'spamer', 'a')
    make_post(client, 'post1', 'spamcontent1', authorship='anon')
    make_post(client, 'post2', 'spamcontent2', authorship='paranoid')
    make_post(client, 'post3', 'normcontent')

    register_and_login(client, 'mdrtr', 'a')
    become_moderator(app, 'mdrtr')

    check_page_doesnt_contain(client, '/u/spamer', 'spamcontent')
    check_page_contains_several(client, '/u/anonymous', ['spamcontent1', 'spamcontent2'])
    check_page_doesnt_contain(client, '/u/anonymous', 'normcontent')
