import fugashi
from helper import *
from jp_parser_helper import *
from jp_parser import *
import sys

parser = fugashi.Tagger('')

verb_conjugations = dict()
adj_conjugations = dict()

results = []
result_seq_set = set()

force_exact = False

load_jmdict(True)
load_conjugations()

kanji_elements_by_seq = dict()
readings_by_seq = dict()

jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len = get_jmdict_kanji_element_set()
jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len = get_jmdict_reading_set()

for l,entries in jmdict_kanji_element_seq.items():
    for elem, seqs in jmdict_kanji_element_seq[l].items():
        for seq in seqs:

            if seq not in kanji_elements_by_seq:
                kanji_elements_by_seq[seq] = [elem]
            else:
                kanji_elements_by_seq[seq].append(elem)

for l,entries in jmdict_reading_seq.items():
    for elem, seqs in jmdict_reading_seq[l].items():
        for seq in seqs:
            if seq not in readings_by_seq:
                readings_by_seq[seq] = [elem]
            else:
                readings_by_seq[seq].append(elem)



if len(sys.argv)>1:
    if sys.argv[1] == '-e':
        term = sys.argv[2]
        force_exact = True
    else:
        term = sys.argv[1]
else:
    force_exact = False
    term = 'サラリ'

def try_from_set(term, jmdict_set, try_len, results, result_seq_set):
    for key in jmdict_set[try_len].keys():
        if term in key:
            seqs = jmdict_set[try_len][key]
            for seq in seqs:
                e = jmdict_kanji_elements
                s = jmdict_kanji_element_seq
                try:
                    kanji_elements = kanji_elements_by_seq[seq]
                except:
                    kanji_elements = []
                readings = readings_by_seq[seq]
                res = (kanji_elements, readings, key,seq)
                if seq not in result_seq_set:
                    results.append(res)
                    result_seq_set.update([seq])
    return 

if force_exact:
    try_from_set(term, jmdict_kanji_element_seq, len(term), results, result_seq_set)
    try_from_set(term, jmdict_reading_seq, len(term), results, result_seq_set)
else:
    try_from_set(term, jmdict_kanji_element_seq, len(term), results, result_seq_set)
    try_from_set(term, jmdict_reading_seq, len(term), results, result_seq_set)
    tlen = len(term)
    while tlen <= jmdict_max_kanji_element_len:
        try_from_set(term, jmdict_kanji_element_seq, tlen, results, result_seq_set)
        tlen += 1

    tlen = len(term)
    while tlen <= jmdict_max_reading_len:
        try_from_set(term, jmdict_reading_seq, tlen, results, result_seq_set)
        tlen += 1


results.reverse()

for kanji_elements, readings, matched_word,seq in results:
    cl_list_per_sense = get_class_list_by_seq(seq) # jmdict_class_list_per_sense[seq]
    meanings_per_sense = get_sense_meanings_by_seq(seq) #) jmdict_meaning_per_sense[seq]
    k_elems = ' '.join(kanji_elements)
    r_elems = ' '.join(readings)
    if k_elems != '':
        r_elems = '(' + r_elems + ')'
    
    print("%s %s %s [F %s/%s]" % (seq, k_elems.ljust(8), r_elems.ljust(8), get_kanji_element_freq(seq), get_reading_freq(seq)))
    for i, (cl_list, meanings) in enumerate(zip(cl_list_per_sense, meanings_per_sense)):
        print("\t\t%d# %s" % (i,meanings))
        for cl in cl_list:
            cl_name = jmdict_class_list[cl]
            pos_code = get_jmdict_pos_code(cl)
            print("\t\t\t%s (%s)" % (cl_name,pos_code))



