import re

# These tags are most possibly self-closing. We need to drop them in the process.
self_closing_tags = ('br', 'hr', 'nobr', 'ref', 'references', 'nowiki')

# These tags are least important in the article (for current understanding).
minor_tags = (
    'abbr', 'b', 'big', 'blockquote', 'center', 'cite', 'div', 'em',
            'font', 'h1', 'h2', 'h3', 'h4', 'hiero', 'i', 'kbd', 'nowiki',
            'p', 'plaintext', 's', 'span', 'strike', 'strong',
            'sub', 'sup', 'tt', 'u', 'var'
)

placeholder_tags = {'math': 'formula', 'code': 'codice'}


def compile_ignore_tag_regex(tag):
    left = re.compile(r'<%s\b.*?>' % tag, re.IGNORECASE | re.DOTALL)  # both <ref> and <reference>
    right = re.compile(r'</\s*%s>' % tag, re.IGNORECASE)
    return (left, right)


# Regex for ignoring tags.
ignored_tags_regex = [compile_ignore_tag_regex(tag) for tag in minor_tags]

# Regex for self closing tags.
self_closing_tags_regex = [
    re.compile(r'<\s*%s\b[^>]*/\s*>' % tag, re.DOTALL | re.IGNORECASE) for tag in self_closing_tags
]

# Regex for placeholder tags.
placeholder_tags_regex = [
    (re.compile(r'<\s*%s(\s*| [^>]+?)>.*?<\s*/\s*%s\s*>' % (tag, tag), re.DOTALL | re.IGNORECASE), repl)
    for tag, repl in placeholder_tags.items()
]
