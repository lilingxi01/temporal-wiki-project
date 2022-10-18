import json
from datetime import datetime
from syntax_cleanning import clean_syntax


def text_parser(raw_text):
    """Parse the wiki raw text into designated form."""
    return clean_syntax(raw_text)


def get_timestamp(iso):
    return round(datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp())


class HistoryEntry:
    """This class is for storing the atom change history of a page."""
    def __init__(self, revision, root_timestamp):
        self.timestamp = get_timestamp(revision['timestamp']) - root_timestamp
        if '#text' in revision['text']:
            self.raw_text = text_parser(revision['text']['#text'])


class HistoryBase:
    """This class is for holding the instance of a wiki page."""
    def __init__(self, page):
        self.title = page['title']
        self.id = page['id']
        self.children = []
        if type(page['revision']) is list:
            self.root_timestamp = get_timestamp(page['revision'][0]['timestamp'])
            for revision in page['revision']:
                self.children.append(HistoryEntry(revision, self.root_timestamp))
        else:
            self.root_timestamp = get_timestamp(page['revision']['timestamp'])
            self.children.append(HistoryEntry(page['revision'], self.root_timestamp))

    def __str__(self):
        return json.dumps({
            'title': self.title,
            'id': self.id,
            'children count': len(self.children),
        }, indent=4)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.children[item]
