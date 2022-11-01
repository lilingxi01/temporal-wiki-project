from grimm import clean_syntax

text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

text, external_links, internal_links, images = clean_syntax(text)
print(text)
print(external_links)
print(internal_links)
print()

print('# External links:')
for external_link in external_links:
    start_pos, end_pos, content = external_link
    print(text[start_pos: end_pos], '-->', content)

print()

print('# Internal links:')
for internal_link in internal_links:
    start_pos, end_pos, content = internal_link
    print(text[start_pos: end_pos], '-->', content)
