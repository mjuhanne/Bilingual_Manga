import fugashi
from helper import *

parser = fugashi.Tagger('')

jmdict_reading_seq = dict()
jmdict_kanji_element_seq = dict()
jmdict_readings = dict()
jmdict_kanji_elements = dict()
jmdict_pos = dict()
max_jmdict_reading_len = 0
max_jmdict_kanji_element_len = 0

jmdict_file = base_dir + "lang/JMdict_e_s.tsv"


# DO NOT CHANGE THE ORDER
unidic_word_classes = [
    'non_jp_char',
    'alphanum',
    '補助記号',

    '助動詞',
    '助詞',

    '名詞',
    '動詞',
    '接尾辞',
    '副詞',
    '代名詞',
    '形容詞',
    '感動詞',
    '形状詞',
    '接頭辞', # prefix
    '接続詞',
    '連体詞',
    '記号',
    '接頭詞',
    'フィラー',  # failure?
]

verb_class_index = unidic_word_classes.index('動詞')
grammatical_particle_class_index = unidic_word_classes.index('助詞')
noun_class_index = unidic_word_classes.index('名詞')
prefix_class_index = unidic_word_classes.index('接頭辞')
suffix_class_index = unidic_word_classes.index('接尾辞')

# words/characters belonging to these classes are lumped
# as one word with other class members. They aren't saved separately in the unique
# words list but instead are lumped into combined word slot, for examlple
# all sequential alphanumerical characters are saved into LUMPED_ALPHANUM_CHARACTER_INDEX
aux_verb_class_index = unidic_word_classes.index('助動詞')
alphanum_class_index = unidic_word_classes.index('alphanum')
non_jp_char_class_index = unidic_word_classes.index('non_jp_char')
punctuation_mark_class_index = unidic_word_classes.index('補助記号')
# all classes up to this index are lumped together
lumped_class_index = punctuation_mark_class_index

LUMPED_NON_JP_CHARACTER_INDEX = 0
LUMPED_ALPHANUM_CHARACTER_INDEX = 1
LUMPED_AUX_VERB_INDEX = 2
LUMPED_GRAM_PARTICLE_INDEX = 3

jmdict_conjugations = dict()

# some common auxiliary verbs, particles and markings which we ignore for frequency analysis
ignored_classes = [
    '補助記号', # ？
    #'助詞', # Grammatical particles: と, ん, から, の, だけ...
    #'助動詞', # Auxiliary verb: ちゃ, た, ます, てる, ない
    ]

ignored_classes_for_freq = [
    '補助記号', # ？
    '助詞', # Grammatical particles: と, ん, から, の, だけ...
    '助動詞', # Auxiliary verb: ちゃ, た, ます, てる, ない
    'non_jp_char',
    'alphanum',
    ]

# words consisting of these wide characters will be ignored
ignored_full_width_characters = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９％"

def is_all_alpha(word):
    if all(c in ignored_full_width_characters for c in word):
        return True
    if word.isascii() and word.isalnum():
        return True
    return False

def parse_with_fugashi(line):
    results = []
    r = parser.parse(line)
    lines = r.split('\n')
    for r_line in lines:

        result = r_line.split("\t")
        if len(result) == 2:
            w = result[0]
            d = result[1].split(',')
            if len(d)>=8:
                wtype = d[0]
                basic_type = d[8]
                pro = d[9]
                lemma = d[7]
                orth_base = d[10]
                results.append(([w,wtype,basic_type,pro],lemma,orth_base))
            elif len(d)>0:
                wtype = d[0]
                results.append(([w,wtype,'',''],'',''))

    return results


def parse_line_with_unidic(line, kanji_count, lemmas):

    res = parse_with_fugashi(line)
    if len(res)==0 and len(line)>0:
        raise Exception("Couldn't parse '%s'" % line)
        # parser couldn't parse this. 
        return 0,0, [{line:''}]
    
    k_c = 0
    words = []
    word_ortho = []
    word_classes = []
    collected_particles = ''
    previous_class_idx = -1
    for (wr,lemma,orth_base) in res:
        w = wr[0]
        cl = wr[1]

        try:
            class_idx = unidic_word_classes.index(cl)
        except:
            raise Exception("Unknown class %d in word %s" % (cl, w))

        word = ''
        if is_all_alpha(w):
            # for some reason wide numbers and alphabets are parsed as 名詞
            class_idx = alphanum_class_index
            pass
        else:

            if cl not in ignored_classes:
                word = orth_base
                if word == '':
                    # empty base form for some reason. Use the parsed form
                    word = w

                if orth_base != lemma and lemma != '':
                    # save lemmas for those words in which they differ from basic form
                    if '-' not in lemma:
                        if not is_katakana_word(lemma):
                            lemmas[word] = lemma
            
        if previous_class_idx != class_idx and previous_class_idx <= lumped_class_index:
            # word class changed so save previously collected word
            if collected_particles != '':
                words.append(collected_particles)
                word_classes.append(previous_class_idx)
                word_ortho.append(None)
                collected_particles = ''

        if class_idx <= lumped_class_index:
            # when many non-JP characters and puntuation marks are 
            # in sequence we don't want to save them separately
            # but instead lump them together
            collected_particles += w
        else:
            words.append(w)
            word_ortho.append(word)
            word_classes.append(class_idx)


        previous_class_idx = class_idx

    if collected_particles != '':
        words.append(collected_particles)
        word_ortho.append(None)
        word_classes.append(class_idx)

    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1

    words, word_ortho, word_classes = attempt_to_fuse_unidic_conjugations(words, word_ortho, word_classes)
    return k_c, words, word_ortho, word_classes

def greedy_conjugations(pos,words,word_ortho,word_classes):
    if pos == len(words) - 1:
        return 0
    #if words[pos] == 'し':
    if words[pos+1] == 'て':
        return 1
    if word_classes[pos+1] == aux_verb_class_index:
        return 1
    return 0
    

def attempt_to_fuse_unidic_conjugations(words, word_ortho, word_classes):
    # test lumping
    lump = ''
    processed_words = []
    processed_ortho = []
    processed_classes = []
    verb_classes = [verb_class_index, aux_verb_class_index]
    prev_cl = None
    saved_ortho = None
    i = 0
    while i<len(words):
        consumed_particles = 0
        w = words[i]
        cl = word_classes[i]
        if cl == verb_class_index:
            consumed_particles = greedy_conjugations(i,words,word_ortho,word_classes)
        consumed_particles += 1
        if consumed_particles > 1:
            processed_words.append(''.join(words[i:i+consumed_particles]))
        else:
            processed_words.append(words[i])
        processed_ortho.append(word_ortho[i])
        processed_classes.append(word_classes[i])
        i += consumed_particles
    return processed_words, processed_ortho, processed_classes



# this will scan for all the possible dictionary entries in the jmdict set
# (either kanji_elements or readings) using the given list of words 
# and starting at position pos.  
def greedy_jmdict_scanning(words, prevent_start_of_scan, word_ref, word_by_seq, searched_word_sets, start_pos, min_word_len, jmdict_set, jmdict_seq_dict, max_jmdict_len):
    lw = len(words)
    
    cycle_pos = start_pos
    while True:

        i = cycle_pos
        wc = 0
        word_chunk = ''
        if not prevent_start_of_scan[i]:
            while (i + wc < lw) and words[i+wc] is not None:

                word_chunk += words[i+wc]
                wc += 1

                # first check that this chunk hasn't been yet searched for this position
                if word_chunk not in searched_word_sets[i]:
                    wc_l = len(word_chunk)
                    if wc_l >= min_word_len and wc_l <= max_jmdict_len:
                        # then check if the word chunk is in the jmdict_set.. (this is much faster)
                        if word_chunk in jmdict_set[wc_l]:
                            # .. found. Now we can use a bit more time to find the sequence number in the dict
                            for jw, seq in jmdict_seq_dict[wc_l].items():
                                if jw == word_chunk:
                                    word_by_seq[seq] = jw
                                    # add this seq reference for all the encompassing words
                                    for j in range(wc):
                                        word_ref[i+j].append(seq)
                    searched_word_sets[i].add(word_chunk)

        cycle_pos += 1
        if cycle_pos > lw - 1:
            return word_ref


def create_phrase_permutations(words, alternative_forms, index=0):
    phrase = []
    i = index
    permutations = []
    while i<len(alternative_forms):
        if alternative_forms[i] is None:
            phrase.append(words[i])
            i += 1
        else:
            p1 = create_phrase_permutations(words,alternative_forms, i+1)
            for p in p1:
                permutations.append(phrase + [words[i]] + p)
            p2 = create_phrase_permutations(words,alternative_forms, i+1)
            for p in p2:
                permutations.append(phrase + [alternative_forms[i]] + p)
            return permutations
    return [phrase]


def scan_jmdict_for_selected_words( permutated_words, prevent_start_of_scan, word_ref, word_by_seq, searched_kanji_word_set, searched_reading_set):

    greedy_jmdict_scanning(permutated_words, prevent_start_of_scan, word_ref, word_by_seq, searched_kanji_word_set, 0, 1, jmdict_kanji_elements, jmdict_kanji_element_seq, max_jmdict_kanji_element_len)

    for i, seqs in enumerate(word_ref):
        if len(seqs) == 0:
            # look for readings only starting from the word for which kanji_element couldn't be found
            greedy_jmdict_scanning(permutated_words, prevent_start_of_scan, word_ref, word_by_seq, searched_reading_set, i, 2, jmdict_readings, jmdict_reading_seq, max_jmdict_reading_len)
            break
    return word_ref

def attempt_adjective_fuse(i, words, ortho):
    stem = ortho[:-1]
    test =  ''.join(words[i:])
    wlen = len(words)
    tenses = jmdict_conjugations[jmdict_adjective_class_index]
    for t in tenses:
        test2 = stem + t
        if test2 in test:
            # there's a match. find the actual right amount of elements
            test = words[i]
            for k, (w) in enumerate(words[i+1:]):
                test += w
                if test2 == test:
                    return k+1
    return 0

def attempt_to_fuse_conjugations(word_index_ref, words, ortho_list, jmdict_class_list):
    wlen = len(words)
    for i, (w, refs,ortho) in enumerate(zip(words, word_index_ref, ortho_list)):
        for rf in refs:
            if rf > 0:
                # its a word
                cl = jmdict_class_list[rf]
                for c in cl:
                    if c in jmdict_conjugations:
                        if i +1 < wlen:
                            if len(word_index_ref[i+1])==0:
                                # orphan particle
                                if c == jmdict_adjective_class_index:
                                    j = attempt_adjective_fuse(i, words, ortho)
                                    for k in range(j):
                                        # add reference to from particle to the stem
                                        word_index_ref[i+k+1].append(rf)
                                pass


def parse_with_jmdict(unidic_words, unidic_word_ortho, unidic_word_class, 
            jmdict_word_list, jmdict_word_count, jmdict_word_seq, jmdict_word_class_list, 
            word_count_per_unidict_class, 
            #jmdict_phrase_list, jmdict_phrase_count, jmdict_phrase_seq
    ):
    # Construct a word list in basic form. Hide the non-JP characters
    # as well as auxiliary verbs (って, ます..)
    # Example: お願いします -> お + 願う + する
    # Then construct alternative forms of words in order to do more diligent searching.
    # This allows searching with the original forms
    # Example: お願いします -> お + 願い + します
    words = []
    alternative_forms = []
    prevent_start_of_scan = []
    wlen = len(unidic_words)
    for i, w in enumerate(unidic_words):
        cli = unidic_word_class[i]
        if cli < aux_verb_class_index:
            # non-JP character or alphanumeric string
            words.append(None)
            alternative_forms.append(None)
            prevent_start_of_scan.append(True)
        elif cli == grammatical_particle_class_index or cli == suffix_class_index:
            # do not start scaning jmdict from this particle
            # but allow it to be included in other parts
            prevent_start_of_scan.append(True)
            words.append(unidic_words[i])
            alternative_forms.append(None)
        else:
            # verb/noun/adverb etc.. Use the basic form as default and 
            # then add the current form as alternative if possible
            words.append(unidic_word_ortho[i])
            if unidic_words[i] != unidic_word_ortho[i]:
                alternative_forms.append(unidic_words[i])
            else:
                alternative_forms.append(None)
            prevent_start_of_scan.append(False)

    """
    This creates a list of permutations for words/alternative words.
    For example:
        お + 願う + する
        お + 願う + します
        お + 願い + する
        お + 願い + します
    """
    permutations = create_phrase_permutations(words, alternative_forms)
    searched_kanji_word_sets = [set() for x in range(wlen)]
    searched_reading_sets = [set() for x in range(wlen)]
    word_seq_ref = [[] for x in range(len(words))]
    word_by_seq = dict()
    for permutated_words in permutations:
        pos = 0
        scan_jmdict_for_selected_words(permutated_words, prevent_start_of_scan, word_seq_ref, word_by_seq, searched_kanji_word_sets, searched_reading_sets)

    # replace the jmdict seq reference with idx number to the word list
    word_index_ref = []
    idx_ref_count = dict()
    particle_pos_in_word = dict()
    for i, seqs in enumerate(word_seq_ref):
        refs = []
        for seq in seqs:
            try:
                idx = jmdict_word_list.index(word_by_seq[seq])
                jmdict_word_count[idx] += 1
            except:
                jmdict_word_list.append(word_by_seq[seq])
                jmdict_word_seq.append(seq)
                jmdict_word_class_list.append(jmdict_pos[seq])
                jmdict_word_count.append(0)
                idx = len(jmdict_word_list) - 1

            # calculate each particle usage in order to sort them and
            # possibly ignore them if they are not useful (auxiliary verbs or 
            # grammar particles) AND they are isolated
            # (not detected as a part of bigger word)
            if idx not in idx_ref_count:
                idx_ref_count[idx] = 1
            else:
                idx_ref_count[idx] += 1

            particle_pos_in_word[(i,idx)] = idx_ref_count[idx]

            cl_list = jmdict_pos[seq]
            if jmdict_expression_class_index in cl_list:
                # this is a phrase
                # we use negative idx for phrases (just for signaling purposes)
                idx = -idx

            refs.append(idx)
        word_index_ref.append(refs)

    # keep count of word occurrence by class
    # Also remove references from those standalone grammatical particles
    for i,(refs) in enumerate(word_index_ref):
        ud_cl = unidic_word_class[i]
        word_count_per_unidict_class[ud_cl] += 1

        # sort the word/phrase reference by their size
        if len(refs)>1:
            ref_sizes = dict()
            for rf in refs:
                ref_sizes[rf] = idx_ref_count[abs(rf)]
            sorted_refs = dict(sorted(ref_sizes.items(), key=lambda x:x[1], reverse=True))
            word_index_ref[i] = list(sorted_refs.keys())

            if particle_pos_in_word[(i,abs(refs[0]))] != 1:
                # the first reference for this particle is in a word in which
                # it isn't a first particle. Let's see if however it is a first
                # particle in other bigger word so we'd like to prioritize it
                # for example 見てもらう in 様子を見てもらう
                for j, rf in enumerate(refs[1:]):
                    if particle_pos_in_word[(i,abs(rf))] == 1:
                        if idx_ref_count[abs(rf)] > 1:
                            # swap the references
                            rf0 = refs[0]
                            refs[0] = rf
                            refs[j+1] = rf0
                            word_index_ref[i] = refs
                            break

        if ud_cl <= grammatical_particle_class_index:
            new_refs = []
            for rf in refs:
                if rf > 0:
                    if idx_ref_count[rf] == 1:
                        # this particle is isolated in this reference
                        pass
                    else:
                        new_refs.append(rf)
                else:
                        new_refs.append(rf)
            word_index_ref[i] = new_refs
        
    attempt_to_fuse_conjugations(word_index_ref, unidic_words, unidic_word_ortho, jmdict_word_class_list)

    return word_index_ref


def parse_block_with_jmdict(parsed_words, parsed_words_ortho, parsed_word_classes, 
            jmdict_word_list, jmdict_word_count, jmdict_word_seq, jmdict_word_class_list, 
            word_count_per_unidict_class, 
    ):
    # flatten this block (bunch of lines = lists of lists) to make life easier
    unidic_words = [w for x in parsed_words for w in x]
    unidic_word_ortho = [w for x in parsed_words_ortho for w in x]
    unidic_word_class = [w for x in parsed_word_classes for w in x]

    word_index_ref = parse_with_jmdict(
        unidic_words, unidic_word_ortho, unidic_word_class, 
        jmdict_word_list, jmdict_word_count, jmdict_word_seq,  jmdict_word_class_list,
        word_count_per_unidict_class, 
    )

    # re-assemble this block back into lines (list of lists)
    i = 0
    block_word_ref = []
    for line in parsed_words:
        new_line = []
        for y in line:
            refs = word_index_ref[i]
            w = unidic_words[i]
            new_line.append({w:refs})
            i += 1
        block_word_ref.append(new_line)
    
    return block_word_ref


def load_conjugations():

    def sort_by_len(orig_list):
        new_list = sorted(orig_list, key=len, reverse=True)
        return new_list
    
    conj_to_jmdict = {
        'adj-i' : "adjective (keiyoushi)"
    }

    o_f = open("lang/Conjugations.txt","r",encoding="utf-8")
    data = o_f.read()
    j = json.loads(data)
    for entry in j:
        n = entry['Name']
        tenses = entry['Tenses']
        if n in conj_to_jmdict:
            jmd_class = conj_to_jmdict[n]
            jmd_class_index = jmdict_parts_of_speech_list.index(jmd_class)
            jmdict_conjugations[jmd_class_index] = []
            for t in tenses:
                if t['Suffix'] != '':
                    jmdict_conjugations[jmd_class_index].append(t['Suffix'])

            # get rid of duplicates
            jmdict_conjugations[jmd_class_index] = list(set(jmdict_conjugations[jmd_class_index]))
            # sort by length so we can get greedy naturally
            jmdict_conjugations[jmd_class_index] = sort_by_len(jmdict_conjugations[jmd_class_index])

    o_f.close()


def load_jmdict():
    global jmdict_kanji_elements, jmdict_readings, max_jmdict_kanji_element_len, max_jmdict_reading_len

    print("Loading JMdict..")
    o_f = open(jmdict_file,"r",encoding="utf-8")
    lines = o_f.readlines()
    o_f.close()

    for line in lines:
        line = line.strip()
        d = line.split('\t')
        seq = int(d[0])
        k_elems = d[1].split(',')
        for k_elem in k_elems:
            l = len(k_elem)
            if l not in jmdict_kanji_element_seq:
                jmdict_kanji_element_seq[l] = dict()
            jmdict_kanji_element_seq[l][k_elem] = seq
            if l > max_jmdict_kanji_element_len:
                max_jmdict_kanji_element_len = l
        r_elems = d[2].split(',')
        for r_elem in r_elems:
            l = len(r_elem)
            if l not in jmdict_reading_seq:
                jmdict_reading_seq[l] = dict()
            jmdict_reading_seq[l][r_elem] = seq
            if l > max_jmdict_reading_len:
                max_jmdict_reading_len = l
        pos_elems = [int(x) for x in d[3].split(',')]
        jmdict_pos[seq] = pos_elems

    # make sure every length has at least empty entry. 
    # Also create sets for faster lookup
    for l in range(max_jmdict_kanji_element_len+1):
        if l not in jmdict_kanji_element_seq:
            jmdict_kanji_element_seq[l] = dict()
        jmdict_kanji_elements[l] = set(jmdict_kanji_element_seq[l].keys())
    for l in range(max_jmdict_reading_len+1):
        if l not in jmdict_reading_seq:
            jmdict_reading_seq[l] = dict()
        jmdict_readings[l] = set(jmdict_reading_seq[l].keys())

    print("Read %d JMdict entries" % len(lines))

    load_conjugations()
