from difflib import Differ
from ergodiff.preprocess import preprocess_str_to_pool
from ergodiff.postprocess import diff_postprocess


example_a = '''The Trial is a novel by the author Franz Kafka which details the story of a character named Josef K, who, for reasons that one never discovers, awakes one morning and is mysteriously arrested and subjected to the rigours of the judicial process for an unspecified crime.
Hello
Good
     
NICE
'''

example_b = '''Like Kafka's other novels, The Trial was left unfinished at his death, and was never intended to be published.
The Trial is a novel by the author Franz Kafka that tells the story of a character named Josef K, who, for reasons that one never discovers, awakes one morning and is arrested and subjected to the rigours of the judicial process for an unspecified crime.
Hll
Goood
     
NICE
'''

differ = Differ()

diff_result = differ.compare(preprocess_str_to_pool(example_a), preprocess_str_to_pool(example_b))

old_sentences, changes = diff_postprocess(diff_result)
print(old_sentences)
print()
print(changes)


