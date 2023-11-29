def register_and_login(client, username, password):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': username, 'password': password}
    )
    assert response.headers["Location"] == "/"

def check_page_contains(client, url, what):
    response = client.get(url)
    assert response.status_code == 200
    assert(what.encode() in response.data)

def check_page_doesnt_contain(client, url, what):
    response = client.get(url)
    assert response.status_code == 200
    assert(what.encode() not in response.data)

def check_page_contains_several(client, url, fragments):
    response = client.get(url)
    assert response.status_code == 200
    for what in fragments:
        assert(what.encode() in response.data)

def test_anon_post1(client):
    register_and_login(client, 'abc', 'a')

    check_page_contains(client, '/create', 'Написать')
    title = 'Some post'
    body = 'This is very sensitive'
    client.post('/create', data={'title':title, 'body':body, 'authorship':'anon'})

    fragments = [title, body, '<div id="nv1">1</div>']
    check_page_contains_several(client, '/', fragments + ['style="color: #00a000"'])
    check_page_doesnt_contain(client, '/u/abc', title)

    client.get('/auth/logout')
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/u/abc', title)

def test_anon_post2(client):
    register_and_login(client, 'abc', 'a')

    check_page_contains(client, '/create', 'Написать')
    title = 'Some post'
    body = 'This is very sensitive'
    client.post('/create', data={'title':title, 'body':body, 'authorship':'paranoid'})

    fragments = [title, body, '<div id="nv1">0</div>']
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/', 'style="color: #00a000"')
    check_page_doesnt_contain(client, '/u/abc', title)

    client.get('/auth/logout')
    check_page_contains_several(client, '/', fragments)
    check_page_doesnt_contain(client, '/u/abc', title)

def test_comment(client):
    register_and_login(client, 'abc', 'a')
    check_page_contains(client, '/create', 'Написать')
    title = 'Some post'
    body = 'This is a post'
    client.post('/create', data={'title':title, 'body':body})

    commenttext = "answer1"
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':commenttext})

    fragments = [title, body, commenttext, 'abc', 'def']
    check_page_contains_several(client, '/1', fragments + ['style="color: #00a000"'])
    client.get('/auth/logout')
    check_page_contains_several(client, '/1', fragments)

def anon_comment_checks(client, type):
    register_and_login(client, 'abc', 'a')
    check_page_contains(client, '/create', 'Написать')
    title = 'Some post'
    body = 'This is a post'
    client.post('/create', data={'title':title, 'body':body})

    commenttext = "answer1"
    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':commenttext, 'authorship': type})

    fragments = [title, body, commenttext, 'abc', 'Anonymous']
    check_page_contains_several(client, '/1', fragments)
    client.get('/auth/logout')
    check_page_contains_several(client, '/1', fragments)
    check_page_doesnt_contain(client, '/1', 'def')

def test_anon_comment1(client):
    anon_comment_checks(client, 'anon')
    
def test_anon_comment2(client):
    anon_comment_checks(client, 'paranoid')