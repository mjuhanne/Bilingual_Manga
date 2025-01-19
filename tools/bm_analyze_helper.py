
from helper import *
from bm_learning_engine_helper import *
from motoko_mongo import *
from jmdict import *

# Up/downgrade the word frequency by chapter(volume) comprehension/effort
# i.e. if we have just skimmed through a volume without much effort (comprehension level 1-2), 
# we want to decrease virtually the number of times we have seen each word. 
# On the contrary, if we know all the words in the volume (comprehension level 5), 
# all the words will be set as known (at known threshold)
comprehension_modifier = [0, 0.1, 0.5, 1, 2]

CI_ALL_WORDS_KNOWN = 0
CI_UNKNOWN_IS_F5K_WORD = 1
CI_UNKNOWN_IS_F10K_WORD = 2
CI_UNKNOWN_IS_F20K_WORD = 3
CI_UNKNOWN_IS_F50K_WORD = 4
CI_UNKNOWN_IS_KATAKANA_WORD = 5
CI_UNKNOWN_IS_LOW_FREQ_WORD = 6
CI_MORE_THAN_1_UNKNOWN_WORD = 7


user_settings = read_user_settings()
learning_settings = get_learning_settings()

jlpt_word_levels = get_jlpt_word_levels()
jlpt_word_reading_levels= get_jlpt_word_reading_levels()
jlpt_kanjis = get_jlpt_kanjis()

chapter_comprehension = user_settings['chapter_reading_status']
learning_settings['learned_jlpt_timestamp'] /= 1000
learning_settings['learned_custom_timestamp'] /= 1000

learning_data = database[COLLECTION_USER_LEARNING_DATA].find_one({'user_id':DEFAULT_USER_ID})

wordlist_cursor = database[COLLECTION_USER_WORD_LEARNING_STATUS].find({'user_id':DEFAULT_USER_ID},{'_id':False,'user_id':False})
learning_data['words'] = {item['wid']:{'s':item['s'],'lf':item['lf']} for item in wordlist_cursor}

kanjilist_cursor = database[COLLECTION_USER_KANJI_LEARNING_STATUS].find({'user_id':DEFAULT_USER_ID},{'_id':False,'ltf':False,'user_id':False})
learning_data['kanjis'] = {item['kanji']:{'s':item['s'],'lf':item['lf']} for item in kanjilist_cursor}


# Read a data set of words/kanjis (a title or a chapter) and gather statistics 
# (number of unique word or kanjis per learning stage. Statistics are gathered pre- and post-read)
# item_type = 'words' or 'kanjis'
# unique: True (gather statistics for only unique words/kanjis). False (calculate total number of occurrences)
def read_dataset(data_set, item_type, learning_dataset, retain_changes=False, 
    save_changes_for_these_stages=[], save_items_for_these_stages=[]):

    known_dataset = learning_dataset[item_type]

    if item_type == 'words':
        title_data_list =  zip(data_set['word_id_list'], data_set['word_frequency'])
        known_threshold = learning_settings['known_word_threshold']
    else:
        title_data_list = data_set['kanji_frequency'].items()
        known_threshold = learning_settings['known_kanji_threshold']

    # these counters contain occurrences per learning stage
    total_counter = dict()
    unique_counter = dict()
    total_post_read_counter = dict()
    unique_post_read_counter = dict()

    for stage,label in learning_stage_labels.items():
        total_counter[stage] = 0
        unique_counter[stage] = 0
        total_post_read_counter[stage] = 0
        unique_post_read_counter[stage] = 0

    saved_changes = dict()
    for stage in save_changes_for_these_stages:
        saved_changes[stage] = []
    saved_items = dict()
    for stage in save_items_for_these_stages:
        saved_items[stage] = []

    num_all_total = 0
    num_all_unique = 0
    for i, (wid, freq) in enumerate(title_data_list):

        if item_type == 'words':
            if learning_settings['omit_particles'] and wid in particles:
                continue

        if wid in known_dataset:
            l_freq = known_dataset[wid]['lf'] # learning phase occurrence
            l_stage = known_dataset[wid]['s']
        else:
            l_freq = 0
            l_stage = STAGE_UNKNOWN
        old_stage = l_stage

        num_all_unique += 1
        num_all_total += freq

        # counters pre-read
        total_counter[l_stage] += freq
        unique_counter[l_stage] += 1

        if l_stage != STAGE_KNOWN:
            # this is a word/kanji not (fully) known after started reading..
            if learning_settings['automatic_learning_enabled']:
                l_freq = l_freq + freq
                l_stage = get_stage_by_frequency_and_class(item_type, l_freq, False)
                if l_stage < old_stage:
                    # don't downgrade stage just by frequency
                    l_stage = old_stage
                if l_stage == STAGE_KNOWN:
                    # we learned this word/kanji during reading and so rest
                    # of the occurrences are considered to be 'known'
                    total_counter[l_stage] += known_threshold
                    freq = l_freq - known_threshold

        # counters post-read
        total_post_read_counter[l_stage] += freq
        unique_post_read_counter[l_stage] += 1

        if retain_changes:
            if wid not in known_dataset:
                known_dataset[wid] = {}
            known_dataset[wid]['s'] = l_stage
            known_dataset[wid]['lf'] = l_freq 

        if old_stage in save_items_for_these_stages:
            saved_items[old_stage].append(wid)

        if old_stage != l_stage:
            if l_stage in save_changes_for_these_stages:
                saved_changes[l_stage].append(wid)

    analysis = dict()
    for analysis_type in ['total_statistics','unique_statistics']:
        if analysis_type == 'unique_statistics':
            counter = unique_counter
            post_read_counter = unique_post_read_counter
            num_all = num_all_unique
        else:
            counter = total_counter
            post_read_counter = total_post_read_counter
            num_all = num_all_total

        an = dict()
        an['num_all'] = num_all

        counter[STAGE_KNOWN_OR_PRE_KNOWN] = counter[STAGE_KNOWN] + counter[STAGE_PRE_KNOWN]
        post_read_counter[STAGE_KNOWN_OR_PRE_KNOWN] = post_read_counter[STAGE_KNOWN] + post_read_counter[STAGE_PRE_KNOWN]
        counter[STAGE_UNKNOWN_OR_UNFAMILIAR] = counter[STAGE_UNKNOWN] + counter[STAGE_UNFAMILIAR]
        post_read_counter[STAGE_UNKNOWN_OR_UNFAMILIAR] = post_read_counter[STAGE_UNKNOWN] + post_read_counter[STAGE_UNFAMILIAR]

        an['num_per_stage'] = dict()
        an['num_post_read_per_stage'] = dict()
        an['pct_per_stage'] = dict()
        an['pct_post_read_per_stage'] = dict()

        # save the occurrences and percentages per learning stage
        for stage,label in learning_stage_labels.items():
            an['num_' + label] = counter[stage]
            an['num_' + label + '_post_read'] = post_read_counter[stage]
            an['num_per_stage'][stage] = counter[stage]
            an['num_post_read_per_stage'][stage] = post_read_counter[stage]
            if num_all > 0:
                an['pct_' + label] = round(100 * counter[stage] / num_all,2)
                an['pct_' + label + '_post_read'] = round(100 * post_read_counter[stage] / num_all,2)
                an['pct_per_stage'][stage] = an['pct_' + label]
                an['pct_post_read_per_stage'][stage] = an['pct_' + label + '_post_read']
            else:
                an['pct_' + label] = -1
                an['pct_' + label+ '_post_read'] = -1
                an['pct_per_stage'][stage] = -1
                an['pct_post_read_per_stage'][stage] = -1
        analysis[analysis_type] = an

    analysis['saved_items'] = saved_items
    analysis['saved_changes'] = saved_changes

    return analysis

# Calculate number and percentage of i+0/i+1/i+.. sentences (i.e. how many
# sentences have 0,1 or more not-known words. In this case PRE_KNOWN words 
# are considered as KNOWN_WORDS)
# Also collect showstopper words (unknown words that prevent a sentence to be 'comprehensible input' i.e. have maximum of 1 unknown words)
def read_sentences(data_set, learning_dataset, results, save_showstopper_words=False):

    known_dataset = learning_dataset["words"]

    unknown_i_sentences = [0] * 3
    unknown_i_sentences_ex_katakana = [0] * 3
    ci_sentence_count = [0] * 8
    unknown_word_occurrences = dict()
    ci_score = 0

    showstopper_word_count = dict()

    for i,sentence in enumerate(data_set['sentence_list']):

        unknown_wids = set()
        unknown_ex_katakana_wids = set()
        for ref in sentence:
            wid = data_set['word_id_list'][ref]

            if learning_settings['omit_particles'] and wid in particles:
                continue

            if wid in known_dataset:
                l_freq = known_dataset[wid]['lf'] # learning phase occurrence
                l_stage = known_dataset[wid]['s']
            else:
                l_freq = 0
                l_stage = STAGE_UNKNOWN
            old_stage = l_stage

            if l_stage == STAGE_FORGOTTEN and wid in unknown_word_occurrences:
                # assume we know the word again after 1 lookup
                l_stage = STAGE_KNOWN
            else:
                if l_stage != STAGE_KNOWN and l_stage != STAGE_PRE_KNOWN:
                    # this is a word not (fully) known after started reading..

                    if wid not in unknown_word_occurrences:
                        unknown_word_occurrences[wid] = 1
                    else:
                        unknown_word_occurrences[wid] += 1

                    if learning_settings['automatic_learning_enabled']:
                        l_freq = l_freq + unknown_word_occurrences[wid]
                        l_stage = get_stage_by_frequency_and_class('words', l_freq, False)
                        if l_stage < old_stage:
                            # don't downgrade stage just by frequency
                            l_stage = old_stage

                    if l_stage != STAGE_KNOWN and l_stage != STAGE_PRE_KNOWN:
                        unknown_wids.update([wid])
                        #unknown_count += 1

                        seq, word = get_seq_and_word_from_word_id(wid)
                        j_freq = get_frequency_by_seq_and_word(seq,word)

                        if not is_katakana_word(word):
                            #unknown_count_ex_katakana += 1
                            unknown_ex_katakana_wids.update([wid])

        unknown_count = len(unknown_wids)
        unknown_count_ex_katakana = len(unknown_ex_katakana_wids)

        if save_showstopper_words:
            if unknown_count == 2:
                for unk_wid in unknown_wids:
                    if unk_wid not in showstopper_word_count:
                        showstopper_word_count[unk_wid] = 1
                    else:
                        showstopper_word_count[unk_wid] += 1

        if unknown_count > 2:
            unknown_count = 2
        if unknown_count_ex_katakana > 2:
            unknown_count_ex_katakana = 2

        if unknown_count == 0:
            ci_sentence_count[CI_ALL_WORDS_KNOWN] += 1
            ci_score += 30
        elif unknown_count == 1:
            if j_freq < 10: # first 5000 words
                ci_sentence_count[CI_UNKNOWN_IS_F5K_WORD] += 1
                ci_score += 100
            elif j_freq < 20: # first 10000 words
                ci_sentence_count[CI_UNKNOWN_IS_F10K_WORD] += 1
                ci_score += 50
            elif j_freq < 40: # first 20000 words
                ci_sentence_count[CI_UNKNOWN_IS_F20K_WORD] += 1
                ci_score += 20
            elif j_freq < 99: # first 50000 words
                ci_sentence_count[CI_UNKNOWN_IS_F50K_WORD] += 1
                ci_score += 10
            elif unknown_count_ex_katakana == 0:
                ci_sentence_count[CI_UNKNOWN_IS_KATAKANA_WORD] += 1
                ci_score += 20
            else:
                ci_sentence_count[CI_UNKNOWN_IS_LOW_FREQ_WORD] += 1
            if l_stage == STAGE_LEARNING or l_stage == STAGE_FORGOTTEN:
                ci_score += 20
        else: 
            ci_sentence_count[CI_MORE_THAN_1_UNKNOWN_WORD] += 1
            if unknown_count_ex_katakana == 1:
                # less penalty for those sentences with only 1 unknown non-katakana word
                ci_score -= 10
            else:
                ci_score -= 50

        unknown_i_sentences[unknown_count] += 1
        unknown_i_sentences_ex_katakana[unknown_count_ex_katakana] += 1

    l_s = len(data_set['sentence_list'])
    results['unknown_i_sentences'] = unknown_i_sentences
    results['unknown_i_sentences_ex_katakana'] = unknown_i_sentences_ex_katakana
    if l_s > 0:
        results['unknown_i_sentences_pct'] = [round(100*unk/l_s,1) for unk in unknown_i_sentences ]
        results['unknown_i_sentences_ex_katakana_pct'] = [round(100*unk/l_s,1) for unk in unknown_i_sentences_ex_katakana ]
        results['comprehensible_input_score'] = round(ci_score/l_s,1)
        results['comprehensible_input_sentence_grading'] = [round(100*cic/l_s,1) for cic in ci_sentence_count ]
    else:
        results['unknown_i_sentences_pct'] = unknown_i_sentences
        results['unknown_i_sentences_ex_katakana_pct'] = unknown_i_sentences_ex_katakana
        results['comprehensible_input_score'] = -1
        results['comprehensible_input_sentence_grading'] = [-1 for cic in ci_sentence_count ]
    results['comprehensible_input_pct'] = round(results['unknown_i_sentences_pct'][0] + results['unknown_i_sentences_pct'][1],1)
    results['comprehensible_input_ex_katakana_pct'] = round(results['unknown_i_sentences_ex_katakana_pct'][0] + results['unknown_i_sentences_ex_katakana_pct'][1],1)

    if save_showstopper_words:

        sorted_showstopper_word_count = dict(sorted(showstopper_word_count.items(), key=lambda x:x[1], reverse=True))
        sorted_showstopper_words = list(sorted_showstopper_word_count.keys())
        # limit saved word count to top 50 words
        if len(sorted_showstopper_words) > 50:
            capped_words = sorted_showstopper_words[:50]
            capped_sorted_showstopper_word_count = {key:sorted_showstopper_word_count[key] for key in capped_words}
            results['showstopper_words'] = capped_sorted_showstopper_word_count
        else:
            results['showstopper_words'] = sorted_showstopper_word_count

        target_ci_pct = 90
        needed_word_count = 0
        if results['comprehensible_input_pct'] < target_ci_pct and l_s > 0:
            ci_sentence_count = unknown_i_sentences[0] + unknown_i_sentences[1]
            while ( 100*ci_sentence_count/l_s < target_ci_pct and needed_word_count<len(sorted_showstopper_words)):
                word = sorted_showstopper_words[needed_word_count]
                ci_sentence_count += sorted_showstopper_word_count[word]
                needed_word_count += 1
        results['showstopper_word_count_for_ci90'] = needed_word_count



# This calculates known/unknown word and kanji distribution of chapter/title
# for each JLPT level (1-5). 
# Additional categories: 0 = non-Katakana non-JLPT word, 6=Katakana non-JLPT word
def fetch_known_jlpt_levels(data, calc, total):

    ## WORDS
    jlpt_word_count_per_level = [ 0 for i in range(7) ]
    total_w = 0
    for wid,freq in zip(data['word_id_list'], data['word_frequency']):
        if wid in learning_data['words']:
            s = learning_data['words'][wid]['s']
            seq,w = get_seq_and_word_from_word_id(wid)
            if s == STAGE_KNOWN or s == STAGE_PRE_KNOWN:
                if w in jlpt_word_levels:
                    level = jlpt_word_levels[w]
                else:
                    if w in jlpt_word_reading_levels:
                        level = jlpt_word_reading_levels[w]
                    else:
                        # non-jlpt word
                        if is_katakana_word(w):
                            level = 6
                        else:
                            level = 0
                if total:
                    jlpt_word_count_per_level[level] += freq
                else:
                    jlpt_word_count_per_level[level] += 1

        if total:
            total_w += freq
        else:
            total_w += 1

    if total_w > 0:
        jlpt_w_level_pct = [ round(100*jlpt_word_count_per_level[i]/total_w,1) for i in range(7) ]
        jlpt_w_level_per_v = [ round(jlpt_word_count_per_level[i]/data['num_virtual_volumes'],1) for i in range(7) ]
    else:
        jlpt_w_level_pct = [ 0 for i in range(7) ]
        jlpt_w_level_per_v = [ 0 for i in range(7) ]

    calc['words']['jlpt_level_pct'] = jlpt_w_level_pct
    calc['words']['jlpt_level_per_v'] = jlpt_w_level_per_v

    ### KANJIS
    jlpt_known_kanji_count_per_level = [ 0 for i in range(6) ]
    jlpt_unknown_kanji_count_per_level = [ 0 for i in range(6) ]
    unknown_jlpt_kanji_set = set()
    unknown_non_jlpt_kanji_set = set()
    for k,c in data['kanji_frequency'].items():
        if k in jlpt_kanjis:
            level = jlpt_kanjis[k]
        else:
            level = 0
        known = False
        if k in learning_data['kanjis']:
            s = learning_data['kanjis'][k]['s']
            if s == STAGE_KNOWN or s == STAGE_PRE_KNOWN:
                known = True
        if known:
            if total:
                jlpt_known_kanji_count_per_level[level] += c
            else:
                jlpt_known_kanji_count_per_level[level] += 1
        else:
            if total:
                jlpt_unknown_kanji_count_per_level[level] += c
            else:
                jlpt_unknown_kanji_count_per_level[level] += 1
                if level == 0:
                    unknown_non_jlpt_kanji_set.update([k])
                else:
                    unknown_jlpt_kanji_set.update([k])


    total_k = calc['kanjis']['num_all']
    if total_k > 0:
        jlpt_k_level_pct = [ round(100*jlpt_known_kanji_count_per_level[i]/total_k,1) for i in range(6) ]
        jlpt_k_level_per_v = [ round(jlpt_known_kanji_count_per_level[i]/data['num_virtual_volumes'],1) for i in range(6) ]
    else:
        jlpt_k_level_pct = [ 0 for i in range(6) ]
        jlpt_k_level_per_v = [ 0 for i in range(6) ]
    calc['kanjis']['jlpt_level_pct'] = jlpt_k_level_pct
    calc['kanjis']['jlpt_level_per_v'] = jlpt_k_level_per_v
    calc['kanjis']['jlpt_num'] = sum([ jlpt_known_kanji_count_per_level[i] for i in range(1,6) ])
    calc['kanjis']['jlpt_unknown_num'] = sum([ jlpt_unknown_kanji_count_per_level[i] for i in range(1,6) ])
    calc['kanjis']['non_jlpt_unknown_num'] = jlpt_unknown_kanji_count_per_level[0]
    if not total:
        calc['kanjis']['jlpt_unknown_list'] = list(unknown_jlpt_kanji_set)
        calc['kanjis']['non_jlpt_unknown_list'] = list(unknown_non_jlpt_kanji_set)

def analyze_dataset(data_set):
    analysis = dict()
    analysis['total_statistics'] = dict()
    analysis['unique_statistics'] = dict()
    w_an = read_dataset(data_set, "words", learning_data)
    analysis['total_statistics']['words'] = w_an['total_statistics']
    analysis['unique_statistics']['words'] =  w_an['unique_statistics']
    k_an = read_dataset(data_set, "kanjis", learning_data)
    analysis['total_statistics']['kanjis'] = k_an['total_statistics']
    analysis['unique_statistics']['kanjis'] =  k_an['unique_statistics']

    read_sentences(data_set, learning_data, analysis, save_showstopper_words=True)
    
    analysis['total_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['total_statistics']['words']['pct_known_pre_known'],1)
    analysis['unique_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['unique_statistics']['words']['pct_known_pre_known'],1)
        
    return analysis, data_set



