from motoko_metadata import *

DEFAULT_USER_ID = 0


def get_language_summary(title_id):
    summary = database[COLLECTION_LANG_SUMMARY].find_one({'_id':title_id})
    if summary is None:
        print("%s [%s] has no summary!" % (get_title_by_id(title_id),title_id))
    return summary


def get_user_set_words():
    words = database[COLLECTION_USER_SET_WORDS].find({'user_id':DEFAULT_USER_ID}).to_list()
    wid_to_history = dict()
    for w_data in words:
        wid_to_history[w_data['wid']] = w_data['history']
    return wid_to_history


def is_ocr_verified(id):
    md = get_metadata_by_title_id(id)
    if md['type'] == 'book':
        return True
    else:
        # TODO
        return False
