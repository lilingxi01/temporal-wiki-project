from difflib import Differ
from .preprocess import preprocess_str_to_pool


class HistoryDiff:
    def __init__(self, old_text, new_text):
        self.differ = Differ()

        self.old_pool = preprocess_str_to_pool(old_text)
        self.new_pool = preprocess_str_to_pool(new_text)

        self.diff = self.differ.compare(self.old_pool, self.new_pool)

    def __str__(self):
        return '\n'.join(list(self.diff))
