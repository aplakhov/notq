from notq.markup import make_html

def test_youtube1():
    html = make_html("https://youtu.be/L_Guz73e6fw?t=5300")
    assert('iframe' in html and 'L_Guz73e6fw' in html)

def test_youtube2():
    html = make_html("https://www.youtube.com/watch?v=s_NcZl5bi38&t=132s")
    assert('iframe' in html and 's_NcZl5bi38' in html)

def test_quote():
    html = make_html("> citation")
    assert('<blockquote>' in html and 'citation' in html)

def test_pre():
    html = make_html("    print('Hello world')")
    assert('<pre>' in html and "print('Hello world')" in html)
