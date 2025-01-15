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


file_list_cache = []
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

titles = dict()

parser = argparse.ArgumentParser(
    prog="books2bm",
    description="Import books to Bilingualmanga.",
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

def create_new_title(title, title_from_filename, simulate=False):

    title_id = create_oid(title, "title", ask_confirmation=(ask_confirmation_for_new_titles and not simulate))
    if title_id is None:
        # oid not found and adding new one was manually skipped
        return None

    title_from_filename, publisher = extract_publisher_from_title(title_from_filename)

    # normalize the title just in case
    # It can be in Unicode composed form (i.e. で)
    # or decomposed (i.e. て　+　゙	 mark).  The strings are stored in composed form
    clean_title = ud.normalize('NFC',title)

    print("Creating new title [%s]: %s " % (title_id, title))

    t_metadata = dict()
    t_metadata['created_timestamp'] = int(time.time())

    if has_cjk(clean_title) or has_word_hiragana(clean_title) or has_word_katakana(clean_title):
        t_metadata['jptit'] = clean_title
        t_metadata['entit'] = PLACEHOLDER
    else:
        t_metadata['entit'] = clean_title
        t_metadata['jptit'] = clean_title
    t_metadata['title_from_filename'] = title_from_filename

    t_metadata['genres'] = []
    if publisher is not None:
        t_metadata['Publisher'] = publisher
    else:
        t_metadata['Publisher'] = PLACEHOLDER

    t_metadata['Author'] = [PLACEHOLDER]
    t_metadata['Release'] = PLACEHOLDER

    t_metadata['coveren'] = PLACEHOLDER
    t_metadata['coverjp'] = PLACEHOLDER
    t_metadata['Artist'] = []

    t_metadata['Status'] = 'Completed' # assumption
    t_metadata['search'] = ''
    t_metadata['enid'] = title_id
    t_metadata['verified_ocr'] = True
    t_metadata['is_book'] = True

    t_data = dict()
    t_data['_id'] = title_id
    t_data['en_data'] = dict()
    t_data['jp_data'] = dict()

    t_data['syn_jp'] = ''
    t_data['syn_en'] = ''
    t_data['is_book'] = True

    t_data['en_data']['ch_naen'] = []
    t_data['en_data']['ch_enh'] = []
    t_data['en_data']['vol_en'] = dict()
    t_data['en_data']['ch_en'] = dict()

    t_data['jp_data']['ch_najp'] = []
    t_data['jp_data']['ch_jph'] = []
    t_data['jp_data']['vol_jp']= dict()
    t_data['jp_data']['ch_jp'] = dict()
    t_data['jp_data']['virtual_chapter_page_count'] = []

    if not simulate:
        save_metadata(title_id, t_metadata, t_data, False)
    return title_id, t_metadata, t_data

def update_metadata_from_google_books(t_metadata, t_data, gb, force=False):
    vi = gb['volumeInfo']
    if '訳)' in t_metadata['jptit']:
        t_metadata['jptit'] = clean_google_books_title(vi['title']) + " (%s訳)" % t_metadata['translator']
    else:
        t_metadata['jptit'] = clean_google_books_title(vi['title'])

    if t_metadata['entit'] == PLACEHOLDER or force:
        if 'en_title_deepl' in gb:
            t_metadata['entit'] = gb['en_title_deepl']
            t_metadata['entit_is_translated'] = True

    if 'categories' in vi:
        t_metadata['genres'] = vi['categories']

    if (t_metadata['Publisher'] == PLACEHOLDER or force) and 'publisher' in vi:
        t_metadata['Publisher'] = vi['publisher']

    if 'authors' in vi:
        t_metadata['Author'] = vi['authors']

    if t_metadata['Release'] == PLACEHOLDER or force:
        try:
            t_metadata['Release'] = int(vi['publishedDate'].split('-')[0])
        except:
            pass

    if 'en_synopsis_deepl' in gb:
        t_data['syn_en_deepl'] = gb['en_synopsis_deepl']
    t_data['syn_jp'] = gb['volumeInfo']['description']

def process_volume(args, title_id, title, vol_info, vol_id=None):
    t_metadata = get_metadata_by_title_id(title_id)
    t_data = get_data_by_title_id(title_id)

    if 'Publisher' not in t_metadata:
        t_metadata['Publisher'] = PLACEHOLDER

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
        vol_name = get_metadata_from_epub(t_metadata, t_data, lang, book, vol_info)
        cover_title, _ = extract_publisher_from_title(title)
        save_cover_image_from_epub(t_metadata, book, lang, cover_title)
    else:
        lang = 'jp' # assumption
        vol_name = vol_info['volume_name']
        detected_publisher = get_publisher_from_txt_file(vol_info['path'] + vol_info['filename'])
        if detected_publisher is not None and t_metadata['Publisher'] == PLACEHOLDER:
            t_metadata['Publisher'] = detected_publisher

    if vol_name in t_data['jp_data']['vol_jp'] or vol_name in t_data['en_data']['vol_en']:
        print("%s [%s] Skipping already existing volume %s (%s)" % (title, title_id, vol_name, vol_info['filename']))
        return None, None

    if 'author' in vol_info:
        if t_metadata['Author'] == [PLACEHOLDER]:
            t_metadata['Author'] = [vol_info['author']]

    if 'translator' not in t_metadata:
        t_metadata['translator'] = ''
    if t_metadata['translator'] == '' and vol_info['translator'] != '':
        t_metadata['translator'] = vol_info['translator']

    gb = None
    if not is_title_ignored_for_google_books(title_id):
        gb = get_google_books_entry(title_id)
        if gb is None or refresh_google_books_data:
            author = t_metadata['Author'][0]
            if author != PLACEHOLDER and t_metadata['jptit'] != PLACEHOLDER:
                search_metadata = {
                    'title' : t_metadata['jptit'],
                    'author' : author,
                    'translator' : t_metadata['translator'],
                    'publisher' : t_metadata['Publisher']
                }
                gb = search_records_and_select_one(title_id, search_metadata, -1, manual_confirmation=ask_google_books_match_confirmation)
                if gb is None:
                    if ask_google_books_match_confirmation:
                        print("Author: " + author)
                        if t_metadata['translator'] != '':
                            print("Translator: " + t_metadata['translator'])
                        if t_metadata['Publisher']  != PLACEHOLDER:
                            print("Publisher: " + t_metadata['Publisher'])
                        ans = input("Input Google book id: ")
                        if ans == '-':
                            ignore_google_book_matching_for_title(title_id)
                        elif ans != '':
                            gb = match_googleid({'title':title_id, 'googleid':ans})
                    else:
                        print("No Google books match found with ",search_metadata)
            else:
                print("Skipping Google Books search because insufficient info. Author %s, jptit: %s" % (author, t_metadata['jptit']))

    # try to fill the remaining missing data from Google books
    if gb is not None:
        update_metadata_from_google_books(t_metadata, t_data, gb)

    if vol_id is None:
        vol_id = create_oid("%s/%s/%s" % (title_id,lang,vol_name), "volume", ask_confirmation=ask_confirmation_for_new_volumes, title_id=title_id)
        if vol_id is None:
            print("Skipped creating new volume")
            return None, None

    if vol_name in t_data[lang + '_data']['vol_' + lang]:
        raise Exception("TODO! replace old vol/chapter info in t_data")

    args['ask_confirmation_for_new_chapters'] = ask_confirmation_for_new_chapters

    if lang == 'en':
        #############  process english chapter
        print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

        if t_metadata['coveren'] == PLACEHOLDER:
            save_cover_image_from_epub(t_metadata, book, 'en',title)

        t_data['en_data']['virtual_chapter_page_count'] = []

        process_result = process_epub(t_data, title_id, book,'en', vol_id, vol_name, args)

    elif lang == 'jp':
        if vol_info['type'] == 'epub':
            print("\tJP EPUB volume [%s]: %s " % (vol_id, vol_name))
            process_result = process_epub(t_data, title_id, book,'jp', vol_id, vol_name, args)

        elif vol_info['type'] == 'txt':
            jp_vol_title = vol_info['volume_name']
            jp_volume_f = vol_info['path'] + vol_info['filename']
            print("\tJP TXT volume [%s]: %s " % (vol_id, jp_vol_title))
            process_result = process_txt_file(t_data, title_id, jp_volume_f ,'jp', vol_id, jp_vol_title, args)

        # if cover is not yet fetched, try to get it from Google Books
        if process_result >= 0 and t_metadata['coverjp'] == PLACEHOLDER:
            if gb is not None:
                fetch_cover_from_google_books(title_id, title, t_metadata, gb)

    if process_result >= 0:
        save_metadata(title_id, t_metadata, t_data, verbose_update)
        return vol_id, lang
    else:
        print("Skipped title %s vol_id %s" % (title_id, vol_id))
        ans = input("Delete possible references? ")
        if ans == 'y':
            remove_chapter_lookup_entry(title_id, vol_id, 'ALL')
        return None, None

def fetch_cover_from_google_books(title_id, title, t_metadata, gb, force=False):
    vi = gb['volumeInfo']
    if 'imageLinks' in vi:
        img_url = vi['imageLinks']['thumbnail']
        target_img_name = clean_name(title)
        suffix = 'jpg' # TODO, assume jpeg 
        target_img_path = 'manga_cover/jp/' + target_img_name + '.' + suffix
        t_metadata['coverjp'] = target_img_path
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
    import_metadata = database[BR_VOL_IMPORT_METADATA].find_one({'filename':vol_info['filename'], 'path':path})
    if import_metadata is None:
        md5digest = md5(vol_info['path'] + vol_info['filename'])
        import_metadata = database[BR_VOL_IMPORT_METADATA].find_one({'md5':md5digest})

    if import_metadata is None:

        print("%s Processing %s" % (vol_info['verbose_recursion_depth'], vol_info['path'] + vol_info['filename']))
        if args['simulate']:
            if args['verbose']:
                print("Title: ",title)
                print("Publisher: ",extract_publisher_from_title(title))
                print(vol_info)

        title_from_filename = title
        if vol_info['type'] == 'epub':
            filepath = vol_info['path'] + vol_info['filename']
            vol_info['volume_name'], title = get_clean_title_and_volume_name_from_epub_file(filepath)
            if title is None:
                print("Corrupt file (%s)?" % (filepath))
                return False
            

        # new volume
        import_metadata = {
            'filename' : vol_info['filename'],
            'vol_name' : vol_info['volume_name'],
            'path' : path,
            'type' : vol_info['type'],
            'collection' :  args['collection'],
            'md5' : md5(vol_info['path'] + vol_info['filename'])
        }

        # try to match this volume with a title
        title_metadata = None
        if vol_info['translator'] != '':
            title_with_translator = title + ' (%s訳)' % vol_info['translator']
            title_metadata = database[BR_METADATA].find_one({'jptit':title,'translator':vol_info['translator']})
            if title_metadata is None:
                title_metadata = database[BR_METADATA].find_one({'jptit':title_with_translator,'translator':vol_info['translator']})
        if title_metadata is None:
            clean_title, publisher = extract_publisher_from_title(title)
            title_metadata = database[BR_METADATA].find_one({'title_from_filename':clean_title})
        if title_metadata is None:
            title_metadata = database[BR_METADATA].find_one({'jptit':title})

            if vol_info['translator'] != '' and title_metadata is not None:
                # ok, so a title with a different translator found. We have to make a separate title
                # and name it explicitely with the translator
                print("Existing title found but with other translator (%s). Creating new title.." % (title_metadata['translator']))
                title_metadata = None
                title = title_with_translator

        if title_metadata is not None and title_metadata['is_book'] == False:
            # existing title found but it is manga. Create a new title
            print("Existing title found but it is manga [%s]. Creating new title.." % (title_metadata['_id']))
            title_metadata = None
            title += ' (book)'

        if title_metadata is None:
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
            title_id, _, _ = create_new_title(title, title_from_filename)
            if title_id is None:
                # skipped creating new title
                if input("Ignore this file?") == 'y':
                    import_metadata['ignore'] = True
                    res = database[BR_VOL_IMPORT_METADATA].insert_one(import_metadata)
                return False
        else:
            title_id = title_metadata['_id']
            print("Existing title found: [%s] [%s] (%s)" % (title_id, title_metadata['entit'], title_metadata['jptit']))

        if args['simulate']:
            if args['verbose']:
                print(" * Match with title [%s] %s" % (title_id,title_metadata['jptit']))
            return False

        vol_id, lang = process_volume(args, title_id, title, vol_info)
        if vol_id is None:
            return False
        import_metadata['lang'] = lang
        import_metadata['_id'] = vol_id
        database[BR_VOL_IMPORT_METADATA].insert_one(import_metadata)
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
                    database[BR_VOL_IMPORT_METADATA].delete_one({'_id':vol_id})
                    print("Removed volume %s from processed list. Can now be re-imported")
            else:
                process_volume(title_id, title, vol_info, vol_id)
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
        md = database[BR_METADATA].find_one(({'_id':args['title_id']}))
        if md is None:
            print("Couldn't find %s" % args['title_id'])
            return

        d = database[BR_METADATA].delete_one({'_id':args['title_id']})
        d = database[BR_DATA].delete_one({'_id':args['title_id']})
        d = database[BR_CUSTOM_LANG_ANALYSIS].delete_one({'_id':args['title_id']})
        d = database[BR_LANG_SUMMARY].delete_one({'_id':args['title_id']})
        d = database[BR_LANG_SUMMARY].delete_one({'_id':args['title_id']})
        for vol in volumes:
            ref = database[BR_VOL_IMPORT_METADATA].find_one({'_id':vol})
            if ref is None:
                print("Vol %s: No file reference to be freed(?)" % (vol))
            else:
                print("Vol %s: Freeing reference for %s" % (vol, ref['filename']))
                d = database[BR_LANG_SUMMARY].delete_one({'_id':vol})


def set_google_book_id(args):
    title_id = args['title_id']
    google_book_id = args['google_book_id']
    gb = match_googleid({'title':title_id, 'googleid':google_book_id})
    if gb is not None:
        t_metadata = get_metadata_by_title_id(title_id)
        t_data = get_data_by_title_id(title_id)
        update_metadata_from_google_books(t_metadata, t_data, gb, force=True)
        fetch_cover_from_google_books(title_id, t_metadata['jptit'], t_metadata, gb, force=True)
        save_metadata(title_id, t_metadata, t_data, verbose_update)
    else:
        print("Couldn't set google book id to %s" % google_book_id)


def show(args):

    title_id = args['title_id']

    volume_ids = get_volumes_by_title_id(title_id)
    metadata = get_metadata_by_title_id(title_id)
    print(metadata)
    for vol_id in volume_ids:
        vol = get_volume_number_by_volume_id(vol_id)
        import_data = database[BR_VOL_IMPORT_METADATA].find_one({'_id':vol_id})
        if import_data is None:
            print("No import data found for title %s / vol %d" % (title_id,vol_id))
        else:
            print("\nVol %d [%s]" % (vol,vol_id), import_data)


def reimport(args):

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
   
    title_name = get_title_by_id(title_id)
    if len(volume_ids)>1:
        print("Supporting only 1 volume titles for now!")
        return -1

    vol_id = volume_ids[0]
    import_data = database[BR_VOL_IMPORT_METADATA].find_one({'_id':vol_id})
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

    process_volume(args, title_id, title, vol_info, vol_id)
    parse_volume_contents(args, title_id, title, vol_id)



#TESTING
#args = {'command':'scan','keyword':None,'force':False,'collection':'PeepoHappyBooks2','source_dir':None,'automatic':True,'simulate':False,'verbose':True,'refresh_metadata':False,'skip_content':False, 'only_epub':False,'only_txt':False,'force_aggregate':False}
#args = {'command':'scan','keyword':'銀河鉄道の','force':True,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':False,'skip_content':False, 'only_epub':False,'only_txt':False}
#args = {'command':'scan','keyword':'Musk','force':False,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':True,'skip_content':False, 'only_epub':False,'only_txt':False}
#args = {'command':'set_en_vol','title_id':'66981f12534685524f9e373a','file':'/Users/markojuhanne/Documents/books/import/Murakami, Haruki (29 books)/Underground/Murakami, Haruki - Underground (Vintage, 2000).epub'}
#args = {'command':'scan','keyword':None,'force':False,'source_dir':default_book_path,'simulate':False,'verbose':True,'refresh_metadata':True,'skip_content':False, 'only_epub':False,'only_txt':False}
#args = {'command':'remove','title_id':'635d54596d960eb0ac756ab1'}

args['combine_chapters'] = True
args['skip_content_import'] = True

#args = {'command':'reimport','title_id':'677500d3999d87aa4e9707fc','force':False,'verbose':True,'force_aggregate':False}


cmd = args.pop('command')


if cmd != None:
  locals()[cmd](args)
