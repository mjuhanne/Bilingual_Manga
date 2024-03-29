from jp_parser_helper import *
from jmdict import *
from parser_logging import *
from helper import *

verb_conjugations = []
adj_conjugations = []
conjugations_dict = dict()

def is_item_allowed_for_conjugation(item):
    if verb_class in item.classes or aux_verb_class in item.classes:
        return True
    if gp_class in item.classes or adjectival_noun_class in item.classes:
        return True
    if adjective_class in item.classes:
        return True
    if suffix_class in item.classes:
        # -さ (-ness)
        return True
    return False


def attempt_conjugation(pos, items, stem, conj_class, rec_level=0):
    #conj_ending, conjugations, details = conjugations_dict[conj_class]
    if rec_level > 6:
        return 0, []

    print_prefix = ''.ljust(4+rec_level*4)
    if rec_level==0:
        LOG(2,"Conjugate %s stem %d:%s" % (get_jmdict_pos_code(conj_class),pos,stem))


    items_l = len(items)
    max_sub_conj_item_count = 0
    max_subj_conj_list = []
    if stem != '':
        conj_root = [(conj_class,stem,'Root')]
    else:
        conj_root = []


    for conj_ending, (conjugations, conj_details) in conjugations_dict[conj_class].items():
        #print(get_jmdict_pos_code(conj_class),items[pos].txt,rec_level)
        for conj in conjugations:
            (tense,suffix,next_type,next_type_suffix,next_type_code) = conj
            details = conj_details[conj]
            # Conjugation.txt doesn't have a follow-up for -Te/-you-to-suru so add it programmatically
            if tense == 'Te-form':
                next_type = jmdict_auxiliary_verb_class
                next_type_suffix = suffix
            elif tense == 'Volitional':
                next_type = jmdict_class_list.index('aux-volitional')
                next_type_suffix = suffix
            if 'repare' in tense:
                pass

            conj_str = stem + suffix
            conj_next_type_str = stem + next_type_suffix

            if next_type is not None and next_type_suffix == '':
                # special case: jump right to next conjugation class because the required 
                # suffix is empty
                LOG(2,print_prefix + "Conjugate by default %s " % get_jmdict_pos_code(next_type))
                sub_conj_item_count, sub_conjs = attempt_conjugation(pos,items,'',next_type, rec_level+1)
                if sub_conj_item_count > max_sub_conj_item_count:
                    max_sub_conj_item_count = sub_conj_item_count
                    max_subj_conj_list = conj_root + [(next_type,next_type_suffix,tense)] + sub_conjs
                    LOG(2,print_prefix + "match " + str(max_subj_conj_list))
                    #print(max_subj_conj_list)

            i = 0
            v_str = ''
            cont = True
            while pos+i<items_l and cont:
                item = items[pos+i]
                found = False

                if is_item_allowed_for_conjugation(item):

                    if 'Required_verb' not in details.keys() or details['Required_verb'] == item.ortho:
                        if item.conjugation_root != '':
                            candidates = [v_str + item.conjugation_root]
                        else:
                            candidates = [v_str + item.txt]
                        for alt in item.alt_forms:
                            if alt != '':
                                candidate = v_str + alt
                                if candidate not in candidates:
                                    candidates.append(candidate)
                        for candidate in candidates:
                            if candidate in conj_str:
                                found = True
                                v_str = candidate
                            elif next_type is not None and candidate in conj_next_type_str:
                                found = True
                                v_str = candidate
                        i += 1
                        
                        if not found:
                            LOG(1,print_prefix + "items %d:%s no match for %s/%s (%s)" % (pos,str(candidates),conj_str,conj_next_type_str,tense))
                else:
                    LOG(2,print_prefix + "item %d:%s not allowed for conjugation" % (pos+i,item.txt))


                if found:
                    if next_type is not None:
                        if v_str == conj_next_type_str:
                            LOG(2,print_prefix + "Conjugate %s with %s (%s) %s " % (v_str,tense,next_type_suffix,get_jmdict_pos_code(next_type)))
                            sub_conj_item_count, sub_conjs = attempt_conjugation(pos+i,items,'',next_type, rec_level+1)
                            if i + sub_conj_item_count > max_sub_conj_item_count:
                                max_sub_conj_item_count = i + sub_conj_item_count
                                max_subj_conj_list = conj_root + [(next_type,next_type_suffix,tense)] + sub_conjs
                                LOG(2,print_prefix + "match " + str(max_subj_conj_list))
                                #print(max_subj_conj_list)
                    if v_str == conj_str:
                        if i > max_sub_conj_item_count:
                            max_sub_conj_item_count = i
                            max_subj_conj_list = conj_root + [('',suffix,tense)]
                            LOG(2,print_prefix + "match " + str(max_subj_conj_list))
                            #print(max_subj_conj_list)
                else:
                    cont = False
                    #LOG(1,"Verb conjugations not found for %s/%s (%s not in %s or %s)" % (items[pos].txt, items[pos].ortho,str(candidates),conj_str,conj_next_type_str),items)
    return max_sub_conj_item_count, max_subj_conj_list


def check_adjectives(pos,items):
    if pos == len(items) - 1:
        return
    ortho = items[pos].ortho
    ending = ''
    if ortho[-1] == 'い':  # i-adjective
        cl = jmdict_adj_i_class
        stem = ortho[:-1]
        LOG(1,"Conjugate i-adj %s/%s" % (ortho,stem))
    else:  # na-adjective
        cl = jmdict_adjectival_noun_class
        stem = ortho
        LOG(1,"Conjugate na-adj %s" % (ortho))
    #ending = next(iter(conjugations_dict[cl]))
    #(conj, conj_details) = conjugations_dict[cl][ending]
    detected_conj_particles, detected_conj_details = attempt_conjugation(pos, items, stem, cl)
    if len(detected_conj_details)>0:
        detected_conj_particles -= 1
        for i in range(detected_conj_particles):
            items[pos+i+1].flags = MERGE_ITEM
        items[pos].conj_details = detected_conj_details
    return


def attempt_maximal_conjugation(pos, items, seqs):
    ortho = items[pos].ortho
    lemma = items[pos].lemma

    stem_candidates = []
    if ortho != '':
        stem_candidates.append(ortho)
    if lemma != '':
        if lemma not in stem_candidates:
            stem_candidates.append(lemma)
    #if items[pos].pron_base != '':
    #    stem_candidates.append(items[pos].pron_base)
    for alt_form in items[pos].alt_forms:
        if alt_form != '':
            if alt_form not in stem_candidates:
                stem_candidates.append(alt_form)

    cl_set = set()
    for seq in seqs:
        cl_list = get_flat_class_list_by_seq(seq)
        cl_set.update(cl_list)

    max_particles_found = 0
    max_conj_details = []
    for cl in cl_set:
            #try:
            cl_txt = jmdict_class_list[cl]
            if cl in verb_conjugations:
                #ending, conj, conj_details = verb_conjugations[cl]
                #ending, conj, conj_details = conjugations_dict[cl]
                for ending, (conj, conj_details) in conjugations_dict[cl].items():

                    for stem_candidate in stem_candidates:
                        stem = stem_candidate[:-len(ending)]
                        removed_ending = stem_candidate[-len(ending):]
                        detected_num = 0
                        if ending == removed_ending:
                            detected_num, detected_conj_details = attempt_conjugation(pos, items, stem, cl)
                            detected_num -= 1
                            if len(detected_conj_details)>0:
                                if detected_num > max_particles_found:
                                    max_particles_found = detected_num
                                    max_conj_details = detected_conj_details
                                elif len(max_conj_details)==0:
                                    # no additional particles detected but 
                                    # the Unidic managed to parse it already
                                    # in the correct inflection
                                    max_conj_details = detected_conj_details

            #except:
            #pass
    return max_particles_found, max_conj_details

def check_verbs(pos,items): 
    if items[pos].conjugated:
        # do not re-conjugate even if reprocessing
        return
    ortho = items[pos].ortho
    if ortho == '':
        return
    lemma = items[pos].lemma
    # First try to get the JMDict entry in order to find the right verb conjugation (v5r etc)
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

    max_particles_conjugated, conj_details = attempt_maximal_conjugation(pos, items, seqs)
    if len(conj_details)>0:
        for i in range(max_particles_conjugated):
            items[pos+i+1].flags = MERGE_ITEM
            items[pos+i+1].conjugated = True
        items[pos].conjugated = True
        items[pos].conj_details = conj_details
        # clear the -masu flag that was in the stem
        if max_particles_conjugated > 0:
            items[pos].is_masu = False
        if items[pos+max_particles_conjugated].ortho == 'ない' or \
                items[pos+max_particles_conjugated].txt[-2:] == 'ない':
            # verbs ending in ない also act as i-adjective
            items[pos].classes.append(adjective_class)
            #items[pos].flags |= REPROCESS
    else:
        LOG(1,"No verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)

    if pos + 1 == len(items):
        # nothing further to check
        return

    # after conjugating (attempt), still try to find some colloquial forms
    pos += max_particles_conjugated
    if pos == len(items) -1:
        return
    
    if aux_verb_class in items[pos+1].classes:
        LOG(1,"Remaining aux verb %s/%s found after conjugation. Adding verb status.." % (items[pos+1].txt, items[pos+1].ortho),items)
        items[pos+1].classes.append(verb_class)

    """
    processed_str = ''.join([items[j].txt for j in range(pos+1)])
    if aux_verb_class in items[pos+1].classes or gp_class in items[pos+1].classes \
            or suffix_class in items[pos+1].classes:
        oku_verbs = ['取る']
        # fuse the different (non)colloquial いる forms into main word
        iru_forms = ['いる','いた','た','ってる','てる']
        nai_forms = ['ねー','へん']
        if items[pos+1].txt in iru_forms: 
            items[pos+1].flags = MERGE_PARTICLE
            items[pos].is_masu = False
        elif items[pos+1].txt in nai_forms:
            allowed = False
            if items[pos].is_masu:
                allowed = True

            #### -1 correct ???
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
        elif items[pos+1].txt == "ってく": 
            # divide the colloquial form to separate particles
            items[pos+1].flags = DIVIDE_PARTICLE
            if items[pos].lemma in oku_verbs:
                # e.g. とっ + てく -> とっ + て + おく
                ku_verb = 'おく'
            else:
                # e.g. 寄っ + てく -> 寄っ + て + いく
                ku_verb = 'いく'
            items[pos+1].divided_particles = [
                LexicalItem('って','',[aux_verb_class]),
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
        elif items[pos+1].txt == "てき": 
            # divide the colloquial form to separate particles
            items[pos+1].flags = DIVIDE_PARTICLE
            # e.g. 探し + てき + なさい -> 探し + て + き + なさい
            ku_verb = 'くる'
            items[pos+1].divided_particles = [
                LexicalItem('て','て',[aux_verb_class]),
                LexicalItem('き',ku_verb,[verb_class],alt_forms=[ku_verb],conjugation_root=ku_verb),
            ]
            items[pos].flags |= REPROCESS
        else:
            if max_particles_conjugated == 0:
                LOG(1,"No exceptional verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
                items[pos].flags |= ERROR_VERB_CONJUGATION
    else:
        if conj_details is None:
            LOG(1,"No verb conjugations found for %s/%s" % (items[pos].txt, items[pos].ortho),items)
            items[pos].flags |= ERROR_VERB_CONJUGATION
        """


"""
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
                    if rec_level < 2 or 'stem' in nt or 'adj-i' in nt:
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
"""
    
def load_conjugations():
    global adj_conjugations, verb_conjugations
    
    o_f = open("lang/Conjugations.txt","r",encoding="utf-8")
    data = o_f.read()
    entries = json.loads(data)
    o_f.close()

    entries_dict = dict()
    for entry in entries:
        n = entry['Name']
        if n not in jmdict_parts_of_speech_codes.keys():
            print("Conjugation %s not in jmdict class codes. Adding" % n)
            jmdict_add_pos(n,n)
            #jmdict_parts_of_speech_codes[n] = n
            #jmdict_class_list.append(n)
        cl_name = jmdict_parts_of_speech_codes[n]
        cli = jmdict_class_list.index(cl_name)
        entries_dict[cli] = entry

    for entry in entries:
        n = entry['Name']
        if n in jmdict_parts_of_speech_codes.keys():
            cl_name = jmdict_parts_of_speech_codes[n]
            cli = jmdict_class_list.index(cl_name)
        else:
            cli = n

        """

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
        """

        # another way
        ending = entry['Tenses'][0]['Suffix']
        tense_details = dict()
        for tense_entry in entry['Tenses']:
            suffix = tense_entry['Suffix']
            tense = tense_entry['Tense']
            #details = [tense_entry['Formal'],tense_entry['Negative']]
            details = [tense_entry['Formal'],tense_entry['Negative']]
            next_type = None
            next_type_suffix = ''
            next_type_code = ''
            if 'Next Type' in tense_entry:
                next_type_code = tense_entry['Next Type']
                if next_type_code in jmdict_parts_of_speech_codes:
                    next_type_cl_name = jmdict_parts_of_speech_codes[next_type_code]
                    next_type = jmdict_class_list.index(next_type_cl_name)
                else:
                    next_type = next_type_code
                next_type_entry = entries_dict[next_type]
                next_type_ending = next_type_entry['Tenses'][0]['Suffix']
                if next_type_ending != '':
                    next_type_suffix = suffix[:-len(next_type_ending)]
                    suffix_removed_ending = suffix[-len(next_type_ending):]
                else:
                    next_type_suffix = suffix
            tense_details[(tense,suffix,next_type,next_type_suffix,next_type_code)] = tense_entry
        tense_length_dict = {(tense,suffix,next_type,next_type_suffix,next_type_code):len(suffix) for (tense,suffix,next_type,next_type_suffix,next_type_code) in tense_details}
        sorted_tenses = dict(sorted(tense_length_dict.items(), key=lambda x:x[1], reverse=True))
        sorted_tenses = list(sorted_tenses)
        if cli not in conjugations_dict.keys():
            conjugations_dict[cli] = dict()
        conjugations_dict[cli][ending] = (list(sorted_tenses), tense_details)

        if 'adj' in n:
            adj_conjugations.append(cli)
        else:
            verb_conjugations.append(cli)

