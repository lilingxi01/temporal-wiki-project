from grimm.cleaner_core import parse_external_links, parse_internal_links, drift_adjust


def test_parse_external_links():
    text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

    text, external_links, images = parse_external_links(text)
    assert text == '[[Wow]], Hello [[world]]ing yeah Lingxi Li!'
    assert external_links == [(9, 14, 'https://google.com/hello'), (33, 42, 'https://lingxi.li')]
    assert images == []


def test_parse_internal_links():
    text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

    text, internal_links, drifts = parse_internal_links(text)
    assert text == 'Wow, [https://google.com/hello Hello] worlding yeah [https://lingxi.li Lingxi Li]!'
    assert internal_links == [(0, 3, 'Wow'), (38, 43, 'world')]


def test_drift_adjust():
    text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

    text, external_links, images = parse_external_links(text)
    text, internal_links, drifts = parse_internal_links(text)
    external_links = drift_adjust(external_links, drifts)
    images = drift_adjust(images, drifts)

    assert text == 'Wow, Hello worlding yeah Lingxi Li!'
    assert external_links == [(5, 10, 'https://google.com/hello'), (25, 34, 'https://lingxi.li')]
    assert internal_links == [(0, 3, 'Wow'), (11, 16, 'world')]
    assert images == []
