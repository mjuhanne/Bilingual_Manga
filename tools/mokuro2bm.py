"""
This script can be used to import Mokuro processed manga to Bilingual Manga

    Manga metadata and file/chapter/volume info will be saved to
        json/ext.manga_data.json
        json/ext.manga_metadata.json

    A 'faux' IPFS Object iD (Title/Volume/Chapter ID) for each new item will be saved to
        json/ext.oids.json

USAGE:

1) python mokuro2bm.py scan -src /mnt/mokuro --copy_images

    The script will assume following directory structure:
        /mnt/mokuro/jp/MangaTitle1/Vol1/Chapter1.html
        /mnt/mokuro/jp/MangaTitle1/Vol1/Chapter1/ .. (image directory)

        OR
        /mnt/mokuro/jp/MangaTitle1/Chapter1.html
        /mnt/mokuro/jp/MangaTitle1/Chapter1/ .. (image directory)

    Corresponding English translations will be searched from:

        /mnt/mokuro/en/MangaTitle1/Vol1/Chapter1/ .. (image directory)

        OR
        /mnt/mokuro/en/MangaTitle1/Chapter1/ .. (image directory)
    
    .. but the chapter/volume directories don't need to match (only manga title directory needs to be the same)

    Cover for japanese manga entry will be downloaded from mangaupdates (in next step)
    For English entries the cover image should be copied manually to
        /mnt/mokuro/en/MangaTitle1/cover.jpg  (or .tiff/.png/.jpeg)
    
    
2) Use mangaupdates.py to match each new manga title ID to mangaupdates.com entry

    The matched entries will be saved to
        json/ext_mangaupdates.json

3) Use
        python mokuro2bm.py fetch_metadata
    to populate manga metadata from mangaupdates and to automatically download the cover images.

4) Each erroneously added manga title can be removed with
        python mokuro2bm.py remove [title_id]

    Title IDs can be searched with
        python mokuro2bm.py search [keyword]
        
"""
import json
import os
from bs4 import BeautifulSoup
import subprocess
from urllib.parse import unquote
from helper import * 
import shutil
import bson
import requests
import re
import argparse
import logging
import unicodedata as ud
logging.captureWarnings(True) # repress HTML certificate verification warnings

default_mokuro_path = '/mnt/Your/Mokuro/Directory'

dw_file_path = 'json/dw.json'
ext_mangaupdates_file = base_dir + "json/ext_mangaupdates.json"

target_ext_oid_path = 'json/ext.oids.json'
target_ocr_path = 'ocr/'
target_ipfs_path = 'ipfs/'

parser = argparse.ArgumentParser(
    prog="mokuro2bm",
    description="Import Mokuro processed manga to Bilingualmanga. Also fetch metadata from MangaUpdates.com",
)
subparsers = parser.add_subparsers(help='', dest='command')

parser_import = subparsers.add_parser('scan', help='Scan and import all the mokuro manga titles with placeholder metadata and process OCR files')
parser_import.add_argument('--force', '-f', action='store_true', help='Force import')
parser_import.add_argument('--copy_images', '-ci', action='store_true', help='Copy also manga image files from source directory to IPFS')
parser_import.add_argument('--source_dir', '-src', type=str, default=default_mokuro_path, help='Source mokuro directory (with jp/ and en/ subdirectories)')
parser_import.add_argument('--simulate', '-s', action='store_true', help='Scan only (do not create new OIDs or import)')
parser_import.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

parser_fetch_metadata = subparsers.add_parser('fetch_metadata', help='Scan and import all the mokuro manga titles with placeholder metadata and process OCR files')
parser_fetch_metadata.add_argument('--force', '-f', action='store_true', help='Force update')
parser_fetch_metadata.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

parser_mark_downloaded = subparsers.add_parser('mark_downloaded', help='Mark the manga as downloaded so Bilingual Manga can fetch it from the local server')
parser_mark_downloaded.add_argument('keyword', type=str, help='Title has to (partially) match the keyword in order to processed')

parser_remove = subparsers.add_parser('remove', help='Remove given title)')
parser_remove.add_argument('title_id', type=str, default=None, help='Title id')

parser_search = subparsers.add_parser('search', help='Search title/chapter_ids with given keyword')
parser_search.add_argument('-v', '--verbose', action='store_true', help='Show all subdirectory OIDs as well')
parser_search.add_argument('keyword', type=str, default=None, help='Keyword')

parser_show = subparsers.add_parser('show', help='Show list of all imported manga')

args = vars(parser.parse_args())
cmd = args.pop('command')

if cmd == 'scan':
    if args['source_dir'][-1] != '/':
        args['source_dir'] += '/'
    src_jp = args['source_dir'] + 'jp/'
    titles = [f_name for f_name in os.listdir(src_jp) if os.path.isdir(src_jp + f_name) and f_name != 'en']
    titles.sort()

ext_object_ids = dict()
oid_to_title = dict()
if os.path.exists(target_ext_oid_path):
    with open(target_ext_oid_path,'r',encoding="UTF-8") as oid_f:
        ext_object_ids = json.loads(oid_f.read())
    for title,oid in ext_object_ids.items():
        oid_to_title[oid] = title

def get_mokuro_id(path_str, create_new_if_not_found=True):
    # the path can be given in Unicode composed form (i.e. で)
    # or decomposed (i.e. て　+　゙	 mark).  The strings are stored in composed form
    path_str_composed = ud.normalize('NFC',path_str)
    if path_str in ext_object_ids:
        return ext_object_ids[path_str]
    if path_str_composed in ext_object_ids:
        return ext_object_ids[path_str_composed]

    if create_new_if_not_found:
        oid = str(bson.objectid.ObjectId())
        ext_object_ids[path_str_composed] = oid
        oid_to_title[oid] = path_str_composed
        print("\tNew OID [%s] %s" % (oid,path_str_composed))
        with open(target_ext_oid_path,'w',encoding="UTF-8") as oid_f:
            oid_f.write(json.dumps(ext_object_ids, ensure_ascii=False))
        return oid
    else:
        return None

j = 0
manga_metadata_per_id = dict()
manga_data_per_id = dict()
ext_mangaupdates = dict()

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


if os.path.exists(ext_mangaupdates_file):
    with open(ext_mangaupdates_file,"r",encoding="utf-8") as f:
        data = f.read()
        ext_mangaupdates = json.loads(data)
        for id,item in ext_mangaupdates.items():
            ext_mangaupdates[id] = item

def download_image(img_url,target_img_path):
    subprocess.run(['wget','--no-verbose',img_url,'-O',target_img_path])

def clean_name(name):
    s = ''
    for x in name:
        if x.isalnum():
            s += x
    return s

CLEANR = re.compile('<.*?>') 

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

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

def fetch_metadata_from_mangaupddates(title_id, title_root, t_metadata, t_data, force=False):
    if title_id not in ext_mangaupdates:
        print("\t[%s] %s not yet matched with mangaupdates.com" % (title_id,t_metadata['entit']))
        return False
    mangaupdates_id = ext_mangaupdates[title_id]['series_id']
    if mangaupdates_id == -1:
        print("Mangaupdates series id is set to NOT_FOUND! Removing stale data..")
        t_data['syn_en'] = PLACEHOLDER
        t_data['syn_jp'] = PLACEHOLDER
        t_metadata['jptit'] = PLACEHOLDER
        t_metadata['coverjp'] = PLACEHOLDER
        t_metadata['genres'] = []
        t_metadata['Author'] = [PLACEHOLDER]
        t_metadata['Artist'] = [PLACEHOLDER]
        t_metadata['Release'] = PLACEHOLDER
        t_metadata['Status'] = PLACEHOLDER
        t_metadata['search'] = PLACEHOLDER
        t_metadata['entit'] = title_root
        return True
    print("\tFetching metadata from mangaupdates.com")
    get_series_url = "http://api.mangaupdates.com/v1/series/"
    headers = {'Content-Type': 'application/json'}
    response = requests.get(get_series_url + str(mangaupdates_id), headers=headers, verify=False)
    r = response.json()

    entit = r['title']
    entit = entit.replace('&#039;',"'")
    entit = entit.replace('&quot;','"')
    t_metadata['entit'] = entit
    jptit = None

    img_url = r['image']['url']['original']
    if img_url is not None:
        suffix = img_url.split('.')[-1]
        target_img_name = clean_name(title_root)
        target_img_path = 'manga_cover/jp/' + target_img_name + '.' + suffix
        t_metadata['coverjp'] = target_img_path
        if not os.path.exists(target_img_path) or force:
            print("\tFetching cover image %s" % img_url)
            download_image(img_url,target_img_path)
    else:
        print("\t%s has no cover image" % entit)

    search_list = []
    for assoc_d in r['associated']:
        if 'title' in assoc_d:
            assoc_title = assoc_d['title']
            assoc_title = assoc_title.replace('&#039;',"'")
            assoc_title = assoc_title.replace('&quot;','"')
            assoc_title = assoc_title.replace('&amp;',"&")
            search_list.append(assoc_title)
            if jptit is None:
                if has_word_hiragana(assoc_title) or has_word_katakana(assoc_title) or has_cjk(assoc_title):
                    jptit = assoc_title
    if jptit is None:
        jptit = entit
    t_metadata['jptit'] = jptit
    t_metadata['search'] = ','.join(search_list)

    genre_list = []
    for genre_d in r['genres']:
        genre_list.append(genre_d['genre'])
    t_metadata['genres'] = genre_list
    t_metadata['Release'] = r['year']
    author_list = []
    artist_list = []
    for author_d in r['authors']:
        if author_d['type'] == 'Author':
            author_list.append(author_d['name'])
        if author_d['type'] == 'Artist':
            artist_list.append(author_d['name'])
    t_metadata['Author'] = author_list
    t_metadata['Artist'] = artist_list
    if 'Complete' in r['status']:
        t_metadata['Status'] = 'Completed'
    elif 'Ongoing' in r['status']:
        t_metadata['Status'] = 'On Going'
    elif 'Hiatus' in r['status']:
        t_metadata['Status'] = 'On Hold'
    elif 'Discontinued' in r['status']:
        t_metadata['Status'] = 'Discontinued'
    else:
        print(" ******* UNKNOWN STATUS: %s" % r['status'])
        t_metadata['Status'] = 'Unknown'

    syn = r['description']
    if syn is not None:
        syn = syn.replace('<BR>','\n')
        syn = syn.replace('&#039;',"'")
        syn = syn.replace('&amp;',"&")
        syn = syn.replace('&quot;','"')
        syn = cleanhtml(syn)
    else:
        syn = "NA"
    t_data['syn_en'] = syn
    t_data['syn_jp'] = syn

    t_metadata['fetched'] = True
    return True

PLACEHOLDER = 'Placeholder'

def fetch_metadata(args):
    for title_id, t_metadata in manga_metadata_per_id.items():

        title = oid_to_title[title_id]

        if args['keyword'] is not None and args['keyword'].lower() not in title.lower():
            continue

        t_data = manga_data_per_id[title_id]

        if t_metadata['fetched'] and not args['force']: # and '&q' not in t_metadata['entit']:
            continue

        print("Fetching metadata for %s [%s]" % (title,title_id))

        if fetch_metadata_from_mangaupddates(title_id,title,t_metadata,t_data,args['force']):
            save_metadata_files()


def save_metadata_files():
    target_f = open(ext_manga_data_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_data_per_id.values())))
    target_f.close()
    target_f = open(ext_manga_metadata_file,'w',encoding="UTF-8")
    target_f.write(json.dumps(list(manga_metadata_per_id.values())))
    target_f.close()

def mark_title_as_downloaded(title_id):
    dw_f = open(dw_file_path,'r',encoding="UTF-8")
    dw = json.loads(dw_f.read())
    dw_f.close()
    if title_id not in dw['pm']:
        print("Adding title_id [%s] to dw.json" % (title_id))
        dw['pm'].append(title_id)
        dw_f = open(dw_file_path,'w',encoding="UTF-8")
        dw_f.write(json.dumps(dw))
        dw_f.close()


def scan(args):
    for title in titles:

        if args['keyword'] is not None and args['keyword'].lower() not in title.lower():
            continue

        if args['simulate']:
            title_id = get_mokuro_id(title, create_new_if_not_found=False)
            if title_id is None:
                print("New title found: %s" % title)
            continue
                
        title_id = get_mokuro_id(title)

        if title_id in manga_metadata_per_id and title_id in manga_data_per_id and not args['force'] and not args['copy_images']:
            continue

        jp_title_path = args['source_dir'] + 'jp/' + title
        print("Processing title [%s]: %s " % (title_id, title))

        jp_volumes = [f_name[:-5] for f_name in os.listdir(jp_title_path) if '.html' in f_name and '.mobile.html' not in f_name and f_name != 'index.html' ]
        jp_volumes.sort()

        if os.path.exists(jp_title_path + '/en'):
            en_path = jp_title_path + '/en/'
        elif os.path.exists(args['source_dir'] + 'en/' + title):
            en_path = args['source_dir'] + 'en/' + title + '/'
        else:
            en_path = None

        if len(jp_volumes)==0:
            print("\tNo volumes found")
        else:

            if title_id not in manga_data_per_id:
                t_data = dict()
                t_data['_id'] = dict()
                t_data['_id']['$oid'] = title_id
                t_data['syn_en'] = PLACEHOLDER
                t_data['syn_jp'] = PLACEHOLDER
                t_data['en_data'] = dict()
                t_data['jp_data'] = dict()

                manga_data_per_id[title_id] = t_data 
            else:
                t_data = manga_data_per_id[title_id]

            if title_id not in manga_metadata_per_id:
                t_metadata = dict()
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

            if 'fetched' not in t_metadata or not t_metadata['fetched']:
                fetch_metadata_from_mangaupddates(title_id,title,t_metadata,t_data)

            if en_path is not None:
                en_volumes = [f_name for f_name in os.listdir(en_path) if os.path.isdir(en_path + f_name) ]
                en_volumes.sort()
            else:
                en_volumes = []

            t_data['en_data']['ch_naen'] = []
            t_data['en_data']['ch_enh'] = []
            t_data['en_data']['vol_en'] = dict()
            t_data['en_data']['ch_en'] = dict()
            ch_idx = 1
            vol_number = 1

            # copy english cover
            if en_path is not None:
                suffixes = ['jpg','jpeg','png','tiff']
                for suffix in suffixes:
                    en_cover_img_path = en_path + 'cover.' + suffix
                    if os.path.exists(en_cover_img_path):

                        target_img_name = clean_name(title) + '.' + suffix
                        target_img_path = 'manga_cover/en/'
                        copy_file(en_cover_img_path,target_img_path, target_img_name)
                        t_metadata['coveren'] = target_img_path + target_img_name

            if args['copy_images']:
                mark_title_as_downloaded(title_id)

            # process english volumes/chapters
            for vol in en_volumes:

                if 'olume' in vol:
                    vol_test = re.findall(r'.*olume[ _-]*([0-9]*[.]?[0-9])+', vol)
                    if len(vol_test)>0:
                        vol_number = int(vol_test[0])
                        if float(vol_test[0]) != vol_number:
                            vol_number = float(vol_test[0])                        

                vol_path = en_path + vol + '/'
                volume_dirs = [f_name for f_name in os.listdir(vol_path) if os.path.isdir(vol_path + f_name) ]
                volume_dirs.sort()
                volume_files = [f_name for f_name in os.listdir(vol_path) if os.path.isfile(vol_path + f_name) ]
                volume_files.sort()
                chapter_is_volume = True
                if len(volume_dirs):
                    chapter_is_volume = False
                vol_id = get_mokuro_id(title_id + '/en/' + vol)

                print("\tVolume [%s]: %s " % (vol_id, vol))

                vol_ipfs_path = target_ipfs_path + vol_id

                if not os.path.exists(vol_ipfs_path):
                    os.mkdir(vol_ipfs_path)

                vol_name = "Volume %s" % str(vol_number)
                if chapter_is_volume:
                    print("Volume (EN) %s with %d pages" % (str(vol_number),len(volume_files)))

                    t_data['en_data']['ch_naen'].append(vol_name)  # 1 chapter per volume
                    t_data['en_data']['ch_enh'].append(vol_id + '/%@rep@%')
                    t_data['en_data']['ch_en'][ch_idx] = []
                    t_data['en_data']['vol_en'][vol_name] = {'s':(ch_idx-1),'e':ch_idx-1}

                    for img in volume_files:
                        if args['copy_images']:
                            src_img_path = vol_path + '/' + img
                            copy_file(src_img_path, vol_ipfs_path, img)
                        t_data['en_data']['ch_en'][ch_idx].append(img)

                    ch_idx += 1
                else:
                    t_data['en_data']['vol_en'][vol_name] = {'s':(ch_idx-1),'e':ch_idx-2 + len(volume_dirs)}

                    for ch in volume_dirs:

                        ch_id = get_mokuro_id(title_id + '/en/' + vol_id + '/' + ch)

                        ch_number = ch_idx
                        if 'hapter' in ch:
                            ch_test = re.findall(r'.*hapter[ _-]*([0-9]*[.]?[0-9])+', ch)
                            if len(ch_test)>0:
                                try:
                                    ch_number = int(ch_test[0])
                                except:
                                    try:
                                        ch_number = float(ch_test[0])
                                    except:
                                        pass

                        ch_name = "Chapter %s" % str(ch_number)

                        t_data['en_data']['ch_naen'].append(ch_name)  # 1 chapter per volume
                        t_data['en_data']['ch_enh'].append(vol_id + '/' + ch_id + '/%@rep@%')
                        t_data['en_data']['ch_en'][ch_idx] = []

                        ch_path = vol_path + ch
                        ch_ipfs_path = vol_ipfs_path + '/' + ch_id + '/'
                        chapter_files = [f_name for f_name in os.listdir(ch_path) if os.path.isfile(ch_path + '/' + f_name) ]
                        chapter_files.sort()
                        print("Chapter (EN) %s with %d pages" % (str(ch_number),len(chapter_files)))
                        for img in chapter_files:
                            if args['copy_images']:
                                src_img_path = ch_path + '/' + img
                                copy_file(src_img_path, ch_ipfs_path, img)                
                            t_data['en_data']['ch_en'][ch_idx].append(img)

                        ch_idx += 1

                vol_number += 1

            # process jp volumes/chapters
            t_data['jp_data']['ch_najp'] = []
            t_data['jp_data']['ch_jph'] = []
            t_data['jp_data']['vol_jp']= dict()
            t_data['jp_data']['ch_jp'] = dict()
            vol_idx = 1
            for vol in jp_volumes:

                vol_dashed = vol.replace(' ','-')
                vol_id = get_mokuro_id(title_id + '/' + vol)

                print("\tVolume JP [%s]: %s " % (vol_id, vol))

                vol_name = "Volume %02d" % vol_idx
                t_data['jp_data']['ch_najp'].append(vol_name)  # 1 chapter per volume
                t_data['jp_data']['ch_jph'].append(vol_id + '/%@rep@%')
                t_data['jp_data']['ch_jp'][vol_idx] = []
                t_data['jp_data']['vol_jp'][vol_name] = {'s':(vol_idx-1),'e':vol_idx-1}

                vol_path = jp_title_path + '/' + vol

                # extracts image file names from the HTML file
                f_name = vol_path + '.html'
                html_f = open(f_name,'r',encoding="UTF-8")
                html_data = html_f.read()
                soup = BeautifulSoup(html_data,features="html.parser")
                pages = soup.find_all(class_='page')
                i = 1
                img_list = []
                ocr_dict = dict()
                target_ocr_file_path = target_ocr_path + vol_id + '.json'
                for page in pages:
                    pagecontainer = page.find(class_='pageContainer')
                    style = pagecontainer.get('style')
                    style_attrs = [s.strip() for s in style.split(';')]
                    for sa in style_attrs:
                        sal = sa.split(':')
                        if len(sal)==2:
                            attr = sal[0]
                            val = sal[1]
                            if attr == 'background-image':
                                sal2 = val.split('"') # get the image path in url('...')
                                if len(sal2)==3:
                                    _img = sal2[1]
                                    img_path = unquote(_img)
                                    img_list.append(img_path)
                                else:
                                    raise Exception("Unknown image url: " + sa)
                            elif attr == 'width':
                                img_width = val
                            elif attr == 'height':
                                img_height = val

                    img_filename = img_path.split('/')[-1]
                    img_ext = img_filename.split('.')[-1]
                    img_base = img_filename[:-(len(img_ext)+1)]

                    blocks = []
                    textboxes = pagecontainer.find_all(class_='textBox')
                    for textbox in textboxes:
                        style = textbox.get('style')
                        style_attrs = [s.strip() for s in style.split(';')]
                        b = dict()
                        for sa in style_attrs:
                            sal = sa.split(':')
                            if len(sal)==2:
                                attr = sal[0]
                                val = sal[1]
                                if attr != 'z-index':
                                    b[attr] = val
                        b['img_w'] = img_width
                        b['img_h'] = img_height
                        p_list = textbox.find_all('p')
                        lines = []
                        for p in p_list:
                            txt = p.get_text()
                            txt = txt.replace('\n','')
                            txt = txt.strip()
                            lines.append(txt)
                        b['lines'] = lines
                        blocks.append(b)

                        ocr_dict[img_base] = blocks

                print("\t.. with %d pages" % (len(img_list)))

                vol_ipfs_path = target_ipfs_path + vol_id

                # copy each image to destination IPFS folder
                for img_path in img_list:
                    img = img_path.split('/')[-1]
                    if args['copy_images']:
                        src_img_path = jp_title_path + '/' + img_path
                        copy_file(src_img_path, vol_ipfs_path, img)
                    t_data['jp_data']['ch_jp'][vol_idx].append(img)

                if not args['copy_images']:
                    print("\t\tWriting OCR file %s" % target_ocr_file_path)
                    target_ocr_f = open(target_ocr_file_path,'w',encoding="UTF-8")
                    target_ocr_f.write(json.dumps(ocr_dict))
                    target_ocr_f.close()

                vol_idx += 1

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

                if title_id in ext_mangaupdates:
                    del(ext_mangaupdates[title_id])
                    ext_mangaupdates[title_id] =  { "series_id":-1 }
                    print(" * Deleted also mangaupdates match")
                    f = open(ext_mangaupdates_file,"w",encoding="utf-8")
                    s = json.dumps(ext_mangaupdates)
                    f.write(s)
                    f.close()

    if not found:
        print("Title id %s not found!" % args['title_id'])

def search(args):
    saved_oids = []
    for title, title_id in ext_object_ids.items():
        if args['keyword'].lower() in title.lower():
            print("[%s] %s" % (title_id,title))
            if args['verbose']:
                saved_oids.append(title_id)
        if args['verbose']:
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

def mark_downloaded(args):
    for title_id, mdata in manga_metadata_per_id.items():
        entit = mdata['entit']
        if args['keyword'].lower() in entit.lower():
            mark_title_as_downloaded(title_id)

#FOR DEBUGGING
#fetch_metadata({'keyword':None,'force':False})
#fetch_metadata({'keyword':'look','force':True})
#remove({'title_id':'6664444753468576c994cdd7'})
#scan(args)

if cmd != None:
  locals()[cmd](args)
