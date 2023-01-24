import os
import json
import argparse

import nltk
from twikireader import TemporalWikiReader, TemporalWikiArticle

from .utils import merge_paraphrasing_map, postprocess_map


global prps_map
prps_map = dict()


def builder_callback(article: TemporalWikiArticle):
    global prps_map

    for revision in article.revisions:
        merge_paraphrasing_map(prps_map, revision)


def main():
    parser = argparse.ArgumentParser(
        prog='prpsdata',
        description='A tool for parsing temporal wikipedia XML dump into paraphrasing dataset.'
    )
    parser.add_argument('--file', type=argparse.FileType('rb'), required=True, help='The XML file.')
    parser.add_argument('--output', type=str, default='./prps.json', help='The output directory.')
    parser.add_argument('--limit', type=int, default=999999, help='Maximum number of articles to parse.')
    args = parser.parse_args()

    reader = TemporalWikiReader(xml_file=args.file, error_log_file='prps-error.log')

    # Reset global variables.
    global prps_map
    prps_map = dict()

    # Install NLTK data.
    nltk.download('punkt')

    reader.build(callback=builder_callback, limit=args.limit)

    output_folder_path = '/'.join(str(args.output).split('/')[:-1])
    if output_folder_path != '' and not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)
    with open(args.output, 'w') as f:
        f.write(json.dumps(postprocess_map(prps_map), indent=2))  # Indent for readability.

    print('[Done] A map of {} sentences have been parsed.'.format(len(prps_map.keys())))


if __name__ == '__main__':
    main()
