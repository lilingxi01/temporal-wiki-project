import json
import os
from difflib import Differ

import xmltodict
from .models import HistoryBase
from ergodiff import auto_reconstruct, preprocess_str_to_pool


def main():
    # Load minimal sample file and content.
    xml_file = open('../sample_data/minimal_sample.xml', 'r')
    xml_content = xml_file.read()

    # Parse the XML content and generate the object tree.
    tree = xmltodict.parse(xml_content)

    # Parse the object tree.
    parsed = []

    if type(tree['mediawiki']['page']) is list:
        for page in tree['mediawiki']['page']:
            parsed.append(HistoryBase(page))
    else:
        parsed.append(HistoryBase(tree['mediawiki']['page']))

    test_article = parsed[0]
    old_sentences, changes, added_lines = test_article.get_change_lists()

    candidate_pool = preprocess_str_to_pool(parsed[0][-1].raw_text)
    reconstruct_result = auto_reconstruct(old_sentences, changes, added_lines)

    # print('\n'.join(candidate_pool))
    # print('=============================')
    # print('\n'.join(reconstruct_result))

    # differ = Differ()
    # for candidate_line, reconstruct_line in zip(candidate_pool, reconstruct_result):
    #      if candidate_line != reconstruct_line:
    #          print('\n'.join(list(differ.compare([candidate_line], [reconstruct_line]))))

    print('Running on', len(parsed[0].children), 'revisions.')
    print('Reconstruct result:', reconstruct_result == candidate_pool)

    if not os.path.exists('../test_output'):
        os.mkdir('../test_output')
    with open('../test_output/sample_1.json', 'w') as f:
        f.write(json.dumps({
            'old_sentences': old_sentences,
            'changes': changes,
            'added_lines': added_lines,
        }))
