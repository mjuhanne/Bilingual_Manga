
from xml.dom import minidom
from helper import *

original_jmdict_file = base_dir + "lang/JMdict_e"
simple_jmdict_file = base_dir + "lang/JMdict_e_s.tsv"


print("Loading JMDict...")
# parse an xml file by name
#file = minidom.parse(original_jmdict_file)

import xml.etree.ElementTree as ET
tree = ET.parse(original_jmdict_file)
root = tree.getroot()


print("Parsing XML...")
#entries = file.getElementsByTagName('entry')
entries = root.findall('entry')

print("Converting %d entries..." % len(entries))


parts_of_speech_counter = dict()

for p in jmdict_parts_of_speech_list:
    parts_of_speech_counter[p] = 0

pos_list_updated = False

o_f = open(simple_jmdict_file,"w",encoding="utf-8")

for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []
    pos_list = [] # parts of speech (verb, noun, expression etc)
    ent_seq = elem.find('ent_seq').text
    k_ele = elem.find('k_ele')
    if k_ele is not None:
        for keb in k_ele.findall('keb'):
            kanji_elements.append(keb.text)
    r_ele = elem.find('r_ele')
    if r_ele is not None:
        for reb in r_ele.findall('reb'):
            readings.append(reb.text)
    s_ele = elem.find('sense')
    if s_ele is not None:
        pos_ele = s_ele.find('pos')
        if pos_ele is not None:
            pos = pos_ele.text
            if pos not in jmdict_parts_of_speech_list:
                jmdict_parts_of_speech_list.append(pos)
                parts_of_speech_counter[pos] = 0
                pos_list_updated = True
            pos_list.append(str(jmdict_parts_of_speech_list.index(pos)))
            parts_of_speech_counter[pos] += 1

    """
    for node in elem.childNodes:
        if node.localName == 'ent_seq':
            ent_seq = node.childNodes[0].data.strip()
        elif node.localName == 'k_ele':
            keb = node.getElementsByTagName('keb')[0]
            for ch in keb.childNodes:
                kanji_elements.append(ch.data.strip())
        elif node.localName == 'r_ele':
            reb = node.getElementsByTagName('reb')[0]
            for ch in reb.childNodes:
                readings.append(ch.data.strip())
        elif node.localName == 'sense':
            pos_el = node.getElementsByTagName('pos')[0]
            if pos_el is not None:
                pos = pos_el.childNodes[0].data.strip()
                test = pos_el.childNodes[0].toxml()
                if pos not in jmdict_parts_of_speech_list:
                    jmdict_parts_of_speech_list.append(pos)
                    parts_of_speech_counter[pos] = 0
                    pos_list_updated = True
                pos_list.append(str(jmdict_parts_of_speech_list.index(pos)))
                parts_of_speech_counter[pos] += 1
    """

    if ent_seq == '2843261':
        pass

    pos_list=list(set(pos_list))
    row = "%s\t%s\t%s\t%s\n" % (ent_seq, ','.join(kanji_elements), ','.join(readings), ','.join(pos_list))
    #print(ent_seq,kanji_elements,readings)

    if pos_list_updated:
        sorted_pos = dict(sorted(parts_of_speech_counter.items(), key=lambda x:x[1], reverse=True))
        print("New POS list! MUST update also bm_ocr_processor.py !", jmdict_parts_of_speech_list)
        print("By frequency:")
        print(sorted_pos)
        print("By frequency (just keys):")
        print(sorted_pos.keys())

    o_f.write(row)
o_f.close()
