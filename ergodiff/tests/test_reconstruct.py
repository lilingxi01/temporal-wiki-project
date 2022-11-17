from ergodiff import Ergodiff, progressive_reconstruct


ergodiff = Ergodiff()


def test_progressive_reconstruct_step():
    example_a = 'Okay, this is added.'
    example_b = 'Okay, that is nicely added.'

    old_sentences, changes, added_lines = ergodiff.get_diff(example_a, example_b)
    new_sentences = progressive_reconstruct(old_sentences, changes)

    assert new_sentences == ['Okay, that is nicely added.']
