from xml.dom import minidom
from helper import *
from jp_parser_helper import *

original_jmdict_file = base_dir + "lang/JMdict_e"
simple_jmdict_file = base_dir + "lang/JMdict_e_s.tsv"
meanings_jmdict_file = base_dir + "lang/JMdict_e_m.tsv"

print("Loading JMDict...")
import xml.etree.ElementTree as ET
tree = ET.parse(original_jmdict_file)
root = tree.getroot()

print("Parsing XML...")
entries = root.findall('entry')

print("Converting %d entries..." % len(entries))

parts_of_speech_counter = dict()

for p in jmdict_parts_of_speech_list:
    parts_of_speech_counter[p] = 0

pos_list_updated = False

o_f = open(simple_jmdict_file,"w",encoding="utf-8")
o_f2 = open(meanings_jmdict_file,"w",encoding="utf-8")

def calculate_frequency_ranking(freq_elems):
    if 'news1' in freq_elems or 'ichi1' in freq_elems:
        return int(12000/500)
    elif 'news2' in freq_elems or 'ichi2' in freq_elems:
        return int(24000/500)
    elif 'spec1' in freq_elems or 'gai1' in freq_elems:
        return int(12000/500)
    elif 'spec2' in freq_elems or 'gai2' in freq_elems:
        return int(24000/500)
    return 99

for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []
    k_freq = None
    r_freq = None
    k_freq_elems = []
    r_freq_elems = []

    pos_list = [] # parts of speech (verb, noun, expression etc)
    ent_seq = elem.find('ent_seq').text
    k_elems = elem.findall('k_ele')
    gloss = []
    for k_elem in k_elems:
        keb = k_elem.find('keb')
        kanji_elements.append(keb.text)
        k_pri_els = k_elem.findall('ke_pri')
        for k_pri_el in k_pri_els:
            pr = k_pri_el.text
            if pr[0:2] == 'nf':
                k_freq = int(pr[2:])
            else:
                k_freq_elems.append(pr)

    r_elems = elem.findall('r_ele')
    for r_elem in r_elems:
        reb = r_elem.find('reb')
        readings.append(reb.text)
        if reb.text == 'ある':
            pass
        r_pri_els = r_elem.findall('re_pri')
        for r_pri_el in r_pri_els:
            pr = r_pri_el.text
            if pr[0:2] == 'nf':
                r_freq = int(pr[2:])
            else:
                r_freq_elems.append(pr)

    s_ele = elem.find('sense')
    if s_ele is not None:
        pos_elems = s_ele.findall('pos')
        for pos_elem in pos_elems:
            pos = pos_elem.text
            if pos not in jmdict_parts_of_speech_list:
                jmdict_parts_of_speech_list.append(pos)
                parts_of_speech_counter[pos] = 0
                pos_list_updated = True
            pos_list.append(str(jmdict_parts_of_speech_list.index(pos)))
            parts_of_speech_counter[pos] += 1

        gl_elems = s_ele.findall('gloss')
        for gl_elem in gl_elems:
            gloss.append(gl_elem.text)

    if k_freq is None:
        k_freq = calculate_frequency_ranking(k_freq_elems)
    if r_freq is None:
        r_freq = calculate_frequency_ranking(r_freq_elems)

    pos_list=list(set(pos_list))
    gloss_str = json.dumps(gloss)    
    row = "%s\t%s\t%s\t%s\t%d\t%s\n" % \
        (ent_seq, ','.join(kanji_elements), ','.join(readings), 
         ','.join(pos_list), k_freq, r_freq)

    row_m = "%s\t%s\t%s\t%s\t%d\t%s\t%s\n" % \
        (ent_seq, ','.join(kanji_elements), ','.join(readings), 
         ','.join(pos_list), k_freq, r_freq, gloss_str)
    
    if pos_list_updated:
        sorted_pos = dict(sorted(parts_of_speech_counter.items(), key=lambda x:x[1], reverse=True))
        print("New POS list! MUST update also bm_ocr_processor.py !", jmdict_parts_of_speech_list)
        print("By frequency:")
        print(sorted_pos)
        print("By frequency (just keys):")
        print(sorted_pos.keys())

    o_f.write(row)
    o_f2.write(row_m)
o_f.close()
o_f2.close()
