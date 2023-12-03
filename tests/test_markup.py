from notq.markup import make_html

def test_youtube1():
    html = make_html("https://youtu.be/L_Guz73e6fw?t=5300")
    assert('iframe' in html and 'L_Guz73e6fw' in html and '5300' not in html)

def test_youtube2():
    html = make_html("https://www.youtube.com/watch?v=s_NcZl5bi38&t=132s")
    assert('iframe' in html and 's_NcZl5bi38' in html and '132' not in html)

def test_youtube_no_pwn():
    html = make_html("https://www.youtube.com/watch?v=<script>")
    assert(not '<script>' in html)

def test_quote():
    html = make_html("> citation")
    assert('<blockquote>' in html and 'citation' in html)

def test_pre():
    html = make_html("    print('Hello world')")
    assert('<pre>' in html and "print('Hello world')" in html)

def check_username(src):
    html = make_html(src)
    assert('<a class="username" href="/u/finder"><img src="/static/silver.png">finder</a>' in html)

def test_usernames():
    check_username('/u/finder')
    check_username('(/u/finder)')
    check_username('а также /u/finder и др.')
    check_username('Привет.\n/u/finder как-то сказал')
    html = make_html('https://reddit.com/u/finder')
    assert(not 'silver.png' in html)

def test_wikilinks():
    html = make_html('[[Москва]], [[London]]')
    expected = r'<a href="https://ru.wikipedia.org/wiki/%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0">Москва</a>, <a href="https://en.wikipedia.org/wiki/London">London</a>'
    assert(expected in html)

def test_code_hilite():
    code = '''
    import re
    import markdown
    from markdown.extensions.wikilinks import WikiLinkExtension
    from html_sanitizer import Sanitizer

    sanitizerConfig = {
        "tags": {
            "a", "h1", "h2", "h3", "strong", "em", "p", "ul", "ol",
            "li", "br", "sub", "sup", "s", "hr", "blockquote", "pre",
            "div", "span", "code",
        },
        "attributes": {"a": ("href",), "div": ("class",), "span": ("class",), "code": ("class",)},
        "empty": {"hr", "a", "br"},
        "separate": {"a", "p", "li", "span"},
        "whitespace": {"br"},
        "keep_typographic_whitespace": True,
    }

    def sanitizeHtml(value):
        sanitizer = Sanitizer(sanitizerConfig)
        return sanitizer.sanitize(value)
    '''
    html = make_html(code)
    assert('<div class="codehilite"><pre><code>' in html)
    assert('<span class="kn">import</span>' in html)
