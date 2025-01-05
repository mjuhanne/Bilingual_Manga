import os
import unicodedata as ud
import json
import bson
import re
import subprocess
import hashlib
import shutil

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
    "(.*)\s*_+\(*(Kindle Single)\)*"
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
