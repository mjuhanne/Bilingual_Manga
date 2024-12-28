from helper import *
import time
from br_mongo import *
from urllib.parse import unquote

custom_lang_analysis_file__deprecated = base_dir + 'json/custom_lang_analysis.json'
google_books_file__deprecated = base_dir + "json/google_books.json"

DROP_COLLECTIONS = False

def get_metadata_by_title_id(id):
    res = database[BR_METADATA].find_one({'_id':id})
    return res

def get_mangaupdates_entry_by_title_id(id):
    res = database[BR_MANGAUPDATES].find_one({'_id':id})
    return res

############ metadata
if DROP_COLLECTIONS:
    database[BR_METADATA].drop()
    database[BR_SETTINGS].drop()


def import_settings_from_metadata(metadata):
    id = metadata['_id']['$oid']
    metadata['_id'] = id
    del(metadata['manga_titles'])
    database[BR_SETTINGS].update_one({'_id':id},{'$set':metadata},upsert=True)

def import_metadata(titles, from_bilingualmanga_org):
    for entry in titles:
        id = entry['enid']
        entry['_id'] = id
        if 'enslug' in entry:
            entry['enslug'] = unquote(entry['enslug'])
        if 'jpslug' in entry:
            entry['jpslug'] = unquote(entry['jpslug'])
        entry['from_bilingualmanga_org'] = from_bilingualmanga_org
        if from_bilingualmanga_org:
            entry['is_book'] = False
        else:
            if 'is_book' not in entry:
                entry['is_book'] = False
        database[BR_METADATA].update_one({'_id':id},{'$set':entry},upsert=True)

with open(ext_manga_metadata_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    titles = json.loads(data)
    import_metadata(titles, False)

with open(manga_metadata_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    metadata = json.loads(data)
    titles = metadata[0]['manga_titles']
    import_metadata(titles, True)
    import_settings_from_metadata(metadata[0])

############## data
if DROP_COLLECTIONS:
    database[BR_DATA].drop()

with open(manga_data_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    _manga_data = json.loads(data)
    for entry in _manga_data:
        entry['is_book'] = False

with open(ext_manga_data_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    _ext_manga_data = json.loads(data)
    for entry in _ext_manga_data:
        if 'is_book' not in entry:
            entry['is_book'] = False
    _manga_data += _ext_manga_data

for entry in _manga_data:
    id = entry['_id']['$oid']

    entry['_id'] = id
    database[BR_DATA].update_one({'_id':id},{'$set':entry},upsert=True)

############ mangaupdates

mangaupdates_file__deprecated = base_dir + "json/mangaupdates.json"
ext_mangaupdates_file__deprecated = base_dir + "json/ext_mangaupdates.json"

mangaupdates_entries = dict()
if os.path.exists(mangaupdates_file__deprecated):
    with open(mangaupdates_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            mangaupdates_entries[id] = item
else:
    print("Existing mangaupdates.json not found")


if os.path.exists(ext_mangaupdates_file__deprecated):
    with open(ext_mangaupdates_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        ext_entries = json.loads(data)
        for id,item in ext_entries.items():
            #if item['series_id'] != -1:
            mangaupdates_entries[id] = item
else:
    print("Existing ext_mangaupdates.json not found")

for id, entry in mangaupdates_entries.items():
    if get_mangaupdates_entry_by_title_id(id) is None:
        entry['_id'] = id
        database[BR_MANGAUPDATES].insert_one(entry)
    else:
        metadata = get_metadata_by_title_id(id)
        #print("Mangaupdates: Skipping existing %s:%s / %s" % (id,metadata['entit'],metadata['jptit']))


########### user data
if DROP_COLLECTIONS:
    database[BR_USERDATA].drop()

if os.path.exists(user_data_file__deprecated):
    with open(user_data_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        user_data = json.loads(data)
        user_data['user_id'] = DEFAULT_USER_ID
        if database[BR_USERDATA].find_one({'user_id':user_data['user_id']}) is None:
            database[BR_USERDATA].insert_one(user_data)
else:
    print("No user data file %s found!" % user_data_file__deprecated)


########## google books matches

if DROP_COLLECTIONS:
    database[BR_GOOGLE_BOOKS].drop()

if os.path.exists(google_books_file__deprecated):
    with open(google_books_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            if database[BR_GOOGLE_BOOKS].find_one({'_id':id}) is None:
                item['_id'] = id
                item['google_book_id'] = item['id']
                del(item['id'])
                database[BR_GOOGLE_BOOKS].insert_one(item)
else:
    print("Existing google_books.json not found")

####### user set words

if DROP_COLLECTIONS:
    database[BR_USER_SET_WORDS].drop()

if os.path.exists(user_set_word_ids_file__deprecated):
    with open(user_set_word_ids_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        user_set_words = json.loads(data)
        print("Writing %d word entries" % len(user_set_words))
        for word_id, word_history in user_set_words.items():
            w_data = {'user_id':DEFAULT_USER_ID,'wid':word_id,'history':word_history}
            if database[BR_USER_SET_WORDS].find_one({'user_id':DEFAULT_USER_ID, 'wid':word_id}) is None:
                database[BR_USER_SET_WORDS].insert_one(w_data)
        print("Done!")
else:
    print("No user set words file %s found!" % user_set_word_ids_file__deprecated)

####### user learning data 

learning_data_filename__deprecated = base_dir + 'lang/user/learning_data.json'

if DROP_COLLECTIONS:
    database[BR_USER_LEARNING_DATA].drop()

if os.path.exists(learning_data_filename__deprecated):
    with open(learning_data_filename__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        learning_data = json.loads(data)
        learning_data['user_id'] = DEFAULT_USER_ID
        print("Writing user learning data with %d word entries" % (len(learning_data['words'])))
        for word_id, word_history in learning_data['words'].items():
            w_data = {'user_id':DEFAULT_USER_ID,'wid':word_id,'history':word_history}
        print("Writing user learning data with %d kanji entries" % (len(learning_data['kanjis'])))
        if database[BR_USER_LEARNING_DATA].find_one({'user_id':DEFAULT_USER_ID}) is None:
            database[BR_USER_LEARNING_DATA].insert_one(learning_data)
        print("Done!")
else:
    print("No learning data file %s found!" % learning_data_filename__deprecated)

############# title id <-> volume id <-> chapter id lookup

database[BR_CHAPTER_LOOKUP_TABLE].drop()

data = database[BR_DATA].find().to_list()
for td in data:
    title_id = td['_id']
    for lang in ['jp','en']:
        lang_data = lang + '_data'
        vol_lang = 'vol_' + lang
        chapter_ids_label = 'ch_' + lang + 'h'
        chapter_names_label = 'ch_na' + lang
        for vol_num, (vol_name, vol_data) in enumerate(td[lang_data][vol_lang].items()):
            if 'id' in vol_data:
                vol_id = vol_data['id']
            else:
                vol_id = ''
            for ch_num, ch_idx in enumerate(range(vol_data['s'],vol_data['e']+1)):
                ch_name = td[lang_data][chapter_names_label][ch_idx]
                ch_id = td[lang_data][chapter_ids_label][ch_idx].split('/')[0]
                d = {
                    'title_id' : title_id,
                    'vol_id' : vol_id,
                    'vol_num' : vol_num,
                    'vol_name' : vol_name,
                    'ch_id' : ch_id,
                    'ch_num' : ch_num,
                    'ch_name' : ch_name,
                    'lang' : lang
                }
                database[BR_CHAPTER_LOOKUP_TABLE].insert_one(d)
