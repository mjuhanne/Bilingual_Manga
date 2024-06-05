"""
This script is used to process BilingualManga.org OCR files (in /ocr directory) and
calculate word and kanji frequencies as well as their cumulative values.
Each chapter(volume/tankobon) OCR file is processed first and then aggregate values 
are saved for each manga title.

These analysis JSON files are saved into lang/volumes and lang/titles directories correspondingly.

Also a set of separate parsed OCR files are saved into './parsed_ocr' directory. These files
will have word-to-word separation in OCR lines and allow for visualization and changing of the
learning stage of each word separately.

Because the original AI based OCR tool most likely didn't handle well the larger text sections
these are ignored (marked as 'skipped blocks'). The blocks are ignored in statistics and also
in the parsed OCR files.

Using this script requires installing following dependencies:

Fugashi:
    pip install fugashi[unidic-lite]

    # The full version of UniDic requires a separate download step
    pip install fugashi[unidic]
    python -m unidic download

JMdict:
    tools/install_jmdict.sh
    python tools/process_jmdict.py

"""

import os
import json
import sys
import argparse
from helper import *
from jp_parser import (
    init_scan_results, parse_block_with_unidic, post_process_unidic_particles, parse_with_jmdict, 
    init_parser, reassemble_block, expand_word_id, #, get_highest_freq_class_list_with_particle_priority,
    get_flat_class_list_by_seq, load_manga_specific_adjustments,
    unidic_class_list, ignored_classes_for_freq
)
from bm_learning_engine_helper import read_user_settings

user_settings = read_user_settings()
chapter_comprehension = user_settings['chapter_reading_status']

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0

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
        
def process_chapter(f_p, fo_p, chapter_data):

    k_c = 0
    c_c = 0
    skipped_c = 0

    results = init_scan_results()
    kanji_count = dict()

    f = open(f_p, "r", encoding="utf-8")
    f_data = f.read()
    f.close()

    if '<head><title>404 Not Found</title></head>' in f_data:
        os.remove(f_p)
        raise Exception("404 error! Deleted file %s.." % f_p)
    
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

    f = open(fo_p, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()

    #sorted_word_count = dict(sorted(unique_jmdict_word_count.items(), key=lambda x:x[1], reverse=True))
    sorted_kanji_count = dict(sorted(kanji_count.items(), key=lambda x:x[1], reverse=True))

    # create a list of unique words (word_ids) and their amount 
    # (senses are pooled so only seq numbers count)
    unique_words_list = []
    unique_words_frequency = []
    unique_words_classes = []
    wid_to_unique_wid_dict = dict()
    for word_id, word_freq in \
        zip(results['priority_word_id_list'], results['priority_word_count']):
        #zip(results['word_id_list'], results['word_count']):
        seq,senses,word = expand_word_id(word_id)
        word_id0 = str(seq) + ':' + word
        if word_id0 in unique_words_list:
            idx = unique_words_list.index(word_id0)
            unique_words_frequency[idx] += word_freq
        else:
            unique_words_list.append(word_id0)
            idx = len(unique_words_list) - 1
            unique_words_frequency.append(word_freq)
            unique_words_classes.append( get_flat_class_list_by_seq(seq) )
        wid_to_unique_wid_dict[word_id] = idx

    num_unique_words = len(unique_words_list)

    # convert the references in sentence list to match unique word list
    adjusted_sentence_list = []
    for sentence in results['sentence_list']:
        new_sentence = []
        for ref in sentence:
            wid = results['word_id_list'][ref]
            new_ref = wid_to_unique_wid_dict[wid]
            new_sentence.append(new_ref)
        adjusted_sentence_list.append(new_sentence)

    chapter_data['num_characters'] = c_c
    chapter_data['num_words'] = w_c
    chapter_data['num_kanjis'] = k_c
    chapter_data['num_sentences'] = len(adjusted_sentence_list)
    chapter_data['num_skipped_blocks'] = skipped_c
    chapter_data['num_unique_words'] = num_unique_words
    chapter_data['num_unique_kanjis'] = len(sorted_kanji_count)
    chapter_data['word_frequency'] = unique_words_frequency
    chapter_data['kanji_frequency'] = sorted_kanji_count
    chapter_data['word_id_list'] = unique_words_list
    chapter_data['word_class_list'] = unique_words_classes
    chapter_data['word_count_per_class'] = results['word_count_per_unidict_class']
    chapter_data['sentence_list'] = adjusted_sentence_list
    chapter_data['parser_version'] = CURRENT_LANUGAGE_PARSER_VERSION

    return c_c, w_c, k_c, skipped_c

def is_file_up_to_date(filename, version, parser_version):

    try:
        if os.path.exists(filename):
            f = open(filename, "r", encoding="utf-8")
            temp_data = json.loads(f.read())
            f.close()
            if 'version' not in temp_data:
                return False
            if 'parser_version' not in temp_data:
                return False
            if temp_data['version'] < version:
                return False
            if temp_data['parser_version'] < parser_version:
                return False
            return True
    except:
        pass
    return False

def process_chapters(args):
    keyword = args['keyword']

    global error_count, processed_chapter_count

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

            if args['chapter'] is not None and chapter_data['chapter'] != args['chapter']:
                if args['verbose']:
                    print("Skipped chapter %d" % chapter_data['chapter'] )
                continue

            if keyword is not None:
                if keyword.lower() not in chapter_data['title'].lower():
                    continue

            if args['read']:
                if not is_chapter_read(chapter_id):
                    if args['verbose']:
                        print("Skipped not read chapter %d" % chapter_data['chapter'] )
                    continue

            #if chapter_data['chapter'] != 9:
            #    continue

            if args['first']:
                if get_chapter_number_by_chapter_id(chapter_id) != 1:
                    continue

            if i < args['start_index']:
                continue

            target_freq_filename = chapter_analysis_dir + chapter_id + ".json"
            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"

            if os.path.exists(input_ocr_file):
                
                if not args['force']:
                    if is_file_up_to_date(target_freq_filename, CURRENT_OCR_SUMMARY_VERSION, CURRENT_LANUGAGE_PARSER_VERSION) and \
                        is_file_up_to_date(parsed_ocr_filename, CURRENT_PARSED_OCR_VERSION, CURRENT_LANUGAGE_PARSER_VERSION):
                            #print("[%d/%d] Skipping %s [chapter %d]" % (i, i_c, chapter_data['title'],chapter_data['chapter']))
                            continue

                #try:
                print("[%d/%d] Scanning %s [%d : %s] " 
                    % (i, i_c, chapter_data['title'], chapter_data['chapter'], chapter_id),end='')

                c_c, w_c, k_c, skipped_c = process_chapter(input_ocr_file, parsed_ocr_filename, chapter_data)
                #except Exception as e:
                #    print("Error scanning %s [%d]" % ( chapter_data['title'], chapter_data['chapter']))
                #    print(e)
                #    error_count += 1
                #    continue

                print(" scanned with %d pages and %d/%d/%d/%d characters/words/kanjis/skipped_blocks" 
                    % ( chapter_data['num_pages'], c_c, w_c, k_c, skipped_c))

                chapter_data['version'] = CURRENT_OCR_SUMMARY_VERSION

                o_f = open(target_freq_filename,"w",encoding="utf-8")
                json_data = json.dumps(chapter_data,  ensure_ascii = False)
                o_f.write(json_data)
                o_f.close()

                processed_chapter_count += 1
            else:
                print("Warning! Missing %s chapter %d" % (title_name, chapter_data['chapter']))


def process_titles(args):
    global processed_title_count

    title_names = get_title_names()
    l_title_names = len(title_names)
    for i, (title_id, title_name) in enumerate(title_names.items()):

        if args['keyword'] is not None:
            if args['keyword'].lower() not in title_name.lower():
                continue

        if args['read']:
            if not is_title_read(title_id):
                continue

        title_data = dict()
        title_data['title_id'] = title_id
        title_data['title'] = title_name

        title_data['num_characters'] = 0
        title_data['num_words'] = 0
        title_data['num_kanjis'] = 0
        title_data['num_pages'] = 0
        title_data['num_unique_words'] = 0
        title_data['num_unique_kanjis'] = 0
        title_data['kanji_frequency'] = dict()
        title_data['num_sentences'] = 0

        total_word_count_per_class = [0] * len(unidic_class_list)

        word_id_list = []
        word_freq = []
        word_classes = []
        sentence_list = []

        title_filename = title_analysis_dir + title_id + ".json"

        vs = get_chapters_by_title_id(title_id)

        if is_file_up_to_date(title_filename, CURRENT_OCR_SUMMARY_VERSION, CURRENT_LANUGAGE_PARSER_VERSION):
            print("Skipping %s [%s] with %d chapters" % (title_name, title_id, len(vs)))
        else:
            print("%d/%d %s [%s] with %d chapters" % (i,l_title_names,title_name, title_id, len(vs)))

            for chapter_id in vs:
                chapter_filename = chapter_analysis_dir + chapter_id + ".json"
                chapter = get_chapter_number_by_chapter_id(chapter_id)

                if os.path.exists(chapter_filename):
                    o_f = open(chapter_filename,"r",encoding="utf-8")
                    chapter_data = json.loads(o_f.read())
                    o_f.close()

                    title_data['num_characters'] += chapter_data['num_characters']
                    title_data['num_words'] += chapter_data['num_words']
                    title_data['num_kanjis'] += chapter_data['num_kanjis']
                    title_data['num_sentences'] += chapter_data['num_sentences']
                    title_data['num_pages'] += chapter_data['num_pages']

                    for i in range(len(unidic_class_list)):
                        total_word_count_per_class[i] += chapter_data['word_count_per_class'][i]

                    chd = chapter_data

                    for i, (word_id, freq, classes) in enumerate(
                            zip(chd['word_id_list'], chd['word_frequency'], chd['word_class_list'])):
                        try:
                            idx = word_id_list.index(word_id)
                            word_freq[idx] += freq
                        except:
                            word_id_list.append(word_id)
                            word_freq.append(freq)
                            word_classes.append(classes)

                    # for each sentence convert word id reference from 
                    # local (chapter) to global (title) reference
                    for sentence in chapter_data['sentence_list']:
                        new_sentence = []
                        for wref in sentence:
                            word_id = chd['word_id_list'][wref]
                            idx = word_id_list.index(word_id)
                            new_sentence.append(idx)
                        sentence_list.append(new_sentence)

                    for w, freq in chapter_data['kanji_frequency'].items():
                        if w in title_data['kanji_frequency']:
                            title_data['kanji_frequency'][w] += freq
                        else:
                            title_data['kanji_frequency'][w] = freq

                else:
                    print("Warning! Missing %s chapter %d" % (title_name, chapter))

            title_data['word_frequency'] = word_freq
            title_data['word_id_list'] = word_id_list
            title_data['word_class_list'] = word_classes
            title_data['sentence_list'] = sentence_list
            title_data['word_count_per_class'] = total_word_count_per_class

            title_data['num_chapters'] = len(vs)
            title_data['num_unique_words'] = len(title_data['word_frequency'])
            title_data['num_unique_kanjis'] = len(title_data['kanji_frequency'])
            title_data['version'] = CURRENT_OCR_SUMMARY_VERSION

            o_f = open(title_filename,"w",encoding="utf-8")
            json_data = json.dumps(title_data,  ensure_ascii = False)
            o_f.write(json_data)
            o_f.close()
            processed_title_count += 1

read_manga_metadata()
read_manga_data()

parser = argparse.ArgumentParser(
    prog="bm_ocr_processor",
    description="Bilingual Manga OCR processing tool",
)

#parser.add_parser('analyze', help='Do comprehension analysis per title')
parser.add_argument('--force', '-f', action='store_true', help='Force reprocessing')
parser.add_argument('--first', '-1', action='store_true', help='Process only first chapter per title')
parser.add_argument('--read', '-r', action='store_true', help='Process only read chapters')
parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
parser.add_argument('--start-index', '-si', nargs='?', type=int, default=1, help='Start from the selected title index')
parser.add_argument('--chapter', '-ch',  nargs='?', type=int, default=None, help='Chapter')
parser.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')

args = vars(parser.parse_args())

#args['force'] = True
#args['keyword'] = 'death note'
#args['chapter'] = 4

if not os.path.exists(title_analysis_dir):
    os.mkdir(chapter_analysis_dir)
if not os.path.exists(chapter_analysis_dir):
    os.mkdir(chapter_analysis_dir)
if not os.path.exists(parsed_ocr_dir):
    os.mkdir(parsed_ocr_dir)

init_parser(load_meanings=True)

process_chapters(args)
if args['chapter'] is None:
    process_titles(args)

print("Total errors: %d. Processed %d titles and %d chapters" % (error_count, processed_title_count, processed_chapter_count))
