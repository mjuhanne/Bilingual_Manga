# This scripts downloads all the OCR files for every volumes/chapters of every title from BilingualManga.org
# Existing downloaded files will be skipped
# You can 

import os
import subprocess
import json
import sys
import time

ocr_dir = "ocr/"
ocr_uri = 'https://cdn.bilingualmanga.org/ocr/'

manga_metadata_file = "json/admin.manga_metadata.json"
manga_data_file = "json/admin.manga_data.json"

manga_data = None
manga_metadata = None

volume_id_to_title_id = dict()
volume_id_to_volume_number = dict()
title_volumes = dict()
title_names = dict()
volume_page_count = dict()


with open(manga_metadata_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_metadata = json.loads(data)
    manga_titles = manga_metadata[0]['manga_titles']
    for t in manga_titles:
        title_id = t['enid']
        title_name = t['entit']
        title_names[title_id] = title_name

with open(manga_data_file,"r",encoding="utf-8") as f:
    data = f.read()
    manga_data = json.loads(data)
    for m in manga_data:
        title_id = m['_id']['$oid']
        volume_ids = m['jp_data']['ch_jph']
        volume_ids = [vid.split('/')[0] for vid in volume_ids]
        pages = m['jp_data']['ch_jp']
        title_volumes[title_id] = volume_ids
        for vid in volume_ids:
            vol = str(volume_ids.index(vid) + 1)
            volume_id_to_title_id[vid] = title_id
            volume_id_to_volume_number[vid] = volume_ids.index(vid) + 1
            volume_page_count[vid] = len(pages[vol])

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

    for title_id, title_name in title_names.items():

        if keyword is not None:
            if keyword.lower() not in title_name.lower():
                continue

        title_data = dict()
        title_data['title_id'] = title_id
        title_data['title'] = title_name

        title_data['num_characters'] = 0
        title_data['num_words'] = 0
        title_data['num_kanjis'] = 0
        title_data['num_pages'] = 0
        title_data['num_individual_words'] = 0
        title_data['num_individual_kanjis'] = 0
        title_data['word_frequency'] = dict()
        title_data['kanji_frequency'] = dict()

        vs = title_volumes[title_id]

        downloaded_count = 0

        for volume_id in vs:
            volume_ocr_filename = ocr_dir + volume_id + ".json"
            vol = volume_id_to_volume_number[volume_id]

            if os.path.exists(volume_ocr_filename):

                o_f = open(volume_ocr_filename,"r",encoding="utf-8")
                d=o_f.read()
                o_f.close()
                if '<head><title>404 Not Found</title></head>' in d:
                    print("404 error in existing file: %s volume %d [%s].. Re-downloading.." % (title_name, vol, volume_id))
                else:
                    try:
                        volume_data = json.loads(d)
                        continue
                    except:
                        print("Corrupt JSON in existing file: %s volume %d [%s].. Re-downloading.." % (title_name, vol, volume_id))
            
            print("Downloading %s [%d/%d]" % (title_name,vol,len(vs)))
            if not download(title_name, vol, volume_id):
                error_count += 1

            downloaded_count += 1
        
        if downloaded_count == 0:
            print(title_name + " was fully downloaded")

if len(sys.argv)>1:
    keyword = sys.argv[1]
else:
    keyword = None

download_titles(keyword)

print("Total errors: %d" % error_count)
