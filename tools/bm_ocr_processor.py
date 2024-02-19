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

CURRENT_PARSED_OCR_VERSION = 1
CURRENT_OCR_SUMMARY_VERSION = 1

import os
import re
import json
import sys

"""
Fugashi/Unidic is used to parse Japanese text. However there are some common words
for which IPADIC is better for analysis. For example 'それで' is parsed with Unidic as two
separate words 'それ' + 'で' whereas IPADIC keeps this word intact. 
Some other common discrepancies:
    'だから' -> 'だ' + 'から'
    'ずっと' -> 'ずっ' + 'と'
    'でも' -> 'で' + 'も'
    'いつも' -> 'いつ' + 'も'
.. and so on...
For this reason there's a separate database (jlpt_difficult_to_parse_vocab_file.json) 
of 400+ common JLPT words for which there's a difference in parsing.
When these words are detected, the UNIDIC parsed words are replaced with IPADIC equivalent ones.
"""
import fugashi
parser = fugashi.Tagger('')

base_dir = "../"
manga_metadata_file = base_dir + "json/admin.manga_metadata.json"
manga_data_file = base_dir + "json/admin.manga_data.json"

input_dir = base_dir + "ocr/"
parsed_ocr_dir = base_dir + "parsed_ocr/"
target_chapter_dir = base_dir + "lang/chapters/"
target_title_dir = base_dir + "lang/titles/"

jlpt_difficult_to_parse_vocab_file =  base_dir + "lang/jlpt/jlpt_difficult_parse.json"

complicated_words_to_parse_unidic = dict()
complicated_words_to_parse_ipadic = dict()
complicated_words_to_parse = []

manga_data = None
manga_metadata = None

chapter_id_to_title_id = dict()
chapter_id_to_chapter_number = dict()
title_chapters = dict()
title_names = dict()
chapter_page_count = dict()

all_word_classes = [
    '名詞',
    '助詞',
    '補助記号',
    '動詞',
    '助動詞',
    '接尾辞',
    '副詞',
    '代名詞',
    '形容詞',
    '感動詞',
    '形状詞',
    '接頭辞',
    '接続詞',
    '連体詞',
    '記号',
    '接頭詞',
    'フィラー',  # failure?
]

# some common auxiliary verbs, particles and markings which we ignore for frequency analysis
ignored_classes = [
    '補助記号', # ？
    '助詞', # Grammatical particles: と, ん, から, の, だけ...
    '助動詞', # Auxiliary verb: ちゃ, た, ます, てる, ない
    ]

# words consisting of these wide characters will be ignored
full_width_alphanum = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９"

cjk_ranges = [
    (0x4E00, 0x9FAF),  # CJK unified ideographs
    (0x3400, 0x4DBF),  # CJK unified ideographs Extension A
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
    (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
]

katakana = list(
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズ"
    "セゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピ"
    "フブプヘベペホボポマミムメモャヤュユョヨラリルレロワ"
    "ヲンーヮヰヱヵヶヴヽヾ"
)

def is_katakana_word(word):
    return all(c in katakana for c in word)

def is_cjk(c):
    return any(s <= ord(c) <= e for (s, e) in cjk_ranges)

def has_cjk(word):
    return any(is_cjk(c) for c in word)

def filter_cjk(text):
    return filter(has_cjk, text)

def parse_with_fugashi(line):
    results = []
    r = parser.parse(line)
    lines = r.split('\n')
    for r_line in lines:

        result = r_line.split("\t")
        if len(result) == 2:
            w = result[0]
            d = result[1].split(',')
            if len(d)>=8:
                wtype = d[0]
                basic_type = d[8]
                pro = d[9]
                lemma = d[7]
                orth_base = d[10]
                results.append(([w,wtype,basic_type,pro],lemma,orth_base))
            elif len(d)>0:
                wtype = d[0]
                results.append(([w,wtype,'',''],'',''))

    return results

def parse(line, replace_with_unidic=True):
    res = parse_with_fugashi(line)
    for w in complicated_words_to_parse:
        if w in line:
            ipadic = complicated_words_to_parse_ipadic[w]
            unidic = complicated_words_to_parse_unidic[w]
            if len(unidic)==0:
                # add some words that Unidic didn't find
                for p in ipadic:
                    res.append((p,p[0],p[0]))
            else:
                # to augment/replace the previous Unidic parse result with the corresponding with ipadic,
                # we must make sure that all the unidic findings are present
                unidic_index = 0
                new_res = []
                match = False
                for (r,lemma,orth_base) in res:
                    if not match and r == unidic[unidic_index]:
                        unidic_index += 1
                        if not replace_with_unidic:
                            new_res.append((r,lemma,orth_base))
                        if unidic_index==len(unidic):
                            # found match -> adding replacement/augment from ipadic
                            for r in ipadic:
                                # these are not in ipadic so copy dummy ones
                                lemma = r[0]
                                orth_base = r[0]
                                new_res.append((r,lemma,orth_base))
                            match = True
                    else:
                        new_res.append((r,lemma,orth_base))
                if match:
                    res = new_res
                else:
                    pass
    return res


def parse_line(line, word_count, word_count_per_class, kanji_count, unique_word_list, unique_word_class_list, lemmas):

    res = parse(line)
    if len(res)==0 and len(line)>0:
        raise Exception("Couldn't parse '%s'" % line)
        # parser couldn't parse this. 
        return 0,0, [{line:''}]
    
    k_c = 0
    parsed_words = []
    postponed_non_jp_string = ''
    for (wr,lemma,orth_base) in res:
        w = wr[0]
        cl = wr[1]

        try:
            class_index = all_word_classes.index(cl)
            word_count_per_class[class_index] += 1
        except:
            raise Exception("Unknown class %d in word %s" % (cl, w))

        word = ''
        if all(c in full_width_alphanum for c in w):
            # for some reason wide numbers and alphabets are parsed as 名詞 so ignore these
            pass
        else:

            if cl not in ignored_classes:
                word = orth_base
                if word == '':
                    # empty base form for some reason. Use the parsed form
                    word = w
                if word in word_count:
                    word_count[word] += 1
                else:
                    word_count[word] = 1

                if orth_base != lemma and lemma != '':
                    if '-' not in lemma:
                        if not is_katakana_word(lemma):
                            lemmas[word] = lemma

        try:
            idx = unique_word_list.index(word)
        except ValueError:
            unique_word_list.append(word)
            unique_word_class_list.append(class_index)
            idx = len(unique_word_list)-1

        if idx == 0:
            # when many non-JP characters are in sequence we don't want to save them separately
            # but instead wait until there's actual JP word
            postponed_non_jp_string += w
        else:
            if postponed_non_jp_string != '':
                parsed_words.append( {postponed_non_jp_string:0} )
                postponed_non_jp_string = ''

            parsed_words.append( {w:idx} )

    if postponed_non_jp_string != '':
        parsed_words.append( {postponed_non_jp_string:0} )

    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1
 

    return k_c, parsed_words


def process_chapter(f_p, fo_p, data, word_count, kanji_count):

    k_c = 0
    c_c = 0
    skipped_c = 0

    # this is the word list of basic forms which are referred to by individual parsed words
    unique_word_list = [''] # initialized with a placeholder for non-parseable/non-JP characters
    unique_word_class_list = [''] # initialized with a placeholder for non-parseable/non-JP characters

    f = open(f_p, "r", encoding="utf-8")
    f_data = f.read()
    f.close()

    if '<head><title>404 Not Found</title></head>' in f_data:
        os.remove(f_p)
        raise Exception("404 error! Deleted file %s.." % f_p)
    
    if 'Qmc36BrKcUook4ozuR5iCMV15rHobhfpKVu68nEJrj5Hw7' in f_p:
        pass

    word_count_per_class = [0] * len(all_word_classes)
    lemmas = dict()
    
    pages = json.loads(f_data)
    for page_id,blocks in pages.items():

        for block in blocks:
            lines = block['lines']
            parsed_lines = []
            if any(len(l)>30 for l in lines):
                # Blocks with any number of long lines have usually been 
                # incorrectly recognized so ignore these when doing statistics
                skipped_c += 1
            else:
                for line in lines:
                    kc, parsed_words = parse_line(line, word_count, word_count_per_class, kanji_count, unique_word_list, unique_word_class_list, lemmas)

                    k_c += kc
                    c_c += len(line)
                    parsed_lines.append(parsed_words)
            
            block['plines'] = parsed_lines

    pages['word_list'] = unique_word_list
    pages['word_class_list'] = unique_word_class_list
    pages['version'] = CURRENT_PARSED_OCR_VERSION

    # the total word count excluding words belonging to ignored classes 
    # (alphanumeric words, punctuation, auxialiary verbs, grammatical particles)
    w_c = sum([word_count_per_class[i] for i in range(len(all_word_classes)) if all_word_classes[i] not in ignored_classes])

    f = open(fo_p, "w", encoding="utf-8")
    f.write(json.dumps(pages, ensure_ascii=False))
    f.close()

    return c_c, w_c, k_c, skipped_c, word_count_per_class


with open(jlpt_difficult_to_parse_vocab_file,"r",encoding="utf-8") as f:
    data = f.read()
    d = json.loads(data)
    for w,k in d.items():
        complicated_words_to_parse.append(w)
        complicated_words_to_parse_unidic[w] = k['unidic']
        complicated_words_to_parse_ipadic[w] = k['ipadic']

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
        chapter_ids = m['jp_data']['ch_jph']
        chapter_ids = [cid.split('/')[0] for cid in chapter_ids]
        pages = m['jp_data']['ch_jp']
        title_chapters[title_id] = chapter_ids
        for cid in chapter_ids:
            chapter = str(chapter_ids.index(cid) + 1)
            chapter_id_to_title_id[cid] = title_id
            chapter_id_to_chapter_number[cid] = chapter_ids.index(cid) + 1
            chapter_page_count[cid] = len(pages[chapter])

error_count = 0
processed_chapter_count = 0
processed_title_count = 0

def is_file_up_to_date(filename, version):
    if os.path.exists(filename):
        f = open(filename, "r", encoding="utf-8")
        temp_data = json.loads(f.read())
        f.close()
        if 'version' not in temp_data:
            return False
        elif temp_data['version'] < version:
            return False
        return True
    else:
        return False

def process_chapters(keyword):
    global error_count, processed_chapter_count
    
    files = [f_name for f_name in os.listdir(input_dir) if os.path.isfile(input_dir + f_name)]

    i = 0
    i_c = len(files)

    for f in files:
        chapter_id = f.split('.')[0]
        if chapter_id not in chapter_id_to_title_id:
            print(f + " unknown!")
        else:

            i += 1
            word_count = dict()
            kanji_count = dict()
            input_ocr_file = input_dir + f

            chapter_data = dict()
            title_id = chapter_id_to_title_id[chapter_id]
            chapter_data['title'] = title_names[title_id]
            chapter_data['chapter'] = chapter_id_to_chapter_number[chapter_id]
            chapter_data['num_pages'] = chapter_page_count[chapter_id]

            if keyword is not None:
                if keyword.lower() not in chapter_data['title'].lower():
                    continue

            target_freq_filename = target_chapter_dir + chapter_id + ".json"
            parsed_ocr_filename = parsed_ocr_dir + chapter_id + ".json"
            

            if is_file_up_to_date(target_freq_filename, CURRENT_OCR_SUMMARY_VERSION) and \
                is_file_up_to_date(parsed_ocr_filename, CURRENT_PARSED_OCR_VERSION):
                    print("Skipping %s [chapter %d]" % (chapter_data['title'],chapter_data['chapter']))
                    continue

            try:
                c_c, w_c, k_c, skipped_c, w_c_per_class = process_chapter(input_ocr_file, parsed_ocr_filename, chapter_data, word_count, kanji_count)
            except Exception as e:
                print("Error scanning %s [%d]" % ( chapter_data['title'], chapter_data['chapter']))
                print(e)
                error_count += 1
                continue

            print("[%d/%d] Scanned %s [%d] with %d pages and %d/%d/%d/%d characters/words/kanjis/skipped_blocks" 
                % (i, i_c, chapter_data['title'], chapter_data['chapter'], chapter_data['num_pages'], c_c, w_c, k_c, skipped_c))

            sorted_word_count = dict(sorted(word_count.items(), key=lambda x:x[1], reverse=True))
            sorted_kanji_count = dict(sorted(kanji_count.items(), key=lambda x:x[1], reverse=True))

            chapter_data['num_characters'] = c_c
            chapter_data['num_words'] = w_c
            chapter_data['num_kanjis'] = k_c
            chapter_data['num_skipped_blocks'] = skipped_c
            chapter_data['num_unique_words'] = len(sorted_word_count)
            chapter_data['num_unique_kanjis'] = len(sorted_kanji_count)
            chapter_data['word_frequency'] = sorted_word_count
            chapter_data['kanji_frequency'] = sorted_kanji_count
            chapter_data['word_count_per_class'] = w_c_per_class

            chapter_data['version'] = CURRENT_OCR_SUMMARY_VERSION

            o_f = open(target_freq_filename,"w",encoding="utf-8")
            json_data = json.dumps(chapter_data,  ensure_ascii = False)
            o_f.write(json_data)
            o_f.close()

            processed_chapter_count += 1


def process_titles(keyword):
    global processed_title_count

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
        title_data['num_unique_words'] = 0
        title_data['num_unique_kanjis'] = 0
        title_data['word_frequency'] = dict()
        title_data['kanji_frequency'] = dict()

        total_word_count_per_class = [0] * len(all_word_classes)

        title_filename = target_title_dir + title_id + ".json"

        vs = title_chapters[title_id]

        if is_file_up_to_date(title_filename, CURRENT_OCR_SUMMARY_VERSION):
            print("Skipping %s [%s] with %d chapters" % (title_name, title_id, len(vs)))
        else:
            print("%s [%s] with %d chapters" % (title_name, title_id, len(vs)))

            for chapter_id in vs:
                chapter_filename = target_chapter_dir + chapter_id + ".json"
                chapter = chapter_id_to_chapter_number[chapter_id]
                if os.path.exists(chapter_filename):
                    o_f = open(chapter_filename,"r",encoding="utf-8")
                    chapter_data = json.loads(o_f.read())
                    o_f.close()

                    title_data['num_characters'] += chapter_data['num_characters']
                    title_data['num_words'] += chapter_data['num_words']
                    title_data['num_kanjis'] += chapter_data['num_kanjis']
                    title_data['num_pages'] += chapter_data['num_pages']

                    for i in range(len(all_word_classes)):
                        total_word_count_per_class[i] += chapter_data['word_count_per_class'][i]

                    for w, freq in chapter_data['word_frequency'].items():
                        if w in title_data['word_frequency']:
                            title_data['word_frequency'][w] += freq
                        else:
                            title_data['word_frequency'][w] = freq

                    for w, freq in chapter_data['kanji_frequency'].items():
                        if w in title_data['kanji_frequency']:
                            title_data['kanji_frequency'][w] += freq
                        else:
                            title_data['kanji_frequency'][w] = freq

                else:
                    print("Warning! Missing %s chapter %d" % (title_name, chapter))

            title_data['num_chapters'] = len(vs)
            title_data['num_unique_words'] = len(title_data['word_frequency'])
            title_data['num_unique_kanjis'] = len(title_data['kanji_frequency'])

            title_data['version'] = CURRENT_OCR_SUMMARY_VERSION

            o_f = open(title_filename,"w",encoding="utf-8")
            json_data = json.dumps(title_data,  ensure_ascii = False)
            o_f.write(json_data)
            o_f.close()
            processed_title_count += 1


if len(sys.argv)>1:
    keyword = sys.argv[1]
else:
    keyword = None

if not os.path.exists(target_title_dir):
    os.mkdir(target_chapter_dir)
if not os.path.exists(target_chapter_dir):
    os.mkdir(target_chapter_dir)
if not os.path.exists(parsed_ocr_dir):
    os.mkdir(parsed_ocr_dir)


#keyword = 'keaton'

process_chapters(keyword)
process_titles(keyword)

print("Total errors: %d. Processed %d titles and %d chapters" % (error_count, processed_title_count, processed_chapter_count))
