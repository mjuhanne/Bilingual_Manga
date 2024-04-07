import sys
from helper import *
from jmdict import *
from jp_parser_helper import *
from conjugation import *
from parser_logging import *
from unidic_preparser import *

_parser_initialized = False

jmdict_noun_pos_list = []
jmdict_verb_pos_list = []


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

The matching lexical items (from Fugashi/Unidic) were:
# お (prefix) + 母 (noun) + さん (suffix)
# This matching condition is one of those defined below
"""
def get_valid_senses_for_scanned_word(scanned_word, pos,num_scanned_items,items,seq):
    global messages # for debugging

    score_modifiers = dict()

    if scanned_word in hard_coded_seqs.keys():
        (unidic_class, wanted_seq) = hard_coded_seqs[scanned_word]
        if num_scanned_items == 1 and unidic_class in items[pos].classes:
            # いる / する / 私 clutter prevention: Don't carry any 
            # references to these words other than the sequence number selected here
            # User can check the other 9 homophones elsewhere though
            if seq == wanted_seq:
                return [ALL_SENSES], score_modifiers
            else:
                return [], score_modifiers

    scanned_word_jmd_cl_list_per_sense = get_class_list_by_seq(seq)
    valid_senses = [set() for x in range(num_scanned_items)]

    def check_valid_sense_exceptions(word,position,unidic_classes,jmd_cl):
        if len(scanned_word) >= HOMOPHONE_MATCHING_WORD_MINIMUM_LENGTH:
            # Sometimes Unidict just fails to parse pure Hiragana words..
            # For example ばんそうこう (bandage) becomes:
            #  ば (grammatical particle)
            #  ん (interjection)
            #  そうこう (adverb) ..
            # To allow matching these kinds of words we disregard the parsed classes
            # if the candidate word has a length of minimum of 5 characters 
            messages[position].append("%s(%s) failed otherwise but matching %s(%s) just due to length" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
            return True

        if num_scanned_items >= 4:
            # minimum of 4 lexical items also matches without considering classes
            return True
        
        if num_scanned_items == 3:
            # if 3 items have at least 2 kanjis then it's a match. This
            # is just to ward off ambiguities caused by hiragana-only items
            kanji_items = 0
            for i in range(num_scanned_items):
                if has_cjk(items[pos+i].txt):
                    kanji_items += 1
            if kanji_items >= 2:
                return True
            
        # let all medium sized words pass regardless of the class
        # but give them lower score. Words with kanji are given higher score
        if len(scanned_word) >= 4:
            if has_cjk(scanned_word):
                score_modifiers[ALL_SENSES] = 0.7
            else:
                score_modifiers[ALL_SENSES] = 0.4
            return True
        if len(scanned_word) >= 3:
            if has_cjk(scanned_word):
                score_modifiers[ALL_SENSES] = 0.5
            else:
                score_modifiers[ALL_SENSES] = 0.3
            return True

        # let all small sized words pass regardless of the class if they have kanji
        # but give them lower score
        if len(scanned_word) >= 2 and has_cjk(scanned_word):
            score_modifiers[ALL_SENSES] = 0.4
            return True
        if len(scanned_word) == 1 and has_cjk(scanned_word):
            score_modifiers[ALL_SENSES] = 0.3
            return True

        return False
            
    sw_len = len(scanned_word)

    for i in range(num_scanned_items):
        word = items[pos+i].txt
        unidic_classes = set(items[pos+i].classes)
        #if word in alternative_classes:
        #    unidic_classes.update(alternative_classes[word])
        is_last = (i==num_scanned_items-1)
        next_word = None
        next_word_classes = set()
        if not is_last:
            next_word = items[pos+i+1].txt
            next_word_classes = set(items[pos+i+1].classes)

        for s_idx, scanned_word_jmd_cl_list in enumerate(scanned_word_jmd_cl_list_per_sense):
            for jmd_cl in scanned_word_jmd_cl_list:
                if jmd_cl == jmdict_expression_class:
                        # everything is allowed as expression/phrase
                        valid_senses[i].update([s_idx])

                if jmd_cl == jmdict_suffix_class:
                    if noun_class in unidic_classes and pos>0:
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
                        if verb_class in next_word_classes or gp_class in next_word_classes:
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
                        if next_word == 'ら' and suffix_class in next_word_classes:
                            # noun or pronoun + ら can still be pronoun (奴ら/お前ら).
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])

                    if pronoun_class in unidic_classes:
                        if suffix_class in next_word_classes:
                            # pronoun + suffix can still be pronoun (私共).
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
                    if numeric_pseudoclass in unidic_classes and i == 0:
                        if num_scanned_items > 1:
                            # allow numeric class for noun if it's the first item and not alone
                            valid_senses[i].update([s_idx])
                    if verb_class in unidic_classes and items[pos].is_masu:
                            # allow masu-stem verb as noun
                            # e.g.　作り
                            valid_senses[i].update([s_idx])
                            if sw_len == 1:
                                score_modifiers[s_idx] = 0.5
                            elif sw_len == 2:
                                score_modifiers[s_idx] = 0.8

                    if rentaishi_class in unidic_classes and noun_class in next_word_classes:
                        # many nouns consist of rentaishi class + noun
                        # e.g. そのまま, その日
                        valid_senses[i].update([s_idx])

                    if adjective_class in unidic_classes and suffix_class in next_word_classes:
                        # allow adjective + suffix as noun
                        # 幼な + じみ
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])
                    if pronoun_class in unidic_classes and suffix_class in next_word_classes:
                        # allow prounoun + suffix as noun
                        #　俺 + たち
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

                if jmd_cl == jmdict_conjunction_class:
                    if noun_class in unidic_classes and next_word == 'に':
                        # 癖に
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

                if jmd_cl in jmdict_verb_pos_list:
                    if noun_class in unidic_classes and verb_class in next_word_classes:
                        # sometimes item detected as noun precede a verb:
                        # 風邪ひく, ご覧なさる, 旅する, 役立つ...
                        valid_senses[i].update([s_idx])
                    if noun_class in unidic_classes and suffix_class in next_word_classes:
                        # Same case as above but the verb is detected as suffix
                        # 不審がる -> 不審 (noun) + がる (suffix)
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

                if jmd_cl == jmdict_adjectival_noun_class:
                    if noun_class in unidic_classes and suffix_class in next_word_classes:
                        # noun + suffix can act as adjectival noun:
                        # 感傷 + 的
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])
                    if verb_class in unidic_classes and suffix_class in next_word_classes:
                        if items[pos].is_masu:
                            # verb in masu-stem + suffix can act as adjectival noun
                            # あり + がち
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])

                if jmd_cl == jmdict_adj_i_class:
                    if noun_class in unidic_classes and adjective_class in next_word_classes:
                        # noun + adjective can act as adjective:
                        # 辛抱 + 強い or 男 + らしい
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

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
            
            if len(valid_senses[i])==0:
                if items[pos+i].any_class:
                    messages[i].append("%s(%s) failed otherwise but preliminary matching %s(%s) just due ALL_CLASS" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
                    valid_senses[i].update([s_idx])
                    if sw_len == 1:
                        score_modifiers[s_idx] = 0.5
                    elif sw_len == 2:
                        score_modifiers[s_idx] = 0.7
                    elif sw_len >= 3:
                        score_modifiers[s_idx] = 0.9


        if len(valid_senses[i]) == 0:
            if check_valid_sense_exceptions(word,pos+i,unidic_classes,jmd_cl):
                return [ALL_SENSES], score_modifiers # no need to check other words

            messages[pos+i].append("%s(%s) has no matching class for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
            # This lexical item matched none of the senses for this word so no need to check other items
            return [], score_modifiers
        
    # get those senses that match all lexical items
    final_valid_senses = set.intersection(*valid_senses)
    if len(final_valid_senses) == len(scanned_word_jmd_cl_list_per_sense):
        return [ALL_SENSES], score_modifiers
    
    if len(final_valid_senses) == 0:
        # check the global exceptions once more in case some particles
        # match some senses and other particles match other senses
        if check_valid_sense_exceptions(scanned_word,pos,unidic_classes,jmd_cl):
            return [ALL_SENSES], score_modifiers # no need to check other words

    return list(final_valid_senses), score_modifiers


def add_matched_sense_reference(chunk, base_score, chunk_len, pos, seq, valid_senses, score_modifiers, scan_results):

    if has_word_katakana(chunk):
        # use always hiragana reading instead of katakana reading if it exists
        h_chunk = katakana_to_hiragana(chunk)
        readings = get_readings_by_seq(seq)
        if h_chunk in readings:
            chunk = h_chunk

    existing_seq_senses = [ 
        (wid.split(':')[0], len(wid.split(':')[1]), scan_results['item_word_id_ref_count'][(wid,pos)])
            for wid in scan_results['item_word_ids'][pos]
    ]

    for sense in valid_senses:
        score_mod = 1
        if sense == ALL_SENSES:
            word_id = str(seq) + ":" + chunk
            seq_sense = str(seq)
            if len(score_modifiers)>0:
                score_mod = next(iter(score_modifiers.values()))
        else:
            word_id = str(seq) + '/' + str(sense) + ":" + chunk
            seq_sense = str(seq) + '/' + str(sense)
            if sense in score_modifiers:
                score_mod = score_modifiers[sense]

        #if word_id not in scan_results['item_word_ids'][pos]:
        if (seq_sense,len(chunk), chunk_len) not in existing_seq_senses:
            # add this word id (seq/sense:word) reference for all the encompassing lexical items
            for j in range(chunk_len):
                scan_results['item_word_ids'][pos+j].append(word_id)

            # add the chunk len and score for each found word id (seq/sense:word)  position
            # for prioritizing purposes
            freq = get_frequency_by_seq_and_word(seq,chunk)
            freq = 100-freq
            pos_score = max(0,6-pos)*20
            score = (len(chunk)*30 + base_score*30 + freq + pos_score)*chunk_len
            score = int(score*score_mod)
            # increase score from hard-coded seq list
            if word_id in priority_word_ids:
                score += priority_word_ids[word_id]
            for j in range(chunk_len):
                scan_results['item_word_id_ref_count'][(word_id,pos+j)] = chunk_len
                scan_results['item_word_id_ref_pos'][(word_id,pos+j)] = j
                scan_results['item_word_id_score'][(word_id,pos+j)] = score

            # add to word id list and word_class (parts of speech) list
            try:
                w_idx = scan_results['word_id_list'].index(word_id)
                scan_results['word_count'][w_idx] += 1
            except:
                scan_results['word_id_list'].append(word_id)
                seq_cl_lists = get_class_list_by_seq(seq)
                if sense == ALL_SENSES:
                    cl_list = [ cl for cls_per_sense in seq_cl_lists for cl in cls_per_sense]
                else:
                    cl_list = seq_cl_lists[sense]
                cl_list = list(set(cl_list)) # get rid of duplicates
                scan_results['word_class_list'].append(cl_list)
                scan_results['word_count'].append(1)


# this will scan for all the possible dictionary entries in the jmdict set
# (either kanji_elements or readings) using the given phrase
# and starting at position pos.  
def greedy_jmdict_scanning(phrase, scores, items, scan_results, searched_chunk_sets, 
        start_pos, min_word_len, jmdict_set, jmdict_seq_dict, max_jmdict_len):
    lp = len(phrase) # length of phrase in particles
    
    cycle_pos = 0
    while True:

        i = start_pos + cycle_pos
        clen = 0
        chunk = ''
        score = 0
        if not (phrase[cycle_pos] == '' or (items[i].flags & START_OF_SCAN_DISABLED)):
            while (cycle_pos + clen < lp):

                chunk += phrase[cycle_pos + clen]
                score += scores[cycle_pos + clen]
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
                                senses, score_modifiers = get_valid_senses_for_scanned_word(chunk,i,clen,items,seq)
                                if len(senses)>0:
                                    add_matched_sense_reference(chunk, score, clen, i, seq, senses, score_modifiers, scan_results)

                    searched_chunk_sets[i].add(chunk)

        cycle_pos += 1
        if cycle_pos > lp - 1:
            return

# Returns a list of phrase permutations and a new start position for next round.
# Permutations are created using original particles/words and ending with 
# an ortho/basic form. Scanning stops when non-Hiragana/Katakana/Kanji character was
# detected
MAX_RECURSION_LEVELS = 5
APPENDABLE_ALT_FORM_SCORE_MODIFIER = 0.7
END_TYPE_ALT_FORM_SCORE_MODIFIER = 0.8
#ORIGINAL_FORM_SCORE_MODIFIER = +5
def create_phrase_permutations(original_words, base_scores, alt_scores, end_type_forms, appendable_forms, items, start=0, recursive_start=None, recursive_level=0):

    # appendable_Forms.append(items[i].txt )  !!!
    permutations = []
    scores = []
    max_recursion_level_index = -1
    if recursive_level < MAX_RECURSION_LEVELS:
        if recursive_start is not None:
            i = recursive_start
        else:
            i = start
        # appendable alternative forms can permutate recursively
        while i<len(original_words) and (not (items[i].flags & NO_SCANNING) ) and (max_recursion_level_index == -1):
            if len(appendable_forms[i])>0:
                for alt_form in [original_words[i]] + appendable_forms[i]:
                    neighbour_alt_score_modifier = 1
                    new_words = original_words[:i] + [alt_form] + original_words[i+1:]
                    if alt_form in alt_scores[i]:
                        score = alt_scores[i][alt_form]
                        if alt_form in items[i].neighbour_alt_score_modifier:
                            neighbour_alt_score_modifier = items[i].neighbour_alt_score_modifier[alt_form]
                    else:
                        score = base_scores[i]
                    #if alt_form == original_words[i]:
                    #    score += ORIGINAL_FORM_SCORE_MODIFIER
                    if alt_form != original_words[i]:
                        score = int(score*APPENDABLE_ALT_FORM_SCORE_MODIFIER)
                    if neighbour_alt_score_modifier == 1 or (i==len(base_scores)-1):
                        new_base_scores = base_scores[:i] + [score] + base_scores[i+1:]
                    else:
                        new_base_scores = base_scores[:i] + [score] + [base_scores[i+1]*neighbour_alt_score_modifier] + base_scores[i+2:]
                    new_perms,new_scores, _, max_rec_level = create_phrase_permutations(new_words, new_base_scores, alt_scores, end_type_forms, appendable_forms, items, start, i+1, recursive_level+1)
                    if max_rec_level != -1:
                        max_recursion_level_index = max_rec_level
                    permutations += new_perms
                    scores += new_scores
            i += 1
    else:
        max_recursion_level_index = recursive_start

    # .. whereas end type alternative forms will be the end of this branch
    if recursive_start is not None:
        i = recursive_start
    else:
        i = start
    while i<len(original_words) and (not (items[i].flags & NO_SCANNING) ) and (i != max_recursion_level_index):
        permutation_root = original_words[start:i]
        score_root = base_scores[start:i]
        for alt_form in end_type_forms[i]:
            permutations.append(permutation_root + [alt_form])
            if alt_form in alt_scores[i]:
                score = alt_scores[i][alt_form]
            else:
                score = base_scores[i]
            #if alt_form == original_words[i]:
            #    score += ORIGINAL_FORM_SCORE_MODIFIER
            score = int(score*END_TYPE_ALT_FORM_SCORE_MODIFIER)
            scores.append(score_root + [score])
        i += 1
    
    if i> 0:
        # finally add the whole original as one permutation
        orig = original_words[start:i]
        if orig not in permutations:
            permutations = [orig] + permutations
            orig_scores = base_scores[start:i]
            scores = [orig_scores] + scores
    if i<len(original_words) and (max_recursion_level_index == -1):
        i += 1  # add one because the last one was a punctuation etc..
    elif max_recursion_level_index != -1:
        i -= 1  # start next round 1 item earlier to create overlap if recursion process
        # was cut prematurely
    return permutations, scores, i, max_recursion_level_index


def scan_jmdict_for_phrase( phrase, scores, pos, items, scan_results, searched_kanji_word_set, searched_reading_set):

    greedy_jmdict_scanning(phrase, scores, items, scan_results, searched_kanji_word_set, pos, 1, jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len)
    greedy_jmdict_scanning(phrase, scores, items, scan_results, searched_reading_set, pos, 1, jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len)

def init_scan_results():
    scan_results = dict()
    scan_results['word_id_list'] = []
    scan_results['word_count'] = []
    scan_results['word_class_list'] = []
    scan_results['word_count_per_unidict_class'] = \
        [0 for x in range(len(unidic_class_list))] 
    scan_results['priority_word_id_list'] = []
    scan_results['priority_word_count'] = []
    return scan_results


def parse_with_jmdict(unidic_items, scan_results):
    global messages
    if not _parser_initialized:
        raise Exception("Not yet initialized!")
    
    def add_to_priority_word_list(word_id):
        priority_wid_list = scan_results['priority_word_id_list']
        priority_wid_count = scan_results['priority_word_count']
        if word_id in priority_wid_list:
            idx = priority_wid_list.index(word_id)
            priority_wid_count[idx] += 1
        else:
            priority_wid_list.append(word_id)
            idx = len(priority_wid_list) - 1
            priority_wid_count.append(1)

    scan_results['item_word_ids'] = [[] for x in range(len(unidic_items))]
    scan_results['item_word_id_ref_count'] = dict()
    scan_results['item_word_id_ref_pos'] = dict()
    scan_results['item_word_id_score'] = dict()

    # By default we use lexical items in the form they word in the original text
    # Example: お願いします -> お + 願い + します

    # In order to do more exhaustive scanning we also construct 
    # a list of alternative (basic/ortho) forms if they differ from the originals.
    # Example: お願いします -> お + 願う + する
    wlen = len(unidic_items)
    appendable_forms = [[] for x in range(wlen)]
    end_type_forms = [[] for x in range(wlen)]
    original_forms = [item.txt for item in unidic_items]
    base_scores = [item.base_score for item in unidic_items]
    alt_scores = [item.alt_scores for item in unidic_items]
    for i, item in enumerate(unidic_items):
        appendable_forms[i] += item.appendable_alt_forms
        if not (item.flags & (NO_SCANNING | DISABLE_ORTHO)):
            if (item.txt != item.ortho) and item.ortho != '':
                if item.ortho not in appendable_forms[i]:
                    end_type_forms[i].append(item.ortho)
            for alt_form in item.alt_forms:
                if alt_form not in end_type_forms[i]:
                    if alt_form not in appendable_forms[i]:
                        end_type_forms[i].append(alt_form)
        if item.flags & SCAN_WITH_LEMMA:
            end_type_forms[i].append(item.lemma)

        #if elongation_mark_class in item.classes:
        #    end_type_forms[i].append('')  # add one permutation without the elongation mark

        wid = unidic_items[i].word_id
        if wid != '':
            # add explicit word id reference
            seq,sense,word = get_word_id_components(wid)
            add_matched_sense_reference(word,item.base_score,1,i,seq,[sense],{},scan_results) 

    searched_kanji_word_sets = [set() for x in range(wlen)]
    searched_reading_sets = [set() for x in range(wlen)]

    
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
        permutations, scores, next_pos, _ = create_phrase_permutations(original_forms, base_scores, alt_scores, end_type_forms, appendable_forms, unidic_items, pos)
        if get_verbose_level()>=1:
            LOG(1,"Permutations %d-%d" % (pos,next_pos-1))
            for perms,sc in zip(permutations,scores):
                p_str = [("%s(%d)" % (p,s)).ljust(6) for p,s in zip(perms,sc)]
                LOG(1, "  %s" % (''.join(p_str)))
            LOG(1,"***********")

        # Scan this chunk with each permutation and for every lexical item get references 
        # (sequence number+sense index) to JMDict entries
        for i, permutated_chunk in enumerate(permutations):
            if len(permutated_chunk)>0:
                chunk_scores = scores[i]
                scan_jmdict_for_phrase(permutated_chunk, chunk_scores, pos, unidic_items, scan_results, searched_kanji_word_sets, searched_reading_sets)

        pos = next_pos

    ### POST PROCESSING

    scan_results['item_word_id_refs'] = []
    scan_results['item_word_id_scores'] = []
    scan_results['item_longest_common_word_id'] = []
    
    for i,(word_ids) in enumerate(scan_results['item_word_ids']):
        pos_ref_index = i
        cll = unidic_items[i].classes
        # keep count of word occurrence by class. 
        # Use only last class in the list (most likely the correct one) 
        # to avoid double counting
        scan_results['word_count_per_unidict_class'][cll[-1]] += 1

        # Fuse untethered small particles if marked for that
        if unidic_items[i].flags &  BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED:
            if len(word_ids)==0 and i>0:
                # grab the references from previous item
                word_ids = scan_results['item_word_ids'][i-1]
                pos_ref_index = i - 1

        # log missing references
        if get_verbose_level() >= 1:
            if len(word_ids) == 0:
                l_level = 1
                if len(cll)==1 and cll[0] <= punctuation_mark_class:
                    l_level = 3
                else:
                    STATS_NO_REFS(unidic_items[i], cll[-1])
                LOG_HEADING()
                LOG(l_level," %d : %s Has no references because.. " % (i,unidic_items[i]))
                if len( messages[i]) == 0:
                    LOG(l_level," .. no matches in scanning",items=unidic_items)
                else:
                    for msg in messages[i]:
                        LOG(l_level,"  %s" % msg)
                    LOG(l_level,"",items=unidic_items)
            elif get_verbose_level() >= 2:
                if len(messages[i])>0:
                    LOG_HEADING()
                    LOG(2," %d : %s Removed references.. " % (i,unidic_items[i]))
                    for msg in messages[i]:
                        print("\t%s" % (msg))
                    LOG(2,"\t.. remaining references:")
                    for word_id in word_ids:
                        seq,senses,word = expand_word_id(word_id)
                        score = scan_results['item_word_id_score'][(word_id,pos_ref_index)]
                        for sense in senses:
                            cl_list = get_class_list_by_seq(seq)[sense]
                            meanings = get_meanings_by_sense(seq,sense)
                            if len(cl_list) == 1:
                                LOG(2,"\t%s %d [%d/%d] %s %s" % (word.ljust(6,'　'),score,seq,sense, jmdict_class_list[cl_list[0]], meanings))
                            else:
                                LOG(2,"\t%s %d [%d/%d] %s with classes:" % (word.ljust(6,'　'),score, seq, sense, meanings))
                                for cl in cl_list:
                                    LOG(2,"\t\t\t- %s" % (jmdict_class_list[cl]))

        # Sort each JMDict reference by its scoring
        longest_common_word_id = 0
        if len(word_ids)>0:
            scoring = []
            for word_id in word_ids:
                seq,senses,word = expand_word_id(word_id)
                word = word_id.split(':')[1]
                score = scan_results['item_word_id_score'][(word_id,pos_ref_index)]
                refs = scan_results['item_word_id_ref_count'][(word_id,pos_ref_index)]
                if refs > longest_common_word_id:
                    longest_common_word_id = refs
                scoring.append( (word_id,score) )
            scoring.sort(key=lambda x:x[1], reverse=True)
            word_ids = [x[0] for x in scoring]
            word_id_scores = [score for (word_id,score) in scoring] # get only the score
        else:
            word_id_scores = []
        scan_results['item_word_id_scores'].append(word_id_scores)
        scan_results['item_word_ids'][i] = word_ids
        scan_results['item_longest_common_word_id'].append(longest_common_word_id)

    best_score, best_combination = calculate_best_phrase_combination(unidic_items,scan_results)
    scan_results['score'] = best_score

    for i,(word_ids) in enumerate(scan_results['item_word_ids']):
        refs = []
        if len(word_ids)>0:
            best_word_id = best_combination[i]
            # always select the best word_id first in the list
            if word_ids[0] != best_word_id:
                if best_word_id == '':
                    # TODO: add empty word
                    pass
                else:
                    best_idx = word_ids.index(best_word_id)
                    word_ids.pop(best_idx)
                    word_ids = [best_word_id] + word_ids
                    best_w_score = scan_results['item_word_id_scores'][i].pop(best_idx)
                    scan_results['item_word_id_scores'][i] = [best_w_score] + scan_results['item_word_id_scores'][i]

            if best_word_id != '':
                # add the best word id to priority word list and increment freq count
                ref_count = scan_results['item_word_id_ref_count'][(best_word_id,i)]
                if scan_results['item_word_id_ref_pos'][(best_word_id,i)] == 0:
                    add_to_priority_word_list(best_word_id)
                if ref_count > 1:
                    # this best word_id is a phrase (consists of multiple lexical items)
                    # e.g. 手を出す
                    # in addition to the phrase itself, we want to add 
                    # each item (手 + を + 出す)
                    # to the priority word list
                    if len(word_ids)>1:
                        next_best_word = word_ids[1]
                        if scan_results['item_word_id_ref_pos'][(next_best_word,i)] == 0:
                            if scan_results['item_word_id_ref_count'][(next_best_word,i)] == 1:
                                add_to_priority_word_list(next_best_word)

            # reference the word_id as index number in word_id_list
            for word_id in word_ids:
                w_idx = scan_results['word_id_list'].index(word_id)
                refs.append(w_idx)
        scan_results['item_word_id_refs'].append(refs)

    # these are not needed anymore
    del(scan_results['item_word_id_ref_pos'])
    del(scan_results['item_word_id_ref_count'])
    del(scan_results['item_word_id_score'])
    del(scan_results['item_longest_common_word_id'])


def calculate_best_phrase_combination(items,scan_results):
    best_score = 0
    best_permutation = []
    pos = 0
    while pos < len(items):
        best_chunk_score, best_chunk_permutation, rec_fail = \
            do_calculate_best_phrase_combination(pos,items,scan_results)
        LOG(1,"Chunk permutation score : %d %s" % (best_score, best_permutation))
        if len(best_chunk_permutation)>0:
            best_score += best_chunk_score
            best_permutation += best_chunk_permutation
            pos += len(best_chunk_permutation)
        else:
            best_permutation += ['']
            pos += 1

    LOG(1,"Best phrase permutation: %d %s" % (best_score, best_permutation))
    return best_score, best_permutation

def do_calculate_best_phrase_combination(pos,items,scan_results, rec_level=0):
    best_score = -1
    best_combination = []

    if rec_level >= 16:
        # too many recursion levels so just return the first score/word_id in the list (it's already sorted)
        # and continue from the next word with level 0
        if len(scan_results['item_word_id_scores'][pos])>0:
            return scan_results['item_word_id_scores'][pos][0], [scan_results['item_word_ids'][pos][0]], True
        else:
            return 0, [], True

    if items[pos].flags & NO_SCANNING:
        return 0, [], False
    
    if scan_results['item_longest_common_word_id'][pos]==1:
        # this lexical item references only words that are not shared by other items
        # so we can return the first score/word_id in the list (it's already sorted)
        return scan_results['item_word_id_scores'][pos][0], [scan_results['item_word_ids'][pos][0]], False

    _word_ids = scan_results['item_word_ids'][pos]
    _word_id_scores = scan_results['item_word_id_scores'][pos]
    word_ids = _word_ids + ['']
    word_id_scores = _word_id_scores + [-300]
    processed_words = set()
    for word_id,score in zip(word_ids,word_id_scores):
        print_prefix = "\t"*pos
        if word_id != '':
            seq,senses,word = expand_word_id(word_id)
            word = word_id.split(':')[1]
            ref_pos = scan_results['item_word_id_ref_pos'][(word_id,pos)]
            ref_steps = scan_results['item_word_id_ref_count'][(word_id,pos)]
        else:
            word = ''
            ref_pos = 0
            ref_steps = 1

        if ref_pos == 0:
            # check only from the first element of each word_id
            combination = [word_id]*ref_steps
            if word not in processed_words:
                processed_words.add(word)

                #print(print_prefix,pos,word)
                print_prefix += "  "
                if pos + ref_steps < len(items):
                    #print(print_prefix,pos,"Trying sub-items at pos %d" % (pos+ref_steps), scan_results['item_word_ids'][pos+ref_steps])
                    best_sub_score, best_sub_combination, fail_rec = do_calculate_best_phrase_combination(pos+ref_steps,items,scan_results, rec_level+1)
                    if fail_rec:
                        # too many recursion levels
                        return best_score, best_combination, True

                    #print(print_prefix,pos,"Result score(%d) + sub " % score,best_sub_score,best_sub_combination)

                    score += best_sub_score
                    combination += best_sub_combination
                if rec_level==0:
                    LOG(1,"Combination score %d: %s" % (score,combination))


                if score > best_score:
                    best_score = score
                    best_combination = combination
                    #print(print_prefix,pos,"Best: ",best_score,best_combination)
    return best_score, best_combination, False

def parse_block_with_unidic(lines, kanji_count):

    kansai_ben = ['']
    # どった
    # ったんか  ta-no-ka?

    # unidic will generally parse text more reliably if the whole block is processed as one line
    line = ''.join(lines)
    kc, ud_items = parse_line_with_unidic(line,kanji_count)

    # check if the first item is wrongly aux verb
    #if ud_items[0].classes[0] == aux_verb_class:
    #    print(bcolors.FAIL,"First item is aux verb! %s in %s" % (ud_items[0].txt,line),bcolors.ENDC)

    # HOWEVER, there are times when unidic will match erroneously a word between the lines:
    # e.g.  two line block ['あ～～あ', 'なんてこった']
    # will be parsed into following lexical elements:
    # ['あ','～～',あなん,'て','こった']
    # In this case unidic will find a word 'あなん' which wasn't there in the first place
    # so we want to dissect it
    line_pos = 0
    line_idx = 0
    item_idx = 0
    mismatch = False
    item_txt_list = [item.txt for item in ud_items]
    """

    if '３０４３０５' in line:
        pass

    failed = False
    while item_idx < len(item_txt_list) and not failed:
        remaining_line = lines[line_idx][line_pos:]
        if remaining_line == '':
            print("TODO !!!!!!!!")
            failed = True
        else:

            if item_txt_list[item_idx] not in remaining_line:            
                mismatch = True
                part1 = item_txt_list[item_idx][:len(remaining_line)]
                part2 = item_txt_list[item_idx][len(part1):]
                cll = ud_items[item_idx].classes
                
                ud_items[item_idx].flags |= REPLACE_ITEM
                ud_items[item_idx].txt = part1
                ud_items[item_idx].is_masu = False
                ud_items[item_idx].any_class = True
                item2 = LexicalItem(part2,'',cll)
                item2.any_class = True
                ud_items[item_idx].replaced_items = [
                    ud_items[item_idx],
                    item2
                ]

            line_pos += len(item_txt_list[item_idx])
            item_idx += 1
            if line_pos >= len(lines[line_idx]):
                line_pos -= len(lines[line_idx])
                line_idx += 1

    if not failed:
        if mismatch:
            LOG(1,"Unidic parsing mismatch %s vs %s. Dividing items" % (str(lines),str(item_txt_list)))
            ud_items = merge_or_replace_items(ud_items)

    """
    while item_idx < len(item_txt_list) and not mismatch:
        if item_txt_list[item_idx] not in lines[line_idx][line_pos:]:
            #print("Possible mismatch: %s (%s)" % (ud_items[item_idx].txt,unidic_class_to_string(ud_items[item_idx].classes[0])))
            if aux_verb_class not in ud_items[item_idx].classes or \
                  ud_items[item_idx].txt == 'です': #or \
                #ud_items[item_idx].txt == 'でし':
                mismatch = True
            else:
                line_pos += len(item_txt_list[item_idx])
                item_idx += 1
        else:
            line_pos += len(item_txt_list[item_idx])
            item_idx += 1
        if line_pos >= len(lines[line_idx]):
            line_pos -= len(lines[line_idx])
            line_idx += 1

    if mismatch:
        LOG(1,"Unidic parsing mismatch %s vs %s" % (str(lines),str(item_txt_list)))
        #print("\nUnidic parsing mismatch %s vs \n%s" % (str(lines),str(item_txt_list)))
        ud_items = []
        kc = 0
        for line in lines:
            line_kc, line_ud_items = parse_line_with_unidic(line,kanji_count)
            kc += line_kc
            ud_items += line_ud_items
        item_txt_list = [item.txt for item in ud_items]
        LOG(1,"New parse results %s" % (str(item_txt_list)))
        #print("New parse results: \n%s" % (str(item_txt_list)))
        pass
    return kc, ud_items

def reassemble_block(original_lines, unidic_items, item_word_ref): #, item_word_scores):
    # re-assemble this block back into lines (list of lists)
    i = 0
    block_word_ref = []
    block_word_scores = []
    next_new_line_str = ''
    next_new_line = []
    #next_new_line_scores = []
    for line in original_lines:
        if len(next_new_line_str) <= len(line):
            new_line = next_new_line
            #new_line_scores = next_new_line_scores
        else:
            new_line = []
            #new_line_scores = []
            w = next_new_line_str
        new_line_str = next_new_line_str
        next_new_line_str = ''
        next_new_line = []
        #next_new_line_scores = []
        while line not in new_line_str:
            w = unidic_items[i].txt
            refs = item_word_ref[i]
            #scores = item_word_scores[i]
            new_line_str += w
            i += 1

            if len(new_line_str) <= len(line):
                new_line.append({w:refs})
                #new_line_scores.append(scores)

        if len(new_line_str) > len(line):
            # some of the particles were fused temporarily for scanning purposes. 
            # Don't want to lengthen a line so let's break them up again
            next_new_line_str = new_line_str[len(line):]
            num_extra_characters = len(new_line_str) - len(line)
            w = w[:-num_extra_characters]
            next_new_line = [{next_new_line_str:refs}]
            #next_new_line_scores = [scores]
            new_line.append({w:refs})
            #new_line_scores.append(scores)

        block_word_ref.append(new_line)
        #block_word_scores.append(new_line_scores)
    
    return block_word_ref #, block_word_scores


def reassemble_block_scores(original_lines, unidic_items, item_word_scores):
    # re-assemble this block back into lines (list of lists)
    i = 0
    block_word_scores = []
    next_new_line_str = ''
    next_new_line_scores = []
    for line in original_lines:
        if len(next_new_line_str) <= len(line):
            new_line_scores = next_new_line_scores
        else:
            new_line_scores = []
            w = next_new_line_str
        new_line_str = next_new_line_str
        next_new_line_str = ''
        next_new_line_scores = []
        while line not in new_line_str:
            w = unidic_items[i].txt
            scores = item_word_scores[i]
            new_line_str += w
            i += 1

            if len(new_line_str) <= len(line):
                new_line_scores.append(scores)

        if len(new_line_str) > len(line):
            # some of the particles were fused temporarily for scanning purposes. 
            # Don't want to lengthen a line so let's break them up again
            next_new_line_str = new_line_str[len(line):]
            num_extra_characters = len(new_line_str) - len(line)
            w = w[:-num_extra_characters]
            next_new_line_scores = [scores]
            new_line_scores.append(scores)

        block_word_scores.append(new_line_scores)
    
    return block_word_scores


def init_parser(load_meanings=False):
    global jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len
    global jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len
    global _parser_initialized
    global jmdict_noun_pos_list, jmdict_verb_pos_list

    load_jmdict(load_meanings=load_meanings)
    load_conjugations()

    jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len = get_jmdict_kanji_element_set()
    jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len = get_jmdict_reading_set()

    # create combined verb and noun classes for easier lookup
    for cl in jmdict_class_list:
        idx = jmdict_class_list.index(cl)
        if 'verb' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_verb_pos_list.append(idx)
        if 'copula' in cl:
            jmdict_verb_pos_list.append(idx)
        elif 'noun' in cl and idx not in allowed_other_class_bindings.keys():
            jmdict_noun_pos_list.append(idx)
    _parser_initialized = True
