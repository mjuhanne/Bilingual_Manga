import fugashi
import sys
from dataclasses import dataclass, field
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
    classes:list
    flags: int = 0
    divided_particles:list = field(default_factory=lambda: [])
    conjugation_root:str = ''
    details:list = None
    is_masu = False
    alt_forms: list = field(default_factory=lambda: [])
    lemma: str = ''
    conj_details:list = field(default_factory=lambda: [])
    word_id: str = ''

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
                if '-' in lemma:
                    lemma = lemma.split('-')[0]
                orth_base = d[10]
                results.append(([w,wtype,basic_type,pro],lemma,orth_base,d))
            elif len(d)>0:
                wtype = d[0]
                results.append(([w,wtype,'',''],'','',d))

    return results


mid_sentence_punctuation_marks = ['・']

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
        #elif w in mid_sentence_punctuation_marks:
        #    # for some reason wide numbers and alphabets are parsed as nouns so
        #    # switch their class into this pseudoclass
        #    cl = mid_sentence_punctuation_mark_class
        else:
            if class_name not in ignored_classes:
                word = orth_base
                if word == '':
                    # empty base form for some reason. Use the parsed form
                    word = w
            
        if previous_cl != cl and previous_cl <= lumped_class:
            # word class changed so save previously collected word
            if collected_particles != '':
                items.append(LexicalItem(collected_particles,'',[previous_cl]))
                collected_particles = ''

        if cl <= lumped_class:
            # when many non-JP characters and punctuation marks are 
            # in sequence we don't want to save them separately
            # but instead lump them together
            collected_particles += w
        else:
            item = LexicalItem(w,word,[cl],details=details,lemma=lemma)
            if '連用形' in details[5]:
                # this should be in -masu form
                # for some reason 使っ / だっ verbs have 連用形 flag even though it's not.
                if w[-1] != 'っ':
                    item.is_masu = True
            if is_katakana_word(w):
                item.alt_forms = [katagana_to_hiragana(w)]
            items.append(item)

        previous_cl = cl

    if collected_particles != '':
        items.append(LexicalItem(collected_particles,'',[cl]))

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
    if aux_verb_class in items[pos+1].classes:
        # disable the ortho form for the erroneously detected aux verb
        # (most likely な in みたいな or に in 早めに)
        disable_ortho_list = ['な','に','なら']
        if items[pos+1].txt in disable_ortho_list:
            items[pos+1].flags |= DISABLE_ORTHO
    return

def attempt_conjugation(i, items, stem, conj, conj_details):
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
            if test == test2:
                # Unidic already parsed this in maximal way (usually -masu form)
                # i.e.  成り
                return 0, conj_details[t]
            for k, (w) in enumerate(words[i+1:]):
                test += w
                if test2 == test:
                    return k+1, conj_details[t]
    return 0, None

def check_adjectives(pos,items):
    if pos == len(items) - 1:
        return
    ortho = items[pos].ortho
    if ortho[-1] == 'い':
        ending, conj, conj_details = adj_conjugations[jmdict_adj_i_class]
        stem = ortho[:-1]
    else:
        ending, conj, conj_details = adj_conjugations[jmdict_adjectival_noun_class] # the な　adjectives
        stem = ortho
    detected_conj_particles, detected_conj_details = attempt_conjugation(pos, items, stem, conj, conj_details)
    if detected_conj_particles > 0:
        for i in range(detected_conj_particles):
            items[pos+i+1].flags = MERGE_PARTICLE
        items[pos].conj_details = detected_conj_details
    return

def attempt_maximal_conjugation(pos, items, seqs):
    ortho = items[pos].ortho
    lemma = items[pos].lemma
    max_particles_found = 0
    max_conj_details = None
    for seq in seqs:
        cl_list = get_flat_class_list_by_seq(seq)
        for cl in cl_list:
            try:
                cl_txt = jmdict_class_list[cl]
                if cl in verb_conjugations:
                    ending, conj, conj_details = verb_conjugations[cl]

                    candidates = []
                    if ortho != '':
                        candidates.append(ortho)
                    if lemma != '':
                        candidates.append(lemma)
                    candidates += items[pos].alt_forms
                    for candidate in candidates:
                        stem = candidate[:-len(ending)]
                        removed_ending = candidate[-len(ending):]
                        detected_num = 0
                        if ending == removed_ending:
                            detected_num, detected_conj_details = attempt_conjugation(pos, items, stem, conj, conj_details)
                            if detected_conj_details is not None:
                                if detected_num > max_particles_found:
                                    max_particles_found = detected_num
                                    max_conj_details = detected_conj_details
                                elif max_conj_details is None:
                                    # no additional particles detected but 
                                    # the Unidic managed to parse it already
                                    # in the correct inflection
                                    max_conj_details = detected_conj_details

                    """
                    stem = ortho[:-len(ending)]
                    removed_ending = ortho[-len(ending):]
                    detected_num = 0
                    if ending == removed_ending:
                        detected_num, detected_conj_details = attempt_conjugation(pos, items, stem, conj, conj_details)
                        if detected_num > max_particles_found:
                            max_particles_found = detected_num
                            max_conj_details = detected_conj_details

                    if ending != removed_ending or detected_num == 0:
                        stem = lemma[:-len(ending)]
                        removed_ending = lemma[-len(ending):]
                        if ending == removed_ending:
                            detected_num, detected_conj_details = attempt_conjugation(pos, items, stem, conj, conj_details)
                            if detected_num > max_particles_found:
                                max_particles_found = detected_num
                                max_conj_details = detected_conj_details
                    """
            except:
                pass
    return max_particles_found, max_conj_details

def check_verbs(pos,items): 
    ortho = items[pos].ortho
    lemma = items[pos].lemma
    # preliminary JMDict check 
    seqs = search_sequences_by_word(ortho)
    if len(seqs) == 0:
        # maybe ortho was in conditional form (作れる) ? Try the lemma (作る)
        alt_form = lemma
        if lemma[0] != ortho[0]:
            # However sometimes the lemma has different kanji (帰れる -> 返る)
            # so we want to enforce the same kanji
            if is_cjk(ortho[0]):
                alt_form = ortho[0] + lemma[1:]
            else:
                # ortho is hiragana so we have to fetch the reading of lemma
                s_lemma = search_sequences_by_word(lemma)
                if len(s_lemma) > 0:
                    readings = get_readings_by_seq(s_lemma[0])
                    alt_form = readings[0]
                else:
                    LOG(1,"Couldn't find seq for lemma %s when doing verb conjugations found for %s/%s" % (lemma,items[pos].txt, items[pos].ortho),items)
        seqs = search_sequences_by_word(alt_form)
        if len(seqs)>0:
            # only lemma matched. We have to add it to permutation list
            #items[pos].flags |= SCAN_WITH_LEMMA
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)

    if pos + 1 == len(items):
        # nothing further to check
        return
    max_particles_conjugated, conj_details = attempt_maximal_conjugation(pos, items, seqs)
    if conj_details is not None:
        for i in range(max_particles_conjugated):
            items[pos+i+1].flags = MERGE_PARTICLE
            items[pos].flags |= REPROCESS
        items[pos].conj_details = conj_details
        # clear the -masu flag that was in the stem
        if max_particles_conjugated > 0:
            items[pos].is_masu = False


    # after conjugating (attempt), still try to find some colloquial forms
    pos += max_particles_conjugated
    if pos == len(items) -1:
        return
    processed_str = ''.join([items[j].txt for j in range(pos+1)])
    if aux_verb_class in items[pos+1].classes or gp_class in items[pos+1].classes:
        oku_verbs = ['取る']
        # fuse the different (non)colloquial いる forms into main word
        iru_forms = ['いる','いた','た','てる']
        nai_forms = ['ねー','へん']
        if items[pos+1].txt in iru_forms: 
            items[pos+1].flags = MERGE_PARTICLE
            items[pos].is_masu = False
        elif items[pos+1].txt in nai_forms:
            allowed = False
            if items[pos].is_masu:
                allowed = True
            elif processed_str[-1] == 'て' or processed_str[-1] == 'で':
                if len(processed_str) > 1:
                    if processed_str[-2] != 'く' and processed_str[-2] != 'て' and processed_str[-2] != 'で': 
                        # it's not negative form if it's -くて / ーてて form
                        # like 忙しくてねー  / 先生にはあこがれててねー
                        allowed = True
                else:
                    allowed = True
            if allowed:
                items[pos+1].flags = MERGE_PARTICLE
                items[pos].alt_forms.append(items[pos].txt + 'ない')
        elif items[pos+1].txt == "て": 
            if items[pos].txt[-1] == 'て':
                # accept the colloquial form, e.g. 生きて + て　+ ほしい
                items[pos+1].flags = MERGE_PARTICLE
        elif items[pos+1].txt == "てく": 
            # divide the colloquial form to separate particles
            items[pos+1].flags = DIVIDE_PARTICLE
            if items[pos].lemma in oku_verbs:
                # e.g. とっ + てく -> とっ + て + おく
                ku_verb = 'おく'
            else:
                # e.g. 寄っ + てく -> 寄っ + て + いく
                ku_verb = 'いく'
            items[pos+1].divided_particles = [
                LexicalItem('て','て',[aux_verb_class]),
                LexicalItem('く',ku_verb,[verb_class],conjugation_root=ku_verb),
            ]
            items[pos].flags |= REPROCESS
        elif items[pos+1].txt == "てか":
            # divide the colloquial form to separate particles
            if items[pos].lemma in oku_verbs:
                # e.g. とっ + てか + ない -> とっ + て + おか　+ ない
                ku_verb = 'おく'
                neg_ku_verb = 'おか'
            else:
                # e.g. 寄っ + てか + ない -> 寄っ + て + いか　+ ない
                # e.g. 寄っ + てく -> 寄っ + て + いく
                ku_verb = 'いく'
                neg_ku_verb = 'いか'
            # e.g. 寄っ + てか + ない -> 寄っ + て + いか　+ ない
            items[pos+1].flags = DIVIDE_PARTICLE
            items[pos+1].divided_particles = [
                LexicalItem('て','て',[aux_verb_class]),
                LexicalItem('か',ku_verb,[verb_class],REPROCESS,alt_forms=[neg_ku_verb], conjugation_root=neg_ku_verb),
            ]
            items[pos].flags |= REPROCESS
        elif items[pos+1].txt == "てこ": 
            # divide the colloquial form to separate particles
            items[pos+1].flags = DIVIDE_PARTICLE
            # e.g. はいっ + てこ -> はいっ + て + いこう
            ku_verb = 'いく'
            items[pos+1].divided_particles = [
                LexicalItem('て','て',[aux_verb_class]),
                LexicalItem('こ',ku_verb,[verb_class],alt_forms=[ku_verb],conjugation_root=ku_verb),
            ]
            items[pos].flags |= REPROCESS
        else:
            if max_particles_conjugated == 0:
                LOG(1,"No exceptional verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
                items[pos].flags |= ERROR_VERB_CONJUGATION
    else:
        if max_particles_conjugated == 0:
            LOG(1,"No verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
            items[pos].flags |= ERROR_VERB_CONJUGATION


def check_nouns(pos,items):
    if pos + 1 == len(items):
        # nothing further to check
        return
    if aux_verb_class in items[pos+1].classes:
        if items[pos+1].txt == 'に' and items[pos+1].ortho == 'だ':
            # Erroneously detected aux verb. Disable the ortho form to prevent false results
            # For example in the phrase 別にいいでしょ the scanner would try 'だいい' 
            items[pos+1].flags |= DISABLE_ORTHO
        if items[pos+1].txt == 'な' and items[pos+1].ortho == 'だ':
            # the reason is same as above
            items[pos+1].flags |= DISABLE_ORTHO
    if punctuation_mark_class in items[pos+1].classes:
        if items[pos+1].txt[0] == 'ー':
            if items[pos].txt[-1] in katakana:
                # unidict dissected this word erroneously
                # 格ゲ + ー  -> 格ゲー
                items[pos+1].flags |= MERGE_PARTICLE
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
    for ew in explicit_word_changes:
        p_list = ew[0]
        p_classes = ew[1]
        condition = ew[2]
        task = ew[3]
        params = ew[4]
        lp = len(p_list)
        if pos + lp <= lw:
            i = 0
            while (i<lp) and (items[pos+i].txt==p_list[i]) and (p_classes[i] in items[pos+i].classes):
                i += 1
            if i == lp:
                # All items match. Check extra conditions yet.
                allowed = True
                if condition & COND_BLOCK_START and pos>0:
                    allowed = False
                if condition & COND_NOT_BEFORE_VERB and pos+lp<lw:
                    if verb_class in items[pos+lp].classes:
                        allowed = False
                if condition & COND_NOT_AFTER_NOUN and pos>0:
                    if noun_class in items[pos-1].classes:
                        allowed = False
                if condition & COND_NOT_AFTER_ADJ and pos>0:
                    if adjective_class in items[pos-1].classes:
                        allowed = False

                if allowed:
                    if task == TASK_MERGE:
                        if 'parts' in params.keys():
                            # merge several items into two or more items
                            i = 0
                            for part,cl,ortho in zip(params['parts'],params['classes'],params['orthos']):
                                items[pos+i].txt = part
                                items[pos+i].ortho = ortho
                                items[pos+i].alt_forms = []
                                items[pos+i].classes = [cl]
                                i += 1
                            while i<lp:
                                items[pos+i].flags = REMOVE_PARTICLE
                                i += 1
                        else:
                            # simple merge
                            target_class = params['class']
                            # Change the class of the first particle and mark the next ones to be merged
                            items[pos].classes = [target_class]
                            for i in range(1,lp):
                                items[pos+i].flags = MERGE_PARTICLE
                        changed = True
                    if task == TASK_DIVIDE:
                        items[pos].divided_particles = [
                            LexicalItem(part,part,items[pos].classes)
                                for part in params['parts']
                        ]                        
                        items[pos].flags |= REPROCESS | DIVIDE_PARTICLE
                        changed = True
                    else:
                        if 'class' in params.keys():
                            # Only add new class to the class list but do not merge
                            target_class = params['class']
                            for i in range(0,lp):
                                if target_class not in items[pos+i].classes:
                                    items[pos+i].classes.append(target_class)
                                    changed = True

                    if 'ortho' in params.keys():
                        ortho = params['ortho']
                        for i in range(0,lp):
                            items[pos+i].ortho = ortho
                    if 'alt' in params.keys():
                        alt_form = params['alt']
                        #for i in range(0,lp):
                        #    items[pos+i].alt_txt = alt_txt
                        if alt_form not in items[pos].alt_forms:
                            items[pos].alt_forms.append(alt_form)
                    if 'root_ortho' in params.keys():
                        items[pos].ortho = params['root_ortho']
                        for i in range(1,lp):
                            items[pos+i].ortho = ''
                    if 'add_flags' in params.keys():
                        item_flags = params['add_flags']
                        for i in range(lp):
                            items[pos+i].flags |= item_flags[i]
                    if 'word_id' in params.keys():
                        # force the word id for these items
                        for i in range(lp):
                            items[pos+i].word_id = params['word_id']
                            items[pos+i].flags |= NO_SCANNING

    if items[pos].txt in alternative_forms.keys():
        alt_forms = alternative_forms[items[pos].txt]
        for alt_form in alt_forms:
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)
                changed = True

    alt_cll = []
    if items[pos].txt in alternative_classes:
        alt_cll = alternative_classes[items[pos].txt]
    if items[pos].ortho in alternative_classes:
        alt_cll = alternative_classes[items[pos].ortho]
    for cl in alt_cll:
        if cl not in items[pos].classes:
            items[pos].classes.append(cl)
            changed = True

    """
    if 'ー' in items[pos].txt:
        # create an alternative form by removing ー 
        alt_form = items[pos].txt.replace('ー','')
        if alt_form != '':
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)
                changed = True
    """

    """
    if len(items[pos].txt)>1 and items[pos].txt[-1] == 'っ':
        # Possibly dialect. Check alternative form without the emphasis
        # おっしえなーい  -> おしえなーい
        alt_form = items[pos].txt[:-1]
        if alt_form not in items[pos].alt_forms:
            items[pos].alt_forms.append(alt_form)
            changed = True
    """

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
        items[pos].flags |= REPROCESS # this allows cascading changes
    return changed

"""
TODO: must check -chan only after incorporating JMnedict

def check_suffix(pos,items):
    if pos == 0:
        LOG(1,"No suffix %s/%s found in the beginning of sentence!" % (items[pos].txt, items[pos].ortho),items)
        return
    name_chan = False
    chanto = False
    if items[pos].txt == 'ちゃん':
        # is it name-ちゃん or ちゃん + と or name-ちゃん + と + (違って etc) ?

        if pos == len(items)-1:
            # last item
            name_chan = True
        else:
            if items[pos+1].txt == 'と':
                chanto = True
            else:
                name_chan = True


        if name_chan:
            # make sure that the previous item is handled as noun
            if verb_class in items[pos-1].classes:
                items[pos-1].ortho = ''
            items[pos-1].classes = [noun_class]
        elif chanto:
            items[pos+1].flags |= MERGE_PARTICLE
            items[pos].ortho = ''
"""

def particle_post_processing(pos, items):
    if not handle_explicit_form_and_class_changes(pos,items):
        cll = items[pos].classes

        if len(cll) == 1 and cll[0] <= punctuation_mark_class:
            items[pos].flags |= NO_SCANNING
            #items[pos].flags |= START_OF_SCAN_DISABLED
            return True

        if verb_class in cll:
            return check_verbs(pos,items)
        if adjective_class in cll or (aux_verb_class in cll and items[pos].ortho == 'ない'):
            # ない　acts as i-adjective
            return check_adjectives(pos,items)
        if adjectival_noun_class in cll:
            return check_adjectival_nouns(pos,items)
        if noun_class in cll:
            return check_nouns(pos,items)
        #if suffix_class in cll:
        #    return check_suffix(pos,items)
        if aux_verb_class in cll:
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
                if pos > 0 and adjectival_noun_class in items[pos-1].classes:
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
            processed_items[pos-1].flags |= REPROCESS
        elif items[i].flags & DIVIDE_PARTICLE:
            for new_item in items[i].divided_particles:
                processed_items.append(new_item)
                pos += 1
        elif items[i].flags & REMOVE_PARTICLE:
            pass
        else:
            processed_items.append(items[i])
            pos += 1
    return processed_items


def post_process_unidic_particles(items):
    cont = True
    for i in range(len(items)):
        items[i].flags |= REPROCESS
    while cont:
        for i in range(len(items)):
            if items[i].flags & REPROCESS:
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
                    if verb_class in unidic_classes and items[pos].is_masu:
                        if noun_class in next_word_classes:
                            # allow masu-stem verb + noun as noun
                            # e.g. 食べ + 放題
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
def create_phrase_permutations(original_words, ortho_forms_list, items, start=0):
    i = start
    permutations = []
    while i<len(original_words): # and (not (items[i].flags & NO_SCANNING) ):
        for ortho_form in ortho_forms_list[i]:
            permutations.append(original_words[start:i] + [ortho_form])
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
    original_forms = [item.txt for item in unidic_items]
    for i, w in enumerate(unidic_items):
        alt_forms[i] += unidic_items[i].alt_forms
        if not (unidic_items[i].flags & (NO_SCANNING | DISABLE_ORTHO)):
            if (unidic_items[i].txt != unidic_items[i].ortho):
                alt_forms[i].append(unidic_items[i].ortho)
        if unidic_items[i].flags & SCAN_WITH_LEMMA:
            alt_forms[i].append(unidic_items[i].lemma)

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
        permutations, next_pos = create_phrase_permutations(original_forms, alt_forms, unidic_items, pos)
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


def get_conjugations_recursively(root_entries, conj_name, rec_level):
    tenses = []
    tense_details = dict()
    remove_suffix = None
    for e in root_entries:
        if e['Name'] == conj_name:
            for t in e['Tenses']:
                sfx = t['Suffix']
                details = t['Tense']
                if t['Negative']:
                    details += ' negative'
                if t['Formal']:
                    details += ' formal'
                if remove_suffix == None:
                    remove_suffix = sfx
                if sfx != '':
                    tenses.append(sfx)
                    tense_details[sfx] = [(conj_name,sfx,details)]
                if 'Next Type' in t:
                    nt = t['Next Type']
                    if rec_level < 1 or 'stem' in nt or 'adj-i' in nt:
                        sub_conjugations, sub_tense_params, sub_remove_suffix = get_conjugations_recursively(root_entries, nt, rec_level + 1)
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
                            tense_details[base + st] =  [(conj_name,base,details)] + sub_tense_params[st]

    return tenses, tense_details, remove_suffix

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
            conj_list, conj_details, ending = get_conjugations_recursively(entries, n, 0)
            conj_list = list(set(conj_list))  # get rid of possible duplicates

            # sort by conjugation length so we can be greedy by default
            # i.e. get the longest possible conjugation found in the phrase
            conj_dict = {x:len(x) for x in conj_list}
            sorted_conj = dict(sorted(conj_dict.items(), key=lambda x:x[1], reverse=True))

            if 'adj' in n:
                adj_conjugations[cli] = (ending, list(sorted_conj), conj_details)
            else:
                verb_conjugations[cli] = (ending, list(sorted_conj), conj_details)


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
