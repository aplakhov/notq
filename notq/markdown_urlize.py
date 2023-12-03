import markdown
import xml.etree.ElementTree as etree

# Global Vars
URLIZE_RE = '(%s)' % '|'.join([
    r'<https?://[^>]*>',
    r'(?:^|[( ,\n])https?://[^)<>\s]+[^.,)<>\s]',
    r'(?:^|[( ,\n])www\.[^)<>\s]+[^.,)<>\s]',
    r'(?:^|[( ,\n])[^(<\s"]+\.(?:com|net|org|ru)\b',
])

class UrlizePattern(markdown.inlinepatterns.Pattern):
    """ Return a link Element given an autolink (`http://example/com`). """
    def handleMatch(self, m):
        url = m.group(2)
        
        if url.startswith('<'):
            url = url[1:-1]
            
        text = url

        if 'youtube.com/watch' in url or 'youtu.be' in url:
            return None # we want to deal with youtube links in a different way

        if not url.split('://')[0] in ('http','https'):
            if '@' in url and not '/' in url:
                return None
            else:
                url = 'http://' + url
    
        el = etree.Element("a")
        el.set('href', url)
        el.text = text
        return el

class UrlizeExtension(markdown.Extension):
    """ Urlize Extension for Python-Markdown. """

    def extendMarkdown(self, md):
        """ Replace autolink with UrlizePattern """
        md.inlinePatterns.register(UrlizePattern(URLIZE_RE, md), 'autolink', 175)

def makeExtension(*args, **kwargs):
    return UrlizeExtension(*args, **kwargs)
