import xmltodict
from history_model import HistoryBase
from diff_module import HistoryDiff

# Load minimal sample file and content.
xml_file = open('./sample_data/minimal_sample.xml', 'r')
xml_content = xml_file.read()

# Parse the XML content and generate the object tree.
tree = xmltodict.parse(xml_content)

# Parse the object tree.
parsed = []

if type(tree['mediawiki']['page']) is list:
    for page in tree['mediawiki']['page']:
        parsed.append(HistoryBase(page))
else:
    parsed.append(HistoryBase(tree['mediawiki']['page']))

# Generate history map based on
history = HistoryDiff(
    old_text=parsed[0][0].raw_text,
    new_text=parsed[0][1].raw_text
)

print(history)
