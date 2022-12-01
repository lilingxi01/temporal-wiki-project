import os
import json
from difflib import SequenceMatcher
from typing import List

import xmltodict
from .models import HistoryBase
from ergodiff import auto_reconstruct, preprocess_str_to_pool

import argparse

curr_article = None
article_count = 0


def record_error_log(path: str, content: str):
    output_folder_path = '/'.join(str(path).split('/')[:-1])
    if output_folder_path != '' and not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)
    with open(path, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(prog='twikidata', description='A tool for parsing temporal wikipedia XML dump.')
    parser.add_argument('--file', type=argparse.FileType('rb'), required=True, help='The XML file.')
    parser.add_argument('--output', type=str, default='./twikidata-output.json', help='The output directory.')
    parser.add_argument('--limit', type=int, default=99999, help='Maximum number of articles to parse.')
    args = parser.parse_args()

    # Load minimal sample file and content.
    xml_file = args.file

    print('[Parse] Parsing XML file...')

    parsed_articles: List = []
    global curr_article
    global article_count

    def handle_item(path, item):
        global curr_article
        global article_count
        if path[-1][0] == 'title':
            if curr_article is not None:
                parsed_articles.append(curr_article)
            if article_count >= args.limit:
                curr_article = None
                return False
            article_count += 1
            print('[Parse] Parsing article ({}):'.format(article_count), item.strip())
            curr_article = HistoryBase(item.strip())
        if path[-1][0] == 'id':
            if curr_article is not None:
                curr_article.set_id(item.strip())
        if curr_article is not None and type(item) is dict and 'text' in item and '#text' in item['text']:
            # TODO: Store the parent id for each revision.
            curr_article.add_revision(item['text']['#text'], item['timestamp'])
        return True

    try:
        xmltodict.parse(xml_file, item_depth=3, item_callback=handle_item)
    except xmltodict.ParsingInterrupted:
        print('[Parse] Parsing interrupted (because it has reached the limit).')

    if curr_article is not None:
        parsed_articles.append(curr_article)
        curr_article = None

    article_count = 0

    print('[Build] Building history differences...')

    processed_articles = []

    for parsed_article in parsed_articles:
        old_sentences, changes, added_lines = parsed_article.get_change_lists()
        processed_articles.append({
            'id': parsed_article.id,
            'title': parsed_article.title,
            'old_sentences': old_sentences,
            'changes': changes,
            'added_lines': added_lines,
        })

        print('[Build] Parsing progress: {} / {}'.format(len(processed_articles), len(parsed_articles)))

        candidate_final_version = preprocess_str_to_pool(parsed_article[-1].raw_text)
        final_version = auto_reconstruct(old_sentences, changes, added_lines)

        try:
            candidate_article = '\n'.join(candidate_final_version).split()
            reconstructed_article = '\n'.join(final_version).split()
        except TypeError:
            record_error_log('./error_logs/{}.json'.format(
                'error_' + '+'.join(parsed_article.title.split())),
                json.dumps({
                    'id': parsed_article.id,
                    'title': parsed_article.title,
                    'reason': 'Article not iterable.',
                    'last_revision': candidate_final_version,
                    'reconstructed': final_version,
                }),
            )
            continue

        mismatch_sequence = SequenceMatcher(None, candidate_article, reconstructed_article)
        if mismatch_sequence.ratio() < 1.0:
            print('>>> [Warning] Final version mismatch:', parsed_article.title, 'with matching ratio',
                  mismatch_sequence.ratio())
            record_error_log('./error_logs/{}.json'.format(
                'mismatch_' + '+'.join(parsed_article.title.split())),
                json.dumps({
                    'id': parsed_article.id,
                    'title': parsed_article.title,
                    'differences': [(tag, candidate_article[i1:i2], reconstructed_article[j1:j2]) for
                                    tag, i1, i2, j1, j2 in
                                    mismatch_sequence.get_opcodes() if tag != 'equal'],
                    'last_revision': candidate_article,
                    'reconstructed': reconstructed_article,
                }),
            )

    output_folder_path = '/'.join(str(args.output).split('/')[:-1])
    if output_folder_path != '' and not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)
    with open(args.output, 'w') as f:
        f.write(json.dumps(processed_articles))

    print('[Done] {} articles have been parsed.'.format(len(processed_articles)))


if __name__ == '__main__':
    main()
