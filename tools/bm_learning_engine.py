# Bilingual Manga custom language analysis tool

import os
import json
import copy
import argparse
import time
import sys

# Full history is just for debugging because the resulting data set becomes quickly too large.
# Instead we keep history only when the learning stage changes
RETAIN_FULL_WORD_HISTORY = False  

AVERAGE_PAGES_PER_VOLUME = 180

STAGE_NONE = 0  # this is reserved for word ignored automatically (such as punctuation)
STAGE_UNKNOWN = 1
STAGE_UNFAMILIAR = 2
STAGE_LEARNING = 3
STAGE_PRE_KNOWN = 4
STAGE_KNOWN = 5
STAGE_FORGOTTEN = 6
STAGE_IGNORED = 7 # this is for words explicitely ignore by the user
STAGE_KNOWN_OR_PRE_KNOWN = 8 # a composite stage for statistics, doesn't really exist in reading

learning_stage_labels = {
    STAGE_UNKNOWN : 'unknown',
    STAGE_UNFAMILIAR : 'unfamiliar',
    STAGE_LEARNING : 'learning',
    STAGE_PRE_KNOWN : 'pre_known',
    STAGE_KNOWN : 'known',
    STAGE_FORGOTTEN : 'forgotten',
    STAGE_IGNORED : 'ignored',
    STAGE_KNOWN_OR_PRE_KNOWN : 'known_pre_known' 
}

SOURCE_JLPT = 'jlpt'
SOURCE_CUSTOM = 'cu'
SOURCE_LANGUAGE_REACTOR = 'lr'
SOURCE_CHAPTER = 'ch'
SOURCE_ENGINE = 'en'
SOURCE_USER = 'u'

base_dir = '../'

# input files
manga_metadata_file = base_dir + 'json/admin.manga_metadata.json'
manga_data_file = base_dir + 'json/admin.manga_data.json'

chapter_dir = base_dir + 'lang/chapters/'
title_dir = base_dir + 'lang/titles/'

jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  base_dir + "lang/jlpt/jlpt_vocab.json"

user_data_file = base_dir + 'json/user_data.json'

language_reactor_json_file = base_dir + 'lang/user/language-reactor.json'

user_known_words_file = base_dir + 'lang/user/user_known_words.csv'
user_known_kanjis_file = base_dir + 'lang/user/user_known_kanjis.csv'
user_word_occurrence_file = base_dir + 'lang/user/user_word_occurrence.tsv'
user_kanji_occurrence_file = base_dir + 'lang/user/user_kanji_occurrence.tsv'

user_set_words_file = base_dir + 'json/user_set_words.json'

# output files
learning_data_filename = base_dir + 'lang/user/learning_data.json'
output_analysis_file = base_dir + 'json/custom_lang_analysis.json'
suggested_preread_dir = base_dir + 'lang/suggested_preread/'

needed_paths = [ chapter_dir, title_dir, jlpt_kanjis_file, jlpt_vocab_file, user_data_file]
for path in needed_paths:
    if not os.path.exists(path):
        raise Exception("Required path [%s] not found!" % path)

# Up/downgrade the word frequency by chapter(volume) comprehension/effort
# i.e. if we have just skimmed through a volume without much effort (comprehension level 1-2), 
# we want to decrease virtually the number of times we have seen each word. 
# On the contrary, if we know all the words in the volume (comprehension level 5), 
# all the words will be set as known (at known threshold)
comprehension_modifier = [0, 0.1, 0.5, 1, 2]

chapter_id_to_title_id = dict()
title_name_to_id = dict()
title_chapters = dict()
chapter_id_to_chapter_number = dict()
chapter_number_to_chapter_id = dict()
title_names = dict()
title_ratings = dict()
title_rating_votes = dict()
chapter_id_to_chapter_name = dict()

chapter_comprehension = dict()

learning_data = dict()
manually_set_word_learning_stages = dict()

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

jlpt_kanjis = dict()
jlpt_words = dict()

## 

cjk_ranges = [
    (0x4E00, 0x9FAF),  # CJK unified ideographs
    (0x3400, 0x4DBF),  # CJK unified ideographs Extension A
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
]

katakana = list(
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズ"
    "セゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピ"
    "フブプヘベペホボポマミムメモャヤュユョヨラリルレロワ"
    "ヲンーヮヰヱヵヶヴヽヾ"
)


def is_cjk(c):
    return any(s <= ord(c) <= e for (s, e) in cjk_ranges)

def is_katakana_word(word):
    return all(c in katakana for c in word)


#################### Read input files #################################

with open(jlpt_kanjis_file,"r",encoding="utf-8") as f:
    jlpt_kanjis = json.loads(f.read())

with open(jlpt_vocab_file,"r",encoding="utf-8") as f:
    v = json.loads(f.read())
    jlpt_words = v['words']
    jlpt_words_parsed = v['words_parsed']
    jlpt_word_count_per_level = v['word_count_per_level']
    jlpt_word_readings = v['word_readings']
    jlpt_word_reading_reverse = v['word_reading_reverse']
    jlpt_word_level_suitable_form = v['word_level_suitable_form']
    jlpt_word_kanji_level = v['word_kanji_level']

try: 
    with open(learning_data_filename,"r",encoding="utf-8") as f:
        data = f.read()
        learning_data = json.loads(data)

        # the history information for further speculative analysis is unnecessary
        for item_type in ['words','kanjis']:
            for item in learning_data[item_type].keys():
                del learning_data[item_type][item]['h']

except Exception as e:
    print("Learning data not set! Update!")

try: 
    with open(user_set_words_file,"r",encoding="utf-8") as f:
        data = f.read()
        user_set_words = json.loads(data)
except:
    print("User set words file doesn't exist")
    user_set_words = dict()


with open(manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_metadata = json.loads(data)
    manga_titles = manga_metadata[0]['manga_titles']
    for t in manga_titles:
        title_id = t['enid']
        title_name = t['entit']
        title_names[title_id] = title_name
        title_name_to_id[title_name] = title_id

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        chapter_ids = m['jp_data']['ch_jph']
        chapter_ids = [vid.split('/')[0] for vid in chapter_ids]
        pages = m['jp_data']['ch_jp']
        title_chapters[title_id] = chapter_ids
        chapter_names = m['jp_data']['ch_najp']
        chapter_number = 1
        for cid in chapter_ids:
            chapter_id_to_title_id[cid] = title_id
            chapter_id_to_chapter_number[cid] = chapter_number
            chapter_id_to_chapter_name[cid] = chapter_names[chapter_number-1]
            chapter_number += 1

if os.path.exists(user_data_file):
    with open(user_data_file,"r") as f:
        d = f.read()
        user_data = json.loads(d)
        chapter_comprehension = user_data['chapter_reading_status']
        if 'learning_settings' in user_data:
            learning_settings = user_data['learning_settings']
            initial_remembering_period = learning_settings['initial_remembering_period']*24*60*60
            if initial_remembering_period > 0:
                enable_forgetting = True
            learning_settings['learned_jlpt_timestamp'] /= 1000
            learning_settings['learned_custom_timestamp'] /= 1000

        else:
            raise Exception("Please set the learning settings first in the Language settings screen!")
else:
    raise Exception("Please set the learning settings first in the Language settings screen!")


def get_manga_chapter_name(chapter_id):
    return title_names[chapter_id_to_title_id[chapter_id]] + '/' + str(chapter_id_to_chapter_number[chapter_id])

def get_title_id(item):
    if item in title_name_to_id:
        return title_name_to_id[item]
    if title_names.keys():
        # the item is in fact the title id
        return item
    raise Exception("unknown manga title/id %d" % item)

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


def get_stage_by_frequency(item_type, freq):
    if item_type == 'words':
        if freq >= learning_settings['known_word_threshold']:
            if learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= learning_settings['learning_word_threshold']:
            return STAGE_LEARNING
    if item_type == 'kanjis':
        if freq >= learning_settings['known_kanji_threshold']:
            if learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= learning_settings['learning_kanji_threshold']:
            return STAGE_LEARNING
    return STAGE_UNFAMILIAR


# If a word hasn't been seen after remembering_period then downgrade
# a KNOWN word/kanji to FORGOTTEN. Also PRE_KNOWN stage will be downgraded back to LEARNING
def handle_forgotten_event(item_type, item, next_timestamp):

    current_stage = event_history[item_type][item][-1]['s']
    if not enable_forgetting:
        return current_stage
    if item in unforgettable_items[item_type]:
        return current_stage
    last_timestamp = event_history[item_type][item][-1]['t']
    if current_stage == STAGE_KNOWN or current_stage == STAGE_PRE_KNOWN:
        forgot_timestamp = last_timestamp + remembering_periods[item_type][item]
        if forgot_timestamp < next_timestamp:

            forgotten_event = {
                's' : STAGE_FORGOTTEN,
                't' : forgot_timestamp,
                'm': {'src' : SOURCE_ENGINE },
            }
            days_lapsed = int(remembering_periods[item_type][item]/(24*60*60))
            if current_stage == STAGE_KNOWN:
                print("Forgot %s %s" % (item_type,item))
                forgotten_event['m']['comment'] = 'Forgot after %d days' % days_lapsed
            else:
                if item_type == 'words':
                    threshold = learning_settings['known_word_threshold']
                else:
                    threshold = learning_settings['known_kanji_threshold']
                forgotten_event['s'] = STAGE_LEARNING
                forgotten_event['m']['comment'] = 'Downgraded PRE-KNOWN to LEARNING after %d days' % days_lapsed
                learning_freq[item_type][item] = threshold - 1
                print("Downgraded %s %s back to LEARNING" % (item_type,item))
                
            event_history[item_type][item].append(forgotten_event)
            current_stage = STAGE_FORGOTTEN
    return current_stage

# insert all manual events updates (word to 'known' etc..) preceding the next event
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
                    manual_event_pointer[item_type][item] += 1
                    next_insertion_attempt = True


def update_item_stage(item_type, item, stage, timestamp, metadata ):
    global event_history, manual_events, manual_event_pointer

    new_event = {
        's' : stage,
        't' : timestamp,
        'm' : metadata
    }

    # chronologically interleave manual event updates between automatic ones if needed
    insert_manual_events( item_type, item, timestamp )

    # add the automatic stage update
    if item not in event_history[item_type]:
        event_history[item_type][item] = [new_event]
    else:
        current_stage = event_history[item_type][item][-1]['s']
        if current_stage != STAGE_IGNORED:

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


def update_item_stage_by_frequency(item_type, item, freq, adjusted_freq, timestamp, metadata ):
    if item in lifetime_freq[item_type]:
        lifetime_freq[item_type][item] += freq
        learning_freq[item_type][item] += adjusted_freq
    else:
        lifetime_freq[item_type][item] = freq
        learning_freq[item_type][item] = adjusted_freq
    stage = get_stage_by_frequency(item_type, learning_freq[item_type][item])
    update_item_stage(item_type, item, stage, timestamp, metadata)

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

                    create_manual_event(item_type, item, stage, timestamp, {'src':source} )
                    if timestamp == 0:
                        unforgettable_items[item_type].add(item)

        print("Loaded %s" % (filename))
    else:
        print("%s not found" % (filename))


# This will replay the automatic and manual learning events 
# and update the statistics for known/learning/forgotten words and kanjis
def update(args):

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
        if level >= learning_settings['jlpt_word_level']:
            create_manual_event('words',w, STAGE_KNOWN, jlpt_timestamp, {'src':SOURCE_JLPT, 'comment':'JLPT level %d' % level})
            learning_data['num_unique_jlpt_words'] += 1
            if jlpt_timestamp == 0:
                unforgettable_items['words'].add(w)
    learning_data['num_unique_jlpt_kanjis'] = 0
    for k, level in jlpt_kanjis.items():
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
        # automatic learning was disabled so we just copy the manually set status
        event_history = manual_events
    else:
        ##########  learning by reading #######

        # sort chapters chronologically by timestamp
        chapter_timestamps = {}
        for chapter_id, reading_data in chapter_comprehension.items():
            if reading_data['status'] != 'Read':
                continue

            if 'completion_timestamp' not in reading_data:
                print("Warning! Skipping " + get_manga_chapter_name(chapter_id) + " because no completion timestamp set!")
                continue

            chapter_timestamps[chapter_id] = reading_data['completion_timestamp']
        sorted_chapters = dict(sorted(chapter_timestamps.items(), key=lambda x:x[1]))
        
        for chapter_id, timestamp_ms in sorted_chapters.items():

            timestamp = int(timestamp_ms/1000)

            reading_data = chapter_comprehension[chapter_id]

            comprehension = reading_data['comprehension']

            title_id = chapter_id_to_title_id[chapter_id]
            title_name = title_names[title_id]
            chapter_filename = chapter_dir + chapter_id + ".json"
            chapter = chapter_id_to_chapter_number[chapter_id]

            print(" * Read %s [chapter %d]" % (title_name, chapter))

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

                for w, freq in chapter_data['word_frequency'].items():
                    adjusted_freq = adjust_and_cap_frequency(freq, comprehension)
                    update_item_stage_by_frequency('words',w,freq,adjusted_freq,timestamp,word_metadata)

                for k, freq in chapter_data['kanji_frequency'].items():
                    adjusted_freq = adjust_and_cap_frequency(freq, comprehension)
                    update_item_stage_by_frequency('kanjis',k,freq,adjusted_freq,timestamp,word_metadata)

            else:
                print(" ! Warning! Missing frequency data for %s chapter %d [%s]" % (title_name, chapter, chapter_filename))

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

    o_f = open(learning_data_filename,"w",encoding="utf-8")
    json_data = json.dumps(learning_data, ensure_ascii=False)
    o_f.write(json_data)
    o_f.close()


# Read a data set of words/kanjis (a title or a chapter) and gather statistics 
# (number of unique word or kanjis per learning stage. Statistics are gathered pre- and post-read)
# item_type = 'words' or 'kanjis'
# unique: True (gather statistics for only unique words/kanjis). False (calculate total number of occurrences)
def read_dataset(data_set, item_type, learning_dataset, retain_changes=False, save_changes_for_these_stages=[]):

    known_dataset = learning_dataset[item_type]

    if item_type == 'words':
        title_data_set = data_set['word_frequency']
        known_threshold = learning_settings['known_word_threshold']
    else:
        title_data_set = data_set['kanji_frequency']
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

    saved_items = dict()
    for stage in save_changes_for_these_stages:
        saved_items[stage] = []

    for w,freq in title_data_set.items():

        if w in known_dataset:
            l_freq = known_dataset[w]['lf'] # learning phase occurrence
            l_stage = known_dataset[w]['s']
        else:
            l_freq = 0
            l_stage = STAGE_UNKNOWN
        old_stage = l_stage

        # counters pre-read
        total_counter[l_stage] += freq
        unique_counter[l_stage] += 1

        if l_stage != STAGE_KNOWN:
            # this is a word/kanji not (fully) known after started reading..
            if learning_settings['automatic_learning_enabled']:
                l_freq = l_freq + freq
                l_stage = get_stage_by_frequency(item_type, l_freq)
                if l_stage == STAGE_KNOWN:
                    # we learned this word/kanji during reading and so rest
                    # of the occurrences are considered to be 'known'
                    total_counter[l_stage] += known_threshold
                    freq = l_freq - known_threshold

        # counters post-read
        total_post_read_counter[l_stage] += freq
        unique_post_read_counter[l_stage] += 1

        if retain_changes:
            if w not in known_dataset:
                known_dataset[w] = {}
            known_dataset[w]['s'] = l_stage
            known_dataset[w]['lf'] = l_freq 

        if old_stage != l_stage:
            if l_stage in save_changes_for_these_stages:
                saved_items[l_stage].append(w)

    analysis = dict()
    for analysis_type in ['total_statistics','unique_statistics']:
        if analysis_type == 'unique_statistics':
            counter = unique_counter
            post_read_counter = unique_post_read_counter
            if item_type == 'words':
                num_all = data_set['num_unique_words']
            else:
                num_all = data_set['num_unique_kanjis']
        else:
            counter = total_counter
            post_read_counter = total_post_read_counter
            if item_type == 'words':
                num_all = data_set['num_words']
            else:
                num_all = data_set['num_kanjis']

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

    analysis['saved'] = saved_items

    return analysis

# This calculates known/unknown word and kanji distribution of chapter/title
# for each JLPT level (1-5). 
# Additional categories: 0 = non-Katakana non-JLPT word, 6=Katakana non-JLPT word
def fetch_known_jlpt_levels(data, calc, total):

    ## WORDS
    jlpt_word_count_per_level = [ 0 for i in range(7) ]
    for w,c in data['word_frequency'].items():
        if w in learning_data['words']:
            s = learning_data['words'][w]['s']
            if s == STAGE_KNOWN or s == STAGE_PRE_KNOWN:
                if w in jlpt_words:
                    level = jlpt_words[w]
                else:
                    if w in jlpt_word_reading_reverse:
                        rw = jlpt_word_reading_reverse[w]

                        if len(rw)==1:
                            w = rw[0]
                            level = jlpt_words[w]
                        else:
                            # ambigous (too many homonymous readings). Assume non-jlpt word
                            if is_katakana_word(w):
                                level = 6
                            else:
                                level = 0
                    else:
                        # non-jlpt word
                        if is_katakana_word(w):
                            level = 6
                        else:
                            level = 0
                if total:
                    jlpt_word_count_per_level[level] += c
                else:
                    jlpt_word_count_per_level[level] += 1

    total_w = calc['words']['num_all']
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
    
    analysis['total_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['total_statistics']['words']['pct_known_pre_known'],1)
    analysis['unique_statistics']['words']['pct_known_pre_known'] = \
        round(analysis['unique_statistics']['words']['pct_known_pre_known'],1)
    
    return analysis, data_set


# Analyze all titles
def analyze_titles():

    print("Analyzing comprehension for all manga titles")

    analysis = dict()

    for title_id, title_name in title_names.items():

        title_filename = title_dir + title_id + ".json"

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
        tid = chapter_id_to_title_id[chapter_id]
        if tid == title_id:
            chapter = chapter_id_to_chapter_number[chapter_id]
            if chapter > highest_read_chapter:
                highest_read_chapter = chapter
                highest_read_chapter_id = chapter_id

    if highest_read_chapter == 0:
        highest_read_chapter_id = title_chapters[title_id][0]
    else:
        if highest_read_chapter == len(title_chapters[title_id]):
            # all read
            return None
        highest_read_chapter_id = title_chapters[title_id][highest_read_chapter]

    return highest_read_chapter_id


def analyze_next_unread():

    print("Analyzing comprehension for the next unread chapters/volumes")
    analysis = dict()
    next_unread_chapter = dict()

    for title_id, title_name in title_names.items():

        chapter_id = get_next_unread_chapter(title_id)
        if chapter_id is None:
            print(" * %s already read" % title_name)
            continue

        chapter = chapter_id_to_chapter_number[chapter_id]
        next_unread_chapter[title_id] = chapter

        chapter_filename = chapter_dir + chapter_id + ".json"

        if not os.path.exists(chapter_filename):
            print("%s chapter %d not found! [%s]" % (title_name, chapter, chapter_filename))
            continue

        chapter_analysis, chapter_data = load_and_analyze_dataset(chapter_filename)

        analysis[title_id] = chapter_analysis

    return analysis


def suggest_preread(args):

    target_title_id = get_title_id(args['title'])

    print("Analyzing suggested pre-reading for" + title_names[target_title_id])

    index_title_filename = title_dir + target_title_id + ".json"
    o_f = open(index_title_filename,"r",encoding="utf-8")
    target_title_data = json.loads(o_f.read())
    o_f.close()

    # first read the target title and save analysis before pre-reading
    target_word_analysis = read_dataset(target_title_data, "words", learning_data, save_changes_for_these_stages=[STAGE_UNFAMILIAR,STAGE_LEARNING])
    #target_unique_word_analysis = w_an['unique_statistics']
    target_pct_known = target_word_analysis['total_statistics']['pct_known_pre_known']

    analysis = dict()

    for title_id, title_name in title_names.items():
        this_session_learning_data = copy.deepcopy(learning_data)

        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        num_pages = title_data['num_pages']
        num_words = title_data['num_words']

        title_analysis = dict()

        # calculate number of common weak (unfamiliar or learning) words
        cuuw = 0
        w_list = title_data['word_frequency'].keys()
        for w in target_word_analysis['saved'][STAGE_UNKNOWN]:
            if w in w_list:
                cuuw += 1
        title_analysis['num_common_unique_weak_words'] = cuuw
        if num_pages > 0:
            title_analysis['num_common_unique_weak_words_per_vol'] = int(cuuw/(num_pages/180))
        else:
            title_analysis['num_common_unique_weak_words_per_vol'] = -1


        # first read the candidate, retaining the words learned from this session
        # while analyzing how difficult this candidate series is..
        w_an = read_dataset(title_data, "words", this_session_learning_data, retain_changes=True)
        candidate_word_analysis = w_an['total_statistics']
        candidate_pct_known = candidate_word_analysis['pct_known_pre_known']
        if candidate_pct_known < target_pct_known:
            print("Skipping %s with comprehension %.1f" % (title_name,candidate_pct_known))
            continue


        # .. then analyze how much reading the candidate improved the comprehension of target manga
        w_an = read_dataset(target_title_data, "words", this_session_learning_data)
        title_analysis_words = w_an['total_statistics']
        #title_analysis_kanjis = read_dataset(target_title_data, "kanji_frequency", this_session_learning_data)

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
        else:
            points = -1

        title_analysis['improvement_pct'] = round(improvement_pct,2)
        title_analysis['relative_improvement'] = round(points,2) # in relation to the effort
        analysis[title_id] = title_analysis

    o_f = open(suggested_preread_dir + target_title_id + '.json' ,"w",encoding="utf-8")
    timestamp = int(time.time())*1000
    data = {'timestamp':timestamp, 'analysis':analysis}
    json_data = json.dumps(data)
    o_f.write(json_data)
    o_f.close()


def series_analysis_for_jlpt():

    print("Analyzing suggested reading for JLPT")

    analysis = dict()

    count = 0
    for title_id, title_name in title_names.items():

        ### TESTING
        print(title_name)
        count += 1
        #if count > 50:
        #    return

        #this_session_learning_data = copy.deepcopy(learning_data)

        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        # first read the candidate and save the words learned from this session
        # while analyzing how difficult this candidate series is..
        title_analysis = dict()
        w_an = read_dataset(title_data, "words", learning_data, save_changes_for_these_stages=[STAGE_KNOWN, STAGE_PRE_KNOWN])
        title_analysis['words'] = w_an['total_statistics']
        k_an = read_dataset(title_data, "kanjis", learning_data, save_changes_for_these_stages=[STAGE_KNOWN,STAGE_PRE_KNOWN])
        title_analysis['kanjis'] = k_an['total_statistics']
        candidate_pct_known = title_analysis['words']['pct_known_pre_known']

        num_pages = title_data['num_pages']
        num_words = title_data['num_words']

        # .. then calculate how many new JLPT words/kanjis we would have learned
        new_known_words = w_an['saved'][STAGE_KNOWN]
        new_known_words += w_an['saved'][STAGE_PRE_KNOWN]
        new_known_kanjis = k_an['saved'][STAGE_KNOWN]
        new_known_kanjis += k_an['saved'][STAGE_PRE_KNOWN]

        jlpt_points = 0
        for w in new_known_words:
            level = 0
            if w in jlpt_words:
                level = jlpt_words[w]
            else:
                if w in jlpt_word_reading_reverse:
                    rw = jlpt_word_reading_reverse[w]
                    if len(rw)>1:
                        #print("ambigous")
                        pass
                    else:
                        w = rw[0]
                        level = jlpt_words[w] + 0.5
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
        title_analysis['num_new_known_words'] = len(new_known_words)
        title_analysis['num_new_known_kanjis'] = len(new_known_kanjis)
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


parser = argparse.ArgumentParser(
    prog="bmfa",
    description="Bilingual Manga Custom Language Analyzer",
)

subparsers = parser.add_subparsers(help='', dest='command')
parser_update = subparsers.add_parser('update', help='Update known words and kanjis')

parser_analyze = subparsers.add_parser('analyze', help='Do comprehension analysis per title')

parser_suggest_preread = subparsers.add_parser('suggest_preread', help='Analyze given title and then suggest beneficial pre-read titles which increase comprehension')
parser_suggest_preread.add_argument('title', type=str, help='Target manga title')

args = vars(parser.parse_args())
cmd = args.pop('command')

#analyze(args)
update(args)
#suggest_preread({'title':'65aea95f6ef2b44925c45c5b'})

if cmd is not None:
    try:
        locals()[cmd](args)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(-1)
