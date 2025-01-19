from jp_parser_helper import jmdict_particle_class
from helper import *
from motoko_mongo import *

_user_settings = dict()
_learning_settings = dict()
_counter_word_ids = dict()

def is_chapter_read(cid):
    chapter_comprehension = _user_settings['chapter_reading_status']

    for chapter_id, reading_data in chapter_comprehension.items():
        if chapter_id == cid:
            if reading_data['status'] == 'Read':
                return True
            if reading_data['status'] == 'Reading':
                return True
    return False

# is title (partly) read?
def is_title_read(id):
    chapter_ids = get_chapters_by_title_id(id,lang='jp')
    for cid in chapter_ids:
        if is_chapter_read(cid):
            return True

def read_user_settings():
    global _user_settings, _learning_settings

    _user_settings = database[COLLECTION_USERDATA].find_one({'user_id':DEFAULT_USER_ID})
    if _user_settings is not None:
        if 'learning_settings' in _user_settings:
            _learning_settings = _user_settings['learning_settings']
        else:
            raise Exception("Please set the learning settings first in the Language settings screen!")
    else:
        raise Exception("Please set the learning settings first in the Language settings screen!")
    return _user_settings

def get_learning_settings():
    return _learning_settings


def get_stage_by_frequency_and_class(item_type, freq, is_particle):
    if item_type == 'words':
        if _learning_settings['always_know_particles']:
            if is_particle:
                return STAGE_KNOWN
            
        if freq >= _learning_settings['known_word_threshold']:
            if _learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= _learning_settings['learning_word_threshold']:
            return STAGE_LEARNING
    elif item_type == 'kanjis':
        if freq >= _learning_settings['known_kanji_threshold']:
            if _learning_settings['automatic_graduation_to_known']:
                return STAGE_KNOWN
            else:
                return STAGE_PRE_KNOWN
        elif freq >= _learning_settings['learning_kanji_threshold']:
            return STAGE_LEARNING
    return STAGE_UNFAMILIAR

def load_counter_word_ids():
    global _counter_word_ids
    if os.path.exists(counter_word_id_file):
        with open(counter_word_id_file,"r",encoding="utf-8") as f:
            data = f.read()
            lines = data.split('\n')
            for line in lines:
                d = line.split('\t')
                if len(d)>1:
                    word_id = d[0]
                    word_id = strip_sense_from_word_id(word_id)
                    k_elem = d[1]
                    _counter_word_ids[k_elem] = word_id
    else:
        print("Counter word id file doesn't exist")


def get_possible_counter_word_id_from_word(word):
    i = 0
    while i<len(word) and is_numerical(word[i]):
        i += 1
    if i > 0:
        root_word = word[i:]
        if root_word in _counter_word_ids:
            return _counter_word_ids[root_word]
    else:
        if word[0] == '第':
            return _counter_word_ids['第']
    return None

def get_possible_counter_word_id(word_id):
    seq,_,word = get_word_id_components(word_id)
    wid = get_possible_counter_word_id_from_word(word)
    if wid is None:
        return word_id
    return wid

def get_analysis_data_for_chapter(chapter_id):
    chapter_filename = chapter_analysis_dir + chapter_id + ".json"
    if os.path.exists(chapter_filename):
        o_f = open(chapter_filename,"r",encoding="utf-8")
        chapter_data = json.loads(o_f.read())
        o_f.close()
        return chapter_data
    return None


def get_analysis_data_for_volume(volume_id):
    volume_filename = volume_analysis_dir + volume_id + ".json"
    if os.path.exists(volume_filename):
        o_f = open(volume_filename,"r",encoding="utf-8")
        volume_data = json.loads(o_f.read())
        o_f.close()
        return volume_data

    chapter_ids = get_chapters_by_volume_id(volume_id)
    if len(chapter_ids) == 1:
        # there is only 1 chapter so we can use that
        an = get_analysis_data_for_chapter(chapter_ids[0])
        if an is not None:
            an['num_chapters'] = 1
            an['num_characters_per_ch'] = [an['num_characters']]
            an['num_words_per_ch'] = [an['num_words']]
            an['num_kanjis_per_ch'] = [an['num_kanjis']]
            an['num_sentences_per_ch'] = [ an['num_sentences']]
            an['num_pages_per_ch'] = [an['num_pages']]
            return an
    return None


def get_analysis_data_for_title(title_id):
    title_filename = title_analysis_dir + title_id + ".json"
    if os.path.exists(title_filename):
        o_f = open(title_filename,"r",encoding="utf-8")
        title_data = json.loads(o_f.read())
        o_f.close()
        return title_data

    volume_ids = get_volumes_by_title_id(title_id)
    if len(volume_ids) == 1:
        # there is only 1 volume so we can use that
        return get_analysis_data_for_volume(volume_ids[0])
    return None

