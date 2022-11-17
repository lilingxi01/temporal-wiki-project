from difflib import Differ
from typing import List


def inner_diff_preprocess(sentence: str) -> List[str]:
    # TODO: Might want to use regex to split by any amount of continuous spaces?
    output = sentence.rstrip('\n').split()
    while '' in output:
        output.remove('')
    return output


def process_inner_diff(old_sentence: str, new_sentence: str, differ: Differ):
    diff = differ.compare(inner_diff_preprocess(old_sentence), inner_diff_preprocess(new_sentence))

    curr_index = 0

    # For the format of items of changes, check Notion documentation.
    # Basically they are tuples in this format: `(starting_index, old_text, new_text)`.
    changes = []

    # Pending row is ONLY for keeping the information and waiting for '?'.
    # It does not wait for next '-' or '+', as `edit_context` variable did this work.
    pending_word = None

    # Only '+' and '-' will have pending behavior. So potential values are None, '-', or '+'.
    pending_change_type = None

    for row in diff:
        if not len(row):
            continue

        change_type = row[0]
        content = row[2:]

        consumed_by_previous_row = False

        if change_type == '?':
            continue

        if pending_word and pending_change_type:
            # Cleanup and archive pending information.
            if pending_change_type == '+':
                changes.append((curr_index, '', pending_word))
            else:
                if change_type == '+':
                    changes.append((curr_index, pending_word, content))
                    consumed_by_previous_row = True
                else:
                    changes.append((curr_index, pending_word, ''))
                curr_index += len(pending_word) + 1
            pending_word = None
            pending_change_type = None

        if consumed_by_previous_row:
            continue

        if change_type == ' ':
            # Do nothing for un-changed word.
            curr_index += len(content) + 1
            pass
        elif change_type in ['+', '-']:
            # We will wait for '?' in this case.
            pending_word = content
            pending_change_type = change_type

    # Finalize the parsing if there are any pending change left.
    if pending_word and pending_change_type == '+':
        changes.append((curr_index, '', pending_word))
    elif pending_word and pending_change_type == '-':
        changes.append((curr_index, pending_word, ''))

    return changes
