from typing import Callable, List
import xmltodict

from .structure import TemporalWikiArticle


class TemporalWikiReader:
    def __init__(self, xml_file: str, error_log_file: str):
        self.xml_file = xml_file
        self.error_log_file = error_log_file

        self.curr_article = None
        self.article_count = 0

    def build(self, callback: Callable[[TemporalWikiArticle], None], limit: int = -1):
        print('[Parse] Parsing XML file...')

        self.curr_article = None
        self.article_count = 0

        parsed_articles: List = []

        def handle_item(path, item):
            if path[-1][0] == 'title':
                if self.curr_article is not None:
                    parsed_articles.append(self.curr_article)
                    callback(self.curr_article)
                if limit != -1 and self.article_count >= limit:
                    self.curr_article = None
                    return False
                self.article_count += 1
                print('[Parse] Parsing article ({}):'.format(self.article_count), item.strip())
                self.curr_article = TemporalWikiArticle(title=item.strip())
            if path[-1][0] == 'id':
                if self.curr_article is not None:
                    self.curr_article.id = item.strip()
            if self.curr_article is not None and type(item) is dict and 'text' in item and '#text' in item['text']:
                self.curr_article.add_revision(item['text']['#text'])
            return True

        try:
            xmltodict.parse(self.xml_file, item_depth=3, item_callback=handle_item)
        except xmltodict.ParsingInterrupted:
            print('[Parse] Parsing interrupted (because it has reached the limit).')

        if self.curr_article is not None:
            parsed_articles.append(self.curr_article)
            callback(self.curr_article)
            self.curr_article = None
