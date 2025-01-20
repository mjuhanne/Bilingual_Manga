from mongo import *
database = mongo_client['motoko']

COLLECTION_SETTINGS = "settings"
COLLECTION_TITLEDATA = "titledata"
COLLECTION_VOLUMEDATA = "volumedata"
COLLECTION_CHAPTERDATA = "chapterdata"
COLLECTION_IMAGE_CORRESPONDENCE_DATA = "imgcorrdata"

COLLECTION_VOL_IMPORT_METADATA = "vol_import_metadata"
COLLECTION_GOOGLE_BOOKS_VOLUMEDATA = "google_books_volumedata"
COLLECTION_MANGAUPDATES = "mangaupdates"
COLLECTION_LANG_SUMMARY = "lang_summary"

COLLECTION_USERDATA = "userdata"
COLLECTION_CUSTOM_LANG_ANALYSIS = "custom_lang_analysis"
COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY = "custom_lang_analysis_summary"
COLLECTION_USER_SET_WORDS = "user_set_words"
COLLECTION_USER_LEARNING_DATA = "user_learning_data"
COLLECTION_USER_WORD_LEARNING_STATUS = "user_word_learning_status"
COLLECTION_USER_KANJI_LEARNING_STATUS = "user_kanji_learning_status"
COLLECTION_USER_WORD_LEARNING_HISTORY = "user_word_learning_history"
COLLECTION_SUGGESTED_PREREAD = "suggested_preread"
