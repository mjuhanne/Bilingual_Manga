from helper import *
import time
from motoko_mongo import *
from urllib.parse import unquote

google_books_file__deprecated = base_dir + "json/google_books.json"

DROP_COLLECTIONS = False

def get_mangaupdates_entry_by_title_id(id):
    res = database[COLLECTION_MANGAUPDATES].find_one({'_id':id})
    return res

############ metadata + data -> titledata + volumedata + chapterdata + settings
if DROP_COLLECTIONS:
    database[COLLECTION_TITLEDATA].drop()
    database[COLLECTION_VOLUMEDATA].drop()
    database[COLLECTION_CHAPTERDATA].drop()
    database[COLLECTION_SETTINGS].drop()


manga_data_per_id = dict()

with open(manga_data_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    _manga_data = json.loads(data)
    for entry in _manga_data:
        entry['is_book'] = False

if os.path.exists(ext_manga_data_file__deprecated):
    with open(ext_manga_data_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        _ext_manga_data = json.loads(data)
        for entry in _ext_manga_data:
            if 'is_book' not in entry:
                entry['is_book'] = False
        _manga_data += _ext_manga_data

for entry in _manga_data:
    id = entry['_id']['$oid']
    manga_data_per_id[id] = entry


def import_settings_from_metadata(metadata):
    id = metadata['_id']['$oid']
    metadata['_id'] = id
    del(metadata['manga_titles'])
    database[COLLECTION_SETTINGS].update_one({'_id':id},{'$set':metadata},upsert=True)

def import_metadata(titles, collection):

    for entry_idx, entry in enumerate(titles):
        id = entry['enid']
        td = manga_data_per_id[id]
        entry['_id'] = id        

        print(entry_idx)

        jp_data = dict()
        en_data = dict()

        title_entry = {
            '_id':id,
            'genres':entry['genres'],
            'authors' : entry['Author'],
            'artists' : entry['Artist'],
            'status' : entry['Status'],
            'search' : entry['search'],
            'lang' : {'en':en_data,'jp':jp_data}
        }
        
        timestamp = int(time.time())
        title_entry['created_timestamp'] = timestamp
        title_entry['updated_timestamp'] = timestamp

        jp_data['title'] = entry['jptit']
        en_data['title'] = entry['entit']
        if 'jpslug' in entry:
            jp_data['slug'] = entry['jpslug']
        if 'enslug' in entry:
            en_data['slug'] = entry['enslug']
        en_volumes = []
        jp_volumes = []
        en_data['volumes'] = en_volumes
        jp_data['volumes'] = jp_volumes

        if td['is_book']:
            title_entry['type'] = 'book'
        else:
            title_entry['type'] = 'manga'


        title_id = id
        for lang in ['jp','en']:
            lang_data = lang + '_data'
            vol_lang = 'vol_' + lang
            chapter_ids_label = 'ch_' + lang + 'h'
            chapter_names_label = 'ch_na' + lang
            chapter_files_label = 'ch_' + lang
            for vol_num, (vol_name, vol_data) in enumerate(td[lang_data][vol_lang].items()):
                if 'id' in vol_data:
                    vol_id = vol_data['id']
                else:
                    vol_id = 'bm_' + title_id + '_' + lang + '_' + str(vol_num)

                if lang == 'jp':
                    jp_volumes.append(vol_id)
                else:
                    en_volumes.append(vol_id)

                vol_num_pages = 0
                vol_chapters = []
                for ch_num, ch_idx in enumerate(range(vol_data['s'],vol_data['e']+1)):
                    ch_name = td[lang_data][chapter_names_label][ch_idx]
                    ch_url = td[lang_data][chapter_ids_label][ch_idx]
                    ch_id = ch_url.split('/')[0]
                    ch_files = td[lang_data][chapter_files_label][str(ch_idx+1)]
                    ch_entry = {
                        'title_id' : title_id,
                        'vol_id' : vol_id,
                        'ch_id' : ch_id,
                        'ch_num' : ch_num,
                        'ch_name' : ch_name,
                        'lang' : lang,
                        'ch_url' : ch_url,
                        'files' : ch_files,
                        'num_pages' : len(ch_files),
                        'created_timestamp' : timestamp,
                        'updated_timestamp' : timestamp
                    }
                    vol_num_pages += ch_entry['num_pages']
                    vol_chapters.append(ch_id)
                    if database[COLLECTION_CHAPTERDATA].find_one({'ch_id':ch_id}) is None:
                        database[COLLECTION_CHAPTERDATA].insert_one(ch_entry)

                vol_entry = {
                    'title_id' : title_id,
                    'vol_id' : vol_id,
                    'vol_name' : vol_name,
                    'lang' : lang,
                    'num_pages' : vol_num_pages,
                    'collection' : collection,
                    'chapters' : vol_chapters,
                    'created_timestamp' : title_entry['created_timestamp'],
                    'updated_timestamp' : title_entry['updated_timestamp']
                }
                if vol_num == 0:
                    if lang == 'jp':
                        vol_entry['cover'] = entry['coverjp']
                        vol_entry['syn'] = td['syn_jp']
                        vol_entry['release'] = entry['Release']
                    else:
                        vol_entry['cover'] = entry['coveren']
                        vol_entry['syn'] = td['syn_en']
                
                database[COLLECTION_VOLUMEDATA].update_one({'vol_id':vol_id},{'$set':vol_entry},upsert=True)


        database[COLLECTION_TITLEDATA].update_one({'_id':id},{'$set':title_entry},upsert=True)

        if 'img_data' in td:
            img_corr_entry = td['img_data']
            database[COLLECTION_IMAGE_CORRESPONDENCE_DATA].update_one({'_id':id},{'$set':img_corr_entry},upsert=True)


if os.path.exists(ext_manga_metadata_file__deprecated):
    with open(ext_manga_metadata_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        titles = json.loads(data)
        import_metadata(titles, "User")

with open(manga_metadata_file__deprecated,"r",encoding="utf-8") as f:
    data = f.read()
    metadata = json.loads(data)
    titles = metadata[0]['manga_titles']
    import_metadata(titles, "bm")
    import_settings_from_metadata(metadata[0])

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
        database[COLLECTION_MANGAUPDATES].insert_one(entry)
    else:
        metadata = get_metadata_by_title_id(id)
        #print("Mangaupdates: Skipping existing %s:%s / %s" % (id,metadata['entit'],metadata['jptit']))


########### user data
if DROP_COLLECTIONS:
    database[COLLECTION_USERDATA].drop()

if os.path.exists(user_data_file__deprecated):
    with open(user_data_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        user_data = json.loads(data)
        user_data['user_id'] = DEFAULT_USER_ID
        if database[COLLECTION_USERDATA].find_one({'user_id':user_data['user_id']}) is None:
            database[COLLECTION_USERDATA].insert_one(user_data)
else:
    print("No user data file %s found!" % user_data_file__deprecated)


########## google books matches

if DROP_COLLECTIONS:
    database[COLLECTION_GOOGLE_BOOKS_VOLUMEDATA].drop()

if os.path.exists(google_books_file__deprecated):
    with open(google_books_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            if database[COLLECTION_GOOGLE_BOOKS_VOLUMEDATA].find_one({'_id':id}) is None:
                item['_id'] = id
                item['google_book_id'] = item['id']
                del(item['id'])
                database[COLLECTION_GOOGLE_BOOKS_VOLUMEDATA].insert_one(item)
else:
    print("Existing google_books.json not found")

####### user set words

if DROP_COLLECTIONS:
    database[COLLECTION_USER_SET_WORDS].drop()

if os.path.exists(user_set_word_ids_file__deprecated):
    with open(user_set_word_ids_file__deprecated,"r",encoding="utf-8") as f:
        data = f.read()
        user_set_words = json.loads(data)
        print("Writing %d word entries" % len(user_set_words))
        for word_id, word_history in user_set_words.items():
            w_data = {'user_id':DEFAULT_USER_ID,'wid':word_id,'history':word_history}
            if database[COLLECTION_USER_SET_WORDS].find_one({'user_id':DEFAULT_USER_ID, 'wid':word_id}) is None:
                database[COLLECTION_USER_SET_WORDS].insert_one(w_data)
        print("Done!")
else:
    print("No user set words file %s found!" % user_set_word_ids_file__deprecated)

