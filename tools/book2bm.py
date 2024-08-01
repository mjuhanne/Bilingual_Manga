import json
import os
import subprocess
from helper import * 
import shutil
import argparse
import logging
import re

from book2bm_helper import *
from book2bm_epub_helper import *
from book2bm_txt_helper import *

default_book_path = '/mnt/Your/Book/Directory'

verbose = False


titles = dict()

parser = argparse.ArgumentParser(
    prog="books2bm",
    description="Import books to Bilingualmanga.",
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_import = subparsers.add_parser('scan', help='Scan and import all the mokuro manga titles with placeholder metadata and process OCR files')
parser_import.add_argument('--force', '-f', action='store_true', help='Force import')
parser_import.add_argument('--source_dir', '-src', type=str, default=default_book_path, help='Source mokuro directory (with jp/ and en/ subdirectories)')
parser_import.add_argument('--simulate', '-s', action='store_true', help='Scan only (do not create new OIDs or import)')
parser_import.add_argument('-v', '--verbose', action='store_true', help='Verbose')
parser_import.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

parser_remove = subparsers.add_parser('remove', help='Remove given title)')
parser_remove.add_argument('title_id', type=str, default=None, help='Title id')

parser_search = subparsers.add_parser('search', help='Search title/chapter_ids with given keyword')
parser_search.add_argument('-v', '--verbose', action='store_true', help='Show all subdirectory OIDs as well')
parser_search.add_argument('keyword', type=str, default=None, help='Keyword')

parser_show = subparsers.add_parser('show', help='Show list of all imported manga')

parser_set_en_vol = subparsers.add_parser('set_en_vol', help='Set english vol for title')
parser_set_en_vol.add_argument('title_id', type=str, default=None, help='Title id')
parser_set_en_vol.add_argument('--file', '-f', type=str, help='Source .epub file')


args = vars(parser.parse_args())

if 'verbose' in args:
    verbose = args['verbose']

if verbose:
    print("Args: ",args)

cmd = args.pop('command')

if cmd == 'scan':
    if args['source_dir'][-1] != '/':
        args['source_dir'] += '/'
    src_jp = args['source_dir'] + 'jp/'
    source_items = [f_name for f_name in os.listdir(src_jp) if '.epub' in f_name.lower() or '.txt' in f_name.lower() or os.path.isdir(src_jp + f_name)]

    source_items.sort()


j = 0
manga_metadata_per_id = dict()
manga_data_per_id = dict()

if os.path.exists(ext_manga_metadata_file):
    with open(ext_manga_metadata_file,"r",encoding="utf-8") as f:
        data = f.read()
        _manga_metadata = json.loads(data)
        for mdata in _manga_metadata:
            id = mdata['enid']
            manga_metadata_per_id[id] = mdata

if os.path.exists(ext_manga_data_file):
    with open(ext_manga_data_file,"r",encoding="utf-8") as f:
        data = f.read()
        _manga_data = json.loads(data)
        for mdata in _manga_data:
            id = mdata['_id']['$oid']
            manga_data_per_id[id] = mdata

def copy_file(src, target_path, target_file):

    if not os.path.exists(target_path):
        os.mkdir(target_path)
    
    p  = target_path + '/' + target_file
    if os.path.exists(src):
        if not os.path.exists(p):
            print("\tCopying %s to %s" % (src,p))
            shutil.copyfile(src, p)
    else:
        print("\tDoes not exist! %s" % src)


PLACEHOLDER = 'Placeholder'


def save_metadata_files():
    target_f = open(ext_manga_data_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_data_per_id.values()),ensure_ascii=False))
    target_f.close()
    target_f = open(ext_manga_metadata_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_metadata_per_id.values()),ensure_ascii=False))
    target_f.close()

dir_regex = [
    "\(一般小説\)+\s+\[([^\]]+)\]\s+([^（\(\s\)]+)"
]

def get_info_from_directory(source_item):
    # extract info from directory names such as:
    # (一般小説) [藤沢周平] よろずや平四郎活人剣（上）（下） (青空文庫対応txt 表紙付)(校正08-11-04)
    author = None
    title = source_item
    for reg in dir_regex:
        res = re.search(reg,source_item)
        if res is not None:
            author = res.groups()[0]
            title = res.groups()[1]
            return title, author
    return title, author

def recursive_scan(root_path,source_item,title=None, author=None):
    global titles
    new_path = root_path + source_item + '/'
    if os.path.isdir(new_path):
        sub_items = [f_name for f_name in os.listdir(new_path) if '.epub' in f_name.lower() or '.txt' in f_name.lower() or os.path.isdir(new_path + f_name)]
        sub_items.sort()
        if source_item[0] == '_' or source_item == 'jp':
            # just a simple sub-directory which doesn't infer a title 
            # e.g.  _science_fiction/  or _murakami
            for sub_item in sub_items:
                recursive_scan(new_path, sub_item)
        else:
            # a subdirectory from which we can infer the title (and maybe the author)
            title, author = get_info_from_directory(source_item)
            for sub_item in sub_items:
                recursive_scan(new_path, sub_item, title, author)
    else:
        vol_info = None
        if '.epub' in source_item:
            new_title, vol_info = get_info_from_epub_file_name(root_path,source_item)
            if title is None:
                title = new_title
        elif '.txt' in source_item.lower():
            new_title, vol_info = get_info_from_txt_file_name(root_path,source_item,title,author)
            if title is None:
                title = new_title
        if title is not None and vol_info is not None:
            if title not in titles:
                titles[title] = []
            titles[title].append(vol_info)


def scan(args):
    recursive_scan(args['source_dir'], 'jp')

    for title,volumes in titles.items():

        if args['keyword'] is not None and args['keyword'].lower() not in title.lower():
            if verbose:
                print("Skipping %s" % title)
            continue

        if args['simulate']:
            title_id = get_oid(title, create_new_if_not_found=False)
            if title_id is None:
                print("New title found: %s" % title)
                for v in volumes:
                    print("\t%s" % (v['filename']))
                    if v['type'] == 'txt':
                        print("\t%s/%s/%s" % (v['author'],title,v['volume_name']))
                        chapters = get_chapters_from_txt_file(v['path'] + v['filename'])
                        for chapter in chapters:
                            print("\t\t[%d] %s" % (chapter['num_pages'],chapter['name']))
                    elif v['type'] == 'epub':
                        jp_volume_f = v['path'] + v['filename']
                        jp_book = epub.read_epub(jp_volume_f)
                        creator, _ = jp_book.get_metadata('DC', 'creator')[0]
                        print("\t  %s/%s/%s" % (creator,title,v['volume_name']))
                        chapter_titles,_ = get_chapters_from_epub(jp_book,args['verbose'])
                        #for chapter in chapter_titles:
                        #    print("\t\t%s" % (chapter))
                print("")
            continue
                
        title_id = get_oid(title)

        if title_id in manga_metadata_per_id and title_id in manga_data_per_id and not args['force']:
            if verbose:
                print("Skipping already processed %s" % title)
            continue

        print("Processing title [%s]: %s " % (title_id, title))

        if os.path.exists(args['source_dir'] + 'en/' + title + '.epub'):
            en_book = epub.read_epub(args['source_dir'] + 'en/' + title + '.epub')
            en_vol_title,_ = en_book.get_metadata('DC', 'title')[0]
        else:
            en_book = None

        if title_id not in manga_data_per_id:
            t_data = dict()
            t_data['_id'] = dict()
            t_data['_id']['$oid'] = title_id
            if en_book is not None:
                t_data['syn_en'] = en_vol_title
            else:
                t_data['syn_en'] = PLACEHOLDER
            t_data['syn_jp'] = PLACEHOLDER
            t_data['en_data'] = dict()
            t_data['jp_data'] = dict()

            t_data['en_data']['ch_naen'] = []
            t_data['en_data']['ch_enh'] = []
            t_data['en_data']['vol_en'] = dict()
            t_data['en_data']['ch_en'] = dict()

            manga_data_per_id[title_id] = t_data 
        else:
            t_data = manga_data_per_id[title_id]

        if title_id not in manga_metadata_per_id:
            t_metadata = dict()
            if en_book is not None:
                t_metadata['entit'] = en_book.get_metadata('DC', 'title')
            else:
                t_metadata['entit'] = title

            t_metadata['jptit'] = PLACEHOLDER
            t_metadata['coveren'] = PLACEHOLDER
            t_metadata['coverjp'] = PLACEHOLDER
            t_metadata['genres'] = []
            t_metadata['Author'] = [PLACEHOLDER]
            t_metadata['Artist'] = [PLACEHOLDER]

            t_metadata['Release'] = PLACEHOLDER
            t_metadata['Status'] = PLACEHOLDER
            t_metadata['search'] = PLACEHOLDER
            t_metadata['enid'] = title_id
            t_metadata['fetched'] = False

            manga_metadata_per_id[title_id] = t_metadata 
        else:
            t_metadata = manga_metadata_per_id[title_id]
        t_metadata['verified_ocr'] = True
        t_metadata['is_book'] = True
        t_data['is_book'] = True


        #############  process english chapters
        if en_book is not None:

            t_data['en_data']['ch_naen'] = []
            t_data['en_data']['ch_enh'] = []
            t_data['en_data']['vol_en'] = dict()
            t_data['en_data']['ch_en'] = dict()

            vol_name = en_vol_title
            vol_id = get_oid(title_id + '/en/' + vol_name)
            vol_number = 1

            print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

            vol_ipfs_path = target_ipfs_path + vol_id

            if not os.path.exists(vol_ipfs_path):
                os.mkdir(vol_ipfs_path)
 
            save_cover_image_from_epub(t_metadata, en_book, 'en',title)

            t_data['en_data']['virtual_chapter_page_count'] = []

            process_epub(t_data, title_id, en_book,'en', vol_id, en_vol_title, 0, args['verbose'])


        #############  process jp volumes/chapters
        t_data['jp_data']['ch_najp'] = []
        t_data['jp_data']['ch_jph'] = []
        t_data['jp_data']['vol_jp']= dict()
        t_data['jp_data']['ch_jp'] = dict()
        t_data['jp_data']['virtual_chapter_page_count'] = []
        total_ch_count = 0

        for vol_idx, vol_info in enumerate(volumes):

            jp_volume_f = vol_info['path'] + vol_info['filename']

            if vol_info['type'] == 'epub':
                jp_book = epub.read_epub(jp_volume_f)
                jp_vol_title,_ = jp_book.get_metadata('DC', 'title')[0]

                vol_id = get_oid(title_id + '/jp/' + jp_vol_title)

                print("\tJP EPUB volume [%s]: %s " % (vol_id, jp_vol_title))

                if vol_idx == 0:
                    # get the metadata from the first volume
                    t_data['syn_jp'] = jp_book.get_metadata('DC', 'description')

                    # get rid of of the volume part in title
                    jptitle = jp_vol_title.split(' 上 ')[0]
                    jptitle = jptitle.split(' 中 ')[0]
                    jptitle = jptitle.split(' 下 ')[0]

                    t_metadata['jptit'] = jptitle
                    creator, _ = jp_book.get_metadata('DC', 'creator')[0]
                    t_metadata['Author'] = [creator]

                    # get the cover image from the first volume also
                    save_cover_image_from_epub(t_metadata, jp_book, 'jp',title)

                total_ch_count += process_epub(t_data, title_id, jp_book,'jp', vol_id, jp_vol_title, total_ch_count, args['verbose'])

            elif vol_info['type'] == 'txt':

                jp_vol_title = vol_info['volume_name']

                vol_id = get_oid(title_id + '/jp/' + jp_vol_title)

                print("\tJP TXT volume [%s]: %s " % (vol_id, jp_vol_title))

                if vol_idx == 0:
                    # get the metadata from the first volume

                    # todo metadata
                    t_metadata['jptit'] = title
                    t_metadata['Author'] = [vol_info['author']]

                total_ch_count += process_txt_file(t_data, title_id, jp_volume_f ,'jp', vol_id, jp_vol_title, total_ch_count)


        save_metadata_files()

def remove(args):
    found = False
    for title, title_id in ext_object_ids.items():
        if args['title_id'] == title_id:

            if title_id in manga_metadata_per_id:
                found = True
                print("Deleting %s [%s]" % (title,title_id))
                del(manga_data_per_id[title_id])
                del(manga_metadata_per_id[title_id])
                save_metadata_files()

    if not found:
        print("Title id %s not found!" % args['title_id'])


def set_en_vol(args):
    title_id = args['title_id']
    if title_id in manga_metadata_per_id:
        t_data = manga_data_per_id[title_id]
        t_metadata = manga_metadata_per_id[title_id]

        en_book = epub.read_epub(args['file'])
        en_vol_title,_ = en_book.get_metadata('DC', 'title')[0]

        t_metadata['entit'] = en_vol_title
        t_data['syn_en'] = en_book.get_metadata('DC', 'description')

        t_data['en_data']['ch_naen'] = []
        t_data['en_data']['ch_enh'] = []
        t_data['en_data']['vol_en'] = dict()
        t_data['en_data']['ch_en'] = dict()
        ch_idx = 1

        vol_name = en_vol_title
        vol_id = get_oid(title_id + '/en/' + vol_name)
        vol_number = 1

        print("\tVolume EN [%s]: %s " % (vol_id, vol_name))

        vol_ipfs_path = target_ipfs_path + vol_id

        if not os.path.exists(vol_ipfs_path):
            os.mkdir(vol_ipfs_path)

        save_cover_image_from_epub(t_metadata, en_book, 'en',en_vol_title)

        t_data['en_data']['virtual_chapter_page_count'] = []

        process_epub(t_data, title_id, en_book,'en', vol_id, en_vol_title, 0)

        save_metadata_files()

    else:
        print("Title id %s not found!" % args['title_id'])

def search(args):
    saved_oids = []
    for title, title_id in ext_object_ids.items():
        if args['keyword'].lower() in title.lower():
            print("[%s] %s" % (title_id,title))
            if verbose:
                saved_oids.append(title_id)
        if verbose:
            for oid in saved_oids:
                if oid in title:
                    print("[%s] -> [%s] %s" % (oid,title_id,title))

def show(args):
    for title_id, mdata in manga_metadata_per_id.items():
        for title, oid in ext_object_ids.items():
            if oid == title_id:
                entit = mdata['entit']
                mark = ' '
                if entit.lower() != title.lower():
                    mark = '*'
                print("%s [%s] %s\t%s" % (mark,title_id,title.ljust(20),mdata['entit']))


if cmd != None:
  locals()[cmd](args)
