# Bilingual Manga custom language analysis tool

import os
import json
import copy
import argparse
import time
import sys

AVERAGE_PAGES_PER_VOLUME = 180

user_jlpt_word_level = None
user_jlpt_kanji_level = None

# This setting applies to both the known words/kanjis statistics (we consider those 
# chapters marked read in Bilingual manga) AND also speculative learning during
# when the analysis process itself 'reads' a chapter/title and gives us an estimate of the 
# average comprehension
learning_by_reading_enabled = True
known_word_threshold = 5 # default
known_kanji_threshold = 5 # default

base_dir = './'

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

# output files
known_filename = base_dir + 'lang/user/known.json'
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

chapter_id_to_title_id = dict()
title_name_to_id = dict()
title_chapters = dict()
chapter_id_to_chapter_number = dict()
chapter_number_to_chapter_id = dict()
title_names = dict()
title_ratings = dict()
title_rating_votes = dict()

chapter_comprehension = dict()

known_data = dict()

jlpt_kanjis = dict()
jlpt_words = dict()

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


with open(jlpt_kanjis_file,"r",encoding="utf-8") as f:
    data = f.read()
    jlpt_kanjis = json.loads(data)

with open(jlpt_vocab_file,"r",encoding="utf-8") as f:
    d = f.read()
    v = json.loads(d)
    jlpt_words = v['words']
    jlpt_words_parsed = v['words_parsed']
    jlpt_word_count_per_level = v['word_count_per_level']
    jlpt_word_readings = v['word_readings']
    jlpt_word_reading_reverse = v['word_reading_reverse']
    jlpt_word_level_suitable_form = v['word_level_suitable_form']
    jlpt_word_kanji_level = v['word_kanji_level']

try: 
    with open(known_filename,"r",encoding="utf-8") as f:
        data = f.read()
        known_data = json.loads(data)
except:
    print("Known words not set! Update!")

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
        for vid in chapter_ids:
            chapter_id_to_title_id[vid] = title_id
            chapter_number = chapter_ids.index(vid) + 1
            chapter_id_to_chapter_number[vid] = chapter_number
            chapter_number_to_chapter_id[(title_id,chapter_number)] = vid

if os.path.exists(user_data_file):
    with open(user_data_file,"r") as f:
        d = f.read()
        user_data = json.loads(d)
        chapter_comprehension = user_data['chapter_reading_status']
        if 'known_word_threshold' in user_data:
            known_word_threshold = user_data['known_word_threshold']
        if 'known_kanji_threshold' in user_data:
            known_kanji_threshold = user_data['known_kanji_threshold']
        if 'jlpt_word_level' in user_data:
            user_jlpt_word_level = int(user_data['jlpt_word_level'])
        if 'jlpt_kanji_level' in user_data:
            user_jlpt_kanji_level = int(user_data['jlpt_kanji_level'])
        if 'learning_by_reading_enabled' in user_data:
            learning_by_reading_enabled = int(user_data['learning_by_reading_enabled'])
else:
    print("No comprehension (user_data) file!")


def get_title_id(item):
    if item in title_name_to_id:
        return title_name_to_id[item]
    if title_names.keys():
        # the item is in fact the title id
        return item
    raise Exception("unknown manga title/id %d" % item)

def modify_freq_by_comprehension(freq, comprehension, known_threshold):
    if comprehension==5:
        # perfect comprehension for this volume/chapter -> set this word/kanji as known
        return known_threshold
    return freq*comprehension_modifier[comprehension]

def read_lang_json(filename, item_type, lang_dict):
    read_count = 0
    if os.path.exists(filename):
        with open(filename,"r",encoding="utf-8") as f:

            pass

def read_lang_list(filename, item_type, lang_dict, threshold=None, overwrite=False):
    num_known = 0
    num_recognized = 0
    line_number = 1
    if os.path.exists(filename):
        with open(filename,"r",encoding="utf-8") as f:
            if filename.split('.')[-1] == 'json':
                j = json.loads(f.read())

                # TODO: handle timestamps

                for lemma, data in j.items():
                    # scale 1-5 to occurrence threshold (5 == known threshold)
                    if 'stage' not in data:
                        raise Exception("Error in %s" % filename)
                    occ = data['stage'] * threshold / 5
                    if (occ >= threshold):
                        num_known += 1
                    else:
                        num_recognized += 1
                    if overwrite:
                        lang_dict[lemma] = occ
                    else:
                        # TODO: how should we handle many data points for single word/kanji?
                        # (automatic additive occurrence data (with threshold) vs manual known level
                        raise Exception("not yet implemented")

            else:
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
                    if len(d)>1:
                        # optional occurrance value
                        if not d[1].isnumeric():
                            raise Exception("Error in %s line %d: Occurrence value %s" % (filename, line_number, item))
                        freq = int(d[1])
                    else:
                        if threshold is None:
                            raise Exception("%s must have occurrence data" % filename)
                        freq = threshold

                    if overwrite:
                        lang_dict[item] = freq
                    else:
                        if item in lang_dict:
                            lang_dict[item] += freq
                        else:
                            lang_dict[item] = freq

                    if lang_dict[item] >= threshold:
                        num_known += 1
                    else:
                        num_recognized += 1

        print("Loaded %s with %d known and %d recognized/learning stage new %ss" % (filename,num_known,num_recognized,item_type))
    else:
        print("%s not found" % (filename))
    return num_known, num_recognized

# Update statistics for known/read words and kanjis
def update(args):

    global known_data

    known_data = dict()
    known_data['word_frequency'] = dict()
    known_data['kanji_frequency'] = dict()
    known_data['num_characters'] = 0
    known_data['num_words'] = 0
    known_data['num_kanjis'] = 0
    known_data['num_pages'] = 0

    known_data['num_unique_jlpt_words'] = 0
    if user_jlpt_word_level is not None:
        for w, level in jlpt_words.items():
            if level >= user_jlpt_word_level:
                known_data['word_frequency'][w] = known_word_threshold
                known_data['num_unique_jlpt_words'] += 1
    known_data['num_unique_jlpt_kanjis'] = 0
    if user_jlpt_kanji_level is not None:
        for k, level in jlpt_kanjis.items():
            if level >= user_jlpt_kanji_level:
                known_data['kanji_frequency'][k] = known_kanji_threshold
                known_data['num_unique_jlpt_kanjis'] += 1

    # custom list containing number of occurrences of each kanji and word (from external sources)
    num_known_w_c, num_recog_w_c = read_lang_list(user_word_occurrence_file, 'word', known_data['word_frequency'] )
    known_data['num_unique_known_words_custom'] = num_known_w_c
    known_data['num_unique_recog_words_custom'] = num_recog_w_c
    num_known_k_c, num_recog_k_c = read_lang_list(user_kanji_occurrence_file, 'kanji', known_data['kanji_frequency'] )
    known_data['num_unique_known_kanjis_custom'] = num_known_k_c
    known_data['num_unique_recog_kanjis_custom'] = num_recog_k_c

    # custom list containing a list of known kanjis and words (from external sources)
    num_known_w_c2, num_recog_w_c2 = read_lang_list(user_known_words_file, 'word', known_data['word_frequency'], threshold=known_word_threshold )
    known_data['num_unique_known_words_custom'] += num_known_w_c2
    known_data['num_unique_recog_words_custom'] += num_recog_w_c2
    num_known_k_c2, num_recog_k_c2 = read_lang_list(user_known_kanjis_file, 'kanji', known_data['kanji_frequency'], threshold=known_kanji_threshold )
    known_data['num_unique_known_kanjis_custom'] += num_known_k_c2
    known_data['num_unique_recog_kanjis_custom'] += num_recog_k_c2

    # List of known/learning words exported from Language Reactor
    num_known_w_lr, num_learning_w_lr = read_lang_list(language_reactor_json_file, 'word', known_data['word_frequency'], threshold=known_word_threshold, overwrite=True)
    known_data['num_unique_known_words_lr'] = num_known_w_lr
    known_data['num_unique_learning_words_lr'] = num_learning_w_lr

    # mid-stage calculation in order get # of new learned words by reading
    num_unique_known_words_preread = \
        known_data['num_unique_jlpt_words'] + \
        known_data['num_unique_known_words_custom'] + \
        known_data['num_unique_known_words_lr']
    num_unique_recog_words_preread = len(known_data['word_frequency']) - num_unique_known_words_preread
    num_unique_known_kanjis_preread = \
        known_data['num_unique_jlpt_kanjis'] + \
        known_data['num_unique_known_kanjis_custom']
    num_unique_recog_kanjis_preread = len(known_data['kanji_frequency']) - num_unique_known_kanjis_preread

    ##########  learning by reading
    known_data['num_unique_known_words_by_reading'] = 0
    known_data['num_unique_recog_words_by_reading'] = 0
    known_data['num_unique_known_kanjis_by_reading'] = 0
    known_data['num_unique_recog_kanjis_by_reading'] = 0

    if learning_by_reading_enabled:
        for chapter_id, reading_data in chapter_comprehension.items():

            if reading_data['status'] != 'Read':
                continue

            comprehension = reading_data['comprehension']

            title_id = chapter_id_to_title_id[chapter_id]
            title_name = title_names[title_id]
            chapter_filename = chapter_dir + chapter_id + ".json"
            chapter = chapter_id_to_chapter_number[chapter_id]

            print(" * Read %s [chapter %d]" % (title_name, chapter))

            if os.path.exists(chapter_filename):
                o_f = open(chapter_filename,"r",encoding="utf-8")
                chapter_data = json.loads(o_f.read())
                o_f.close()

                known_data['num_characters'] += chapter_data['num_characters']
                known_data['num_words'] += chapter_data['num_words']
                known_data['num_kanjis'] += chapter_data['num_kanjis']
                known_data['num_pages'] += chapter_data['num_pages']

                for w, freq in chapter_data['word_frequency'].items():
                    orig_freq = 0
                    mod_freq = modify_freq_by_comprehension(freq, comprehension, known_word_threshold)
                    if w in known_data['word_frequency']:
                        orig_freq = known_data['word_frequency'][w]
                        known_data['word_frequency'][w] += mod_freq
                    else:
                        known_data['word_frequency'][w] = mod_freq
                    if orig_freq < known_word_threshold and known_data['word_frequency'][w] >= known_word_threshold:
                        # a new learned word
                        known_data['num_unique_known_words_by_reading'] += 1

                for k, freq in chapter_data['kanji_frequency'].items():
                    orig_freq = 0
                    mod_freq = modify_freq_by_comprehension(freq, comprehension, known_kanji_threshold)
                    if k in known_data['kanji_frequency']:
                        orig_freq = known_data['kanji_frequency'][k]
                        known_data['kanji_frequency'][k] += mod_freq
                    else:
                        known_data['kanji_frequency'][k] = mod_freq
                    if orig_freq < known_kanji_threshold and known_data['kanji_frequency'][k] >= known_kanji_threshold:
                        # a new learned kanji
                        known_data['num_unique_known_kanjis_by_reading'] += 1

            else:
                print(" ! Warning! Missing frequency data for %s chapter %d [%s]" % (title_name, chapter, chapter_filename))

    known_data['num_unique_words'] = len(known_data['word_frequency'])
    known_data['num_unique_kanjis'] = len(known_data['kanji_frequency'])

    # total number of unique known words & kanjis
    known_words = [w for w,freq in known_data['word_frequency'].items() if freq >= known_word_threshold]
    known_kanjis = [k for k,freq in known_data['kanji_frequency'].items() if freq >= known_kanji_threshold]
    known_data['num_unique_known_words'] = len(known_words)
    known_data['num_unique_known_kanjis'] = len(known_kanjis)

    # total number of unique recognized words & kanjis
    known_data['num_unique_recog_words'] = known_data['num_unique_words'] - known_data['num_unique_known_words']
    known_data['num_unique_recog_kanjis'] = known_data['num_unique_kanjis'] - known_data['num_unique_known_kanjis']

    # number of new recognized words & kanjis after reading
    known_data['num_unique_recog_words_by_reading'] = known_data['num_unique_recog_words'] - num_unique_recog_words_preread
    known_data['num_unique_recog_kanjis_by_reading'] = known_data['num_unique_recog_kanjis'] - num_unique_recog_kanjis_preread

    # these are for diagnostic purposes
    timestamp = int(time.time())
    known_data['timestamp'] = timestamp
    conf = dict()
    conf['user_jlpt_word_level'] = user_jlpt_word_level
    conf['user_jlpt_kanji_level'] = user_jlpt_kanji_level
    conf['learning_by_reading_enabled'] = learning_by_reading_enabled
    conf['known_word_threshold'] = known_word_threshold
    conf['known_kanji_threshold'] = known_kanji_threshold
    known_data['configuration'] = conf 

    o_f = open(known_filename,"w",encoding="utf-8")
    json_data = json.dumps(known_data)
    o_f.write(json_data)
    o_f.close()


# item = 'word_frequency' or 'kanji_frequency'
def calculate_known_statistics(title_data, item, known_threshold, secondary_known_dataset=None, unique=False, save_unknown_items=False):
    global known_data

    if secondary_known_dataset is not None:
        known_dataset = secondary_known_dataset
    else:
        known_dataset = known_data

    an = dict()
    an['num_known'] = 0
    if save_unknown_items:
        an['unknown'] = []

    for w,freq in title_data[item].items():

        if w in known_dataset[item]:
            k_f = known_dataset[item][w]
        else:
            k_f = 0

        unknown = True
        if k_f >= known_word_threshold:
            if unique:
                an['num_known'] += 1
            else:
                an['num_known'] += freq
            unknown = False
        else:
            # this is a word/kanji not (fully) known after started reading..
            if learning_by_reading_enabled:
                if k_f + freq > known_threshold:
                    # we learned this word/kanji during reading and so rest
                    # of the occurrences are considered to be 'known'
                    known_freq_after_learning = k_f + freq - known_threshold
                    if unique:
                        an['num_known'] += 1
                    else:
                        an['num_known'] += known_freq_after_learning
                    unknown = False

        if unknown:
            if save_unknown_items:
                an['unknown'].append(w)

    if item == 'word_frequency':
        if unique:
            num_all = title_data['num_unique_words']
        else:
            num_all = title_data['num_words']
    else:
        if unique:
            num_all = title_data['num_unique_kanjis']
        else:
            num_all = title_data['num_kanjis']
    an['num_all'] = num_all

    an['num_unknown'] = num_all - an['num_known']

    if num_all > 0:
        an['pct_known'] = round(100*an['num_known'] / num_all,2)
        an['pct_unknown'] = round(100*an['num_unknown'] / num_all,1)
    else:
        an['pct_known'] = -1
        an['pct_unknown'] = -1

    return an

# This calculates known/unknown word and kanji distribution of chapter/title
# for each JLPT level (1-5). 
# Additional categories: 0 = non-Katakana non-JLPT word, 6=Katakana non-JLPT word
def fetch_known_jlpt_levels(data, calc, total):

    ## WORDS
    jlpt_word_count_per_level = [ 0 for i in range(7) ]
    for w,c in data['word_frequency'].items():
        if w in known_data['word_frequency'] and known_data['word_frequency'][w] >= known_word_threshold:
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
        if k in known_data['kanji_frequency'] and known_data['kanji_frequency'][k] >= known_kanji_threshold:
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


# Analyze all titles
def analyze_titles():

    print("Analyzing comprehension for all manga titles")

    analysis = dict()

    for title_id, title_name in title_names.items():

        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        #fetch_jlpt_levels(title_id, title_data)

        title_analysis = dict()
        #title_analysis['data'] = title_data
        title_analysis['total_statistics'] = dict()
        title_analysis['total_statistics']['words'] = calculate_known_statistics(title_data, "word_frequency", known_word_threshold, unique=False)
        title_analysis['total_statistics']['kanjis'] = calculate_known_statistics(title_data, "kanji_frequency", known_kanji_threshold, unique=False)
        title_analysis['unique_statistics'] = dict()
        title_analysis['unique_statistics']['words'] = calculate_known_statistics(title_data, "word_frequency", known_word_threshold, unique=True)
        title_analysis['unique_statistics']['kanjis'] = calculate_known_statistics(title_data, "kanji_frequency", known_kanji_threshold, unique=True)
        
        # Average tankobon volume page count is 180, but it might vary considerable by
        # manga, so to make those statistics more comparable we calculate virtual volume
        # count and use that for those variables that rely on # of volumes.
        title_data['num_virtual_volumes'] = round(title_data['num_pages'] / AVERAGE_PAGES_PER_VOLUME,2)

        fetch_known_jlpt_levels(title_data, title_analysis['total_statistics'], total=True)
        fetch_known_jlpt_levels(title_data, title_analysis['unique_statistics'], total=False)

        title_analysis['total_statistics']['words']['pct_known'] = \
            round(title_analysis['total_statistics']['words']['pct_known'],1)
        title_analysis['unique_statistics']['words']['pct_known'] = \
            round(title_analysis['unique_statistics']['words']['pct_known'],1)

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

        o_f = open(chapter_filename,"r",encoding="utf-8")
        chapter_data = json.loads(o_f.read())
        o_f.close()

        title_analysis = dict()
        title_analysis['data'] = chapter_data
        title_analysis['total_statistics'] = dict()
        title_analysis['total_statistics']['words'] = calculate_known_statistics(chapter_data, "word_frequency", known_word_threshold, unique=False)
        title_analysis['total_statistics']['kanjis'] = calculate_known_statistics(chapter_data, "kanji_frequency", known_kanji_threshold, unique=False)
        title_analysis['unique_statistics'] = dict()
        title_analysis['unique_statistics']['words'] = calculate_known_statistics(chapter_data, "word_frequency", known_word_threshold, unique=True)
        title_analysis['unique_statistics']['kanjis'] = calculate_known_statistics(chapter_data, "kanji_frequency", known_kanji_threshold, unique=True)

        del(chapter_data['word_frequency'])
        del(chapter_data['kanji_frequency'])

        title_analysis['total_statistics']['words']['pct_known'] = \
            round(title_analysis['total_statistics']['words']['pct_known'],1)
        title_analysis['unique_statistics']['words']['pct_known'] = \
            round(title_analysis['unique_statistics']['words']['pct_known'],1)

        analysis[title_id] = title_analysis

    return analysis


# frequency_type is 'word_frequency' or 'kanji_frequency'
def read_title(title_data, this_session_known_data, frequency_type, known_threshold ):

    new_known_items = []

    for w, freq in title_data[frequency_type].items():
        previous_freq = 0
        if w in this_session_known_data[frequency_type]:
            previous_freq = this_session_known_data[frequency_type][w]
            this_session_known_data[frequency_type][w] += freq
        else:
            this_session_known_data[frequency_type][w] = freq

        if previous_freq < known_threshold and this_session_known_data[frequency_type][w] >= known_threshold:
            new_known_items.append(w)

    return new_known_items


def suggest_preread(args):

    target_title_id = get_title_id(args['title'])

    print("Analyzing suggested pre-reading for" + title_names[target_title_id])

    index_title_filename = title_dir + target_title_id + ".json"
    o_f = open(index_title_filename,"r",encoding="utf-8")
    target_title_data = json.loads(o_f.read())
    o_f.close()

    # analysis before pre-reading
    target_word_analysis = calculate_known_statistics(target_title_data, "word_frequency", known_word_threshold, unique=False)
    target_unique_word_analysis = calculate_known_statistics(target_title_data, "word_frequency", known_word_threshold, unique=True, save_unknown_items=True)
    target_pct_known = target_word_analysis['pct_known']

    analysis = dict()

    for title_id, title_name in title_names.items():
        this_session_known_data = copy.deepcopy(known_data)

        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        num_pages = title_data['num_pages']
        num_words = title_data['num_words']

        # first analyze how difficult this candidate series is..
        candidate_word_analysis = calculate_known_statistics(title_data, "word_frequency", known_word_threshold, secondary_known_dataset=this_session_known_data, unique=False)
        candidate_pct_known = candidate_word_analysis['pct_known']
        if candidate_pct_known < target_pct_known:
            print("Skipping %s with comprehension %.1f" % (title_name,candidate_pct_known))
            continue

        title_analysis = dict()
        
        # calculate number of common unique unknown words
        cuuw = 0
        w_list = title_data['word_frequency'].keys()
        for w in target_unique_word_analysis['unknown']:
            if w in w_list:
                cuuw += 1
        title_analysis['num_common_unique_unknown_words'] = cuuw
        if num_pages > 0:
            title_analysis['num_common_unique_unknown_words_per_vol'] = int(cuuw/(num_pages/180))
        else:
            title_analysis['num_common_unique_unknown_words_per_vol'] = -1

        # .. then read the candidate, retaining the words learned from this session
        read_title(title_data, this_session_known_data, 'word_frequency', known_word_threshold)
        #read_title(title_data, this_session_known_data, 'kanji_frequency', known_kanji_threshold)

        # then analyze how much reading the candidate improved the comprehension of target series
        title_analysis_words = calculate_known_statistics(target_title_data, "word_frequency", known_word_threshold, secondary_known_dataset=this_session_known_data)
        #title_analysis_kanjis = calculate_known_statistics(target_title_data, "kanji_frequency", known_kanji_threshold, secondary_known_dataset=this_session_known_data)

        improvement_pct = title_analysis_words['pct_known'] - target_pct_known
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
    timestamp = int(time.time())
    data = {'timestamp':timestamp, 'analysis':analysis}
    json_data = json.dumps(data)
    o_f.write(json_data)
    o_f.close()


def series_analysis_for_jlpt():

    print("Analyzing suggested reading for JLPT")

    analysis = dict()

    for title_id, title_name in title_names.items():
        this_session_known_data = copy.deepcopy(known_data)

        title_filename = title_dir + title_id + ".json"
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()

        # first analyze how difficult this candidate series is..
        title_analysis = dict()
        #title_analysis['data'] = title_data
        title_analysis['words'] = calculate_known_statistics(title_data, "word_frequency", known_word_threshold, secondary_known_dataset=this_session_known_data, unique=False)
        title_analysis['kanjis'] = calculate_known_statistics(title_data, "kanji_frequency", known_kanji_threshold, secondary_known_dataset=this_session_known_data, unique=False)
        candidate_pct_known = title_analysis['words']['pct_known']

        num_pages = title_data['num_pages']
        num_words = title_data['num_words']

        # .. then read the candidate, retaining the words learned from this session
        new_known_words = read_title(title_data, this_session_known_data, 'word_frequency', known_word_threshold)
        new_known_kanjis = read_title(title_data, this_session_known_data, 'kanji_frequency', known_kanji_threshold)

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
    timestamp = int(time.time())
    data = {'timestamp': timestamp, 'analysis' : d}
    json_data = json.dumps(data)
    o_f.write(json_data)
    o_f.close()


if cmd is not None:
    try:
        locals()[cmd](args)
    except Exception as e:
        print(e, file=sys.stderr)
        exit(-1)
