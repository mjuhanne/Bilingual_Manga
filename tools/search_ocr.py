"""
Search OCR file contents
"""

import os
import json
import sys
import argparse
from helper import *
from jp_parser import (
    init_scan_results, parse_block_with_unidic, post_process_unidic_particles, parse_with_jmdict, 
    init_parser, reassemble_block,
    unidic_class_name_strings,
    pretty_print_lexical_item,
)
from bm_learning_engine_helper import read_user_settings
# for loggin
from jp_parser import open_log_file, close_log_file, set_verbose_level
from jp_parser_print import print_scanning_results
import time

user_settings = read_user_settings()
chapter_comprehension = user_settings['chapter_reading_status']

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0

selected_class = None
keyword = None

shown_chapter = ''
shown_page = ''

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

def show_source(chapter_data, page_id):
    global shown_page, shown_chapter
    ch = "%s [%d]" % (chapter_data['title'],chapter_data['chapter'])
    if shown_chapter != ch:
        shown_chapter = ch
        print("-- %s [%d] " 
            % (chapter_data['title'], chapter_data['chapter']))
    if shown_page != page_id:
        print(page_id)
        shown_page = page_id

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

                if args['parse'] or args['jmdparse'] or args['item']:

                    kc, ud_items = \
                        parse_block_with_unidic(lines, kanji_count)

                    ud_items = \
                        post_process_unidic_particles(ud_items)
                    
                    match = False
                    if args['item']:
                        for item in ud_items:
                            if selected_class is None or selected_class in ud_items.classes:
                                if keyword == item.txt:
                                    match = True
                                    item.color = bcolors.OKBLUE
                    else:
                        if keyword in line:
                            match = True

                    if match:
                        colored_line = ''
                        if args['item']:
                            for item in ud_items:
                                if item.color is not None:
                                    colored_line += item.color + item.txt + bcolors.ENDC
                                else:
                                    colored_line += item.txt
                        else:
                            colored_line = line.replace(keyword, bcolors.OKBLUE + keyword + bcolors.ENDC)
                        print("\t",colored_line)
                        show_source(chapter_data,page_id)
                        if args['parse'] or args['jmdparse']:
                            for item in ud_items:
                                pretty_print_lexical_item(item)

                        if args['jmdparse']:
                            parse_with_jmdict(
                                ud_items, results,
                            )
                            jlines = reassemble_block(lines, ud_items, results['item_word_id_refs'])
                            print_scanning_results(jlines, results, ud_items)

                else:
                    # basic free text search
                    if keyword in line:
                        show_source(chapter_data,page_id)
                        line = line.replace(keyword, bcolors.OKBLUE + keyword + bcolors.ENDC)
                        print("\t",line)


def check_chapters(args):
    

    i = 0
    title_names = get_title_names()
    i_c = len(title_names)
    for title_id, title_name in title_names.items():

      if args['title'] is None or args['title'].lower() in title_name.lower():

        i += 1
        chapters = get_chapters_by_title_id(title_id)

        for chapter_id in chapters:

            input_ocr_file = ocr_dir + str(chapter_id) + '.json'

            chapter_data = dict()
            chapter_data['title'] = get_title_by_id(title_id)
            chapter_data['chapter'] = get_chapter_number_by_chapter_id(chapter_id)
            chapter_data['num_pages'] =  get_chapter_page_count(chapter_id)

            if args['read'] and not is_chapter_read(chapter_id):
                continue

            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"
            process_chapter(input_ocr_file, parsed_ocr_filename, chapter_data)


init_parser(load_meanings=True)

read_manga_metadata()
read_manga_data()


parser = argparse.ArgumentParser(
    prog="search OCR files for text or lexical elements",
    description="",
)

parser.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')
parser.add_argument('--item', '-i', action='store_true', help='Match only distinct Lexical items')
parser.add_argument('--parse', '-p', action='store_true', help='Parse block with Unidict and show results')
parser.add_argument('--jmdparse', '-pp', action='store_true', help='Parse block with Unidict and JMDict and show results')
parser.add_argument('--class', '-c', default=None, help='Match only Lexical items with given class')
parser.add_argument('--first', '-1', action='store_true', help='Process only first chapter per title')
parser.add_argument('--read', '-r', action='store_true', help='Process only read chapters')
parser.add_argument('--title', '-t', default=None, help='Title has to (partially) match the keyword in order to processed')

args = vars(parser.parse_args())

if args['class'] is not None:
    for cl,class_name in unidic_class_name_strings.items():
        if args['class'] in class_name:
            selected_class = cl
            print("Selected class",class_name)
    if selected_class is None:
        print("No such class found!")
        exit(1)

#args['keyword'] = 'んなくちゃ'
#args['title'] = 'hina'
#args['parse'] = True
keyword = args['keyword']


if args['parse']:
    init_parser(load_meanings=True)

open_log_file("ocr-log.txt")
set_verbose_level(0)


check_chapters(args)

close_log_file()

