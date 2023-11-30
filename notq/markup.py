import re
import markdown
from html_sanitizer import Sanitizer

sanitizerConfig = {
    "tags": {
        "a", "h1", "h2", "h3", "strong", "em", "p", "ul", "ol",
        "li", "br", "sub", "sup", "hr", "blockquote", "pre"
    },
    "attributes": {"a": ("href",)},
    "empty": {"hr", "a", "br"},
    "separate": {"a", "p", "li"},
    "whitespace": {"br"},
    "keep_typographic_whitespace": True,
}

def sanitizeHtml(value):
    sanitizer = Sanitizer(sanitizerConfig)
    return sanitizer.sanitize(value)

youtubere = re.compile(r"<p>(\s)*https://(youtu.be/|www.youtube.com/watch\?v=)(?P<id>(\S)*)(\s)*</p>")
def resolveYoutubeEmbeds(html):
    return youtubere.sub(r'<iframe class="youtube" width="560" src="https://www.youtube.com/embed/\g<id>" frameborder="0" allowfullscreen></iframe>', html)

def make_html(text, do_embeds = True):
    html = markdown.markdown(text, )
    html = sanitizeHtml(html)
    if do_embeds:
        html = resolveYoutubeEmbeds(html)
    return html
