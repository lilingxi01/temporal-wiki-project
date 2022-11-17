from typing import List


def auto_reconstruct(old_sentences: List[str], changes: List[List[List[str]]], added_lines: List[List[int]]) -> List[str]:
    """
    Progressive replacement of the old sentences with the changes.

    :param old_sentences: The old sentences.
    :param changes: The changes.
    :return: The new sentences.
    """
    processing_first_sentence = True
    curr_iteration_index = 0
    for change_list, added_lines_list in zip(changes, added_lines):
        # The first version already has the empty lines recorded,
        # so when processing the first sentence, we ignore them.
        if not processing_first_sentence:
            for added_line in added_lines_list:
                old_sentences.insert(added_line, '')

        try:
            old_sentences = progressive_reconstruct(old_sentences, change_list)
        except IndexError:
            print('IndexError at iteration', curr_iteration_index)

        while '' in old_sentences:
            old_sentences.remove('')
        processing_first_sentence = False
        curr_iteration_index += 1
    return old_sentences


def progressive_reconstruct(old_sentences: List[str], changes: List[List[str]]) -> List[str]:
    """
    Progressive replacement of the old sentences with the changes.

    :param old_sentences: The old sentences.
    :param changes: The changes.
    :return: The new sentences.
    """
    new_sentences = []
    curr_sentence_index = 0
    for old_sentence, change_list in zip(old_sentences, changes):
        new_sentence = old_sentence
        index_drift = 0
        for start, old, new in change_list:
            start += index_drift
            if old == '':
                # if start - 1 >= len(new_sentence):
                #     print(curr_sentence_index, new_sentence, start, old, new)
                if start - 1 >= len(new_sentence) or (start - 1 >= 0 and new_sentence[start - 1] != ' '):
                    new = ' ' + new
                if start + len(old) < len(new_sentence) and new_sentence[start + len(old)] != ' ':
                    new = new + ' '
                new_sentence = new_sentence[:start] + new + new_sentence[start + len(old):]
                index_drift += len(new) - len(old)
            elif new == '':
                if start - 1 >= 0:
                    new_sentence = new_sentence[:start - 1] + new_sentence[start + len(old):]
                elif start + len(old) < len(new_sentence):
                    new_sentence = new_sentence[:start] + new_sentence[start + len(old) + 1:]
                else:
                    new_sentence = new_sentence[:start] + new_sentence[start + len(old):]
                index_drift -= len(old) + 1
            else:
                new_sentence = new_sentence[:start] + new + new_sentence[start + len(old):]
                index_drift += len(new) - len(old)
        new_sentences.append(new_sentence)
        curr_sentence_index += 1
    return new_sentences
