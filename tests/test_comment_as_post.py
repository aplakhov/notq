import time
from tests.util import *

def test_comment_as_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2', 'newpost':'on'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3', 'newpost':'on'})
    
    time.sleep(10)
    register_and_login(client, 'ghi', 'a')
    check_page_contains_several(client, '/1', ['abc', 'def', 'comment1', 'comment2', 'comment3'])
    check_page_contains_several(client, '/2', ['Ответ на запись "post1"', 'def', 'comment2'])
    check_page_contains_several(client, '/3', ['Ответ на запись "post1"', 'def', 'comment3'])
