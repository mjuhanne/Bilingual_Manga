import json
import os

# Other tools depend on the right format of the parsed OCR and summary files..
CURRENT_PARSED_OCR_VERSION = 3
CURRENT_OCR_SUMMARY_VERSION = 3
CURRENT_METADATA_CACHE_VERSION = 2
# .. whereas older language parser works but may not have parsed all the words as efficiently
CURRENT_LANUGAGE_PARSER_VERSION = 3

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

source_labels = {
    SOURCE_JLPT     : 'JLPT',
    SOURCE_CUSTOM   : 'Custom word/kanji list',
    SOURCE_LANGUAGE_REACTOR : 'Language Reactor',
    SOURCE_CHAPTER  : 'Chapter',
    SOURCE_ENGINE   : 'Automatic engine event',
    SOURCE_USER     : 'User set word',
}

ALL_SENSES = 100

base_dir = './'

ocr_dir = base_dir + "ocr/"
ocr_uri = 'https://cdn.bilingualmanga.org/ocr/'

chapter_analysis_dir = base_dir + "lang/chapters/"
title_analysis_dir = base_dir + "lang/titles/"

user_data_file = base_dir + 'json/user_data.json'
user_set_words_file__old = base_dir + 'json/user_set_words.json'  # deprecated
user_set_word_ids_file = base_dir + 'json/user_set_word_ids.json'


manga_metadata_file = base_dir + "json/admin.manga_metadata.json"
manga_data_file = base_dir + "json/admin.manga_data.json"

jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_with_waller_kanji_restrictions_path_= base_dir + "lang/jlpt-vocab/data_with_waller_restricted_kanji/"
jlpt_vocab_path =  base_dir + "lang/jlpt-vocab/data/"
jlpt_vocab_jmdict_file =  base_dir + "lang/jlpt/jlpt_vocab_jmdict.json"

_title_names = dict()
_title_name_to_id = dict()
_chapter_id_to_title_id = dict()
_chapter_id_to_chapter_number = dict()
_chapter_id_to_chapter_name = dict()
_title_chapters = dict()
_chapter_page_count = dict()

_jlpt_word_jmdict_references = None
_jlpt_word_levels = None
_jlpt_word_reading_levels = None

_manga_data = dict()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_user_set_words():
    try: 
        with open(user_set_word_ids_file,"r",encoding="utf-8") as f:
            data = f.read()
            return json.loads(data)
    except:
        print("User set word id file doesn't exist")
        return []

def get_chapter_name_by_id(id):
    return _chapter_id_to_chapter_name[id]

def get_title_names():
    return _title_names

def get_title_by_id(id):
    return _title_names[id]

def get_title_id_by_title_name(name):
    return _title_name_to_id[name]

def get_title_id_by_chapter_id(id):
    return _chapter_id_to_title_id[id]

def get_chapter_id_to_title_id():
    return _chapter_id_to_title_id

def get_chapter_number_by_chapter_id(id):
    return _chapter_id_to_chapter_number[id]

def get_chapters_by_title_id(id):
    return _title_chapters[id]

def get_chapter_page_count(id):
    return _chapter_page_count[id]

def read_manga_metadata():
    global _title_names, _title_name_to_id
    with open(manga_metadata_file,"r",encoding="utf-8") as f:
        data = f.read()
        manga_metadata = json.loads(data)
        manga_titles = manga_metadata[0]['manga_titles']
        for t in manga_titles:
            title_id = t['enid']
            title_name = t['entit']
            _title_names[title_id] = title_name
            _title_name_to_id[title_name] = title_id

def read_manga_data():
    global _manga_data
    global _chapter_id_to_title_id, _chapter_id_to_chapter_number, _chapter_id_to_chapter_name
    global _chapter_page_count, _title_chapters
    with open(manga_data_file,"r",encoding="utf-8") as f:
        data = f.read()
        _manga_data = json.loads(data)
        for m in _manga_data:
            title_id = m['_id']['$oid']
            chapter_ids = m['jp_data']['ch_jph']
            chapter_ids = [cid.split('/')[0] for cid in chapter_ids]
            pages = m['jp_data']['ch_jp']
            _title_chapters[title_id] = chapter_ids
            chapter_names = m['jp_data']['ch_najp']
            chapter_number = 1
            for cid in chapter_ids:
                _chapter_id_to_title_id[cid] = title_id
                _chapter_id_to_chapter_number[cid] = chapter_number
                _chapter_id_to_chapter_name[cid] = chapter_names[chapter_number-1]
                _chapter_page_count[cid] = len(pages[str(chapter_number)])
                chapter_number += 1

def get_manga_data():
    return _manga_data

def get_manga_chapter_name(chapter_id):
    return _title_names[_chapter_id_to_title_id[chapter_id]] + '/' + str(_chapter_id_to_chapter_number[chapter_id])

def get_title_id(item):
    if item in _title_name_to_id:
        return _title_name_to_id[item]
    if _title_names.keys():
        # the item is in fact the title id
        return item
    raise Exception("unknown manga title/id %d" % item)

def get_jlpt_kanjis():
    with open(jlpt_kanjis_file,"r",encoding="utf-8") as f:
        jlpt_kanjis = json.loads(f.read())
    return jlpt_kanjis


def get_jlpt_word_levels():
    global _jlpt_word_levels
    if _jlpt_word_levels is None:
        calculate_jlpt_word_levels()
    return _jlpt_word_levels

def get_jlpt_word_reading_levels():
    global _jlpt_word_reading_levels
    if _jlpt_word_reading_levels is None:
        calculate_jlpt_word_levels()
    return _jlpt_word_reading_levels

def calculate_jlpt_word_levels():
    global _jlpt_word_levels, _jlpt_word_reading_levels
    refs = get_jlpt_word_jmdict_references()
    _jlpt_word_levels = dict()
    _jlpt_word_reading_levels = dict()
    for level, seqs_per_level in refs.items():
        for seq, word_dict in seqs_per_level.items():
            for word in word_dict['kanji']:
                if word not in _jlpt_word_levels:
                    _jlpt_word_levels[word] = level
                else:
                    if _jlpt_word_levels[word] < level:
                        _jlpt_word_levels[word] = level

            for reading in word_dict['kana']:
                if reading not in _jlpt_word_reading_levels:
                    _jlpt_word_reading_levels[reading] = level
                else:
                    if _jlpt_word_reading_levels[reading] < level:
                        _jlpt_word_reading_levels[reading] = level
            

def get_jlpt_word_jmdict_references():
    global _jlpt_word_jmdict_references
    if _jlpt_word_jmdict_references is not None:
        return _jlpt_word_jmdict_references
    refs = dict()
    for level in range(1,6):
        filename = "%sn%d.csv" %(jlpt_vocab_with_waller_kanji_restrictions_path_,level)
        refs[level] = dict()
        with open(filename,"r",encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[1:]: #skip header
                d = line.split(',')

                if d[0] != '':
                    seq = int(d[0])
                    if seq not in refs[level]:
                        refs[level][seq] = {'kanji':[],'kana':[]}
                    kana = d[2]
                    kana = kana.replace('"','')
                    if kana != '':
                        if kana not in refs[level][seq]['kana']:
                            refs[level][seq]['kana'].append(kana)

                    kanji = d[1]
                    kanji = kanji.replace('"','')
                    if kanji != '':
                        if kanji not in refs[level][seq]['kanji']:
                            refs[level][seq]['kanji'].append(kanji)
                    
    _jlpt_word_jmdict_references = refs
    return refs

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

def is_katakana_word(word):
    return all(c in katakana for c in word)

def has_word_katakana(word):
    return any(c in katakana for c in word)

def is_cjk(c):
    return any(s <= ord(c) <= e for (s, e) in cjk_ranges)

def has_cjk(word):
    return any(is_cjk(c) for c in word)

def filter_cjk(text):
    return filter(has_cjk, text)

hira_start = int("3041", 16)
hira_end = int("3096", 16)
kata_start = int("30a1", 16)

hira_to_kata = dict()
kata_to_hira = dict()
for i in range(hira_start, hira_end+1):
    hira_to_kata[chr(i)] = chr(i-hira_start+kata_start)
    #print(chr(i), chr(i-hira_start+kata_start))    
for hira,kata in hira_to_kata.items():
    kata_to_hira[kata] = hira

def hiragana_to_katakana(word):
    katakana = ''
    for chr in word:
        if chr in hira_to_kata:
            katakana += hira_to_kata[chr]
        else:
            katakana += chr
    return katakana

def katagana_to_hiragana(word):
    hiragana = ''
    for chr in word:
        if chr in kata_to_hira:
            hiragana += kata_to_hira[chr]
        else:
            hiragana += chr
    return hiragana

def get_seq_and_word_from_word_id(word_id):
    sw = word_id.split(':')
    word = sw[1]
    seq = sw[0].split('/')[0]
    return int(seq),word

def get_word_id_components(word_id):
    sw = word_id.split(':')
    word = sw[1]
    ss = sw[0].split('/')
    seq = int(ss[0])
    if len(ss) > 1:
        sense = int(ss[1])
    else:
        sense = ALL_SENSES
    return seq,sense,word

def strip_sense_from_word_id(word_id):
    seq,word = get_seq_and_word_from_word_id(word_id)
    return str(seq) + ':' + word
