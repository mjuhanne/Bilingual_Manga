"""
This script is used to process BilingualManga.org OCR files (in /ocr directory) and
calculate word and kanji frequencies as well as cumulative values.
Each chapter(volume/tankobon) OCR file is processed first and then aggregate values 
are saved for each manga title.

These analysis JSON files are saved into lang/volumes and lang/titles directories correspondingly.

Also a set of separate parsed OCR files are saved into './parsed_ocr' directory. These files
will have word-to-word separation in OCR lines and allow for visualization and changing of the
learning stage of each word separately.

Because the original AI based OCR tool most likely didn't handle well the larger text sections
these are ignored (marked as 'skipped blocks'). The blocks are ignored in statistics and also
in the parsed OCR files.

Using this script requires installing also the fugashi dependencies:
    pip install fugashi[unidic-lite]

    # The full version of UniDic requires a separate download step
    pip install fugashi[unidic]
    python -m unidic download
"""

import os
import json
import sys
from helper import *
from jp_parser import (
    parse_line_with_unidic, post_process_unidic_particles, parse_with_jmdict, 
    load_jmdict, load_conjugations, reassemble_block,
    unidic_word_classes, ignored_classes_for_freq
)
# for loggin
from jp_parser import open_log_file, close_log_file, set_verbose_level

parsed_ocr_dir = base_dir + "parsed_ocr/"
error_count = 0
processed_chapter_count = 0
processed_title_count = 0


def process_chapter(f_p, fo_p, chapter_data):

    k_c = 0
    c_c = 0
    skipped_c = 0

    # this is the word list of basic forms which are referred to by individual parsed words
    # initialized with a placeholder for non-parseable/non-JP characters and auxiliary verbs
    unique_jmdict_word_list = ['','*','-'] 
    unique_jmdict_word_count = [0,0,0]
    unique_jmdict_word_class_list = [[],[],[]] 
    unique_jmdict_word_seq = [0,0,0]
    word_count_per_class = [0] * len(unidic_word_classes)

    kanji_count = dict()
    lemmas = dict()

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
                #for line in lines:
                kc, ud_words, ud_word_ortho, ud_word_class, = \
                    parse_line_with_unidic(line, kanji_count, lemmas)

                k_c += kc
                c_c += len(line)

                ud_words, ud_word_ortho, ud_word_class, ud_word_flags = \
                    post_process_unidic_particles(ud_words, ud_word_ortho, ud_word_class)

                word_ref  = parse_with_jmdict(
                    ud_words, ud_word_ortho, ud_word_class, ud_word_flags,
                    unique_jmdict_word_list, unique_jmdict_word_count, unique_jmdict_word_seq,  unique_jmdict_word_class_list,
                    word_count_per_class, 
                )

                block['jlines'] = reassemble_block(lines, ud_words, word_ref)

        page_count += 1
        if page_count % progress_bar_interval == 0:
            print(".",end='',flush=True)

    pages['word_list'] = unique_jmdict_word_list
    pages['word_seq'] = unique_jmdict_word_seq
    pages['word_class_list'] = unique_jmdict_word_class_list
    pages['lemmas'] = lemmas
    pages['version'] = CURRENT_PARSED_OCR_VERSION
    pages['parser_version'] = CURRENT_LANUGAGE_PARSER_VERSION

    # the total word count excluding words belonging to ignored classes 
    # (alphanumeric words, punctuation, auxialiary verbs, grammatical particles)
    w_c = sum([word_count_per_class[i] for i in range(len(unidic_word_classes)) if unidic_word_classes[i] not in ignored_classes_for_freq])

    f = open(fo_p, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()

    #sorted_word_count = dict(sorted(unique_jmdict_word_count.items(), key=lambda x:x[1], reverse=True))
    sorted_kanji_count = dict(sorted(kanji_count.items(), key=lambda x:x[1], reverse=True))

    chapter_data['num_characters'] = c_c
    chapter_data['num_words'] = w_c
    chapter_data['num_kanjis'] = k_c
    chapter_data['num_skipped_blocks'] = skipped_c
    chapter_data['num_unique_words'] = len(unique_jmdict_word_list)
    chapter_data['num_unique_kanjis'] = len(sorted_kanji_count)
    chapter_data['word_frequency'] = unique_jmdict_word_count
    chapter_data['kanji_frequency'] = sorted_kanji_count
    chapter_data['words'] = unique_jmdict_word_list
    chapter_data['word_seq'] = unique_jmdict_word_seq
    chapter_data['lemmas'] = lemmas
    chapter_data['word_count_per_class'] = word_count_per_class
    chapter_data['parser_version'] = CURRENT_LANUGAGE_PARSER_VERSION

    return c_c, w_c, k_c, skipped_c

def is_file_up_to_date(filename, version, parser_version):
    ## TESTING
    return False

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
    else:
        return False

def process_chapters(keyword):
    global error_count, processed_chapter_count
    
    files = [f_name for f_name in os.listdir(ocr_dir) if os.path.isfile(ocr_dir + f_name)]

    i = 0
    i_c = len(files)

    for f in files:
        chapter_id = f.split('.')[0]
        try:
            title_id = get_title_id_by_chapter_id(chapter_id)
        except:
            title_id = ''

        if title_id == '':
            print(f + " unknown!")
        else:

            i += 1
            input_ocr_file = ocr_dir + f

            chapter_data = dict()
            chapter_data['title'] = get_title_by_id(title_id)
            chapter_data['chapter'] = get_chapter_number_by_chapter_id(chapter_id)
            chapter_data['num_pages'] =  get_chapter_page_count(chapter_id)

            if keyword is not None:
                if keyword.lower() not in chapter_data['title'].lower():
                    continue

            target_freq_filename = chapter_analysis_dir + chapter_id + ".json"
            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"
            

            if is_file_up_to_date(target_freq_filename, CURRENT_OCR_SUMMARY_VERSION, CURRENT_LANUGAGE_PARSER_VERSION) and \
                is_file_up_to_date(parsed_ocr_filename, CURRENT_PARSED_OCR_VERSION, CURRENT_LANUGAGE_PARSER_VERSION):
                    print("Skipping %s [chapter %d]" % (chapter_data['title'],chapter_data['chapter']))
                    continue

            #try:
            print("[%d/%d] Scanning %s [%d] " 
                % (i, i_c, chapter_data['title'], chapter_data['chapter']),end='')

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


def process_titles(keyword):
    global processed_title_count

    for title_id, title_name in get_title_names().items():

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
        title_data['num_unique_words'] = 0
        title_data['num_unique_kanjis'] = 0
        title_data['kanji_frequency'] = dict()
        title_data['lemmas'] = dict()

        total_word_count_per_class = [0] * len(unidic_word_classes)

        word_list = []
        word_freq = []
        word_seq = []

        title_filename = title_analysis_dir + title_id + ".json"

        vs = get_chapters_by_title_id(title_id)

        if is_file_up_to_date(title_filename, CURRENT_OCR_SUMMARY_VERSION, CURRENT_LANUGAGE_PARSER_VERSION):
            print("Skipping %s [%s] with %d chapters" % (title_name, title_id, len(vs)))
        else:
            print("%s [%s] with %d chapters" % (title_name, title_id, len(vs)))

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
                    title_data['num_pages'] += chapter_data['num_pages']

                    for i in range(len(unidic_word_classes)):
                        total_word_count_per_class[i] += chapter_data['word_count_per_class'][i]

                    chd = chapter_data

                    for i, (word, seq, freq) in enumerate(
                            zip(chd['words'], chd['word_seq'],chd['word_frequency'])):
                        try:
                            idx = word_seq.index(seq)
                            word_freq[idx] += freq
                        except:
                            word_seq.append(seq)
                            word_list.append(word)
                            word_freq.append(freq)

                    for w, freq in chapter_data['kanji_frequency'].items():
                        if w in title_data['kanji_frequency']:
                            title_data['kanji_frequency'][w] += freq
                        else:
                            title_data['kanji_frequency'][w] = freq

                    for w, lemma in chapter_data['lemmas'].items():
                        if w not in title_data['lemmas']:
                            title_data['lemmas'][w] = lemma
                else:
                    print("Warning! Missing %s chapter %d" % (title_name, chapter))

            title_data['word_frequency'] = word_freq
            title_data['word_seq'] = word_seq
            title_data['words'] = word_list
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

keyword = "keaton" #"dream"
if len(sys.argv)>1:
    keyword = sys.argv[1]


if not os.path.exists(title_analysis_dir):
    os.mkdir(chapter_analysis_dir)
if not os.path.exists(chapter_analysis_dir):
    os.mkdir(chapter_analysis_dir)
if not os.path.exists(parsed_ocr_dir):
    os.mkdir(parsed_ocr_dir)


load_jmdict()
load_conjugations()


open_log_file("ocr-log.txt")
set_verbose_level(0)
process_chapters(keyword)
process_titles(keyword)

close_log_file()

print("Total errors: %d. Processed %d titles and %d chapters" % (error_count, processed_title_count, processed_chapter_count))
