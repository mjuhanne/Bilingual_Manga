import os
import json
import copy
import argparse
import time
import random
from mongo import *

from helper import *
from bm_learning_engine_helper import *
from jmdict import *
from br_mongo import *
from bm_analyze_helper import *

SUGGESTED_PREREAD_ANALYSIS_VERSION = 1

#input files
jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  base_dir + "lang/jlpt/jlpt_vocab.json"
language_reactor_json_file = base_dir + 'lang/user/language-reactor.json'
user_known_words_file = base_dir + 'lang/user/user_known_words.csv'
user_known_kanjis_file = base_dir + 'lang/user/user_known_kanjis.csv'
user_word_occurrence_file = base_dir + 'lang/user/user_word_occurrence.tsv'
user_kanji_occurrence_file = base_dir + 'lang/user/user_kanji_occurrence.tsv'

user_settings = read_user_settings()
chapter_comprehension = user_settings['chapter_reading_status']

# output files
suggested_preread_dir = base_dir + 'lang/suggested_preread/'


progress_output = False
old_analysis = dict()

last_progress = 0
def reset_progress():
    global last_progress
    last_progress = 0

def print_progress(i,title_count,msg):
    global last_progress
    if title_count != 0:
        p = int(100*i/title_count)
    else:
        p = 100
    if p != last_progress:
        print("%s (%d%%)  " % (msg,p), flush=True)
        last_progress = p

def calculate_average_summary(custom_lang_analysis_metadata):

    print("Calculating average summary..")
    avg_ci_sentence_count = [0] * 8
                
    cursor = database[BR_CUSTOM_LANG_ANALYSIS].find(
            {'user_id':DEFAULT_USER_ID,'type':'series'},{'comprehensible_input_sentence_grading':True})

    count = 0
    for analysis in cursor:
        # aggregate ci sentence grading
        count += 1
        for i in range(8):
            avg_ci_sentence_count[i] += analysis['comprehensible_input_sentence_grading'][i]

    # calculate ci sentence grading average
    for i in range(8):
        avg_ci_sentence_count[i] /= count
    avg_ci_sentence_count = [ round(ac,1) for ac in avg_ci_sentence_count ]

    # average summary.  
    # TODO: rest of the average values
    summary = dict()
    summary['series'] = {'avg_ci_sentence_count':avg_ci_sentence_count}
    summary['title_id'] = "average_title"
    summary['type'] = "summary"
    summary['user_id'] = DEFAULT_USER_ID
    summary['custom_lang_analysis_metadata'] = custom_lang_analysis_metadata
    summary = json.loads(json.dumps(summary)) # make sure all integer keys are converted to strings

    database[BR_CUSTOM_LANG_ANALYSIS_SUMMARY].replace_one(
        {'user_id':DEFAULT_USER_ID,'title_id':"average_title"},
        summary, upsert=True
    )
    print("Done!")


def do_analyze(data_set, title_name, an_type):
    if data_set is None:
        if not progress_output:
            print("%s %s datafile not found!" % (an_type, title_name))
        return None
    
    analysis, data = analyze_dataset(data_set)
    analysis['num_pages'] = data['num_pages']
    
    # Average tankobon volume page count is 180, but it might vary considerable by
    # manga, so to make those statistics more comparable we calculate virtual volume
    # count and use that for those variables that rely on # of volumes.
    data['num_virtual_volumes'] = round(data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

    fetch_known_jlpt_levels(data, analysis['total_statistics'], total=True)
    fetch_known_jlpt_levels(data, analysis['unique_statistics'], total=False)
    return analysis


def analyze_title(args, title_id, title_name):
    data_set = get_analysis_data_for_title(title_id)
    return do_analyze(data_set, title_name, "Title")


# Get next non-fully read volume (some chapters might be read and some not)
def get_next_unread_volume(title_id):
    ch_id = get_next_unread_chapter(title_id)
    if ch_id is not None:
        return get_volume_id_by_chapter_id(ch_id)
    return None

def get_next_unread_chapter(title_id):

    title_chapters = get_chapters_by_title_id(title_id,lang='jp')
    if len(title_chapters) == 0:
        print(" * Warning! %s has no chapters" % title_id)
        return None

    # find next unread chapter
    highest_read_chapter = 0
    highest_read_chapter_id = None
    for chapter_id, _ in chapter_comprehension.items():
        if chapter_id in title_chapters:
            chapter = get_chapter_idx_by_chapter_id(chapter_id)
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


def analyze_next_unread_chapter(args, title_id, title_name):

    chapter_id = get_next_unread_chapter(title_id)
    if chapter_id is None:
        if not progress_output:
            print(" * %s already read" % title_name)
        return None

    chapter = get_chapter_idx_by_chapter_id(chapter_id)
    data_set = get_analysis_data_for_chapter(chapter_id)
    chapter_analysis = do_analyze(data_set, title_name, "chapter")
    if chapter_analysis is not None:
        chapter_analysis['unread_idx'] = chapter

    return chapter_analysis


def analyze_next_unread_volume(args, title_id, title_name):

    vol_id = get_next_unread_volume(title_id)
    if vol_id is None:
        if not progress_output:
            print(" * %s already read" % title_name)
        return None

    volume = get_volume_number_by_volume_id(vol_id)
    data_set = get_analysis_data_for_volume(vol_id)
    volume_analysis = do_analyze(data_set, title_name, "chapter")
    if volume_analysis is not None:
        volume_analysis['unread_idx'] = volume

    return volume_analysis


def series_analysis_for_jlpt(args, title_id, title_name):

    title_data = get_analysis_data_for_title(title_id)
    if title_data is None:
        print("Title %s/%s datafile not found!" % (title_id,title_name))
        return None

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

    return title_analysis


def suggest_preread(args):

    target_title_id = get_title_id(args['title'])

    if not progress_output:
        print("Analyzing suggested pre-reading for " + get_title_by_id(target_title_id))

    # load analysis data for target title
    target_data = None
    failed_msg = None
    if args['target_scope'] == 'title':
        target_data = get_analysis_data_for_title(target_title_id)
        target_selection = 'title'
    elif args['target_scope'] == 'next_unread_volume':
        target_selection = 'next_unread_volume'
        if is_book(target_title_id):
            target_volume_id = get_next_unread_volume(target_title_id)
            if target_volume_id is None:
                failed_msg = 'All volumes read!'
            else:
                target_volume = get_volume_number_by_volume_id(target_volume_id)
                target_data = get_analysis_data_for_volume(target_volume_id)
                if target_data is None:
                    failed_msg = 'Next unread volume %s (%d) not found!' % (target_volume_id,target_volume)
        else:
            target_chapter_id = get_next_unread_chapter(target_title_id)
            if target_chapter_id is None:
                failed_msg = 'All chapters read!'
            else:
                target_chapter = get_chapter_idx_by_chapter_id(target_chapter_id)
                target_data = get_analysis_data_for_chapter(target_chapter_id)
                if target_data is None:
                    failed_msg = 'Next unread chapter %s (%d) not found!' % (target_chapter_id,target_chapter)
    elif args['target_scope'] == 'next_unread_chapter':
        target_selection = 'next_unread_chapter'
        target_chapter_id = get_next_unread_chapter(target_title_id)
        if target_chapter_id is None:
            failed_msg = 'All chapters read!'
        else:
            target_chapter = get_chapter_idx_by_chapter_id(target_chapter_id)
            target_data = get_analysis_data_for_chapter(target_chapter_id)
            if target_data is None:
                failed_msg = 'Next unread chapter %s (%d) not found!' % (target_chapter_id,target_chapter)
    else:
        raise Exception("Invalid target scope!")

    source_filter = args['filter']
    source_selection = args['source_scope']

    if failed_msg is not None:
        if progress_output:
            print_progress(0,0,failed_msg)
        else:
            print(failed_msg)
        return

    # load previous analysis results for source titles
    old_data = database[BR_SUGGESTED_PREREAD].find(
        {'user_id':DEFAULT_USER_ID,
         'target_title_id':target_title_id,'target_selection':target_selection,
         'source_selection':source_selection
    })
    old_suggestions = {entry['source_title_id']:entry for entry in old_data}

    summary_data = database[BR_CUSTOM_LANG_ANALYSIS_SUMMARY].aggregate([
        {
            '$match': {
            'user_id':DEFAULT_USER_ID,
            },
        },
        {
            '$lookup' : {
                'from':'br_metadata',
                'localField':'title_id',
                'foreignField':'_id',
                'as' : 'metadata'
            }
        },
        {
            '$unwind': {
                'path':'$metadata',
                'preserveNullAndEmptyArrays':True
            }
        }
    ])
    summary_by_title = {entry['title_id']:entry for entry in summary_data}

    MINIMUM_SOURCE_CI = 90

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

        processed_titles = []
        for title_id, summary in summary_by_title.items():
            if title_id != 'average_manga' and title_id != 'average_title':
                source_ci = 0
                if source_selection == 'title':
                    if 'comprehensible_input_pct' in summary['series']:
                        source_ci = summary['series']['comprehensible_input_pct']
                elif source_selection == 'next_unread_volume':
                    if 'comprehensible_input_pct' in summary['next_unread_volume']:
                        source_ci = summary['next_unread_volume']['comprehensible_input_pct']
                if source_ci < MINIMUM_SOURCE_CI:
                    continue

                if (title_id not in old_suggestions or old_suggestions[title_id]['timestamp'] != summary['custom_lang_analysis_metadata']['timestamp']) or \
                    ('version' not in old_suggestions[title_id] or old_suggestions[title_id]['version'] != SUGGESTED_PREREAD_ANALYSIS_VERSION):
                        if source_filter == 'all':
                            processed_titles.append(title_id)
                        else:
                            if source_filter == 'book' and summary['metadata']['is_book']:
                                processed_titles.append(title_id)
                            if source_filter != 'book' and not summary['metadata']['is_book']:
                                processed_titles.append(title_id)

        reset_progress()

        title_count = len(processed_titles)

        for i, title_id in enumerate(processed_titles):

            summary = summary_by_title[title_id]
            title_name = summary['metadata']['entit']

            print_progress(i,title_count,"Analyzing")

            # TODO: optimize
            this_session_learning_data = copy.deepcopy(learning_data)

            if source_selection == 'title':
                candidate_data = get_analysis_data_for_title(title_id)
                volume = 'ALL'
                num_volumes = len(get_volumes_by_title_id(title_id, lang='jp'))
            elif source_selection == 'next_unread_volume':
                if is_book(title_id):
                    vol_id = get_next_unread_volume(title_id)
                    if vol_id is None:
                        if not progress_output:
                            print("Skipping %s because already read all volumes" % (title_name))
                        continue
                    volume = str(get_volume_number_by_volume_id(vol_id))
                    candidate_data = get_analysis_data_for_volume(vol_id)
                else:
                    chapter_id = get_next_unread_chapter(title_id)
                    if chapter_id is None:
                        if not progress_output:
                            print("Skipping %s because already read all chapters/volumes" % (title_name))
                        continue
                    # regard all manga chapters as volumes
                    volume = str(get_chapter_idx_by_chapter_id(chapter_id))
                    candidate_data = get_analysis_data_for_chapter(chapter_id)
                num_volumes = 1
            else:
                raise Exception("Invalid source scope!")

            if candidate_data is not None:

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

                title_analysis['pct_known_pre_known_word'] = candidate_pct_known
                title_analysis['comprehensible_input_pct'] = candicate_pct_ci

                title_analysis['user_id'] = DEFAULT_USER_ID
                title_analysis['target_title_id'] = target_title_id
                title_analysis['target_selection'] = target_selection
                title_analysis['source_selection'] = source_selection
                title_analysis['source_title_id'] = title_id
                title_analysis['timestamp'] = summary['custom_lang_analysis_metadata']['timestamp']
                title_analysis['version'] = SUGGESTED_PREREAD_ANALYSIS_VERSION
                database[BR_SUGGESTED_PREREAD].replace_one(
                    {'user_id':DEFAULT_USER_ID,
                    'target_title_id':target_title_id,'target_selection':target_selection,
                    'source_title_id':title_id,'source_selection':source_selection
                    },
                    title_analysis, upsert=True
                )

    if progress_output:
        print_progress(title_count,title_count,"Done")

def is_up_to_date(analysis):
    if 'update_due' in analysis['custom_lang_analysis_metadata']:
        due =  analysis['custom_lang_analysis_metadata']['update_due']
        timestamp = int(time.time())*1000
        if due > timestamp:
            return True
    return False


def calculate_due_update_time(analysis):
    if analysis['comprehensible_input_pct'] < 80 or analysis['comprehensible_input_pct'] > 95:
        # less need to update so frequently
        due_days = random.randint(7,30)
    elif analysis['comprehensible_input_pct'] < 85:
        due_days = random.randint(4,7)
    else:
        due_days = random.randint(1,4)
    due_timestamp = (int(time.time()) + 60*60*24*due_days )*1000
    return due_timestamp
    
def calculate_reading_completion_percentage(title_id):
    all_chapters = get_chapters_by_title_id(title_id, lang='jp')
    if len(all_chapters) == 0:
        return 0

    total_pages = 0
    read_pages = 0
    for ch in all_chapters:
        ch_pages = get_chapter_page_count(ch)
        total_pages += ch_pages
        if ch in chapter_comprehension.keys():
            read_pages += ch_pages

    if total_pages == 0:
        return 0
    return round(100*read_pages/total_pages,1)



def analyze(args):
    global old_analysis

    an_types = ['series','next_unread_chapter','next_unread_volume','series_analysis_for_jlpt']

    # load previous analysis
    if not args['force']:
        for an_type in an_types:
                    
            cursor = database[BR_CUSTOM_LANG_ANALYSIS].find(
                    {'user_id':DEFAULT_USER_ID,'type':an_type},{'_id':False})
            old_analysis[an_type] = {an['title_id']:an for an in cursor}

    if not progress_output:
        print("Analyzing comprehension..")
    reset_progress()

    title_names = get_title_names()
    title_count = len(title_names)

    timestamp = int(time.time())*1000
    custom_lang_analysis_metadata = {
        'version':get_version(OCR_SUMMARY_VERSION),
        'parser_version': get_version(LANUGAGE_PARSER_VERSION),
        'timestamp' : timestamp,
    }

    for i, (title_id, title_name) in enumerate(title_names.items()):

        jp_title = get_jp_title_by_id(title_id)
        if progress_output:
            print_progress(i,title_count,"Analyzing")

        if args['title'] is not None and args['title'].lower() not in title_name.lower() and args['title'] != title_id and args['title'] not in jp_title:
            continue

        if args['read']:
            if not is_title_read(title_id):
                continue

        if args['title'] is not None:
            print("Analyzing",title_name)

        d = dict()
        if is_book(title_id):
            funcs = [analyze_title, analyze_next_unread_chapter, analyze_next_unread_volume, series_analysis_for_jlpt]
            func_an_types = an_types
        else:
            # assume that all manga chapters are actually volumes
            funcs = [analyze_title, analyze_next_unread_chapter, series_analysis_for_jlpt]
            func_an_types = ['series','next_unread_volume','series_analysis_for_jlpt']

        updated = False
        for func, an_type in zip(funcs, func_an_types):

            if not args['force'] and an_type in old_analysis and title_id in old_analysis[an_type] \
                and is_up_to_date(old_analysis[an_type][title_id]):
                d[an_type] = old_analysis[an_type][title_id]
            else:
                d[an_type] = func(args, title_id, title_name)
                if d[an_type] is not None:
                    updated = True

        if updated:
            update_due = calculate_due_update_time(d['series'])

            custom_lang_analysis_metadata['update_due'] = update_due

            summary = dict()
            summary_fields = ['pct_known_pre_known','comprehensible_input_pct','comprehensible_input_ex_katakana_pct','comprehensible_input_score','num_unknown_unfamiliar','jlpt_unknown_num','relative_improvement_pts']
            for an_type in an_types:
                summary[an_type] = dict()
                if an_type in d:
                    an = d[an_type]
                    if an is not None:
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
            summary['user_id'] = DEFAULT_USER_ID
            summary['custom_lang_analysis_metadata'] = custom_lang_analysis_metadata
            summary['reading_pct'] = calculate_reading_completion_percentage(title_id)
            if args['title'] is not None:
                print("Saving %s:%s" % (title_id, 'summary'))
            database[BR_CUSTOM_LANG_ANALYSIS_SUMMARY].replace_one(
                {'user_id':DEFAULT_USER_ID,'title_id':title_id},
                summary, upsert=True
            )

    if args['title'] is None:
        calculate_average_summary(custom_lang_analysis_metadata)

    # try to create an index just in case it doesn't already exist
    database[BR_CUSTOM_LANG_ANALYSIS_SUMMARY].create_index({'title_id':-1})
    database[BR_SUGGESTED_PREREAD].create_index({'target_title_id':1})


#################### Read input files #################################

if __name__ == '__main__':

    needed_paths = [ chapter_analysis_dir, title_analysis_dir, jlpt_kanjis_file, jlpt_vocab_file]
    for path in needed_paths:
        if not os.path.exists(path):
            raise Exception("Required path [%s] not found!" % path)



    parser = argparse.ArgumentParser(
        prog="bm_analyze",
        description="Bilingual Manga Language Analyzing Tool",
    )

    subparsers = parser.add_subparsers(help='', dest='command')
    parser_analyze = subparsers.add_parser('analyze', help='Do comprehension analysis per title')
    parser_analyze.add_argument('--title', '-t', type=str, default=None, help='Target manga title')
    parser_analyze.add_argument('--force', '-f', action='store_true', help='Force update')
    parser_analyze.add_argument('--progress-output', '-po', action='store_true', help='Output only progress')
    parser_analyze.add_argument('--read', '-r', action='store_true', help='Process only read titles')

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


    #analyze({'title':None,'force':False,'read':False})
    #analyze({'title':'Hitch','force':False})
    #analyze_next_unread({'title':'tortoise','force':True})
    #suggest_preread({'title':'66c8adc22e77804a9dc14ede','filter':'book','progress-output':False,'target_scope':'title','source_scope':'next_unread_volume'})
    #suggest_preread({'title':'6696a9de5346852c2184aed0','filter':'manga','progress-output':False,'target_scope':'next_unread_chapter','source_scope':'next_unread_volume'})

    if cmd is not None:
        #try:
        locals()[cmd](args)
        #except Exception as e:
        #    print(e, file=sys.stderr)
        #    exit(-1)

