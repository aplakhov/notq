import re
import markdown
import xml.etree.ElementTree as etree

class SimpleTagPattern(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        tagname = m.group(2)
        el = etree.Element('a')
        el.set('href', f'/tag/{tagname}')
        el.text = " #" + tagname
        return el

SIMPLE_TAG_REGEXP = r'[ ,]#([A-Za-z0-9]+)'

class SimpleTagExtension(markdown.Extension):
    """ SimpleTag Extension for Python-Markdown. """

    def extendMarkdown(self, md):
        md.inlinePatterns.register(SimpleTagPattern(SIMPLE_TAG_REGEXP, md), 'simpletag', 175)

def collect_tags(text):
    return set(re.findall(SIMPLE_TAG_REGEXP, text))
