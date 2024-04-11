from helper import *
from jp_parser_helper import *
from jp_parser_print import pretty_print_lexical_item
from conjugation import *

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
            if has_word_katakana(w):
                item.alt_forms = [katakana_to_hiragana(w)]
                item.appendable_alt_forms = [katakana_to_hiragana(w)]
            if pron_base != '':
                item.pron_base = katakana_to_hiragana(pron_base)
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
        if lemma not in item.alt_forms:
            item.alt_forms.append(lemma)
            item.appendable_alt_forms.append(lemma)

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
        condition = ew[2]
        lp = len(p_list)
        if pos + lp <= lw:
            if condition & COND_FLEXIBLE:
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
                if condition:
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
                    if condition & COND_AFTER_MASU:
                        if pos == 0:
                            allowed = False
                        else:
                            if not items[pos-1].is_masu:
                                allowed = False
                    if condition & COND_END_OF_CLAUSE:
                        if not items[pos].end_of_clause:
                            allowed = False
                    if condition & COND_AFTER_TE:
                        if pos == 0:
                            allowed = False
                        else:
                            if items[pos-1].txt[-1] != 'て':
                                allowed = False
                    if condition & COND_AFTER_AUX_VERB:
                        if pos == 0:
                            allowed = False
                        else:
                            if aux_verb_class not in items[pos-1].classes:
                                allowed = False

                    if condition & COND_BEFORE_ITEM:
                        if pos+lp == lw:
                            allowed = False
                        if params['item_txt'] != items[pos+1].txt:
                            allowed = False
                        if params['item_class'] not in items[pos+1].classes:
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
                            if pos<len(items)-1:
                                if cl not in items[pos+1].classes:
                                    items[pos+1].classes.append(cl)
                            if cl not in items[pos].classes:
                                items[pos].classes.append(cl)

    for small_vowel in small_vowels:
        if small_vowel in items[pos].txt:
            idx = items[pos].txt.index(small_vowel)
            if idx > 0:
                if items[pos].txt[idx-1] in small_vowel_fade[small_vowel]:
                    # create an alternative form by removing the small vowel
                    alt_form = items[pos].txt.replace(small_vowel,'')
                    if alt_form not in items[pos].alt_forms:
                        items[pos].alt_forms.append(alt_form)
                    if alt_form not in items[pos].appendable_alt_forms:
                        items[pos].appendable_alt_forms.append(alt_form)
                    items[pos].alt_scores[alt_form] = int(items[pos].base_score*0.8)


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
            # TODO: finetune
            #rep = get_vowel_extension(items[pos-1].txt[-1])
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
        if adjective_class in cll and not verb_class in cll:
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
                    #items[pos].flags |= BIND_TO_PREVIOUS_ITEM_IF_LEFT_UNTETHERED

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
                pretty_print_lexical_item(items[pos-1])
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
                        if prev_alt_form in processed_items[pos-1].alt_scores:
                            score = processed_items[pos-1].alt_scores[prev_alt_form]
                        else:
                            score = processed_items[pos-1].base_score
                        if alt_form in items[i].alt_scores:
                            score += items[i].alt_scores[alt_form]
                        else:
                            score += items[i].base_score
                        processed_items[pos-1].alt_scores[new_alt] = score
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

            if get_verbose_level()>=2:
                LOG(2,"resulting..")
                pretty_print_lexical_item(items[pos-1])

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

def post_process_unidic_particles(items):
    omit_flags = MERGE_ITEM | REPLACE_ITEM | REMOVE_ITEM

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

    inhibit_seqs(items)

    return items
