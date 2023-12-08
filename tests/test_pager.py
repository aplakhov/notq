from tests.util import *
from notq.constants import POST_FEED_PAGE_SIZE

def test_throttling(client):
    register_and_login(client, 'abc', 'a')
    for n in range(10):
        make_post(client, f'post{n}', f'content{n}')
    check_page_doesnt_contain(client, '/', 'content5')
    check_page_doesnt_contain(client, '/new', 'content5')
    check_page_doesnt_contain(client, '/best/day', 'content5')

def check_pager_50_posts(client, base_url):
    check_page_contains_several(client, base_url + '/page/1', ['postcontent', 'Страница'])
    check_page_doesnt_contain(client, base_url + '/page/2', 'postcontent')
    if not base_url:
        base_url = '/'
    check_page_contains_several(client, base_url, ['postcontent', 'Страница'])

def test_comment_as_post(client):
    for n in range(2 * POST_FEED_PAGE_SIZE):
        register_and_login(client, f'user{n}', 'a')
        make_post(client, f'post{n}', f'postcontent{n}')
    check_pager_50_posts(client, '')
    check_pager_50_posts(client, '/new')
    check_pager_50_posts(client, '/best/day')
    check_pager_50_posts(client, '/best/week')
