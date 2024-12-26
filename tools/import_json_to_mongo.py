from helper import *
import time
from br_mongo import *
from urllib.parse import unquote

custom_lang_analysis_file = base_dir + 'json/custom_lang_analysis.json'
google_books_file = base_dir + "json/google_books.json"

DROP_COLLECTIONS = True

def get_metadata_by_title_id(id):
    res = database[BR_METADATA].find_one({'_id':id})
    return res

def get_data_by_title_id(id):
    res = database[BR_DATA].find_one({'_id':id})
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
    if database[BR_SETTINGS].find_one({'_id':id}) is None:
        metadata['_id'] = id
        del(metadata['manga_titles'])
        database[BR_SETTINGS].insert_one(metadata)

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
        if get_metadata_by_title_id(id) is None:
            database[BR_METADATA].insert_one(entry)
        else:
            pass
            #print("Metadata: Skipping existing %s:%s / %s" % (id,entry['entit'],entry['jptit']))

with open(ext_manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    titles = json.loads(data)
    import_metadata(titles, False)

with open(manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    metadata = json.loads(data)
    titles = metadata[0]['manga_titles']
    import_metadata(titles, True)
    import_settings_from_metadata(metadata[0])

############## data
if DROP_COLLECTIONS:
    database[BR_DATA].drop()

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    _manga_data = json.loads(data)

with open(ext_manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    _ext_manga_data = json.loads(data)
    _manga_data += _ext_manga_data

for entry in _manga_data:
    id = entry['_id']['$oid']

    entry['_id'] = id
    if get_data_by_title_id(id) is None:
        database[BR_DATA].insert_one(entry)
    else:
        metadata = get_metadata_by_title_id(id)
        #print("Data: Skipping existing %s:%s / %s" % (id,metadata['entit'],metadata['jptit']))

############ mangaupdates

mangaupdates_file = base_dir + "json/mangaupdates.json"
ext_mangaupdates_file = base_dir + "json/ext_mangaupdates.json"

mangaupdates_entries = dict()
if os.path.exists(mangaupdates_file):
    with open(mangaupdates_file,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            mangaupdates_entries[id] = item
else:
    print("Existing mangaupdates.json not found")


if os.path.exists(ext_mangaupdates_file):
    with open(ext_mangaupdates_file,"r",encoding="utf-8") as f:
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

if os.path.exists(user_data_file):
    with open(user_data_file,"r",encoding="utf-8") as f:
        data = f.read()
        user_data = json.loads(data)
        user_data['user_id'] = DEFAULT_USER_ID
        if database[BR_USERDATA].find_one({'user_id':user_data['user_id']}) is None:
            database[BR_USERDATA].insert_one(user_data)
else:
    print("No user data file %s found!" % user_data_file)


########## google books matches

if DROP_COLLECTIONS:
    database[BR_GOOGLE_BOOKS].drop()
    #try:
    with open(google_books_file,"r",encoding="utf-8") as f:
        data = f.read()
        entries = json.loads(data)
        for id,item in entries.items():
            if database[BR_GOOGLE_BOOKS].find_one({'_id':id}) is None:
                item['_id'] = id
                item['google_book_id'] = item['id']
                del(item['id'])
                database[BR_GOOGLE_BOOKS].insert_one(item)
    #except:
    #print("Existing google_books.json not found")

