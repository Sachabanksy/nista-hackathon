import os
import xml.etree.cElementTree as ET
import pandas as pd

directory = "scrapedxml/debates/"
total_df = []

def iter_docs(author):
    author_attr = author.attrib
    for doc in author.iter('speech'):
        doc_dict = author_attr.copy()
        doc_dict.update(doc.attrib)
        doc_dict['data'] = doc[0].text
        yield doc_dict

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".xml"): 
        filepath = os.path.join(directory, filename)
        print("Parsing ", filepath)
        tree = ET.parse(filepath)
        root = tree.getroot()
        doc_df = pd.DataFrame(list(iter_docs(root)))
        total_df.append(doc_df)
        continue
    else:
        continue

total_df = pd.concat(total_df)
total_df = total_df.reset_index(drop=True)
print(total_df)

total_df.to_csv('hansard.csv')
