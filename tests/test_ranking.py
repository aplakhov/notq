from tests.util import *
import time
 
def check_page_contains_ordered(client, url, fragments):
    response = client.get(url)
    assert response.status_code == 200
    prev_idx = -1
    for what in fragments:
        idx = response.data.find(what.encode())
        assert idx >= 0, what + " should be found"
        assert idx > prev_idx, what + " should go in order"
        prev_idx = idx

def test_posts_ranking(client):
    register_and_login(client, 'abc', 'a')

    make_post(client, 'post1', 'content1')
    time.sleep(1)
    make_post(client, 'post2', 'content2')
    time.sleep(1)
    make_post(client, 'post3', 'content3')
    time.sleep(1)
    make_post(client, 'post4', 'content4')

    # novote on post1, downvote post2
    client.post('/1/vote/1')
    client.post('/2/vote/0')

    register_and_login(client, 'def', 'a')
    # upvote post3
    client.post('/3/vote/2')

    # check that everything goes in order post3 (2 votes), post4 (1 vote), post1 (0 votes), post2 (-1 vote)
    votes_ordered = ['post3', 'content3', 'post4', 'content4', 'post1', 'content1', 'post2', 'content2']
    check_page_contains_ordered(client, '/', votes_ordered)

    best_ordered = ['post3', 'content3', 'post4', 'content4', 'post1', 'content1'] # no post2 because it has negative score
    check_page_contains_ordered(client, '/best/day', best_ordered)
    check_page_contains_ordered(client, '/best/year', best_ordered)

    time_ordered = ['post4', 'content4', 'post3', 'content3', 'post2', 'content2', 'post1', 'content1']
    check_page_contains_ordered(client, '/new', time_ordered)

def test_comments_ranking(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment4'})
    time.sleep(1)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment5'})
    # novote on comment1, downvote comment3
    client.post('/1/votec/1/1')
    client.post('/1/votec/3/0')

    register_and_login(client, 'ghi', 'a')
    # upvote comment 4
    client.post('/1/votec/4/2')

    ordered = ['post1', 'content1', 
                'comment4', # 2 votes
                'comment5', # 1 vote
                'comment1', # 0 votes
                'comment2', # goes after comment1
                'comment3'  # -1 vote
            ]
    check_page_contains_ordered(client, '/1', ordered)
