from jp_parser_helper import jmdict_particle_class
from helper import *

_user_settings = dict()
_learning_settings = dict()
_counter_word_ids = dict()

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


def get_stage_by_frequency_and_class(item_type, freq, class_list):
    if item_type == 'words':
        if _learning_settings['always_know_particles']:
            if jmdict_particle_class in class_list:
                return STAGE_KNOWN
            
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

