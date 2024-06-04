"""
"""

import os
import json
import sys
import argparse
from helper import *
from jmdict import *

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0

seq_count = dict()
priority_seq_count = dict()

def process_chapter(fo_p):
    global seq_count, priority_seq_count

    if not os.path.exists(fo_p):
        return
    
    f = open(fo_p, "r", encoding="utf-8")
    pages = json.loads(f.read())
    ignore_keys = ['parsed_data','version','parser_version']
    sorted_keys = sorted(list(pages.keys()))
    for key in sorted_keys:
        if key in ignore_keys:
            continue
        blocks = pages[key]
        for block in blocks:
            seqs = set()
            priority_seqs = set()
            for jl in block['jlines']:
                for part in jl:
                    refs = next(iter(part.values()))
                    p = next(iter(part.keys()))

                    for i,ref in enumerate(refs):
                        wid = pages['parsed_data']['word_id_list'][ref]
                        seq, word = get_seq_and_word_from_word_id(wid)

                        freq = get_frequency_by_seq_and_word(seq,word)
                        if freq < 99 or has_cjk(word) or len(word)>2:
                            seqs.update([seq])

                        if i == 0:
                            priority_seqs.update([seq])

            for seq in seqs:
                if seq not in seq_count:
                    seq_count[seq] = 1
                else:
                    seq_count[seq] += 1
            for seq in priority_seqs:
                if seq not in priority_seq_count:
                    priority_seq_count[seq] = 1
                else:
                    priority_seq_count[seq] += 1
        

        pass

    f.close()


def process_chapters():
    
    i = 0
    title_names = get_title_names()
    i_c = len(title_names)
    for title_id, title_name in title_names.items():

        i += 1
        chapters = get_chapters_by_title_id(title_id)

        for chapter_id in chapters:

            input_ocr_file = ocr_dir + str(chapter_id) + '.json'

            chapter_data = dict()
            chapter_data['title'] = get_title_by_id(title_id)
            chapter_data['chapter'] = get_chapter_number_by_chapter_id(chapter_id)
            chapter_data['num_pages'] =  get_chapter_page_count(chapter_id)

            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"
            
            #try:
            print("[%d/%d] Scanning %s [%d] " 
                % (i, i_c, chapter_data['title'], chapter_data['chapter']))

            process_chapter(parsed_ocr_filename)

        sorted_seqs = dict(sorted(seq_count.items(), key=lambda x:x[1], reverse=True))
        sorted_seqs = list(sorted_seqs.keys())  

        sorted_priority_seqs = dict(sorted(priority_seq_count.items(), key=lambda x:x[1], reverse=True))
        sorted_priority_seqs = list(sorted_priority_seqs.keys())  
        d = {'priority_seq_count':priority_seq_count,'seq_count':seq_count,'sorted_priority_freq_list':sorted_priority_seqs,'sorted_freq_list':sorted_seqs}
        o_f = open("lang/seq_count.json","w",encoding="utf-8")
        json_data = json.dumps(d,  ensure_ascii = False)
        o_f.write(json_data)
        o_f.close()




read_manga_metadata()
read_manga_data()

load_jmdict()

process_chapters()

