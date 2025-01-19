import json
import os
from helper import * 
import argparse
import time
from book2bm_helper import *
from book2bm_epub_helper import *
from book2bm_txt_helper import *
from google_books_tools import get_google_books_entry, search_records_and_select_one, clean_google_books_title, match_googleid, is_title_ignored_for_google_books, ignore_google_book_matching_for_title, match_googleid
from jp_parser import *
from bm_ocr_processor import do_process_title, parsed_ocr_dir
from bm_lang_summary import calculate_summary_for_title, calculate_averages
from bm_analyze import analyze as individual_analysis

default_collection = "User"

collection_file = "json/collections.json"
collections = {}
if os.path.exists(collection_file):
    with open(collection_file,"r") as f:
        data = json.loads(f.read())
        collections = data['collections']
else:
    collections = {'User':{'path':'/mnt/Your/Book/Directory'}}
    with open(collection_file,"w") as f:
        f.write(json.dumps({'version':1,'collections':collections}))


file_list_cache = None
default_book_path = '/mnt/Your/Book/Directory'

verbose = False
verbose_update = True

ask_confirmation_for_new_titles = True
ask_confirmation_for_new_volumes = True
ask_confirmation_for_new_chapters = True
refresh_google_books_data = False
ask_google_books_match_confirmation = True
parse_chapters_automatically = True
process_aozora_books_initially_as_one_chapter = True
check_for_orphan_volumes = True

titles = dict()

parser = argparse.ArgumentParser(
    prog="books2bm",
    description="Import books to Motoko.",
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_import = subparsers.add_parser('scan', help='Scan and import all titles with placeholder metadata and process OCR files')
parser_import.add_argument('--force', '-f', action='store_true', help='Force import')
parser_import.add_argument('--collection', '-c', type=str, default=default_collection, help='Scan from selected collection (defined in json/collections.json)')
parser_import.add_argument('--source_dir', '-src', type=str, default=None, help='Explicit source directory for scanning. If set then collection name is set to "Other"')
parser_import.add_argument('--simulate', '-s', action='store_true', help='Scan only (do not create new OIDs or import)')
parser_import.add_argument('--refresh_metadata', '-rm', action='store_true', help='Refresh metadata from Google books')
parser_import.add_argument('--automatic', '-a', action='store_true', help="Do not ask for confirmation for adding titles/volumes/chapters or Google Books matching")
parser_import.add_argument('--only_epub', '-oe', action='store_true', help="Process only epubs")
parser_import.add_argument('--only_txt', '-ot', action='store_true', help="Process only txt files")
parser_import.add_argument('-v', '--verbose', action='store_true', help='Verbose')
parser_import.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

parser_show = subparsers.add_parser('show', help='Show title info)')
parser_show.add_argument('title_id', type=str, default=None, help='Title id')

parser_remove = subparsers.add_parser('remove', help='Remove given title)')
parser_remove.add_argument('title_id', type=str, default=None, help='Title id')

parser_remove = subparsers.add_parser('reimport', help='Re-import a title/volume')
parser_remove.add_argument('title_id', type=str, default=None, help='Title or volume id')

parser_search = subparsers.add_parser('search', help='Search title/chapter_ids with given keyword')
parser_search.add_argument('-v', '--verbose', action='store_true', help='Show all subdirectory OIDs as well')
parser_search.add_argument('keyword', type=str, default=None, help='Keyword')

parser_set_google_book_id = subparsers.add_parser('set_google_book_id', help='Bind title with Google Books ID and update metadata')
parser_set_google_book_id.add_argument('title_id', type=str, default=None, help='Title id')
parser_set_google_book_id.add_argument('google_book_id', type=str, help='Google Book Id')


args = vars(parser.parse_args())

if 'verbose' in args:
    verbose = args['verbose']

if verbose:
    print("Args: ",args)

j = 0

def get_file_listing(root_path):
    global file_list_cache
    items = []
    if file_list_cache is not None:
        for item in file_list_cache:
            if item[:len(root_path)] == root_path:
                p = item[len(root_path):]
                if '/' in p:
                    # omit sub-items for now
                    p = p.split('/')[0] + '/'
                pl = p.lower()
                if p not in items:
                    items.append(p)
    else:
        for f_name in os.listdir(root_path):
            if os.path.isdir(root_path + f_name):
                items.append(f_name + '/')
            else:
            #elif '.epub' in fl or '.txt' in fl:
                items.append(f_name)
    return items

scanned_file_count = 0
scanned_dir_count = 0
ignored_count_by_ext = dict()
def recursive_scan(args, root_path, filtered_file_type=None, recursion_depth=0, recursion_depth_str=''):
    global scanned_dir_count, scanned_file_count, ignored_count_by_ext

    sub_items = get_file_listing(root_path)
    if filtered_file_type is not None:
        sub_items = [f_name for f_name in sub_items if filtered_file_type in f_name.lower()]
    sub_items.sort()

    for sub_item_idx, sub_item in enumerate(sub_items):
        recursion_depth_str_iter = recursion_depth_str + ' [%d/%d]' % (sub_item_idx+1,len(sub_items))

        new_path = root_path + sub_item
        if new_path[-1] == '/':
            scanned_dir_count += 1
            # is path
            if len(sub_item)>2 and sub_item[:2] == '__':
                # skip
                pass
            else:
                recursive_scan(args, new_path, 
                    filtered_file_type=filtered_file_type, 
                    recursion_depth = recursion_depth+1,
                    recursion_depth_str=recursion_depth_str_iter
                )
        else:
            scanned_file_count += 1
            vol_info = None
            title = None
            ext = sub_item.split('.')[-1].lower()
            if ext == 'epub':
                title, vol_info = get_info_from_epub_file_name(root_path,sub_item)
            elif ext == 'txt':
                title, vol_info = get_info_from_txt_file_name(root_path,sub_item)
            else:
                print("Ignoring ",new_path)
                if ext not in ignored_count_by_ext:
                    ignored_count_by_ext[ext] = 1
                else:
                    ignored_count_by_ext[ext] += 1
            if title is not None and vol_info is not None:
                vol_info['verbose_recursion_depth'] = recursion_depth_str_iter
                process_file(args, title, vol_info)
            #else:
            #    print("Missing file name processor: %s" % sub_item)
            #    pass
    pass

def create_new_title(title, vol_info, simulate=False):

    title_id = create_oid(title, "title", ask_confirmation=(ask_confirmation_for_new_titles and not simulate))
    if title_id is None:
        # oid not found and adding new one was manually skipped
        return None

    # normalize the title just in case
    # It can be in Unicode composed form (i.e. で)
    # or decomposed (i.e. て　+　゙	 mark).  The strings are stored in composed form
    clean_title = ud.normalize('NFC',title)

    print("Creating new title [%s]: %s " % (title_id, title))

    t_metadata = dict()
    t_metadata['created_timestamp'] = int(time.time())

    t_metadata['lang'] = {'jp':{},'en':{}}

    if has_cjk(clean_title) or has_word_hiragana(clean_title) or has_word_katakana(clean_title):
        t_metadata['lang']['jp']['title'] = clean_title
        t_metadata['lang']['en']['title'] = ''
    else:
        t_metadata['lang']['jp']['title'] = clean_title
        t_metadata['lang']['en']['title'] = clean_title
    t_metadata['title_from_filename'] = vol_info['title_from_filename']

    t_metadata['genres'] = []
    t_metadata['publisher'] = vol_info['publisher']

    t_metadata['authors'] = []
    if 'author' in vol_info:
        t_metadata['authors'].append(vol_info['author'])

    t_metadata['artists'] = []

    t_metadata['status'] = 'Completed' # assumption
    t_metadata['search'] = ''
    t_metadata['type'] = 'book'

    if not simulate:
        save_metadata(title_id, t_metadata, False)
    return title_id, t_metadata

def update_metadata_from_google_books(t_metadata, vol_data, gb, force=False):
    vi = gb['volumeInfo']
    if '訳)' in t_metadata['lang']['jp']['title']:
        t_metadata['lang']['jp']['title'] = clean_google_books_title(vi['title']) + " (%s訳)" % t_metadata['translator']
    else:
        t_metadata['lang']['jp']['title'] = clean_google_books_title(vi['title'])

    if t_metadata['lang']['en']['title'] == '' or force:
        if 'en_title_deepl' in gb:
            t_metadata['lang']['en']['title'] = gb['en_title_deepl']
            t_metadata['title_is_translated'] = True

    if 'categories' in vi:
        t_metadata['genres'] = vi['categories']

    if ('publisher' not in t_metadata or force) and 'publisher' in vi:
        t_metadata['publisher'] = vi['publisher']

    if 'authors' in vi:
        t_metadata['authors'] = vi['authors']

    if vol_data['release'] == '' or force:
        try:
            vol_data['release'] = int(vi['publishedDate'].split('-')[0])
        except:
            pass

    if 'en_synopsis_deepl' in gb:
        vol_data['syn_en_deepl'] = gb['en_synopsis_deepl']
    vol_data['syn'] = gb['volumeInfo']['description']

def process_volume(args, title_id, title, vol_info, vol_id=None):
    t_metadata = get_metadata_by_title_id(title_id)

    vol_data = {
        'chapters':[], 'cover':'', 'collection':args['collection'], 
        'title_id':title_id, 'syn':'', 'release':'', 'num_pages':0,
        'created_timestamp':int(time.time()), 'updated_timestamp':int(time.time())
    }

    # first try to get the metadata from epub or vol_info
    if vol_info['type'] == 'epub':
        filepath = vol_info['path'] + vol_info['filename']
        try:
            book = epub.read_epub(filepath)
        except Exception as e:
            print("Corrupt file (%s)? %s" % (filepath, str(e)))
            return None, None
        lang = get_language_from_epub(book)
        if lang != 'jp' and lang != 'en':
            print("Invalid language %s in file %s" % (lang,filepath))
            #ans = input("Manually give corrent language (or empty to skip): ")
            ans = 'jp'
            if ans != '':
                lang = ans
            else:
                return None, None
        vol_data['lang'] = lang
        vol_name = get_metadata_from_epub(t_metadata, vol_data, lang, book)
        cover_title, _ = extract_publisher_from_title(title)
        save_cover_image_from_epub(title_id, book, vol_data, cover_title)
    else:
        lang = 'jp' # assumption
        vol_data['lang'] = lang
        vol_name = vol_info['volume_name']
        detected_publisher = get_publisher_from_txt_file(vol_info['path'] + vol_info['filename'])
        if detected_publisher is not None and 'publisher' not in t_metadata:
            t_metadata['publisher'] = detected_publisher

    vol_data['vol_name'] = vol_name

    existing_volume_ids, existing_vol_info_dict = get_volume_and_chapter_info(title_id, lang)
    existing_volume_names = [vi['vol_name'] for vi in existing_vol_info_dict.values()]

    if vol_name in existing_volume_names:
        print("%s [%s] Skipping already existing volume %s (%s)" % (title, title_id, vol_name, vol_info['filename']))
        return None, None

    if 'author' in vol_info:
        if len(t_metadata['authors'])==0:
            t_metadata['authors'] = [vol_info['author']]

    #if 'translator' not in t_metadata:
    #    t_metadata['translator'] = ''
    if ('translator' not in t_metadata or t_metadata['translator'] == '') and vol_info['translator'] != '':
        t_metadata['translator'] = vol_info['translator']

    if vol_id is None:
        vol_id = create_oid("%s/%s/%s" % (title_id,lang,vol_name), "volume", ask_confirmation=ask_confirmation_for_new_volumes, title_id=title_id)
        if vol_id is None:
            print("Skipped creating new volume")
            return None, None
    vol_data['vol_id'] = vol_id

    gb = None
    if not is_title_ignored_for_google_books(vol_id):
        gb = get_google_books_entry(vol_id)
        if gb is None or refresh_google_books_data:
            jptit = t_metadata['lang']['jp']['title']
            if len(t_metadata['authors'])>0 and jptit != '':
                search_metadata = {
                    'title' : jptit,
                    'author' : t_metadata['authors'][0],
                    'translator' : getattr(t_metadata,'translator',''),
                    'publisher' : t_metadata['publisher']
                }
                gb = search_records_and_select_one(vol_data, search_metadata, -1, manual_confirmation=ask_google_books_match_confirmation)
                if gb is None:
                    if ask_google_books_match_confirmation:
                        print("Author: " + t_metadata['authors'][0])
                        if t_metadata['translator'] != '':
                            print("Translator: " + t_metadata['translator'])
                        if t_metadata['Publisher']  != PLACEHOLDER:
                            print("Publisher: " + t_metadata['publisher'])
                        ans = input("Input Google book id: ")
                        if ans == '-':
                            ignore_google_book_matching_for_title(vol_id)
                        elif ans != '':
                            gb = match_googleid({'title':vol_id, 'googleid':ans})
                    else:
                        print("No Google books match found with ",search_metadata)
            else:
                print("Skipping Google Books search because insufficient info. Authors %s, jptit: %s" % (str(t_metadata['authors']), jptit))

    # try to fill the remaining missing data from Google books
    if gb is not None:
        update_metadata_from_google_books(t_metadata, vol_data, gb)


    args['ask_confirmation_for_new_chapters'] = ask_confirmation_for_new_chapters

    if lang == 'en':
        #############  process english volume
        print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

        if vol_data['cover'] == '':
            save_cover_image_from_epub(title_id, book, vol_data, title)

        chapters_processed, total_num_pages = process_epub(vol_data, title_id, book, args)

    elif lang == 'jp':
        if vol_info['type'] == 'epub':
            print("\tJP EPUB volume [%s]: %s " % (vol_id, vol_name))
            chapters_processed, total_num_pages = process_epub(vol_data, title_id, book, args)

        elif vol_info['type'] == 'txt':
            jp_volume_f = vol_info['path'] + vol_info['filename']
            print("\tJP TXT volume [%s]: %s " % (vol_id, vol_data['vol_name']))
            chapters_processed, total_num_pages = process_txt_file(vol_data, title_id, jp_volume_f, args)

        # if cover is not yet fetched, try to get it from Google Books
        if chapters_processed >= 0 and vol_data['cover'] == '':
            if gb is not None:
                fetch_cover_from_google_books(vol_data, gb)

    vol_data['num_pages'] = total_num_pages

    if chapters_processed >= 0:
        if 'volumes' not in t_metadata['lang'][lang]:
            t_metadata['lang'][lang]['volumes'] = []
        t_metadata['lang'][lang]['volumes'].append(vol_id)
        save_metadata(title_id, t_metadata, verbose_update)
        update_volume_data(vol_data)
        return vol_id, lang
    else:
        print("Skipped title %s vol_id %s" % (title_id, vol_id))
        database[COLLECTION_VOLUMEDATA].delete_one({'vol_id':vol_id})
        return None, None

def fetch_cover_from_google_books(vol_data, gb, force=False):
    vi = gb['volumeInfo']
    if 'imageLinks' in vi:
        img_url = vi['imageLinks']['thumbnail']
        target_img_name = vol_data['vol_id']
        suffix = 'jpg' # TODO, assume jpeg 
        target_img_path = 'manga_cover/jp/' + target_img_name + '.' + suffix
        vol_data['cover'] = target_img_path
        if not os.path.exists(target_img_path) or force:
            print("\tFetching cover image %s" % img_url)
            download_image(img_url,target_img_path)

def parse_volume_contents(args, title_id, title_name, vol_id):
    parser_args = {'force':False, 'chapter':None, 'read':False, 'first':False, 
                   'start_index':False, 'only_new' :True, 'force_aggregate':True, 
                   'omit_parsed_ocr_file':args['skip_content_import'] 
    }
    do_process_title(parser_args, title_id, title_name, counter_str='')

    calculate_summary_for_title(title_id)
    if args['skip_content_import']:
        # clear the OCR file afterwards, keeping only the language analysis summary
        target_ocr_file_path = target_ocr_path + vol_id + '.json'
        if os.path.exists(target_ocr_file_path):
            os.remove(target_ocr_file_path)
        target_ocr_file_path = parsed_ocr_dir + vol_id + '.json'
        if os.path.exists(target_ocr_file_path):
            os.remove(target_ocr_file_path)
            
    analyzer_args = {'title':title_id,  'read':False, 'force':True }
    individual_analysis(analyzer_args)



def process_file(args, title, vol_info):

    if args['keyword'] is not None and args['keyword'].lower() not in vol_info['filename']:
        return 
    
    path = vol_info['path'].split(args['source_dir'])[1]
    import_metadata = database[COLLECTION_VOL_IMPORT_METADATA].find_one({'filename':vol_info['filename'], 'path':path})
    if import_metadata is None:
        md5digest = md5(vol_info['path'] + vol_info['filename'])
        import_metadata = database[COLLECTION_VOL_IMPORT_METADATA].find_one({'md5':md5digest})

    if import_metadata is not None:
        title_id = get_title_id_by_volume_id(import_metadata['_id'])
    else:
        title_id = None

    if import_metadata is None or (check_for_orphan_volumes and title_id is None):

        print("%s Processing %s" % (vol_info['verbose_recursion_depth'], vol_info['path'] + vol_info['filename']))
        if args['simulate']:
            if args['verbose']:
                print("Title: ",title)
                print("Publisher: ",extract_publisher_from_title(title))
                print(vol_info)

        vol_info['title_from_filename'] = title
        if vol_info['type'] == 'epub':
            filepath = vol_info['path'] + vol_info['filename']
            if augment_vol_info_from_epub_file(filepath, vol_info):
                title = vol_info['title']
            else:
                print("Corrupt file (%s)?" % (filepath))
                return False
            
        if 'author' not in vol_info:
            print("File (%s) does not have author! Skipping.." % (filepath))
            return False
            
        # new volume
        if import_metadata is None:
            import_metadata = {
                'filename' : vol_info['filename'],
                'vol_name' : vol_info['volume_name'],
                'path' : path,
                'type' : vol_info['type'],
                'collection' :  args['collection'],
                'md5' : md5(vol_info['path'] + vol_info['filename'])
            }

        vol_info['title_from_filename'], publisher = extract_publisher_from_title(vol_info['title_from_filename'])
        if publisher is not None:
            vol_info['publisher'] = publisher
        if 'publisher' not in vol_info:
            vol_info['publisher'] = ''

        # try to match this volume with a title
        title_metadata = []
        match_query = {"$expr":{"$in":[vol_info['author'],"$authors"]},'lang.jp.title':title}
        if vol_info['translator'] != '':
            match_query["translator"] = vol_info['translator']
            title_metadata = database[COLLECTION_TITLEDATA].aggregate([{'$match':match_query}]).to_list()
            if len(title_metadata)==0:
                title_with_translator = title + ' (%s訳)' % vol_info['translator']
                match_query['lang.jp.title'] = title_with_translator
                title_metadata = database[COLLECTION_TITLEDATA].aggregate([{'$match':match_query}]).to_list()
        #if len(title_metadata)==0:
        #    title_metadata = database[COLLECTION_TITLEDATA].find({'title_from_filename':vol_info##['title_from_filename']}).to_list()
        if len(title_metadata)==0:
            match_query = {"$expr":{"$in":[vol_info['author'],"$authors"]},'lang.jp.title':title}
            title_metadata = database[COLLECTION_TITLEDATA].aggregate([{'$match':match_query}]).to_list()

            if vol_info['translator'] != '' and len(title_metadata)>0:
                # ok, so a title with a different translator found. We have to make a separate title
                # and name it explicitely with the translator
                print("Existing title found but with other translator (%s). Creating new title.." % (title_metadata['translator']))
                title_metadata = []
                title = title_with_translator

        if len(title_metadata)>0 and title_metadata[0]['type'] == 'manga':
            # existing title found but it is manga. Create a new title
            print("Existing title found but it is manga [%s]. Creating new title.." % (title_metadata['_id']))
            title_metadata = []
            title += ' (book)'

        if len(title_metadata)==0:
            if args['simulate']:
                if args['verbose']:
                    print(" * No title match")
                return False

            # no match --> create new title
            print("\nNew title:")
            print("\tTitle: ",title)
            print("\tVolume: ",vol_info['volume_name'])
            if 'author' in vol_info:
                print("\tAuthor: ",vol_info['author'])
            if vol_info['translator'] != '':
                print("\tTranslator: ",vol_info['translator'])
            print("\tFilename: ",vol_info['filename'])
            print("\tPath: ",vol_info['path'])
            title_id, _ = create_new_title(title, vol_info)
            if title_id is None:
                # skipped creating new title
                if input("Ignore this file?") == 'y':
                    import_metadata['ignore'] = True
                    res = database[COLLECTION_VOL_IMPORT_METADATA].insert_one(import_metadata)
                return False
        else:
            title_metadata = title_metadata[0]
            title_id = title_metadata['_id']
            print("Existing title found: [%s] %s" % (title_id, get_title_from_metadata(title_metadata)))

            if args['simulate']:
                if args['verbose']:
                    print(" * Match with title [%s] %s" % (title_id,get_title_from_metadata(title_metadata)))
                return False

        if '_id' in import_metadata:
            previous_vol_id = import_metadata['_id']
        else:
            previous_vol_id = None
        vol_id, lang = process_volume(args, title_id, title, vol_info, previous_vol_id)
        if vol_id is None:
            return False
        import_metadata['lang'] = lang
        import_metadata['_id'] = vol_id
        database[COLLECTION_VOL_IMPORT_METADATA].update_one({'_id':vol_id},{'$set':import_metadata},upsert=True)
        if lang == 'jp':
            parse_volume_contents(args, title_id, title, vol_id)
    else:
        if (args['force'] and (args['keyword'].lower() in title.lower() or args['keyword']==import_metadata['_id'])):
            # re-process existing volume
            vol_id = import_metadata['_id']
            title_id = get_title_id_by_volume_id(vol_id)
            if title_id is None:
                print("Orphan volume detected! ",import_metadata)
                ans = input("Remove? ")
                if ans == 'y':
                    database[COLLECTION_VOL_IMPORT_METADATA].delete_one({'_id':vol_id})
                    print("Removed volume %s from processed list. Can now be re-imported")
            else:
                process_volume(args, title_id, title, vol_info, vol_id)
                if lang == 'jp':
                    parse_volume_contents(args, title_id, title, vol_id)

            pass
    return True


def scan(args):
    global ask_confirmation_for_new_titles, ask_confirmation_for_new_volumes, ask_confirmation_for_new_chapters, ask_google_books_match_confirmation
    global file_list_cache, scanned_dir_count, scanned_file_count, ignored_count_by_ext

    if args['automatic']:
        ask_confirmation_for_new_titles = False
        ask_confirmation_for_new_volumes = False
        ask_confirmation_for_new_chapters = False
        ask_google_books_match_confirmation = False

    if args['only_epub']:
        filtered_file_type = '.epub'
    elif args['only_txt']:
        filtered_file_type = '.txt'
    else:
        filtered_file_type = None
    if parse_chapters_automatically:
        init_parser(load_meanings=True)
        
    if args['source_dir'] is None:
        args['source_dir'] = collections[args['collection']]['path']

    if args['source_dir'][-1] != '/':
        args['source_dir'] += '/'

    if 'cache_file_list' in collections[args['collection']] and collections[args['collection']]['cache_file_list']:
        if not os.path.exists('cache'):
            os.mkdir("cache")
        cache_file = 'cache/' + args['collection']+'.json'
        if os.path.exists(cache_file):
            with open(cache_file,"r") as f:
                file_list_cache = json.loads(f.read())
                print("Loaded file cache listing with %d entries" % len(file_list_cache))

        else:
            print("Creating file listing cache for collection %s" % args['collection'])
            file_list_cache = [os.path.join(dp, f) for dp, dn, filenames in os.walk(collections[args['collection']]['path']) for f in filenames]
            with open(cache_file,"w") as f:
                f.write(json.dumps(file_list_cache))

    if not os.path.exists(target_ocr_path):
        os.mkdir(target_ocr_path)

    recursive_scan(args, args['source_dir'], filtered_file_type=filtered_file_type)
    print("Scanned total %d files in %d directories" % (scanned_file_count,scanned_dir_count))
    print("Ignored file extensions: ",ignored_count_by_ext)


def remove(args):
    title = get_title_by_id(args['title_id'])
    jp_title = get_jp_title_by_id(args['title_id'])
    print("Title: %s / %s " % (title, jp_title))
    volumes = get_volumes_by_title_id(args['title_id'])
    for vol in volumes:
        if vol != '':
            print("\tVol [%s] %s" % (vol,get_volume_name(vol)))
            chapters = get_chapters_by_volume_id(vol)
            for cid in chapters:
                print("\t\tChapter [%s] %s" % (cid,get_chapter_name_by_id(cid)))

    ans = input("Delete this?")
    if ans == 'y':
        delete_title(args['title_id'])
        return True
    return False


def set_google_book_id(args):
    title_id = args['title_id']
    try:
        volume_ids, vol_info = get_volume_and_chapter_info(title_id, 'jp')
        first_vol = vol_info[volume_ids[0]]
        first_vol_id = first_vol['vol_id']
    except:
        first_vol_id = args['title_id']
        first_vol = get_volume_data(first_vol_id)

    google_book_id = args['google_book_id']
    gb = match_googleid({'vol_id':first_vol_id, 'googleid':google_book_id})
    if gb is not None:
        t_metadata = get_metadata_by_title_id(title_id)

        update_metadata_from_google_books(t_metadata, first_vol, gb, force=True)
        fetch_cover_from_google_books(first_vol, gb, force=True)
        update_volume_data(first_vol)
    else:
        print("Couldn't set google book id to %s" % google_book_id)


def show(args):

    title_id = args['title_id']

    volume_ids = get_volumes_by_title_id(title_id)
    metadata = get_metadata_by_title_id(title_id)
    print(metadata)
    for vol_id in volume_ids:
        vol = get_volume_number_by_volume_id(vol_id)
        import_data = database[COLLECTION_VOL_IMPORT_METADATA].find_one({'_id':vol_id})
        if import_data is None:
            print("No import data found for title %s / vol %d" % (title_id,vol_id))
        else:
            print("\nVol %d [%s]" % (vol,vol_id), import_data)


# reimport volume (by id) or first volume of given title (by id)
def reimport(args):
    global ask_confirmation_for_new_chapters, ask_google_books_match_confirmation

    volume_ids = get_volumes_by_title_id(args['title_id'])
    if len(volume_ids) == 0:
        title_id = get_title_id_by_volume_id(args['title_id'])
        if title_id is not None:
            volume_ids = [args['title_id']]
        else:
            print("No volume or title id found!")
            return -1
    else:         
        title_id = args['title_id']
   
    vol_id = volume_ids[0]

    import_data = database[COLLECTION_VOL_IMPORT_METADATA].find_one({'_id':vol_id})
    if  import_data is None:
        print("No import data found for title %s / vol %d" % (title_id,vol_id))
        return -1

    collection = import_data['collection'] 
    if collection not in collections:
        print("No collection %s found for title %s / vol %d" % (collection, title_id,vol_id))
        return -1
    coll_data = collections[collection]
    vol_path = coll_data['path'] + import_data['path']
    vol_filename = import_data['filename']
    if not os.path.exists(vol_path + vol_filename):
        print("No volume file %s found for title %s / vol %d" % (vol_path+vol_filename, title_id,vol_id))
        return -1

    vol_info = None
    if '.epub' in vol_filename:
        title, vol_info = get_info_from_epub_file_name(vol_path,vol_filename)
    elif '.txt' in vol_filename.lower():
        title, vol_info = get_info_from_txt_file_name(vol_path,vol_filename)

    # remove existing volume info
    remove_volume(title_id, vol_id)

    ask_confirmation_for_new_chapters = False
    ask_google_books_match_confirmation = False
    args['combine_chapters'] = False
    args['skip_content_import'] = False
    args['collection'] = collection

    process_volume(args, title_id, title, vol_info, vol_id)

    init_parser(load_meanings=True)
    parse_volume_contents(args, title_id, title, vol_id)



if __name__ == '__main__':

    #remove({'title_id':'678bb44b23502369d941f279'})

    #TESTING
    #args = {'command':'scan','keyword':None,'force':False,'collection':'PeepoHappyBooks2','source_dir':None,'automatic':True,'simulate':False,'verbose':True,'refresh_metadata':False,'skip_content':False, 'only_epub':False,'only_txt':False,'force_aggregate':False}
    #args = {'command':'scan','keyword':None,'force':False,'collection':'User','source_dir':None,'automatic':False,'simulate':False,'verbose':True,'refresh_metadata':False,'skip_content':False, 'only_epub':False,'only_txt':False,'force_aggregate':False}


    #args = {'command':'scan','keyword':'銀河鉄道の','force':True,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':False,'skip_content':False, 'only_epub':False,'only_txt':False}
    #args = {'command':'scan','keyword':'Musk','force':False,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':True,'skip_content':False, 'only_epub':False,'only_txt':False}
    #args = {'command':'set_en_vol','title_id':'66981f12534685524f9e373a','file':'/Users/markojuhanne/Documents/books/import/Murakami, Haruki (29 books)/Underground/Murakami, Haruki - Underground (Vintage, 2000).epub'}
    #args = {'command':'scan','keyword':None,'force':False,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':True,'skip_content':False, 'only_epub':False,'only_txt':False}
    #args = {'command':'remove','title_id':'635d54596d960eb0ac756ab1'}

    args['combine_chapters'] = True
    args['skip_content_import'] = True

    #parse_volume_contents(args, '678bafb5eca8513c8e10ffda', 'ヴァーチャル・ライト', '678bafb6eca8513c8e10ffdb')

    #args = {'command':'reimport','title_id':'677500d3999d87aa4e9707fc','force':False,'verbose':True,'force_aggregate':False}


    cmd = args.pop('command')


    if cmd != None:
        locals()[cmd](args)
