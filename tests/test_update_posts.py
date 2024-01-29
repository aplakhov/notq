from tests.util import *

def test_update_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    make_post(client, 'post2', 'content2')

    client.post('/1/update', data={'title':'postNew', 'body':'new content'})

    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'post1' not in html
    assert 'content1' not in html
    assert 'postNew' in html
    assert 'new content' in html
    assert 'Отредактировано модератором' not in html

    check_page_contains(client, '/1', 'new content')

    register_and_login(client, 'def', 'a')
    response = client.post('/2/update', data={'title':'post2', 'body':'new content'})
    assert response.status_code == 403

    response = client.get('/2')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'post2' in html
    assert 'content2' in html
    assert 'new content' not in html

def test_delete_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    make_post(client, 'post2', 'content2')

    client.post('/1/delete')
    
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode()
    assert 'post1' not in html
    assert 'content1' not in html
    assert 'post2' in html
    assert 'content2' in html

def test_cant_edit_or_delete_not_your_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    do_logout(client, 'abc')
    check_forbidden_action(client, '/1/update', data={'title':'post1', 'body':'new content'})
    check_forbidden_action(client, '/1/delete')

    register_and_login(client, 'def', 'a')
    check_forbidden_action(client, '/1/update', data={'title':'post1', 'body':'new content'})
    check_forbidden_action(client, '/1/delete')
    
    check_page_contains_several(client, '/', ['post1', 'content1'])
