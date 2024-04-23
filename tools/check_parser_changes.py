"""
"""

import os
import json
import sys
import argparse
from helper import *
from jp_parser import (
    init_scan_results, parse_block_with_unidic, post_process_unidic_particles, parse_with_jmdict, 
    init_parser, reassemble_block, expand_word_id, #, get_highest_freq_class_list_with_particle_priority,
    get_flat_class_list_by_seq, get_sense_meanings_by_seq, load_manga_specific_adjustments,
    unidic_class_list, ignored_classes_for_freq
)
from jmdict import get_frequency_by_seq_and_word
from bm_learning_engine_helper import read_user_settings
# for loggin
from jp_parser import open_log_file, close_log_file, set_verbose_level
import time

user_settings = read_user_settings()
chapter_comprehension = user_settings['chapter_reading_status']

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0

item_must_match = False

def is_chapter_read(cid):
    for chapter_id, reading_data in chapter_comprehension.items():
        if chapter_id == cid:
            if reading_data['status'] == 'Read':
                return True
            if reading_data['status'] == 'Reading':
                return True
    return False

def is_title_read(id):
    chapter_ids = get_chapters_by_title_id(id)
    for cid in chapter_ids:
        if is_chapter_read(cid):
            return True


def does_word_id_match(new_wid,prev_wid):
    if new_wid == prev_wid:
        return True
    new_seq_sense = new_wid.split(':')[0]
    prev_seq_sense = prev_wid.split(':')[0]
    if new_seq_sense == prev_seq_sense:
        return True
    new_s = new_seq_sense.split('/')
    prev_s = prev_seq_sense.split('/')
    if len(new_s)==1:
        if new_s[0] == prev_s[0]:
            return True
    return False

all_mismatches = []
mismatch_count = dict()
def process_chapter(f_p, fo_p, chapter_data):
    global all_mismatches, mismatch_count

    k_c = 0
    c_c = 0
    skipped_c = 0

    results = init_scan_results()
    kanji_count = dict()

    if not os.path.exists(f_p):
        print("%s does not exist! Skipping.." % f_p)
        return 0,0,0,0
    f = open(f_p, "r", encoding="utf-8")
    f_data = f.read()
    f.close()

    pages = json.loads(f_data)
    page_count = 0
    progress_bar_interval = int(len(pages)/10)
    if progress_bar_interval == 0:
        progress_bar_interval = 1
    for page_id,blocks in pages.items():

        for block in blocks:
            lines = block['lines']

            if any(len(l)>32 for l in lines):
                # Blocks with any number of very long lines have usually been 
                # incorrectly recognized so ignore these
                skipped_c += 1
                block['jlines'] = []
            else:
                line = ''.join(lines)

                if '飲まさ' in line:
                    pass

                #for line in lines:
                kc, ud_items, mismatch = \
                    parse_block_with_unidic(lines, kanji_count)

                k_c += kc
                c_c += len(line)

                ud_items = \
                    post_process_unidic_particles(ud_items)

                parse_with_jmdict(
                    ud_items, results,
                )

                block['jlines'] = reassemble_block(lines, ud_items, results['item_word_id_refs'])

        page_count += 1
        if page_count % progress_bar_interval == 0:
            print(".",end='',flush=True)

    pages['parsed_data'] = results
    pages['version'] = CURRENT_PARSED_OCR_VERSION
    pages['parser_version'] = CURRENT_LANUGAGE_PARSER_VERSION

    # the total word count excluding words belonging to ignored classes 
    # (alphanumeric words, punctuation, auxialiary verbs, grammatical particles)
    w_c = sum([results['word_count_per_unidict_class'][i] for i in range(len(unidic_class_list)) if unidic_class_list[i] not in ignored_classes_for_freq])

    f = open(fo_p, "r", encoding="utf-8")
    prev_data = json.loads(f.read())
    ignore_keys = ['parsed_data','version','parser_version']
    sorted_keys = sorted(list(pages.keys()))
    page = 0
    for key in sorted_keys:
        if key in ignore_keys:
            continue
        ch = chapter_data['chapter'] - 1
        url = 'http://localhost:5173/manga/%s?lang=jp&chen=%d&chjp=%d&enp=%d&jpp=%d#img_store' \
            % (chapter_data['title_id'],ch,ch,page,page)
        page += 1
        new_blocks = pages[key]
        prev_blocks = prev_data[key]
        for new_block, prev_block in zip(new_blocks,prev_blocks):
            mismatch = False
            mismatch_elems = []
            mismatched_new_elems = []
            for new_jl, prev_jl in zip(new_block['jlines'], prev_block['jlines']):
                new_jl_i = 0
                prev_jl_i = 0
                sub_i = 0
                #for new_part, prev_part in zip(new_jl,prev_jl):
                while new_jl_i < len(new_jl):
                    new_part = new_jl[new_jl_i]
                    prev_part = prev_jl[prev_jl_i]
                    new_refs = next(iter(new_part.values()))
                    prev_refs = next(iter(prev_part.values()))
                    new_p = next(iter(new_part.keys()))
                    prev_p = next(iter(prev_part.keys()))

                    new_wid = '()'
                    if len(new_refs)>0:
                        new_wid = pages['parsed_data']['word_id_list'][new_refs[0]]
                    prev_wid = '()'
                    if len(prev_refs)>0:
                        prev_wid = prev_data['parsed_data']['word_id_list'][prev_refs[0]]

                    if new_p == prev_p:
                        new_jl_i += 1
                        prev_jl_i += 1
                    elif new_p in prev_p:
                        new_jl_i += 1
                        sub_i += len(new_p)
                        #if prev_p[-len(new_p):] == new_p:
                        if sub_i == len(prev_p):
                            prev_jl_i += 1
                            sub_i = 0
                    elif prev_p in new_p:
                        prev_jl_i += 1
                        sub_i += len(prev_p)
                        #if new_p[-len(prev_p):] == prev_p:
                        if sub_i == len(new_p):
                            new_jl_i += 1
                            sub_i = 0
                    else:
                        print('\n' + str([next(iter(p.keys())) for p in new_jl]))
                        print(str([next(iter(p.keys())) for p in prev_jl]))
                        raise Exception("mismatch: %s vs %s" % (new_p,prev_p))

                    if not does_word_id_match(new_wid,prev_wid) or (item_must_match and new_p != prev_p):
                        mismatch = True
                        mismatch_elems.append((new_p,new_wid,prev_p,prev_wid))
                        mismatched_new_elems.append((new_p,new_wid))

            if mismatch:
                if mismatch_elems in all_mismatches:
                    for m in mismatched_new_elems:
                        if m not in mismatch_count:
                            mismatch_count[m] = 1
                        else:
                            mismatch_count[m] += 1
                    pass
                else:
                    all_mismatches.append(mismatch_elems)
                    for m in mismatched_new_elems:
                        if m not in mismatch_count:
                            mismatch_count[m] = 1
                        else:
                            mismatch_count[m] += 1
                    print('\n[%s] %s %s' % (key,str(new_block['lines']).replace("'",'"'),url))
                    for new_jl, prev_jl in zip(new_block['jlines'], prev_block['jlines']):
                        if len(new_jl) != len(prev_jl):
                            pass
                        prev_i = 0
                        for i, new_part in enumerate(new_jl):
                            new_refs = next(iter(new_part.values()))
                            new_p = next(iter(new_part.keys()))

                            new_wid = '()'
                            if len(new_refs)>0:
                                new_wid = pages['parsed_data']['word_id_list'][new_refs[0]]
                            prev_wid = '()'
                            if prev_i < len(prev_jl):
                                prev_part = prev_jl[prev_i]
                                prev_p = next(iter(prev_part.keys()))
                                prev_refs = next(iter(prev_part.values()))
                                if len(prev_refs)>0:
                                    prev_wid = prev_data['parsed_data']['word_id_list'][prev_refs[0]]

                            p = new_p
                            p2 = ''
                            if new_p != prev_p:
                                if prev_p in new_p:
                                    #print(new_p,"missing from old set",prev_p)
                                    p2 = prev_p + '\t'
                                    prev_i += 1
                                elif new_p in prev_p:
                                    #print(prev_p,"missing from new set",new_p)
                                    if prev_p.index(new_p) < len(prev_p) - len(new_p):
                                        prev_i -= 1
                                    p2 = prev_p+ '\t'
                        
                            prev_i += 1

                            new_meaning = ''
                            prev_meaning = ''
                            new_freq = ''
                            prev_freq = ''
                            mark = ''
                            if new_wid != prev_wid:
                                
                                if does_word_id_match(new_wid,prev_wid):
                                    mark = '!'
                                else:
                                    mark = '!!!'
                                    if new_wid != '()':
                                        new_seq,new_word = get_seq_and_word_from_word_id(new_wid)
                                        new_sense_meanings = get_sense_meanings_by_seq(new_seq)
                                        new_meaning = '(' + new_sense_meanings[0][0] + ')'
                                        new_freq = '[%d]' % (get_frequency_by_seq_and_word(new_seq,new_word))
                                    if prev_wid != '()':
                                        prev_seq,prev_word = get_seq_and_word_from_word_id(prev_wid)
                                        try:
                                            prev_sense_meanings = get_sense_meanings_by_seq(prev_seq)
                                            prev_freq = '[%d]' % (get_frequency_by_seq_and_word(prev_seq, prev_word))
                                        except:
                                            prev_sense_meanings = [['N/A']]
                                            prev_freq = '[N/A]'
                                        prev_meaning =  '(' + prev_sense_meanings[0][0]+ ')'
                            else:
                                if p2 != '':
                                    mark = '!!'
                            print("\t%s\t%s\t%s%s%s\t%s%s%s%s" % (mark,new_p,new_wid,new_meaning,new_freq,p2,prev_wid,prev_meaning,prev_freq))
                    pass
    f.close()

    return c_c, w_c, k_c, skipped_c

def check_chapters(args):
    

    i = 0
    title_names = get_title_names()
    i_c = len(title_names)
    for title_id, title_name in title_names.items():

      if args['keyword'] is None or args['keyword'].lower() in title_name.lower():

        load_manga_specific_adjustments(title_name)

        i += 1
        chapters = get_chapters_by_title_id(title_id)

        for chapter_id in chapters:


            input_ocr_file = ocr_dir + str(chapter_id) + '.json'

            chapter_data = dict()
            chapter_data['title'] = get_title_by_id(title_id)
            chapter_data['chapter'] = get_chapter_number_by_chapter_id(chapter_id)
            chapter_data['num_pages'] =  get_chapter_page_count(chapter_id)
            chapter_data['title_id'] = title_id

            if args['read'] and not is_chapter_read(chapter_id):
                continue

            if args['chapter'] is not None and chapter_data['chapter'] != args['chapter']:
                continue

            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"
            
            #try:
            print("[%d/%d] Scanning %s [%d] " 
                % (i, i_c, chapter_data['title'], chapter_data['chapter']),end='')

            c_c, w_c, k_c, skipped_c = process_chapter(input_ocr_file, parsed_ocr_filename, chapter_data)


read_manga_metadata()
read_manga_data()


parser = argparse.ArgumentParser(
    prog="check_parser_changes",
    description="",
)

parser.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')
parser.add_argument('--read', '-r', action='store_true', help='Process only read chapters')
parser.add_argument('--chapter', '-ch',  nargs='?', type=int, default=None, help='Chapter')

args = vars(parser.parse_args())

init_parser(load_meanings=True)

open_log_file("ocr-log.txt")
set_verbose_level(0)
t = time.time()

#args['keyword'] = 'hina'
#args['chapter'] = 6
#args['read'] = True

check_chapters(args)

t2 =  time.time()
print("Elapsed ",(t2-t))
close_log_file()


for mismatch,count in mismatch_count.items():
    print(mismatch,count)
#print("Total errors: %d. Processed %d titles and %d chapters" % (error_count, processed_title_count, processed_chapter_count))
