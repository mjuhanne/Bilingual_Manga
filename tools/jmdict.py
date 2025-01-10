from helper import base_dir, has_cjk, is_cjk, num_cjk, is_katakana_word, katakana_to_hiragana
import json
import time
import pickle
import os

jmdict_data = None

jmdict_file = base_dir + "lang/JMdict_e_s.tsv"
jmdict_with_meanings_file = base_dir + "lang/JMdict_e_m.tsv"
jmnedict_file = base_dir + "lang/JMnedict_e.tsv"

jmdict_with_meanings_pickle_file = base_dir + "lang/JMdict_e_m.pickle"
jmdict_pickle_file = base_dir + "lang/JMdict_e_s.pickle"

# JMDict Parts of Speech (classes)
# DO NOT CHANGE THE ORDER
jmdict_class_list = [
    # these are our modifications.
    #'non_jp_char',
    #'alphanum',
    #'punctuation marks 補助記号',
    "common verb class",
    "common noun class",
    "_reserved_",
    # These are from JMdict. Sorted by frequency in descending order
    'noun (common) (futsuumeishi)', 
    'expressions (phrases, clauses, etc.)', 
    'adjectival nouns or quasi-adjectives (keiyodoshi)', 
    'Ichidan verb', 
    'adverb (fukushi)', 
    "nouns which may take the genitive case particle 'no'", 
    "Godan verb with 'ru' ending", "Godan verb with 'su' ending", 
    'adjective (keiyoushi)', "Godan verb with 'ku' ending", 
    'interjection (kandoushi)', "Godan verb with 'mu' ending", 
    'noun or verb acting prenominally', "Godan verb with 'u' ending", 
    'suffix', "adverb taking the 'to' particle", "'taru' adjective", 
    'suru verb - special class', 'pronoun', 'noun, used as a suffix', 
    'prefix', 'particle', 'conjunction', "Godan verb with 'tsu' ending", 
    'noun or participle which takes the aux. verb suru', 'counter', 
    'pre-noun adjectival (rentaishi)', "Godan verb with 'gu' ending", 
    'Ichidan verb - zuru verb (alternative form of -jiru verbs)', 
    'auxiliary verb', 'numeric', 'noun, used as a prefix', 
    "Godan verb with 'bu' ending", 'suru verb - included', 'auxiliary', 
    'Godan verb - Iku/Yuku special class', 
    "Nidan verb (lower class) with 'mu' ending (archaic)", 
    "'ku' adjective (archaic)", 'su verb - precursor to the modern suru', 
    'unclassified', "Yodan verb with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'dzu' ending (archaic)", 
    "Yodan verb with 'ku' ending (archaic)", 'archaic/formal form of na-adjective', 
    'adjective (keiyoushi) - yoi/ii class', "Yodan verb with 'su' ending (archaic)", 
    "Godan verb with 'nu' ending", "Yodan verb with 'hu/fu' ending (archaic)", 
    "Godan verb with 'u' ending (special class)", 'Kuru verb - special class', 
    'Godan verb - -aru special class', 'copula', "'shiku' adjective (archaic)", 
    'irregular ru verb, plain form ends with -ri', 
    "Godan verb with 'ru' ending (irregular verb)", 
    "Yodan verb with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'hu/fu' ending (archaic)", 
    "Nidan verb (lower class) with 'ku' ending (archaic)", 
    "Nidan verb (lower class) with 'tsu' ending (archaic)", 
    'intransitive verb', "Nidan verb (lower class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'yu' ending (archaic)", 
    "Nidan verb (upper class) with 'yu' ending (archaic)", 
    'auxiliary adjective', 'irregular nu verb', 
    "Nidan verb (upper class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'su' ending (archaic)", 
    "Yodan verb with 'mu' ending (archaic)", 
    "Nidan verb with 'u' ending (archaic)", 
    "Nidan verb (upper class) with 'bu' ending (archaic)", 
    "Nidan verb (lower class) with 'nu' ending (archaic)", 
    'Ichidan verb - kureru special class', 
    "Nidan verb (upper class) with 'hu/fu' ending (archaic)", 
    'verb unspecified', "Nidan verb (upper class) with 'ru' ending (archaic)", 
    "Yodan verb with 'gu' ending (archaic)", "Yodan verb with 'bu' ending (archaic)", 
    "Nidan verb (upper class) with 'ku' ending (archaic)", 
    "Nidan verb (upper class) with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'zu' ending (archaic)", 
    "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)", 
    'transitive verb'
]

jmdict_parts_of_speech_codes = {
'adj-f': "noun or verb acting prenominally",
'adj-i': "adjective (keiyoushi)",
'adj-ix': "adjective (keiyoushi) - yoi/ii class",
'adj-kari': "'kari' adjective (archaic)",
'adj-ku': "'ku' adjective (archaic)",
'adj-na': "adjectival nouns or quasi-adjectives (keiyodoshi)",
'adj-nari': "archaic/formal form of na-adjective",
'adj-no': "nouns which may take the genitive case particle 'no'",
'adj-pn': "pre-noun adjectival (rentaishi)",
'adj-shiku': "'shiku' adjective (archaic)",
'adj-t': "'taru' adjective",
'adv': "adverb (fukushi)",
'adv-to': "adverb taking the 'to' particle",
'aux': "auxiliary",
'aux-adj': "auxiliary adjective",
'aux-v': "auxiliary verb",
'conj': "conjunction",
'cop': "copula",
'ctr': "counter",
'exp': "expressions (phrases, clauses, etc.)",
'int': "interjection (kandoushi)",
'n': "noun (common) (futsuumeishi)",
'n-adv': "adverbial noun (fukushitekimeishi)",
'n-pr': "proper noun",
'n-pref': "noun, used as a prefix",
'n-suf': "noun, used as a suffix",
'n-t': "noun (temporal) (jisoumeishi)",
'num': "numeric",
'pn': "pronoun",
'pref': "prefix",
'prt': "particle",
'suf': "suffix",
'unc': "unclassified",
'v-unspec': "verb unspecified",
'v1': "Ichidan verb",
'v1-s': "Ichidan verb - kureru special class",
'v2a-s': "Nidan verb with 'u' ending (archaic)",
'v2b-k': "Nidan verb (upper class) with 'bu' ending (archaic)",
'v2b-s': "Nidan verb (lower class) with 'bu' ending (archaic)",
'v2d-k': "Nidan verb (upper class) with 'dzu' ending (archaic)",
'v2d-s': "Nidan verb (lower class) with 'dzu' ending (archaic)",
'v2g-k': "Nidan verb (upper class) with 'gu' ending (archaic)",
'v2g-s': "Nidan verb (lower class) with 'gu' ending (archaic)",
'v2h-k': "Nidan verb (upper class) with 'hu/fu' ending (archaic)",
'v2h-s': "Nidan verb (lower class) with 'hu/fu' ending (archaic)",
'v2k-k': "Nidan verb (upper class) with 'ku' ending (archaic)",
'v2k-s': "Nidan verb (lower class) with 'ku' ending (archaic)",
'v2m-k': "Nidan verb (upper class) with 'mu' ending (archaic)",
'v2m-s': "Nidan verb (lower class) with 'mu' ending (archaic)",
'v2n-s': "Nidan verb (lower class) with 'nu' ending (archaic)",
'v2r-k': "Nidan verb (upper class) with 'ru' ending (archaic)",
'v2r-s': "Nidan verb (lower class) with 'ru' ending (archaic)",
'v2s-s': "Nidan verb (lower class) with 'su' ending (archaic)",
'v2t-k': "Nidan verb (upper class) with 'tsu' ending (archaic)",
'v2t-s': "Nidan verb (lower class) with 'tsu' ending (archaic)",
'v2w-s': "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)",
'v2y-k': "Nidan verb (upper class) with 'yu' ending (archaic)",
'v2y-s': "Nidan verb (lower class) with 'yu' ending (archaic)",
'v2z-s': "Nidan verb (lower class) with 'zu' ending (archaic)",
'v4b': "Yodan verb with 'bu' ending (archaic)",
'v4g': "Yodan verb with 'gu' ending (archaic)",
'v4h': "Yodan verb with 'hu/fu' ending (archaic)",
'v4k': "Yodan verb with 'ku' ending (archaic)",
'v4m': "Yodan verb with 'mu' ending (archaic)",
'v4n': "Yodan verb with 'nu' ending (archaic)",
'v4r': "Yodan verb with 'ru' ending (archaic)",
'v4s': "Yodan verb with 'su' ending (archaic)",
'v4t': "Yodan verb with 'tsu' ending (archaic)",
'v5aru': "Godan verb - -aru special class",
'v5b': "Godan verb with 'bu' ending",
'v5g': "Godan verb with 'gu' ending",
'v5k': "Godan verb with 'ku' ending",
'v5k-s': "Godan verb - Iku/Yuku special class",
'v5m': "Godan verb with 'mu' ending",
'v5n': "Godan verb with 'nu' ending",
'v5r': "Godan verb with 'ru' ending",
'v5r-i': "Godan verb with 'ru' ending (irregular verb)",
'v5s': "Godan verb with 'su' ending",
'v5t': "Godan verb with 'tsu' ending",
'v5u': "Godan verb with 'u' ending",
'v5u-s': "Godan verb with 'u' ending (special class)",
#'v5uru': "Godan verb - Uru old class verb (old form of Eru)",
'vi': "intransitive verb",
'vk': "Kuru verb - special class",
'vn': "irregular nu verb",
'vr': "irregular ru verb, plain form ends with -ri",
'vs': "noun or participle which takes the aux. verb suru",
'vs-c': "su verb - precursor to the modern suru",
'vs-i': "suru verb - included",
'vs-s': "suru verb - special class",
'vt': "transitive verb",
'vz': "Ichidan verb - zuru verb (alternative form of -jiru verbs)",
'gikun': "gikun (meaning as reading) or jukujikun (special kanji reading)",
'ik': "word containing irregular kana usage",
'ok': "out-dated or obsolete kana usage",
'rk': "rarely used kana form",
'sk': "search-only kana form",
}

#jmdict_noun_class = jmdict_class_list.index('noun (common) (futsuumeishi)')
jmdict_prefix_class = jmdict_class_list.index('prefix')
jmdict_suffix_class = jmdict_class_list.index('suffix')
jmdict_noun_as_suffix_class = jmdict_class_list.index('noun, used as a suffix')

jmdict_prenominal_class = jmdict_class_list.index('noun or verb acting prenominally')

jmdict_suru_verb_class = jmdict_class_list.index('suru verb - included')
jmdict_godan_ru_i_verb_class = jmdict_class_list.index("Godan verb with 'ru' ending (irregular verb)")

jmdict_adjectival_noun_class = jmdict_class_list.index('adjectival nouns or quasi-adjectives (keiyodoshi)')
jmdict_adj_i_class = jmdict_class_list.index('adjective (keiyoushi)')
jmdict_adj_ii_class = jmdict_class_list.index('adjective (keiyoushi) - yoi/ii class')
jmdict_adj_pn_class = jmdict_class_list.index('pre-noun adjectival (rentaishi)')

jmdict_pronoun_class = jmdict_class_list.index('pronoun')

jmdict_interjection_class = jmdict_class_list.index('interjection (kandoushi)')

jmdict_expression_class = jmdict_class_list.index('expressions (phrases, clauses, etc.)')

jmdict_adverb_class = jmdict_class_list.index('adverb (fukushi)')
jmdict_adverb_to_class = jmdict_class_list.index("adverb taking the 'to' particle")

jmdict_conjunction_class = jmdict_class_list.index('conjunction')
jmdict_particle_class = jmdict_class_list.index('particle')

jmdict_numeric_class = jmdict_class_list.index('numeric')
jmdict_counter_class = jmdict_class_list.index('counter')

jmdict_aux_adj_class = jmdict_class_list.index('auxiliary adjective')
jmdict_auxiliary_class = jmdict_class_list.index('auxiliary')

jmdict_auxiliary_verb_class = jmdict_class_list.index('auxiliary verb')

jmdict_adj_no_class = jmdict_class_list.index("nouns which may take the genitive case particle 'no'")

jmdict_noun_class = jmdict_class_list.index("noun (common) (futsuumeishi)")

particles = [
    '1469800:の',
    '2029010:を',
    '2028980:で',
    '2028990:に',
    '2028940:も',
    '2028920:は',
    '2215430:には',
    '2028930:が',
    '1008490:と', 
    '1002980:から', 
    '2028970:か',
    '1525680:まで',
]

# create combined verb and noun classes for easier lookup
_jmdict_verb_pos_list = []
for cl in jmdict_class_list:
    idx = jmdict_class_list.index(cl)
    if 'adverb' not in cl:
        if 'verb' in cl:
            _jmdict_verb_pos_list.append(idx)
_jmdict_verb_pos_set = set(_jmdict_verb_pos_list)


pos_code_by_class = dict()
for i,jmdict_class_expl in enumerate(jmdict_class_list):
    for pos_code, cl_expl in jmdict_parts_of_speech_codes.items():
        if jmdict_class_expl == cl_expl:
            pos_code_by_class[i] = pos_code

def get_jmdict_pos_code(jmdict_class):
    if jmdict_class in pos_code_by_class:
        return pos_code_by_class[jmdict_class]
    return jmdict_class

def get_jmdict_class_by_pos_code(pos_code):
    if pos_code in jmdict_parts_of_speech_codes:
        return jmdict_class_list.index(jmdict_parts_of_speech_codes[pos_code])
    raise Exception("No POS code %s" % pos_code)

def jmdict_add_pos(pos_code,explanation):
    jmdict_parts_of_speech_codes[pos_code] = explanation
    jmdict_class_list.append(explanation)
    pos_code_by_class[ jmdict_class_list.index(explanation) ] = pos_code

def get_jmdict_kanji_element_set():
    return jmdict_data['kanji_elements_set_by_len'], jmdict_data['kanji_element_seq'], jmdict_data['max_kanji_element_len']

def get_jmdict_reading_set():
    return jmdict_data['readings_set_by_len'], jmdict_data['reading_seq'], jmdict_data['max_reading_len']

def is_jmnedict(seq):
    return seq >= 5000000 and seq <= 10000000

def search_sequences_by_word(word, only_jmdict=True):
    if len(word)>jmdict_data['max_kanji_element_len'] or len(word)>jmdict_data['max_reading_len']:
        return []
    seqs = []
    if word in jmdict_data['kanji_element_seq'][len(word)]:
        seqs = jmdict_data['kanji_element_seq'][len(word)][word]
    else:
        if word in jmdict_data['reading_seq'][len(word)]:
            seqs = jmdict_data['reading_seq'][len(word)][word]
    if only_jmdict:
        seqs = [seq for seq in seqs if seq > 1000000 and seq < 5000000]
    return seqs

def search_sequences_by_elements(kanji_element,reading):
    k_seqs = []
    if kanji_element != '':
        if kanji_element in jmdict_data['kanji_element_seq'][len(kanji_element)]:
            k_seqs = jmdict_data['kanji_element_seq'][len(kanji_element)][kanji_element]
    if reading == '':
        return k_seqs
    
    r_seqs = []
    if reading != '':
        if reading in jmdict_data['reading_seq'][len(reading)]:
            r_seqs = jmdict_data['reading_seq'][len(reading)][reading]
    if kanji_element == '':
        return r_seqs

    seqs = set(k_seqs).intersection(set(r_seqs))
    return seqs

def get_flat_class_list_by_seq(seq):
    return jmdict_data['flat_class_list'][seq]

def get_class_list_by_seq(seq):
    return jmdict_data['class_list_per_sense'][seq]

def get_combined_seq_frequency(seq):
    raise Exception("TODO")
    return min(_kanji_element_freq[seq],_reading_freq[seq])

def get_frequency_by_seq_and_word(seq,word):
    if seq not in jmdict_data['elem_freq']:
        return 100
    if word in jmdict_data['elem_freq'][seq]:
        return jmdict_data['elem_freq'][seq][word]
    if is_katakana_word(word):
        hw = katakana_to_hiragana(word)
        if hw in jmdict_data['elem_freq'][seq]:
            return jmdict_data['elem_freq'][seq][hw]
    return 100

def get_kanji_element_freq(seq):
    raise Exception("TODO")
    return _kanji_element_freq[seq]

def get_reading_freq(seq):
    raise Exception("TODO")
    return _reading_freq[seq]

def get_meanings_by_sense(seq,sense):
    return jmdict_data['meaning_per_sense'][seq][sense]

def get_sense_meanings_by_seq(seq):
    return jmdict_data['meaning_per_sense'][seq]

def get_kanji_elements_by_seq(seq):
    return jmdict_data['kanji_elements_by_seq'][seq]

def get_readings_by_seq(seq):
    if seq in jmdict_data['readings_by_seq']:
        return jmdict_data['readings_by_seq'][seq]
    return []

def get_common_priority_tags(seq):
    raise Exception("TODO")
    return _common_pri_tags[seq]

def get_kanji_element_priority_tags(seq):
    raise Exception("TODO")
    return _k_pri_tags[seq]

def get_reading_priority_tags(seq):
    raise Exception("TODO")
    return _r_pri_tags[seq]

def get_priority_tags(seq,word):
    return jmdict_data['pri_tags'][seq][word]

def get_verb_seqs_for_single_kanji(word):
    if word[0] in jmdict_data['single_kanji_verbs']:
        return jmdict_data['single_kanji_verbs'][word[0]]
    return []

def get_adjective_seqs_for_single_kanji(word):
    if word[0] in jmdict_data['single_kanji_adjectives']:
        return jmdict_data['single_kanji_adjectives'][word[0]]
    return []

def jmdict_add_custom_word(seq,k_elem,r_elem,meaning,cl,freq):
    global jmdict_data
    l = len(k_elem)
    if k_elem not in jmdict_data['kanji_element_seq'][l]:
        jmdict_data['kanji_element_seq'][l][k_elem] = [seq]
    else:
        jmdict_data['kanji_element_seq'][l][k_elem].append(seq)
    jmdict_data['kanji_elements_set_by_len'][len(k_elem)].update([k_elem])
    l = len(r_elem)
    if r_elem not in jmdict_data['reading_seq'][l]:
        jmdict_data['reading_seq'][l][r_elem] = [seq]
    else:
        jmdict_data['reading_seq'][l][r_elem].append(seq)
    jmdict_data['readings_set_by_len'][len(r_elem)].update([r_elem])
    jmdict_data['meaning_per_sense'][seq] = [[meaning]]
    jmdict_data['pri_tags'][seq] = []
    jmdict_data['flat_class_list'][seq] = [cl]
    jmdict_data['class_list_per_sense'][seq] = [[cl]]
    jmdict_data['elem_freq'][seq] = {k_elem:freq, r_elem:freq}
    jmdict_data['kanji_elements_by_seq'][seq] = [k_elem]
    jmdict_data['readings_by_seq'][seq] = [r_elem]


def load_jmdict(load_meanings=False, verbose=True):
    global jmdict_data
    if jmdict_data is not None:
        return
    
    t1 = int(time.time())

    if verbose:
        print("Loading JMdict..")
    if load_meanings:
        if os.path.exists(jmdict_with_meanings_pickle_file):
            with open(jmdict_with_meanings_pickle_file,"rb") as f:
                jmdict_data = pickle.load(f)
        else:
            fn = jmdict_with_meanings_file
    else:
        if os.path.exists(jmdict_pickle_file):
            with open(jmdict_pickle_file,"rb") as f:
                jmdict_data = pickle.load(f)
        else:
            fn =jmdict_file

    if jmdict_data is not None:
        t2 = int(time.time())
        if verbose:
            print("Read %d JMdict entries in %d seconds" % (len(jmdict_data['readings_by_seq']),t2-t1))
        return

    o_f = open(fn,"r",encoding="utf-8")
    lines = o_f.readlines()
    o_f.close()

    jmdict_data = {}
    jmdict_data['readings_by_seq'] = dict()
    jmdict_data['readings_set_by_len'] = dict()
    jmdict_data['reading_seq'] = dict()
    jmdict_data['elem_freq'] = dict()
    jmdict_data['kanji_elements_by_seq'] = dict()
    jmdict_data['kanji_elements_set_by_len'] = dict()
    jmdict_data['kanji_element_seq'] = dict()
    jmdict_data['class_list_per_sense'] = dict()
    jmdict_data['flat_class_list'] = dict()
    jmdict_data['meaning_per_sense'] = dict()
    jmdict_data['max_reading_len'] = 0
    jmdict_data['max_kanji_element_len'] = 0
    jmdict_data['pri_tags'] = dict()
    jmdict_data['single_kanji_adjectives'] = dict()
    jmdict_data['single_kanji_verbs'] = dict()

    for line in lines:
        d = line.split('\t')
        d[-1] = d[-1].strip()
        seq = int(d[0])

        l_l = json.loads(d[3])
        jmdict_data['class_list_per_sense'][seq] = l_l
        # flatten the class list for faster lookup
        flat_cll = list(set([x for sense_cl_l in l_l for x in sense_cl_l]))
        jmdict_data['flat_class_list'][seq] = flat_cll
        cl_set = set(flat_cll)

        jmdict_data['elem_freq'][seq] = dict()
        k_elems = d[1].split(',')
        k_elem_freq = d[4].split(',')
        jmdict_data['kanji_elements_by_seq'][seq] = [] 
        for k_elem,k_freq in zip(k_elems,k_elem_freq):
            if k_elem != '':
                l = len(k_elem)
                if l not in jmdict_data['kanji_element_seq']:
                    jmdict_data['kanji_element_seq'][l] = dict()
                if k_elem not in jmdict_data['kanji_element_seq'][l]:
                    jmdict_data['kanji_element_seq'][l][k_elem] = [seq]
                else:
                    jmdict_data['kanji_element_seq'][l][k_elem].append(seq)
                if l > jmdict_data['max_kanji_element_len']:
                    jmdict_data['max_kanji_element_len'] = l
                jmdict_data['kanji_elements_by_seq'][seq].append(k_elem)
                jmdict_data['elem_freq'][seq][k_elem] = int(k_freq)

                k = k_elem[0]
                if l > 1 and is_cjk(k) and num_cjk(k_elem) == 1:
                    if jmdict_adj_i_class in cl_set:
                        if k not in jmdict_data['single_kanji_adjectives']:
                            jmdict_data['single_kanji_adjectives'][k] = [seq]
                        else:
                            jmdict_data['single_kanji_adjectives'][k].append(seq)
                    if len(cl_set.intersection(_jmdict_verb_pos_set))>1:
                        if k not in jmdict_data['single_kanji_verbs']:
                            jmdict_data['single_kanji_verbs'][k] = [seq]
                        else:
                            jmdict_data['single_kanji_verbs'][k].append(seq)

        r_elems = d[2].split(',')
        r_elem_freq = d[5].split(',')
        jmdict_data['readings_by_seq'][seq] = [] 
        for r_elem,r_freq in zip(r_elems,r_elem_freq):
            l = len(r_elem)
            if l not in jmdict_data['reading_seq']:
                jmdict_data['reading_seq'][l] = dict()
            if r_elem not in jmdict_data['reading_seq'][l]:
                jmdict_data['reading_seq'][l][r_elem] = [seq]
            else:
                jmdict_data['reading_seq'][l][r_elem].append(seq)
            if l > jmdict_data['max_reading_len']:
                jmdict_data['max_reading_len'] = l
            jmdict_data['readings_by_seq'][seq].append(r_elem)
            jmdict_data['elem_freq'][seq][r_elem] = int(r_freq)

        jmdict_data['pri_tags'][seq] = json.loads(d[6])

        if load_meanings:
            jmdict_data['meaning_per_sense'][seq] = json.loads(d[7])

    if verbose:
        print("Loading JMnedict..")
    o_f = open(jmnedict_file,"r",encoding="utf-8")
    lines = o_f.readlines()
    o_f.close()

    for line in lines:
        d = line.split('\t')
        d[-1] = d[-1].strip()
        seq = int(d[0])

        l_l = json.loads(d[3])

        jmdict_data['elem_freq'][seq] = dict()
        jmdict_data['flat_class_list'][seq] = [jmdict_noun_class]
        jmdict_data['class_list_per_sense'][seq] = [[jmdict_noun_class]]
        k_elems = d[1].split(',')
        freq = d[3]
        jmdict_data['kanji_elements_by_seq'][seq] = [] 
        for k_elem in k_elems:
            if k_elem != '':
                l = len(k_elem)
                if l not in jmdict_data['kanji_element_seq']:
                    jmdict_data['kanji_element_seq'][l] = dict()
                if k_elem not in jmdict_data['kanji_element_seq'][l]:
                    jmdict_data['kanji_element_seq'][l][k_elem] = [seq]
                else:
                    jmdict_data['kanji_element_seq'][l][k_elem].append(seq)
                if l > jmdict_data['max_kanji_element_len']:
                    jmdict_data['max_kanji_element_len'] = l
                jmdict_data['kanji_elements_by_seq'][seq].append(k_elem)
                jmdict_data['elem_freq'][seq][k_elem] = int(freq)

        r_elems = d[2].split(',')
        jmdict_data['readings_by_seq'][seq] = []
        for r_elem in r_elems:
            l = len(r_elem)
            if l not in jmdict_data['reading_seq']:
                jmdict_data['reading_seq'][l] = dict()
            if r_elem not in jmdict_data['reading_seq'][l]:
                jmdict_data['reading_seq'][l][r_elem] = [seq]
            else:
                jmdict_data['reading_seq'][l][r_elem].append(seq)
            if l > jmdict_data['max_reading_len']:
                jmdict_data['max_reading_len'] = l
            jmdict_data['readings_by_seq'][seq].append(r_elem)
            jmdict_data['elem_freq'][seq][r_elem] = int(freq)

        jmdict_data['meaning_per_sense'][seq] = [json.loads(d[4])] # jmnedict contains only 1 sense

    # make sure every length has at least empty entry. 
    # Also create sets consisting of just a word for faster lookup
    for l in range(jmdict_data['max_kanji_element_len']+1):
        if l not in jmdict_data['kanji_element_seq']:
            jmdict_data['kanji_element_seq'][l] = dict()
        jmdict_data['kanji_elements_set_by_len'][l] = set(jmdict_data['kanji_element_seq'][l].keys())
    for l in range(jmdict_data['max_reading_len']+1):
        if l not in jmdict_data['reading_seq']:
            jmdict_data['reading_seq'][l] = dict()
        jmdict_data['readings_set_by_len'][l] = set(jmdict_data['reading_seq'][l].keys())

    t2 = int(time.time())

    if load_meanings:
        with open(jmdict_with_meanings_pickle_file,"wb") as f:
            pickle.dump(jmdict_data, f)
    else:
        with open(jmdict_pickle_file,"wb") as f:
            pickle.dump(jmdict_data, f)

    if verbose:
        print("Read %d JMdict entries in %d seconds" % (len(lines),t2-t1))


# Expand the word id reference into a tuple of  seq + sense list + word: (seq,[senses],word)
#  For example "2153760/0:者" results in (2153760,[0],者) whereas
# ALL_SENSES is denoted with a reference without slash+sense index number
# so return all the senses: (2153760,[0,1,...,n],者)
def expand_word_id(word_id):
    s1 = word_id.split(':')
    word = s1[1]
    s = s1[0].split('/')
    seq = int(s[0])
    if len(s) > 1:
        senses = [int(s[1])]
    else:
        senses = []
        for i in range(len(get_class_list_by_seq(seq))):
            senses.append((i))
    return (seq,senses,word)


