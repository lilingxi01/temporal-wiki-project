from project.grimm.cleaner_core import parse_external_links, parse_internal_links, drift_adjust

text = '[[Wow]], [https://google.com/hello Hello] [[world]]ing yeah [https://lingxi.li Lingxi Li]!'

text, external_links, images = parse_external_links(text)
print(text)
print(external_links)
print(images)
print()

text, internal_links, drifts = parse_internal_links(text)
print(text)
print(internal_links)
print(drifts)
print()

external_links = drift_adjust(external_links, drifts)
images = drift_adjust(images, drifts)
print(external_links)
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
