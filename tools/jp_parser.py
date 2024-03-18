import fugashi
import sys
from dataclasses import dataclass
from helper import *
from jmdict import *
from jp_parser_helper import *

parser = fugashi.Tagger('')

_parser_initialized = False

verb_conjugations = dict()
adj_conjugations = dict()

jmdict_noun_pos_list = []
jmdict_verb_pos_list = []

@dataclass
class LexicalItem:
    txt: str
    ortho: str
    cl: int
    flags: int = 0
    divided_particles = []
    conjugation_root:str = ''
    details:list = None
    is_masu = False
    alt_txt: str = ''
    lemma: str = ''

########### LOGGING FACILITIES ######################

verbose_level = 0
log_file = None

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

######### END OF LOGGING FACILITIES #################

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
                results.append(([w,wtype,basic_type,pro],lemma,orth_base,d))
            elif len(d)>0:
                wtype = d[0]
                results.append(([w,wtype,'',''],'','',d))

    return results


def parse_line_with_unidic(line, kanji_count):

    res = parse_with_fugashi(line)
    if len(res)==0 and len(line)>0:
        raise Exception("Couldn't parse '%s'" % line)
    
    k_c = 0
    items = []
    collected_particles = ''
    previous_cl = -1
    for (wr,lemma,orth_base,details) in res:
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
            item = LexicalItem(w,word,cl,details=details,lemma=lemma)
            if '連用形' in details[5]:
                item.is_masu = True
            if is_katakana_word(w):
                item.alt_txt = katagana_to_hiragana(w)
            items.append(item)

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
        disable_ortho_list = ['な','に','なら']
        if items[pos+1].txt in disable_ortho_list:
            items[pos+1].flags |= DISABLE_ORTHO
    return

def attempt_conjugation(i, items, stem, conj):
    words = []
    for item in items:
        if item.conjugation_root != '':
            words.append(item.conjugation_root)
        else:
            words.append(item.txt)
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

def attempt_maximal_conjugation(pos, items):
    ortho = items[pos].ortho
    lemma = items[pos].lemma
    max_particles_found = 0
    seqs = search_sequences_by_word(ortho)
    for seq in seqs:
        cl_list = get_flat_class_list_by_seq(seq)
        for cl in cl_list:
            try:
                cl_txt = jmdict_class_list[cl]
                if cl in verb_conjugations:
                    ending, conj = verb_conjugations[cl]
                    stem = ortho[:-len(ending)]
                    removed_ending = ortho[-len(ending):]
                    if ending == removed_ending:
                        detected_num = attempt_conjugation(pos, items, stem, conj)
                        if detected_num > max_particles_found:
                            max_particles_found = detected_num
                    else:
                        stem = lemma[:-len(ending)]
                        removed_ending = lemma[-len(ending):]
                        if ending == removed_ending:
                            detected_num = attempt_conjugation(pos, items, stem, conj)
                            if detected_num > max_particles_found:
                                max_particles_found = detected_num

            except:
                pass
    return max_particles_found

def check_verbs(pos,items): 
    if pos + 1 == len(items):
        # nothing further to check
        return
    max_particles_conjugated = attempt_maximal_conjugation(pos, items)
    if max_particles_conjugated > 0:
        for i in range(max_particles_conjugated):
            items[pos+i+1].flags = MERGE_PARTICLE
        return
    else:
        if items[pos+1].cl == aux_verb_class:
            if items[pos+1].txt == "てる": 
                # accept the colloquial form, e.g. 持っ + てる
                items[pos+1].flags = MERGE_PARTICLE
            elif items[pos+1].txt == "てく": 
                # divide the colloquial form to separate particles
                # e.g. 寄っ + てく -> 寄っ + て + いく
                items[pos+1].flags = DIVIDE_PARTICLE
                items[pos+1].divided_particles = [
                    LexicalItem('て','て',aux_verb_class),
                    LexicalItem('く','いく',verb_class),
                ]
            elif items[pos+1].txt == "てか":
                # divide the colloquial form to separate particles
                # e.g. 寄っ + てか + ない -> 寄っ + て + いか　+ ない
                items[pos+1].flags = DIVIDE_PARTICLE
                items[pos+1].divided_particles = [
                    LexicalItem('て','て',aux_verb_class),
                    LexicalItem('か','いく',verb_class,REPROCESS,'いか'),
                ]
            else:
                LOG(1,"No exceptional verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
                items[pos].flags |= ERROR_VERB_CONJUGATION
        else:
            LOG(1,"No verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
            items[pos].flags |= ERROR_VERB_CONJUGATION


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
    if items[pos+1].cl == verb_class:
        if len(items[pos].txt)>1 and items[pos].txt[-1] == 'っ':
            # Possibly dialect. Check alternative form without the emphasis
            # おっしえなーい  -> おしえなーい
            items[pos].alt_txt == items[pos].txt[:-1]
    return


vowel_extension = {
    'ァ' : "ャヮヵ",
    'ア' : "カガサザタダナハバパマヤラワ",
    'ィ' : "ヶ",
    'イ' : "キギセゼチヂテデニシジケゲヒビピミメリレ",
    'ゥ' : "ュョ",
    'ウ' : "クグコゴソゾッツヅトドヌノスズフブプホボポムモユヨルロヲンヴ",
    'ェ' : "",
    'エ' : "ネヘベペ",
    'ォ' : "",
    'オ' : "",

    'あ' : "かがさざただなはばぱまやわ",
    'い' : "きぎせぜちてでにしじけげひびぴみめりれ",
    'う' : "くぐこごそぞつとどぬのすずふぷぶほぼぽむもゆよるろ",
    'え' : "ねへべぺ",
}

vowel_extension_by_kana = dict()
for ext,kana_list in vowel_extension.items():
    for k in kana_list:
        vowel_extension_by_kana[k] = ext

def get_vowel_extension(chr):
    if chr in vowel_extension_by_kana:
        return vowel_extension_by_kana[chr]
    return ''

def handle_explicit_form_and_class_changes(pos,items):
    changed = False

    lw = len(items)
    for ew in explicit_words:
        p_list = ew[0]
        p_classes = ew[1]
        condition = ew[2]
        target_class = ew[3]
        if len(ew)>4:
            extra_fields = ew[4]
        else:
            extra_fields = dict()
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
                    if 'ortho' in extra_fields.keys():
                        ortho = extra_fields['ortho']
                        for i in range(0,lp):
                            items[pos+i].ortho = ortho
                    if 'root_ortho' in extra_fields.keys():
                        items[pos].ortho = extra_fields['root_ortho']
                        for i in range(1,lp):
                            items[pos+i].ortho = ''
                    changed = True

    if items[pos].txt in alternative_forms.keys():
        if items[pos].alt_txt != alternative_forms[items[pos].txt]:
            items[pos].alt_txt = alternative_forms[items[pos].txt]
            changed = True
    """
    elif 'ー' in items[pos].txt:
        # create an alternative form by extending the vowel when ー is detected
        # Example: ありがとー　->　ありがとう
        i = items[pos].txt.index('ー')
        if i>0:
            rep = get_vowel_extension(items[pos].txt[i-1]))
            if rep != '':
                items[pos].alt_txt = items[pos].txt.replace('ー',rep)
                changed = True
    """

    if changed:
        items[pos].flags |= REPROCESS
    return changed

def particle_post_processing(pos, items):
    if not handle_explicit_form_and_class_changes(pos,items):
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
            if items[pos].txt == 'に':
                if pos > 0 and items[pos-1].cl == adjectival_noun_class:
                    # almost identical case as above, but here it's 
                    # adjectival noun + に 
                    # Example: ロマンチック + に 
                    items[pos].ortho = items[pos].txt
                    items[pos].flags |= BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED
    else:
        return True

# merge/divide those particles that are marked
def merge_or_divide_particles(items):
    pos = 0
    processed_items = []
    for i in range(len(items)):
        if items[i].flags & MERGE_PARTICLE:
            processed_items[pos-1].txt += items[i].txt
        elif items[i].flags & DIVIDE_PARTICLE:
            for new_item in items[i].divided_particles:
                processed_items.append(new_item)
                pos += 1
        else:
            processed_items.append(items[i])
            pos += 1
    return processed_items


def post_process_unidic_particles(items):
    cont = True
    while cont:
        for i in range(len(items)):
            items[i].flags &= (~REPROCESS) # clear the flag
            if items[i].flags != MERGE_PARTICLE and items[i].flags != DIVIDE_PARTICLE: 
                particle_post_processing(i,items)

        # merge those particles that are marked
        items = merge_or_divide_particles( items )

        cont = False
        if any(item.flags & REPROCESS for item in items):
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

The matching lexical items (from Fugashi/Unidic) were:
# お (prefix) + 母 (noun) + さん (suffix)
# This matching condition is one of those defined below
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

    scanned_word_jmd_cl_list_per_sense = get_class_list_by_seq(seq)
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
                    if noun_class in unidic_classes and suffix_class == next_word_class:
                        # Same case as above but the verb is detected as suffix
                        # 不審がる -> 不審 (noun) + がる (suffix)
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])

                if jmd_cl == jmdict_adjectival_noun_class:
                    if noun_class in unidic_classes and suffix_class == next_word_class:
                        # noun + suffix can act as adjectival noun:
                        # 感傷 + 的
                        valid_senses[i].update([s_idx])
                        valid_senses[i+1].update([s_idx])
                    if verb_class in unidic_classes and suffix_class == next_word_class:
                        if items[pos].is_masu:
                            # verb in masu-stem + suffix can act as adjectival noun
                            # あり + がち
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

            #if num_scanned_items >= 4:
            #    INCIDENCE_COUNTER("acceptance by scanned items length>=4",scanned_word,items)

            if len(scanned_word) >= HOMOPHONE_MATCHING_WORD_MINIMUM_LENGTH:
                # Sometimes Unidict just fails to parse pure Hiragana words..
                # For example ばんそうこう (bandage) becomes:
                #  ば (grammatical particle)
                #  ん (interjection)
                #  そうこう (adverb) ..
                # To allow matching these kinds of words we disregard the parsed classes
                # if the candidate word has a length of minimum of 5 characters 
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
            word_id = str(seq) + ":" + chunk
        else:
            word_id = str(seq) + '/' + str(sense) + ":" + chunk

        # add this word id (seq/sense:word) reference for all the encompassing lexical items
        for j in range(chunk_len):
            scan_results['item_word_ids'][pos+j].append(word_id)

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
def create_phrase_permutations(original_words, ortho_forms_list, start=0):
    i = start
    permutations = []
    while i<len(original_words): # and (not (items[i].flags & NO_SCANNING) ):
        for ortho_form in ortho_forms_list[i]:
            permutations.append(original_words[start:i] + [ortho_form])
        i += 1
    
    if i> 0:
        # finally add the whole original as one permutation
        permutations.append(original_words[start:i])
        #permutations = [original_words[start:i]] + permutations
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
    
    # By default we use lexical items in the form they word in the original text
    # Example: お願いします -> お + 願い + します

    # In order to do more exhaustive scanning we also construct 
    # a list of alternative (basic/ortho) forms if they differ from the originals.
    # Example: お願いします -> お + 願う + する
    wlen = len(unidic_items)
    alt_forms = [[] for x in range(wlen)]
    original_forms = [item.txt for item in unidic_items]
    for i, w in enumerate(unidic_items):
        if unidic_items[i].alt_txt != '':
            alt_forms[i].append(unidic_items[i].alt_txt)
        if (unidic_items[i].txt != unidic_items[i].ortho) \
                and not (unidic_items[i].flags & (NO_SCANNING | DISABLE_ORTHO)):
            alt_forms[i].append(unidic_items[i].ortho)

    searched_kanji_word_sets = [set() for x in range(wlen)]
    searched_reading_sets = [set() for x in range(wlen)]

    scan_results['item_word_ids'] = [[] for x in range(len(unidic_items))]
    
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
        permutations, next_pos = create_phrase_permutations(original_forms, alt_forms, pos)
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

    scan_results['item_word_id_refs'] = []
    for i,(word_ids) in enumerate(scan_results['item_word_ids']):
        cl = unidic_items[i].cl
        # keep count of word occurrence by class
        scan_results['word_count_per_unidict_class'][cl] += 1

        # Fuse untethered small particles if marked for that
        if unidic_items[i].flags &  BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED:
            if len(word_ids)==0 and i>0:
                # grab the references from previous item
                word_ids = scan_results['item_word_ids'][i-1]

        # log missing references
        if verbose_level >= 1:
            if len(word_ids) == 0:
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

        # Sort each particle/word reference by the size of the word/phrase 
        # it's referencing. The second sort criteria is the frequency of the entry
        if len(word_ids)>1:
            ref_sizes = []
            for word_id in word_ids:
                seq,senses,word = expand_word_id(word_id)
                word = word_id.split(':')[1]
                ref_sizes.append( (word_id,len(word), 
                    get_frequency_by_seq_and_word(seq,word)) )
            ref_sizes.sort(key=lambda x:x[2], reverse=False)
            ref_sizes.sort(key=lambda x:x[1], reverse=True)
            
            word_ids = [x[0] for x in ref_sizes]

        refs = []
        for word_id in word_ids:
            # add this seq/sense reference sense list for all the encompassing lexical items
            w_idx = scan_results['word_id_list'].index(word_id)
            refs.append(w_idx)
        scan_results['item_word_id_refs'].append(refs)


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
