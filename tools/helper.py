import json
import os
import hashlib
from motoko_metadata import *
from motoko_language_data import *

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
STAGE_UNKNOWN_OR_UNFAMILIAR = 9 # a composite stage for statistics, doesn't really exist in reading

learning_stage_labels = {
    STAGE_UNKNOWN : 'unknown',
    STAGE_UNFAMILIAR : 'unfamiliar',
    STAGE_LEARNING : 'learning',
    STAGE_PRE_KNOWN : 'pre_known',
    STAGE_KNOWN : 'known',
    STAGE_FORGOTTEN : 'forgotten',
    STAGE_IGNORED : 'ignored',
    STAGE_KNOWN_OR_PRE_KNOWN : 'known_pre_known',
    STAGE_UNKNOWN_OR_UNFAMILIAR : 'unknown_unfamiliar' 
}

SOURCE_JLPT = 'jlpt'
SOURCE_CUSTOM = 'cu'
SOURCE_ANKI = 'a'
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
    SOURCE_ANKI     : 'Anki',
}

ALL_SENSES = 100

base_dir = './'

ocr_dir = base_dir + "ocr/"
ocr_uri = 'https://cdn.bilingualmanga.org/ocr/'

chapter_analysis_dir = base_dir + "lang/chapters/"
volume_analysis_dir = base_dir + "lang/volumes/"
title_analysis_dir = base_dir + "lang/titles/"

manga_metadata_file__deprecated = base_dir + "json/BM_data.manga_metadata.json"
manga_data_file__deprecated = base_dir + "json/BM_data.manga_data.json"
ext_manga_data_file__deprecated = 'json/ext.manga_data.json'
ext_manga_metadata_file__deprecated= 'json/ext.manga_metadata.json'

user_data_file__deprecated = base_dir + 'json/user_data.json'
user_set_word_ids_file__deprecated = base_dir + 'json/user_set_word_ids.json'

jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_with_waller_kanji_restrictions_path_= base_dir + "lang/jlpt-vocab/data_with_waller_restricted_kanji/"
jlpt_vocab_path =  base_dir + "lang/jlpt-vocab/data/"
jlpt_vocab_jmdict_file =  base_dir + "lang/jlpt/jlpt_vocab_jmdict.json"

manga_specific_settings_file = base_dir + "tools/manga_specific_settings.json"
counter_word_id_file = base_dir + "lang/counter_word_ids.tsv"

version_file = "json/versions.json"

with open(version_file,"r",encoding="utf-8") as f:
    _versions = json.loads(f.read())

PARSED_OCR_VERSION = 'parsed_ocr'
OCR_SUMMARY_VERSION = 'ocr_summary'
METADATA_CACHE_VERSION = 'metadata_cache'
# .. whereas older language parser works but may not have parsed all the words as efficiently
LANUGAGE_PARSER_VERSION = 'language_parser'


def get_version(version_type):
    if version_type in _versions:
        return _versions[version_type]
    raise Exception("Unknown version type '%s' !" % version_type)

_jlpt_word_jmdict_references = None
_jlpt_word_levels = None
_jlpt_word_reading_levels = None

full_width_alpha_characters = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ％"
full_width_numeric_characters = "０１２３４５６７８９"
numerics = list('〇一二三四五六七八九十百万億') + list(full_width_numeric_characters)

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
                        if has_word_katakana(kana):
                            kana = katakana_to_hiragana(kana)
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

def is_numerical(word):
    return all(c in numerics for c in word)
    
def num_cjk(word):
    count = 0
    for c in word:
        if is_cjk(c):
            count += 1
    return count

def has_cjk(word):
    return any(is_cjk(c) for c in word)

def has_numbers(word):
    return any(c in numerics for c in word)

def filter_cjk(text):
    return filter(has_cjk, text)

hira_start = int("3041", 16)
hira_end = int("3096", 16)
kata_start = int("30a1", 16)

def is_hiragana(c):
    return hira_start <= ord(c) <= hira_end

def is_hiragana_word(word):
    return all(is_hiragana(c) for c in word)

def has_word_hiragana(word):
    return any(is_hiragana(c) for c in word)

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

def katakana_to_hiragana(word):
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

# Modified stable hash function implementation from https://death.andgravity.com/stable-hashing
def get_stable_hash(thing):
    byte_digest = hashlib.md5(json.dumps(thing).encode('utf-8')).digest()
    return int.from_bytes(byte_digest)
