from jp_parser_helper import jmdict_particle_class
from helper import *

_user_settings = dict()
_learning_settings = dict()

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
