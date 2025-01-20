from motoko_mongo import *

def get_chapter_name_by_id(id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':id})
    return res['ch_name']

def get_title_from_metadata(metadata):
    if 'en' in metadata['lang'] and metadata['lang']['en']['title'] != '':
        return metadata['lang']['en']['title'] 
    else:
        return metadata['lang']['jp']['title']

def get_title_names():
    res =  database[COLLECTION_TITLEDATA].find({},{'lang':True})
    title_names = {entry['_id']:get_title_from_metadata(entry) for entry in res}
    return title_names

def get_jp_title_names():
    res =  database[COLLECTION_TITLEDATA].find({},{'lang':True})
    jp_title_names = {entry['_id']:entry['lang']['jp']['title'] for entry in res}
    return jp_title_names

def get_title_by_id(id):
    md = get_metadata_by_title_id(id)
    return get_title_from_metadata(md)


def get_jp_title_by_id(id):
    md = get_metadata_by_title_id(id)
    return md['lang']['jp']['title']

def get_title_id_by_title_name(name):
    res = database[COLLECTION_TITLEDATA].find_one({'lang.en.title':name})
    if res is not None:
        return res['_id']
    res = database[COLLECTION_TITLEDATA].find_one({'lang.jp.title':name})
    if res is not None:
        return res['_id']
    return None

def get_title_id_by_chapter_id(id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':id})
    if res is None:
        return None
    return res['title_id']

def get_lang_by_chapter_id(id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':id})
    return res['lang']

def get_volume_data(vol_id):
    res = database[COLLECTION_VOLUMEDATA].find_one({'vol_id':vol_id})
    return res

def get_volume_and_chapter_info(title_id, lang):
    res = database[COLLECTION_TITLEDATA].aggregate(
        [
            { "$match" : {'_id':title_id}},
            { "$lookup": {'from':'volumedata','localField':'_id','foreignField':'title_id','as':'volumedata'}}
        ]
    ).to_list()
    if len(res) != 1:
        raise Exception("get_volume_and_chapter_info(%s,%s): returned %d entries" % (title_id,lang,len(res)) )
    metadata = res[0]
    if 'volumes' not in metadata['lang'][lang]:
        return [],{}
    volumes = metadata['lang'][lang]['volumes']
    volume_info_by_id = {}
    for vol_info in metadata['volumedata']:
        if vol_info['lang'] == lang:
            volume_info_by_id[vol_info['vol_id']] = vol_info
    return volumes, volume_info_by_id

def get_ordered_chapter_list_by_title(title_id, lang):
    volumes, vol_info = get_volume_and_chapter_info(title_id, lang)
    chapter_ids = []
    for vol_id in volumes:
        vol = vol_info[vol_id]
        chapter_ids += vol['chapters']
    return chapter_ids

def get_first_jp_vol_id(title_id):
    volume_ids, _ = get_volume_and_chapter_info(title_id, 'jp')
    first_vol_id = volume_ids[0]
    return first_vol_id

# index number of chapter of all volumes in the title
def get_chapter_idx_by_chapter_id(cid):
    title_id = get_title_id_by_chapter_id(cid)
    lang  = get_lang_by_chapter_id(cid)
    chapter_ids = get_ordered_chapter_list_by_title(title_id, lang)
    return chapter_ids.index(cid) + 1

# index number of the chapter in its parent volume
def get_chapter_number_by_chapter_id(id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':id})
    return res['ch_num'] + 1

def get_chapters_by_title_id(id,lang=None):
    if lang is None:
        res = database[COLLECTION_CHAPTERDATA].find({'title_id':id},{'ch_id':True}).to_list()
    else:
        res = database[COLLECTION_CHAPTERDATA].find({'title_id':id,'lang':lang},{'ch_id':True}).to_list()
    chapter_ids = [entry['ch_id'] for entry in res ]
    return chapter_ids

def get_volumes_by_title_id(id, lang=None):
    if lang is None:
        res = database[COLLECTION_VOLUMEDATA].find({'title_id':id},{'vol_id':True}).to_list()
    else:
        res = database[COLLECTION_VOLUMEDATA].find({'title_id':id,'lang':lang},{'vol_id':True}).to_list()
    volume_ids = set([entry['vol_id'] for entry in res ])
    return list(volume_ids)

def get_volume_name(vol_id):
    res = database[COLLECTION_VOLUMEDATA].find_one({'vol_id':vol_id})
    return res['vol_name']

def get_volume_number_by_volume_id(vol_id):
    vol_data = database[COLLECTION_VOLUMEDATA].find_one({'vol_id':vol_id})
    metadata = database[COLLECTION_TITLEDATA].find_one({'_id':vol_data['title_id']})
    volumes = metadata['lang'][vol_data['lang']]['volumes']
    return volumes.index(vol_id) + 1

def get_chapters_by_volume_id(vol_id):
    res = database[COLLECTION_CHAPTERDATA].find({'vol_id':vol_id},{'ch_id':True}).to_list()
    ch_ids = [entry['ch_id'] for entry in res ]
    return ch_ids

def get_volume_id_by_chapter_id(ch_id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':ch_id})
    if res is not None:
        return res['vol_id']
    return None

def get_title_id_by_volume_id(vol_id):
    res = database[COLLECTION_VOLUMEDATA].find_one({'vol_id':vol_id})
    if res is not None:
        return res['title_id']
    return None

def get_chapter_page_count(ch_id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':ch_id})
    if res is not None:
        return res['num_pages']
    return 0

def get_page_count_for_chapters(title_id):
    res = database[COLLECTION_CHAPTERDATA].find({'title_id':title_id})
    if res is not None:
        pages_count = {entry['ch_id']:entry['num_pages'] for entry in res }
        return pages_count
    return {}

    
def get_synopsis_by_title_id(title_id, lang):
    volume_ids, vol_info = get_volume_and_chapter_info(title_id, lang)
    first_vol = vol_info[volume_ids[0]]
    return first_vol['syn']

def get_synopsis(vol_id):
    vol_data = get_volume_data(vol_id)
    return vol_data['syn']

def is_book(id):
    md = get_metadata_by_title_id(id)
    return md['type'] == 'book'

def get_title_type(id):
    md = get_metadata_by_title_id(id)
    return md['type']

def get_authors(id):
    md = get_metadata_by_title_id(id)
    return md['authors']

def get_publisher(id):
    md = get_metadata_by_title_id(id)
    return md['publishers']

def get_metadata_by_title_id(id):
    return database[COLLECTION_TITLEDATA].find_one({'_id':id})


def get_chapter_files_by_chapter_id(ch_id):
    res = database[COLLECTION_CHAPTERDATA].find_one({'ch_id':ch_id})
    if res is not None:
        return res['files']
    return []


def get_title_id(item):
    title_id = get_title_id_by_title_name(item)
    if title_id is not None:
        return title_id
    
    mt = database[COLLECTION_TITLEDATA].find_one({'_id':item})
    if mt is not None:
        # the item is in fact the title id
        return item
    raise Exception("unknown manga title/id %s" % item)

def delete_title(title_id):
    database[COLLECTION_TITLEDATA].delete_one({'_id':title_id})
    database[COLLECTION_VOLUMEDATA].delete_many({'title_id':title_id})
    database[COLLECTION_CHAPTERDATA].delete_many({'title_id':title_id})
    database[COLLECTION_CUSTOM_LANG_ANALYSIS].delete_one({'_id':title_id})
    database[COLLECTION_CUSTOM_LANG_ANALYSIS_SUMMARY].delete_one({'_id':title_id})
    database[COLLECTION_GOOGLE_BOOKS_VOLUMEDATA].delete_one({'_id':title_id})
    database[COLLECTION_LANG_SUMMARY].delete_one({'_id':title_id})
    volumes = get_volumes_by_title_id(title_id)
    for vol in volumes:
        ref = database[COLLECTION_VOL_IMPORT_METADATA].find_one({'_id':vol})
        if ref is None:
            print("Vol %s: No file reference to be freed(?)" % (vol))
        else:
            print("Vol %s: Freeing reference for %s" % (vol, ref['filename']))
            database[COLLECTION_VOL_IMPORT_METADATA].delete_one({'_id':vol})
