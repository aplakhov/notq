from notq.markdown_tags import collect_tags
from notq.markup import make_html

def test_basic_markdown():
    assert "<strong>test" in make_html('**test**')
    assert "<em>test" in make_html('*test*')
    assert '<a href="http://example.com">link label</a>' in make_html('[link label](http://example.com)')
    assert '<a href="https://ya.ru">Ссылка кириллицей</a>' in make_html('[Ссылка кириллицей](https://ya.ru)\nЕщё какой-то текст')

def test_images_markdown():
    img_url = 'https://avatars.mds.yandex.net/get-znatoki/1649112/2a0000017df2e071b3be6ccc02411b7d362a'
    html = make_html(f"![image description]({img_url})")
    assert '<img' in html
    assert f'src="{img_url}"' in html
    assert 'image description' in html

def check_simple_url(u):
    html = make_html(u)
    assert '<a href=' in html and u in html
    html = make_html('Вот url:\n' + u)
    assert '<a href=' in html and u in html
    html = make_html('Вот url:\n\n' + u)
    assert '<a href=' in html and u in html

def check_user_link_preserved(u):
    initial = '<a href="' + u + '">ссылка</a>'
    assert initial in make_html(initial)

def test_simple_urls():
    check_simple_url("https://ya.ru")
    check_simple_url("https://ru.wikipedia.org/wiki/Тест")
    check_simple_url("https://yandex.ru/search/?text=тест")
    check_simple_url("vk.com")
    check_simple_url("mail.ru")

    check_user_link_preserved("https://google.com")
    check_user_link_preserved("http://reddit.com/r/programming/top?sort=month")

    assert 'href' not in make_html("finder@yandex-team.ru")

def test_youtube1():
    html = make_html("https://youtu.be/L_Guz73e6fw?t=5300")
    assert 'iframe' in html and 'L_Guz73e6fw' in html and '5300' not in html

def test_youtube2():
    html = make_html("https://www.youtube.com/watch?v=s_NcZl5bi38&t=132s")
    assert 'iframe' in html and 's_NcZl5bi38' in html and '132' not in html

def test_youtube_no_pwn():
    html = make_html("https://www.youtube.com/watch?v=<script>")
    assert not '<script>' in html

def test_quote():
    html = make_html("> citation")
    assert '<blockquote>' in html and 'citation' in html

def test_pre():
    html = make_html("    print('Hello world')")
    assert '<pre>' in html and "print('Hello world')" in html

def check_username(src):
    html = make_html(src)
    assert '<a class="username" href="/u/finder"><img src="/static/silver.png">finder</a>' in html

def test_usernames():
    check_username('/u/finder')
    check_username('(/u/finder)')
    check_username('а также /u/finder и др.')
    check_username('Привет.\n/u/finder как-то сказал')
    html = make_html('https://reddit.com/u/finder')
    assert not 'silver.png' in html

def test_wikilinks():
    html = make_html('[[Москва]], [[London]]')
    expected = r'<a href="https://ru.wikipedia.org/wiki/%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0">Москва</a>, <a href="https://en.wikipedia.org/wiki/London">London</a>'
    assert expected in html

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
    assert '<div class="codehilite"><pre><code>' in html
    assert '<span class="kn">import</span>' in html

def test_spoilers():
    html = make_html('%%spoiler text%%')
    assert '<span class="spoiler"' in html and 'spoiler text' in html

    html = make_html('some of the text is %%a spoiler%%')
    assert '<span class="spoiler"' in html and 'a spoiler' in html and 'some of the text is' in html

def test_tags():
    text = 'Вот несколько тэгов: #math, #boobs, и еще раз #math'
    html = make_html(text)
    assert '<a href="/tag/math"> #math</a>' in html
    assert '<a href="/tag/boobs"> #boobs</a>' in html
    tags = collect_tags(text)
    assert len(tags) == 2
    assert "math" in tags
    assert "boobs" in tags

def test_url_with_anchor():
    text = "https://en.wikipedia.org/wiki/List_of_accidents_and_disasters_by_death_toll#Space"
    html = make_html(text)
    assert "<a " in html
    assert "tag" not in html
    assert text in html
