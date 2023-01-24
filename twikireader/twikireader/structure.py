class TemporalWikiArticle:
    def __init__(self, title: str):
        self.title = title
        self.revisions = []
        self.id = None

    def add_revision(self, revision_text):
        self.revisions.append(revision_text)
