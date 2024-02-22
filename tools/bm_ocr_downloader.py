# This scripts downloads all the OCR files for every volumes/chapters of every title from BilingualManga.org
# Existing downloaded files will be skipped

import os
import subprocess
import json
import sys
import time

from helper import *

error_count = 0

def download(title_name,vol,volume_id):
    url = ocr_uri + volume_id + '.json'
    subprocess.run(['wget','--no-verbose',url,'-O','temp'])
    time.sleep(1)
    f = open('temp','r')
    data = f.read()
    f.close()
    if '<head><title>404 Not Found</title></head>' in data:
        print("404 error in downloaded file: %s volume %d [%s].." % (title_name, vol, volume_id))
        return False
    try:
        volume_data = json.loads(data)
        ocr_p = ocr_dir + volume_id + '.json'

    except:
        print("Corrupt JSON in downloaded file: %s volume %d [%s].. Re-downloading.." % (title_name, vol, volume_id))
        return False
    subprocess.run(['mv','temp',ocr_p])
    return True


def download_titles(keyword):
    global error_count

    for title_id, title_name in get_title_names().items():

        if keyword is not None:
            if keyword.lower() not in title_name.lower():
                continue

        chapters = get_chapters_by_title_id(title_id)

        downloaded_count = 0

        for chapter_id in chapters:
            chapter_ocr_filename = ocr_dir + chapter_id + ".json"
            chapter = get_chapter_number_by_chapter_id(chapter_id)

            if os.path.exists(chapter_ocr_filename):

                o_f = open(chapter_ocr_filename,"r",encoding="utf-8")
                d=o_f.read()
                o_f.close()
                if '<head><title>404 Not Found</title></head>' in d:
                    print("404 error in existing file: %s chapter %d [%s].. Re-downloading.." % (title_name, chapter, chapter_id))
                else:
                    try:
                        volume_data = json.loads(d)
                        continue
                    except:
                        print("Corrupt JSON in existing file: %s volume %d [%s].. Re-downloading.." % (title_name, chapter, chapter_id))
            
            print("Downloading %s [%d/%d]" % (title_name,chapter,len(chapters)))
            if not download(title_name, chapter, chapter_id):
                error_count += 1

            downloaded_count += 1
        
        if downloaded_count == 0:
            print(title_name + " was fully downloaded")

read_manga_metadata()
read_manga_data()

if len(sys.argv)>1:
    keyword = sys.argv[1]
else:
    keyword = None

download_titles(keyword)

print("Total errors: %d" % error_count)
