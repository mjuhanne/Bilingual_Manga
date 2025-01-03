from bm_learning_engine_helper import read_user_settings
import os
from helper import *

user_settings = read_user_settings()
ocr_corrections_file = base_dir + "json/ocr_corrections.json"

ocr_corrections = {}
if os.path.exists(ocr_corrections_file):
    f = open(ocr_corrections_file, "r", encoding="utf-8")
    ocr_corrections = json.loads(f.read())
    f.close()

        
def apply_ocr_correction(chapter_id,page_id,block_num,lines):
    if chapter_id in ocr_corrections['block_errata']:
        correction_list = ocr_corrections['block_errata'][chapter_id]
        for correction in correction_list:
            if page_id == correction['pr'] and block_num == correction['b']:
                if ''.join(lines) == ''.join(correction['old_block']):
                    print("Applied correction %s -> %s on page ref [%s]" % (lines,correction['new_block'],page_id))
                    return correction['new_block']
                else:
                    print("Correction %s doesn't match old block %s" % (str(correction),str(lines)))
                    return lines
    return lines

def do_get_priority_word_ids(corrections,page_id=None,block_num=None):
    ids = []
    for word_data in corrections:
        if word_data['pr'] == 'ALL' or word_data['pr'] == page_id:
            if 'bid' not in word_data or word_data['bid'] == block_num:
                ids.append(word_data['wid'])
    return ids

def get_manually_set_priority_word_ids(title_id,chapter_id,page_id,block_num):
    word_ids = []
    if 'ALL' in ocr_corrections['word_id_errata']:
        word_ids += do_get_priority_word_ids(ocr_corrections['word_id_errata']['ALL'])
    if title_id in ocr_corrections['word_id_errata']:
        word_ids += do_get_priority_word_ids(ocr_corrections['word_id_errata'][title_id])
    if chapter_id in ocr_corrections['word_id_errata']:
        word_ids += do_get_priority_word_ids(ocr_corrections['word_id_errata'][chapter_id],page_id,block_num)
    return word_ids
