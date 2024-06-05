from jmdict import get_jmdict_pos_code
from jp_parser_structs import *
from helper import full_width_numeric_characters, full_width_alpha_characters

def is_all_alpha(word):
    if all(c in full_width_alpha_characters for c in word):
        return True
    if word.isascii() and word.isalnum():
        return True
    return False

def is_all_numeric(word):
    if all(c in full_width_numeric_characters for c in word):
        return True
    if word.isascii() and word.isalnum():
        return True
    return False

