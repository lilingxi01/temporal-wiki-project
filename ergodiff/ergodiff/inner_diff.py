from difflib import SequenceMatcher
from typing import List


def inner_diff_preprocess(sentence: str) -> List[str]:
    # TODO: Might want to use regex to split by any amount of continuous spaces?
    output = sentence.rstrip('\n').split()
    while '' in output:
        output.remove('')
    return output


def process_inner_diff(old_sentence: str, new_sentence: str):
    old_words = inner_diff_preprocess(old_sentence)
    new_words = inner_diff_preprocess(new_sentence)
    seq_matcher = SequenceMatcher(None, old_words, new_words)
    opcodes = seq_matcher.get_opcodes()

    curr_index = 0

    # For the format of items of changes, check Notion documentation.
    # Basically they are tuples in this format: `(starting_index, old_text, new_text)`.
    changes = []

    for opcode in opcodes:
        tag, i1, i2, j1, j2 = opcode
        old_text = ' '.join(old_words[i1:i2])
        new_text = ' '.join(new_words[j1:j2])
        if tag != 'equal':
            changes.append((curr_index, old_text, new_text))
        curr_index += len(old_text) + 1 if old_text != '' else 0

    return changes
