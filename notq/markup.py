import re
import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
from html_sanitizer import Sanitizer
from notq.markdown_urlize import UrlizeExtension
from notq.markdown_spoilers import SpoilerExtension

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

usernamere = re.compile(r"[^a-zA-Z0-9]/u/(?P<name>[a-zA-Z0-9-]+)")
def resolveUsernames(html):
    return usernamere.sub(r'<a class="username" href="/u/\g<name>"><img src="/static/silver.png">\g<name></a>', html)

youtubere = re.compile(r"<p>(\s)*https://(youtu.be/|www.youtube.com/watch\?v=)(?P<id>[0-9a-zA-Z_]+)(\S)*(\s)*</p>")
def resolveYoutubeEmbeds(html):
    return youtubere.sub(r'<iframe class="youtube" width="560" src="https://www.youtube.com/embed/\g<id>" frameborder="0" allowfullscreen></iframe>', html)

def ruenwiki_link_builder(label, base, end):
    if re.search('[а-яА-Я]', label):
        return "https://ru.wikipedia.org/wiki/" + label
    else:
        return "https://en.wikipedia.org/wiki/" + label

def make_html(text, do_embeds = True):
    html = markdown.markdown(text, extensions=[
        WikiLinkExtension(build_url=ruenwiki_link_builder),
        UrlizeExtension(),
        SpoilerExtension(),
        'codehilite',
    ])
    html = sanitizeHtml(html)
    html = resolveUsernames(html)
    if do_embeds:
        html = resolveYoutubeEmbeds(html)
    return html
