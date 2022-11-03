from typing import Iterator, List


def diff_postprocess(diff: Iterator[str]):
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
        print(change_type, content)

        # If it is not '?' and we have pending row, then we archive it.
        if change_type != '?' and pending_row and pending_change_type:
            # Cleanup and archive pending information.
            if edit_context and pending_change_type == '+':
                old_row, old_change = edit_context
                new_row, new_change = pending_row, ''
                edit_change = change_expander(old_row, new_row, old_change, new_change)
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
                edit_change = change_expander(old_row, new_row, old_change, new_change)
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

    return old_sentences, changes


# TODO: Design of 'progressive replacement' function - trim the empty line in the output for line deletion.
# TODO: For the ProRep function, we need to handle the index drift while replacing by tracking down the length
#  change of the previous children.


# TODO: Documentation.
def build_waypoints(sentence: str, forward=False):
    waypoints = []
    if forward:
        total_len = len(sentence)
        curr_waypoint = total_len
        for index, character in enumerate(reversed(sentence)):
            index = total_len - 1 - index
            if character == ' ':
                curr_waypoint = index
                waypoints.append(-1)
            else:
                waypoints.append(curr_waypoint)
        return waypoints[::-1]
    else:
        curr_waypoint = 0
        for index, character in enumerate(sentence):
            index = index
            if character == ' ':
                curr_waypoint = index + 1
                waypoints.append(-1)
            else:
                waypoints.append(curr_waypoint)
        return waypoints


# TODO: Documentation.
# Notice: `end` is its actual position + 1. Similar rule as ending index.
def get_waypoint(start: int, end: int, forward_waypoints: List[int], backward_waypoints: List[int]):
    start_pos = start if backward_waypoints[start] == -1 else backward_waypoints[start]
    end_pos = end if forward_waypoints[end - 1] == -1 else forward_waypoints[end - 1]
    return start_pos, end_pos


def track_changes_without_waypoints(change_pattern: str, target: str):
    changes = []
    opened = False
    curr_start = -1

    for index, character in enumerate(change_pattern):
        if character == target:
            if not opened:
                opened = True
                curr_start = index
        else:
            if opened:
                opened = False
                changes.append((curr_start, index))

    if opened:
        changes.append((curr_start, len(change_pattern)))

    return changes


# TODO: Merge all tracking functions into one loop.
def track_changes(change_pattern: str, target: str, forward_waypoints: List[int], backward_waypoints: List[int]):
    changes = []
    opened = False
    curr_start = -1

    for index, character in enumerate(change_pattern):
        if character == target:
            if not opened:
                opened = True
                curr_start = index
        else:
            if opened:
                opened = False
                changes.append(get_waypoint(curr_start, index, forward_waypoints, backward_waypoints))

    if opened:
        changes.append(get_waypoint(curr_start, len(change_pattern), forward_waypoints, backward_waypoints))

    return changes


# TODO: Documentation.
def change_expander(old_sentence: str, new_sentence: str, old_change_pattern: str, new_change_pattern: str) -> List[tuple]:
    change_list = set()

    # Track the expansion waypoints.
    old_forward_waypoints = build_waypoints(old_sentence, forward=True)
    old_backward_waypoints = build_waypoints(old_sentence, forward=False)
    new_forward_waypoints = build_waypoints(new_sentence, forward=True)
    new_backward_waypoints = build_waypoints(new_sentence, forward=False)

    add_changes = track_changes(new_change_pattern, '+', new_forward_waypoints, new_backward_waypoints)
    delete_changes = track_changes(old_change_pattern, '-', old_forward_waypoints, old_backward_waypoints)
    old_edit_changes = track_changes(old_change_pattern, '^', old_forward_waypoints, old_backward_waypoints)
    new_edit_changes = track_changes(new_change_pattern, '^', new_forward_waypoints, new_backward_waypoints)

    # The handling order should be 'delete', 'edit', and 'add'.
    # And we want to treat all of them to be 'edit', so it becomes better in the word-basis.

    # Because when deleting, editing new sentence, the index becomes not promising.
    # In order to track where the content was added in the original sentence, we need to track the drift.
    # This drift is only for offsetting the index of "new sentence", never the old one.
    # Should be plus onto the current index (on new sentence).

    upper_drifts = [0] * len(old_sentence)
    lower_drifts = [0] * len(new_sentence)

    old_length_tracker = [0] * len(old_sentence)
    new_length_tracker = [0] * len(new_sentence)

    for start, end in sorted(list(set(delete_changes + old_edit_changes)), key=lambda x: x[0]):
        old_length_tracker[start] = end - start

    for start, end in sorted(list(set(add_changes + new_edit_changes)), key=lambda x: x[0]):
        new_length_tracker[start] = end - start

    cumulative_drift = 0
    curr_index = 0
    while curr_index < len(old_length_tracker) and curr_index - cumulative_drift < len(new_length_tracker):
        curr_tracker_value = old_length_tracker[curr_index]
        target_tracker_value = new_length_tracker[curr_index - cumulative_drift]
        if curr_tracker_value == 0 and target_tracker_value == 0:
            upper_drifts[curr_index] = cumulative_drift
            curr_index += 1
            continue
        difference = curr_tracker_value - target_tracker_value
        target_index = curr_index + curr_tracker_value
        while curr_index < target_index:
            upper_drifts[curr_index] = cumulative_drift
            curr_index += 1
        cumulative_drift += difference

    cumulative_drift = 0
    curr_index = 0
    while curr_index < len(new_length_tracker) and curr_index + cumulative_drift < len(old_length_tracker):
        curr_tracker_value = new_length_tracker[curr_index]
        target_tracker_value = old_length_tracker[curr_index + cumulative_drift]
        if curr_tracker_value == 0 and target_tracker_value == 0:
            lower_drifts[curr_index] = cumulative_drift
            curr_index += 1
            continue
        difference = target_tracker_value - curr_tracker_value
        target_index = curr_index + curr_tracker_value
        while curr_index < target_index:
            lower_drifts[curr_index] = cumulative_drift
            curr_index += 1
        cumulative_drift += difference

    print('upper:', upper_drifts)
    print('lower:', lower_drifts)

    for start, end in delete_changes:
        corresponding_index = start - upper_drifts[start]
        new_start, new_end = get_waypoint(corresponding_index, corresponding_index, new_forward_waypoints,
                                          new_backward_waypoints)
        old_text = old_sentence[start:end]
        new_text = new_sentence[new_start:new_end]
        change_list.add((start, old_text, new_text))

    for i in range(len(old_edit_changes)):
        old_start, old_end = old_edit_changes[i]
        old_change_text = old_sentence[old_start:old_end]
        new_start, new_end = new_edit_changes[i]
        new_change_text = new_sentence[new_start:new_end]
        change_list.add((old_start, old_change_text, new_change_text))

    for start, end in add_changes:
        corresponding_index = start + lower_drifts[start]
        if upper_drifts[corresponding_index] == start:
            old_start, old_end = get_waypoint(corresponding_index, corresponding_index, old_forward_waypoints,
                                              old_backward_waypoints)
        else:
            old_start, old_end = 0, 0
        old_text = old_sentence[old_start:old_end]
        new_text = new_sentence[start:end]
        change_list.add((corresponding_index, old_text, new_text))

    return sorted(list(change_list), key=lambda x: x[0])

