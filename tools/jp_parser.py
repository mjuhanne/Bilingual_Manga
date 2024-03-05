import fugashi
import sys
from helper import *
from jp_parser_helper import *

parser = fugashi.Tagger('')

jmdict_readings = dict()
jmdict_reading_seq = dict()
jmdict_reading_freq = dict()
jmdict_kanji_elements = dict()
jmdict_kanji_element_seq = dict()
jmdict_kanji_element_freq = dict()
jmdict_class_list_per_sense = dict()
jmdict_flat_class_list = dict()
jmdict_meaning_per_sense = dict()
max_jmdict_reading_len = 0
max_jmdict_kanji_element_len = 0

verb_conjugations = dict()
adj_conjugations = dict()

verbose_level = 0
log_file = None

def get_jmdict_data():
    return jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_readings, jmdict_reading_seq, jmdict_meaning_per_sense, max_jmdict_kanji_element_len, max_jmdict_reading_len

"""
def get_classes_from_seq_sense(seq_sense):
    seq,senses = expand_sense_ref(seq_sense)
    cls = set()
    for sense in senses:
        cls.update(jmdict_class_list_per_sense[seq][sense])
    return cls
"""

def get_highest_freq_class_list_with_particle_priority(seq_senses):
    f_min = 100
    f_min_cl = []
    for seq_sense in seq_senses:
        seq,senses = expand_sense_ref(seq_sense)
        for sense in senses:
            cl_list = jmdict_class_list_per_sense[seq][sense]
            if jmdict_particle_class in cl_list:
                return cl_list
            f = min(jmdict_kanji_element_freq[seq],jmdict_reading_freq[seq])
            if f < f_min:
                f_min = f
                f_min_cl = cl_list
    return f_min_cl

stats_no_refs = dict()

def STATS_NO_REFS(item,cl):
    if (item.txt,cl) not in stats_no_refs:
        stats_no_refs[(item.txt,cl)] = 1
    else:
        stats_no_refs[(item.txt,cl)] += 1

incidences = dict()
def INCIDENCE_COUNTER(incidence, target_word, items):
    if incidence not in incidences:
        incidences[incidence] = []
    incidences[incidence].append((target_word,[item.txt for item in items]))

def LOG_HEADING(level=2):
    if level <= verbose_level:
        print("*************")

def LOG(level, msg, items=None):
    if level <= verbose_level:
        print(msg)
        if log_file is not None:
            print(msg, file=log_file)
            if items is not None:
                print("Phrase:"+''.join([item.txt for item in items]), file=log_file)

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
    print("No refs statistics:", file=log_file)
    for (incidence_msg,i_list) in incidences.items():
        print("**** %s ****" % incidence_msg, file=log_file)
        for (target_word, words) in i_list:
            print("%s : %s" %(target_word.ljust(6,'　'),''.join(words)), file=log_file)
        print("-- Total %d incidences" % len(i_list), file=log_file)

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

from dataclasses import dataclass
@dataclass
class LexicalItem:
    txt: str
    ortho: str
    cl: int
    flags: int = 0

def parse_line_with_unidic(line, kanji_count, lemmas):

    res = parse_with_fugashi(line)
    if len(res)==0 and len(line)>0:
        raise Exception("Couldn't parse '%s'" % line)
    
    k_c = 0
    items = []
    collected_particles = ''
    previous_cl = -1
    for (wr,lemma,orth_base) in res:
        w = wr[0]
        class_name = wr[1]

        try:
            cl = unidic_class_list.index(class_name)
        except:
            raise Exception("Unknown class %d in word %s" % (class_name, w))

        word = ''
        if is_all_alpha(w):
            # for some reason wide numbers and alphabets are parsed as nouns so
            # switch their class into this pseudoclass
            cl = alphanum_pseudoclass
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
                items.append(LexicalItem(collected_particles,'',previous_cl))
                collected_particles = ''

        if cl <= lumped_class:
            # when many non-JP characters and punctuation marks are 
            # in sequence we don't want to save them separately
            # but instead lump them together
            collected_particles += w
        else:
            items.append(LexicalItem(w,word,cl))

        previous_cl = cl

    if collected_particles != '':
        items.append(LexicalItem(collected_particles,'',cl))

    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1

    return k_c, items 

def check_adjectival_nouns(pos,items): 
    if pos == len(items) - 1:
        return
    if items[pos+1].cl == aux_verb_class:
        # disable the ortho form for the erroneously detected aux verb
        # (most likely な in みたいな or に in 早めに)
        items[pos+1].flags |= DISABLE_ORTHO
    return

def attempt_conjugation(i, items, stem, conj):
    words = [item.txt for item in items]
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

def check_adjectives(pos,items):
    if pos == len(items) - 1:
        return
    ortho = items[pos].ortho
    if ortho[-1] == 'い':
        ending, conj = adj_conjugations[jmdict_adj_i_class]
        stem = ortho[:-1]
    else:
        ending, conj = adj_conjugations[jmdict_adjectival_noun_class] # the な　adjectives
        stem = ortho
    detected_num = attempt_conjugation(pos, items, stem, conj)
    # TODO

    #for i in range(detected_num):
    #    item_flags[pos+i+1] = MERGE_PARTICLE

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
            cl_list = jmdict_flat_class_list[seq]
            for cl in cl_list:
                cl_txt = jmdict_class_list[cl]
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

def check_verbs(pos,items): 
    if pos + 1 == len(items):
        # nothing further to check
        return
    verb_cl, stem, conj = get_verb_conjugations(items[pos].ortho)
    if conj is not None:
        detected_num = attempt_conjugation(pos, items, stem, conj)
        if detected_num > 0:
            for i in range(detected_num):
                items[pos+i+1].flags = MERGE_PARTICLE
                #item_flags[pos+i+1] = START_OF_SCAN_DISABLED
        else:
            if items[pos+1].cl == aux_verb_class:
                if items[pos+1].txt == "てる": 
                    # accept the colloquial form, e.g. 持っ + てる
                    items[pos+1].flags = MERGE_PARTICLE
    else:
        LOG(1,"No verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
        items[pos].flags |= ERROR_VERB_CONJUGATION
    return

def check_nouns(pos,items):
    if pos + 1 == len(items):
        # nothing further to check
        return
    if items[pos+1].cl == aux_verb_class:
        if items[pos+1].txt == 'に' and items[pos+1].ortho == 'だ':
            # Erroneously detected aux verb. Disable the ortho form to prevent false results
            # For example in the phrase 別にいいでしょ the scanner would try 'だいい' 
            items[pos+1].flags |= DISABLE_ORTHO
        if items[pos+1].txt == 'な' and items[pos+1].ortho == 'だ':
            # the reason is same as above
            items[pos+1].flags |= DISABLE_ORTHO
    return

def handle_explicit_words(pos,items):
    if items[pos].txt in alternative_forms.keys():
        items[pos].ortho = alternative_forms[items[pos].txt]

    lw = len(items)
    for (p_list,p_classes,target_class,condition,extra_tasks) in explicit_words:
        lp = len(p_list)
        if pos + lp <= lw:
            i = 0
            while (i<lp) and (items[pos+i].txt==p_list[i]) and (items[pos+i].cl==p_classes[i]):
                i += 1
            if i == lp:
                # All items match. Check extra conditions yet.
                allowed = True
                if condition == COND_BLOCK_START and pos>0:
                    allowed = False

                if allowed:
                    # Change the class of the first particle and mark the next ones to be merged
                    items[pos].cl = target_class
                    for i in range(1,lp):
                        items[pos+i].flags = MERGE_PARTICLE
                    if extra_tasks == TASK_CLEAR_ORTHO:
                        for i in range(0,lp):
                            items[pos+i].ortho = ''
                    return True
    return False

def particle_post_processing(pos, items):
    if not handle_explicit_words(pos,items):
        cl = items[pos].cl
        if cl == verb_class:
            return check_verbs(pos,items)
        elif cl == adjective_class:
            return check_adjectives(pos,items)
        elif cl == adjectival_noun_class:
            return check_adjectival_nouns(pos,items)
        elif cl <= punctuation_mark_class:
            items[pos].flags |= NO_SCANNING
            return True
        elif cl == noun_class:
            return check_nouns(pos,items)
        elif cl == aux_verb_class:
            if items[pos].txt == 'な':
                # The parser usually thinks it has detected な like 
                # in なければ. In this case the ortho form is だ 
                # However usually the detection of な is erroneous,
                # for example: な in どうなんでしょう.
                # The ortho form creates problems when later using it in phrase
                # permutations (どうだ in addition to どうな). 
                # It's safe to delete the ortho for な　because
                # we already handle verb conjugations without relying on the 
                # ortho forms from auxiliary verb particles
                items[pos].ortho = items[pos].txt
                # な might often modify the preceding (adjectival) noun
                # like 素敵(すてき) + な
                # but JMDict doesn't recognize these forms, nor does it
                # have an entry to な as a particle in this case, so 
                # we want to fuse な　into the preceding word later after scanning
                # is complete
                items[pos].flags |= BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED

        elif cl == grammatical_particle_class:
            # do not allow jmdict to start scanning from this grammatical particle
            # if it's too small (easily mixed up with other words)
            # but allow it to be included in other parts. Only exception
            # is just at the beginning of the sentence (it could be mistake in Unidic)
            #if (pos > 0) and (len(words[pos]) <= SMALL_PARTICLE_THRESHOLD):
            #    item_flags[pos] |= START_OF_SCAN_DISABLED
            #    return True
            return False
        elif cl == suffix_class:
            # do not allow jmdict to start scanning from this particle
            # but allow it to be included in other parts
            #item_flags[i] |= START_OF_SCAN_DISABLED
            return False
    else:
        return True

# merge those particles that are marked
def merge_particles(items):
    pos = 0
    processed_items = []
    for i in range(len(items)):
        if items[i].flags & MERGE_PARTICLE:
            processed_items[pos-1].txt += items[i].txt
        else:
            processed_items.append(items[i])
            pos += 1
    return processed_items


def post_process_unidic_particles(items):
    cont = True
    while cont:
        for i in range(len(items)):
            items[i].flags &= (~PROCESS_AFTER_MERGING) # clear the flag
            if items[i].flags != MERGE_PARTICLE: 
                particle_post_processing(i,items)

        # merge those particles that are marked
        items = merge_particles( items )

        cont = False
        if any(item.flags & PROCESS_AFTER_MERGING for item in items):
            # do another round
            cont = True

    return items

ALL_SENSES = 100

"""
This makes sure that only appropriate jmdict senses are assigned to 
the unidic lex items that make up the scanned word/phrase
Example:
    お母さん with seq number 1002650 and following senses (each having)
            1# ['mother', 'mom', 'mum', 'ma']
                noun (common) (futsuumeishi)
            2# ['wife']
                noun (common) (futsuumeishi)
            3# ['you (of an elderly person older than the speaker)', 'she', 'her']
                pronoun
The matching lexical items were お + 母 + さん
"""
def get_valid_senses_for_scanned_word(scanned_word, pos,num_scanned_items,items,seq):
    global messages # for debugging

    if scanned_word in hard_coded_seqs.keys():
        (unidic_class, wanted_seq) = hard_coded_seqs[scanned_word]
        if num_scanned_items == 1 and items[pos].cl==unidic_class:
            # いる / する / 私 clutter prevention: Don't carry any 
            # references to these words other than the sequence number selected here
            # User can check the other 9 homophones elsewhere though
            if seq == wanted_seq:
                return [ALL_SENSES]
            else:
                return []

    scanned_word_jmd_cl_list_per_sense = jmdict_class_list_per_sense[seq]
    valid_senses = [set() for x in range(num_scanned_items)]

    for i in range(num_scanned_items):
        word = items[pos+i].txt
        unidic_classes = set([items[pos+i].cl])
        if word in alternative_classes:
            unidic_classes.update(alternative_classes[word])
        is_last = (i==num_scanned_items-1)
        next_word = None
        next_word_class = None
        if not is_last:
            next_word = items[pos+i+1].txt
            next_word_class = items[pos+i+1].cl

        prev_word_in_block = None
        prev_word_in_block_classes = set()
        if pos + i - 1 >= 0:
            prev_word_in_block = items[pos+i-1].txt
            prev_word_in_block_classes = set([items[pos+i-1].cl])
            if prev_word_in_block in alternative_classes:
                prev_word_in_block_classes.update(alternative_classes[prev_word_in_block])

        """
        if prefix_class in unidic_classes:
            if i != 0:
                # prefix must be the first particle in the word
                return []
        """

        for s_idx, scanned_word_jmd_cl_list in enumerate(scanned_word_jmd_cl_list_per_sense):
            for jmd_cl in scanned_word_jmd_cl_list:
                if jmd_cl == jmdict_expression_class:
                        # everything is allowed as expression/phrase
                        valid_senses[i].update([s_idx])

                if jmd_cl == jmdict_suffix_class:
                    if noun_class in unidic_classes and i>0:
                        # nouns can act as suffix (like -家)
                        # as long as they are not alone or at the beginning
                        valid_senses[i].update([s_idx])

                if jmd_cl == jmdict_prefix_class:
                    if noun_class in unidic_classes and i == 0:
                        # nouns can act as prefix (like 全-)
                        # as long as they are at the beginning. Not being
                        # standalone is not enforced because sometimes
                        # they are indeed isolated in the dictionary (like 全) 
                        valid_senses[i].update([s_idx])

                if jmd_cl == jmdict_adverb_class:
                    if adjectival_noun_class in unidic_classes or noun_class in unidic_classes:
                        if next_word == 'に':
                            # (adjectival) noun + に can be adverb
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])
                    if adverb_class in unidic_classes:
                        if next_word_class == verb_class or next_word_class == grammatical_particle_class:
                            # Allow adverbs to stay as adverbs when followed by 
                            # a verb or a grammatical particle
                            # どう + して,  もし + も、、少し + ずつ
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])

                if jmd_cl == jmdict_pronoun_class:
                    if pronoun_class in unidic_classes:
                        if next_word == 'か':
                            # pronoun + か can still be pronoun (誰か).
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])
                    if pronoun_class in unidic_classes or noun_class in unidic_classes:
                        if next_word == 'ら' and next_word_class == suffix_class:
                            # noun or pronoun + ら can still be pronoun (奴ら/お前ら).
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])

                if jmd_cl in jmdict_noun_pos_list:
                    if prefix_class in unidic_classes and i == 0:
                        if num_scanned_items > 1:
                            # allow prefix for noun if it's the first item and not alone
                            valid_senses[i].update([s_idx])
                    if suffix_class in unidic_classes and is_last:
                        if num_scanned_items > 1:
                            # allow suffix for noun if it's the last item and not alone
                            valid_senses[i].update([s_idx])

                if jmd_cl == jmdict_conjunction_class:
                    if noun_class in unidic_classes and next_word == 'に':
                        # 癖に
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

                if jmd_cl in jmdict_verb_pos_list:
                    if noun_class in unidic_classes and verb_class == next_word_class:
                        # sometimes item detected as noun precede a verb:
                        # 風邪ひく, ご覧なさる, 旅する, 役立つ...
                        valid_senses[i].update([s_idx])

                # more general allow rules based on jmdict <-> unidic class bindings
                if s_idx not in valid_senses:
                    if jmd_cl in jmdict_noun_pos_list:
                        if not (unidic_classes & allowed_noun_bindings):
                            messages[pos+i].append("%s(%s) not in allowed noun bindings for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
                        else:
                            valid_senses[i].update([s_idx])
                    if jmd_cl in jmdict_verb_pos_list:
                        if not (unidic_classes & allowed_verb_bindings):
                            messages[pos+i].append("%s(%s) not in allowed verb bindings for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
                        else:
                            valid_senses[i].update([s_idx])
                    if jmd_cl in allowed_other_class_bindings:
                        if not (unidic_classes & set(allowed_other_class_bindings[jmd_cl])):
                            messages[pos+i].append("%s(%s) not allowed for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
                        else:
                            valid_senses[i].update([s_idx])

        if len(valid_senses[i]) == 0:

            if num_scanned_items >= 4:
                INCIDENCE_COUNTER("acceptance by scanned items length>=4",scanned_word,items)
            if len(scanned_word) >= 6:
                INCIDENCE_COUNTER("acceptance by scanned word length>=6",scanned_word,items)

            for scanned_word_jmd_cl_list in scanned_word_jmd_cl_list_per_sense:
                for jmd_cl in scanned_word_jmd_cl_list:
                    if jmd_cl in jmdict_noun_pos_list:
                        # Sometimes Unidict just fails to parse pure Hiragana words..
                        # For example ばんそうこう (bandage) becomes:
                        #  ば (grammatical particle)
                        #  ん (interjection)
                        #  そうこう (adverb) ..
                        # To allow matching these kinds of words we disregard the parsed classes
                        # if the candidate word is a noun and has a length of minimum of 5 characters 
                        if len(scanned_word) >= HOMOPHONE_MATCHING_WORD_MINIMUM_LENGTH:
                            messages[pos+i].append("%s(%s) failed otherwise but matching %s(%s) just due to length" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
                            return [ALL_SENSES] # no need to check other words

            messages[pos+i].append("%s(%s) has no matching class for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
            # This lexical item matched none of the senses for this word so no need to check other items
            return []
        
    # get those senses that match all lexical items
    final_valid_senses = set.intersection(*valid_senses)
    if len(final_valid_senses) == len(scanned_word_jmd_cl_list_per_sense):
        return [ALL_SENSES]
    return list(final_valid_senses)


def add_matched_sense_reference(chunk, chunk_len, pos, seq, valid_senses, scan_results):
    for sense in valid_senses:
        if sense == ALL_SENSES:
            seq_s = str(seq)
        else:
            seq_s = str(seq) + '/' + str(sense)
        scan_results['word_by_seq'][seq_s] = chunk

        # add this seq/sense reference for all the encompassing lexical items
        for j in range(chunk_len):
            scan_results['item_sense_ref'][pos+j].append(seq_s)

        # add the matched chunk (word) to word list (if new), increment word count
        # and add back-reference from the word to this sense
        try:
            w_idx = scan_results['word_list'].index(chunk)
            if seq_s not in scan_results['word_senses'][w_idx]:
                scan_results['word_senses'][w_idx] += [seq_s]
            scan_results['word_count'][w_idx] += 1
        except:
            scan_results['word_list'].append(chunk)
            scan_results['word_senses'].append([seq_s])
            scan_results['word_count'].append(1)
            w_idx = len(scan_results['word_list']) - 1

        # add sense to sense_list, reference the word
        # and list also its Parts of Speech classes
        try:
            s_idx = scan_results['sense_list'].index(seq_s)
        except:
            scan_results['sense_list'].append(seq_s)
            scan_results['sense_word_index'].append(w_idx)
            seq_cl_lists = jmdict_class_list_per_sense[seq]
            if sense == ALL_SENSES:
                cl_list = [ cl for cls_per_sense in seq_cl_lists for cl in cls_per_sense]
            else:
                cl_list = jmdict_class_list_per_sense[seq][sense]
            cl_list = list(set(cl_list)) # get rid of duplicates
            scan_results['sense_class_list'].append(cl_list)
            s_idx = len(scan_results['sense_list']) - 1



    #    if s_idx not in refs:
    #        refs.append(s_idx)
    #item_sense_idx_ref.append(refs)


# this will scan for all the possible dictionary entries in the jmdict set
# (either kanji_elements or readings) using the given phrase
# and starting at position pos.  
def greedy_jmdict_scanning(phrase, items, scan_results, searched_chunk_sets, 
        start_pos, min_word_len, jmdict_set, jmdict_seq_dict, max_jmdict_len):
    lp = len(phrase) # length of phrase in particles
    
    cycle_pos = 0
    while True:

        i = start_pos + cycle_pos
        clen = 0
        chunk = ''
        if not ( items[i].flags & START_OF_SCAN_DISABLED):
            while (cycle_pos + clen < lp):

                chunk += phrase[cycle_pos + clen]
                clen += 1

                # first check that this chunk hasn't been yet searched for this position
                if chunk not in searched_chunk_sets[i]:
                    clen_c = len(chunk) # chunk size in characters, not particles
                    if clen_c >= min_word_len and clen_c <= max_jmdict_len:
                        # then check if the word chunk is in the jmdict set.. (this is much faster)
                        if chunk in jmdict_set[clen_c]:
                            # .. found. Now we can use a bit more time to find the sequence number in the dict
                            seqs = jmdict_seq_dict[clen_c][chunk]
                            for seq in seqs:
                                senses = get_valid_senses_for_scanned_word(chunk,i,clen,items,seq)
                                if len(senses)>0:
                                    add_matched_sense_reference(chunk, clen, i, seq, senses, scan_results)

                    searched_chunk_sets[i].add(chunk)

        cycle_pos += 1
        if cycle_pos > lp - 1:
            return

# Returns a list of phrase permutations and a new start position for next round.
# Permutations are created using original particles/words and ending with 
# an ortho/basic form. Scanning stops when non-Hiragana/Katakana/Kanji character was
# detected
def create_phrase_permutations(original_words, ortho_forms, start=0):
    i = start
    permutations = []
    while i<len(original_words): # and (not (items[i].flags & NO_SCANNING) ):
        if ortho_forms[i] is not None:
            permutations.append(original_words[start:i] + [ortho_forms[i]])
        i += 1
    
    if i> 0:
        # finally add the whole original as one permutation
        permutations.append(original_words[start:i])
    if i<len(original_words):
        i += 1  # add one because the last one was a punctuation etc..
    return permutations, i


def scan_jmdict_for_phrase( phrase, pos, items, scan_results, searched_kanji_word_set, searched_reading_set):

    greedy_jmdict_scanning(phrase, items, scan_results, searched_kanji_word_set, pos, 1, jmdict_kanji_elements, jmdict_kanji_element_seq, max_jmdict_kanji_element_len)
    greedy_jmdict_scanning(phrase, items, scan_results, searched_reading_set, pos, 1, jmdict_readings, jmdict_reading_seq, max_jmdict_reading_len)


# Expand the sense reference into a tuple of seq + sense lists: (seq,[senses])
#  For example "203943/1" results in (203943,[1]) whereas
# ALL_SENSES is denoted with a reference without slash+sense index number
# so return all the senses: (203943,[1,2,...,n])
def expand_sense_ref(seq_sense):
    s = seq_sense.split('/')
    seq = int(s[0])
    if len(s) > 1:
        exp_list = [int(s[1])]
    else:
        exp_list = []
        for i in range(len(jmdict_class_list_per_sense[seq])):
            exp_list.append((i))
    return (seq,exp_list)

"""
def expand_sense_tuple(seq_senses):
    exp_list = []
    for seq, sense in seq_senses:
        if sense == ALL_SENSES:
            for i in range(len(jmdict_class_list_per_sense[seq])):
                exp_list.append((seq,i))
        else:
            exp_list.append((seq,sense))
    return exp_list
"""

def init_scan_results():
    scan_results = dict()
    scan_results['sense_list'] = []
    scan_results['sense_word_index'] = []
    scan_results['sense_class_list'] = []

    scan_results['word_list'] = [] # ['','*','-'] 
    scan_results['word_count'] = [] # [0,0,0]
    scan_results['word_senses'] = [] # [None,None,None]
    scan_results['word_count_per_unidict_class'] = \
        [0 for x in range(len(unidic_class_list))] 
    return scan_results


def parse_with_jmdict(unidic_items, scan_results):
    global messages
    # By default we use lexical items in the form they word in the original text
    # Example: お願いします -> お + 願い + します

    # In order to do more exhaustive scanning we also construct 
    # a list of basic/ortho forms if they differ from the originals.
    # Example: お願いします -> お + 願う + する
    ortho_forms = []
    original_forms = [item.txt for item in unidic_items]
    wlen = len(unidic_items)
    for i, w in enumerate(unidic_items):
        cli = unidic_items[i].cl
        if (unidic_items[i].txt != unidic_items[i].ortho) \
                and not (unidic_items[i].flags & (NO_SCANNING | DISABLE_ORTHO)):
            ortho_forms.append(unidic_items[i].ortho)
        else:
            ortho_forms.append(None)

    searched_kanji_word_sets = [set() for x in range(wlen)]
    searched_reading_sets = [set() for x in range(wlen)]

    scan_results['item_sense_ref'] = [[] for x in range(len(unidic_items))]
    scan_results['word_by_seq'] = dict()
    
    """
    Create a list of permutations of for phrases based on the original and basic/ortho form 
    of each word. 
    For example:
        お願いします 
        ----------------
        お + 願う
        お + 願い + する
        お + 願い + します

    Phrases are constructed from original words from the block, separated by any punctuation marks
    """
    pos = 0
    messages = [[] for _ in range(len(unidic_items))]
    while pos < len(unidic_items):
        permutations, next_pos = create_phrase_permutations(original_forms, ortho_forms, pos)
        if verbose_level>=1:
            LOG(2,"Permutations:")
            for p in permutations:
                p_str = [x.ljust(6) for x in p]
                LOG(2, "  %s" % (''.join(p_str)))
            LOG(2,"***********")

        # Scan this chunk with each permutation and for every lexical item get references 
        # (sequence number+sense index) to JMDict entries
        for permutated_chunk in permutations:
            scan_jmdict_for_phrase(permutated_chunk, pos, unidic_items, scan_results, searched_kanji_word_sets, searched_reading_sets)

        pos = next_pos

    ### POST PROCESSING

    scan_results['item_sense_idx_ref'] = []
    for i,(seq_senses) in enumerate(scan_results['item_sense_ref']):
        cl = unidic_items[i].cl
        # keep count of word occurrence by class
        scan_results['word_count_per_unidict_class'][cl] += 1

        # Fuse untethered small particles if marked for that
        if unidic_items[i].flags &  BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED:
            if len(seq_senses)==0 and i>0:
                # grab the references from previous item
                scan_results['item_sense_ref'][i] = scan_results['item_sense_ref'][i-1]

        # log missing references
        if verbose_level >= 1:
            if len(seq_senses) == 0:
                l_level = 1
                if cl <= punctuation_mark_class:
                    l_level = 3
                else:
                    STATS_NO_REFS(unidic_items[i], cl)
                LOG_HEADING()
                LOG(l_level," %d : %s Has no references because.. " % (i,unidic_items[i]))
                if len( messages[i]) == 0:
                    LOG(l_level," .. no matches in scanning",items=unidic_items)
                else:
                    for msg in messages[i]:
                        LOG(l_level,"  %s" % msg)
                    LOG(l_level,"",items=unidic_items)
            elif verbose_level >= 2:
                if len(messages[i])>0:
                    LOG_HEADING()
                    LOG(2," %d : %s Removed references.. " % (i,unidic_items[i]))
                    for msg in messages[i]:
                        print("\t%s" % (msg))
                    LOG(2,"\t.. remaining references:")
                    for seq_sense in seq_senses:
                        seq,senses = expand_sense_ref(seq_sense)
                        for sense in senses:
                            cl_list = jmdict_class_list_per_sense[seq][sense]
                            if len(cl_list) == 1:
                                LOG(2,"\t%s[%d/%d] %s %s" % (scan_results['word_by_seq'][seq_sense].ljust(6,'　'),seq,sense, jmdict_class_list[cl_list[0]], jmdict_meaning_per_sense[seq][sense]))
                            else:
                                LOG(2,"\t%s[%d/%d] %s with classes:" % (scan_results['word_by_seq'][seq_sense].ljust(6,'　'),seq, sense,jmdict_meaning_per_sense[seq][sense]))
                                for cl in cl_list:
                                    LOG(2,"\t\t\t- %s" % (jmdict_class_list[cl]))

        # Sort each particle/word reference by the size of the word/phrase 
        # it's referencing. The second sort criteria is the frequency of the entry
        if len(seq_senses)>1:
            #ref_sizes = dict()
            #for seq_sense in seq_senses:
            #    ref_sizes[seq_sense] = len(scan_results['word_by_seq'][seq_sense])
            #sorted_refs = dict(sorted(ref_sizes.items(), key=lambda x:x[1], reverse=True))
            ref_sizes = []
            for seq_sense in seq_senses:
                seq = int(seq_sense.split('/')[0])
                ref_sizes.append( (seq_sense,len(scan_results['word_by_seq'][seq_sense]), 
                    min(jmdict_kanji_element_freq[seq],jmdict_reading_freq[seq])) )
            ref_sizes.sort(key=lambda x:x[2], reverse=False)
            ref_sizes.sort(key=lambda x:x[1], reverse=True)
            
            scan_results['item_sense_ref'][i] = [x[0] for x in ref_sizes]

        refs = []
        for seq_s in scan_results['item_sense_ref'][i]:
            # add this seq/sense reference sense list for all the encompassing lexical items
            s_idx = scan_results['sense_list'].index(seq_s)
            refs.append(s_idx)
        scan_results['item_sense_idx_ref'].append(refs)


    # replace the jmdict seq_sense reference with idx number to the seq/sense list
    """
    item_sense_idx_ref = []
    for i, seq_senses in enumerate(scan_results['item_sense_ref']):
        refs = []
        for seq,sense in seq_senses:
            if sense == ALL_SENSES:
                seq_s = str(seq)
            else:
                seq_s = str(seq) + '/' + str(sense)

            try:
                w_idx = jmdict_word_list.index(scan_results['word_by_seq'][seq])
                if seq_s not in jmdict_word_senses[w_idx]:
                    jmdict_word_senses[w_idx] += [seq_s]
                jmdict_word_count[w_idx] += 1
            except:
                jmdict_word_list.append(scan_results['word_by_seq'][seq])
                jmdict_word_senses.append([seq_s])
                jmdict_word_count.append(1)
                w_idx = len(jmdict_word_list) - 1

            try:
                s_idx = jmdict_sense_list.index(seq_s)
            except:
                jmdict_sense_list.append(seq_s)
                jmdict_sense_word_index.append(w_idx)
                seq_cl_lists = jmdict_class_list_per_sense[seq]
                if sense == ALL_SENSES:
                    cl_list = [ cl for cls_per_sense in seq_cl_lists for cl in cls_per_sense]
                else:
                    cl_list = jmdict_class_list_per_sense[seq][sense]
                cl_list = list(set(cl_list)) # get rid of duplicates
                jmdict_sense_class_list.append(cl_list)
                s_idx = len(jmdict_sense_list) - 1

            if s_idx not in refs:
                refs.append(s_idx)
        item_sense_idx_ref.append(refs)
    """
    #return item_sense_idx_ref

def reassemble_block(original_lines, unidic_items, item_sense_ref):
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
            w = unidic_items[i].txt
            refs = item_sense_ref[i]
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
            cli = jmdict_class_list.index(cl_name)
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

        l_l = json.loads(d[3])
        jmdict_class_list_per_sense[seq] = l_l
        # flatten the class list for faster lookup
        jmdict_flat_class_list[seq] = [x for sense_cl_l in l_l for x in sense_cl_l]

        jmdict_kanji_element_freq[seq] = int(d[4])
        jmdict_reading_freq[seq] = int(d[5])

        if load_meanings:
            jmdict_meaning_per_sense[seq] = json.loads(d[6])

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

    # manual fixes to class references
    """
    for seq, jmdict_class_list in manual_additions_to_jmdict_classes.items():
        for cl in jmdict_class_list:
            jmdict_cl[seq].append(cl)
    """

    # create combined verb and noun classes for easier lookup
    for cl in jmdict_class_list:
        idx = jmdict_class_list.index(cl)
        if 'verb' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_verb_pos_list.append(idx)
        if 'copula' in cl:
            jmdict_verb_pos_list.append(idx)
        elif 'noun' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_noun_pos_list.append(idx)

