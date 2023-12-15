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

    assert 'comment1' not in html
    assert 'edited comment2' in html
    assert 'comment3' not in html
    assert 'комментарий удалён' in html

    register_and_login(client, 'ghi', 'a')
    response = client.post('/1/updatecomment/2', data={'body': 'pwn'})
    assert response.status_code == 403

def test_cant_edit_not_your_comment(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment2'})
    check_forbidden_action(client, '/1/updatecomment/1', data={'body':'new content'})
    check_forbidden_action(client, '/1/updatecomment/1', data={'body':''})

    client.get('/auth/logout')
    check_forbidden_action(client, '/1/updatecomment/1', data={'body':'new content'})
    check_forbidden_action(client, '/1/updatecomment/1', data={'body':''})
    check_forbidden_action(client, '/1/updatecomment/2', data={'body':'new content'})
    check_forbidden_action(client, '/1/updatecomment/2', data={'body':''})

    register_and_login(client, 'ghi', 'a')    
    check_page_contains_several(client, '/1', ['comment1', 'comment2'])
