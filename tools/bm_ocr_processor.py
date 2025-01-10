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
    get_flat_class_list_by_seq, load_manga_specific_adjustments, set_parser_settings,
    unidic_class_list, ignored_classes_for_freq
)
from bm_learning_engine_helper import is_chapter_read, is_title_read
from ocr_processor_helper import *

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0

processed_titles = set()

save_word_classes = False

def do_process_chapter(title_id, chapter_id, f_p, fo_p, chapter_data, omit_parsed_ocr_file):

    k_c = 0
    c_c = 0
    skipped_c = 0

    results = init_scan_results()
    set_parser_settings('keep_only_priority_references', omit_parsed_ocr_file)
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
    ocr_is_verified = is_ocr_verified(title_id)
    for page_id,blocks in pages.items():

        for i,block in enumerate(blocks):
            lines = block['lines']

            if not ocr_is_verified and any(len(l)>32 for l in lines):
                # Blocks with any number of very long lines have usually been 
                # incorrectly recognized so ignore these
                skipped_c += 1
                block['jlines'] = []
            else:
                lines = apply_ocr_correction(chapter_id,page_id,i,lines)

                line = ''.join(lines)
                kc, ud_items, mismatch = \
                    parse_block_with_unidic(lines, kanji_count)

                k_c += kc
                c_c += len(line)

                ud_items = \
                    post_process_unidic_particles(ud_items)
                
                priority_word_ids = get_manually_set_priority_word_ids(title_id,chapter_id,page_id,i)

                parse_with_jmdict(
                    ud_items, priority_word_ids, results,
                )

                block['jlines'] = reassemble_block(lines, ud_items, results['item_word_id_refs'])

        page_count += 1
        if page_count % progress_bar_interval == 0:
            print(".",end='',flush=True)

    pages['parsed_data'] = results
    pages['version'] = get_version(PARSED_OCR_VERSION)
    pages['parser_version'] = get_version(LANUGAGE_PARSER_VERSION)

    # the total word count excluding words belonging to ignored classes 
    # (alphanumeric words, punctuation, auxialiary verbs, grammatical particles)
    w_c = sum([results['word_count_per_unidict_class'][i] for i in range(len(unidic_class_list)) if unidic_class_list[i] not in ignored_classes_for_freq])

    if not omit_parsed_ocr_file:
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
            wid = results['priority_word_id_list'][ref]
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
    if save_word_classes:
        chapter_data['word_class_list'] = unique_words_classes
    chapter_data['word_count_per_class'] = results['word_count_per_unidict_class']
    chapter_data['sentence_list'] = adjusted_sentence_list
    chapter_data['parser_version'] = get_version(LANUGAGE_PARSER_VERSION)

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
            if 'num_pages' in temp_data and temp_data['num_pages'] == 0:
                return False
            #if 'num_characters' in temp_data and temp_data['num_characters'] < 1000:
            #    return False
            return True
    except:
        pass
    return False


def process_chapter(args, title_id, title_name, chapter_id, info_str = ''):
    input_ocr_file = ocr_dir + str(chapter_id) + '.json'

    chapter_data = dict()
    chapter_data['title'] = get_title_by_id(title_id)
    chapter_data['chapter'] = get_chapter_number_by_chapter_id(chapter_id)
    chapter_data['num_pages'] =  get_chapter_page_count(chapter_id)

    target_analysis_filename = chapter_analysis_dir + chapter_id + ".json"
    parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"

    if os.path.exists(input_ocr_file):

        if args['only_new']:
            if os.path.exists(target_analysis_filename):
                return None

        if not args['force']:
            if is_file_up_to_date(target_analysis_filename, get_version(OCR_SUMMARY_VERSION), get_version(LANUGAGE_PARSER_VERSION)) and \
                is_file_up_to_date(parsed_ocr_filename, get_version(PARSED_OCR_VERSION), get_version(LANUGAGE_PARSER_VERSION)):
                    #print("[%d/%d] Skipping %s [chapter %d]" % (i, i_c, chapter_data['title'],chapter_data['chapter']))
                    print(".",end='',flush=True)
                    return None
            

        print(info_str,end='')
        #try:

        c_c, w_c, k_c, skipped_c = do_process_chapter(title_id, chapter_id, input_ocr_file, parsed_ocr_filename, chapter_data, args['omit_parsed_ocr_file'])
        #except Exception as e:
        #    print("Error scanning %s [%d]" % ( chapter_data['title'], chapter_data['chapter']))
        #    print(e)
        #    error_count += 1
        #    continue

        print(" scanned with %d pages and %d/%d/%d/%d characters/words/kanjis/skipped_blocks" 
            % ( chapter_data['num_pages'], c_c, w_c, k_c, skipped_c))

        chapter_data['version'] = get_version(OCR_SUMMARY_VERSION)

        o_f = open(target_analysis_filename,"w",encoding="utf-8")
        json_data = json.dumps(chapter_data,  ensure_ascii = False)
        o_f.write(json_data)
        o_f.close()

        return chapter_data
    else:
        print("Warning! Missing %s chapter %d" % (title_name, chapter_data['chapter']))
        return None


def process_title_chapters(args, title_id, title_name, counter_str=''):

    global error_count, processed_chapter_count

    load_manga_specific_adjustments(title_name)

    chapters = get_chapters_by_title_id(title_id, lang='jp')
    title_name = get_title_by_id(title_id)

    for i, chapter_id in enumerate(chapters):

        chapter_idx = get_chapter_idx_by_chapter_id(chapter_id)

        if args['chapter'] is not None and chapter_idx != args['chapter']:
            if args['verbose']:
                print("Skipped chapter %d" % chapter_idx )
            continue

        if args['read']:
            if not is_chapter_read(chapter_id):
                if args['verbose']:
                    print("Skipped not read chapter %d" % chapter_idx )
                continue

        if args['first']:
            if chapter_idx != 1:
                continue

        if i+1 < args['start_index']:
            continue

        info_str = "[%s] (%d/%d) Scanning %s [%d : %s] " % (counter_str, i+1, len(chapters), title_name, get_chapter_idx_by_chapter_id(chapter_id), chapter_id)
        chapter_data = process_chapter(args, title_id, title_name, chapter_id, info_str)
        if chapter_data is not None:
            processed_chapter_count += 1
            processed_titles.update([title_id])
    return processed_chapter_count



def do_process_title(args, title_id, title_name, counter_str=''):
    global processed_title_count

    processed_chapter_count = process_title_chapters(args, title_id, title_name, counter_str)

    # aggregate data for the whole title
    #if processed_chapter_count > 0:
    volume_ids = get_volumes_by_title_id(title_id, lang='jp')
    for vol_id in volume_ids:
        # Aggregate data for the each volume
        # Applicable only for books. For mangas each chapter is considered as volume 
        # and handled already below
        chapter_ids = get_chapters_by_volume_id(vol_id)
        if len(chapter_ids)>1:
            vol_name = title_name + ' - ' + get_volume_name(vol_id)
            process_chapter_set(args, vol_id, vol_name ,chapter_ids, volume_analysis_dir, counter_str)

    if not is_book(title_id) or len(volume_ids) > 1:
            # it's a manga (each chapter is a volume) or there are more than 1 volume
            chapter_ids = get_chapters_by_title_id(title_id)
            if len(chapter_ids) > 1:
                if process_chapter_set(args, title_id, title_name, chapter_ids, title_analysis_dir, counter_str):
                    processed_title_count += 1

        

def process_titles(args):

    title_names = get_title_names()
    l_title_names = len(title_names)
    for i, (title_id, title_name) in enumerate(title_names.items()):

        jp_title = get_jp_title_by_id(title_id)

        if args['book'] and not is_book(title_id):
            continue

        if args['keyword'] is not None:
            if args['keyword'].lower() not in title_name.lower() and args['keyword'] not in jp_title and args['keyword'] != title_id:
                continue

        if args['author']:
            authors = get_authors(title_id)
            found = False
            for author in authors:
                if args['author'].lower() in author:
                    found = True
            if not found:
                continue

        if args['read']:
            if not is_title_read(title_id):
                continue

        if title_name == 'Placeholder':
            title_name = jp_title
        do_process_title(args, title_id, title_name,"%d/%d" % (i,l_title_names))



def process_chapter_set(args, target_id, target_name, chapter_ids, analysis_dir, counter_str):

    title_data = dict()
    title_data['id'] = target_id
    title_data['name'] = target_name

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

    output_filename = analysis_dir + target_id + ".json"

    if not args['force'] and not args['force_aggregate'] and target_id not in processed_titles and is_file_up_to_date(output_filename, get_version(OCR_SUMMARY_VERSION), get_version(LANUGAGE_PARSER_VERSION)):
        print("Skipping %s [%s] with %d chapters" % (target_name, target_id, len(chapter_ids)))
        return False
    else:
        print("%s %s [%s] with %d chapters" % (counter_str,target_name, target_id, len(chapter_ids)))

        parser_version = 0
        title_data['num_characters_per_ch'] = []
        title_data['num_words_per_ch'] = []
        title_data['num_kanjis_per_ch'] = []
        title_data['num_sentences_per_ch'] = []
        title_data['num_pages_per_ch']= []

        for chapter_id in chapter_ids:
            chapter_filename = chapter_analysis_dir + chapter_id + ".json"
            chapter = get_chapter_idx_by_chapter_id(chapter_id)

            if os.path.exists(chapter_filename):
                o_f = open(chapter_filename,"r",encoding="utf-8")
                chapter_data = json.loads(o_f.read())
                o_f.close()

                title_data['num_characters'] += chapter_data['num_characters']
                title_data['num_words'] += chapter_data['num_words']
                title_data['num_kanjis'] += chapter_data['num_kanjis']
                title_data['num_sentences'] += chapter_data['num_sentences']
                title_data['num_pages'] += chapter_data['num_pages']

                title_data['num_characters_per_ch'].append(chapter_data['num_characters'])
                title_data['num_words_per_ch'].append(chapter_data['num_words'])
                title_data['num_kanjis_per_ch'].append(chapter_data['num_kanjis'])
                title_data['num_sentences_per_ch'].append(chapter_data['num_sentences'])
                title_data['num_pages_per_ch'].append(chapter_data['num_pages'])

                parser_version = chapter_data['parser_version']

                for i in range(len(unidic_class_list)):
                    total_word_count_per_class[i] += chapter_data['word_count_per_class'][i]

                chd = chapter_data

                for i, (word_id, freq) in enumerate(
                        zip(chd['word_id_list'], chd['word_frequency'])):
                    try:
                        idx = word_id_list.index(word_id)
                        word_freq[idx] += freq
                    except:
                        word_id_list.append(word_id)
                        word_freq.append(freq)
                        if save_word_classes:
                            classes = chd['word_class_list'][i]
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
                print("Warning! Missing %s chapter %d" % (target_name, chapter))
                title_data['num_characters_per_ch'].append(0)
                title_data['num_words_per_ch'].append(0)
                title_data['num_kanjis_per_ch'].append(0)
                title_data['num_sentences_per_ch'].append(0)
                title_data['num_pages_per_ch'].append(0)

        title_data['word_frequency'] = word_freq
        title_data['word_id_list'] = word_id_list
        if save_word_classes:
            title_data['word_class_list'] = word_classes
        title_data['sentence_list'] = sentence_list
        title_data['word_count_per_class'] = total_word_count_per_class

        title_data['num_chapters'] = len(chapter_ids)
        title_data['num_unique_words'] = len(title_data['word_frequency'])
        title_data['num_unique_kanjis'] = len(title_data['kanji_frequency'])
        title_data['version'] = get_version(OCR_SUMMARY_VERSION)
        title_data['parser_version'] = parser_version

        o_f = open(output_filename,"w",encoding="utf-8")
        json_data = json.dumps(title_data,  ensure_ascii = False)
        o_f.write(json_data)
        o_f.close()
        return True
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog="bm_ocr_processor",
        description="Bilingual Manga OCR processing tool",
    )

    #parser.add_parser('analyze', help='Do comprehension analysis per title')
    parser.add_argument('--force', '-f', action='store_true', help='Force reprocessing')
    parser.add_argument('--force_aggregate', '-fa', action='store_true', help='Force aggregating data at title/volume level')
    parser.add_argument('--first', '-1', action='store_true', help='Process only first chapter per title')
    parser.add_argument('--read', '-r', action='store_true', help='Process only read chapters')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    parser.add_argument('--start-index', '-si', nargs='?', type=int, default=1, help='Start from the selected title index')
    parser.add_argument('--chapter', '-ch',  nargs='?', type=int, default=None, help='Chapter')
    parser.add_argument('--only_new', '-on', action='store_true', help='Process only new chapters')
    parser.add_argument('--book', '-b',  action='store_true', help='Parse books only')
    parser.add_argument('keyword', nargs='?', type=str, default=None, help='Title has to (partially) match the keyword in order to processed')
    parser.add_argument('--author', '-a',  nargs='?', type=str, default=None, help='Author')
    parser.add_argument('--omit_parsed_ocr_file', '-oo', action='store_true', help='Do not save the full parsed ocr chapter file (only chapter/volume/title analysis files)')

    args = vars(parser.parse_args())

    #args['force'] = True
    #args['book'] = True
    #args['keyword'] = '67715885b339fc79230d89c2'
    #args['force_aggregate'] = True
    #args['chapter'] = 12
    #args['only_new'] = True
    #args['omit_parsed_ocr_file'] = True

    if not os.path.exists(title_analysis_dir):
        os.mkdir(title_analysis_dir)
    if not os.path.exists(volume_analysis_dir):
        os.mkdir(volume_analysis_dir)
    if not os.path.exists(chapter_analysis_dir):
        os.mkdir(chapter_analysis_dir)
    if not os.path.exists(parsed_ocr_dir):
        os.mkdir(parsed_ocr_dir)

    init_parser(load_meanings=True)

    process_titles(args)

    print("Total errors: %d. Processed %d titles and %d chapters" % (error_count, processed_title_count, processed_chapter_count))
