import markdown
import xml.etree.ElementTree as etree

class SpoilerPattern(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        el = etree.Element('span')
        el.set('class', 'spoiler')
        el.text = m.group(2)
        return el

class SpoilerExtension(markdown.Extension):
    """ Spoiler Extension for Python-Markdown. """

    def extendMarkdown(self, md):
        md.inlinePatterns.register(SpoilerPattern(r'%%([^%]+)%%', md), 'spoiler', 175)
