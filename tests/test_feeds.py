from tests.util import *

def test_new_feed(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    make_post(client, 'post2', 'content2')

    check_page_contains_several(client, '/feed/new', [
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        'abc', 'post1', 'content1', 'post2', 'content2'
    ])

def test_upvoted_feed(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    make_post(client, 'post2', 'content2')

    register_and_login(client, 'def', 'a')
    client.post('/1/vote/2')

    register_and_login(client, 'ghi', 'a')
    client.post('/1/vote/2')

    check_page_doesnt_contain(client, '/feed/upvoted', 'post2');
    check_page_contains_several(client, '/feed/new', [
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        'abc', 'post1', 'content1'
    ])

def test_user_feed(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    register_and_login(client, 'def', 'a')
    make_post(client, 'post2', 'content2')

    check_page_doesnt_contain(client, '/feed/u/abc', 'post2');
    check_page_contains_several(client, '/feed/u/abc', [
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        'abc', 'post1', 'content1'
    ])
    check_page_doesnt_contain(client, '/feed/u/def', 'post1');
    check_page_contains_several(client, '/feed/u/def', [
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        'def', 'post2', 'content2'
    ])
