import nltk
from typing import List, Dict, Set
from grimm import clean_syntax


def split_to_sentences(paragraph: str) -> List[str]:
    """
    Split a paragraph into sentences.
    :param paragraph: a paragraph
    :return: a list of sentences
    """
    sentences = []
    text, _, _, _ = clean_syntax(paragraph)
    for sentence in nltk.sent_tokenize(text):
        sentence = sentence.strip()
        if len(sentence) > 0:
            sentences.append(sentence)
    return sentences


def merge_paraphrasing_map(curr_map: Dict[str, Set[str]], curr_paragraph: str):
    """
    Merge the paraphrasing map of the current paragraph into the global map.
    :param curr_map: the current paragraph's paraphrasing map
    :param curr_paragraph: the current paragraph
    :return: the global paraphrasing map
    """
    curr_pool = split_to_sentences(curr_paragraph)
    for i in range(len(curr_pool) - 1):
        curr_set = curr_map.get(curr_pool[i], set())
        curr_set.add(curr_pool[i + 1])
        curr_map[curr_pool[i]] = curr_set


def postprocess_map(paraphrasing_map: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Post-process the paraphrasing map.
    :param paraphrasing_map: the paraphrasing map
    :return: the post-processed paraphrasing map
    """
    target_map = {}
    for key in paraphrasing_map:
        target_map[key] = list(paraphrasing_map[key])
    return target_map
