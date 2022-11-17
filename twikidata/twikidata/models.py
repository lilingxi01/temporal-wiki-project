import json
from datetime import datetime

from ergodiff import Ergodiff
from grimm import clean_syntax


def text_parser(raw_text):
    """Parse the wiki raw text into designated form."""
    text, external_links, internal_links, images = clean_syntax(raw_text)
    return text


def get_timestamp(iso):
    return round(datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp())


class HistoryEntry:
    """This class is for storing the atom change history of a page."""
    def __init__(self, revision, root_timestamp):
        self.timestamp = get_timestamp(revision['timestamp']) - root_timestamp
        if '#text' in revision['text']:
            self.raw_text = text_parser(revision['text']['#text'])
        else:
            self.raw_text = None


class HistoryBase:
    """This class is for holding the instance of a wiki page."""
    def __init__(self, page):
        self.title = page['title']
        self.id = page['id']
        self.children = []
        self.ergodiff = Ergodiff()
        if type(page['revision']) is list:
            self.root_timestamp = get_timestamp(page['revision'][0]['timestamp'])
            for revision in page['revision']:
                self.children.append(HistoryEntry(revision, self.root_timestamp))
        else:
            self.root_timestamp = get_timestamp(page['revision']['timestamp'])
            self.children.append(HistoryEntry(page['revision'], self.root_timestamp))

    def get_change_lists(self):
        old_sentences = None
        changes = []
        added_lines = []
        prev_text = self.children[0].raw_text
        for revision in self.children[1:]:
            if revision.raw_text is None:
                print('[Skip] Empty revision:', revision)
                continue
            text = revision.raw_text
            curr_sentences, curr_changes, curr_added_lines = self.ergodiff.get_diff(prev_text, text)

            if old_sentences is None:
                old_sentences = curr_sentences
            changes.append(curr_changes)
            added_lines.append(curr_added_lines)
            prev_text = text
        return old_sentences, changes, added_lines

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
