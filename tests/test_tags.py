import time
from tests.util import *

def test_tags(client):
    register_and_login(client, 'abc', 'a')
    content1 = 'Вот пост с тэгами #math и #boobs'
    make_post(client, 'post_heading1', content1)
    content2 = 'А вот только с тэгом #boobs и загадочной картинкой.\nЧто же на ней изображено?'
    make_post(client, 'post_heading2', content2)

    check_page_contains_several(client, '/tag/boobs', ['abc', 'post_heading1', 'post_heading2'])

    check_page_contains_several(client, '/tag/math', ['abc', 'post_heading1'])
    check_page_doesnt_contain(client, '/tag/random', 'post_heading2')

    check_page_doesnt_contain(client, '/tag/random', 'post_heading')
