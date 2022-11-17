from ergodiff import Ergodiff


ergodiff = Ergodiff()


def test_add_line():
    example_a = 'Hello, world!\nThis is a test.'
    example_b = 'Hello, world!\nOkay, this is added.\nThis is a test.'

    old_sentences, changes, added_lines = ergodiff.get_diff(example_a, example_b)

    assert old_sentences == ['Hello, world!', '', 'This is a test.']
    assert changes[0] == []
    assert changes[1] == [(0, '', 'Okay, this is added.')]
    assert changes[2] == []
    assert added_lines == [1]


def test_delete_line():
    example_a = 'Hello, world!\nOkay, this is added.\nThis is a test.'
    example_b = 'Hello, world!\nThis is a test.'

    old_sentences, changes, added_lines = ergodiff.get_diff(example_a, example_b)

    assert old_sentences == ['Hello, world!', 'Okay, this is added.', 'This is a test.']
    assert changes[0] == []
    assert changes[1] == [(0, 'Okay, this is added.', '')]
    assert changes[2] == []
    assert added_lines == []


def test_mutate_line_add():
    example_a = 'Okay, this is added.'
    example_b = 'Okay, that is nicely added.'

    old_sentences, changes, added_lines = ergodiff.get_diff(example_a, example_b)

    assert old_sentences == ['Okay, this is added.']
    assert changes[0] == [(6, 'this', 'that'), (14, '', 'nicely')]
    assert added_lines == []


def test_mutate_line_delete():
    example_a = 'Okay, this one is added perfectly.'
    example_b = 'Okay, that one is added.'

    old_sentences, changes, added_lines = ergodiff.get_diff(example_a, example_b)

    assert old_sentences == ['Okay, this one is added perfectly.']
    assert changes[0] == [(6, 'this', 'that'), (18, 'added', 'added.'), (24, 'perfectly.', '')]
    assert added_lines == []
