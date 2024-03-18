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
entries_with_many_senses = 0
entries_with_more_than_3_senses = 0

for p in jmdict_class_list:
    parts_of_speech_counter[p] = 0

jlpt_refs = get_jlpt_word_jmdict_references()

pos_list_updated = False

o_f = open(simple_jmdict_file,"w",encoding="utf-8")
o_f2 = open(meanings_jmdict_file,"w",encoding="utf-8")

# the cut-offs for news1/spec1 are 12000 and for news2/spec2 12000,
# but we half that value because that's the average frequency.  Then divide by 500
# to get the comparable results for those NFxx tags which use 500 word bins
def calculate_frequency_ranking(freq_elems):
    freq = 99
    if 'news1' in freq_elems or 'ichi1' in freq_elems:
        freq = int(12000/2/500)
    elif 'news2' in freq_elems or 'ichi2' in freq_elems:
        freq = int(24000/2/500)
    elif 'spec1' in freq_elems or 'gai1' in freq_elems:
        freq = int(12000/2/500)
    elif 'spec2' in freq_elems or 'gai2' in freq_elems:
        freq = int(24000/2/500)
    return freq

# form: 'kanji' or 'kana'
def get_jlpt_level(seq,form):
    for i in range(0,5):
        level = 5 - i
        if seq in jlpt_refs[level]:
            if jlpt_refs[level][seq][form] != []:
                return level
    return 0

# Lower the frequency ranking (i.e. make it more priority) if it belongs
# to JLPT word list, especially for beginner level words
# form: 'kanji' (kanji_element) or 'kana' (reading)
def apply_jlpt_modifier_to_frequency_ranking(seq, freq, jlpt_level):
    if jlpt_level > 0:
        return int(freq / (1+jlpt_level/2))
    return freq

for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []
    k_freq = None
    r_freq = None
    k_freq_elems = []
    r_freq_elems = []

    pos_list_per_sense = [] # parts of speech (verb, noun, expression etc)
    ent_seq = elem.find('ent_seq').text
    k_elems = elem.findall('k_ele')
    gloss_list_per_sense = []
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

    s_elems = elem.findall('sense')
    for s_ele in s_elems:
        pos_elems = s_ele.findall('pos')
        gloss_list  = []
        pos_list = []
        for pos_elem in pos_elems:
            pos = pos_elem.text
            if pos not in jmdict_class_list:
                jmdict_class_list.append(pos)
                parts_of_speech_counter[pos] = 0
                pos_list_updated = True
            pos_list.append(int(jmdict_class_list.index(pos)))
            parts_of_speech_counter[pos] += 1

        gl_elems = s_ele.findall('gloss')
        for gl_elem in gl_elems:
            gloss_list.append(gl_elem.text)
        pos_list_per_sense.append(pos_list)
        gloss_list_per_sense.append(gloss_list)
    if len(s_elems)>1:
        entries_with_many_senses += 1
    if len(s_elems)>3:
        entries_with_more_than_3_senses += 1

    if k_freq is None:
        k_freq = calculate_frequency_ranking(k_freq_elems)
    if r_freq is None:
        r_freq = calculate_frequency_ranking(r_freq_elems)

    k_jlpt_level = get_jlpt_level(int(ent_seq), 'kanji')
    if k_jlpt_level > 0:
        k_freq = apply_jlpt_modifier_to_frequency_ranking(int(ent_seq), k_freq, k_jlpt_level)
        k_freq_elems.append('JLPT' + str(k_jlpt_level))

    r_jlpt_level = get_jlpt_level(int(ent_seq), 'kana')
    if r_jlpt_level > 0:
        r_freq = apply_jlpt_modifier_to_frequency_ranking(int(ent_seq), r_freq, r_jlpt_level)
        r_freq_elems.append('JLPT' + str(r_jlpt_level))

    all_freq_elems = set( k_freq_elems + r_freq_elems )
    common_freq_elems = []
    only_k_freq_elems = []
    only_r_freq_elems = []
    for fe in all_freq_elems:
        if fe in k_freq_elems and fe in r_freq_elems:
            common_freq_elems.append(fe)
        elif fe in k_freq_elems:
            only_k_freq_elems.append(fe)
        else:
            only_r_freq_elems.append(fe)

    pos_list=json.dumps(pos_list_per_sense)
    gloss_str = json.dumps(gloss_list_per_sense)
    row = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\n" % \
        (ent_seq, ','.join(kanji_elements), ','.join(readings), 
        pos_list, k_freq, r_freq,
        ','.join(common_freq_elems),','.join(only_k_freq_elems), ','.join(only_r_freq_elems),
        )

    row_m = "%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" % \
        (ent_seq, ','.join(kanji_elements), ','.join(readings), 
         pos_list, k_freq, r_freq, 
        ','.join(common_freq_elems),','.join(only_k_freq_elems), ','.join(only_r_freq_elems),
         gloss_str)
    
    if pos_list_updated:
        sorted_pos = dict(sorted(parts_of_speech_counter.items(), key=lambda x:x[1], reverse=True))
        print("New POS list! MUST update also bm_ocr_processor.py !", jmdict_class_list)
        print("By frequency:")
        print(sorted_pos)
        print("By frequency (just keys):")
        print(sorted_pos.keys())

    o_f.write(row)
    o_f2.write(row_m)
o_f.close()
o_f2.close()

print("Wrote %d entries, of which %d (%d) had more than 1 (3) sense" % (len(entries), entries_with_many_senses, entries_with_more_than_3_senses))
