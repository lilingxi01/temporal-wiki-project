from typing import Iterator, Tuple, List

from ergodiff.inner_diff import process_inner_diff


def process_outer_diff(diff: Iterator[str]) -> Tuple[List[str], List[List[str]], List[int]]:
    old_sentences = []

    # For the format of items of changes, check Notion documentation.
    # Basically they are tuples in this format: `(starting_index, old_text, new_text)`.
    changes = []

    # Pending row is ONLY for keeping the information and waiting for '?'.
    # It does not wait for next '-' or '+', as `edit_context` variable did this work.
    pending_row = None

    # Only '+' and '-' will have pending behavior. So potential values are None, '-', or '+'.
    pending_change_type = None

    # Store the edit context.
    # We need to know the previous line is '-' + '?', so that we can track the relationship.
    # We have no `pending_changes` list because when we have the change detail,
    # we store them into edit context or directly archive it.
    edit_context = None

    potential_edit_add = False

    for row in diff:
        if not len(row):
            continue

        change_type = row[0]
        content = row[2:].rstrip('\n')

        # If it is not '?' and we have pending row, then we archive it.
        if change_type != '?' and pending_row and pending_change_type:
            # Cleanup and archive pending information.
            if edit_context and pending_change_type == '+':
                old_row, old_change = edit_context
                new_row, new_change = pending_row, ''
                edit_change = process_inner_diff(old_row, new_row)
                old_sentences.append(old_row)
                changes.append(edit_change)
                edit_context = None
            elif pending_change_type == '+':
                old_sentences.append('')
                changes.append([(0, '', pending_row)])
            else:
                old_sentences.append(pending_row)
                changes.append([(0, pending_row, '')])
                if change_type == '+':
                    potential_edit_add = True
            pending_row = None
            pending_change_type = None

        if change_type == ' ':
            # Archive the un-changed sentence directly.
            old_sentences.append(content)
            changes.append([])  # An empty change-list means that we have no change in this row.
        elif change_type in ['+', '-']:
            # We will wait for '?' in this case.
            pending_row = content
            pending_change_type = change_type
        elif change_type == '?':
            if pending_change_type == '+':
                # Finalize the edit change.
                if not edit_context and potential_edit_add:
                    old_row, old_change = old_sentences.pop(), ''
                    changes.pop()
                elif edit_context:
                    old_row, old_change = edit_context
                else:
                    old_row, old_change = '', ''  # TODO: Problematic! Need to find a way to handle it more precisely.
                new_row, new_change = pending_row, content
                edit_change = process_inner_diff(old_row, new_row)
                # Finalize the edit change and archive it.
                old_sentences.append(old_row)
                changes.append(edit_change)
                # Cleanup outdated variables.
                edit_context = None
            else:
                # Keep the change context and wait for '+'.
                edit_context = (pending_row, content)

            # Final cleanup.
            pending_row = None
            pending_change_type = None
            potential_edit_add = False

    # Finalize the parsing if there are any pending change left.
    if pending_row and pending_change_type == '+':
        old_sentences.append('')
        changes.append([(0, '', pending_row)])
    elif pending_row and pending_change_type == '-':
        old_sentences.append(pending_row)
        changes.append([(0, pending_row, '')])

    # Compute the index of added lines.
    # Because we are not accepting any existing line to be empty,
    # so all empty lines should be added lines in current iteration.
    added_lines = []
    for index, line in enumerate(old_sentences):
        if line == '':
            added_lines.append(index)

    return old_sentences, changes, added_lines
