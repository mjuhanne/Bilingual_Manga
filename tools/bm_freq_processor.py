# This script is used to process BilingualManga.org OCR files (in /ocr directory) and
# calculate word and kanji frequencies as well as cumulative values.
# Each tankobon/volume OCR file is processed first and then aggregate values are saved for each manga title
# Analysis JSON files are saved into freq/volumes and freq/titles directories.
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

manga_metadata_file = "../json/admin.manga_metadata.json"
manga_data_file = "../json/admin.manga_data.json"

input_dir = "../ocr/"
target_vol_dir = "freq/volumes/"
target_title_dir = "freq/titles/"

jlpt_difficult_to_parse_vocab_file =  "freq/jlpt/jlpt_difficult_parse.json"

complicated_words_to_parse_unidic = dict()
complicated_words_to_parse_ipadic = dict()
complicated_words_to_parse = []

manga_data = None
manga_metadata = None

volume_id_to_title_id = dict()
volume_id_to_volume_number = dict()
title_volumes = dict()
title_names = dict()
volume_page_count = dict()

with open(jlpt_difficult_to_parse_vocab_file,"r",encoding="utf-8") as f:
    data = f.read()
    d = json.loads(data)
    for w,k in d.items():
        complicated_words_to_parse.append(w)
        complicated_words_to_parse_unidic[w] = k['unidic']
        complicated_words_to_parse_ipadic[w] = k['ipadic']

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

# some common auxiliary words and markings which we ignore
ignored_classes = [
    '補助記号', # ？
    '助詞', # と, ん
    '助動詞', # ちゃ, た
    ]

lemma_to_orth_base = dict()

def parse_line(line, word_count, kanji_count):
    global lemma_to_orth_base
    res = parse(line)
    w_c = 0
    k_c = 0
    for (wr,lemma,orth_base) in res:
        w = wr[0]
        cl = wr[1]
        if cl not in ignored_classes:
            word = orth_base
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1
            w_c += 1
    for k in set(filter_cjk(line)):
        k_c += 1
        if k in kanji_count:
            kanji_count[k] += 1
        else:
            kanji_count[k] = 1
    return w_c, k_c


def scan_tankobon(f_p, data, word_count, kanji_count):

    w_c = 0
    k_c = 0
    c_c = 0

    f = open(f_p, "r", encoding="utf-8")

    f_data = f.read()
    f.close()

    if '<head><title>404 Not Found</title></head>' in f_data:
        os.remove(f_p)
        raise Exception("404 error! Deleting file %s.." % f_p)
    
    pages = json.loads(f_data)
    for page_id,blocks in pages.items():

        for block in blocks:
            lines = block['lines']
            if any(len(l)>20 for l in lines):
                pass
            else:
                for line in lines:
                    if len(line) > 20:
                        pass
        
                    wc, kc = parse_line(line, word_count, kanji_count)
                    w_c += wc
                    k_c += kc
                    c_c += len(line)

    return c_c, w_c, k_c

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

def process_volumes(keyword):
    global error_count
    
    files = [f_name for f_name in os.listdir(input_dir) if os.path.isfile(input_dir + f_name)]

    i = 0
    i_c = len(files)

    for f in files:
        volume_id = f.split('.')[0]
        if volume_id not in volume_id_to_title_id:
            print(f + " unknown!")
        else:

            i += 1
            word_count = dict()
            kanji_count = dict()
            p = input_dir + f

            volume_data = dict()
            title_id = volume_id_to_title_id[volume_id]
            volume_data['title'] = title_names[title_id]
            volume_data['volume'] = volume_id_to_volume_number[volume_id]
            volume_data['num_pages'] = volume_page_count[volume_id]

            if keyword is not None:
                if keyword.lower() not in volume_data['title'].lower():
                    continue

            target_filename = target_vol_dir + volume_id + ".json"
            if os.path.exists(target_filename):
                print("Skipping %s [vol %d]" % (volume_data['title'],volume_data['volume']))
                continue

            try:
                c_c, w_c, k_c = scan_tankobon(p, volume_data, word_count, kanji_count)
            except Exception as e:
                print("Error scanning %s [%d]" % ( volume_data['title'], volume_data['volume']))
                print(e)
                error_count += 1
                continue

            print("[%d/%d] Scanned %s [%d] with %d pages and %d/%d/%d characters/words/kanjis" 
                % (i, i_c, volume_data['title'], volume_data['volume'], volume_data['num_pages'], c_c, w_c, k_c))


            sorted_word_count = dict(sorted(word_count.items(), key=lambda x:x[1], reverse=True))
            sorted_kanji_count = dict(sorted(kanji_count.items(), key=lambda x:x[1], reverse=True))

            volume_data['num_characters'] = c_c
            volume_data['num_words'] = w_c
            volume_data['num_kanjis'] = k_c
            volume_data['num_individual_words'] = len(sorted_word_count)
            volume_data['num_individual_kanjis'] = len(sorted_kanji_count)
            volume_data['word_frequency'] = sorted_word_count
            volume_data['kanji_frequency'] = sorted_kanji_count

            o_f = open(target_filename,"w",encoding="utf-8")
            json_data = json.dumps(volume_data)
            o_f.write(json_data)
            o_f.close()


def process_titles(keyword):
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

        title_filename = target_title_dir + title_id + ".json"

        vs = title_volumes[title_id]

        if os.path.exists(title_filename):
            print("Skipping %s [%s] with %d volumes" % (title_name, title_id, len(vs)))
        else:
            print("%s [%s] with %d volumes" % (title_name, title_id, len(vs)))

            for volume_id in vs:
                volume_filename = target_vol_dir + volume_id + ".json"
                vol = volume_id_to_volume_number[volume_id]
                if os.path.exists(volume_filename):
                    o_f = open(volume_filename,"r",encoding="utf-8")
                    volume_data = json.loads(o_f.read())
                    o_f.close()

                    title_data['num_characters'] += volume_data['num_characters']
                    title_data['num_words'] += volume_data['num_words']
                    title_data['num_kanjis'] += volume_data['num_kanjis']
                    title_data['num_pages'] += volume_data['num_pages']

                    for w, freq in volume_data['word_frequency'].items():
                        if w in title_data['word_frequency']:
                            title_data['word_frequency'][w] += freq
                        else:
                            title_data['word_frequency'][w] = freq

                    for w, freq in volume_data['kanji_frequency'].items():
                        if w in title_data['kanji_frequency']:
                            title_data['kanji_frequency'][w] += freq
                        else:
                            title_data['kanji_frequency'][w] = freq

                else:
                    print("Warning! Missing %s volume %d" % (title_name, vol))


            title_data['num_individual_words'] = len(title_data['word_frequency'])
            title_data['num_individual_kanjis'] = len(title_data['kanji_frequency'])

            o_f = open(title_filename,"w",encoding="utf-8")
            json_data = json.dumps(title_data)
            o_f.write(json_data)
            o_f.close()


if len(sys.argv)>1:
    keyword = sys.argv[1]
else:
    keyword = None

process_volumes(keyword)
process_titles(keyword)

print("Total errors: %d" % error_count)
