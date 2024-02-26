import json
import os

# Other tools depend on the right format of the parsed OCR and summary files..
CURRENT_PARSED_OCR_VERSION = 3
CURRENT_OCR_SUMMARY_VERSION = 3
CURRENT_METADATA_CACHE_VERSION = 2
# .. whereas older language parser works but may not have parsed all the words as efficiently
CURRENT_LANUGAGE_PARSER_VERSION = 10

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


jmdict_parts_of_speech_list = [
    # these are our modifications.
    'non_jp_char',
    'alphanum',
    'punctuation marks 補助記号',
    # These are from JMdict. Sorted by frequency in descending order
    'noun (common) (futsuumeishi)', 
    'expressions (phrases, clauses, etc.)', 
    'adjectival nouns or quasi-adjectives (keiyodoshi)', 
    'Ichidan verb', 
    'adverb (fukushi)', 
    "nouns which may take the genitive case particle 'no'", 
    "Godan verb with 'ru' ending", "Godan verb with 'su' ending", 
    'adjective (keiyoushi)', "Godan verb with 'ku' ending", 
    'interjection (kandoushi)', "Godan verb with 'mu' ending", 
    'noun or verb acting prenominally', "Godan verb with 'u' ending", 
    'suffix', "adverb taking the 'to' particle", "'taru' adjective", 
    'suru verb - special class', 'pronoun', 'noun, used as a suffix', 
    'prefix', 'particle', 'conjunction', "Godan verb with 'tsu' ending", 
    'noun or participle which takes the aux. verb suru', 'counter', 
    'pre-noun adjectival (rentaishi)', "Godan verb with 'gu' ending", 
    'Ichidan verb - zuru verb (alternative form of -jiru verbs)', 
    'auxiliary verb', 'numeric', 'noun, used as a prefix', 
    "Godan verb with 'bu' ending", 'suru verb - included', 'auxiliary', 
    'Godan verb - Iku/Yuku special class', 
    "Nidan verb (lower class) with 'mu' ending (archaic)", 
    "'ku' adjective (archaic)", 'su verb - precursor to the modern suru', 
    'unclassified', "Yodan verb with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'ru' ending (archaic)", 
    "Nidan verb (lower class) with 'dzu' ending (archaic)", 
    "Yodan verb with 'ku' ending (archaic)", 'archaic/formal form of na-adjective', 
    'adjective (keiyoushi) - yoi/ii class', "Yodan verb with 'su' ending (archaic)", 
    "Godan verb with 'nu' ending", "Yodan verb with 'hu/fu' ending (archaic)", 
    "Godan verb with 'u' ending (special class)", 'Kuru verb - special class', 
    'Godan verb - -aru special class', 'copula', "'shiku' adjective (archaic)", 
    'irregular ru verb, plain form ends with -ri', 
    "Godan verb with 'ru' ending (irregular verb)", 
    "Yodan verb with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'hu/fu' ending (archaic)", 
    "Nidan verb (lower class) with 'ku' ending (archaic)", 
    "Nidan verb (lower class) with 'tsu' ending (archaic)", 
    'intransitive verb', "Nidan verb (lower class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'yu' ending (archaic)", 
    "Nidan verb (upper class) with 'yu' ending (archaic)", 
    'auxiliary adjective', 'irregular nu verb', 
    "Nidan verb (upper class) with 'gu' ending (archaic)", 
    "Nidan verb (lower class) with 'su' ending (archaic)", 
    "Yodan verb with 'mu' ending (archaic)", 
    "Nidan verb with 'u' ending (archaic)", 
    "Nidan verb (upper class) with 'bu' ending (archaic)", 
    "Nidan verb (lower class) with 'nu' ending (archaic)", 
    'Ichidan verb - kureru special class', 
    "Nidan verb (upper class) with 'hu/fu' ending (archaic)", 
    'verb unspecified', "Nidan verb (upper class) with 'ru' ending (archaic)", 
    "Yodan verb with 'gu' ending (archaic)", "Yodan verb with 'bu' ending (archaic)", 
    "Nidan verb (upper class) with 'ku' ending (archaic)", 
    "Nidan verb (upper class) with 'tsu' ending (archaic)", 
    "Nidan verb (lower class) with 'zu' ending (archaic)", 
    "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)", 
    'transitive verb'
]

jmdict_parts_of_speech_codes = {
'gadj-f': "noun or verb acting prenominally",
'gadj-i': "adjective (keiyoushi)",
'gadj-ix': "adjective (keiyoushi) - yoi/ii class",
'gadj-kari': "'kari' adjective (archaic)",
'gadj-ku': "'ku' adjective (archaic)",
'gadj-na': "adjectival nouns or quasi-adjectives (keiyodoshi)",
'gadj-nari': "archaic/formal form of na-adjective",
'gadj-no': "nouns which may take the genitive case particle 'no'",
'gadj-pn': "pre-noun adjectival (rentaishi)",
'gadj-shiku': "'shiku' adjective (archaic)",
'gadj-t': "'taru' adjective",
'gadv': "adverb (fukushi)",
'gadv-to': "adverb taking the 'to' particle",
'gaux': "auxiliary",
'gaux-adj': "auxiliary adjective",
'gaux-v': "auxiliary verb",
'gconj': "conjunction",
'gcop': "copula",
'gctr': "counter",
'gexp': "expressions (phrases, clauses, etc.)",
'gint': "interjection (kandoushi)",
'gn': "noun (common) (futsuumeishi)",
'gn-adv': "adverbial noun (fukushitekimeishi)",
'gn-pr': "proper noun",
'gn-pref': "noun, used as a prefix",
'gn-suf': "noun, used as a suffix",
'gn-t': "noun (temporal) (jisoumeishi)",
'gnum': "numeric",
'gpn': "pronoun",
'gpref': "prefix",
'gprt': "particle",
'gsuf': "suffix",
'gunc': "unclassified",
'gv-unspec': "verb unspecified",
'gv1': "Ichidan verb",
'gv1-s': "Ichidan verb - kureru special class",
'gv2a-s': "Nidan verb with 'u' ending (archaic)",
'gv2b-k': "Nidan verb (upper class) with 'bu' ending (archaic)",
'gv2b-s': "Nidan verb (lower class) with 'bu' ending (archaic)",
'gv2d-k': "Nidan verb (upper class) with 'dzu' ending (archaic)",
'gv2d-s': "Nidan verb (lower class) with 'dzu' ending (archaic)",
'gv2g-k': "Nidan verb (upper class) with 'gu' ending (archaic)",
'gv2g-s': "Nidan verb (lower class) with 'gu' ending (archaic)",
'gv2h-k': "Nidan verb (upper class) with 'hu/fu' ending (archaic)",
'gv2h-s': "Nidan verb (lower class) with 'hu/fu' ending (archaic)",
'gv2k-k': "Nidan verb (upper class) with 'ku' ending (archaic)",
'gv2k-s': "Nidan verb (lower class) with 'ku' ending (archaic)",
'gv2m-k': "Nidan verb (upper class) with 'mu' ending (archaic)",
'gv2m-s': "Nidan verb (lower class) with 'mu' ending (archaic)",
'gv2n-s': "Nidan verb (lower class) with 'nu' ending (archaic)",
'gv2r-k': "Nidan verb (upper class) with 'ru' ending (archaic)",
'gv2r-s': "Nidan verb (lower class) with 'ru' ending (archaic)",
'gv2s-s': "Nidan verb (lower class) with 'su' ending (archaic)",
'gv2t-k': "Nidan verb (upper class) with 'tsu' ending (archaic)",
'gv2t-s': "Nidan verb (lower class) with 'tsu' ending (archaic)",
'gv2w-s': "Nidan verb (lower class) with 'u' ending and 'we' conjugation (archaic)",
'gv2y-k': "Nidan verb (upper class) with 'yu' ending (archaic)",
'gv2y-s': "Nidan verb (lower class) with 'yu' ending (archaic)",
'gv2z-s': "Nidan verb (lower class) with 'zu' ending (archaic)",
'gv4b': "Yodan verb with 'bu' ending (archaic)",
'gv4g': "Yodan verb with 'gu' ending (archaic)",
'gv4h': "Yodan verb with 'hu/fu' ending (archaic)",
'gv4k': "Yodan verb with 'ku' ending (archaic)",
'gv4m': "Yodan verb with 'mu' ending (archaic)",
'gv4n': "Yodan verb with 'nu' ending (archaic)",
'gv4r': "Yodan verb with 'ru' ending (archaic)",
'gv4s': "Yodan verb with 'su' ending (archaic)",
'gv4t': "Yodan verb with 'tsu' ending (archaic)",
'gv5aru': "Godan verb - -aru special class",
'gv5b': "Godan verb with 'bu' ending",
'gv5g': "Godan verb with 'gu' ending",
'gv5k': "Godan verb with 'ku' ending",
'gv5k-s': "Godan verb - Iku/Yuku special class",
'gv5m': "Godan verb with 'mu' ending",
'gv5n': "Godan verb with 'nu' ending",
'gv5r': "Godan verb with 'ru' ending",
'gv5r-i': "Godan verb with 'ru' ending (irregular verb)",
'gv5s': "Godan verb with 'su' ending",
'gv5t': "Godan verb with 'tsu' ending",
'gv5u': "Godan verb with 'u' ending",
'gv5u-s': "Godan verb with 'u' ending (special class)",
'gv5uru': "Godan verb - Uru old class verb (old form of Eru)",
'gvi': "intransitive verb",
'gvk': "Kuru verb - special class",
'gvn': "irregular nu verb",
'gvr': "irregular ru verb, plain form ends with -ri",
'gvs': "noun or participle which takes the aux. verb suru",
'gvs-c': "su verb - precursor to the modern suru",
'gvs-i': "suru verb - included",
'gvs-s': "suru verb - special class",
'gvt': "transitive verb",
'gvz': "Ichidan verb - zuru verb (alternative form of -jiru verbs)",
'ggikun': "gikun (meaning as reading) or jukujikun (special kanji reading)",
'gik': "word containing irregular kana usage",
'gok': "out-dated or obsolete kana usage",
'grk': "rarely used kana form",
'gsk': "search-only kana form",
}

jmdict_adjective_class_index = jmdict_parts_of_speech_list.index('adjective (keiyoushi)')

jmdict_expression_class_index = jmdict_parts_of_speech_list.index('expressions (phrases, clauses, etc.)')

base_dir = './'

ocr_dir = base_dir + "ocr/"
ocr_uri = 'https://cdn.bilingualmanga.org/ocr/'

chapter_analysis_dir = base_dir + "lang/chapters/"
title_analysis_dir = base_dir + "lang/titles/"

user_data_file = base_dir + 'json/user_data.json'
user_set_words_file = base_dir + 'json/user_set_words.json'

manga_metadata_file = base_dir + "json/admin.manga_metadata.json"
manga_data_file = base_dir + "json/admin.manga_data.json"

jlpt_kanjis_file = base_dir + "lang/jlpt/jlpt_kanjis.json"
jlpt_vocab_file =  base_dir + "lang/jlpt/jlpt_vocab.json"

_title_names = dict()
_title_name_to_id = dict()
_chapter_id_to_title_id = dict()
_chapter_id_to_chapter_number = dict()
_chapter_id_to_chapter_name = dict()
_title_chapters = dict()
_chapter_page_count = dict()

_user_settings = dict()
_learning_settings = dict()

_jlpt_word_reading_reverse = dict()
_jlpt_words = dict()

_manga_data = dict()

def get_user_set_words():
    try: 
        with open(user_set_words_file,"r",encoding="utf-8") as f:
            data = f.read()
            user_set_words = json.loads(data)
    except:
        print("User set words file doesn't exist")
    return user_set_words

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

def get_stage_by_frequency(item_type, freq):
    if item_type == 'words':
        if freq >= _learning_settings['known_word_threshold']:
            if _learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= _learning_settings['learning_word_threshold']:
            return STAGE_LEARNING
    if item_type == 'kanjis':
        if freq >= _learning_settings['known_kanji_threshold']:
            if _learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= _learning_settings['learning_kanji_threshold']:
            return STAGE_LEARNING
    return STAGE_UNFAMILIAR

def read_user_settings():
    global _user_settings, _learning_settings
    if os.path.exists(user_data_file):
        with open(user_data_file,"r") as f:
            d = f.read()
            _user_settings = json.loads(d)
            if 'learning_settings' in _user_settings:
                _learning_settings = _user_settings['learning_settings']
            else:
                raise Exception("Please set the learning settings first in the Language settings screen!")
    else:
        raise Exception("Please set the learning settings first in the Language settings screen!")
    return _user_settings

def get_learning_settings():
    return _learning_settings

def get_jlpt_kanjis():
    with open(jlpt_kanjis_file,"r",encoding="utf-8") as f:
        jlpt_kanjis = json.loads(f.read())
    return jlpt_kanjis

def read_jlpt_word_file():
    global _jlpt_words, _jlpt_word_reading_reverse
    with open(jlpt_vocab_file,"r",encoding="utf-8") as f:
        v = json.loads(f.read())
        _jlpt_words = v['words']
        _jlpt_word_reading_reverse = v['word_reading_reverse']
        """
        jlpt_words_parsed = v['words_parsed']
        jlpt_word_count_per_level = v['word_count_per_level']
        jlpt_word_readings = v['word_readings']
        jlpt_word_reading_reverse = v['word_reading_reverse']
        jlpt_word_level_suitable_form = v['word_level_suitable_form']
        jlpt_word_kanji_level = v['word_kanji_level']
        """

def get_jlpt_words():
    return _jlpt_words

def get_jlpt_word_reverse_readings():
    return _jlpt_word_reading_reverse

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

def is_cjk(c):
    return any(s <= ord(c) <= e for (s, e) in cjk_ranges)

def has_cjk(word):
    return any(is_cjk(c) for c in word)

def filter_cjk(text):
    return filter(has_cjk, text)
