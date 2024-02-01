from tests.util import *
from notq.autocut import autocut
from notq.constants import AUTOCUT_COMMENT_HEIGHT

def test_comment_as_post(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment1'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':1, 'text':'comment2', 'newpost':'on'})
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':'comment3', 'newpost':'on'})
    
    register_and_login(client, 'ghi', 'a')
    check_page_contains_several(client, '/1', ['abc', 'def', 'comment1', 'comment2', 'comment3'])
    check_page_contains_several(client, '/2', ['<h1>Ответ на запись &#34;post1&#34;</h1>', 'def', 'comment2'])
    check_page_contains_several(client, '/3', ['<h1>Ответ на запись &#34;post1&#34;</h1>', 'def', 'comment3'])

def test_comment_as_post_and_return(client):
    register_and_login(client, 'abc', 'a')
    make_post(client, 'post1', 'content1')

    register_and_login(client, 'def', 'a')
    lorem_ipsum = 'Sed ut perspiciatis, unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam eaque ipsa, quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt, explicabo. Nemo enim ipsam voluptatem, quia voluptas sit, aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos, qui ratione voluptatem sequi nesciunt, neque porro quisquam est, qui dolorem ipsum, quia dolor sit, amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt, ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit, qui in ea voluptate velit esse, quam nihil molestiae consequatur, vel illum, qui dolorem eum fugiat, quo voluptas nulla pariatur? At vero eos et accusamus et iusto odio dignissimos ducimus, qui blanditiis praesentium voluptatum deleniti atque corrupti, quos dolores et quas molestias excepturi sint, obcaecati cupiditate non provident, similique sunt in culpa, qui officia deserunt mollitia animi, id est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio, cumque nihil impedit, quo minus id, quod maxime placeat, facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet, ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat.' * 3
    assert lorem_ipsum != autocut(lorem_ipsum, AUTOCUT_COMMENT_HEIGHT, True)
    client.post('/addcomment', data={'parentpost':1, 'parentcomment':0, 'text':lorem_ipsum, 'newpost':'on'})

    check_page_contains_several(client, '/', ['<h1>Ответ на запись &#34;post1&#34;</h1>', 'def', lorem_ipsum[:50]])
    check_page_contains_several(client, '/2', ['<h1>Ответ на запись &#34;post1&#34;</h1>', 'def', lorem_ipsum])
    check_page_contains_several(client, '/1', ['abc', 'post1', 'def', 'Sed ut perspiciatis', 'Читать дальше →'])
