from helper import *
from jp_parser_helper import *
from jp_parser_print import pretty_print_lexical_item
from conjugation import *
from jmdict import search_sequences_by_word

import fugashi
parser = fugashi.Tagger('')

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
                pron_base = d[11]
                results.append(([w,wtype,basic_type,pro],lemma,orth_base,pron_base,d))
            elif len(d)>0:
                wtype = d[0]
                results.append(([w,wtype,'',''],'','','',d))

    return results

def parse_line_with_unidic(line, kanji_count):

    res = parse_with_fugashi(line)
    if len(res)==0 and len(line)>0:
        raise Exception("Couldn't parse '%s'" % line)
    
    k_c = 0
    items = []
    collected_particles = ''
    previous_cl = -1
    for (wr,lemma,orth_base,pron_base,details) in res:
        w = wr[0]
        class_name = wr[1]

        try:
            cl = unidic_class_list.index(class_name)
        except:
            raise Exception("Unknown class %d in word %s" % (class_name, w))
        
        word = ''
        if is_all_numeric(w):
            # for some reason wide numbers and alphabets are parsed as nouns so
            # switch their class into this pseudoclass
            cl = numeric_pseudoclass
        elif is_all_alpha(w):
            # for some reason wide numbers and alphabets are parsed as nouns so
            # switch their class into this pseudoclass
            cl = alphabet_pseudoclass
        elif w in mid_sentence_punctuation_marks:
            cl = mid_sentence_punctuation_mark_class
        elif w in elongation_marks:
            cl = elongation_mark_class
        else:
            if class_name not in ignored_classes:
                word = orth_base
                if word == '':
                    # empty base form for some reason. Use the parsed form
                    word = w
            
        if previous_cl != cl and previous_cl <= lumped_class:
            # word class changed so save previously collected word
            if collected_particles != '':
                items.append(LexicalItem(collected_particles,'',[previous_cl], base_score=get_class_base_score(cl)))
                collected_particles = ''

        if cl <= lumped_class:
            # when many non-JP characters and punctuation marks are 
            # in sequence we don't want to save them separately
            # but instead lump them together
            collected_particles += w
        else:
            item = LexicalItem(w,word,[cl],details=details,lemma=lemma, base_score=get_class_base_score(cl))
            if '連用形' in details[5]:
                # this should be in -masu form
                # for some reason 使っ / だっ verbs have 連用形 flag even though it's not.
                if w[-1] != 'っ':
                    item.is_masu = True

            if cl == suffix_class and details[1] == '動詞的':
                # If the suffix works as a verb 
                # (as めいた in 要求めいた or -がってる in 怖がってる),
                # add the verb class in order to enable the conjugation 
                item.classes.append(verb_class)

            if has_word_katakana(w):
                item.alt_forms = [katakana_to_hiragana(w)]
                item.appendable_alt_forms = [katakana_to_hiragana(w)]
            if pron_base != '':
                item.pron_base = katakana_to_hiragana(pron_base)
            if is_katakana_word(w):
                item.is_katakana = True
            elif is_hiragana_word(w):
                item.is_hiragana = True

            #if lemma != '' and lemma != word:
            #    item.alt_forms.append(lemma)
            #    item.alt_scores[lemma] = 0.5
            items.append(item)

        previous_cl = cl

    if collected_particles != '':
        items.append(LexicalItem(collected_particles,'',[cl], base_score=get_class_base_score(cl)))

    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1

    return k_c, items 


def add_alternative_form_from_lemma(item):
    lemma = item.lemma
    # First try to get the JMDict entry to see if there is a match
    seqs = search_sequences_by_word(item.txt)
    if len(seqs) == 0 and lemma != '':
        # maybe the original form had a unusual form (e.g. カン違い)
        #seqs = search_sequences_by_word(lemma)

        # just add the lemma as an alternative
        if lemma not in item.alt_forms and lemma != item.txt:
            LOG(2, "%s: Added alt form from lemma %s" % (item.txt,lemma))
            item.alt_forms.append(lemma)
            item.appendable_alt_forms.append(lemma)
            item.alt_scores[lemma] = 0.4

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

def divide_item(pos,items):
    new_items = []

    i = 0
    for ch in items[pos].txt:
        cll = items[pos].classes
        if i<len(items[pos].ortho):
            ortho = items[pos].ortho[i]
        else:
            ortho = ''
        it = LexicalItem(ch,ortho,cll)
        it.base_score = get_class_base_score(cll[0])
        new_items.append(it)
        i += 1
    
    # just replace the first item with all the items
    # and remove the rest of the replaced items
    items[pos].replaced_items = new_items
    items[pos].flags |= REPROCESS | REPLACE_ITEM
    i = 1

jmdict_kanji_elements, jmdict_kanji_element_seq, jmdict_max_kanji_element_len = get_jmdict_kanji_element_set()

def get_highest_freq_seq_for_word(word):
    best_seq = None
    best_freq = 10000
    if word in jmdict_kanji_elements[len(word)]:
        seqs = jmdict_kanji_element_seq[len(word)][word]
        for seq in seqs:
            freq = get_frequency_by_seq_and_word(seq,word)
            if freq < best_freq:
                best_freq = freq
                best_seq = seq
    return best_seq, best_freq


spatio_temporal_kanjis = list('左右')
def is_spatiotemporal(word):
    return all(c in spatio_temporal_kanjis for c in word)


def check_nouns(pos,items):

    txt = items[pos].txt

    if is_numerical(txt):
        divide_item(pos,items)
    if is_spatiotemporal(txt[0]):
        divide_item(pos,items)
    elif len(txt) == 2 and is_cjk(txt[0]) and is_cjk(txt[1]):
        primary_seq, primary_freq = get_highest_freq_seq_for_word(txt)
        if primary_seq is not None:
            # divide nouns into smaller parts if Unidic separates the word inefficiently
            # and other combination seems more likely. Greedy parser can then 
            # find the words more easily
            # e.g. 部下 + 達 instead of 部 + 下達
            allowed = False
            if pos > 0 and noun_class in items[pos-1].classes:
                variant = items[pos-1].txt[-1] + txt[0]
                allowed=True
            if pos < len(items) -1 and (noun_class in items[pos+1].classes or suffix_class in items[pos+1].classes):
                variant = txt[1] + items[pos+1].txt[0] 
                allowed=True
            if allowed:
                variant_seq, variant_freq = get_highest_freq_seq_for_word(variant)
                if variant_freq < primary_freq:
                    divide_item(pos,items)
        else:
            # no word was found for this kanji-only noun. Divide it to allow
            # matching later with individual kanjis
            #divide_item(pos,items)
            pass

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
    if elongation_mark_class in items[pos+1].classes:
        if items[pos+1].txt[0] == 'ー':
            if items[pos].txt[-1] in katakana:
                # unidict dissected this word erroneously
                # 格ゲ + ー  -> 格ゲー
                items[pos+1].flags |= MERGE_ITEM
    return

small_vowels = "ァィゥェォぁぃぅぇぉ"

small_vowel_fade = {
    'ァ' : "アカサタナハマヤラワガザダバパあかさたなはまやらわがざだばぱ",
    'ィ' : "イキシチニヒミリギジヂビピいきしちにひみりぎじぢびぴ",
    'ゥ' : "ウクスツヌフムユルヴグズヅブプうくすつぬふむゆるぐずづぶぷ",
    'ェ' : "エケセテネヘメレゲゼデベペえけせてねへめれげぜでべぺ",
    'ォ' : "オコソトノホモヨロヲゴゾドボポおこそとのほもよろごぞどぼぽ",
    'ぁ' : "アカサタナハマヤラワガザダバパあかさたなはまやらわがざだばぱ",
    'ぃ' : "イキシチニヒミリギジヂビピいきしちにひみりぎじぢびぴ",
    'ぅ' : "ウクスツヌフムユルヴグズヅブプうくすつぬふむゆるぐずづぶぷ",
    'ぇ' : "エケセテネヘメレゲゼデベペえけせてねへめれげぜでべぺ",
    'ぉ' : "オコソトノホモヨロヲゴゾドボポおこそとのほもよろごぞどぼぽ",
}
short_vowel_fade_by_kana = dict()
for ext,kana_list in small_vowel_fade.items():
    for k in kana_list:
        short_vowel_fade_by_kana[k] = ext

vowel_extension = {
    'ァ' : "ャヮヵ",
    'ア' : "カガサザタダナハバパマヤラワ",
    'ィ' : "ヶ",
    'イ' : "イキギセゼチヂテデニシジケゲヒビピミメリレ",
    'ゥ' : "ュョ",
    'ウ' : "ウクグコゴソゾッツヅトドヌノスズフブプホボポムモユヨルロヲンヴ",
    'ェ' : "",
    'エ' : "エネヘベペ",
    'ォ' : "",
    'オ' : "オ",

    'あ' : "あかがさざただなはばぱまやわ",
    'い' : "いきぎせぜちてでにしじけげひびぴみめりれ",
    'う' : "うくぐこごそぞつとどぬのすずふぷぶほぼぽむもゆよょるろ",
    'え' : "えねへべぺ",
}

vowel_extension_by_kana = dict()
for ext,kana_list in vowel_extension.items():
    for k in kana_list:
        vowel_extension_by_kana[k] = ext

def get_vowel_extension(chr):
    if chr in vowel_extension_by_kana:
        return vowel_extension_by_kana[chr]
    return ''

def check_matching_condition(items,pos,conditions,word,original_word,num_scanned_items,params=None):
    matched_conditions = COND_NONE
    flexible = conditions & COND_FLEXIBLE

    # TODO: add flexible matching with rest of the conditions
    if conditions & COND_NON_BASE_FORM:
        for i in range(num_scanned_items):
            if not items[pos+i].is_base_form:
                matched_conditions |= COND_NON_BASE_FORM
    if conditions & COND_NON_ORIGINAL_FORM:
        if word != original_word:
            matched_conditions |= COND_NON_ORIGINAL_FORM
    if conditions & COND_BEFORE_CLASS:
        if pos+num_scanned_items < len(items):
            if params['cond_class'] in items[pos+num_scanned_items].classes:
                matched_conditions |= COND_BEFORE_CLASS
    if conditions & COND_END_OF_CLAUSE:
        if items[pos+num_scanned_items-1].end_of_clause:
            matched_conditions |= COND_END_OF_CLAUSE
    if conditions & COND_BLOCK_START and pos == 0:
        matched_conditions |= COND_BLOCK_START
    if conditions & COND_AFTER_MASU:
        if pos >0 and items[pos-1].is_masu:
            matched_conditions |= COND_AFTER_MASU
    if conditions & COND_AFTER_TE:
        if pos >0 and items[pos-1].txt[-1] == 'て':
            matched_conditions |= COND_AFTER_TE
    if conditions & COND_BEFORE_TE:
        if pos < len(items)-1 and items[pos+1].txt[-1] == 'て':
            matched_conditions |= COND_BEFORE_TE
    if conditions & COND_AFTER_CLASS:
        if pos >0 and params['cond_class'] in items[pos-1].classes:
            matched_conditions |= COND_AFTER_CLASS
    if conditions & COND_BEFORE_ITEM:
        if not flexible:
            if pos+num_scanned_items < len(items):
                if params['item_txt'] == items[pos+num_scanned_items].txt:
                    if params['item_class'] in items[pos+num_scanned_items].classes or params['item_class']==any_class:
                        matched_conditions |= COND_BEFORE_ITEM
        else:
            stop = False
            i = pos+num_scanned_items
            while (i < len(items)) and not stop:
                if items[i].txt in elongation_marks:
                    i += 1
                else:
                    if params['item_txt'] == items[i].txt:
                        if params['item_class'] in items[i].classes or params['item_class']==any_class:
                            matched_conditions |= COND_BEFORE_ITEM
                    stop = True

    if conditions & COND_AFTER_ITEM:
        if pos>0:
            if params['item_txt'] == items[pos-1].txt:
                if params['item_class'] in items[pos-1].classes or params['item_class']==any_class:
                    matched_conditions |= COND_AFTER_ITEM

    if conditions & COND_NOT:
        if matched_conditions == COND_NONE:
            # none of the other conditions matched so inversely this is a match
            matched_conditions = conditions

    if flexible:
        # just add this here to allow easier comparison
        matched_conditions |= COND_FLEXIBLE

    return matched_conditions

def handle_explicit_form_and_class_changes(pos,items, explicit_change_list):
    changed = False

    def set_alt_form(item,alt_form):
        if isinstance(alt_form, list):
            alt_forms = alt_form
        else:
            alt_forms = [alt_form]
        item.alt_forms = []
        item.appendable_alt_forms = []
        for af in alt_forms:
            if af != '' and af[-1] == '_':
                # this is non-appendable alt form
                af = af[:-1]
                item.alt_forms.append(af)
            else:
                item.alt_forms.append(af)
                if af != '':
                    item.appendable_alt_forms.append(af)

    def does_pattern_match(ew):
        p_list = ew[0]
        p_classes = ew[1]
        lp = len(p_list)
        i = 0
        j = 0
        cont = True
        gaps = []
        while (i<lp) and (pos+j<len(items)) and cont:
            if j != 0 and items[pos+j].txt in elongation_marks:
                gaps.append(i)
                j += 1
            else:
                if items[pos+j].txt != p_list[i]:
                    cont = False
                elif p_classes[i] != any_class and p_classes[i] not in items[pos+j].classes:
                    cont = False
                i += 1
                j += 1
        if i == lp and cont:
            return True, gaps
        return False, []

    lw = len(items)
    for ew in explicit_change_list:
        p_list = ew[0]
        p_classes = ew[1]
        conditions = ew[2]
        params = ew[4]
        flexible_matching = False
        if 'flexible_matching' in params:
            flexible_matching = params['flexible_matching']

        lp = len(p_list)
        if pos + lp <= lw:
            if flexible_matching:
                # flexible matching mode allows elongation marks inside the pattern but scanning is slower
                match, gaps = does_pattern_match(ew)
            else:
                # rigid pattern and class matching
                i = 0
                while (i<lp) and (items[pos+i].txt==p_list[i]) and ((p_classes[i] == any_class) or (p_classes[i] in items[pos+i].classes)):
                    i += 1
                if i == lp:
                    match = True
                    gaps = []
                else:
                    match = False
            if match:
                # All items match. Check extra conditions yet.
                task = ew[3]
                params = ew[4]
                allowed = True
                if conditions:
                    matched_conds = check_matching_condition(items,pos,conditions,'','',lp,params)
                    if matched_conds != conditions:
                        allowed = False

                if allowed:
                    if get_verbose_level()>=1:
                        LOG(1,"%s matches item alteration %s" % (items[pos].txt,str(ew)))
                    if task == TASK_MERGE:
                        if 'parts' in params:
                            # merge several items into two or more items
                            i = 0
                            if len(gaps)>0:
                                raise Exception("TODO gaps in merge!")
                            for part,cl,ortho in zip(params['parts'],params['classes'],params['orthos']):
                                items[pos+i].txt = part
                                items[pos+i].ortho = ortho
                                items[pos+i].alt_forms = []
                                items[pos+i].appendable_alt_forms = []
                                items[pos+i].classes = [cl]
                                i += 1
                            while i<lp:
                                items[pos+i].flags = REMOVE_ITEM
                                i += 1
                        else:
                            # simple merge
                            if len(gaps)>0:
                                raise Exception("TODO gaps in merge!")
                            if 'class' in params:
                                target_class = params['class']
                                # Change the class of the first particle and mark the next ones to be merged
                                items[pos].classes = [target_class]
                            elif 'class_list' in params:
                                    target_class_list = params['class_list']
                                    # Change the class of the first particle and mark the next ones to be merged
                                    items[pos].classes = target_class_list
                            for i in range(1,lp):
                                items[pos+i].flags = MERGE_ITEM
                        changed = True
                    elif task == TASK_REPLACE or task == TASK_DIVIDE:
                        # replace 1 or more items with two or more items
                        new_items = []
                        j = 0
                        i = 0
                        while i < len(params['parts']):
                            if i in gaps:
                                gaps.pop(0)
                                new_items.append(items[pos+j])
                            else:
                                part = params['parts'][i]
                                cll = items[pos].classes
                                if 'classes' in params:
                                    cll = [params['classes'][i]]
                                elif 'class' in params:
                                    cll = [params['class']]
                                it = LexicalItem(part,'',cll)
                                it.base_score = get_class_base_score(cll[0])
                                if 'orthos' in params:
                                    it.ortho = params['orthos'][i]
                                if 'conjugation_roots' in params:
                                    it.conjugation_root = params['conjugation_roots'][i]
                                if 'alt_forms' in params:
                                    set_alt_form(it,params['alt_forms'][i] )
                                if 'word_id' in params:
                                    # force the word id for these items
                                    it.word_id = params['word_id']
                                    it.flags |= NO_SCANNING
                                new_items.append(it)
                                i += 1
                            j += 1
                        
                        # just replace the first item with all the items
                        # and remove the rest of the replaced items
                        items[pos].replaced_items = new_items
                        items[pos].flags |= REPROCESS | REPLACE_ITEM
                        i = 1
                        while i<lp:
                            items[pos+i].flags = REMOVE_ITEM
                            i += 1
                    elif task == TASK_MODIFY:
                        if 'add_class' in params:
                            # Only add new class to the class list but do not merge or divide
                            target_class = params['add_class']
                            for i in range(0,lp):
                                if target_class not in items[pos+i].classes:
                                    items[pos+i].classes.append(target_class)
                                    changed = True
                        elif 'classes' in params:
                            # Only set new classes but do not merge or divide
                            for i in range(0,lp):
                                cll = [params['classes'][i]]
                                if cll != items[pos+i].classes:
                                    items[pos+i].classes = cll
                                    changed = True
                        elif 'class' in params:
                            # Only set new class but do not merge or divide
                            for i in range(0,lp):
                                cll = [params['class']]
                                if cll != items[pos+i].classes:
                                    items[pos+i].classes = cll
                                    changed = True
                        if 'orthos' in params:
                            for i in range(0,lp):
                                ort = params['orthos'][i]
                                if items[pos+i].ortho != ort:
                                    items[pos+i].ortho = ort
                                    changed = True

                    if 'ortho' in params:
                        ortho = params['ortho']
                        for i in range(0,lp):
                            items[pos+i].ortho = ortho
                    if 'alt' in params:
                        alt_form = params['alt']
                        items[pos].alt_forms = [alt_form]
                        if alt_form != '':
                            items[pos].appendable_alt_forms = [alt_form]
                        if 'alt_score' in params:
                            items[pos].alt_scores[alt_form] = params['alt_score']
                    if 'alt_forms' in params:
                        for i in range(0,lp):
                            set_alt_form(items[pos+i], params['alt_forms'][i])
                    if 'root_ortho' in params:
                        items[pos].ortho = params['root_ortho']
                        for i in range(1,lp):
                            items[pos+i].ortho = ''
                    if 'add_flags' in params:
                        item_flags = params['add_flags']
                        for i in range(lp):
                            items[pos+i].flags |= item_flags[i]
                    if 'word_id' in params:
                        # force the word id for these items
                        for i in range(lp):
                            items[pos+i].word_id = params['word_id']
                            items[pos+i].flags |= NO_SCANNING
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
            items[pos+1].flags |= MERGE_ITEM
            items[pos].ortho = ''
"""

def add_alternative_forms_and_classes(pos,items):

    if items[pos].txt in alternative_forms.keys():
        alt_forms = alternative_forms[items[pos].txt]
        for alt_form in alt_forms:
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)
            if alt_form not in items[pos].appendable_alt_forms:
                items[pos].appendable_alt_forms.append(alt_form)

    alt_cll = set()
    if items[pos].txt in alternative_classes:
        alt_cll.update(alternative_classes[items[pos].txt])
    if items[pos].ortho in alternative_classes:
        alt_cll.update(alternative_classes[items[pos].ortho])
    for alt_form in items[pos].alt_forms:
        if alt_form in alternative_classes:
            alt_cll.update(alternative_classes[alt_form])
    for cl in alt_cll:
        if cl not in items[pos].classes:
            items[pos].classes.append(cl)

def get_previous_main_classes(items,pos):
    while pos > 0:
        if gp_class not in items[pos-1].classes:
            if aux_verb_class not in items[pos-1].classes or verb_class in items[pos-1].classes:
                return items[pos-1].classes
        pos -= 1
    return []


def add_emphatetic_and_elongated_alternative_forms(pos,items):

    for elong_mark in elongation_marks:
        if elong_mark in items[pos].txt:
            allowed = True
            # if elongation mark is before/after/sandwiched between numerals, do nothing
            if pos > 0 and numeric_pseudoclass in items[pos-1].classes:
                allowed = False
            if pos < len(items)-1 and numeric_pseudoclass in items[pos+1].classes:
                allowed = False
            if allowed:
                # create an alternative form by removing ー 
                alt_form = items[pos].txt.replace(elong_mark,'')
                if alt_form not in items[pos].alt_forms:
                    items[pos].alt_forms.append(alt_form)
                if alt_form not in items[pos].appendable_alt_forms:
                    items[pos].appendable_alt_forms.append(alt_form)
                
                #items[pos].alt_scores[alt_form] = int(items[pos].base_score*0.3)
                #if pos != len(items) -1:
                #    items[pos].neighbour_alt_score_modifier[alt_form] = 0.3

                # remove class restrictions when doing JMDict search
                # because Unidic most likely didn't recognize the class correctly
                #items[pos].any_class = True

                if pos > 0:
                    if alt_form == '':
                        # if current alternative element becomes empty, transfer
                        # the class of previous element to this one and following element
                        # For example in ['すごー','ー','い']   the middle element is 
                        # empty and the 'ー' and 'い' elements are marked as adjective
                        for cl in items[pos-1].classes:
                            if cl != prefix_class:
                                if pos<len(items)-1:
                                    if cl not in items[pos+1].classes:
                                        items[pos+1].classes.append(cl)
                                if cl not in items[pos].classes:
                                    items[pos].classes.append(cl)

                    prev_cll = get_previous_main_classes(items,pos)
                    if verb_class in prev_cll:
                        # allow conjugation for this and the next item
                        # because Unidict most likely didn't detect the class correctly
                        items[pos].explicitly_allow_conjugation = True
                        if pos < len(items) - 1:
                            items[pos+1].explicitly_allow_conjugation = True

    for small_vowel in small_vowels:
        if small_vowel in items[pos].txt:
            idx = items[pos].txt.index(small_vowel)
            allowed = False
            if idx > 0:
                # is the previous character in the lexical item suitable e.g. のォ ?
                if items[pos].txt[idx-1] in small_vowel_fade[small_vowel]:
                    allowed = True
            else:
                if pos > 0:
                    # is the last character in the previous lexical item suitable e.g. この + ォ ?
                    if len(items[pos-1].txt)>0 and items[pos-1].txt[-1] in small_vowel_fade[small_vowel]:
                        allowed = True

            if allowed:
                # create an alternative form by removing the small vowel
                alt_form = items[pos].txt.replace(small_vowel,'')
                if alt_form not in items[pos].alt_forms:
                    items[pos].alt_forms.append(alt_form)
                if alt_form not in items[pos].appendable_alt_forms:
                    items[pos].appendable_alt_forms.append(alt_form)
                items[pos].alt_scores[alt_form] = int(items[pos].base_score*0.8)


    if items[pos].txt == '・':
        items[pos].alt_forms.append('')
        items[pos].appendable_alt_forms.append('')
        items[pos].alt_scores[''] = 0.01

    if len(items[pos].txt)>1:
        if items[pos].txt[-1] == 'っ' or items[pos].txt[-1] == 'ッ':
            # Possibly dialect. Check alternative form without the emphasis
            # おっしえなーい  -> おしえなーい
            alt_form = items[pos].txt[:-1]
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)
                items[pos].appendable_alt_forms.append(alt_form)
                items[pos].alt_scores[alt_form] = int(items[pos].base_score*0.3)
                if pos != len(items) -1:
                    items[pos].neighbour_alt_score_modifier[alt_form] = 0.3

    if 'ー' in items[pos].txt:
        # create an alternative form by extending the vowel when ー is detected
        # Example: ありがとー　->　ありがとう
        i = items[pos].txt.index('ー')
        if i>0:
            rep = get_vowel_extension(items[pos].txt[i-1])
        elif pos > 0:
            # TODO: finetune. At least prevent alt-only single item scan match
            #if pos > 0:
            #    rep = get_vowel_extension(items[pos-1].txt[-1])
            #else:
            rep = ''
        else:
            rep = ''
        if rep != '':
            alt_form = items[pos].txt.replace('ー',rep)
            if alt_form not in items[pos].alt_forms:
                items[pos].alt_forms.append(alt_form)
            if alt_form not in items[pos].appendable_alt_forms:
                items[pos].appendable_alt_forms.append(alt_form)
            items[pos].alt_scores[alt_form] = int(items[pos].base_score*0.9)
            if pos != len(items) -1:
                items[pos].neighbour_alt_score_modifier[alt_form] = 0.9


        # Add alternative forms for colloquial vowel extension
        # e.g. えれー -> えらい, ねー -> ない
        def get_norm_form_for_colloquial_vowel_extension(ch):
            colloquial_vowel_extension = {
                'れ' : 'らい',
                'て' : 'たい',
            }
            if ch in colloquial_vowel_extension:
                return colloquial_vowel_extension[ch]
            return ''

        normal_form = ''
        if i>0:
            normal_form = get_norm_form_for_colloquial_vowel_extension(items[pos].txt[i-1])
            normal_form_pos = pos
            alt_form = items[pos].txt[:i-1] + normal_form
        else:
            if pos>0:
                normal_form = get_norm_form_for_colloquial_vowel_extension(items[pos-1].txt[-1])
                alt_form = items[pos-1].txt[:-1] + normal_form
                normal_form_pos = pos-1
        if normal_form != '':
            items[normal_form_pos].alt_forms.append(alt_form)
            items[normal_form_pos].appendable_alt_forms.append(alt_form)
            items[normal_form_pos].alt_scores[alt_form] = 0.7*items[normal_form_pos].base_score
            prev_main_classes = get_previous_main_classes(items,normal_form_pos)
            # Colloquial vowel extension is mainly with verbs and adjectives
            """
            if verb_class not in prev_main_classes and verb_class not in items[normal_form_pos].classes:
                items[normal_form_pos].classes.append(verb_class)
            if adjectival_noun_class not in prev_main_classes and adjectival_noun_class not in items[normal_form_pos].classes:
                items[normal_form_pos].classes.append(adjectival_noun_class)
            """
            #items[normal_form_pos].alt_form_flags[alt_form] = ANY_CLASS
            #items[normal_form_pos].any_class = True 

def convert_to_adjective_from_singlekanji(items,pos):
    seqs = get_adjective_seqs_for_single_kanji(items[pos].txt)
    for seq in seqs:
        kanji_elements = get_kanji_elements_by_seq(seq)
        for k_elem in kanji_elements:
            if items[pos].txt in k_elem:
                if k_elem not in items[pos].alt_orthos:
                    items[pos].alt_orthos.append(k_elem)
    if len(seqs)>0:
        items[pos].classes.append(adjective_class)


def particle_post_processing(pos, items):
    if not handle_explicit_form_and_class_changes(pos,items, explicit_word_changes):
        cll = items[pos].classes

        add_alternative_forms_and_classes(pos,items)

        if len(cll) == 1:
            if cll[0] <= punctuation_mark_class:
                items[pos].flags |= NO_SCANNING
                return
            #if cll[0] <= mid_sentence_punctuation_mark_class:
            #    items[pos].flags |= START_OF_SCAN_DISABLED
            #    return True

        if verb_class in cll or (aux_verb_class in cll and (items[pos].ortho=='だ')or(items[pos].ortho=='ない')):
            check_verbs(pos,items)
        if prefix_class in cll and pos < len(items) - 1 and is_hiragana(items[pos+1].txt[0]):
            # erroneously assigned as prefix, most likely an adjective
            convert_to_adjective_from_singlekanji(items,pos)
        # TODO: adjust check_adjectives for this to work
        #if noun_class in items[pos].classes and pos < len(items) - 1 and items[pos+1].txt == 'しき':
        #    # erroneously assigned as noun, most likely an adjective
        #    convert_to_adjective_from_singlekanji(items,pos)
        if adjective_class in cll and not verb_class in cll:
            return check_adjectives(pos,items)
        if adjectival_noun_class in cll:
            return check_adjectival_nouns(pos,items)
        if noun_class in cll:
            return check_nouns(pos,items)
        if interjection_class in cll:
            if pos > 0 and prefix_class in items[pos-1].classes:
                # wrong classification
                items[pos].any_class = True
        if aux_verb_class in cll and pos == 0 and items[pos].txt != 'じゃ':
            # wrong classification
            items[pos].any_class = True
            if len(items)>1:
                if aux_verb_class in items[pos+1].classes:
                    # also the next item has likely wrong classification
                    items[pos+1].any_class = True
        if suffix_class in cll and pos == 0:
            # wrong classification
            # most likely noun, but allow other classes as well
            items[pos].classes.append(noun_class)
            items[pos].any_class = True
        if gp_class in cll and items[pos].txt == 'の':
            if pos > 0 and pos < len(items)-1:
                if noun_class in items[pos-1].classes and (verb_class in items[pos+1].classes or adjective_class in items[pos+1].classes):
                    # add alternative for の -> が
                    # e.g. 気の付く　-> 気が付く
                    items[pos].alt_forms.append('が')
                    items[pos].appendable_alt_forms.append('が')
                    items[pos].alt_scores['が'] = 0.1

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
                if pos > 0 and pos < len(items)-1 and \
                    (adjectival_noun_class in items[pos-1].classes or \
                     noun_class in items[pos-1].classes or \
                     suffix_class in items[pos-1].classes
                     ):
                    #items[pos].flags |= BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED
                    items[pos].flags |= MERGE_ITEM
            if items[pos].txt == 'に':
                if pos > 0 and adjectival_noun_class in items[pos-1].classes:
                    # almost identical case as above, but here it's 
                    # adjectival noun + に 
                    # Example: ロマンチック + に 
                    items[pos].ortho = items[pos].txt
                    items[pos].flags |= MERGE_ITEM
                    # many adjectival noun + に combinations work as adverbs
                    # e.g. 非常に
                    items[pos-1].classes.append(adverb_class)
                    #items[pos].flags |= BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED
            if items[pos].txt == 'し':
                if items[pos].ortho == 'き':
                    # let's drop this nonsense
                    items[pos].ortho = ''
            

# merge or replace those particles that are marked
def merge_or_replace_items(items):
    pos = 0
    processed_items = []
    changed_items = []
    for i in range(len(items)):
        if items[i].flags & MERGE_ITEM:
            changed_items.append(processed_items[pos-1])
            if get_verbose_level()>=2:
                LOG(2,bcolors.OKGREEN + "Merged item" + bcolors.ENDC)
                pretty_print_lexical_item(processed_items[pos-1])
                LOG(2,"with")
                pretty_print_lexical_item(items[i])

            prev_txt = processed_items[pos-1].txt
            new_txt = prev_txt + items[i].txt

            # create alternative form permutations for merged particle
            prev_appendable_alt_forms = [processed_items[pos-1].txt]
            for alt_form in processed_items[pos-1].appendable_alt_forms:
                if alt_form not in prev_appendable_alt_forms:
                    prev_appendable_alt_forms.append(alt_form)

            # preserve the score of each previous alt form
            for alt_form in prev_appendable_alt_forms:
                if alt_form not in processed_items[pos-1].alt_scores:
                    processed_items[pos-1].alt_scores[alt_form] = processed_items[pos-1].base_score

            new_alts = processed_items[pos-1].alt_forms

            variations = items[i].alt_forms + [items[i].txt]
            ortho = items[i].ortho
            if ortho != '' and ortho not in variations:
                variations.append(ortho)

            for alt_form in variations:
                for prev_alt_form in prev_appendable_alt_forms:
                    new_alt = prev_alt_form + alt_form
                    if new_alt != new_txt and new_alt not in new_alts:

                        # combine alt form score
                        if prev_alt_form in processed_items[pos-1].alt_scores:
                            score = processed_items[pos-1].alt_scores[prev_alt_form]
                        else:
                            score = processed_items[pos-1].base_score
                        if alt_form in items[i].alt_scores:
                            score += items[i].alt_scores[alt_form]
                        else:
                            score += items[i].base_score
                        processed_items[pos-1].alt_scores[new_alt] = score

                        # combine alt form flags
                        flag = 0
                        if prev_alt_form in processed_items[pos-1].alt_form_flags:
                            flag = processed_items[pos-1].alt_form_flags[prev_alt_form]
                        if alt_form in items[i].alt_form_flags:
                            flag |= items[i].alt_form_flags[alt_form]
                        if flag != 0:
                            processed_items[pos-1].alt_form_flags[new_alt] = flag

                        new_alts.append(new_alt)

            new_appendable_alt_forms = []
            for alt_form in items[i].appendable_alt_forms:
                for prev_alt_form in prev_appendable_alt_forms:
                    new_alt = prev_alt_form + alt_form
                    if new_alt != new_txt and new_alt not in new_appendable_alt_forms:
                        new_appendable_alt_forms.append(new_alt)

            prev_ortho = processed_items[pos-1].ortho
            if prev_ortho != '':
                if prev_ortho not in processed_items[pos-1].alt_scores:
                    processed_items[pos-1].alt_scores[prev_ortho] = processed_items[pos-1].base_score

            processed_items[pos-1].alt_forms = new_alts
            processed_items[pos-1].appendable_alt_forms = new_appendable_alt_forms
            processed_items[pos-1].txt = new_txt
            processed_items[pos-1].base_score += items[i].base_score

            if items[i].any_class:
                # propagate the ANY_CLASS flag to root item
                processed_items[pos-1].any_class = True

            if get_verbose_level()>=2:
                LOG(2,"resulting..")
                pretty_print_lexical_item(processed_items[pos-1])

            #processed_items[pos-1].flags |= REPROCESS

        elif items[i].flags & REPLACE_ITEM:
            if get_verbose_level()>=2:
                LOG(2,bcolors.OKCYAN + "Replace item" + bcolors.ENDC)
                pretty_print_lexical_item(items[i])
                LOG(2,"with")
                for it in items[i].replaced_items:
                    pretty_print_lexical_item(it)
            for new_item in items[i].replaced_items:
                new_item.flags &= (~REPLACE_ITEM) # clear the flag just in case
                processed_items.append(new_item)
                changed_items.append(new_item)
                pos += 1
        elif items[i].flags & REMOVE_ITEM:
            if get_verbose_level()>=2:
                LOG(2,bcolors.WARNING + "Remove item" + bcolors.ENDC)
                pretty_print_lexical_item(items[i])
            pass
        else:
            processed_items.append(items[i])
            pos += 1

    for i in range(len(changed_items)):
        add_alternative_forms_and_classes(i,changed_items)

    return processed_items

def inhibit_seqs(items):
    li = len(items)
    for pattern in inhibit_seq_pattern_list:
        txt = pattern[0]
        cl = pattern[1]
        required_postfix_list = pattern[2]
        seq_list = pattern[3]
        
        for i,item in enumerate(items):
            if item.txt == txt and cl in item.classes:
                if i < li - 1:
                    next_txt = items[i+1].txt
                    for postfix in required_postfix_list:
                        if postfix in next_txt and next_txt.index(postfix) == 0:
                            LOG(2,"%d:%s matched inhibit pattern %s" % (i,item.txt,str(pattern)),color=bcolors.WARNING )
                            item.inhibit_seq_list += seq_list


def stutter_detection(items):
    ignored_stutter_chars = ['ハ','は']
    y_hiragana = ['ゃ','ゅ','ょ']

    # TODO
    ignored_stutter_words = ['だだっこ','おおおとこ','とっとと']
    # ['で、', 'でっけー', '男．．．']
    # ["ええっ？", "映画を", "観てた！？"]
    # ["あーっと、", "ボールは", "あさっての", "方向へ！！"]
    # ["だだって", "しょうがないじゃないか"
    # ['そ', 'そうね', '手先だけは', '器用かも']
    # ["ななな", "なんだよ。"]

    # stutter detection
    i = 0
    stop = False
    if len(items) > 1 and len(items[0].txt)>0:
        stutter_char = items[0].txt[0]
        stutter_y_char = None
        j = 1
        if len(items[0].txt)>1:
            if items[0].txt[1] in y_hiragana:
                stutter_y_char =  items[0].txt[1]
                j += 1
        else:
            i += 1
            j = 0
            if len(items[i].txt)>0:
                if items[i].txt[j] in y_hiragana:
                    stutter_y_char =  items[i].txt[j]
                    j += 1

        stutter_char_count = 0
        if not is_cjk(stutter_char):
            while not stop:
                while i < len(items) and j >= len(items[i].txt):
                    j = 0
                    i += 1
                    
                if i < len(items):
                    if items[i].txt[j] in mid_sentence_punctuation_marks:
                        j += 1
                        stutter_char_count += 1
                    elif items[i].txt[j] in elongation_marks:
                        j += 1
                        stutter_char_count += 1
                    elif items[i].txt[j] == stutter_char and (stutter_y_char is None or (j<(len(items[i].txt)-1) and items[i].txt[j+1] == stutter_y_char)):
                        j += 1
                        stutter_char_count += 1
                        if stutter_y_char is not None:
                            j += 1
                            stutter_char_count += 1
                    elif punctuation_mark_class in items[i].classes:
                        j = 0
                        stutter_char_count += len(items[i].txt)
                        i += 1
                    else:
                        verified_stutter = False
                        if i > 0: # and stutter_char_count > 1:
                            if j > 0 and stutter_char not in ignored_stutter_chars: # and stutter_char == items[i].txt[j-1]:
                                if stutter_char_count > 1:
                                    verified_stutter = True
                            else:
                                if is_cjk(items[i].txt[j]):
                                    if stutter_char == 'お' and i==1 and j==0:
                                        # ignore honorific お as stutter when it is attached directly to the kanji
                                        pass
                                    else:
                                        seqs = search_sequences_by_word(items[i].txt)
                                        for seq in seqs:
                                            readings = get_readings_by_seq(seq)
                                            for reading in readings:
                                                if reading[0] == stutter_char:
                                                    if  (stutter_y_char is None or ((len(reading)>1) and (stutter_y_char == reading[1]))):
                                                        verified_stutter = True

                            if verified_stutter:
                                for k in range(0,i):
                                    LOG(1,"Flagging %d:%s to NO-SCAN because of stutter" % (k,items[k].txt))
                                    items[k].classes = [stutter_class]
                                    items[k].flags |= NO_SCANNING
                        stop = True
                else:
                    stop = True


def post_process_unidic_particles(items):
    omit_flags = MERGE_ITEM | REPLACE_ITEM | REMOVE_ITEM

    stutter_detection(items)

    # move emphasis mark on verbs from base to the next conjugative element
    for i in range(len(items)-1):
        if verb_class in items[i].classes or aux_verb_class in items[i].classes:
            if items[i].txt[-1] == 'っ':
                if aux_verb_class in items[i+1].classes or gp_class in items[i+1].classes:
                    items[i].txt = items[i].txt[:-1]
                    prev_txt = items[i+1].txt
                    items[i+1].txt = 'っ' + prev_txt
                    items[i+1].ortho = ''
                    # it's possible that this emphasis mark was due to dialect
                    # so add a variation without it but with lower score
                    #if prev_txt not in items[i+1].alt_forms:
                    #    items[i+1].alt_forms.append(prev_txt)
                    #    items[i+1].alt_scores[prev_txt] = int(items[i+1].base_score*0.6)

                    # This item cannot be the last item of a scanned word
                    ending_alt_form_exceptions = ['だ']
                    if items[i].txt not in ending_alt_form_exceptions:
                        items[i].non_ending_alt_forms.append(items[i].txt)

    # add variants for possible OCR misread
    misread_characters = {
        'つ' : 'っ',
        'ぱ' : 'ば',
        'ば' : 'ぱ',
        'び' : 'ぴ',
        'ぴ' : 'び',
        'ぶ' : 'ぷ',
        'ぷ' : 'ぶ',
        'べ' : 'ぺ',
        'ぺ' : 'べ',
        'ぼ' : 'ぽ',
        'ぽ' : 'ぼ',
        'バ' : 'パ',
        'パ' : 'バ',
        'ビ' : 'ピ',
        'ピ' : 'ビ',
        'ブ' : 'プ',
        'プ' : 'ブ',
        'ベ' : 'ペ',
        'ペ' : 'ベ',
        'ボ' : 'ポ',
        'ポ' : 'ボ',
    }
    misread_kanjis = {
        'ロ' : '口',  # katakana ro -> guchi
        'タ' : '夕', # katakana ta -> yuu (evening)
    }
    for i in range(len(items)):
        for misread_letter,correct_letter in misread_characters.items():
            if misread_letter in items[i].txt:
                alt = items[i].txt.replace(misread_letter,correct_letter)
                if alt not in items[i].alt_forms:
                    items[i].alt_forms.append(alt)
                    items[i].appendable_alt_forms.append(alt)
                    items[i].alt_scores[alt] = 0.4
        for misread_kanji, correct_kanji in misread_kanjis.items():
            if items[i].txt == misread_kanji:
                items[i].alt_forms.append(correct_kanji)
                items[i].appendable_alt_forms.append(correct_kanji)
                items[i].alt_scores[correct_kanji] = 0.8


    # identify end-of-clause items
    for i in range(len(items)):
        if i==len(items)-1:
            items[i].end_of_clause = True
        else:
            if items[i+1].txt == 'って' or punctuation_mark_class in items[i+1].classes:
                items[i].end_of_clause = True

    # modify items before trying conjugation
    for i in range(len(items)):
        #if is_item_allowed_for_conjugation(items[i]):
        if not (items[i].flags & omit_flags): 
            handle_explicit_form_and_class_changes(i,items, pre_conjugation_modifications)
    items = merge_or_replace_items( items )

    for i in range(len(items)):
        add_emphatetic_and_elongated_alternative_forms(i,items)
        cll = items[i].classes
        if aux_verb_class not in cll and gp_class not in cll and verb_class not in cll:
            add_alternative_form_from_lemma(items[i])


    if get_verbose_level()>0:
        print("\nAfter unidic preparser:")
        for i in range(len(items)):
            pretty_print_lexical_item(items[i])


    cont = True
    for i in range(len(items)):
        items[i].flags |= REPROCESS
    while cont:
        for i in range(len(items)):
            if items[i].flags & REPROCESS:
                items[i].flags &= (~REPROCESS) # clear the flag
                if not (items[i].flags & omit_flags): 
                    particle_post_processing(i,items)

        # merge those particles that are marked
        items = merge_or_replace_items( items )

        cont = False
        if any(item.flags & REPROCESS for item in items):
            # do another round
            cont = True

    for item in items:        
        if verb_class in item.classes:# or aux_verb_class in item.classes:
            # add alt form for ぬ -> ない
            # e.g. 知れぬ -> 知れない
            if len(item.txt)>0 and item.txt[-1] == 'ぬ':
                if item.ortho != '' and item.ortho[-1] != 'ぬ':
                    alt = item.txt[:-1] + 'ない'
                    item.alt_forms.append(alt)
                    item.appendable_alt_forms.append(alt)


    inhibit_seqs(items)

    return items
