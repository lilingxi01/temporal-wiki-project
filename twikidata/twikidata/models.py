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
    def __init__(self, revision_text, timestamp, root_timestamp):
        self.timestamp = get_timestamp(timestamp) - root_timestamp
        self.raw_text = text_parser(revision_text)


class HistoryBase:
    """This class is for holding the instance of a wiki page."""
    def __init__(self, title):
        self.title = title
        self.revisions = []
        self.root_timestamp = None
        self.ergodiff = Ergodiff()
        self.id = None

    def set_id(self, id: str):
        self.id = id

    def add_revision(self, revision_text, timestamp):
        if len(self.revisions) == 0:
            self.root_timestamp = get_timestamp(timestamp)
        self.revisions.append(HistoryEntry(revision_text, timestamp, self.root_timestamp))

    def get_change_lists(self):
        old_sentences = None
        changes = []
        added_lines = []
        prev_text = self.revisions[0].raw_text
        for revision in self.revisions[1:]:
            if revision.raw_text is None:
                # print('[Skip] Empty revision:', revision)
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
            'children count': len(self.revisions),
        }, indent=4)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.revisions[item]
