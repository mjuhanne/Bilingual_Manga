import os
import json
import copy
import argparse
import time
import sys

from helper import *
from bm_learning_engine_helper import *
from jmdict import *

# Full history is just for debugging because the resulting data set becomes quickly too large.
# Instead we keep history only for those events when the learning stage changes
RETAIN_FULL_WORD_HISTORY = False  

#input files
jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  base_dir + "lang/jlpt/jlpt_vocab.json"
language_reactor_json_file = base_dir + 'lang/user/language-reactor.json'
user_known_words_file = base_dir + 'lang/user/user_known_words.csv'
user_known_kanjis_file = base_dir + 'lang/user/user_known_kanjis.csv'
user_word_occurrence_file = base_dir + 'lang/user/user_word_occurrence.tsv'
user_kanji_occurrence_file = base_dir + 'lang/user/user_kanji_occurrence.tsv'

# output files
learning_data_filename = base_dir + 'lang/user/learning_data.json'
output_analysis_file = base_dir + 'json/custom_lang_analysis.json'
suggested_preread_dir = base_dir + 'lang/suggested_preread/'

# Up/downgrade the word frequency by chapter(volume) comprehension/effort
# i.e. if we have just skimmed through a volume without much effort (comprehension level 1-2), 
# we want to decrease virtually the number of times we have seen each word. 
# On the contrary, if we know all the words in the volume (comprehension level 5), 
# all the words will be set as known (at known threshold)
comprehension_modifier = [0, 0.1, 0.5, 1, 2]

learning_data = dict()

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
            class_list = data_set['word_class_list'][i]
            if learning_settings['omit_particles'] and jmdict_particle_class in class_list:
                continue
        else:
            class_list = None

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
                l_stage = get_stage_by_frequency_and_class(item_type, l_freq, class_list)
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
def read_sentences(data_set, learning_dataset, results):

    known_dataset = learning_dataset["words"]

    unknown_i_sentences = [0] * 3
    unknown_word_occurrences = dict()

    opt_ci_points = 0

    for i,sentence in enumerate(data_set['sentence_list']):

        unknown_count = 0
        unknown_points = 0
        for ref in sentence:
            wid = data_set['word_id_list'][ref]

            class_list = data_set['word_class_list'][ref]
            if learning_settings['omit_particles'] and jmdict_particle_class in class_list:
                continue

            if wid in known_dataset:
                l_freq = known_dataset[wid]['lf'] # learning phase occurrence
                l_stage = known_dataset[wid]['s']
            else:
                l_freq = 0
                l_stage = STAGE_UNKNOWN
            old_stage = l_stage

            if l_stage != STAGE_KNOWN and l_stage != STAGE_PRE_KNOWN:
                # this is a word/kanji not (fully) known after started reading..

                if wid not in unknown_word_occurrences:
                    unknown_word_occurrences[wid] = 1
                else:
                    unknown_word_occurrences[wid] += 1

                if learning_settings['automatic_learning_enabled']:
                    l_freq = l_freq + unknown_word_occurrences[wid]
                    l_stage = get_stage_by_frequency_and_class(item_type, l_freq, class_list)
                    if l_stage < old_stage:
                        # don't downgrade stage just by frequency
                        l_stage = old_stage

                if l_stage != STAGE_KNOWN and l_stage != STAGE_PRE_KNOWN:
                    unknown_count += 1

                    seq, word = get_seq_and_word_from_word_id(wid)
                    j_freq = get_frequency_by_seq_and_word(seq,word)

                    if j_freq < 10: # first 5000 words
                        unknown_points += 100
                    elif j_freq < 20: # first 10000 words
                        unknown_points += 50
                    elif j_freq < 40: # first 20000 words
                        unknown_points += 20
                    elif j_freq < 99: # first 50000 words
                        unknown_points += 10
                    if l_stage == STAGE_LEARNING or l_stage == STAGE_FORGOTTEN:
                        unknown_points += 20

        if unknown_count > 2:
            unknown_count = 2

        if unknown_count == 0:
            opt_ci_points += 30
        elif unknown_count == 1:
            opt_ci_points += unknown_points
        else: 
            opt_ci_points -= 50

        unknown_i_sentences[unknown_count] += 1

    l_s = len(data_set['sentence_list'])
    results['unknown_i_sentences'] = unknown_i_sentences
    results['unknown_i_sentences_pct'] = [round(100*unk/l_s,1) for unk in unknown_i_sentences ]
    results['comprehensible_input_pct'] = round(results['unknown_i_sentences_pct'][0] + results['unknown_i_sentences_pct'][1],1)
    #results['w_comprehensible_input_pct'] = round(results['unknown_i_sentences_pct'][1]*0.5 + results['unknown_i_sentences_pct'][1] - results['unknown_i_sentences_pct'][2],1)
    results['opt_comprehensible_input_pts'] = round(opt_ci_points/l_s,1)

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
    jlpt_kanji_count_per_level = [ 0 for i in range(6) ]
    for k,c in data['kanji_frequency'].items():
        if k in learning_data['kanjis']:
            s = learning_data['kanjis'][k]['s']
            if s == STAGE_KNOWN or s == STAGE_PRE_KNOWN:
                if k in jlpt_kanjis:
                    level = jlpt_kanjis[k]
                else:
                    level = 0
                if total:
                    jlpt_kanji_count_per_level[level] += c
                else:
                    jlpt_kanji_count_per_level[level] += 1

    total_k = calc['kanjis']['num_all']
    if total_k > 0:
        jlpt_k_level_pct = [ round(100*jlpt_kanji_count_per_level[i]/total_k,1) for i in range(6) ]
        jlpt_k_level_per_v = [ round(jlpt_kanji_count_per_level[i]/data['num_virtual_volumes'],1) for i in range(6) ]
    else:
        jlpt_k_level_pct = [ 0 for i in range(6) ]
        jlpt_k_level_per_v = [ 0 for i in range(6) ]
    calc['kanjis']['jlpt_level_pct'] = jlpt_k_level_pct
    calc['kanjis']['jlpt_level_per_v'] = jlpt_k_level_per_v


def load_and_analyze_dataset(file_name):
    o_f = open(file_name,"r",encoding="utf-8")
    data_set = json.loads(o_f.read())
    o_f.close()

    analysis = dict()
    analysis['total_statistics'] = dict()
    analysis['unique_statistics'] = dict()
    w_an = read_dataset(data_set, "words", learning_data)
    analysis['total_statistics']['words'] = w_an['total_statistics']
    analysis['unique_statistics']['words'] =  w_an['unique_statistics']
    k_an = read_dataset(data_set, "kanjis", learning_data)
    analysis['total_statistics']['kanjis'] = k_an['total_statistics']
    analysis['unique_statistics']['kanjis'] =  k_an['unique_statistics']

    read_sentences(data_set, learning_data, analysis)
    
    analysis['total_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['total_statistics']['words']['pct_known_pre_known'],1)
    analysis['unique_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['unique_statistics']['words']['pct_known_pre_known'],1)
    
    return analysis, data_set


# Analyze all titles
def analyze_titles():

    print("Analyzing comprehension for all manga titles")

    analysis = dict()

    for title_id, title_name in get_title_names().items():

        title_filename = title_analysis_dir + title_id + ".json"

        if not os.path.exists(title_filename):
            print("Title %s datafile %s not found!" % (title_name,title_filename))
            continue

        title_analysis, title_data = load_and_analyze_dataset(title_filename)
        
        # Average tankobon volume page count is 180, but it might vary considerable by
        # manga, so to make those statistics more comparable we calculate virtual volume
        # count and use that for those variables that rely on # of volumes.
        title_data['num_virtual_volumes'] = round(title_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

        fetch_known_jlpt_levels(title_data, title_analysis['total_statistics'], total=True)
        fetch_known_jlpt_levels(title_data, title_analysis['unique_statistics'], total=False)

        analysis[title_id] = title_analysis
    
    return analysis

def get_next_unread_chapter(title_id):

    highest_read_chapter = 0
    highest_read_chapter_id = None
    for chapter_id, _ in chapter_comprehension.items():
        tid = get_title_id_by_chapter_id(chapter_id)
        if tid == title_id:
            chapter = get_chapter_number_by_chapter_id(chapter_id)
            if chapter > highest_read_chapter:
                highest_read_chapter = chapter
                highest_read_chapter_id = chapter_id

    title_chapters = get_chapters_by_title_id(title_id)
    if highest_read_chapter == 0:
        highest_read_chapter_id = title_chapters[0]
    else:
        if highest_read_chapter == len(title_chapters):
            # all read
            return None
        highest_read_chapter_id = title_chapters[highest_read_chapter]

    return highest_read_chapter_id


def analyze_next_unread():

    print("Analyzing comprehension for the next unread chapters/volumes")
    analysis = dict()
    next_unread_chapter = dict()

    for title_id, title_name in get_title_names().items():

        chapter_id = get_next_unread_chapter(title_id)
        if chapter_id is None:
            print(" * %s already read" % title_name)
            continue

        chapter = get_chapter_number_by_chapter_id(chapter_id)
        next_unread_chapter[title_id] = chapter

        chapter_filename = chapter_analysis_dir + chapter_id + ".json"

        if not os.path.exists(chapter_filename):
            print("%s chapter %d not found! [%s]" % (title_name, chapter, chapter_filename))
            continue

        chapter_analysis, chapter_data = load_and_analyze_dataset(chapter_filename)

        analysis[title_id] = chapter_analysis

    return analysis


def suggest_preread(args):

    target_title_id = get_title_id(args['title'])
    read_whole_titles = False

    print("Analyzing suggested pre-reading for " + get_title_by_id(target_title_id))

    if read_whole_titles:
        index_title_filename = title_analysis_dir + target_title_id + ".json"
        o_f = open(index_title_filename,"r",encoding="utf-8")
        target_data = json.loads(o_f.read())
        o_f.close()
    else:
        target_chapter_id = get_next_unread_chapter(target_title_id)
        target_chapter = get_chapter_number_by_chapter_id(target_chapter_id)

        index_chapter_filename = chapter_analysis_dir + target_chapter_id + ".json"
        if os.path.exists(index_chapter_filename):
            o_f = open(index_chapter_filename,"r",encoding="utf-8")
            target_data = json.loads(o_f.read())
            o_f.close()


    # first read the target title and save analysis before pre-reading
    target_word_analysis = read_dataset(target_data, "words", learning_data, 
        save_items_for_these_stages=[STAGE_UNFAMILIAR,STAGE_LEARNING, STAGE_FORGOTTEN])
    weak_word_ids = set(target_word_analysis['saved_items'][STAGE_UNFAMILIAR])
    weak_word_ids.update(target_word_analysis['saved_items'][STAGE_LEARNING])
    weak_word_ids.update(target_word_analysis['saved_items'][STAGE_FORGOTTEN])
    target_pct_known = target_word_analysis['total_statistics']['pct_known_pre_known']

    # comprehensible input (CI) = percentage of senteces with 0 or 1 not-known/pre-known words
    read_sentences(target_data, learning_data, target_word_analysis)
    target_pct_ci = target_word_analysis['comprehensible_input_pct']

    analysis = dict()

    for title_id, title_name in get_title_names().items():

        # TODO: optimize
        this_session_learning_data = copy.deepcopy(learning_data)

        if read_whole_titles:
            candidate_filename = title_analysis_dir + title_id + ".json"
            chapter = 'ALL'
        else:
            chapter_id = get_next_unread_chapter(title_id)
            if chapter_id is None:
                print("Skipping %s because already read all chapters" % (title_name))
                continue
            chapter = str(get_chapter_number_by_chapter_id(chapter_id))
            candidate_filename = chapter_analysis_dir + chapter_id + ".json"
        if not os.path.exists(candidate_filename):
            print("Skipping %s because data file %s not found" % (title_name,candidate_filename))
            continue

        o_f = open(candidate_filename,"r",encoding="utf-8")
        candidate_data = json.loads(o_f.read())
        o_f.close()

        num_pages = candidate_data['num_pages']
        num_words = candidate_data['num_words']

        title_analysis = dict()
        title_analysis['chapter'] = chapter

        # first read the candidate, retaining the words learned from this session
        # while analyzing how difficult this candidate series is..
        w_an = read_dataset(candidate_data, "words", this_session_learning_data, retain_changes=True)
        candidate_word_analysis = w_an['total_statistics']
        candidate_pct_known = candidate_word_analysis['pct_known_pre_known']
        if candidate_pct_known < target_pct_known - 2:
            print("Skipping %s with comprehension %.1f" % (title_name,candidate_pct_known))
            continue
        read_sentences(candidate_data, this_session_learning_data, w_an)
        candicate_pct_ci = w_an['comprehensible_input_pct']
        if candicate_pct_ci < target_pct_ci:
            print("Skipping %s with comprehensible input %.1f" % (title_name,candicate_pct_ci))
            continue

        # calculate number of common unique weak (unfamiliar or learning) words
        w_id_set = set(candidate_data['word_id_list'])
        common_unique_weak_words = w_id_set.intersection(weak_word_ids)
        cuww = len(common_unique_weak_words)
        title_analysis['num_common_unique_weak_words'] = cuww
        if num_pages > 0:
            title_analysis['num_common_unique_weak_words_per_vol'] = int(cuww/(num_pages/180))
        else:
            title_analysis['num_common_unique_weak_words_per_vol'] = -1

        # .. then analyze how much reading the candidate improved the comprehension of target manga
        w_an = read_dataset(target_data, "words", this_session_learning_data)
        title_analysis_words = w_an['total_statistics']
        read_sentences(target_data, this_session_learning_data, w_an)
        improvement_ci_pct = w_an['comprehensible_input_pct'] - target_pct_ci

        improvement_pct = title_analysis_words['pct_known_pre_known'] - target_pct_known
        if num_pages > 0:
            # calculate how much the reading comprehension improves in regards to pages and words read
            divider = num_words + num_pages*30
            points = 1000000*improvement_pct / divider
            # and modify the sort value depending on how difficult reading this candidate actually was
            # (2 is easy, 0.5 is hard)
            if candidate_pct_known > 95:
                difficulty_modifier = 2
            elif candidate_pct_known < 80:
                difficulty_modifier = 0.5
            else:
                difficulty_modifier = (candidate_pct_known - 80)/(95-80)*(2-0.5) + 0.5
            points *= difficulty_modifier

            ci_points = 1000000*improvement_ci_pct / divider
            # and modify the sort value depending on how difficult reading this candidate actually was
            # (2 is easy, 0.5 is hard)
            if candicate_pct_ci > 95:
                difficulty_modifier = 2
            elif candicate_pct_ci < 80:
                difficulty_modifier = 0.5
            else:
                difficulty_modifier = (candicate_pct_ci - 80)/(95-80)*(2-0.5) + 0.5
            ci_points *= difficulty_modifier

        else:
            points = -1
            ci_points = -1

        title_analysis['improvement_pct'] = round(improvement_pct,2)
        title_analysis['improvement_ci_pct'] = round(improvement_ci_pct,2)
        title_analysis['relative_improvement'] = round(points,2) # in relation to the effort
        title_analysis['relative_ci_improvement'] = round(ci_points,2) # in relation to the effort
        analysis[title_id] = title_analysis

    o_f = open(suggested_preread_dir + target_title_id + '.json' ,"w",encoding="utf-8")
    timestamp = int(time.time())*1000
    data = {'timestamp':timestamp, 'analysis':analysis, 'read_whole_titles':read_whole_titles}
    json_data = json.dumps(data)
    o_f.write(json_data)
    o_f.close()


def series_analysis_for_jlpt():

    print("Analyzing suggested reading for JLPT")

    analysis = dict()

    count = 0
    for title_id, title_name in get_title_names().items():

        title_filename = title_analysis_dir + title_id + ".json"
        if not os.path.exists(title_filename):
            print("Title %s datafile %s not found!" % (title_name,title_filename))
            continue

        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        # first read the candidate and save the words learned from this session
        # while analyzing how difficult this candidate series is..
        title_analysis = dict()
        w_an = read_dataset(title_data, "words", learning_data, save_changes_for_these_stages=[STAGE_KNOWN, STAGE_PRE_KNOWN, STAGE_LEARNING], save_items_for_these_stages=[STAGE_LEARNING])
        title_analysis['words'] = w_an['total_statistics']
        k_an = read_dataset(title_data, "kanjis", learning_data, save_changes_for_these_stages=[STAGE_KNOWN,STAGE_PRE_KNOWN, STAGE_LEARNING], save_items_for_these_stages=[STAGE_LEARNING])
        title_analysis['kanjis'] = k_an['total_statistics']
        candidate_pct_known = title_analysis['words']['pct_known_pre_known']

        num_pages = title_data['num_pages']
        num_words = title_data['num_words']

        # .. then calculate how many new JLPT words/kanjis we would have learned
        new_known_word_ids = w_an['saved_changes'][STAGE_KNOWN]
        new_known_word_ids += w_an['saved_changes'][STAGE_PRE_KNOWN]
        new_learning_word_ids = w_an['saved_changes'][STAGE_LEARNING]
        new_known_kanjis = k_an['saved_changes'][STAGE_KNOWN]
        new_known_kanjis += k_an['saved_changes'][STAGE_PRE_KNOWN]
        new_learning_kanjis = k_an['saved_changes'][STAGE_LEARNING]

        jlpt_points = 0
        # Give points for every new known/pre-known JLPT word..
        # Prioritize beginner level (from JLPT5 downwards) words by giving 2 points per level
        # E.g. 10 points per every new known JLPT5 leve
        for wid in new_known_word_ids:
            level = 0
            seq, w = get_seq_and_word_from_word_id(wid)
            if w in jlpt_word_levels:
                level = jlpt_word_levels[w]
            else:
                if w in jlpt_word_reading_levels:
                    level = jlpt_word_reading_levels[w]
            jlpt_points += level*2

        # .. and for learning stage JLPT words give half amount of points
        for wid in new_learning_word_ids:
            level = 0
            seq, w = get_seq_and_word_from_word_id(wid)
            if w in jlpt_word_levels:
                level = jlpt_word_levels[w]
            else:
                if w in jlpt_word_reading_levels:
                    level = jlpt_word_reading_levels[w]
            jlpt_points += level

        if num_pages > 0:
            # how many new JLPT words learned in regards to pages and words read
            divider = num_words + num_pages*30
            points = 10000*jlpt_points / divider
            # and modify the value depending on how difficult reading this candidate actually was
            # (2 is easy, 0.5 is hard)
            if candidate_pct_known > 95:
                difficulty_modifier = 2
            elif candidate_pct_known < 80:
                difficulty_modifier = 0.5
            else:
                difficulty_modifier = (candidate_pct_known - 80)/(95-80)*(2-0.5) + 0.5
            points *= difficulty_modifier
        else:
            points = -1

        title_analysis['relative_points'] = round(points,1)
        title_analysis['absolute_points'] = jlpt_points
        title_analysis['num_new_known_words'] = len(new_known_word_ids)
        title_analysis['num_new_known_kanjis'] = len(new_known_kanjis)
        title_analysis['num_new_learning_words'] = len(new_learning_word_ids)
        title_analysis['num_new_learning_kanjis'] = len(new_learning_kanjis)
        analysis[title_id] = title_analysis

    return analysis


def analyze(args):

    d = dict()
    d['series_analysis'] = analyze_titles()
    d['next_unread_chapter_analysis'] =  analyze_next_unread()
    d['series_analysis_for_jlpt'] =  series_analysis_for_jlpt()

    o_f = open(output_analysis_file,"w",encoding="utf-8")
    timestamp = int(time.time())*1000
    data = {'timestamp': timestamp, 'analysis' : d}
    json_data = json.dumps(data)
    o_f.write(json_data)
    o_f.close()


#################### Read input files #################################

needed_paths = [ chapter_analysis_dir, title_analysis_dir, jlpt_kanjis_file, jlpt_vocab_file, user_data_file]
for path in needed_paths:
    if not os.path.exists(path):
        raise Exception("Required path [%s] not found!" % path)

try: 
    with open(learning_data_filename,"r",encoding="utf-8") as f:
        data = f.read()
        learning_data = json.loads(data)

        # the history information for further speculative analysis is unnecessary
        for item_type in ['words','kanjis']:
            for item in learning_data[item_type].keys():
                del learning_data[item_type][item]['h']
                del learning_data[item_type][item]['ltf']

except Exception as e:
    print("Learning data not set! Update!")

read_manga_data()
read_manga_metadata()
load_jmdict()

user_set_words = get_user_set_words()
user_settings = read_user_settings()
learning_settings = get_learning_settings()

jlpt_word_levels = get_jlpt_word_levels()
jlpt_word_reading_levels= get_jlpt_word_reading_levels()
jlpt_kanjis = get_jlpt_kanjis()

chapter_comprehension = user_settings['chapter_reading_status']
initial_remembering_period = learning_settings['initial_remembering_period']*24*60*60
if initial_remembering_period > 0:
    enable_forgetting = True
learning_settings['learned_jlpt_timestamp'] /= 1000
learning_settings['learned_custom_timestamp'] /= 1000

parser = argparse.ArgumentParser(
    prog="bm_analyze",
    description="Bilingual Manga Analyzing Tool",
)

subparsers = parser.add_subparsers(help='', dest='command')
parser_analyze = subparsers.add_parser('analyze', help='Do comprehension analysis per title')

parser_suggest_preread = subparsers.add_parser('suggest_preread', help='Analyze given title and then suggest beneficial pre-read titles which increase comprehension')
parser_suggest_preread.add_argument('title', type=str, help='Target manga title')

args = vars(parser.parse_args())
cmd = args.pop('command')

#analyze({'title'})
#analyze_next_unread()
#suggest_preread({'title':'Detective Conan'})

if cmd is not None:
    try:
        locals()[cmd](args)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(-1)

