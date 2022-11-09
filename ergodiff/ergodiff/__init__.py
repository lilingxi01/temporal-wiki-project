from difflib import Differ
from .preprocess import preprocess_str_to_pool
from .postprocess import diff_postprocess


class Ergodiff:
    def __init__(self):
        self.differ = Differ()

    def get_diff(self, old_text, new_text):
        diff_result = self.differ.compare(preprocess_str_to_pool(old_text), preprocess_str_to_pool(new_text))
        old_sentences, changes, added_lines = diff_postprocess(diff_result)
        return old_sentences, changes, added_lines
