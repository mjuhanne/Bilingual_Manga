import os
import json
import copy
import argparse
import time
from mongo import *

from helper import *
from bm_learning_engine_helper import *
from jmdict import *
from br_mongo import *

#input files
jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  base_dir + "lang/jlpt/jlpt_vocab.json"
language_reactor_json_file = base_dir + 'lang/user/language-reactor.json'
user_known_words_file = base_dir + 'lang/user/user_known_words.csv'
user_known_kanjis_file = base_dir + 'lang/user/user_known_kanjis.csv'
user_word_occurrence_file = base_dir + 'lang/user/user_word_occurrence.tsv'
user_kanji_occurrence_file = base_dir + 'lang/user/user_kanji_occurrence.tsv'

# output files
suggested_preread_dir = base_dir + 'lang/suggested_preread/'

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

progress_output = False
learning_data = dict()
summary_data = dict()
ext_summary_data = dict()
old_analysis = dict()

last_progress = 0
def reset_progress():
    global last_progress
    last_progress = 0

def print_progress(i,title_count,msg):
    global last_progress
    p = int(100*i/title_count)
    if p != last_progress:
        print("%s (%d%%)  " % (msg,p), flush=True)
        last_progress = p


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
                        l_stage = get_stage_by_frequency_and_class('words', l_freq, class_list)
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

    read_sentences(data_set, learning_data, analysis, save_showstopper_words=True)
    
    analysis['total_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['total_statistics']['words']['pct_known_pre_known'],1)
    analysis['unique_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['unique_statistics']['words']['pct_known_pre_known'],1)
        
    return analysis, data_set


# Analyze all titles
def analyze_titles(args):

    if not progress_output:
        print("Analyzing comprehension for titles")
    else:
        reset_progress()

    avg_ci_sentence_count = [0] * 7

    analysis = dict()

    title_count = len(get_title_names().keys())
    reset_progress()
    for i, (title_id, title_name) in enumerate(get_title_names().items()):

        if args['title'] is not None and args['title'].lower() not in title_name.lower():
            continue

        if 'series' in old_analysis and title_id in old_analysis['series'] and not args['force']:
            title_analysis = old_analysis['series'][title_id]
        else:
            # recalculate analysis

            if progress_output:
                print_progress(i,title_count,"Analyzing comprehension for all manga titles")

            title_filename = title_analysis_dir + title_id + ".json"

            if not os.path.exists(title_filename):
                if not progress_output:
                    print("Title %s datafile %s not found!" % (title_name,title_filename))
                continue

            title_analysis, title_data = load_and_analyze_dataset(title_filename)
            title_analysis['num_pages'] = title_data['num_pages']
            
            # Average tankobon volume page count is 180, but it might vary considerable by
            # manga, so to make those statistics more comparable we calculate virtual volume
            # count and use that for those variables that rely on # of volumes.
            title_data['num_virtual_volumes'] = round(title_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

            fetch_known_jlpt_levels(title_data, title_analysis['total_statistics'], total=True)
            fetch_known_jlpt_levels(title_data, title_analysis['unique_statistics'], total=False)

        # aggregate ci sentence grading
        for i in range(7):
            avg_ci_sentence_count[i] += title_analysis['comprehensible_input_sentence_grading'][i]

        if args['title'] is not None:
            print("\t%s\tCI %.1f Known words %.1f%%" % (title_name,title_analysis['comprehensible_input_pct'],
                title_analysis['total_statistics']['words']['pct_known_pre_known']))

        analysis[title_id] = title_analysis

    # calculate ci sentence grading average
    for i in range(7):
        avg_ci_sentence_count[i] /= len(analysis.keys())
    avg_ci_sentence_count = [ round(ac,1) for ac in avg_ci_sentence_count ]

    return analysis, avg_ci_sentence_count


# Get next non-fully read volume (some chapters might be read and some not)
def get_next_unread_volume(title_id):
    ch_id = get_next_unread_chapter(title_id)
    if ch_id is not None:
        return get_volume_id_by_chapter_id(ch_id)
    return None

def get_next_unread_chapter(title_id):

    title_chapters = get_chapters_by_title_id(title_id)
    if len(title_chapters) == 0:
        print(" * Warning! %s has no chapters" % title_id)
        return None

    # find next unread chapter
    highest_read_chapter = 0
    highest_read_chapter_id = None
    for chapter_id, _ in chapter_comprehension.items():
        if chapter_id in title_chapters:
            chapter = get_chapter_number_by_chapter_id(chapter_id)
            if chapter > highest_read_chapter:
                highest_read_chapter = chapter
                highest_read_chapter_id = chapter_id

    # skip chapters which have missing chapter data files or too few content (i.e. indexes)
    valid_found = False
    while not valid_found and highest_read_chapter < len(title_chapters):
        chapter_filename = chapter_analysis_dir + chapter_id + ".json"
        if os.path.exists(chapter_filename):
            if not is_book(title_id):
                # assume every manga chapter/volume has enough content
                valid_found = True
            else:
                summary = get_language_summary(title_id)
                if summary is None:
                    return None
                ns = summary['num_sentences']
                if ns == 0:
                    print("Warning! %s has no content!" % get_title_by_id(title_id))
                    return None
                if summary['num_sentences_per_ch'][highest_read_chapter] < 30:
                    # this chapter has low number of sentences. Most likely a index chapter, so skip it
                    highest_read_chapter += 1
                else:
                    valid_found = True
        else:
            highest_read_chapter += 1

    if highest_read_chapter == len(title_chapters):
        # all read
        return None

    if highest_read_chapter == 0:
        highest_read_chapter_id = title_chapters[0]
    else:
        highest_read_chapter_id = title_chapters[highest_read_chapter]

    return highest_read_chapter_id


def analyze_next_unread(args):

    if not progress_output:
        print("Analyzing comprehension for the next unread chapters/volumes")
    next_ch_analysis = dict()
    next_vol_analysis = dict()

    title_count = len(get_title_names().keys())
    reset_progress()
    for i, (title_id, title_name) in enumerate(get_title_names().items()):

        if args['title'] is not None and args['title'].lower() not in title_name.lower():
            continue

        if 'next_unread_chapter' in old_analysis and title_id in old_analysis['next_unread_chapter'] and not args['force']:
            chapter_analysis = old_analysis['next_unread_chapter'][title_id]
        else:
            # recalculate analysis

            if progress_output:
                print_progress(i,title_count,"Analyzing comprehension for the next unread chapters/volumes")

            chapter_id = get_next_unread_chapter(title_id)
            if chapter_id is None:
                chapter_analysis = None
                if not progress_output:
                    print(" * %s already read" % title_name)
            else:

                chapter = get_chapter_number_by_chapter_id(chapter_id)
                #next_unread_chapter[title_id] = chapter

                chapter_filename = chapter_analysis_dir + chapter_id + ".json"

                if not os.path.exists(chapter_filename):
                    if not progress_output:
                        print("%s chapter %d not found! [%s]" % (title_name, chapter, chapter_filename))
                    continue

                chapter_analysis, chapter_data = load_and_analyze_dataset(chapter_filename)
                chapter_analysis['unread_idx'] = chapter
                chapter_analysis['num_pages'] = chapter_data['num_pages']

                # Average tankobon volume page count is 180, but it might vary considerable by
                # manga, so to make those statistics more comparable we calculate virtual volume
                # count and use that for those variables that rely on # of volumes.
                chapter_data['num_virtual_volumes'] = round(chapter_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

                fetch_known_jlpt_levels(chapter_data, chapter_analysis['total_statistics'], total=True)
                fetch_known_jlpt_levels(chapter_data, chapter_analysis['unique_statistics'], total=False)

        if args['title'] is not None:
            print("\t[ch] %s\tCI %.1f Known words %.1f%%" % (title_name,chapter_analysis['comprehensible_input_pct'],
                chapter_analysis['total_statistics']['words']['pct_known_pre_known']))

        if chapter_analysis is not None:
            if is_book(title_id):
                next_ch_analysis[title_id] = chapter_analysis
            else:
                # assume that all manga chapters are actually volumes
                next_vol_analysis[title_id] = chapter_analysis

        if is_book(title_id):
            if 'next_unread_volume' in old_analysis and title_id in old_analysis['next_unread_volume'] and not args['force']:
                volume_analysis = old_analysis['next_unread_volume'][title_id]
            else:
                # recalculate analysis

                if progress_output:
                    print_progress(i,title_count,"Analyzing comprehension for the next unread chapters/volumes")

                vol_id = get_next_unread_volume(title_id)
                if vol_id is None:
                    volume_analysis = None
                    if not progress_output:
                        print(" * %s already read" % title_name)
                else:

                    volume = get_volume_number_by_volume_id(vol_id)
                    #next_unread_chapter[title_id] = chapter

                    volume_filename = volume_analysis_dir + vol_id + ".json"

                    if not os.path.exists(volume_filename):
                        if not progress_output:
                            print("%s volume %d not found! [%s]" % (title_name, volume, volume_filename))
                        continue

                    volume_analysis, vol_data = load_and_analyze_dataset(volume_filename)
                    volume_analysis['unread_idx'] = volume
                    volume_analysis['num_pages'] = vol_data['num_pages']

                    # Average tankobon volume page count is 180, but it might vary considerable by
                    # manga, so to make those statistics more comparable we calculate virtual volume
                    # count and use that for those variables that rely on # of volumes.
                    vol_data['num_virtual_volumes'] = round(vol_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

                    fetch_known_jlpt_levels(vol_data, volume_analysis['total_statistics'], total=True)
                    fetch_known_jlpt_levels(vol_data, volume_analysis['unique_statistics'], total=False)

            if volume_analysis is not None:
                next_vol_analysis[title_id] = volume_analysis

    return next_ch_analysis, next_vol_analysis


def suggest_preread(args):

    target_title_id = get_title_id(args['title'])

    # read previous analysis
    suggest_preread_data = dict()
    fn = suggested_preread_dir + target_title_id + '.json'
    if os.path.exists(fn):
        o_f = open(fn ,"r",encoding="utf-8")
        suggest_preread_data = json.loads(o_f.read())
        o_f.close()
    if 'title' not in suggest_preread_data:
        suggest_preread_data['title'] = dict()
    if 'next_unread_volume' not in suggest_preread_data:
        suggest_preread_data['next_unread_volume'] = dict()
    if 'next_unread_chapter' not in suggest_preread_data:
        suggest_preread_data['next_unread_chapter'] = dict()

    if not progress_output:
        print("Analyzing suggested pre-reading for " + get_title_by_id(target_title_id))

    target_data = None
    if args['target_scope'] == 'title':
        index_title_filename = title_analysis_dir + target_title_id + ".json"
        o_f = open(index_title_filename,"r",encoding="utf-8")
        target_data = json.loads(o_f.read())
        o_f.close()
        target_selection = 'title'
    elif args['target_scope'] == 'next_unread_volume':
        target_selection = 'next_unread_volume'
        if is_book(target_title_id):
            target_volume_id = get_next_unread_volume(target_title_id)
            if target_volume_id is None:
                suggest_preread_data[target_selection] = {'success':False,'status':'All volumes read!'}
            else:
                target_volume = get_volume_number_by_volume_id(target_volume_id)
                index_volume_filename = volume_analysis_dir + target_volume_id + ".json"
                if os.path.exists(index_volume_filename):
                    o_f = open(index_volume_filename,"r",encoding="utf-8")
                    target_data = json.loads(o_f.read())
                    o_f.close()
                else:
                    suggest_preread_data[target_selection] = {'success':False,'status':'Next unread volume %s (%d) not found!' % (target_volume_id,target_volume)}
        else:
            target_chapter_id = get_next_unread_chapter(target_title_id)
            if target_chapter_id is None:
                suggest_preread_data[target_selection] = {'success':False,'status':'All chapters read!'}
            else:
                target_chapter = get_chapter_number_by_chapter_id(target_chapter_id)
                index_chapter_filename = chapter_analysis_dir + target_chapter_id + ".json"
                if os.path.exists(index_chapter_filename):
                    o_f = open(index_chapter_filename,"r",encoding="utf-8")
                    target_data = json.loads(o_f.read())
                    o_f.close()
                else:
                    suggest_preread_data[target_selection] = {'success':False,'status':'Next unread chapter %s (%d) not found!' % (target_chapter_id,target_chapter)}
    elif args['target_scope'] == 'next_unread_chapter':
        target_selection = 'next_unread_chapter'
        target_chapter_id = get_next_unread_chapter(target_title_id)
        if target_chapter_id is None:
            suggest_preread_data[target_selection] = {'success':False,'status':'All chapters read!'}
        else:
            target_chapter = get_chapter_number_by_chapter_id(target_chapter_id)
            index_chapter_filename = chapter_analysis_dir + target_chapter_id + ".json"
            if os.path.exists(index_chapter_filename):
                o_f = open(index_chapter_filename,"r",encoding="utf-8")
                target_data = json.loads(o_f.read())
                o_f.close()
            else:
                suggest_preread_data[target_selection] = {'success':False,'status':'Next unread chapter %s (%d) not found!' % (target_chapter_id,target_chapter)}
    else:
        raise Exception("Invalid target scope!")

    source_filter = args['filter']
    source_selection = args['source_scope']

    if target_data is not None:
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

        processed_titles = []
        for title_id, title_name in get_title_names().items():
            if source_filter == 'all':
                processed_titles.append((title_id,title_name))
            else:
                if source_filter == 'book' and is_book(title_id):
                    processed_titles.append((title_id,title_name))
                if source_filter != 'book' and not is_book(title_id):
                    processed_titles.append((title_id,title_name))

        reset_progress()

        title_count = len(processed_titles)

        for i, (title_id, title_name) in enumerate(processed_titles):

            if progress_output:
                print_progress(i,title_count,"Analyzing")

            # TODO: optimize
            this_session_learning_data = copy.deepcopy(learning_data)

            if source_selection == 'title':
                candidate_filename = title_analysis_dir + title_id + ".json"
                volume = 'ALL'
                num_volumes = len(get_volumes_by_title_id(title_id))
            elif source_selection == 'next_unread_volume':
                if is_book(title_id):
                    vol_id = get_next_unread_volume(title_id)
                    if vol_id is None:
                        if not progress_output:
                            print("Skipping %s because already read all volumes" % (title_name))
                        continue
                    volume = str(get_volume_number_by_volume_id(vol_id))
                    candidate_filename = volume_analysis_dir + vol_id + ".json"
                else:
                    chapter_id = get_next_unread_chapter(title_id)
                    if chapter_id is None:
                        if not progress_output:
                            print("Skipping %s because already read all chapters/volumes" % (title_name))
                        continue
                    # regard all manga chapters as volumes
                    volume = str(get_chapter_number_by_chapter_id(chapter_id))
                    candidate_filename = chapter_analysis_dir + chapter_id + ".json"
                num_volumes = 1
            else:
                raise Exception("Invalid source scope!")

            if os.path.exists(candidate_filename):
                o_f = open(candidate_filename,"r",encoding="utf-8")
                candidate_data = json.loads(o_f.read())
                o_f.close()

                num_pages = candidate_data['num_pages']
                num_words = candidate_data['num_words']

                title_analysis = dict()
                title_analysis['volume'] = volume

                # first read the candidate, retaining the words learned from this session
                # while analyzing how difficult this candidate series is..
                w_an = read_dataset(candidate_data, "words", this_session_learning_data, retain_changes=True)
                candidate_word_analysis = w_an['total_statistics']
                candidate_pct_known = candidate_word_analysis['pct_known_pre_known']
                if candidate_pct_known < target_pct_known - 5:
                    if not progress_output:
                        print("Skipping %s with comprehension %.1f" % (title_name,candidate_pct_known))
                    continue
                read_sentences(candidate_data, this_session_learning_data, w_an)
                candicate_pct_ci = w_an['comprehensible_input_pct']
                if candicate_pct_ci < target_pct_ci:
                    if not progress_output:
                        print("Skipping %s with comprehensible input %.1f" % (title_name,candicate_pct_ci))
                    continue
                
                # calculate number of common unique weak (unfamiliar or learning) words
                w_id_set = set(candidate_data['word_id_list'])
                common_unique_weak_words = w_id_set.intersection(weak_word_ids)
                cuww = len(common_unique_weak_words)
                title_analysis['num_common_unique_weak_words'] = cuww
                title_analysis['num_analyzed_pages'] = num_pages
                title_analysis['num_analyzed_volumes'] = num_volumes

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


        timestamp = int(time.time())*1000
        suggest_preread_data[target_selection][source_selection] = {
            'success':True,
            'status':'OK',
            'timestamp':timestamp, 
            'analysis':analysis
        }

    o_f = open(suggested_preread_dir + target_title_id + '.json' ,"w",encoding="utf-8")
    json_data = json.dumps(suggest_preread_data)
    o_f.write(json_data)
    o_f.close()

    if progress_output:
        print_progress(i,title_count,"Done")


def series_analysis_for_jlpt(args):

    print("Analyzing suggested reading for JLPT",flush=True)

    analysis = dict()

    count = 0
    for title_id, title_name in get_title_names().items():

        if args['title'] is not None and args['title'].lower() not in title_name.lower():
            continue

        if 'series_analysis_for_jlpt' in old_analysis and title_id in old_analysis['series_analysis_for_jlpt'] and not args['force']:
            title_analysis = old_analysis['series_analysis_for_jlpt'][title_id]
        else:
            # recalculate analysis

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

            title_analysis['relative_improvement_pts'] = round(points,1)
            title_analysis['improvement_pts'] = jlpt_points
            title_analysis['num_new_known_words'] = len(new_known_word_ids)
            title_analysis['num_new_known_kanjis'] = len(new_known_kanjis)
            title_analysis['num_new_learning_words'] = len(new_learning_word_ids)
            title_analysis['num_new_learning_kanjis'] = len(new_learning_kanjis)

        analysis[title_id] = title_analysis

    return analysis


def analyze(args):
    global old_analysis

    # TODO. Load older analysis if it exists

    d = dict()
    d['series'], avg_ci_sentence_count = analyze_titles(args)
    next_ch_analysis, next_vol_analysis = analyze_next_unread(args)
    d['next_unread_chapter'] =  next_ch_analysis
    d['next_unread_volume'] =  next_vol_analysis
    d['series_analysis_for_jlpt'] =  series_analysis_for_jlpt(args)

    timestamp = int(time.time())*1000
    custom_lang_analysis_metadata = {
        'version':get_version(OCR_SUMMARY_VERSION),
        'parser_version': get_version(LANUGAGE_PARSER_VERSION),
        'timestamp' : timestamp
    }
    for title_id in d['series'].keys():
        summary = dict()
        an_types = ['series','next_unread_chapter','next_unread_volume','series_analysis_for_jlpt']
        summary_fields = ['pct_known_pre_known','comprehensible_input_pct','comprehensible_input_ex_katakana_pct','comprehensible_input_score','num_unknown_unfamiliar','jlpt_unknown_num','relative_improvement_pts']
        for an_type in an_types:
            summary[an_type] = dict()
            if title_id not in d[an_type]:
                print("Warning. %s not in %s" % (title_id, an_type))
            else:
                an = d[an_type][title_id]
                an['title_id'] = title_id
                an['type'] = an_type
                an['user_id'] = DEFAULT_USER_ID
                an['custom_lang_analysis_metadata'] = custom_lang_analysis_metadata
                an = json.loads(json.dumps(an)) # make sure all integer keys are converted to strings
                if args['title'] is not None:
                    print("Saving %s:%s" % (title_id, an_type))
                database[BR_CUSTOM_LANG_ANALYSIS].replace_one(
                    {'user_id':an['user_id'],'type':an_type,'title_id':title_id},
                    an, upsert=True
                )

                # pick only few data points from each analysis for summary 
                def recursive_selective_copy(input_branch, output_branch):
                    for key,val in input_branch.items():
                        if key in summary_fields:
                            output_branch[key] = val
                        elif isinstance(val,dict):
                            output_branch[key] = dict()
                            recursive_selective_copy(input_branch[key], output_branch[key])
                            if len(output_branch[key]) == 0:
                                del(output_branch[key])

                recursive_selective_copy(an, summary[an_type])
                if len(summary[an_type]) == 0:
                    del(summary[an_type])

        # save the summary
        summary['title_id'] = title_id
        summary['type'] = "summary"
        summary['user_id'] = DEFAULT_USER_ID
        summary['custom_lang_analysis_metadata'] = custom_lang_analysis_metadata
        if args['title'] is not None:
            print("Saving %s:%s" % (title_id, 'summary'))
        database[BR_CUSTOM_LANG_ANALYSIS].replace_one(
            {'user_id':DEFAULT_USER_ID,'type':'summary','title_id':title_id},
            summary, upsert=True
        )

    # average summary.  
    # TODO: rest of the average values
    summary = dict()
    summary['series'] = {'avg_ci_sentence_count':avg_ci_sentence_count}
    summary['title_id'] = "average_manga"
    summary['type'] = "summary"
    summary['user_id'] = DEFAULT_USER_ID
    summary['custom_lang_analysis_metadata'] = custom_lang_analysis_metadata
    summary = json.loads(json.dumps(summary)) # make sure all integer keys are converted to strings

    database[BR_CUSTOM_LANG_ANALYSIS].replace_one(
        {'user_id':DEFAULT_USER_ID,'type':'summary','title_id':"average"},
        summary, upsert=True
    )



#################### Read input files #################################

needed_paths = [ chapter_analysis_dir, title_analysis_dir, jlpt_kanjis_file, jlpt_vocab_file]
for path in needed_paths:
    if not os.path.exists(path):
        raise Exception("Required path [%s] not found!" % path)

learning_data = database[BR_USER_LEARNING_DATA].find_one({'user_id':DEFAULT_USER_ID})

wordlist_cursor = database[BR_USER_WORD_LEARNING_STATUS].find({'user_id':DEFAULT_USER_ID},{'_id':False,'user_id':False})
learning_data['words'] = {item['wid']:{'s':item['s'],'lf':item['lf']} for item in wordlist_cursor}

kanjilist_cursor = database[BR_USER_KANJI_LEARNING_STATUS].find({'user_id':DEFAULT_USER_ID},{'_id':False,'ltf':False,'user_id':False})
learning_data['kanjis'] = {item['kanji']:{'s':item['s'],'lf':item['lf']} for item in kanjilist_cursor}


parser = argparse.ArgumentParser(
    prog="bm_analyze",
    description="Bilingual Manga Language Analyzing Tool",
)

subparsers = parser.add_subparsers(help='', dest='command')
parser_analyze = subparsers.add_parser('analyze', help='Do comprehension analysis per title')
parser_analyze.add_argument('--title', '-t', type=str, default=None, help='Target manga title')
parser_analyze.add_argument('--force', '-f', action='store_true', help='Force update')
parser_analyze.add_argument('--progress-output', '-po', action='store_true', help='Output only progress')

parser_suggest_preread = subparsers.add_parser('suggest_preread', help='Analyze given title and then suggest beneficial pre-read titles which increase comprehension')
parser_suggest_preread.add_argument('title', type=str, help='Target manga title')
parser_suggest_preread.add_argument('--progress-output', '-po', action='store_true', help='Output only progress')
parser_suggest_preread.add_argument('--target_scope', '-ts', type=str, help='Scope of the target manga/book. Valid selections: title, next_unread_volume, next_unread_chapter')
parser_suggest_preread.add_argument('--source_scope', '-ss', type=str, help='Scope of the source manga/book. Valid selections: title, next_unread_volume')
parser_suggest_preread.add_argument('--filter', '-f', type=str, default="all",  help='Process only [book|manga|all]')

args = vars(parser.parse_args())

#args = {'command':'analyze','title':None,'progress_output':False}

cmd = args.pop('command')
progress_output = False
if 'progress_output' in args:
    progress_output = args['progress_output']

load_jmdict(verbose=not progress_output)

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

#analyze({'title':'Hitch','force':False})
#analyze_next_unread({'title':'tortoise','force':True})
#suggest_preread({'title':'66620803ae0ef12efe53117a','filter':'book','progress-output':False,'target_scope':'title','source_scope':'next_unread_volume'})
#suggest_preread({'title':'6696a9de5346852c2184aed0','filter':'manga','progress-output':False,'target_scope':'next_unread_chapter','source_scope':'next_unread_volume'})

if cmd is not None:
    #try:
    locals()[cmd](args)
    #except Exception as e:
    #    print(e, file=sys.stderr)
    #    exit(-1)

