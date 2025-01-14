from mongo import *
database = client['bilingualreader']

BR_SETTINGS = "br_settings"
BR_METADATA = "br_metadata"
BR_DATA = "br_data"
BR_MANGAUPDATES = "br_mangaupdates"
BR_USERDATA = "br_userdata"
BR_LANG_SUMMARY = "br_lang_summary"
BR_CUSTOM_LANG_ANALYSIS = "br_custom_lang_analysis"
BR_CUSTOM_LANG_ANALYSIS_SUMMARY = "br_custom_lang_analysis_summary"
BR_GOOGLE_BOOKS = "br_google_books"
BR_VOL_IMPORT_METADATA = "br_vol_import_metadata"
BR_USER_SET_WORDS = "br_user_set_words"
BR_USER_LEARNING_DATA = "br_user_learning_data"
BR_USER_WORD_LEARNING_STATUS = "br_user_word_learning_status"
BR_USER_KANJI_LEARNING_STATUS = "br_user_kanji_learning_status"
BR_USER_WORD_LEARNING_HISTORY = "br_user_word_learning_history"
BR_CHAPTER_LOOKUP_TABLE = "br_chapter_lookup_table"
BR_SUGGESTED_PREREAD = "br_suggested_preread"