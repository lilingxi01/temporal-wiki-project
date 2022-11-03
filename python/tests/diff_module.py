from difflib import Differ
from ergodiff.preprocess import preprocess_str_to_pool
from ergodiff.postprocess import diff_postprocess


example_a = '''Hi, I want to meet you
Hello
Good
     
NICE
'''

example_b = '''Hi, I would like to meet you
Helo
Goood
     
NICE
'''

differ = Differ()

diff_result = differ.compare(preprocess_str_to_pool(example_a), preprocess_str_to_pool(example_b))

old_sentences, changes = diff_postprocess(diff_result)
print(old_sentences)
print()
print(changes)


