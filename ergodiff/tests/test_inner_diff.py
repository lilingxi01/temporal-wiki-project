from ergodiff import Ergodiff


ergodiff = Ergodiff()


def test_inner_diff():
    example_a = 'Okay, this is added.'
    example_b = 'Okay, that is nicely added.'

    result = ergodiff.get_sentence_diff(example_a, example_b)
    assert result == [(6, 'this', 'that'), (14, '', 'nicely')]
