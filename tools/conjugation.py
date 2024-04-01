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


def attempt_conjugation(pos, items, inflection, conj_class, rec_level=0):
    #conj_ending, conjugations, details = conjugations_dict[conj_class]
    if rec_level > 6:
        return 0, []

    print_prefix = ''.ljust(4+rec_level*4)

    items_l = len(items)
    max_sub_conj_item_count = -1
    max_subj_conj_list = []

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
            elif suffix[-2:] == 'そう':
                next_type = jmdict_class_list.index('copula')
                next_type_suffix = suffix

            """
            if next_type is not None and next_type_suffix == '':
                # special case: jump right to next conjugation class because the required 
                # suffix is empty
                LOG(2,print_prefix + "Conjugate by default %s " % get_jmdict_pos_code(next_type))
                sub_conj_item_count, sub_conjs = attempt_conjugation(pos,items,'',next_type, rec_level+1)
                if sub_conj_item_count > max_sub_conj_item_count:
                    max_sub_conj_item_count = sub_conj_item_count
                    max_subj_conj_list = [(next_type,next_type_suffix,tense)] + sub_conjs
                    LOG(2,print_prefix + "match " + str(max_subj_conj_list))
                    #print(max_subj_conj_list)
            """

            if suffix == 'くなかった':
                pass
            i = 0
            v_str = inflection
            cont = True
            attempted_next_types = set()
            while pos+i<=items_l and cont:

                if next_type is not None and next_type not in attempted_next_types:
                    if next_type_suffix in v_str and v_str.index(next_type_suffix)==0:
                        if v_str == next_type_suffix:
                            next_inflection = ''
                        else:
                            next_inflection = v_str[len(next_type_suffix):]
                        LOG(2,print_prefix + "Conjugate %s with %s (%s) %s " % (v_str,tense,next_type_suffix,get_jmdict_pos_code(next_type)))
                        attempted_next_types.add(next_type)
                        sub_conj_item_count, sub_conjs = attempt_conjugation(pos+i,items,next_inflection,next_type, rec_level+1)
                        if i + sub_conj_item_count > max_sub_conj_item_count:
                            max_sub_conj_item_count = i + sub_conj_item_count
                            max_subj_conj_list = [(next_type,next_type_suffix,tense)] + sub_conjs
                            LOG(1,print_prefix + "match " + str(max_subj_conj_list))
                            #print(max_subj_conj_list)
                if v_str == suffix:
                    if i > max_sub_conj_item_count:
                        max_sub_conj_item_count = i
                        max_subj_conj_list = [('',suffix,tense)]
                        LOG(1,print_prefix + "match " + str(max_subj_conj_list))
                        #print(max_subj_conj_list)

                found = False
                if pos+i < items_l:
                    item = items[pos+i]
                    if is_item_allowed_for_conjugation(item):

                        if 'Required_verb' not in details or details['Required_verb'] == item.ortho:
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
                                if candidate in suffix and suffix.index(candidate)==0:
                                    # there is full match or we can continue building up the suffix
                                    LOG(3,print_prefix + "item %d:%s matches %s (%s)" % (pos,candidate,suffix,tense))
                                    v_str = candidate
                                    found = True
                                elif next_type is not None:

                                    # TODO: is suffix here ot nexT_type_suffix ??
                                    if candidate in next_type_suffix and suffix.index(candidate)==0:
                                        LOG(3,print_prefix + "item %d:%s matches next type suffix %s (%s)" % (pos,candidate,next_type_suffix,tense))
                                        v_str = candidate
                                        found = True
                                    elif next_type_suffix == '':
                                        LOG(3,print_prefix + "item %d:%s matches empty next type suffix (%s)" % (pos,candidate,tense))
                                        v_str = candidate
                                        found = True
                                    elif next_type_suffix in candidate and candidate.index(next_type_suffix)==0:
                                        # there is a full match for the next type suffix OR
                                        # it was too long, but we push the surplus to the next recursion
                                        LOG(3,print_prefix + "item %d:%s overly matches next type suffix %s (%s)" % (pos,candidate,next_type_suffix,tense))
                                        v_str = candidate
                                        found = True
                            i += 1

                            if not found:
                                LOG(2,print_prefix + "items %d:%s no match for %s/%s (%s)" % (pos,str(candidates),suffix,next_type_suffix,tense))
                    else:
                        LOG(2,print_prefix + "item %d:%s not allowed for conjugation" % (pos+i,item.txt))
                        pass

                if not found or ((next_type is None or next_type in attempted_next_types) and len(v_str)>len(suffix)):
                    cont = False
                    #LOG(1,"Verb conjugations not found for %s/%s (%s not in %s or %s)" % (items[pos].txt, items[pos].ortho,str(candidates),conj_str,conj_next_type_str),items)
    return max_sub_conj_item_count, max_subj_conj_list

def check_adjectives(pos,items):
    
    if pos == len(items) - 1:
        return
    # TODO: alts
    ortho = items[pos].ortho
    if ortho == '':
        return
    if ortho[-1] == 'い':  # i-adjective
        cl = jmdict_adj_i_class
        stem = ortho[:-1]
        inflection = items[pos].txt[len(stem):]
        LOG(1,"Conjugate i-adj %s/%s" % (ortho,stem))
    else:  # na-adjective
        cl = jmdict_adjectival_noun_class
        stem = ortho
        inflection = ''
        LOG(1,"Conjugate na-adj %s" % (ortho))
    #ending = next(iter(conjugations_dict[cl]))
    #(conj, conj_details) = conjugations_dict[cl][ending]
    detected_conj_particles, detected_conj_details = attempt_conjugation(pos+1, items, inflection, cl)
    if len(detected_conj_details)>0:
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
            
    inflection_candidates = [items[pos].txt]
    for alt_form in items[pos].alt_forms:
        if alt_form != '':
            if alt_form not in inflection_candidates:
                inflection_candidates.append(alt_form)

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
                        removed_stem_ending = stem_candidate[-len(ending):]
                        detected_num = 0
                        if ending == removed_stem_ending:
                            for inflection_candidate in inflection_candidates:
                                if stem != '' and stem in inflection_candidate:
                                    inflection = inflection_candidate[len(stem):]
                                else:
                                    inflection = inflection_candidate

                                LOG(1,"Conjugate %s %d:%s + %s" % (get_jmdict_pos_code(cl),pos,stem,inflection))
                                conj_root = [(cl,stem,'Root')]
                                detected_num, detected_conj_details = attempt_conjugation(pos+1, items, inflection, cl)
                                #detected_num -= 1
                                if len(detected_conj_details)>0:
                                    if detected_num > max_particles_found:
                                        max_particles_found = detected_num
                                        max_conj_details = conj_root + detected_conj_details
                                    elif len(max_conj_details)==0:
                                        # no additional particles detected but 
                                        # the Unidic managed to parse it already
                                        # in the correct inflection
                                        max_conj_details = conj_root + detected_conj_details

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
    if len(seqs) == 0 and lemma != '':
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

