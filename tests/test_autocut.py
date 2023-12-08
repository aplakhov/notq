from notq.autocut import autocut
from notq.constants import AUTOCUT_YOUTUBE_HEIGHT
from tests.util import *

LOREM_IPSUM = '''Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
 tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
 exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
 Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
 Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'''

def test_simple_autocut():
    line = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit'
    text = '\n'.join([line] * 4)
    assert autocut(text, 3, False) == '\n'.join([line] * 3)

def test_large_comment_without_paragraphs():
    line = ' '.join(['word'] * 500)
    cut = autocut(line, 20, True)
    assert len(cut) < len(line)

def test_wall_of_letters():
    line = ' '.join(['x'] * 1200)
    cut = autocut(line, 20, True)
    assert len(cut) < len(line)

def check_no_autocut(x):
    assert autocut(x, 15, True) == x

def test_no_autocut():
    check_no_autocut('Мама мыла раму')
    check_no_autocut('1233545')
    check_no_autocut(LOREM_IPSUM)

def test_simple_autocut_after_youtube():
    youtubelink = 'https://www.youtube.com/watch?v=L_Guz73e6fw&t=2582s'
    test = youtubelink + '''
        In other news, water is wet and air is breathable. Lorem ipsum dolor sit amet, consectetur adipiscing elit.'''
    cut = autocut(test, AUTOCUT_YOUTUBE_HEIGHT, False)
    assert cut == youtubelink

def test_autocut_real_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')
    check_page_doesnt_contain(client, '/', 'Читать дальше')
    make_post(client, 'post1', ' '.join([LOREM_IPSUM] * 10))
    check_page_contains(client, '/new', 'Читать дальше')
    check_page_doesnt_contain(client, '/1', 'Читать дальше')
    check_page_doesnt_contain(client, '/2', 'Читать дальше')
