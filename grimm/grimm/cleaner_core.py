import re
import html
from urllib.parse import quote as urlencode
from html.entities import name2codepoint

from .support.magicwords import MagicWords
from .support.tags import ignored_tags_regex, self_closing_tags_regex, placeholder_tags_regex


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


def clean_syntax(text, html_safe=True):
    """
    Transforms wiki markup. If the command line flag --escapedoc is set then the text is also escaped
    @see https://www.mediawiki.org/wiki/Help:Formatting
    :param text: the text to clean.
    :param html_safe: whether to convert reserved HTML characters to entities.
    @return: the cleaned text.
    """

    # Drop transclusions (template, parser functions)
    text = drop_nested(text, r'{{', r'}}')

    # Drop tables
    text = drop_nested(text, r'{\|', r'\|}')

    # replace external links
    text, external_links, images = parse_external_links(text)

    # replace internal links
    text, internal_links, drifts = parse_internal_links(text)

    external_links = drift_adjust(external_links, drifts)
    images = drift_adjust(images, drifts)

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
    for pattern in self_closing_tags_regex:
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end()))

    # Drop ignored tags
    for left, right in ignored_tags_regex:
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
    for pattern, placeholder in placeholder_tags_regex:
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

    return text, external_links, internal_links, images


# ----------------------------------------------------------------------


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
    # I do not really know the purpose of this function for now.


# Match HTML comments
# The buggy template {{Template:T}} has a comment terminating with just "->"
comment = re.compile(r'<!--.*?-->', re.DOTALL)

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

# Match the tail of an internal link.
# Check here: https://www.mediawiki.org/wiki/Help:Links#Internal_links
internal_link_tail_re = re.compile('\w+')


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

# This protocol is coming from https://www.mediawiki.org/wiki/Manual:$wgUrlProtocols
wiki_url_protocols = [
    'bitcoin:', 'ftp://', 'ftps://', 'geo:', 'git://', 'gopher://', 'http://',
    'https://', 'irc://', 'ircs://', 'magnet:', 'mailto:', 'mms://', 'news:',
    'nntp://', 'redis://', 'sftp://', 'sip:', 'sips:', 'sms:', 'ssh://',
    'svn://', 'tel:', 'telnet://', 'urn:', 'worldwind://', 'xmpp:', '//'
]

# Constants needed for external link processing
# Everything except bracket, space, or control characters
# \p{Zs} is unicode 'separator, space' category. It covers the space 0x20
# as well as U+3000 is IDEOGRAPHIC SPACE for bug 19052
external_link_url_class = r'[^][<>"\x00-\x20\x7F\s]'
external_link_regex = re.compile(
    '\[(((?i)' + '|'.join(wiki_url_protocols) + ')' + external_link_url_class + r'+)\s*([^\]\x00-\x08\x0a-\x1F]*?)\]',
    re.S | re.U)
external_image_regex = re.compile(
    r"""^(http://|https://)([^][<>"\x00-\x20\x7F\s]+)
    /([A-Za-z0-9_.,~%\-+&;#*?!=()@\x80-\xFF]+)\.((?i)gif|png|jpg|jpeg)$""",
    re.X | re.S | re.U)


def parse_external_links(text):
    result = ''
    links = []
    images = []

    cur = 0
    for m in external_link_regex.finditer(text):
        # Append the text between last find and this find.
        result += text[cur:m.start()]

        # Update cursor.
        cur = m.end()

        url = m.group(1)
        label = m.group(3)

        # Current position of result string.
        curr_pos = len(result)

        # Only add label to the final text.
        result += label

        # TODO: We might need to parse the image more carefully.
        # Based on the definition here - https://www.mediawiki.org/wiki/Help:Images
        # Images have url, type, and caption(alt).
        # Current regex seems not parse them correctly.
        m = external_image_regex.match(label)
        if m:
            images.append((curr_pos, curr_pos + len(label), url))
        else:
            links.append((curr_pos, curr_pos + len(label), url))

    return result + text[cur:], links, images


# ----------------------------------------------------------------------
# WikiLinks
# See https://www.mediawiki.org/wiki/Help:Links#Internal_links

# Can be nested [[File:..|..[[..]]..|..]], [[Category:...]], etc.
# Also: [[Help:IPA for Catalan|[andora]]]


def parse_internal_links(text):
    """
    Replaces external links of the form:
    [[title |...|label]]trail

    with title concatenated with trail, when present, e.g. 's' for plural.
    """
    # call this after removal of external links, so we need not worry about
    # triple closing ]]].

    result = ''
    links = []
    drifts = []

    cur = 0

    # `s` is the starting point, and `e` is the ending point.
    for s, e in find_balanced_pairs(text, ['[['], [']]']):
        m = internal_link_tail_re.match(text, e)
        if m:
            trail = m.group(0)
            end = m.end()
        else:
            trail = ''
            end = e

        # Inner content (got rid of `[[` and `]]`)
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
        result += text[cur:s]

        # Get current position of result string.
        curr_pos = len(result)

        # Compute label based on its title and its trail.
        label = make_internal_link(title, label)

        # Add links.
        links.append((curr_pos, curr_pos + len(label), urlencode(title)))

        # Compute the drift effect.
        drift = len(label) - len(text[s:e])
        drifts.append((e, drift))

        # Finally append the label.
        result += label + trail

        # Forward the cursor.
        cur = end

    return result + text[cur:], links, drifts


def make_internal_link(title, label) -> str:
    colon_0 = title.find(':')
    if colon_0 > 0 and title[:colon_0] not in accepted_namespaces:
        return ''
    if colon_0 == 0:
        # Also drop cases like ":File:"
        colon_1 = title.find(':', colon_0 + 1)
        if colon_1 > 1 and title[colon_0 + 1:colon_1] not in accepted_namespaces:
            return ''
    return label


def drift_adjust(links: list, drifts: list):
    prev_drift_sum = 0
    adjusted_links = []

    # This algorithm is really fast.
    # Only O(m+n) running time where m is len(links) and n is len(drifts).

    for drift_index, drift_amount in drifts:
        while links and links[0][0] < drift_index:
            start_pos, end_pos, content = links.pop(0)
            adjusted_links.append((start_pos + prev_drift_sum, end_pos + prev_drift_sum, content))

        prev_drift_sum += drift_amount

    # Process remaining links.
    for link in links:
        start_pos, end_pos, content = link
        adjusted_links.append((start_pos + prev_drift_sum, end_pos + prev_drift_sum, content))

    return adjusted_links


# ----------------------------------------------------------------------
# parser functions utilities


# TODO: Organize this function.
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
