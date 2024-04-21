import fugashi
from helper import *
from jp_parser_helper import *
from jp_parser import *
import sys
import argparse

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



parser = argparse.ArgumentParser(
    prog="jmdict_tool",
    description="JMDict search tool",
)

#parser.add_parser('analyze', help='Do comprehension analysis per title')
parser.add_argument('--exact', '-e', action='store_true', help='Require exact match')
parser.add_argument('--part-of-speech', '-pos', nargs='?', type=str, default=None, help='Filter entries with this part of speech code')
parser.add_argument('keyword', nargs='?', type=str, default='', help='search term')

args = vars(parser.parse_args())

term = args['keyword']
force_exact = args['exact']
"""
if len(sys.argv)>1:
    if sys.argv[1] == '-e':
        term = sys.argv[2]
        force_exact = True
    elif sys.argv[1] == '-pos':
        target_pos = sys.argv[2]
        term = ''
        force_exact = False
    else:
        term = sys.argv[1]
else:
    force_exact = False
    term = ''
    target_pos = 'aux-v'
"""

if args['part_of_speech'] is not None:
    if args['part_of_speech'] in jmdict_parts_of_speech_codes:
        target_class = jmdict_class_list.index(jmdict_parts_of_speech_codes[args['part_of_speech']])
    else:
        print("POS %s not found! Select from this list:" % args['part_of_speech'])
        for pos,expl in jmdict_parts_of_speech_codes.items():
            print("%s\t%s" % (pos,expl))
        exit(1)
else:
    target_class = None

def try_from_set(term, jmdict_set, try_len, results, result_seq_set):
    for key in jmdict_set[try_len].keys():
        if term in key:
            seqs = jmdict_set[try_len][key]
            for seq in seqs:
                #e = jmdict_kanji_elements
                #s = jmdict_kanji_element_seq
                cll = get_flat_class_list_by_seq(seq)
                if target_class is None or target_class in cll:
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
    k_elem_freq = ["%s(%d)" % (elem,get_frequency_by_seq_and_word(seq,elem)) for elem in kanji_elements]
    r_elem_freq = ["%s(%d)" % (elem,get_frequency_by_seq_and_word(seq,elem)) for elem in readings]
    k_elems = ' '.join(k_elem_freq)
    r_elems = ' '.join(r_elem_freq)
    if k_elems != '':
        r_elems = '(' + r_elems + ')'
    
    print("%s %s %s" % (seq, k_elems.ljust(8), r_elems.ljust(8)))
    for i, (cl_list, meanings) in enumerate(zip(cl_list_per_sense, meanings_per_sense)):
        print("\t\t%d# %s" % (i,meanings))
        for cl in cl_list:
            cl_name = jmdict_class_list[cl]
            pos_code = get_jmdict_pos_code(cl)
            print("\t\t\t%s (%s)" % (cl_name,pos_code))

print("Total %d matches" % len(results))


