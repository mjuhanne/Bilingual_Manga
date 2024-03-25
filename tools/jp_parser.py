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

    if scanned_word in hard_coded_seqs.keys():
        (unidic_class, wanted_seq) = hard_coded_seqs[scanned_word]
        if num_scanned_items == 1 and unidic_class in items[pos].classes:
            # いる / する / 私 clutter prevention: Don't carry any 
            # references to these words other than the sequence number selected here
            # User can check the other 9 homophones elsewhere though
            if seq == wanted_seq:
                return [ALL_SENSES]
            else:
                return []

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

        """
        prev_word_in_block = None
        prev_word_in_block_classes = set()
        if pos + i - 1 >= 0:
            prev_word_in_block = items[pos+i-1].txt
            prev_word_in_block_classes = set(items[pos+i-1].classes)
            #if prev_word_in_block in alternative_classes:
            #    prev_word_in_block_classes.update(alternative_classes[prev_word_in_block])
        """

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

                if jmd_cl in jmdict_noun_pos_list:
                    if prefix_class in unidic_classes and i == 0:
                        if num_scanned_items > 1:
                            # allow prefix for noun if it's the first item and not alone
                            valid_senses[i].update([s_idx])
                    if suffix_class in unidic_classes and is_last:
                        if num_scanned_items > 1:
                            # allow suffix for noun if it's the last item and not alone
                            valid_senses[i].update([s_idx])
                    """
                    if verb_class in unidic_classes and items[pos].is_masu:
                        if noun_class in next_word_classes:
                            # allow masu-stem verb + noun as noun
                            # e.g. 食べ + 放題
                            valid_senses[i].update([s_idx])
                            valid_senses[i+1].update([s_idx])
                    """
                    if verb_class in unidic_classes and items[pos].is_masu:
                            # allow masu-stem verb as noun
                            # e.g.　作り
                            valid_senses[i].update([s_idx])

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

        if len(valid_senses[i]) == 0:
            if check_valid_sense_exceptions(word,pos+i,unidic_classes,jmd_cl):
                return [ALL_SENSES] # no need to check other words

            messages[pos+i].append("%s(%s) has no matching class for %s(%s)" % (word, unidic_classes_to_string(unidic_classes), scanned_word, jmdict_class_list[jmd_cl]))
            # This lexical item matched none of the senses for this word so no need to check other items
            return []
        
    # get those senses that match all lexical items
    final_valid_senses = set.intersection(*valid_senses)
    if len(final_valid_senses) == len(scanned_word_jmd_cl_list_per_sense):
        return [ALL_SENSES]
    
    if len(final_valid_senses) == 0:
        # check the global exceptions once more in case some particles
        # match some senses and other particles match other senses
        if check_valid_sense_exceptions(scanned_word,pos,unidic_classes,jmd_cl):
            return [ALL_SENSES] # no need to check other words

    return list(final_valid_senses)


def add_matched_sense_reference(chunk, chunk_len, pos, seq, valid_senses, scan_results):
    for sense in valid_senses:
        if sense == ALL_SENSES:
            word_id = str(seq) + ":" + chunk
        else:
            word_id = str(seq) + '/' + str(sense) + ":" + chunk

        # add this word id (seq/sense:word) reference for all the encompassing lexical items
        for j in range(chunk_len):
            scan_results['item_word_ids'][pos+j].append(word_id)

        # add the chunk len for each found  word id (seq/sense:word)  position
        # for prioritizing purposes
        for j in range(chunk_len):
            scan_results['item_word_id_ref_count'][(word_id,pos+j)] = chunk_len

        # add word id to word id list and list
        # also its Parts of Speech classes
        try:
            w_idx = scan_results['word_id_list'].index(word_id)
            scan_results['word_count'][w_idx] += 1
        except:
            scan_results['word_id_list'].append(word_id)
            #scan_results['sense_word_index'].append(w_idx)
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
def greedy_jmdict_scanning(phrase, items, scan_results, searched_chunk_sets, 
        start_pos, min_word_len, jmdict_set, jmdict_seq_dict, max_jmdict_len):
    lp = len(phrase) # length of phrase in particles
    
    cycle_pos = 0
    while True:

        i = start_pos + cycle_pos
        clen = 0
        chunk = ''
        if not (phrase[cycle_pos] == '' or (items[i].flags & START_OF_SCAN_DISABLED)):
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
MAX_PERMUTATION_LEVELS = 4
def create_phrase_permutations(original_words, ortho_forms, alt_forms, items, start=0, recursive_start=None, recursive_level=0):
    if recursive_start is not None:
        i = recursive_start
    else:
        i = start
    permutations = []
    while i<len(original_words) and (not (items[i].flags & NO_SCANNING) ):
        permutation_base = original_words[start:i]
        for ortho_form in ortho_forms[i]:
            permutations.append(permutation_base + [ortho_form])

        if recursive_level < MAX_PERMUTATION_LEVELS:
            for alt_form in alt_forms[i]:
                new_words = original_words[:i] + [alt_form] + original_words[i+1:]
                new_perms,i2 = create_phrase_permutations(new_words, ortho_forms, alt_forms, items, start, i+1, recursive_level+1)
                permutations += new_perms

        i += 1
    
    if i> 0:
        # finally add the whole original as one permutation
        #permutations.append(original_words[start:i])
        permutations = [original_words[start:i]] + permutations
    if i<len(original_words):
        i += 1  # add one because the last one was a punctuation etc..
    return permutations, i


def scan_jmdict_for_phrase( phrase, pos, items, scan_results, searched_kanji_word_set, searched_reading_set):

    greedy_jmdict_scanning(phrase, items, scan_results, searched_kanji_word_set, pos, 1, jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len)
    greedy_jmdict_scanning(phrase, items, scan_results, searched_reading_set, pos, 1, jmdict_readings, jmdict_reading_seq, jmdict_max_reading_len)

def init_scan_results():
    scan_results = dict()
    scan_results['word_id_list'] = []
    scan_results['word_count'] = []
    scan_results['word_class_list'] = []
    scan_results['word_count_per_unidict_class'] = \
        [0 for x in range(len(unidic_class_list))] 
    return scan_results


def parse_with_jmdict(unidic_items, scan_results):
    global messages
    if not _parser_initialized:
        raise Exception("Not yet initialized!")

    scan_results['item_word_ids'] = [[] for x in range(len(unidic_items))]
    scan_results['item_word_id_ref_count'] = dict()

    # By default we use lexical items in the form they word in the original text
    # Example: お願いします -> お + 願い + します

    # In order to do more exhaustive scanning we also construct 
    # a list of alternative (basic/ortho) forms if they differ from the originals.
    # Example: お願いします -> お + 願う + する
    wlen = len(unidic_items)
    alt_forms = [[] for x in range(wlen)]
    ortho_forms = [[] for x in range(wlen)]
    original_forms = [item.txt for item in unidic_items]
    for i, item in enumerate(unidic_items):
        alt_forms[i] += item.alt_forms
        if not (item.flags & (NO_SCANNING | DISABLE_ORTHO)):
            if (item.txt != item.ortho) and item.ortho != '':
                ortho_forms[i].append(item.ortho)
        if item.flags & SCAN_WITH_LEMMA:
            alt_forms[i].append(item.lemma)
        if elongation_mark_class in item.classes:
            alt_forms[i].append('')  # add one permutation without the elongation mark

        wid = unidic_items[i].word_id
        if wid != '':
            seq,sense,word = get_word_id_components(wid)
            add_matched_sense_reference(word,1,i,seq,[sense],scan_results) 

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
        permutations, next_pos = create_phrase_permutations(original_forms, ortho_forms, alt_forms, unidic_items, pos)
        if verbose_level>=1:
            LOG(2,"Permutations %d-%d" % (pos,next_pos-1))
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

    scan_results['item_word_id_refs'] = []
    
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
        if verbose_level >= 1:
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
            elif verbose_level >= 2:
                if len(messages[i])>0:
                    LOG_HEADING()
                    LOG(2," %d : %s Removed references.. " % (i,unidic_items[i]))
                    for msg in messages[i]:
                        print("\t%s" % (msg))
                    LOG(2,"\t.. remaining references:")
                    for word_id in word_ids:
                        seq,senses,word = expand_word_id(word_id)
                        for sense in senses:
                            cl_list = get_class_list_by_seq(seq)[sense]
                            meanings = get_meanings_by_sense(seq,sense)
                            if len(cl_list) == 1:
                                LOG(2,"\t%s[%d/%d] %s %s" % (word.ljust(6,'　'),seq,sense, jmdict_class_list[cl_list[0]], meanings))
                            else:
                                LOG(2,"\t%s[%d/%d] %s with classes:" % (word.ljust(6,'　'),seq, sense, meanings))
                                for cl in cl_list:
                                    LOG(2,"\t\t\t- %s" % (jmdict_class_list[cl]))

        # Sort each JMDict reference by following criteria:
        # 1) length of the JMDict word/phrase.
        # 2) the amount of lexical items that reference the JMDict entry
        # 3) the frequency of the JMDict entry
        if len(word_ids)>1:
            ref_sizes = []
            for word_id in word_ids:
                seq,senses,word = expand_word_id(word_id)
                word = word_id.split(':')[1]
                word_id_ref_count = scan_results['item_word_id_ref_count'][(word_id,pos_ref_index)]
                ref_sizes.append( (word_id,len(word), word_id_ref_count,
                    get_frequency_by_seq_and_word(seq,word)) )
            ref_sizes.sort(key=lambda x:x[3], reverse=False)
            ref_sizes.sort(key=lambda x:x[2], reverse=True)
            ref_sizes.sort(key=lambda x:x[1], reverse=True)
            
            word_ids = [x[0] for x in ref_sizes]

        refs = []
        for word_id in word_ids:
            # reference the word_id as index number in word_id_list
            w_idx = scan_results['word_id_list'].index(word_id)
            refs.append(w_idx)
        scan_results['item_word_id_refs'].append(refs)

    del(scan_results['item_word_id_ref_count']) # not needed anymore


def reassemble_block(original_lines, unidic_items, item_sense_ref):
    # re-assemble this block back into lines (list of lists)
    i = 0
    block_word_ref = []
    next_new_line_str = ''
    next_new_line = []
    for line in original_lines:
        if len(next_new_line_str) <= len(line):
            new_line = next_new_line
        else:
            new_line = []
            w = next_new_line_str
        new_line_str = next_new_line_str
        next_new_line_str = ''
        next_new_line = []
        while line not in new_line_str:
            w = unidic_items[i].txt
            refs = item_sense_ref[i]
            new_line_str += w
            i += 1

            if len(new_line_str) <= len(line):
                new_line.append({w:refs})

        if len(new_line_str) > len(line):
            # some of the particles were fused temporarily for scanning purposes. 
            # Don't want to lengthen a line so let's break them up again
            next_new_line_str = new_line_str[len(line):]
            num_extra_characters = len(new_line_str) - len(line)
            w = w[:-num_extra_characters]
            next_new_line = [{next_new_line_str:refs}]
            new_line.append({w:refs})

        block_word_ref.append(new_line)
    
    return block_word_ref


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