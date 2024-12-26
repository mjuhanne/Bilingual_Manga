from helper import *
from jp_parser_helper import *
import time
from mongo import *
database =client['jmdict']

original_jmdict_file = base_dir + "lang/JMdict_e"
original_jmnedict_file = base_dir + "lang/JMnedict.xml"

kanji_element_seq = dict()
reading_element_seq = dict()

############################### JMDICT ###############

print("Loading JMDict...")
import xml.etree.ElementTree as ET
time0 = int(time.time())
tree = ET.parse(original_jmdict_file)
root = tree.getroot()

print("Parsing XML...")
entries = root.findall('entry')

time1 = int(time.time())
print("Loaded in %d seconds" % (time1-time0))
print("Converting %d entries..." % len(entries))

jlpt_refs = get_jlpt_word_jmdict_references()

# create combined verb and noun classes for easier lookup
_jmdict_verb_pos_list = []
for cl in jmdict_class_list:
    idx = jmdict_class_list.index(cl)
    if 'adverb' not in cl:
        if 'verb' in cl:
            _jmdict_verb_pos_list.append(idx)
_jmdict_verb_pos_set = set(_jmdict_verb_pos_list)


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
def get_jlpt_level(seq,form,word):
    for i in range(0,5):
        level = 5 - i
        if seq in jlpt_refs[level]:
            if word in jlpt_refs[level][seq][form]:
                return level
    return 0

# Lower the frequency ranking (i.e. make it more priority) if it belongs
# to JLPT word list, especially for beginner level words
def apply_jlpt_modifier_to_frequency_ranking(seq, freq, jlpt_level):
    if jlpt_level > 0:
        return int(freq / (1+jlpt_level/2))
    return freq

batch = []
_single_kanji_adjectives = dict()
_single_kanji_verbs = dict()

database["entries"].drop()
count = 0
for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []

    elem_freq = dict()
    elem_pri_elems = dict()

    pos_list_per_sense = [] # parts of speech (verb, noun, expression etc)
    ent_seq = int(elem.find('ent_seq').text)
    gloss_list_per_sense = []
    min_r_freq = 99

    # process readings
    r_elems = elem.findall('r_ele')
    for r_elem in r_elems:
        reb_elem = r_elem.find('reb')
        reb = reb_elem.text
        readings.append(reb)

        if reb not in reading_element_seq:
            reading_element_seq[reb] = [ent_seq]
        else:
            reading_element_seq[reb].append(ent_seq)

        elem_freq[reb] = None
        elem_pri_elems[reb] = []
        r_pri_els = r_elem.findall('re_pri')
        for r_pri_el in r_pri_els:
            pr = r_pri_el.text
            if pr[0:2] == 'nf':
                elem_freq[reb] = int(pr[2:])
            else:
                elem_pri_elems[reb].append(pr)
        if elem_freq[reb] is None:
            elem_freq[reb] = calculate_frequency_ranking(elem_pri_elems[reb])
        r_jlpt_level = get_jlpt_level(ent_seq, 'kana', reb)
        if r_jlpt_level > 0:
            elem_freq[reb] = apply_jlpt_modifier_to_frequency_ranking(ent_seq, elem_freq[reb], r_jlpt_level)
            elem_pri_elems[reb].append('JLPT' + str(r_jlpt_level))
        if elem_freq[reb] < min_r_freq:
            min_r_freq = elem_freq[reb]

    # process kanji elements
    k_elems = elem.findall('k_ele')
    for k_elem in k_elems:
        keb_elem = k_elem.find('keb')
        keb = keb_elem.text
        kanji_elements.append(keb)

        if keb not in kanji_element_seq:
            kanji_element_seq[keb] = [ent_seq]
        else:
            kanji_element_seq[keb].append(ent_seq)

        k_pri_els = k_elem.findall('ke_pri')
        elem_freq[keb] = None
        elem_pri_elems[keb] = []
        for k_pri_el in k_pri_els:
            pr = k_pri_el.text
            if pr[0:2] == 'nf':
                elem_freq[keb] = int(pr[2:])
            else:
                elem_pri_elems[keb].append(pr)
        if elem_freq[keb] is None:
            elem_freq[keb] = calculate_frequency_ranking(elem_pri_elems[keb])
        k_jlpt_level = get_jlpt_level(ent_seq, 'kanji', keb)
        if k_jlpt_level > 0:
            elem_freq[keb] = apply_jlpt_modifier_to_frequency_ranking(ent_seq, elem_freq[keb], k_jlpt_level)
            elem_pri_elems[keb].append('JLPT' + str(k_jlpt_level))
        # give slight edge also for those kanji elements whose reading frequency is common
        # (in contrast to those entries for which both kanji/kana readings are uncommon)
        if elem_freq[keb] == 99 and min_r_freq < 99:
            elem_freq[keb] -= 1

    # process senses
    flat_pos_set = set()
    s_elems = elem.findall('sense')
    for s_ele in s_elems:
        pos_elems = s_ele.findall('pos')
        gloss_list  = []
        pos_list = []
        for pos_elem in pos_elems:
            pos = pos_elem.text
            if pos not in jmdict_class_list:
                jmdict_class_list.append(pos)
                pos_list_updated = True
            cl = int(jmdict_class_list.index(pos))
            pos_list.append(cl)
            flat_pos_set.update([cl])

        gl_elems = s_ele.findall('gloss')
        for gl_elem in gl_elems:
            gloss_list.append(gl_elem.text)
        s_inf_elem = s_ele.find('ent_seq')
        if s_inf_elem is not None:
            gloss_list.append('(%s)' % s_inf_elem.text)
        pos_list_per_sense.append(pos_list)
        gloss_list_per_sense.append(gloss_list)

    # create single kanji verb/adjective lookup table
    for keb in kanji_elements:
        k = keb[0]
        if len(keb) > 1 and is_cjk(k) and num_cjk(keb) == 1:
            if jmdict_adj_i_class in flat_pos_set:
                if k not in _single_kanji_adjectives:
                    _single_kanji_adjectives[k] = [ent_seq]
                else:
                    _single_kanji_adjectives[k].append(ent_seq)
            if len(flat_pos_set.intersection(_jmdict_verb_pos_set))>1:
                if k not in _single_kanji_verbs:
                    _single_kanji_verbs[k] = [ent_seq]
                else:
                    _single_kanji_verbs[k].append(ent_seq)

    k_list = [{'t':k, 'f':elem_freq[k],'p':elem_pri_elems[k]} for k in kanji_elements]
    r_list = [{'t':r, 'f':elem_freq[r],'p':elem_pri_elems[r]} for r in readings]
    s_list = [{'gl':gloss_list_per_sense[i], 'pl':pos_list_per_sense[i]} for i in range(len(gloss_list_per_sense))]
    entry = {'_id':ent_seq,'kl':k_list,'rl':r_list,'sl':s_list}


    batch.append(entry)
    if len(batch)>10000:
        count += len(batch)
        database["entries"].insert_many(batch)
        batch = []
        print(count)
    
if len(batch)>0:
    database["entries"].insert_many(batch)
    count += len(batch)
    batch = []

print("Wrote %d entries" % (count))
time2 = int(time.time())
print("Converted in %d seconds" % (time2-time1))

########### Lookup tables for kanji adjectives and verbs

database["ska_lookup"].drop()
print("Writing single kanji adjectives lookup tables")
batch = [{'_id':k,'seqs':seqs} for k,seqs in _single_kanji_adjectives.items()]
database["ska_lookup"].insert_many(batch)
print("Wrote %d entries" % (len(batch)))

database["skv_lookup"].drop()
print("Writing single kanji verbs lookup tables")
batch = [{'_id':k,'seqs':seqs} for k,seqs in _single_kanji_verbs.items()]
database["skv_lookup"].insert_many(batch)
print("Wrote %d entries" % (len(batch)))


################################ JMNEDICT ###############

print("Loading JMnedict...")
import xml.etree.ElementTree as ET
tree = ET.parse(original_jmnedict_file)
root = tree.getroot()

print("Parsing XML...")
entries = root.findall('entry')

print("Converting %d entries..." % len(entries))
count = 0
batch = []

for elem in entries:
    ent_seq = None
    readings = []
    kanji_elements = []

    elem_freq = dict()
    elem_pri_elems = dict()

    ent_seq = elem.find('ent_seq').text

    pri_dict = {'spec1':99}

    r_elems = elem.findall('r_ele')
    for r_elem in r_elems:
        reb_elem = r_elem.find('reb')
        reb = reb_elem.text
        readings.append(reb)

        if reb not in reading_element_seq:
            reading_element_seq[reb] = [ent_seq]
        else:
            reading_element_seq[reb].append(ent_seq)

        elem_freq[reb] = 100 # default
        elem_pri_elems[reb] = []
        r_pri_els = r_elem.findall('re_pri')

        for r_pri_el in r_pri_els:
            pr = r_pri_el.text
            if pr in pri_dict:
                elem_pri_elems[reb].append(pr)
                #freq = pri_dict[pr]
            else:
                print("Unknown priority element %s on seq %s" % (pr,ent_seq))

    k_elems = elem.findall('k_ele')
    for k_elem in k_elems:
        keb_elem = k_elem.find('keb')
        keb = keb_elem.text
        kanji_elements.append(keb)

        if keb not in kanji_element_seq:
            kanji_element_seq[keb] = [ent_seq]
        else:
            kanji_element_seq[keb].append(ent_seq)

        elem_freq[keb] = 100 # default
        elem_pri_elems[keb] = []
        k_pri_els = k_elem.findall('ke_pri')

        for k_pri_el in k_pri_els:
            pr = k_pri_el.text
            if pr in pri_dict:
                elem_pri_elems[keb].append(pr)
                #freq = pri_dict[pr]
            else:
                print("Unknown priority element %s on seq %s" % (pr,ent_seq))

    trans_elem = elem.find('trans')
    trans_det_elems = trans_elem.findall('trans_det')
    gloss_list = []
    pos_list = []
    for trans_det_elem in trans_det_elems:
        gloss_list.append(trans_det_elem.text)
        pos_list.append(jmdict_noun_class)

    k_list = [{'t':k, 'f':elem_freq[k],'p':elem_pri_elems[k]} for k in kanji_elements]
    r_list = [{'t':r, 'f':elem_freq[r],'p':elem_pri_elems[r]} for r in readings]
    # for JMNedict there is only 1 sense per entry
    s_list = [{'gl':gloss_list, 'pl':pos_list}]
    entry = {'_id':ent_seq,'kl':k_list,'rl':r_list,'sl':s_list}

    batch.append(entry)
    if len(batch)>10000:
        count += len(batch)
        database["entries"].insert_many(batch)
        batch = []
        print(count)
    
if len(batch)>0:
    database["entries"].insert_many(batch)
    count += len(batch)
    batch = []

print("Wrote %d entries" % (len(entries)))

######## COMMON LOOKUP TABLES ############

database["ke_lookup"].drop()
print("Writing kanji element lookup tables")
batch = []
count = 0
for k,seqs in kanji_element_seq.items():
    batch.append({'_id':k,'seqs':seqs})
    if len(batch)>10000:
        database["ke_lookup"].insert_many(batch)
        count += len(batch)
        print(count)
        batch = []
if len(batch)>0:
    database["ke_lookup"].insert_many(batch)


database["re_lookup"].drop()
print("Writing reading element lookup tables")
batch = []
for r,seqs in reading_element_seq.items():
    batch.append({'_id':r,'seqs':seqs})
    if len(batch)>10000:
        database["re_lookup"].insert_many(batch)
        count += len(batch)
        print(count)        
        batch = []
if len(batch)>0:
    database["re_lookup"].insert_many(batch)
