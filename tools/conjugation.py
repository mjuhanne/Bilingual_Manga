from jp_parser_helper import *
from jmdict import *
from parser_logging import *
from helper import *

verb_conjugations = dict()
adj_conjugations = dict()

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

