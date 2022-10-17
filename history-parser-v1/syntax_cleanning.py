import re
import html
from magicwords import MagicWords
from urllib.parse import quote as urlencode
from html.entities import name2codepoint


# match tail after wikilink
tailRE = re.compile('\w+')  # TODO: I still cannot understand what it really did here.
syntaxhighlight = re.compile('&lt;syntaxhighlight .*?&gt;(.*?)&lt;/syntaxhighlight&gt;', re.DOTALL)

##
# Defined in <siteinfo>
# We include as default Template, when loading external template file.
# For now, I do not know the purpose of template here.
known_namespaces = set(['Template'])

##
# Drop these elements from article text
#
dropped_html_elements = [
    'gallery', 'timeline', 'noinclude', 'pre',
    'table', 'tr', 'td', 'th', 'caption', 'div',
    'form', 'input', 'select', 'option', 'textarea',
    'ul', 'li', 'ol', 'dl', 'dt', 'dd', 'menu', 'dir',
    'ref', 'references', 'img', 'imagemap', 'source', 'small'
]

##
# Recognize only these namespaces
# w: Internal links to the Wikipedia
# wiktionary: Wiki dictionary
# wikt: shortcut for Wiktionary
#
accepted_namespaces = ['w', 'wiktionary', 'wikt']


def clean_syntax(text, expand_templates=False, should_keep_link=True, html_safe=True):
    """
    Transforms wiki markup. If the command line flag --escapedoc is set then the text is also escaped
    @see https://www.mediawiki.org/wiki/Help:Formatting
    :param extractor: the Extractor t use.
    :param text: the text to clean.
    :param expand_templates: whether to perform template expansion.
    :param html_safe: whether to convert reserved HTML characters to entities.
    @return: the cleaned text.
    """

    # Drop transclusions (template, parser functions)
    text = drop_nested(text, r'{{', r'}}')

    # Drop tables
    text = drop_nested(text, r'{\|', r'\|}')

    # replace external links
    text = replace_external_links(text, should_keep_link=should_keep_link)

    # replace internal links
    text = replace_internal_links(text, should_keep_link=should_keep_link)

    # drop MagicWords behavioral switches
    text = MagicWords.regex.sub('', text)

    # ############### Process HTML ###############

    # turn into HTML, except for the content of <syntaxhighlight>
    res = ''
    cur = 0
    for m in syntaxhighlight.finditer(text):
        end = m.end()
        res += unescape(text[cur:m.start()]) + m.group(1)
        cur = end
    text = res + unescape(text[cur:])

    # Handle bold/italic/quote
    text = bold_italic.sub(r'<b>\1</b>', text)
    text = bold.sub(r'<b>\1</b>', text)
    text = italic.sub(r'<i>\1</i>', text)

    # residuals of unbalanced quotes
    text = text.replace("'''", '').replace("''", '"')

    # Collect spans

    spans = []
    # Drop HTML comments
    for m in comment.finditer(text):
        spans.append((m.start(), m.end()))

    # Drop self-closing tags
    for pattern in selfClosing_tag_patterns:
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))

    # Drop ignored tags
    for left, right in ignored_tag_patterns:
        for m in left.finditer(text):
            spans.append((m.start(), m.end()))
        for m in right.finditer(text):
            spans.append((m.start(), m.end()))

    # Bulk remove all spans
    text = drop_spans(spans, text)

    # Drop discarded elements
    for tag in dropped_html_elements:
        text = drop_nested(text, r'<\s*%s\b[^>/]*>' % tag, r'<\s*/\s*%s>' % tag)

    # Turn into text what is left (&amp;nbsp;) and <syntaxhighlight>
    # TODO: Might not need it.
    text = unescape(text)

    # Expand placeholders
    for pattern, placeholder in placeholder_tag_patterns:
        index = 1
        for match in pattern.finditer(text):
            text = text.replace(match.group(), '%s_%d' % (placeholder, index))
            index += 1

    text = text.replace('<<', u'«').replace('>>', u'»')

    #############################################

    # Cleanup text
    text = text.replace('\t', ' ')
    text = spaces.sub(' ', text)
    text = dots.sub('...', text)
    text = re.sub(u' (,:\.\)\]»)', r'\1', text)
    text = re.sub(u'(\[\(«) ', r'\1', text)
    text = re.sub(r'\n\W+?\n', '\n', text, flags=re.U)  # lines with only punctuations
    text = text.replace(',,', ',').replace(',.', '.')
    if html_safe:
        text = html.escape(text, quote=False)
    return text


# ----------------------------------------------------------------------

# These tags are most possibly self-closing. We need to drop them in the process.
possible_self_closing_tags = ('br', 'hr', 'nobr', 'ref', 'references', 'nowiki')

# These tags are dropped, keeping their content.
# handle 'a' separately, depending on keepLinks
ignored_tags = (
    'abbr', 'b', 'big', 'blockquote', 'center', 'cite', 'div', 'em',
            'font', 'h1', 'h2', 'h3', 'h4', 'hiero', 'i', 'kbd', 'nowiki',
            'p', 'plaintext', 's', 'span', 'strike', 'strong',
            'sub', 'sup', 'tt', 'u', 'var'
)

placeholder_tags = {'math': 'formula', 'code': 'codice'}


def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.

    :param text The HTML (or XML) source text.
    :return The plain text, as a Unicode string, if necessary.
    """

    def fixup(m):
        text = m.group(0)
        code = m.group(1)
        try:
            if text[1] == "#":  # character reference
                if text[2] == "x":
                    return chr(int(code[1:], 16))
                else:
                    return chr(int(code))
            else:  # named entity
                return chr(name2codepoint[code])
        except:
            return text  # leave as is

    return re.sub("&#?(\w+);", fixup, text)


# Match HTML comments
# The buggy template {{Template:T}} has a comment terminating with just "->"
comment = re.compile(r'<!--.*?-->', re.DOTALL)

# Match ignored tags.
# For now, this part is hardcoded alongside this file.
# TODO: I am thinking if I should divide this part into a separate file.
ignored_tag_patterns = []


# TODO: Migration into dedicated files.
def ignore_tag(tag):
    left = re.compile(r'<%s\b.*?>' % tag, re.IGNORECASE | re.DOTALL)  # both <ref> and <reference>
    right = re.compile(r'</\s*%s>' % tag, re.IGNORECASE)
    ignored_tag_patterns.append((left, right))


# TODO: Migration into dedicated files.
for tag in ignored_tags:
    ignore_tag(tag)

# Match selfClosing HTML tags
selfClosing_tag_patterns = [
    re.compile(r'<\s*%s\b[^>]*/\s*>' % tag, re.DOTALL | re.IGNORECASE) for tag in possible_self_closing_tags
]

# Match HTML placeholder tags
placeholder_tag_patterns = [
    (re.compile(r'<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag), re.DOTALL | re.IGNORECASE),
            repl) for tag, repl in placeholder_tags.items()
]

# Match preformatted lines
preformatted = re.compile(r'^ .*?$')

# Match external links (space separates second optional parameter)
externalLink = re.compile(r'\[\w+[^ ]*? (.*?)]')
externalLinkNoAnchor = re.compile(r'\[\w+[&\]]*\]')

# Matches bold/italic
bold_italic = re.compile(r"'''''(.*?)'''''")
bold = re.compile(r"'''(.*?)'''")
italic_quote = re.compile(r"''\"([^\"]*?)\"''")
italic = re.compile(r"''(.*?)''")
quote_quote = re.compile(r'""([^"]*?)""')

# Matches space
spaces = re.compile(r' {2,}')

# Matches dots
dots = re.compile(r'\.{4,}')


# ----------------------------------------------------------------------

def drop_nested(text, open_delim, close_delim):
    """
    A matching function for nested expressions, e.g. namespaces and tables.
    """
    open_re = re.compile(open_delim, re.IGNORECASE)
    close_re = re.compile(close_delim, re.IGNORECASE)
    # partition text in separate blocks { } { }
    spans = []  # pairs (s, e) for each partition
    nest = 0  # nesting level
    start = open_re.search(text, 0)
    if not start:
        return text
    end = close_re.search(text, start.end())
    next = start
    while end:
        next = open_re.search(text, next.end())
        if not next:  # termination
            while nest:  # close all pending
                nest -= 1
                end0 = close_re.search(text, end.end())
                if end0:
                    end = end0
                else:
                    break
            spans.append((start.start(), end.end()))
            break
        while end.end() < next.start():
            # { } {
            if nest:
                nest -= 1
                # try closing more
                last = end.end()
                end = close_re.search(text, end.end())
                if not end:  # unbalanced
                    if spans:
                        span = (spans[0][0], last)
                    else:
                        span = (start.start(), last)
                    spans = [span]
                    break
            else:
                spans.append((start.start(), end.end()))
                # advance start, find next close
                start = next
                end = close_re.search(text, next.end())
                break  # { }
        if next != start:
            # { { }
            nest += 1
    # collect text outside partitions
    return drop_spans(spans, text)


def drop_spans(spans, text):
    """
    Drop from text the blocks identified in :param spans:, possibly nested.
    """
    spans.sort()
    res = ''
    offset = 0
    for s, e in spans:
        if offset <= s:  # handle nesting
            if offset < s:
                res += text[offset:s]
            offset = e
    res += text[offset:]
    return res


# ----------------------------------------------------------------------
# External links

# from: https://doc.wikimedia.org/mediawiki-core/master/php/DefaultSettings_8php_source.html

wgUrlProtocols = [
    'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
    'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
    'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
    'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:', '//'
]

# from: https://doc.wikimedia.org/mediawiki-core/master/php/Parser_8php_source.html

# Constants needed for external link processing
# Everything except bracket, space, or control characters
# \p{Zs} is unicode 'separator, space' category. It covers the space 0x20
# as well as U+3000 is IDEOGRAPHIC SPACE for bug 19052
EXT_LINK_URL_CLASS = r'[^][<>"\x00-\x20\x7F\s]'
ExtLinkBracketedRegex = re.compile(
    '\[(((?i)' + '|'.join(wgUrlProtocols) + ')' + EXT_LINK_URL_CLASS + r'+)\s*([^\]\x00-\x08\x0a-\x1F]*?)\]',
    re.S | re.U)
EXT_IMAGE_REGEX = re.compile(
    r"""^(http://|https://)([^][<>"\x00-\x20\x7F\s]+)
    /([A-Za-z0-9_.,~%\-+&;#*?!=()@\x80-\xFF]+)\.((?i)gif|png|jpg|jpeg)$""",
    re.X | re.S | re.U)


def replace_external_links(text, should_keep_link=True):
    s = ''
    cur = 0
    for m in ExtLinkBracketedRegex.finditer(text):
        s += text[cur:m.start()]
        cur = m.end()

        url = m.group(1)
        label = m.group(3)

        # # The characters '<' and '>' (which were escaped by
        # # removeHTMLtags()) should not be included in
        # # URLs, per RFC 2396.
        # m2 = re.search('&(lt|gt);', url)
        # if m2:
        #     link = url[m2.end():] + ' ' + link
        #     url = url[0:m2.end()]

        # If the link text is an image URL, replace it with an <img> tag
        # This happened by accident in the original parser, but some people used it extensively
        m = EXT_IMAGE_REGEX.match(label)
        if m:
            label = make_external_image(label, should_keep_src=should_keep_link)

        # Use the encoded URL
        # This means that users can paste URLs directly into the text
        # Funny characters like ö aren't valid in URLs anyway
        # This was changed in August 2004
        s += make_external_link(url, label, should_keep_href=should_keep_link)  # + trail

    return s + text[cur:]


def make_external_link(url, anchor, should_keep_href=True):
    """Function applied to wikiLinks"""
    if should_keep_href:
        return f'<a href="{urlencode(url)}">{anchor}</a>'
    else:
        return anchor


def make_external_image(url, alt='', should_keep_src=True):
    if should_keep_src:
        return f'<img src="{url}" alt="{alt}">'
    else:
        return alt


# ----------------------------------------------------------------------
# WikiLinks
# See https://www.mediawiki.org/wiki/Help:Links#Internal_links

# Can be nested [[File:..|..[[..]]..|..]], [[Category:...]], etc.
# Also: [[Help:IPA for Catalan|[andora]]]


def replace_internal_links(text, should_keep_link=True):
    """
    Replaces external links of the form:
    [[title |...|label]]trail

    with title concatenated with trail, when present, e.g. 's' for plural.
    """
    # call this after removal of external links, so we need not worry about
    # triple closing ]]].
    cur = 0
    res = ''
    # `s` is the starting point, and `e` is the ending point.
    for s, e in find_balanced_pairs(text, ['[['], [']]']):
        m = tailRE.match(text, e)
        if m:
            print('>>>>> m:', m)
            trail = m.group(0)
            end = m.end()
        else:
            trail = ''
            end = e
        inner = text[s + 2:e - 2]
        # find first |
        pipe = inner.find('|')
        if pipe < 0:
            title = inner
            label = title
        else:
            title = inner[:pipe].rstrip()
            # find last |
            curp = pipe + 1
            for s1, e1 in find_balanced_pairs(inner, ['[['], [']]']):
                last = inner.rfind('|', curp, s1)
                if last >= 0:
                    pipe = last  # advance
                curp = e1
            label = inner[pipe + 1:].strip()
        res += text[cur:s] + make_internal_link(title, label, should_keep_href=should_keep_link) + trail
        cur = end
    return res + text[cur:]


def make_internal_link(title, label, should_keep_href=True):
    colon = title.find(':')
    if colon > 0 and title[:colon] not in accepted_namespaces:
        return ''
    if colon == 0:
        # drop also :File:
        colon2 = title.find(':', colon + 1)
        if colon2 > 1 and title[colon + 1:colon2] not in accepted_namespaces:
            return ''
    if should_keep_href:
        return f'<a href="{urlencode(title)}">{label}</a>'
    else:
        return label


# ----------------------------------------------------------------------
# parser functions utilities


def find_balanced_pairs(text, open_delim, close_delim):
    """
    You can use this function to find out all these pairs.
    Assuming that text contains a properly balanced expression pairs.
    :param text: The text to be searched.
    :param open_delim: Opening delimiters.
    :param close_delim: Closing delimiters.
    :return: An iterator producing pairs (start, end) of start and end
    positions in text containing a balanced expression.
    """
    # TODO: organize.
    openPat = '|'.join([re.escape(x) for x in open_delim])
    # patter for delimiters expected after each opening delimiter
    afterPat = {o: re.compile(openPat + '|' + c, re.DOTALL) for o, c in zip(open_delim, close_delim)}
    stack = []
    start = 0
    cur = 0
    # end = len(text)
    startSet = False
    startPat = re.compile(openPat)
    nextPat = startPat
    while True:
        next = nextPat.search(text, cur)
        if not next:
            return
        if not startSet:
            start = next.start()
            startSet = True
        delim = next.group(0)
        if delim in open_delim:
            stack.append(delim)
            nextPat = afterPat[delim]
        else:
            opening = stack.pop()
            # assert opening == openDelim[closeDelim.index(next.group(0))]
            if stack:
                nextPat = afterPat[stack[-1]]
            else:
                yield start, next.end()
                nextPat = startPat
                start = next.end()
                startSet = False
        cur = next.end()


def ucfirst(string):
    """:return: a string with just its first character uppercase."""
    # No need to handle the edge cases here. Python handles them all.
    return string[0].upper() + string[1:] if string else ''


def lcfirst(string):
    """:return: a string with its first character lowercase."""
    return string[0].lower() + string[1:] if string else ''


def normalize_namespace(ns):
    return ucfirst(ns)
