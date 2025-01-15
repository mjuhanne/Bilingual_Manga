import os
import unicodedata as ud
import json
import bson
import re
import subprocess
import hashlib
import shutil
import time
from helper import *

PLACEHOLDER = 'Placeholder'

target_ocr_path = 'ocr/'
target_ipfs_path = 'ipfs/'

create_new_titles_override = False
create_new_volumes_override = ''
create_new_chapter_override = ''

def create_oid(path_str, oid_type, ask_confirmation=True, title_id=None, vol_id=None):
    global create_new_titles_override, create_new_volumes_override, create_new_chapter_override
    if ask_confirmation:
        print("Creating new %s OID from '%s'" % (oid_type,path_str))
        if oid_type == "title":
            if not create_new_titles_override:
                ans = input("OK (y=this title, n=no, a=all titles ?")
                if ans == 'a':
                    create_new_titles_override = True 
                elif ans != 'y':
                    return None
        elif oid_type == "volume":
            if create_new_volumes_override == 'all_volumes' or create_new_volumes_override == title_id:
                pass
            else:
                ans = input("OK (y=this volume, n=no, a=all volumes in this title, A=all volumes in all titles?")
                if ans == 'a':
                    create_new_volumes_override = title_id
                elif ans == 'A':
                    create_new_volumes_override = 'all_volumes'
                elif ans != 'y':
                    return None
        elif oid_type == "chapter":
            if create_new_chapter_override == 'all_chapters' or create_new_chapter_override == title_id or create_new_chapter_override == vol_id:
                pass
            else:
                ans = input("OK (y=this chapter, n=no, a=all chapters in this volume, A=all chapters in all volumes?")
                if ans == 'a':
                    create_new_chapter_override = vol_id
                elif ans == 'A':
                    create_new_chapter_override = 'all_chapters'
                elif ans != 'y':
                    return None

    oid = str(bson.objectid.ObjectId())
    print("\tNew OID [%s] %s" % (oid,path_str))
    return oid


def download_image(img_url,target_img_path):
    subprocess.run(['wget','--no-verbose',img_url,'-O',target_img_path])

def get_virtual_page_count_from_characters(num_characters):
    # calculate rough estimate of page count assuming that each page has 550 characters on average
    return int(num_characters/550) + 1

def get_virtual_page_count_from_words(num_words):
    return int(num_words/250) + 1

def save_chapter_pages(chapter_id, chapter_pages):
    if len(chapter_pages) == 0:
        return
    text = ''.join(chapter_pages)
    text = text.replace('<body>','<div class="page">')
    text = text.replace('</body>','</div>')
    if not os.path.exists(target_ipfs_path):
        os.mkdir(target_ipfs_path)
    ch_ipfs_path = target_ipfs_path + chapter_id
    if not os.path.exists(ch_ipfs_path):
        os.mkdir(ch_ipfs_path)
    item_f = open(ch_ipfs_path + '/' + "pages.html",'w',encoding="UTF-8")
    item_f.write(text)
    item_f.close()

def convert_vertical_to_horizontal(lines):
    new_lines = []
    for line in lines:
        line = line.replace('︱','ー')
        line = line.replace('﹃','『')
        line = line.replace('﹄','』')
        line = line.replace('︻','【')
        line = line.replace('︼','】')
        line = line.replace('﹁','「')
        line = line.replace('﹂','」')
        line = line.replace('︶','）')
        line = line.replace('︵','（')
        line = line.replace('︿','〈')
        line = line.replace('﹀','〉')
        
        new_lines.append(line)
    return new_lines

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

publisher_regex = [
    "(.*)\s*_+\(*(.*文庫)\)*",
    "(.*)\s*_+\(*(.*文庫)\)*",
    "(.*)_*【(.*文庫版*)】",
    "(.*)\s*_+\(*(Kindle Single)\)*",
    "(.*)\s*_*\((.*文庫.*)\)"
]

def extract_publisher_from_title(title):
        
    # if possible, extract publisher from the title
    publisher = None
    clean_title = title

    for regex in publisher_regex:
        res = re.search(regex,clean_title)
        if res is not None:
            gr = res.groups()
            clean_title = gr[0]
            publisher = gr[1]
            return clean_title, publisher
        
    clean_title = clean_title.replace('Amazonキンドル','')
    clean_title = clean_title.replace('ダイレクト出版紙の本執筆虎の巻','')
        
    return clean_title, publisher

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


def show_diff(old_data, new_data):
    for key, data in new_data.items():
        if key in old_data:
            if old_data[key] != new_data[key]:
                print("Old %s: " % key,old_data[key])
                print("New %s: " % key,new_data[key])
        else:
            print("Totally new %s: " % key,new_data[key])

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_metadata(title_id, t_metadata, t_data, verbose):
    if t_metadata is not None:
        old_metadata = get_metadata_by_title_id(title_id)
        if old_metadata is not None and verbose:
            show_diff(old_metadata, t_metadata)
        t_metadata['updated_timestamp'] = int(time.time())
        database[BR_METADATA].update_one({'_id':title_id},{'$set':t_metadata},upsert=True)
    if t_data is not None:
        old_data = get_data_by_title_id(title_id)
        if old_data is not None and verbose:
            show_diff(old_data, t_data)
        t_data = json.loads(json.dumps(t_data))
        t_data['updated_timestamp'] = int(time.time())
        database[BR_DATA].update_one({'_id':title_id},{'$set':t_data},upsert=True)


def remove_volume(title_id, vol_id, lang='jp'):
    chapters = get_chapters_by_volume_id(vol_id)
    t_data = get_data_by_title_id(title_id)
    vol_name = get_volume_name(vol_id)

    vol_field = 'vol_' + lang
    lang_data = t_data[lang + '_data']
    vol_data = lang_data[vol_field]

    if len(vol_data)>1:
        raise Exception("TODO: Handle titles with more than 1 volume")

    vd = vol_data[vol_name]
    ch_name_field = 'ch_na' + lang
    ch_files_field = 'ch_' + lang
    ch_ids_field = 'ch_' + lang + 'h'

    if vd['id'] != vol_id:
        print(vd)
        raise Exception("Inconsistent vol data!")

    for ch_idx, ch_id_f  in enumerate(lang_data[ch_ids_field]):
        ch_id = ch_id_f.split('/')[0]
        ch_files = lang_data[ch_files_field][str(ch_idx+1)]
        if ch_id in chapters:
            print("Removing chapter %s content" % ch_id)
            for filename in ch_files:
                f_path = target_ipfs_path + ch_id + '/' + filename
                if os.path.exists(f_path):
                    os.remove(f_path)
            if os.path.exists(target_ipfs_path + ch_id):
                os.rmdir(target_ipfs_path + ch_id)
    
    # Just reset the chapters and volumes for now
    lang_data[ch_name_field] = []
    lang_data[ch_ids_field] = []
    lang_data[ch_files_field] = {}
    lang_data[vol_field] = {}
    lang_data['virtual_chapter_page_count'] = []

    database[BR_CHAPTER_LOOKUP_TABLE].delete_many({'title_id':title_id,'vol_id':vol_id})
    save_metadata(title_id, None, t_data, True)
