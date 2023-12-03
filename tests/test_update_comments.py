from tests.util import *
import time

def test_update_comments(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3'})
    time.sleep(1)

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
