from helper import *
from jp_parser_helper import *
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
    for elong_mark in elongation_marks:
        if elong_mark in items[pos].txt:
            # create an alternative form by removing ー 
            alt_form = items[pos].txt.replace(elong_mark,'')
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

        if len(cll) == 1:
            if cll[0] <= punctuation_mark_class:
                items[pos].flags |= NO_SCANNING
                return True
            #if cll[0] <= mid_sentence_punctuation_mark_class:
            #    items[pos].flags |= START_OF_SCAN_DISABLED
            #    return True

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
