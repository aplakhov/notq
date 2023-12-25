from tests.util import *
from notq.constants import POST_FEED_PAGE_SIZE, POST_COMMENTS_PAGE_SIZE

def test_throttling(client):
    register_and_login(client, 'abc', 'a')
    for n in range(10):
        make_post(client, f'post{n}', f'content{n}')
    check_page_doesnt_contain(client, '/', 'content5')
    check_page_doesnt_contain(client, '/new', 'content5')
    check_page_doesnt_contain(client, '/best/day', 'content5')

def check_exactly_2_pages_pager(client, base_url):
    check_page_contains_several(client, base_url + '/page/1', ['postcontent', 'Страница'])
    check_page_doesnt_contain(client, base_url + '/page/2', 'postcontent')
    if not base_url:
        base_url = '/'
    check_page_contains_several(client, base_url, ['postcontent', 'Страница'])

def test_posts_pager(client):
    for n in range(2 * POST_FEED_PAGE_SIZE):
        register_and_login(client, f'user{n}', 'a')
        make_post(client, f'post{n}', f'postcontent{n}')
    check_exactly_2_pages_pager(client, '')
    check_exactly_2_pages_pager(client, '/new')
    check_exactly_2_pages_pager(client, '/best/day')
    check_exactly_2_pages_pager(client, '/best/week')

def check_exactly_2_pages_comments_pager(client):
    check_page_contains_several(client, '/1', ['postcontent', 'comment', 'Страница'])
    check_page_contains_several(client, '/1/page/1', ['postcontent', 'comment', 'Страница'])
    check_page_doesnt_contain(client, '/1/page/2', 'comment')

def test_comments_pager(client):
    register_and_login(client, 'postuser', 'a')
    make_post(client, 'post0', 'postcontent')
    for n in range(POST_COMMENTS_PAGE_SIZE + 1):
        register_and_login(client, f'user{n}', 'a')
        client.post('/addcomment', data={'parentpost':1, 'parentcomment': 0, 'text': f'comment{n}'})
    check_exactly_2_pages_comments_pager(client)

def test_nested_comments_pager(client):
    register_and_login(client, 'postuser', 'a')
    make_post(client, 'post0', 'postcontent')

    register_and_login(client, 'topcommentuser', 'b')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment': 0, 'text': f'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment': 0, 'text': f'comment2'})

    for parent in [1, 2]:
        for n in range(POST_COMMENTS_PAGE_SIZE):
            cn = parent * POST_COMMENTS_PAGE_SIZE + n
            register_and_login(client, f'user{cn}', 'a')
            client.post('/addcomment', data={'parentpost':1, 'parentcomment': parent, 'text': f'comment{cn}'})
    check_exactly_2_pages_comments_pager(client)
