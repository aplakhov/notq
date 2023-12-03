from tests.util import *

def test_update_comments(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3'})

    client.post('/1/updatecomment/1', data={'body':''})
    client.post('/1/updatecomment/2', data={'body':'edited comment2'})
    client.post('/1/updatecomment/3', data={'body':''})

    response = client.get('/1')
    assert response.status_code == 200
    html = response.data.decode()

    assert('comment1' not in html)
    assert('edited comment2' in html)
    assert('comment3' not in html)
    assert('комментарий удалён' in html)

    register_and_login(client, 'ghi', 'a')
    response = client.post('/1/updatecomment/2', data={'body': 'pwn'})
    assert response.status_code == 403

def test_moderator_actions(client, app):
    register_and_login(client, 'spamer', 'a')
    make_post(client, 'post1', 'spamcontent1')
    make_post(client, 'post2', 'spamcontent2')
    make_post(client, 'post3', 'spamcontent3')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'spamcontent'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'https://spamcontent.ru'})
    client.post('/addcomment', data={'parentpost':2, 'parentcomment':0, 'text':r'%%spamcontent%%'})

    register_and_login(client, 'def', 'a')
    become_moderator(app, 'def')
    client.get('/u/spamer/delete/all')

    response = client.get('/1')
    assert response.status_code == 404

    response = client.get('/')
    assert response.status_code == 200
    assert 'spamcontent' not in response.data.decode()

    response = client.get('/u/spamer')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'Лишен слова' in html and 'spamer' in html
