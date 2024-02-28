import fugashi
import sys
from helper import *
from jp_parser_helper import *

parser = fugashi.Tagger('')

jmdict_readings = dict()
jmdict_reading_seq = dict()
#jmdict_reading_freq = dict()
jmdict_kanji_elements = dict()
jmdict_kanji_element_seq = dict()
#jmdict_kanji_element_freq = dict()
jmdict_pos = dict()
jmdict_meanings = dict()
max_jmdict_reading_len = 0
max_jmdict_kanji_element_len = 0

jmdict_file = base_dir + "lang/JMdict_e_s.tsv"
jmdict_with_meanings_file = base_dir + "lang/JMdict_e_m.tsv"

verb_conjugations = dict()
adj_conjugations = dict()

verbose_level = 0
log_file = None


stats_no_refs = dict()
def STATS_NO_REFS(word,cl):
    if (word,cl) not in stats_no_refs:
        stats_no_refs[(word,cl)] = 1
    else:
        stats_no_refs[(word,cl)] += 1

def LOG_HEADING(level=2):
    if level <= verbose_level:
        print("*************")

def LOG(level, msg, words=None):
    if level <= verbose_level:
        print(msg)
        if log_file is not None:
            print(msg, file=log_file)
            if words is not None:
                print("Phrase:"+''.join(words), file=log_file)

def set_verbose_level(level):
    global verbose_level
    verbose_level = level

def open_log_file(file):
    global log_file
    log_file = open(file, "w", encoding="utf-8")

def close_log_file():
    sorted_stats = dict(sorted(stats_no_refs.items(), key=lambda x:x[1], reverse=False))
    print("No refs statistics:", file=log_file)
    for (word,cl),count in sorted_stats.items():
        print("%s %s %s" % ( str(count).ljust(3), unidic_class_to_string(cl).ljust(10),word), file=log_file)
    log_file.close()

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
    
    k_c = 0
    words = []
    word_ortho = []
    word_classes = []
    collected_particles = ''
    previous_cl = -1
    for (wr,lemma,orth_base) in res:
        w = wr[0]
        class_name = wr[1]

        try:
            cl = unidic_word_classes.index(class_name)
        except:
            raise Exception("Unknown class %d in word %s" % (class_name, w))

        word = ''
        if is_all_alpha(w):
            # for some reason wide numbers and alphabets are parsed as 名詞
            cl = alphanum_class
            pass
        else:

            if class_name not in ignored_classes:
                word = orth_base
                if word == '':
                    # empty base form for some reason. Use the parsed form
                    word = w

                if orth_base != lemma and lemma != '':
                    # save lemmas for those words in which they differ from basic form
                    if '-' not in lemma:
                        if not is_katakana_word(lemma):
                            lemmas[word] = lemma
            
        if previous_cl != cl and previous_cl <= lumped_class:
            # word class changed so save previously collected word
            if collected_particles != '':
                words.append(collected_particles)
                word_classes.append(previous_cl)
                word_ortho.append('')
                collected_particles = ''

        if cl <= lumped_class:
            # when many non-JP characters and punctuation marks are 
            # in sequence we don't want to save them separately
            # but instead lump them together
            collected_particles += w
        else:
            words.append(w)
            word_ortho.append(word)
            word_classes.append(cl)

        previous_cl = cl

    if collected_particles != '':
        words.append(collected_particles)
        word_ortho.append('')
        word_classes.append(cl)

    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1

    return k_c, words, word_ortho, word_classes

def check_adjectival_nouns(pos,words,word_ortho,word_classes, word_flags):
    if pos == len(words) - 1:
        return
    if words[pos+1] == 'に' and word_classes[pos+1] == aux_verb_class: 
        # why is the に classified as 助動詞 ??
        # adjectival noun + に　-> adverb 
        # Example: 早め + に
        word_flags[pos+1] |= MERGE_PARTICLE
        word_flags[pos] |= DISABLE_ORTHO
        word_classes[pos] = adverb_class
    if word_classes[pos+1] == aux_verb_class:
        word_flags[pos+1] |= DISABLE_ORTHO
    if word_classes[pos+1] == suffix_class and word_ortho[pos+1] == 'がる':
        # 嫌がる 
        word_classes[pos] = verb_class
        word_flags[pos+1] |= MERGE_PARTICLE
        word_flags[pos] |= PROCESS_AFTER_MERGING # have to scan this word again as a verb

    return

def attempt_conjugation(i, words, stem, conj):
    test =  ''.join(words[i:])
    for t in conj:
        test2 = stem + t
        if test2 in test:
            # there's a match. find the actual right amount of elements
            test = words[i]
            for k, (w) in enumerate(words[i+1:]):
                test += w
                if test2 == test:
                    return k+1
    return 0

def check_adjectives(pos,words,word_ortho,word_classes, word_flags):
    if pos == len(words) - 1:
        return
    """
    if words[pos+1] == 'な' and word_classes[pos+1] == aux_verb_class: 
        # why is the な classified as 助動詞 ??
        # Anyway, this is the な　after na-adjective so prevent scanning it further
        word_flags[pos+1] |= NO_SCANNING
    """
    ortho = word_ortho[pos]
    if ortho[-1] == 'い':
        ending, conj = adj_conjugations[jmdict_adj_i_class]
        stem = ortho[:-1]
    else:
        ending, conj = adj_conjugations[jmdict_adjectival_noun_class] # the な　adjectives
        stem = ortho
    detected_num = attempt_conjugation(pos, words, stem, conj)
    for i in range(detected_num):
        word_flags[pos+i+1] = MERGE_PARTICLE

    return

def get_verb_conjugations(ortho):
    try:
        seqs = []
        if ortho in jmdict_kanji_element_seq[len(ortho)]:
            seqs = jmdict_kanji_element_seq[len(ortho)][ortho]
        else:
            if ortho in jmdict_reading_seq[len(ortho)]:
                seqs = jmdict_reading_seq[len(ortho)][ortho]
        for seq in seqs:
            cl_list = jmdict_pos[seq]
            for cl in cl_list:
                cl_txt = jmdict_parts_of_speech_list[cl]
                if cl in verb_conjugations:
                    ending, conj = verb_conjugations[cl]
                    stem = ortho[:-len(ending)]
                    removed_ending = ortho[-len(ending):]
                    if ending == removed_ending:
                        return cl, stem, conj
                    else:
                        pass
        pass
    except:
        pass
    return None, '', None

def check_verbs(pos,words,word_ortho,word_classes, word_flags):
    if pos + 1 == len(words):
        # nothing further to check
        return
    if word_ortho[pos] == '喰える':
        pass
    verb_cl, stem, conj = get_verb_conjugations(word_ortho[pos])
    if conj is not None:
        detected_num = attempt_conjugation(pos, words, stem, conj)
        if detected_num > 0:
            for i in range(detected_num):
                word_flags[pos+i+1] = MERGE_PARTICLE
                #word_flags[pos+i+1] = START_OF_SCAN_DISABLED
        else:
            if word_classes[pos+1] == aux_verb_class:
                if words[pos+1] == "てる": 
                    # accept the colloquial form, e.g. 持っ + てる
                    word_flags[pos+1] = MERGE_PARTICLE
    else:
        LOG(1,"No verb conjugations found for %s/%s" % (words[pos], word_ortho[pos]),words)
        word_flags[pos] |= ERROR_VERB_CONJUGATION


    """
    if words[pos+1] == 'て':
        word_flags[pos+1] |= MERGE_PARTICLE
        return
    if words[pos+1] == 'ば' and word_classes[pos+1] == grammatical_particle_class:
        # そういえば
        word_flags[pos+1] |= MERGE_PARTICLE
        return
    if word_classes[pos+1] == aux_verb_class:
        # merge conjucations
        word_flags[pos+1] |= MERGE_PARTICLE
        if pos + 2 < len(words) and word_classes[pos+2] == aux_verb_class:
            word_flags[pos+2] |= MERGE_PARTICLE
        return
    if words[pos+1] == 'ん': # emphatetic particle. Suppress it so it won't be scanned
        word_flags[pos+1] |= NO_SCANNING
        return
    """
    return

def check_nouns(pos,words,word_ortho,word_classes,word_flags):
    if pos + 1 == len(words):
        # nothing further to check
        return
    """
    if words[pos+1] == 'な' and word_classes[pos+1] == aux_verb_class:
        if word_ortho[pos+1] == 'だ':
            # for some reason the ortho in this is case is 'だ' and 
            # for example in phrase 一人なの？ the parser finds 'だの' in addition to 'なの'
            # ..  let's get rid of it
            word_ortho[pos+1] = 'な'
    if words[pos+1] == 'に' and word_classes[pos+1] == aux_verb_class:
        if word_ortho[pos+1] == 'だ':
            # the same as above..
            # In the phrase 別にいいでしょ the parser finds 'だいい' 
            word_ortho[pos+1] = 'に'
            pass
    """
    if word_classes[pos+1] == aux_verb_class:
        # the reason is above
        word_flags[pos+1] |= DISABLE_ORTHO

    return

def check_explicit_words(pos,words,word_ortho,word_classes,word_flags):
    lw = len(words)
    for (p_list,target_class) in explicit_words:
        lp = len(p_list)
        if pos + lp <= lw:
            i = 0
            while (i<lp) and (words[pos+i]==p_list[i]):
                i += 1
            if i == lp:
                # match. Change the class of the first particle and mark the next ones to be merged
                word_classes[pos] = target_class
                for i in range(1,lp):
                    word_flags[pos+i] = MERGE_PARTICLE
                return True
    return False

def particle_post_processing(pos, words, word_ortho, word_classes, word_flags):
    if not check_explicit_words(pos,words,word_ortho,word_classes,word_flags):
        cl = word_classes[pos]
        if cl == verb_class:
            return check_verbs(pos,words,word_ortho,word_classes,word_flags)
        elif cl == adjective_class:
            return check_adjectives(pos,words,word_ortho,word_classes,word_flags)
        elif cl == adjectival_noun_class:
            return check_adjectival_nouns(pos,words,word_ortho,word_classes,word_flags)
        elif cl <= punctuation_mark_class:
            word_flags[pos] |= NO_SCANNING
            return True
        elif cl == noun_class:
            return check_nouns(pos,words,word_ortho,word_classes,word_flags)
        elif cl == grammatical_particle_class:
            # do not allow jmdict to start scanning from this grammatical particle
            # if it's too small (easily mixed up with other words)
            # but allow it to be included in other parts. Only exception
            # is just at the beginning of the sentence (it could be mistake in Unidic)
            if (pos > 0) and (len(words[pos]) <= SMALL_PARTICLE_THRESHOLD):
                word_flags[pos] |= START_OF_SCAN_DISABLED
                return True
            return False
        elif cl == suffix_class:
            # do not allow jmdict to start scanning from this particle
            # but allow it to be included in other parts
            #word_flags[i] |= START_OF_SCAN_DISABLED
            return False
    else:
        return True

# merge those particles that are marked
def merge_particles(words, word_ortho, word_classes, word_flags):
    pos = 0
    processed_words = []
    processed_ortho = []
    processed_classes = []
    processed_word_flags = []

    for i in range(len(words)):
        if word_flags[i] & MERGE_PARTICLE:
            processed_words[pos-1] += words[i]
        else:
            processed_words.append(words[i])
            processed_ortho.append(word_ortho[i])
            processed_classes.append(word_classes[i])
            processed_word_flags.append(word_flags[i])
            pos += 1
    return processed_words, processed_ortho, processed_classes, processed_word_flags


def post_process_unidic_particles(words, word_ortho, word_classes):
    word_flags = [0] * len(words)

    cont = True
    while cont:
        for i in range(len(words)):
            word_flags[i] &= (~PROCESS_AFTER_MERGING) # clear the flag
            if word_flags[i] != MERGE_PARTICLE: 
                particle_post_processing(i, words, word_ortho, word_classes, word_flags)

        # merge those particles that are marked
        words, word_ortho, word_classes, word_flags = \
            merge_particles( words, word_ortho, word_classes, word_flags )

        cont = False
        if any(flag & PROCESS_AFTER_MERGING for flag in word_flags):
            # do another round
            cont = True

    return words, word_ortho, word_classes, word_flags


# this will scan for all the possible dictionary entries in the jmdict set
# (either kanji_elements or readings) using the given list of words 
# and starting at position pos.  
def greedy_jmdict_scanning(words, word_flags, word_ref, word_by_seq, searched_word_sets, start_pos, min_word_len, jmdict_set, jmdict_seq_dict, max_jmdict_len):
    lw = len(words)
    
    cycle_pos = start_pos
    while True:

        i = cycle_pos
        wc = 0
        word_chunk = ''
        if not ( word_flags[i] & START_OF_SCAN_DISABLED):
            while (i + wc < lw) and not (word_flags[i+wc] & NO_SCANNING): # words[i+wc] is not None:

                word_chunk += words[i+wc]
                wc += 1

                # first check that this chunk hasn't been yet searched for this position
                if word_chunk not in searched_word_sets[i]:
                    wc_l = len(word_chunk)
                    if wc_l >= min_word_len and wc_l <= max_jmdict_len:
                        # then check if the word chunk is in the jmdict_set.. (this is much faster)
                        if word_chunk in jmdict_set[wc_l]:
                            # .. found. Now we can use a bit more time to find the sequence number in the dict
                            seqs = jmdict_seq_dict[wc_l][word_chunk]
                            for seq in seqs:
                                word_by_seq[seq] = word_chunk
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


def scan_jmdict_for_selected_words( permutated_words, word_flags, word_ref, word_by_seq, searched_kanji_word_set, searched_reading_set):

    greedy_jmdict_scanning(permutated_words, word_flags, word_ref, word_by_seq, searched_kanji_word_set, 0, 1, jmdict_kanji_elements, jmdict_kanji_element_seq, max_jmdict_kanji_element_len)

    """
    for i, seqs in enumerate(word_ref):
        if len(seqs) == 0:
            # look for readings only starting from the word for which kanji_element couldn't be found
            greedy_jmdict_scanning(permutated_words, word_flags, word_ref, word_by_seq, searched_reading_set, i, 2, jmdict_readings, jmdict_reading_seq, max_jmdict_reading_len)
            break
    """
    greedy_jmdict_scanning(permutated_words, word_flags, word_ref, word_by_seq, searched_reading_set, 0, 2, jmdict_readings, jmdict_reading_seq, max_jmdict_reading_len)
    return word_ref


def check_illegal_class_combinations(word, scanned_word, unidic_class, scanned_word_jmdict_classes, messages):
    for cl in scanned_word_jmdict_classes:
        if cl == jmdict_expression_class:
            # everything is allowed in expression/phrase
            return False
        if cl in jmdict_noun_classes:
            if unidic_class not in allowed_noun_bindings:
                messages.append("%s(%s) not in allowed noun bindings for %s(%s)" % (word, unidic_class_to_string(unidic_class), scanned_word, jmdict_parts_of_speech_list[cl]))
            else:
                return False
        if cl in jmdict_verb_classes:
            if unidic_class not in allowed_verb_bindings:
                messages.append("%s(%s) not in allowed verb bindings for %s(%s)" % (word, unidic_class_to_string(unidic_class), scanned_word, jmdict_parts_of_speech_list[cl]))
            else:
                return False
        if cl in allowed_other_class_bindings:
            if unidic_class not in allowed_other_class_bindings[cl]:
                messages.append("%s(%s) not allowed for %s(%s)" % (word, unidic_class_to_string(unidic_class), scanned_word, jmdict_parts_of_speech_list[cl]))
            else:
                return False
    messages.append("%s(%s) has no matching class for %s(%s)" % (word, unidic_class_to_string(unidic_class), scanned_word, jmdict_parts_of_speech_list[cl]))
    return True


def parse_with_jmdict(unidic_words, unidic_word_ortho, unidic_word_class, unidic_word_flags,
            jmdict_word_list, jmdict_word_count, jmdict_word_seqs, jmdict_word_class_list, 
            word_count_per_unidict_class,
    ):
    # By default we use a word list in basic (ortho) form. 
    # Example: お願いします -> お + 願う + する

    # In order to do more exhaustive scanning we also construct 
    # a list of original word forms (as they were in the text)
    # if they differ from the basic form.
    # Example: お願いします -> お + 願い + します
    original_forms = []
    wlen = len(unidic_words)
    words = []
    for i, w in enumerate(unidic_words):
        cli = unidic_word_class[i]
        if (unidic_words[i] != unidic_word_ortho[i]) \
                and not (unidic_word_flags[i] & (NO_SCANNING | DISABLE_ORTHO)):
            original_forms.append(unidic_words[i])
        else:
            original_forms.append(None)
        if unidic_word_flags[i] & DISABLE_ORTHO:
            words.append(unidic_words[i])
        else:
            words.append(unidic_word_ortho[i])
    """
    This creates a list of permutations for words/alternative words.
    For example:
        お + 願う + する
        お + 願う + します
        お + 願い + する
        お + 願い + します
    """
    permutations = create_phrase_permutations(words, original_forms)
    if verbose_level>=1:
        LOG(2,"Permutations:")
        for p in permutations:
            p_str = [x.ljust(6) for x in p]
            LOG(2, "  %s" % (''.join(p_str)))
        LOG(2,"***********")

    # Scan this block with each permutation and for every word/particle get references 
    # (sequence numbers) to JMDict entries
    searched_kanji_word_sets = [set() for x in range(wlen)]
    searched_reading_sets = [set() for x in range(wlen)]
    word_seq_ref = [[] for x in range(len(unidic_words))]
    word_by_seq = dict()
    for permutated_words in permutations:
        scan_jmdict_for_selected_words(permutated_words, unidic_word_flags, word_seq_ref, word_by_seq, searched_kanji_word_sets, searched_reading_sets)

    seq_count = dict()
    for i, seqs in enumerate(word_seq_ref):
        # calculate how many particles reference each jmdict word/phrase
        for seq in seqs:
            if seq not in seq_count:
                seq_count[seq] = 1
            else:
                seq_count[seq] += 1

    # Remove references for those small particles that are isolated
    # (not part of bigger phrase)
    for i,(seqs) in enumerate(word_seq_ref):
        cl = unidic_word_class[i]
        # keep count of word occurrence by class
        word_count_per_unidict_class[cl] += 1

        messages = []
        new_seqs = []
        for seq in seqs:
            remove_ref = False
            if cl <= grammatical_particle_class:
                if seq_count[seq] == 1:
                    if len(word_by_seq[seq]) <= SMALL_PARTICLE_THRESHOLD:
                        # this particle is isolated for this reference
                        if verbose_level>0:
                            messages.append("Removed isolated small particle reference for %s[%d]" % (word_by_seq[seq],seq ))
                        remove_ref = True

            if not remove_ref:
                remove_ref = check_illegal_class_combinations(unidic_words[i], word_by_seq[seq], cl, jmdict_pos[seq], messages)

            if not remove_ref:
                new_seqs.append(seq)
            #else:
            #    if verbose_level>=2:
            #        print(" %d : %s Removed reference %s[%d]" % (i,unidic_words[i].ljust(6), word_by_seq[seq],seq ))

        if verbose_level >= 1:
            if len(new_seqs) == 0:
                STATS_NO_REFS(unidic_words[i], unidic_word_class[i])
                l_level = 1
                if cl <= grammatical_particle_class:
                    l_level = 2
                LOG_HEADING()
                LOG(l_level," %d : %s Has no references because.. " % (i,unidic_words[i]))
                if len(seqs) == 0:
                    LOG(l_level," .. no matches in scanning",words=unidic_words)
                else:
                    for msg in messages:
                        LOG(l_level,"  %s" % msg)
                    LOG(l_level,"",words=unidic_words)
            elif verbose_level >= 2:
                if len(messages)>0:
                    LOG_HEADING()
                    LOG(2," %d : %s Removed references.. " % (i,unidic_words[i]))
                    for msg in messages:
                        print("\t%s" % (msg))
                    LOG(2,"\t.. remaining references:")
                    for seq in new_seqs:
                        cl_list = jmdict_pos[seq]
                        if len(cl_list) == 1:
                            LOG(2,"\t%s[%d] %s" % (word_by_seq[seq].ljust(6,'　'),seq, jmdict_parts_of_speech_list[cl_list[0]] ))
                        else:
                            LOG(2,"\t%s[%d] with classes:" % (word_by_seq[seq].ljust(6,'　'),seq))
                            for cl in cl_list:
                                LOG(2,"\t\t\t- %s" % (jmdict_parts_of_speech_list[cl]))

        word_seq_ref[i] = new_seqs
        seqs = new_seqs

        # sort each particle/word reference by the size of the word/phrase it's referencing
        if len(seqs)>1:
            ref_sizes = dict()
            for seq in seqs:
                ref_sizes[seq] = len(word_by_seq[seq])
            sorted_refs = dict(sorted(ref_sizes.items(), key=lambda x:x[1], reverse=True))
            word_seq_ref[i] = list(sorted_refs.keys())

    # replace the jmdict seq reference with idx number to the word list
    word_index_ref = []
    for i, seqs in enumerate(word_seq_ref):
        refs = []
        for seq in seqs:
            try:
                idx = jmdict_word_list.index(word_by_seq[seq])
                if seq not in jmdict_word_seqs[idx]:
                    jmdict_word_seqs[idx] += [seq]
                    #jmdict_word_class_list.append([jmdict_pos[seq]])
                jmdict_word_count[idx] += 1
            except:
                jmdict_word_list.append(word_by_seq[seq])
                jmdict_word_seqs.append([seq])
                #jmdict_word_class_list.append([jmdict_pos[seq]])
                jmdict_word_count.append(0)
                idx = len(jmdict_word_list) - 1

            cl_list = jmdict_pos[seq]
            if jmdict_expression_class in cl_list:
                # this is a phrase
                # we use negative idx for phrases (just for signaling purposes)
                idx = -idx
            if idx not in refs:
                refs.append(idx)
        word_index_ref.append(refs)

    return word_index_ref

def reassemble_block(original_lines, unidic_words, word_index_ref):
    # re-assemble this block back into lines (list of lists)
    i = 0
    block_word_ref = []
    next_new_line_str = ''
    next_new_line = []
    for line in original_lines:
        new_line = next_new_line
        new_line_str = next_new_line_str
        next_new_line = ''
        next_new_line = []
        while line not in new_line_str:
            w = unidic_words[i]
            refs = word_index_ref[i]
            new_line_str += w

            if len(new_line_str) > len(line):
                # some of the particles were fused temporarily for scanning purposes. 
                # Don't want to lengthen a line so let's break them up again
                next_new_line_str = new_line_str[len(line):]
                num_extra_characters = len(new_line_str) - len(line)
                w = w[:-num_extra_characters]
                next_new_line = [{next_new_line_str:refs}]
            new_line.append({w:refs})
            i += 1
        
        block_word_ref.append(new_line)
    
    return block_word_ref


def get_conjugations_recursively(root_entries, conj_name, rec_level):
    tenses = []
    remove_suffix = None
    for e in root_entries:
        if e['Name'] == conj_name:
            for t in e['Tenses']:
                sfx = t['Suffix']
                if remove_suffix == None:
                    remove_suffix = sfx
                if sfx != '':
                    tenses.append(sfx)
                if 'Next Type' in t:
                    nt = t['Next Type']
                    if rec_level < 1 or 'stem' in nt:
                        sub_conjugations, sub_remove_suffix = get_conjugations_recursively(root_entries, nt, rec_level + 1)
                        lr = len(sub_remove_suffix)
                        if lr > 0:
                            base = sfx[:-lr]
                            removed_part = sfx[-lr:]
                            if sub_remove_suffix != removed_part:
                                raise Exception("!!")  # Should not happen
                        else:
                            base = sfx
                        for st in sub_conjugations:
                            tenses.append(base + st )
    return tenses, remove_suffix

def load_conjugations():
    global adj_conjugations, verb_conjugations
    
    o_f = open("lang/Conjugations.txt","r",encoding="utf-8")
    data = o_f.read()
    entries = json.loads(data)
    o_f.close()

    for entry in entries:
        n = entry['Name']
        if n in jmdict_parts_of_speech_codes.keys():
            cl_name = jmdict_parts_of_speech_codes[n]
            cli = jmdict_parts_of_speech_list.index(cl_name)
            conj_list, ending = get_conjugations_recursively(entries, n, 0)
            conj_list = list(set(conj_list))  # get rid of possible duplicates

            # sort by conjugation length so we can be greedy by default
            # i.e. get the longest possible conjugation found in the phrase
            conj_dict = {x:len(x) for x in conj_list}
            sorted_conj = dict(sorted(conj_dict.items(), key=lambda x:x[1], reverse=True))

            if 'adj' in n:
                adj_conjugations[cli] = (ending, list(sorted_conj))
            else:
                verb_conjugations[cli] = (ending, list(sorted_conj))


def load_jmdict(load_meanings=False):
    global jmdict_kanji_elements, jmdict_readings, max_jmdict_kanji_element_len, max_jmdict_reading_len

    print("Loading JMdict..")
    if load_meanings:
        o_f = open(jmdict_with_meanings_file,"r",encoding="utf-8")
    else:
        o_f = open(jmdict_file,"r",encoding="utf-8")
    lines = o_f.readlines()
    o_f.close()

    for line in lines:
        line = line.strip()
        d = line.split('\t')
        seq = int(d[0])

        k_elems = d[1].split(',')
        for k_elem in k_elems:
            if k_elem != '':
                l = len(k_elem)
                if l not in jmdict_kanji_element_seq:
                    jmdict_kanji_element_seq[l] = dict()
                if k_elem not in jmdict_kanji_element_seq[l]:
                    jmdict_kanji_element_seq[l][k_elem] = [seq]
                else:
                    jmdict_kanji_element_seq[l][k_elem].append(seq)
                if l > max_jmdict_kanji_element_len:
                    max_jmdict_kanji_element_len = l
        r_elems = d[2].split(',')
        for r_elem in r_elems:
            l = len(r_elem)
            if l not in jmdict_reading_seq:
                jmdict_reading_seq[l] = dict()
            if r_elem not in jmdict_reading_seq[l]:
                jmdict_reading_seq[l][r_elem] = [seq]
            else:
                jmdict_reading_seq[l][r_elem].append(seq)

            if l > max_jmdict_reading_len:
                max_jmdict_reading_len = l
        pos_elems = [int(x) for x in d[3].split(',')]
        jmdict_pos[seq] = pos_elems

        # TOOD: need frequencies?

        if load_meanings:
            jmdict_meanings[seq] = json.loads(d[6])

    # make sure every length has at least empty entry. 
    # Also create sets consisting of just a word for faster lookup
    for l in range(max_jmdict_kanji_element_len+1):
        if l not in jmdict_kanji_element_seq:
            jmdict_kanji_element_seq[l] = dict()
        jmdict_kanji_elements[l] = set(jmdict_kanji_element_seq[l].keys())
    for l in range(max_jmdict_reading_len+1):
        if l not in jmdict_reading_seq:
            jmdict_reading_seq[l] = dict()
        jmdict_readings[l] = set(jmdict_reading_seq[l].keys())

    print("Read %d JMdict entries" % len(lines))

    # create combined verb and noun classes for easier lookup
    for cl in jmdict_parts_of_speech_list:
        idx = jmdict_parts_of_speech_list.index(cl)
        if 'verb' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_verb_classes.append(idx)
        elif 'noun' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_noun_classes.append(idx)

