from helper import base_dir, bcolors
from jmdict import get_jmdict_pos_code
from jp_parser_structs import *
from jmdict import *

word_flag_to_str = {
    NO_SCANNING : "NO_SCAN",
    START_OF_SCAN_DISABLED : "DIS_START",
    #MERGE_PARTICLE : ''
    DISABLE_ORTHO : "DIS_ORTHO",
}
def flags_to_str(word_flag):
    return ' '.join([word_flag_to_str[key] for key in word_flag_to_str.keys() if word_flag & key])

def pretty_print_lexical_item(item):

    if item.ortho == item.txt:
        ortho = '。'
    else:
        ortho = item.ortho
    cll = item.classes
    cl_str = '/'.join([unidic_class_list[cl] for cl in cll]).ljust(5,'　')
    cl_meaning_str = '/'.join([unidic_class_to_string(cl) for cl in cll])
    #conj_list = ['%s(%s)/%s' % (pos,sfx,conj) for (pos,sfx,conj) in item.conj_details]
    conj_list = ['%s(%s)/%s' % (get_jmdict_pos_code(pos),sfx,conj) for (pos,sfx,conj) in item.conj_details]
    conjugation = ' '.join(conj_list)
    flags = ''
    if item.is_masu:
        flags += 'masu '
    if item.end_of_clause:
        flags += 'EOC '
    unidic_verb_conj = ''
    if verb_class in cll and item.details is not None:
        unidic_verb_conj = item.details[5]

    appendable_alt_forms = [alt_form + '+' for alt_form in item.appendable_alt_forms]
    other_alt_forms = [alt_form for alt_form in item.alt_forms if alt_form not in item.appendable_alt_forms]
    alt_forms = appendable_alt_forms + other_alt_forms
    alt_forms_str = '/'.join(alt_forms)

    if item.color is not None:
        col_start = item.color
        col_end = bcolors.ENDC
    else:
        col_start = ''
        col_end = ''

    print("%s %s%s %s %s%s %s %s %s %s %s" % ( 
        flags_to_str(item.flags).ljust(10), col_start, item.txt.ljust(6,'　'), ortho.ljust(6,'　'), alt_forms_str.ljust(6,'　'), col_end,
        cl_str, cl_meaning_str, flags, unidic_verb_conj, conjugation)
    )

def print_scanning_results(jlines, scores, results, ud_items):
    item_idx = 0
    merged_item_str = ''
    for line,line_scores in zip(jlines,scores):
        for entry,scores in zip(line,line_scores):
            w= next(iter(entry))
            cll =ud_items[item_idx].classes
            cl_str = '/'.join([unidic_class_list[cl] for cl in cll]).ljust(5,'　')
            cl_meaning_str = '/'.join([unidic_class_to_string(cl) for cl in cll])
            print(" %s %s %s" % ( 
                w.ljust(6,'　'), cl_str, cl_meaning_str
                )
            )

            word_id_refs = entry[w]
            if len(word_id_refs) == 0:
                print("\t ** NO WORDS FOUND ** ")
            else:
                word_ids = [ results['word_id_list'][w_id_idx] for w_id_idx in word_id_refs]
                for (word_id,score) in zip(word_ids,scores):
                    (seq,senses,word) = expand_word_id(word_id)
                    reading = get_readings_by_seq(seq)[0]
                    if reading == word:
                        reading = ''
                    if '/' not in word_id:
                        s_ref = '*'
                    else:
                        s_ref = str(senses[0])
                    print("\t\t%d [%d/%s] %s\t[F %s/%s] %s" % (score,seq,s_ref, word, get_kanji_element_freq(seq), get_reading_freq(seq),reading))
                    for i,(sense) in enumerate(senses):
                        meanings = get_meanings_by_sense(seq,sense)
                        if s_ref == '*':
                            count = str(i + 1)+'#'
                        else:
                            count = ''
                        print("\t\t\t%s %s" % (count,meanings))
                        cl_list = get_class_list_by_seq(seq)[sense]
                        for cl in cl_list:
                            print("\t\t\t\t%s" % jmdict_class_list[cl])

            merged_item_str += w
            if merged_item_str in ud_items[item_idx].txt:
                if merged_item_str == ud_items[item_idx].txt:
                    item_idx += 1
                    merged_item_str = ''
                else:
                    # continue using the same lexical item for this text chunk
                    pass
            else:
                raise Exception("programming error!")

