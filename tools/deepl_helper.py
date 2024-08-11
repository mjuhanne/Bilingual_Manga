from helper import * 
import deepl
from bm_learning_engine_helper import read_user_settings

user_settings = read_user_settings()

if 'deepl_key' in user_settings:
    translator = deepl.Translator(user_settings['deepl_key'])
else:
    translator = None

def deepl_translate(text):
    if translator is not None:
        result = translator.translate_text(text, target_lang="EN-US")
        return result.text
    return ''
