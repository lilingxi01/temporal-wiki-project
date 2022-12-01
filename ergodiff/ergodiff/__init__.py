from difflib import Differ

from .preprocess import preprocess_str_to_pool
from .outer_diff import process_outer_diff
from .inner_diff import process_inner_diff
from .reconstruct import auto_reconstruct, progressive_reconstruct


class Ergodiff:
    def __init__(self):
        self.differ = Differ()

    def get_diff(self, old_text: str, new_text: str):
        diff_result = self.differ.compare(preprocess_str_to_pool(old_text), preprocess_str_to_pool(new_text))
        old_sentences, changes, added_lines = process_outer_diff(diff_result)
        return old_sentences, changes, added_lines

    def get_sentence_diff(self, old_sentence: str, new_sentence: str):
        return process_inner_diff(old_sentence, new_sentence)
