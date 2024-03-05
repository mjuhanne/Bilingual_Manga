# Bilingual Manga custom language analysis tool

import os
import json
import argparse
import time
import sys
import datetime

from helper import *

# Full history is just for debugging because the resulting data set becomes quickly too large.
# Instead we keep history only for those events when the learning stage changes
RETAIN_FULL_WORD_HISTORY = False  

#input files
language_reactor_json_file = base_dir + 'lang/user/language-reactor.json'
user_known_words_file = base_dir + 'lang/user/user_known_words.csv'
user_known_kanjis_file = base_dir + 'lang/user/user_known_kanjis.csv'
user_word_occurrence_file = base_dir + 'lang/user/user_word_occurrence.tsv'
user_kanji_occurrence_file = base_dir + 'lang/user/user_kanji_occurrence.tsv'

# output files
learning_data_filename = base_dir + 'lang/user/learning_data.json'
output_analysis_file = base_dir + 'json/custom_lang_analysis.json'
suggested_preread_dir = base_dir + 'lang/suggested_preread/'

needed_paths = [ chapter_analysis_dir, title_analysis_dir, jlpt_kanjis_file, jlpt_vocab_file, user_data_file]
for path in needed_paths:
    if not os.path.exists(path):
        raise Exception("Required path [%s] not found!" % path)

# Up/downgrade the word frequency by chapter(volume) comprehension/effort
# i.e. if we have just skimmed through a volume without much effort (comprehension level 1-2), 
# we want to decrease virtually the number of times we have seen each word. 
# On the contrary, if we know all the words in the volume (comprehension level 5), 
# all the words will be set as known (at known threshold)
comprehension_modifier = [0, 0.1, 0.5, 1, 2]

learning_data = dict()
manually_set_word_learning_stages = dict()

trace_item = None

# This contains manual word/kanji events (such as
# learning of JLPT/custom word or manual change of word/kanji learning stage ('pre-known' to 'known' etc)
manual_events = {'words':{}, 'kanjis':{}}
# Pointer to next unprocessed manual event
manual_event_pointer = {'words':{}, 'kanjis':{}}

# this is the 're-played' or reconstructed word/kanji history that contains automatic events 
# (learned -> pre-known or known -> forgotten) etc, interleaved with manual events
event_history = {'words':{}, 'kanjis':{}}

# Lifetime occurrence of words/kanjis
lifetime_freq = {'words':{},'kanjis':{}}

# Adjusted word/kanji occurrence that is regarded when transitioning 
# between familiar->learning->pre-known stages. 
# This gets reset if a word/kanji is set back to learning stage
learning_freq = {'words':{},'kanjis':{}} 

# the period after which known word/kanji will be forgotten if not encountered during reading
remembering_periods = {'words':{},'kanjis':{}} 
unforgettable_items = {'words':set(),'kanjis':set()} 
enable_forgetting = False

chapter_comprehension = dict()

jlpt_kanjis = get_jlpt_kanjis()
read_jlpt_word_file()
jlpt_words = get_jlpt_words()
lemma_cache = dict()

def TRACE_EVENT(e):
    d = datetime.datetime.fromtimestamp(e['t'])
    s = '%s [Stage: %s(%d) Source: %s]' % (d, learning_stage_labels[e['s']].upper(), e['s'], source_labels[e['m']['src']])
    return s

def adjust_and_cap_frequency(freq, comprehension):
    if comprehension==5:
        # perfect comprehension for this volume/chapter -> set this word/kanji as (pre)known
        return learning_settings['known_word_threshold']
    adj_freq = freq * comprehension_modifier[comprehension]
    if learning_settings['max_encounters_per_chapter'] > 0:
        if adj_freq > learning_settings['max_encounters_per_chapter']:
            adj_freq = learning_settings['max_encounters_per_chapter']
    return adj_freq

# create a manual event (JLPT/custom word/kanji learning event or manual change of learning stage)
def create_manual_event(item_type, item, stage, timestamp, metadata ):
    global manual_events, manual_event_pointer
    event = {
        's' : stage,
        't' : timestamp,
        'm' : metadata,
    }
    if item not in manual_events[item_type]:
        manual_events[item_type][item] = [event]
        manual_event_pointer[item_type][item] = 0
        remembering_periods[item_type][item] = initial_remembering_period
    else:
        history = manual_events[item_type][item]

        # keep manual stage history in chronological order so its events can be interleaved 
        # easily with events occuring during chapter reading
        i = 0
        while i < len(history) and history[i]['t'] < timestamp:
            i += 1
        new_history = []
        if i > 0:
            new_history += history[:i]
        new_history += [event]
        new_history += history[i:]
        manual_events[item_type][item] = new_history

    if item not in lifetime_freq[item_type]:
        lifetime_freq[item_type][item] = 0
        learning_freq[item_type][item] = 0

    if trace_item == item:
        print(" + Created new manual event: " + TRACE_EVENT(event))

# If a word hasn't been seen after remembering_period then downgrade
# a KNOWN word/kanji to FORGOTTEN. Also PRE_KNOWN stage will be downgraded back to LEARNING
def handle_forgotten_event(item_type, item, next_timestamp):

    h = event_history[item_type][item]
    current_stage = h[-1]['s']
    if not enable_forgetting:
        return current_stage
    if item in unforgettable_items[item_type]:
        return current_stage
    last_timestamp = h[-1]['t']
    if current_stage == STAGE_KNOWN or current_stage == STAGE_PRE_KNOWN:

        # initialize remembering period if it hasn't yet been done
        try:
            remembering_period = remembering_periods[item_type][item]
        except:
            remembering_period = initial_remembering_period
            remembering_periods[item_type][item] = remembering_period

        forgot_timestamp = last_timestamp + remembering_period
        if forgot_timestamp < next_timestamp:
            forgotten_event = {
                's' : STAGE_FORGOTTEN,
                't' : forgot_timestamp,
                'm': {'src' : SOURCE_ENGINE },
            }
            days_lapsed = int(remembering_period/(24*60*60))
            if current_stage == STAGE_KNOWN:
                if trace_item is not None:
                    print(" ! Forgot %s %s" % (item_type,item))
                forgotten_event['m']['comment'] = 'Forgot after %d days' % days_lapsed
            else:
                if item_type == 'words':
                    threshold = learning_settings['known_word_threshold']
                else:
                    threshold = learning_settings['known_kanji_threshold']
                forgotten_event['s'] = STAGE_LEARNING
                forgotten_event['m']['comment'] = 'Downgraded PRE-KNOWN to LEARNING after %d days' % days_lapsed
                learning_freq[item_type][item] = threshold - 1
                if trace_item is not None:
                    print(" ! Downgraded %s %s back to LEARNING" % (item_type,item))
                
            event_history[item_type][item].append(forgotten_event)
            current_stage = STAGE_FORGOTTEN
    return current_stage

# insert all explicit/manual events preceding the next event
# to word/kanji history timeline
def insert_manual_events( item_type, item, next_event_timestamp=None ):
    if item in manual_events[item_type]:
        
        next_insertion_attempt = True
        while next_insertion_attempt:
            next_insertion_attempt = False

            ptr = manual_event_pointer[item_type][item] 
            if ptr < len(manual_events[item_type][item]):
                manual_event_timestamp = manual_events[item_type][item][ptr]['t']
                if next_event_timestamp is None or (manual_event_timestamp < next_event_timestamp):
                    # this is the spot to insert
                    manual_event = manual_events[item_type][item][ptr]
                    if item not in event_history[item_type]:
                        # this is the first occurrence of this word/kanji
                        event_history[item_type][item] = [manual_event]
                    else:
                        # check if we have forgotten this word/kanji meanwhile
                        new_stage = handle_forgotten_event(item_type, item, manual_event_timestamp)

                        if (new_stage == STAGE_FORGOTTEN) and (manual_event['s']==STAGE_KNOWN):
                            # the engine marked this word/kanji as 'forgotten' but we signaled
                            # that we in indeed remember it so we want to prolong the remembering
                            # period to avoid too frequent nagging
                            manual_event['m']['comment'] = 'Prolonging remembering period'
                            remembering_periods[item_type][item] *= (1+learning_settings['remembering_period_prolong_pct']/100)

                        event_history[item_type][item].append(manual_event)
                        if trace_item is not None:
                            print(" + New manual event: " + TRACE_EVENT(manual_event))

                    manual_event_pointer[item_type][item] += 1
                    next_insertion_attempt = True

def is_lemma_known(lemma):
    if lemma in unforgettable_items:
        return True
    if lemma in event_history['words']:
        if event_history['words'][lemma][-1]['s'] == STAGE_KNOWN:
            return True
    return False

def update_item_stage(item_type, item, lemma, stage, timestamp, metadata ):
    global event_history, manual_events, manual_event_pointer

    new_event = {
        's' : stage,
        't' : timestamp,
        'm' : metadata
    }

    # chronologically interleave manual event updates between automatic ones if needed
    insert_manual_events( item_type, item, timestamp )

    # add the automatic stage updates
    if item not in event_history[item_type]:
        # this is the first occurence for this word/kanji
        event_history[item_type][item] = [new_event]
        if lemma is not None:
            if is_lemma_known(lemma):
                # assume we know this word already
                new_event['s'] = STAGE_KNOWN
                remembering_periods[item_type][item] = initial_remembering_period
        if trace_item is not None:
            print(" * First event: " + TRACE_EVENT(new_event))
    else:
        last_event = event_history[item_type][item][-1]
        current_stage = last_event['s']

        skip = False
        if current_stage == STAGE_IGNORED:
            skip = True
            if trace_item is not None:
                print(" - Passing through during ignored stage")

        elif last_event['m']['src'] == SOURCE_USER and \
            last_event['m']['ci'] == metadata['ci']:
                # skip implicit/automatic event because user has already
                # choosed the learning stage of this word in this very chapter
                # (but its timestamp would have been slightly in the past compared 
                # to the completion timestamp of this chapter).
                skip = True
                if trace_item is not None:
                    print(" - Skipped following implicit event " + TRACE_EVENT(new_event) + "because user")

        if not skip:

            current_stage = last_event['s']

            if trace_item is not None:
                print(" + New event: " + TRACE_EVENT(new_event))

            # reset the remembering period
            if stage != current_stage and stage == STAGE_PRE_KNOWN:
                remembering_periods[item_type][item] = initial_remembering_period
                    
            # check if we have forgotten this word/kanji
            current_stage = handle_forgotten_event(item_type, item, timestamp)

            if current_stage != STAGE_FORGOTTEN:
                if (stage < current_stage):
                    # do not lower the learning stage by just reading
                    new_event['s'] = current_stage

                if RETAIN_FULL_WORD_HISTORY:
                    event_history[item_type][item].append(new_event)
                else:
                    last_event = event_history[item_type][item][-1]
                    if last_event['s'] != new_event['s'] or last_event['m']['src'] != new_event['m']['src']:
                        event_history[item_type][item].append(new_event)
                    else:
                        # overwrite the last entry
                        event_history[item_type][item][-1] = new_event
            else:
                if trace_item is not None:
                    print(" - Passing through during forgotten stage")


def update_item_stage_by_frequency_and_class(item_type, item, lemma, freq, adjusted_freq, class_list, timestamp, metadata ):
    if item in lifetime_freq[item_type]:
        lifetime_freq[item_type][item] += freq
        learning_freq[item_type][item] += adjusted_freq
    else:
        lifetime_freq[item_type][item] = freq
        learning_freq[item_type][item] = adjusted_freq
    stage = get_stage_by_frequency_and_class(item_type, learning_freq[item_type][item], class_list)
    update_item_stage(item_type, item, lemma, stage, timestamp, metadata)

def do_get_num_items(history_set,stage,source):
    num_items = 0
    for item,history in history_set.items():
        h = history[-1]
        if stage is not None and h['s'] != stage:
            continue
        if source is not None and h['m']['src'] != source:
            continue
        num_items += 1
    return num_items

def get_num_manually_set_items(item_type,stage=None,source=None):
    history_set = manual_events[item_type]
    return do_get_num_items(history_set, stage, source)

def get_num_items(item_type,stage=None,source=None):
    history_set = event_history[item_type]
    return do_get_num_items(history_set, stage, source)

def read_lang_list(filename, source, item_type, stage=None, timestamp=None):
    global learning_data

    line_number = 1
    if os.path.exists(filename):
        with open(filename,"r",encoding="utf-8") as f:
            if filename.split('.')[-1] == 'json':
                j = json.loads(f.read())

                for lemma, data in j.items():
                    if trace_item is None or trace_item == lemma:
                        if 's' not in data:
                            raise Exception("Error in %s" % filename)
                        if 'm' in data:
                            metadata = data['m']
                        else:
                            metadata = {}
                        metadata['src'] = source
                        create_manual_event(item_type,lemma, data['s'], data['t'], metadata)
                    
            else:
                assert timestamp != None
                csv = True
                if filename.split('.')[-1] == 'tsv':
                    csv = False

                lines = f.readlines()
                for line in lines:
                    if csv:
                        d = line.split(',')
                    else:
                        d = line.split('\t')
                    item = d[0]

                    item = item.strip()

                    for c in item:
                        if not is_cjk(c):
                            raise Exception("Error in %s line %d: Item %s" % (filename, line_number, item))
                    if stage is None:
                        raise Exception("%s must have occurrence data" % filename)

                    if trace_item is None or trace_item == item:
                        create_manual_event(item_type, item, stage, timestamp, {'src':source} )
                        if timestamp == 0:
                            unforgettable_items[item_type].add(item)

        print("Loaded %s" % (filename))
    else:
        print("%s not found" % (filename))


# This will replay the automatic and manual learning events 
# and update the statistics for known/learning/forgotten words and kanjis
def update(args):
    global trace_item
    if args['trace'] is not None:
        trace_item = args['trace']

    global learning_data, event_history, manual_events

    learning_data = dict()
    learning_data['words'] = dict()
    learning_data['kanjis'] = dict()
    learning_data['num_characters'] = 0
    learning_data['num_words'] = 0
    learning_data['num_kanjis'] = 0
    learning_data['num_pages'] = 0

    # to save space chapters ids are referred by index number
    index_of_chapter_ids = []

    current_timestamp = int(time.time())

    jlpt_timestamp = learning_settings['learned_jlpt_timestamp']
    learning_data['num_unique_jlpt_words'] = 0
    for w, level in jlpt_words.items():
        if trace_item is None or trace_item == w:
            if level >= learning_settings['jlpt_word_level']:
                create_manual_event('words',w, STAGE_KNOWN, jlpt_timestamp, {'src':SOURCE_JLPT, 'comment':'JLPT level %d' % level})
                learning_data['num_unique_jlpt_words'] += 1
                if jlpt_timestamp == 0:
                    unforgettable_items['words'].add(w)
    learning_data['num_unique_jlpt_kanjis'] = 0
    for k, level in jlpt_kanjis.items():
        if trace_item is None or trace_item == k:
            if level >= learning_settings['jlpt_kanji_level']:
                create_manual_event('kanjis', k, STAGE_KNOWN, jlpt_timestamp, {'src':SOURCE_JLPT, 'comment':'JLPT level %d' % level})
                learning_data['num_unique_jlpt_kanjis'] += 1
                if jlpt_timestamp == 0:
                    unforgettable_items['kanjis'].add(k)

    # custom list containing number of occurrences of each kanji and word (from external sources)
    read_lang_list(user_word_occurrence_file, SOURCE_CUSTOM, 'words', timestamp=learning_settings['learned_custom_timestamp'])
    read_lang_list(user_kanji_occurrence_file, SOURCE_CUSTOM, 'kanjis', timestamp=learning_settings['learned_custom_timestamp'])

    # custom list containing a list of known kanjis and words (from external sources)
    read_lang_list(user_known_words_file, SOURCE_CUSTOM, 'words', stage=STAGE_KNOWN, timestamp=learning_settings['learned_custom_timestamp'] )
    read_lang_list(user_known_kanjis_file, SOURCE_CUSTOM, 'kanjis', stage=STAGE_KNOWN, timestamp=learning_settings['learned_custom_timestamp'] )

    learning_data['num_unique_known_words_custom'] = get_num_manually_set_items('words',STAGE_KNOWN, SOURCE_CUSTOM)
    learning_data['num_unique_learning_words_custom'] = get_num_manually_set_items('words',STAGE_LEARNING, SOURCE_CUSTOM)
    learning_data['num_unique_known_kanjis_custom'] = get_num_manually_set_items('kanjis',STAGE_KNOWN, SOURCE_CUSTOM)
    learning_data['num_unique_learning_kanjis_custom'] = get_num_manually_set_items('kanjis',STAGE_LEARNING, SOURCE_CUSTOM)

    # List of known/learning words exported from Language Reactor
    read_lang_list(language_reactor_json_file, SOURCE_LANGUAGE_REACTOR, 'words')
    learning_data['num_unique_known_words_lr'] = get_num_manually_set_items('words',STAGE_KNOWN, SOURCE_LANGUAGE_REACTOR)
    learning_data['num_unique_learning_words_lr'] = get_num_manually_set_items('words',STAGE_LEARNING, SOURCE_LANGUAGE_REACTOR)

    ## load manually set words and their learning stages
    for word, history in user_set_words.items():
        if trace_item is None or trace_item == word:
            for entry in history:
                entry['m']['src'] = SOURCE_USER

                # to save space replace the chapter id with index number 
                cid = entry['m']['cid']
                if cid in index_of_chapter_ids:
                    idx = index_of_chapter_ids.index(cid)
                else:
                    index_of_chapter_ids.append(cid)
                    idx = len(index_of_chapter_ids)-1
                del(entry['m']['cid'])
                entry['m']['ci'] = idx

                create_manual_event('words', word, entry['s'], entry['t'], entry['m'])
    
    if trace_item is not None:
        if trace_item not in manual_events['words']:
            if trace_item not in manual_events['kanjis']:
                print(" !! %s does NOT exist in manual events!" % trace_item)

    learning_data['num_unique_known_words_user'] = get_num_manually_set_items('words',STAGE_KNOWN, SOURCE_USER)
    learning_data['num_unique_learning_words_user'] = get_num_manually_set_items('words',STAGE_LEARNING, SOURCE_USER)

    # mid-stage calculation in order get # of new learned words by reading
    num_unique_known_words_preread = get_num_manually_set_items('words',STAGE_KNOWN)
    num_unique_known_kanjis_preread = get_num_manually_set_items('kanjis',STAGE_KNOWN)
    num_unique_pre_known_words_preread = get_num_manually_set_items('words',STAGE_PRE_KNOWN)
    num_unique_pre_known_kanjis_preread = get_num_manually_set_items('kanjis',STAGE_PRE_KNOWN)
    num_unique_learning_words_preread = get_num_manually_set_items('words',STAGE_LEARNING)
    num_unique_learning_kanjis_preread = get_num_manually_set_items('kanjis',STAGE_LEARNING)


    if not learning_settings['automatic_learning_enabled']:
        # automatic learning was disabled so we just copy the manually set statuses
        event_history = manual_events
    else:
        ##########  learning by reading #######

        # sort chapters chronologically by timestamp
        chapter_timestamps = {}
        for chapter_id, reading_data in chapter_comprehension.items():
            if reading_data['status'] != 'Read':
                continue

            if 'completion_timestamp' not in reading_data:
                print("Warning! Skipping " + get_manga_chapter_name(chapter_id) + " because no completion timestamp set!", file=sys.stderr)
                continue

            chapter_timestamps[chapter_id] = reading_data['completion_timestamp']
        sorted_chapters = dict(sorted(chapter_timestamps.items(), key=lambda x:x[1]))
        
        for chapter_id, timestamp_ms in sorted_chapters.items():

            timestamp = int(timestamp_ms/1000)

            reading_data = chapter_comprehension[chapter_id]

            comprehension = reading_data['comprehension']

            title_id = get_title_id_by_chapter_id(chapter_id)
            title_name = get_title_by_id(title_id)
            chapter_filename = chapter_analysis_dir + chapter_id + ".json"
            chapter = get_chapter_number_by_chapter_id(chapter_id)

            print("[%s] Read %s [chapter %d]" % (datetime.datetime.fromtimestamp(timestamp), title_name, chapter))

            if chapter_id in index_of_chapter_ids:
                idx = index_of_chapter_ids.index(chapter_id)
            else:
               index_of_chapter_ids.append(chapter_id)
               idx = len(index_of_chapter_ids)-1

            word_metadata = {'src':SOURCE_CHAPTER,'ci':idx}

            if os.path.exists(chapter_filename):
                o_f = open(chapter_filename,"r",encoding="utf-8")
                chapter_data = json.loads(o_f.read())
                o_f.close()

                learning_data['num_characters'] += chapter_data['num_characters']
                learning_data['num_words'] += chapter_data['num_words']
                learning_data['num_kanjis'] += chapter_data['num_kanjis']
                learning_data['num_pages'] += chapter_data['num_pages']

                for word, freq, priority_classes in \
                    zip(chapter_data['words'], chapter_data['word_frequency'], chapter_data['word_priority_class']):
                    if trace_item is None or trace_item == word:
                        adjusted_freq = adjust_and_cap_frequency(freq, comprehension)
                        lemma = None
                        try:
                            lemma = chapter_data['lemmas'][word]
                            if lemma in lemma_cache:
                                lemma_cache[lemma].add(word)
                            else:
                                lemma_cache[lemma] = set([word])
                        except:
                            pass
                        update_item_stage_by_frequency_and_class('words',word,lemma,freq,adjusted_freq,priority_classes, timestamp,word_metadata)

                for k, freq in chapter_data['kanji_frequency'].items():
                    if trace_item is None or trace_item == k:
                        adjusted_freq = adjust_and_cap_frequency(freq, comprehension)
                        update_item_stage_by_frequency_and_class('kanjis',k,None,freq,adjusted_freq,[], timestamp,word_metadata)

            else:
                print("Warning! Missing frequency data for %s chapter %d [%s]" % (title_name, chapter, chapter_filename), file=sys.stderr)

        # insert possible manual stage updates which occurred after reading all the chapters
        item_types = ['words','kanjis']
        for item_type in item_types:
            for item in manual_events[item_type].keys():
                insert_manual_events( item_type, item )

        # check for possible word/kanji forgetting event
        item_types = ['words','kanjis']
        for item_type in item_types:
            for item in event_history[item_type].keys():
                handle_forgotten_event(item_type, item, current_timestamp)

        # finally check if lemma is known. In that case the user most likely knows
        # the more common written form
        item_types = ['words']
        for lemma, orth_forms in lemma_cache.items():
            try:
                lemma_h = event_history['words'][lemma]
                if lemma_h[-1]['s'] == STAGE_KNOWN:
                    for w in orth_forms:
                        try:
                            w_h = event_history['words'][w]
                            if not (w_h[-1]['m']['src']==SOURCE_USER):
                                # unless user dictated otherwise, the word is known
                                w_h.append( {
                                    't' : current_timestamp,
                                    's' : STAGE_KNOWN,
                                    'm' : {
                                        'src':SOURCE_ENGINE,
                                        'comment':'Known because lemma %s is also known' % lemma
                                    },
                                })
                        except:
                            pass
            except:
                pass


    # extract the current learning stage for faster lookup. Also save the history for browsing
    item_types = ['words','kanjis']
    for item_type in item_types:
        learning_data[item_type] = {}
        for item, history in event_history[item_type].items():
            learning_data[item_type][item] = {
                's' : history[-1]['s'],
                'h' : history,
                'ltf' : lifetime_freq[item_type][item],
                'lf' : learning_freq[item_type][item],
            }

    learning_data['num_unique_words'] = get_num_items('words')
    learning_data['num_unique_kanjis'] = get_num_items('kanjis')

    # total number of unique known words & kanjis
    learning_data['num_unique_known_words'] =  get_num_items('words',STAGE_KNOWN)
    learning_data['num_unique_known_kanjis'] = get_num_items('kanjis',STAGE_KNOWN)

    # total number of unique known words & kanjis
    learning_data['num_unique_pre_known_words'] =  get_num_items('words',STAGE_PRE_KNOWN)
    learning_data['num_unique_pre_known_kanjis'] = get_num_items('kanjis',STAGE_PRE_KNOWN)

    # total number of unique learning words & kanjis
    learning_data['num_unique_learning_words'] = get_num_items('words',STAGE_LEARNING)
    learning_data['num_unique_learning_kanjis'] = get_num_items('kanjis',STAGE_LEARNING)

    # total number of unique forgotten words & kanjis
    learning_data['num_unique_forgotten_words'] = get_num_items('words',STAGE_FORGOTTEN)
    learning_data['num_unique_forgotten_kanjis'] = get_num_items('kanjis',STAGE_FORGOTTEN)

    # number of new known/learning words & kanjis after reading
    learning_data['num_unique_known_words_by_reading'] = learning_data['num_unique_known_words'] - num_unique_known_words_preread
    learning_data['num_unique_known_kanjis_by_reading'] = learning_data['num_unique_known_kanjis'] - num_unique_known_kanjis_preread
    learning_data['num_unique_pre_known_words_by_reading'] = learning_data['num_unique_pre_known_words'] - num_unique_pre_known_words_preread
    learning_data['num_unique_pre_known_kanjis_by_reading'] = learning_data['num_unique_pre_known_kanjis'] - num_unique_pre_known_kanjis_preread
    learning_data['num_unique_learning_words_by_reading'] = learning_data['num_unique_learning_words'] - num_unique_learning_words_preread
    learning_data['num_unique_learning_kanjis_by_reading'] =learning_data['num_unique_learning_kanjis'] - num_unique_learning_kanjis_preread

    # these are for diagnostic purposes
    timestamp = int(time.time())
    learning_data['timestamp'] = timestamp
    learning_data['learning_settings'] = learning_settings

    learning_data['chapter_ids'] = index_of_chapter_ids

    if trace_item is None:
        o_f = open(learning_data_filename,"w",encoding="utf-8")
        json_data = json.dumps(learning_data, ensure_ascii=False)
        o_f.write(json_data)
        o_f.close()
    else:
        print(learning_data)

read_manga_data()
read_manga_metadata()

user_set_words = get_user_set_words()
user_settings = read_user_settings()
learning_settings = get_learning_settings()
chapter_comprehension = user_settings['chapter_reading_status']
initial_remembering_period = learning_settings['initial_remembering_period']*24*60*60
if initial_remembering_period > 0:
    enable_forgetting = True
learning_settings['learned_jlpt_timestamp'] /= 1000
learning_settings['learned_custom_timestamp'] /= 1000

parser = argparse.ArgumentParser(
    prog="bm_learning_engine",
    description="Bilingual Manga Learning engine",
)

subparsers = parser.add_subparsers(help='', dest='command')
parser_update = subparsers.add_parser('update', help='Update known words and kanjis')
parser_update.add_argument('--trace', type=str, default=None, help='trace changes in selected word/kanji (do not save output)')

args = vars(parser.parse_args())
cmd = args.pop('command')

update({'trace':None})

if cmd is not None:
    try:
        locals()[cmd](args)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(-1)

