from grimm import clean_syntax


def test_clean_syntax():
    text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

    text, external_links, internal_links, images = clean_syntax(text)

    assert text == 'Wow, Hello worlding yeah Lingxi Li!'
    assert external_links == [(5, 10, 'https://google.com/hello'), (25, 34, 'https://lingxi.li')]
    assert internal_links == [(0, 3, 'Wow'), (11, 16, 'world')]
    assert images == []
